from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
import json
from typing import Dict, Any, List
from app.memory.conversation import ConversationManager  # noqa: F401 — used in type context
from app.memory.rag_manager import get_rag_manager
from app.core.planner import TaskPlanner
from app.core.model_router import ModelProvider
from app.core.system_tools import SYSTEM_TOOLS
from app.core.system_executor import get_system_executor

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        # Track active session per client - messages stay in same session
        self.client_sessions: Dict[str, str] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_sessions:
            del self.client_sessions[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    def get_session(self, client_id: str) -> str | None:
        """Get the current session for a client"""
        return self.client_sessions.get(client_id)
    
    def set_session(self, client_id: str, session_id: str):
        """Set the current session for a client"""
        self.client_sessions[client_id] = session_id
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()
task_planner = TaskPlanner()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "message":
                await handle_message(client_id, message_data, websocket)
            elif message_type == "ping":
                await manager.send_message(client_id, {"type": "pong"})
            elif message_type == "new_session":
                # Client explicitly starting a new session
                manager.client_sessions.pop(client_id, None)
                
                # Create a new session in MongoDB with timestamp-based title
                # (will be renamed to smart title after first message)
                from datetime import datetime
                conv_manager = websocket.app.state.conv_manager
                initial_title = f"New Chat - {datetime.now().strftime('%b %d, %I:%M %p')}"
                new_conversation_id = await conv_manager.create_conversation(
                    user_id=client_id,
                    title=initial_title,
                    metadata={"source": "new_session_button"}
                )
                
                # Track the new session
                manager.set_session(client_id, new_conversation_id)
                
                await manager.send_message(client_id, {
                    "type": "session_created",
                    "conversation_id": new_conversation_id,
                    "title": initial_title,
                    "message": "New session created"
                })
            else:
                await manager.send_message(client_id, {
                    "type": "error",
                    "error": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)
        try:
            await manager.send_message(client_id, {
                "type": "error",
                "error": str(e)
            })
        except Exception:
            logger.debug(f"Failed to send error to disconnected client {client_id}")

async def handle_message(client_id: str, message_data: Dict[str, Any], websocket: WebSocket):
    """Handle incoming message and stream response"""
    try:
        # Get conversation_id from message OR use the tracked session
        conversation_id = message_data.get("conversation_id")
        user_message = message_data.get("content")
        metadata = message_data.get("metadata", {})
        use_ollama = metadata.get("use_ollama", False)
        
        if not user_message:
            await manager.send_message(client_id, {
                "type": "error",
                "error": "No message content provided"
            })
            return
        
        # Get app state from websocket
        ai_brain = websocket.app.state.ai_brain
        core_memory = websocket.app.state.core_memory
        vector_store = websocket.app.state.vector_store
        rag_manager = websocket.app.state.rag_manager
        
        # Get system executor
        system_executor = get_system_executor()
        
        # Get conversation manager from app state (initialized once in lifespan)
        conv_manager = websocket.app.state.conv_manager
        
        # SESSION MANAGEMENT FIX:
        # If no conversation_id provided, check if client has an active session
        # Only create new session if explicitly requested (new_session message type)
        is_new_conversation = False
        if not conversation_id:
            # Check for tracked session
            tracked_session = manager.get_session(client_id)
            if tracked_session:
                # Verify session still exists
                existing = await conv_manager.get_conversation(client_id, tracked_session)
                if existing:
                    conversation_id = tracked_session
                    logger.info(f"Using existing session {conversation_id} for client {client_id}")
        
        # Create new conversation only if we still don't have one
        if not conversation_id:
            # Generate smart title using LLM
            from app.core.conversation_namer import get_conversation_namer
            namer = get_conversation_namer()
            title = await namer.generate_title(user_message)
            
            conversation_id = await conv_manager.create_conversation(
                user_id=client_id,
                title=title,
                metadata={"source": "chat"}
            )
            is_new_conversation = True
            # Track this session for the client
            manager.set_session(client_id, conversation_id)
            logger.info(f"Created new session '{title}' ({conversation_id}) for client {client_id}")
        else:
            # Update tracked session
            manager.set_session(client_id, conversation_id)
        
        # Add user message
        user_msg_id = await conv_manager.add_message(
            conversation_id,
            "user",
            user_message,
            metadata=metadata
        )
        
        # Send acknowledgment with conversation ID
        await manager.send_message(client_id, {
            "type": "message_received",
            "conversation_id": conversation_id,
            "message_id": user_msg_id
        })
        
        # ===== FILE ATTACHMENT HANDLING =====
        attached_file = metadata.get("attached_file")
        image_data = None
        audio_data = None
        
        if attached_file:
            file_name = attached_file.get("name", "unknown")
            file_type = attached_file.get("type", "")
            file_data = attached_file.get("data")  # base64 encoded
            
            logger.info(f"Received file attachment: {file_name} ({file_type})")
            
            # Check if it's an image file for vision processing
            if file_type.startswith("image/") and file_data:
                image_data = {
                    "name": file_name,
                    "type": file_type,
                    "data": file_data
                }
                logger.info(f"Image detected - will use Gemini Vision for analysis")
                
                # Notify client that we're processing the image
                await manager.send_message(client_id, {
                    "type": "status",
                    "message": f"Analyzing image: {file_name}",
                    "conversation_id": conversation_id
                })
            
            # Check if it's an audio file for multimodal audio processing
            elif file_type.startswith("audio/") and file_data:
                audio_data = {
                    "name": file_name,
                    "type": file_type,
                    "data": file_data
                }
                logger.info(f"Audio detected - will use Gemini Multimodal Audio")
                
                await manager.send_message(client_id, {
                    "type": "status",
                    "message": f"Processing audio: {file_name}",
                    "conversation_id": conversation_id
                })
        
        # Get conversation messages
        messages = await conv_manager.get_messages(conversation_id)
        
        # Build conversation history
        history = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]
        
        # ===== RAG CONTEXT RETRIEVAL =====
        # Use RAG Manager for unified context retrieval
        rag_context = await rag_manager.get_context_for_query(
            user_query=user_message,
            user_id=client_id,
            conversation_id=conversation_id,
            include_memories=True,
            include_past_conversations=True,
            max_items=5
        )
        
        logger.info(f"RAG context: {rag_context['metadata']['memory_hits']} memories, "
                    f"{rag_context['metadata']['conversation_hits']} past convos")
        
        # Get current date/time for AI context
        from datetime import datetime
        import pytz
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            datetime_context = f"""=== CURRENT DATE & TIME ===
Today is {now.strftime('%A, %B %d, %Y')}
Current time is {now.strftime('%I:%M %p')} IST
Current year: {now.year}"""
        except Exception:
            now = datetime.now()
            datetime_context = f"""=== CURRENT DATE & TIME ===
Today is {now.strftime('%A, %B %d, %Y')}
Current time is {now.strftime('%I:%M %p')}
Current year: {now.year}"""
        
        # Build comprehensive system context with RAG-enhanced memory
        system_context = f"""You are AIZEN, a highly capable AI assistant with system-level access.

{datetime_context}

{rag_context['full_context']}

You can perform system operations like:
- Opening websites and URLs (use open_url tool)
- Starting applications (use start_process tool)
- Managing processes (use list_processes, kill_process tools)
- File operations (use read_file, write_file, search_files, delete_file tools)
- Getting system information (use get_system_stats, get_cpu_info, etc.)
- Desktop automation (use type_text, press_key tools)

When the user asks you to do something that requires a system operation, use the appropriate tool.
For example:
- "open YouTube" -> use open_url with https://youtube.com
- "open notepad" -> use start_process with "notepad.exe"
- "show running processes" -> use list_processes
- "how's my CPU?" -> use get_cpu_info
        """
        
        history.insert(0, {"role": "system", "content": system_context})
        
        # Analyze intent and select model
        intent = await task_planner.analyze_intent(user_message, history)
        
        # Get model selection from metadata or use intelligent routing
        model_provider = metadata.get("model_provider")
        model_name = metadata.get("model_name")
        
        if use_ollama:
            # Backward compatibility
            provider = ModelProvider.OLLAMA
            model = None
        elif model_provider and model_name:
            # Manual override
            try:
                provider = ModelProvider(model_provider)
                model = model_name
            except ValueError:
                provider, model = await task_planner.select_model_provider(intent)
        else:
            # Intelligent routing
            provider, model = await task_planner.select_model_provider(intent)
        
        # Send thinking status with model info
        await manager.send_message(client_id, {
            "type": "thinking",
            "conversation_id": conversation_id,
            "intent": intent,
            "selected_provider": str(provider),
            "selected_model": model
        })
        
        # Check if tools are needed
        tools_to_use = None
        if intent.get("requires_tools") or "open" in user_message.lower() or "start" in user_message.lower():
            tools_to_use = SYSTEM_TOOLS
            await manager.send_message(client_id, {
                "type": "tool_execution",
                "tools": [tool["function"]["name"] for tool in SYSTEM_TOOLS]
            })
        
        # If we have an image or audio, force Gemini provider (multimodal)
        if image_data or audio_data:
            provider = ModelProvider.GEMINI
            model = "gemini-2.5-flash"  # Use flash for multimodal - fast and supports images/audio
            tools_to_use = None  # No tools when doing multimodal for now
            if audio_data:
                logger.info(f"Forcing Gemini provider for audio analysis")
            else:
                logger.info(f"Forcing Gemini provider for image analysis")
        
        # Stream response
        full_response = ""
        tool_calls = []
        pending_operations = []
        
        await manager.send_message(client_id, {
            "type": "stream_start",
            "conversation_id": conversation_id,
            "provider": str(provider),
            "model": model
        })
        
        try:
            # Generate AI response with tools if needed
            async for chunk in ai_brain.stream_generate(
                messages=history,
                temperature=metadata.get("temperature", 0.7),
                max_tokens=metadata.get("max_tokens"),
                provider=provider,
                model=model,
                tools=tools_to_use,
                image_data=image_data,  # Pass image data
                audio_data=audio_data   # Pass audio data
            ):
                # Check if chunk contains tool calls
                if isinstance(chunk, dict) and "tool_calls" in chunk:
                    tool_calls.extend(chunk["tool_calls"])
                    continue
                
                full_response += chunk
                
                # Send chunk
                await manager.send_message(client_id, {
                    "type": "token",
                    "content": chunk,
                    "conversation_id": conversation_id
                })
        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            await manager.send_message(client_id, {
                "type": "error",
                "error": str(e),
                "conversation_id": conversation_id
            })
            return
        
        # Execute tool calls if any
        tool_results = []
        if tool_calls:
            logger.info(f"Executing {len(tool_calls)} tool calls")
            for tool_call in tool_calls:
                tool_name = tool_call.get("function", {}).get("name")
                tool_params = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                
                logger.info(f"Tool call: {tool_name} with params: {tool_params}")
                
                # Execute tool
                result = await system_executor.execute_tool_call(
                    tool_name=tool_name,
                    parameters=tool_params,
                    user_id=client_id
                )
                
                tool_results.append(result)
                
                # Check if operation is pending approval
                if result.get("status") == "pending_approval":
                    # Get operation details from security manager
                    op_id = result.get("operation_id")
                    operation = system_executor.security_manager.pending_operations.get(op_id)
                    
                    if operation:
                        pending_operations.append({
                            "operation_id": op_id,
                            "tool": tool_name,
                            "parameters": tool_params,
                            "message": result.get("message", "Approval required"),
                            "risk_level": operation.risk_level.value
                        })
                        
                        # Send approval request to frontend
                        await manager.send_message(client_id, {
                            "type": "operation_approval_required",
                            "operation_id": op_id,
                            "tool": tool_name,
                            "parameters": tool_params,
                            "message": result.get("message"),
                            "risk_level": operation.risk_level.value
                        })
                
                # If operation completed, add result to response
                elif result.get("status") == "completed":
                    tool_result_text = f"\n\n[System: {tool_name} completed successfully]"
                    full_response += tool_result_text
                    
                    await manager.send_message(client_id, {
                        "type": "token",
                        "content": tool_result_text,
                        "conversation_id": conversation_id
                    })
        
        # Save assistant message first
        assistant_msg_id = await conv_manager.add_message(
            conversation_id,
            "assistant",
            full_response
        )
        
        # ===== POST-CONVERSATION RAG PROCESSING =====
        # Use RAG Manager to extract facts and index the conversation
        try:
            rag_result = await rag_manager.process_conversation_exchange(
                user_message=user_message,
                assistant_response=full_response,
                conversation_id=conversation_id,
                user_id=client_id,
                metadata={"client_id": client_id}
            )
            if rag_result["facts_extracted"] > 0 or rag_result["indexed"]:
                logger.info(f"RAG processed: {rag_result['facts_extracted']} facts, "
                            f"indexed={rag_result['indexed']}, summarized={rag_result['summarized']}")
        except Exception as e:
            logger.error(f"RAG processing failed: {e}")
        
        # Send completion
        completion_metadata = {
            "provider": str(provider),
            "model": model
        }
        
        # Add pending operations to metadata if any
        if pending_operations:
            completion_metadata["pending_operations"] = pending_operations
        
        await manager.send_message(client_id, {
            "type": "complete",
            "conversation_id": conversation_id,
            "message_id": assistant_msg_id,
            "full_response": full_response,
            "provider": str(provider),
            "model": model,
            "metadata": completion_metadata
        })
        
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        await manager.send_message(client_id, {
            "type": "error",
            "error": str(e)
        })
