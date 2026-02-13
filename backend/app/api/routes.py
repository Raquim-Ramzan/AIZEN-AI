from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Depends
from typing import List, Dict, Any
import logging
import json

from app.api.models import (
    ChatRequest, ChatResponse, ConversationCreate, ConversationResponse,
    MessageResponse, MemoryUpdate, FactStore, ToolExecuteRequest,
    ImageGenerateRequest, ModelSelectRequest,
    CoreFactCreate, CoreFactUpdate, CoreFactDelete, CoreMemoryClear
)
from app.memory.conversation import ConversationManager
from app.core.planner import TaskPlanner
from app.core.executor import ToolExecutor
from app.core.model_router import ModelProvider, TaskType
from app.tools import WebSearchTool, FileOpsTool, CodeExecTool, CalendarTool, SystemTool
from app.core.system_tools import SYSTEM_TOOLS, get_tool_by_name
from app.core.system_executor import get_system_executor
from app.api.auth import require_api_key
import base64

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize tools and executor
tool_executor = ToolExecutor()
tool_executor.register_tool(WebSearchTool())
tool_executor.register_tool(FileOpsTool())
tool_executor.register_tool(CodeExecTool())
tool_executor.register_tool(CalendarTool())
tool_executor.register_tool(SystemTool())

task_planner = TaskPlanner()

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(request: Request, limit: int = 50, user_id: str = Depends(require_api_key)):
    """Get all conversations"""
    try:
        conv_manager = request.app.state.conv_manager
        conversations = await conv_manager.get_conversations(user_id, limit)
        return conversations
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: Request, conv: ConversationCreate, user_id: str = Depends(require_api_key)):
    """Create a new conversation"""
    try:
        conv_manager = request.app.state.conv_manager
        conv_id = await conv_manager.create_conversation(user_id, conv.title, conv.metadata)
        conversation = await conv_manager.get_conversation(user_id, conv_id)
        return conversation
    except Exception as e:
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(request: Request, conversation_id: str, user_id: str = Depends(require_api_key)):
    """Get a specific conversation"""
    try:
        conv_manager = request.app.state.conv_manager
        conversation = await conv_manager.get_conversation(user_id, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(request: Request, conversation_id: str, user_id: str = Depends(require_api_key)):
    """Delete a conversation"""
    try:
        conv_manager = request.app.state.conv_manager
        await conv_manager.delete_conversation(user_id, conversation_id)
        return {"status": "deleted", "conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(request: Request, conversation_id: str, conv: ConversationCreate, user_id: str = Depends(require_api_key)):
    """Update a conversation (e.g., rename)"""
    try:
        conv_manager = request.app.state.conv_manager
        
        # Update the conversation title
        success = await conv_manager.update_conversation_title(user_id, conversation_id, conv.title)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Return the updated conversation
        conversation = await conv_manager.get_conversation(user_id, conversation_id)
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(request: Request, conversation_id: str, limit: int = 100, user_id: str = Depends(require_api_key)):
    """Get messages from a conversation"""
    try:
        conv_manager = request.app.state.conv_manager
        messages = await conv_manager.get_messages(conversation_id, limit)
        return messages
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat(
    request: Request,
    chat_req: ChatRequest,
    user_id: str = Depends(require_api_key),
) -> ChatResponse:
    """Non-streaming chat endpoint with system operation support"""
    try:
        ai_brain = request.app.state.ai_brain
        core_memory = request.app.state.core_memory
        vector_store = request.app.state.vector_store
        conv_manager = request.app.state.conv_manager
        system_executor = get_system_executor()
        
        # Create conversation if needed
        if not chat_req.conversation_id:
            chat_req.conversation_id = await conv_manager.create_conversation(
                user_id=user_id,
                title=chat_req.message[:50],
                metadata={}
            )
        
        # Add user message
        await conv_manager.add_message(
            chat_req.conversation_id,
            "user",
            chat_req.message
        )
        
        # Get context
        messages = await conv_manager.get_messages(chat_req.conversation_id)
        
        # Build conversation history
        history = [{"role": m["role"], "content": m["content"]} for m in messages[-10:]]
        
        # ===== RAG CONTEXT RETRIEVAL =====
        # Use RAG Manager for unified context retrieval
        rag_manager = request.app.state.rag_manager
        rag_context = await rag_manager.get_context_for_query(
            user_query=chat_req.message,
            user_id=user_id,
            conversation_id=chat_req.conversation_id,
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
        except:
            now = datetime.now()
            datetime_context = f"""=== CURRENT DATE & TIME ===
Today is {now.strftime('%A, %B %d, %Y')}
Current time is {now.strftime('%I:%M %p')}
Current year: {now.year}"""
        
        # Add context to system message with RAG-enhanced memory
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
        
        # Generate response with intelligent routing
        intent = await task_planner.analyze_intent(chat_req.message, history)
        
        # Determine provider and model
        if chat_req.model_provider and chat_req.model_name:
            # Manual override
            try:
                provider = ModelProvider(chat_req.model_provider)
                model = chat_req.model_name
            except ValueError:
                provider, model = await task_planner.select_model_provider(intent)
        else:
            # Intelligent routing
            provider, model = await task_planner.select_model_provider(
                intent,
                manual_provider=chat_req.preferred_provider
            )
        
        # Backward compatibility with use_ollama
        if chat_req.use_ollama:
            provider = ModelProvider.OLLAMA
            model = None
        
        # Call AI with tools enabled (for providers that support it)
        # Gemini, Groq, and Perplexity all support function calling
        tools_param = SYSTEM_TOOLS if provider in [ModelProvider.GEMINI, ModelProvider.GROQ, ModelProvider.PERPLEXITY] else None
        
        response = await ai_brain.generate(
            messages=history,
            temperature=chat_req.temperature,
            max_tokens=chat_req.max_tokens,
            provider=provider,
            model=model,
            tools=tools_param
        )
        
        assistant_message = response["choices"][0]["message"]["content"]
        used_provider = response.get("provider", str(provider))
        used_model = response.get("model", model)
        
        # Check if AI made a tool call
        tool_calls = response["choices"][0]["message"].get("tool_calls", [])
        pending_operations = []
        
        if tool_calls:
            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                logger.info(f"AI requested tool call: {func_name} with {func_args}")
                
                # Execute the system operation
                result = await system_executor.execute_tool_call(
                    func_name,
                    func_args,
                    user_id=user_id,
                )
                
                if result.get("status") == "pending_approval":
                    # Operation needs approval - add to pending list
                    pending_operations.append({
                        "operation_id": result["operation_id"],
                        "tool": func_name,
                        "parameters": func_args,
                        "message": result.get("message")
                    })
                elif result.get("success"):
                    # Operation completed - append result to message
                    assistant_message += f"\n\n✅ {result.get('message', 'Operation completed successfully')}"
                else:
                    # Operation failed
                    assistant_message += f"\n\n❌ Error: {result.get('error')}"
        
        # If we have pending operations, modify the message
        if pending_operations:
            assistant_message += "\n\n⏳ Some operations require your approval. Please check the approval dialog."
        
        msg_id = await conv_manager.add_message(
            chat_req.conversation_id,
            "assistant",
            assistant_message,
            metadata={
                "provider": used_provider,
                "model": used_model,
                "tool_calls": [tc["function"]["name"] for tc in tool_calls] if tool_calls else [],
                "pending_operations": pending_operations
            }
        )
        
        # ===== POST-CONVERSATION RAG PROCESSING =====
        # Use RAG Manager to extract facts and index the conversation
        try:
            rag_result = await rag_manager.process_conversation_exchange(
                user_message=chat_req.message,
                assistant_response=assistant_message,
                conversation_id=chat_req.conversation_id,
                user_id=user_id
            )
            if rag_result["facts_extracted"] > 0 or rag_result["indexed"]:
                logger.info(f"RAG processed: {rag_result['facts_extracted']} facts, "
                            f"indexed={rag_result['indexed']}")
        except Exception as e:
            logger.error(f"RAG processing failed: {e}")
        
        return ChatResponse(
            conversation_id=chat_req.conversation_id,
            message_id=msg_id,
            content=assistant_message,
            provider=used_provider,
            model=used_model,
            metadata={
                "tool_calls": tool_calls,
                "pending_operations": pending_operations
            } if (tool_calls or pending_operations) else None
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/core")
async def get_core_memory(request: Request, user_id: str = Depends(require_api_key)):
    """Get core memory"""
    try:
        core_memory = request.app.state.core_memory
        memory = await core_memory.get_memory(user_id)
        return memory
    except Exception as e:
        logger.error(f"Get core memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/preference")
async def update_preference(request: Request, update: MemoryUpdate, user_id: str = Depends(require_api_key)):
    """Update user preference"""
    try:
        core_memory = request.app.state.core_memory
        await core_memory.add_preference(user_id, update.key, update.value)
        return {"status": "updated", "key": update.key}
    except Exception as e:
        logger.error(f"Update preference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/fact")
async def store_fact(request: Request, fact: FactStore, user_id: str = Depends(require_api_key)):
    """Store a fact in memory"""
    try:
        vector_store = request.app.state.vector_store
        core_memory = request.app.state.core_memory
        
        doc_id = await vector_store.add_document(fact.content, user_id, fact.metadata)
        await core_memory.add_learned_knowledge(user_id, fact.content)
        
        return {"status": "stored", "id": doc_id}
    except Exception as e:
        logger.error(f"Store fact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/search")
async def search_memory(request: Request, query: str, limit: int = 5, user_id: str = Depends(require_api_key)):
    """Search memory"""
    try:
        vector_store = request.app.state.vector_store
        results = await vector_store.search(query, user_id, limit)
        return {"query": query, "results": results}
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Core Memory CRUD Endpoints
# ============================================

@router.get("/memory/facts")
async def get_core_facts(request: Request, user_id: str = Depends(require_api_key)):
    """Get all core memory facts"""
    try:
        core_memory = request.app.state.core_memory
        facts = await core_memory.get_core_facts(user_id)
        return {"facts": facts, "count": len(facts)}
    except Exception as e:
        logger.error(f"Get core facts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/facts")
async def add_core_fact(request: Request, fact_data: CoreFactCreate, user_id: str = Depends(require_api_key)):
    """Add a new core memory fact"""
    try:
        core_memory = request.app.state.core_memory
        result = await core_memory.add_core_fact(
            user_id=user_id,
            fact=fact_data.fact,
            category=fact_data.category,
            importance=fact_data.importance,
            source="user"
        )
        
        if result:
            return {"status": "created", "fact": result}
        else:
            return {"status": "duplicate", "message": "Fact already exists"}
    except Exception as e:
        logger.error(f"Add core fact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/memory/facts")
async def update_core_fact(request: Request, fact_data: CoreFactUpdate, user_id: str = Depends(require_api_key)):
    """Update an existing core memory fact"""
    try:
        core_memory = request.app.state.core_memory
        success = await core_memory.update_core_fact(
            user_id=user_id,
            fact_id=fact_data.fact_id,
            new_fact=fact_data.new_fact
        )
        
        if success:
            return {"status": "updated", "fact_id": fact_data.fact_id}
        else:
            raise HTTPException(status_code=404, detail="Fact not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update core fact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/memory/facts/{fact_id}")
async def delete_core_fact(request: Request, fact_id: str, user_id: str = Depends(require_api_key)):
    """Delete a core memory fact by ID"""
    try:
        core_memory = request.app.state.core_memory
        success = await core_memory.delete_core_fact(user_id, fact_id)
        
        if success:
            return {"status": "deleted", "fact_id": fact_id}
        else:
            raise HTTPException(status_code=404, detail="Fact not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete core fact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/facts/clear")
async def clear_core_facts(request: Request, clear_data: CoreMemoryClear, user_id: str = Depends(require_api_key)):
    """Clear all core memory facts"""
    try:
        core_memory = request.app.state.core_memory
        await core_memory.clear_all_facts(user_id, keep_identity=clear_data.keep_identity)
        return {
            "status": "cleared", 
            "keep_identity": clear_data.keep_identity
        }
    except Exception as e:
        logger.error(f"Clear core facts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def get_tools():
    """Get available tools"""
    try:
        tools = tool_executor.get_available_tools()
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Get tools error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/execute")
async def execute_tool(tool_req: ToolExecuteRequest):
    """Execute a tool"""
    try:
        result = await tool_executor.execute_tool(tool_req.tool_name, tool_req.parameters)
        return result
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_settings():
    """Get application settings"""
    from app.config import get_settings
    from app.core.model_router import ModelRouter
    
    settings = get_settings()
    router = ModelRouter()
    
    return {
        "providers": {
            "gemini": {
                "configured": bool(settings.gemini_api_key),
                "models": [settings.model_coding, settings.model_chat, settings.model_reasoning]
            },
            "groq": {
                "configured": bool(settings.groq_api_key),
                "models": [settings.model_fast_streaming]
            },
            "perplexity": {
                "configured": bool(settings.perplexity_api_key),
                "models": [settings.model_search, settings.model_research]
            },
            "ollama": {
                "configured": True,
                "models": [settings.ollama_model]
            }
        },
        "model_preferences": {
            "coding": settings.model_coding,
            "chat": settings.model_chat,
            "reasoning": settings.model_reasoning,
            "search": settings.model_search,
            "research": settings.model_research,
            "image": settings.model_image,
            "embedding": settings.model_embedding
        }
    }

@router.get("/models/available")
async def get_available_models():
    """Get all available models by provider"""
    from app.core.model_router import ModelRouter
    router = ModelRouter()
    return router.get_available_models()

@router.post("/models/select")
async def select_model(select_req: ModelSelectRequest):
    """Select optimal model for a task type"""
    from app.core.model_router import ModelRouter, TaskType
    
    try:
        task_type = TaskType(select_req.task_type)
        router = ModelRouter()
        
        provider, model = router.select_model(
            task_type,
            manual_provider=ModelProvider(select_req.manual_provider) if select_req.manual_provider else None,
            manual_model=select_req.manual_model
        )
        
        return {
            "task_type": select_req.task_type,
            "selected_provider": str(provider),
            "selected_model": model
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid task type: {e}")

@router.post("/image/generate", deprecated=True)
async def generate_image(request: Request, image_req: ImageGenerateRequest):
    """
    [DEPRECATED] Image generation endpoint.
    This endpoint is scheduled for removal in Phase 4.
    Use Gemini Vision for image analysis instead.
    """
    raise HTTPException(
        status_code=501, 
        detail="Image generation is deprecated. This feature will be implemented in Phase 4."
    )


# ============================================
# RAG (Retrieval-Augmented Generation) Endpoints
# ============================================

@router.get("/rag/stats")
async def get_rag_stats(request: Request, user_id: str = Depends(require_api_key)):
    """Get comprehensive RAG system statistics"""
    try:
        rag_manager = request.app.state.rag_manager
        if not rag_manager:
            raise HTTPException(status_code=500, detail="RAG Manager not initialized")
        
        stats = rag_manager.get_stats(user_id) if hasattr(rag_manager, 'get_stats_for_user') else rag_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Get RAG stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/rebuild")
async def rebuild_rag_index(request: Request, user_id: str = Depends(require_api_key)):
    """Rebuild the RAG vector index from core memory"""
    try:
        rag_manager = request.app.state.rag_manager
        if not rag_manager:
            raise HTTPException(status_code=500, detail="RAG Manager not initialized")
        
        result = await rag_manager.rebuild_vector_index(user_id)
        return {
            "status": "completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Rebuild RAG index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/search")
async def search_rag(request: Request, query: str, limit: int = 10):
    """Search across all RAG memory sources"""
    try:
        rag_manager = request.app.state.rag_manager
        if not rag_manager:
            raise HTTPException(status_code=500, detail="RAG Manager not initialized")
        
        results = await rag_manager.search_all_memory(query, limit=limit)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/context")
async def get_rag_context(request: Request, query: str, conversation_id: str = None):
    """Get RAG context for a query (preview what the AI would see)"""
    try:
        rag_manager = request.app.state.rag_manager
        if not rag_manager:
            raise HTTPException(status_code=500, detail="RAG Manager not initialized")
        
        context = await rag_manager.get_context_for_query(
            user_query=query,
            conversation_id=conversation_id,
            include_memories=True,
            include_past_conversations=True,
            max_items=5
        )
        return context
    except Exception as e:
        logger.error(f"Get RAG context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/summarize/{conversation_id}")
async def summarize_conversation(request: Request, conversation_id: str, force: bool = False):
    """Generate and store a summary for a conversation"""
    try:
        rag_manager = request.app.state.rag_manager
        if not rag_manager:
            raise HTTPException(status_code=500, detail="RAG Manager not initialized")
        
        summary = await rag_manager.summarize_conversation(conversation_id, force=force)
        
        if summary:
            return {
                "status": "completed",
                "conversation_id": conversation_id,
                "summary": summary
            }
        else:
            return {
                "status": "skipped",
                "conversation_id": conversation_id,
                "message": "Conversation too short or summarization failed"
            }
    except Exception as e:
        logger.error(f"Summarize conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# BACKUP & DATA MANAGEMENT
# =====================================================

@router.post("/backup/create")
async def create_backup(request: Request):
    """Create a full backup of all data stores"""
    try:
        from app.core.backup import get_backup_manager
        backup_manager = get_backup_manager()
        result = await backup_manager.create_full_backup()
        return result
    except Exception as e:
        logger.error(f"Backup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backup/list")
async def list_backups(request: Request):
    """List available backups"""
    try:
        from app.core.backup import get_backup_manager
        backup_manager = get_backup_manager()
        backups = await backup_manager.list_backups()
        return {"backups": backups}
    except Exception as e:
        logger.error(f"List backups error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_data(request: Request, format: str = "json"):
    """Export all data to a portable format"""
    try:
        from app.core.backup import get_backup_manager
        backup_manager = get_backup_manager()
        export_path = await backup_manager.export_data(format=format)
        return {"status": "success", "export_path": str(export_path)}
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# AUDIT LOG
# =====================================================

@router.get("/audit/logs")
async def get_audit_logs(
    request: Request,
    event_type: str = None,
    limit: int = 100
):
    """Get audit log entries"""
    try:
        from app.core.audit_logger import get_audit_logger, EventType
        audit_logger = await get_audit_logger()
        
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                pass
        
        events = await audit_logger.get_events(
            event_type=event_type_enum,
            limit=limit
        )
        return {"events": events}
    except Exception as e:
        logger.error(f"Audit log error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/stats")
async def get_audit_stats(request: Request):
    """Get audit log statistics"""
    try:
        from app.core.audit_logger import get_audit_logger
        audit_logger = await get_audit_logger()
        stats = await audit_logger.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Audit stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# CACHE MANAGEMENT
# =====================================================

@router.get("/cache/stats")
async def get_cache_stats(request: Request):
    """Get cache statistics"""
    try:
        from app.core.cache import get_all_cache_stats
        stats = get_all_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_caches(request: Request):
    """Clear all caches"""
    try:
        from app.core.cache import clear_all_caches
        clear_all_caches()
        return {"status": "success", "message": "All caches cleared"}
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# SMART MEMORY
# =====================================================

@router.post("/memory/add-smart")
async def add_smart_memory(request: Request, fact: str, importance: str = "normal"):
    """Add a fact with smart deduplication"""
    try:
        from app.memory.smart_memory import get_smart_memory_manager
        smart_memory = get_smart_memory_manager()
        result = await smart_memory.add_fact_smart(
            fact=fact,
            importance=importance,
            source="api"
        )
        return result
    except Exception as e:
        logger.error(f"Smart memory add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
