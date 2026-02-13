import logging
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import AsyncOpenAI
import aiohttp
import google.generativeai as genai
from groq import AsyncGroq
from app.config import get_settings
from app.core.model_router import ModelProvider, ModelRouter

logger = logging.getLogger(__name__)

class AIBrain:
    """AI model interface supporting Gemini, Groq, Perplexity, and Ollama"""
    
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        self.perplexity_client = None
        self.ollama_available = False
        self.model_router = ModelRouter()
    async def initialize(self):
        """Initialize AI clients"""
        settings = get_settings()

        # Initialize Gemini
        if settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini_client = genai
                logger.info("Gemini API client initialized")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}")

        # Initialize Groq (OpenAI-compatible)
        if settings.groq_api_key:
            try:
                self.groq_client = AsyncGroq(api_key=settings.groq_api_key)
                logger.info("Groq API client initialized")
            except Exception as e:
                logger.warning(f"Groq initialization failed: {e}")

        # Initialize Perplexity (OpenAI-compatible)
        if settings.perplexity_api_key:
            self.perplexity_client = AsyncOpenAI(
                api_key=settings.perplexity_api_key,
                base_url=settings.perplexity_base_url
            )
            logger.info("Perplexity API client initialized")

        # Check Ollama availability
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{settings.ollama_host}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=2),
                ) as resp:
                    if resp.status == 200:
                        self.ollama_available = True
                        logger.info("Ollama is available")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self.ollama_available = False
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        use_ollama: bool = False,
        provider: Optional[ModelProvider] = None
    ) -> Dict[str, Any]:
        """
        Generate response from AI model
        
        Args:
            messages: Conversation messages
            model: Model name (optional, will be determined by router if not provided)
            temperature: Response randomness (0.0-2.0)
            max_tokens: Maximum tokens in response
            tools: Available tools for function calling
            use_ollama: Backward compatibility flag to force Ollama
            provider: Specific provider to use (optional)
            
        Returns:
            Response dict with choices and message content
        """
        try:
            settings = get_settings()
            # Backward compatibility: use_ollama
            if use_ollama:
                provider = ModelProvider.OLLAMA
                model = model or settings.ollama_model
            
            # Route to appropriate provider
            if provider == ModelProvider.GEMINI and self.gemini_client:
                return await self._gemini_generate(messages, model, temperature, max_tokens, tools)
            elif provider == ModelProvider.GROQ and self.groq_client:
                return await self._groq_generate(messages, model, temperature, max_tokens, tools)
            elif provider == ModelProvider.PERPLEXITY and self.perplexity_client:
                return await self._perplexity_generate(messages, model, temperature, max_tokens, tools)
            elif provider == ModelProvider.OLLAMA and self.ollama_available:
                return await self._ollama_generate(messages, model, temperature, max_tokens)
            else:
                raise Exception(f"Provider {provider} not available or not configured")
                
        except Exception as e:
            logger.error(f"AI generation error with {provider}/{model}: {e}")
            # Try fallback to Ollama
            if provider != ModelProvider.OLLAMA and self.ollama_available:
                logger.info("Falling back to Ollama")
                return await self._ollama_generate(messages, model or settings.ollama_model, temperature, max_tokens)
            raise
    
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        use_ollama: bool = False,
        provider: Optional[ModelProvider] = None,
        image_data: Optional[Dict[str, Any]] = None  # For vision requests
    ) -> AsyncGenerator[str, None]:
        """Stream response from AI model"""
        try:
            settings = get_settings()
            # Backward compatibility: use_ollama
            if use_ollama:
                provider = ModelProvider.OLLAMA
                model = model or settings.ollama_model
            # If we have image data, force Gemini for vision
            if image_data:
                provider = ModelProvider.GEMINI
                logger.info(f"Processing image with Gemini Vision: {image_data.get('name')}")
            
            # Route to appropriate provider
            if provider == ModelProvider.GEMINI and self.gemini_client:
                async for chunk in self._gemini_stream(messages, model, temperature, max_tokens, tools, image_data):
                    yield chunk
            elif provider == ModelProvider.GROQ and self.groq_client:
                async for chunk in self._groq_stream(messages, model, temperature, max_tokens, tools):
                    yield chunk
            elif provider == ModelProvider.PERPLEXITY and self.perplexity_client:
                async for chunk in self._perplexity_stream(messages, model, temperature, max_tokens, tools):
                    yield chunk
            elif provider == ModelProvider.OLLAMA and self.ollama_available:
                async for chunk in self._ollama_stream(messages, model, temperature, max_tokens):
                    yield chunk
            else:
                raise Exception(f"Provider {provider} not available for streaming")
                
        except Exception as e:
            logger.error(f"AI streaming error with {provider}/{model}: {e}")
            # Try fallback to Ollama
            if provider != ModelProvider.OLLAMA and self.ollama_available:
                logger.info("Falling back to Ollama for streaming")
                async for chunk in self._ollama_stream(messages, model or settings.ollama_model, temperature, max_tokens):
                    yield chunk
    
    # ============ GEMINI METHODS ============
    
    def _convert_tools_to_gemini_format(self, tools):
        """Convert OpenAI function calling format to Gemini format"""
        if not tools:
            return None
        
        gemini_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                gemini_tools.append(genai.types.FunctionDeclaration(
                    name=func["name"],
                    description=func["description"],
                    parameters=func["parameters"]
                ))
        
        return [genai.types.Tool(function_declarations=gemini_tools)] if gemini_tools else None
    
    async def _gemini_generate(self, messages, model, temperature, max_tokens, tools=None):
        """Generate using Gemini API with optional function calling"""
        try:
            settings = get_settings()
            # Map model name
            model_name = self.model_router.map_gemini_model_name(model or settings.model_chat)

            # Convert messages to native Gemini Content format
            system_instruction, gemini_contents = self._convert_to_gemini_messages(messages)

            # Convert tools to Gemini format
            gemini_tools = self._convert_tools_to_gemini_format(tools)

            # Create model instance with system instruction
            model_kwargs = {"tools": gemini_tools}
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction

            model_instance = self.gemini_client.GenerativeModel(
                model_name, **model_kwargs
            )

            # Generate with proper Content list
            response = await model_instance.generate_content_async(
                gemini_contents,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            # Check for function calls in response
            tool_calls = []
            if hasattr(response.candidates[0].content, "parts"):
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        tool_calls.append(
                            {
                                "id": f"call_{part.function_call.name}",
                                "type": "function",
                                "function": {
                                    "name": part.function_call.name,
                                    "arguments": json.dumps(
                                        dict(part.function_call.args)
                                    ),
                                },
                            }
                        )

            # Get text content
            content = response.text if hasattr(response, "text") else ""

            # Convert to OpenAI-compatible format
            result = {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": content,
                        }
                    }
                ],
                "model": model_name,
                "provider": "gemini",
            }
            if tool_calls:
                result["choices"][0]["message"]["tool_calls"] = tool_calls

            return result
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise
    
    async def _gemini_stream(self, messages, model, temperature, max_tokens, tools=None, image_data=None):
        """Stream using Gemini API with optional function calling and vision"""
        try:
            import base64

            settings = get_settings()
            # Map model name
            model_name = self.model_router.map_gemini_model_name(model or settings.model_chat)

            # Convert messages to native Gemini Content format
            system_instruction, gemini_contents = self._convert_to_gemini_messages(messages)

            # Convert tools to Gemini format (skip if processing image)
            gemini_tools = None if image_data else self._convert_tools_to_gemini_format(tools)

            # Create model instance with system instruction
            model_kwargs = {"tools": gemini_tools}
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction

            model_instance = self.gemini_client.GenerativeModel(
                model_name, **model_kwargs
            )

            # Build content for generation
            if image_data:
                # Multimodal request with image
                logger.info(f"Creating multimodal request with image: {image_data.get('name')}")
                image_bytes = base64.b64decode(image_data["data"])
                image_part = {
                    "mime_type": image_data.get("type", "image/jpeg"),
                    "data": image_bytes,
                }
                # Last user turn text + image
                last_text = gemini_contents[-1]["parts"][0] if gemini_contents else ""
                content = [last_text, image_part]
            else:
                # Text-only request — pass native Content list
                content = gemini_contents

            # Stream generate
            response = await model_instance.generate_content_async(
                content,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
                stream=True,
            )
            
            # Track tool calls
            tool_calls = []
            
            async for chunk in response:
                try:
                    # Check if chunk has candidates with content
                    if not hasattr(chunk, 'candidates') or not chunk.candidates:
                        continue
                    
                    candidate = chunk.candidates[0]
                    if not hasattr(candidate, 'content') or not candidate.content:
                        continue
                    
                    if not hasattr(candidate.content, 'parts') or not candidate.content.parts:
                        continue
                    
                    # Process each part
                    for part in candidate.content.parts:
                        # Check for function calls FIRST (before trying to access text)
                        if hasattr(part, 'function_call') and part.function_call:
                            # Buffer function call - don't try to convert to text
                            tool_calls.append({
                                "id": f"call_{part.function_call.name}",
                                "type": "function",
                                "function": {
                                    "name": part.function_call.name,
                                    "arguments": json.dumps(dict(part.function_call.args))
                                }
                            })
                            logger.info(f"Gemini function call detected: {part.function_call.name}")
                        # Only try to yield text if part has text content
                        elif hasattr(part, 'text') and part.text:
                            yield part.text
                            
                except Exception as chunk_error:
                    # Log but don't fail on individual chunk errors
                    logger.warning(f"Error processing Gemini chunk: {chunk_error}")
                    continue
            
            # Yield tool calls at the end if any
            if tool_calls:
                logger.info(f"Yielding {len(tool_calls)} tool calls from Gemini stream")
                yield {"tool_calls": tool_calls}
                
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise
    
    def _convert_to_gemini_messages(
        self, messages: List[Dict[str, str]]
    ) -> tuple:
        """
        Convert OpenAI-style messages to native Gemini Content format.

        Returns:
            (system_instruction, contents)
            - system_instruction: str or None (extracted from 'system' role)
            - contents: list of {"role": "user"|"model", "parts": [str]} dicts
        """
        system_parts: list[str] = []
        contents: list[dict] = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if not content:
                continue

            if role == "system":
                system_parts.append(content)
            elif role == "user":
                contents.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                # Gemini uses "model" for assistant turns
                contents.append({"role": "model", "parts": [content]})
            elif role == "tool":
                # Tool results go as user messages in Gemini
                contents.append({"role": "user", "parts": [content]})

        # Gemini requires alternating user/model turns.
        # Merge consecutive same-role entries.
        merged: list[dict] = []
        for c in contents:
            if merged and merged[-1]["role"] == c["role"]:
                merged[-1]["parts"].extend(c["parts"])
            else:
                merged.append(c)

        system_instruction = "\n\n".join(system_parts) if system_parts else None
        return system_instruction, merged
    
    # ============ GROQ METHODS ============
    
    async def _groq_generate(self, messages, model, temperature, max_tokens, tools):
        """Generate using Groq API"""
        settings = get_settings()
        model_name = self.model_router.map_groq_model_name(model or settings.model_fast_streaming)
        
        response = await self.groq_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        result = {
            "choices": [{
                "message": {
                    "role": response.choices[0].message.role,
                    "content": response.choices[0].message.content
                }
            }],
            "model": model_name,
            "provider": "groq"
        }
        return result
    
    async def _groq_stream(self, messages, model, temperature, max_tokens, tools):
        """Stream using Groq API"""
        settings = get_settings()
        model_name = self.model_router.map_groq_model_name(model or settings.model_fast_streaming)
        
        # Add tools to request if provided
        request_params = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"
        
        stream = await self.groq_client.chat.completions.create(**request_params)
        
        # Track tool calls across chunks
        tool_calls_buffer = {}
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle tool calls
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                for tool_call in delta.tool_calls:
                    idx = tool_call.index
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": tool_call.id or "",
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name or "",
                                "arguments": ""
                            }
                        }
                    
                    # Accumulate function arguments
                    if tool_call.function.arguments:
                        tool_calls_buffer[idx]["function"]["arguments"] += tool_call.function.arguments
            
            # Handle text content
            elif delta.content:
                yield delta.content
        
        # Yield tool calls at the end if any were collected
        if tool_calls_buffer:
            yield {"tool_calls": list(tool_calls_buffer.values())}
    
    # ============ PERPLEXITY METHODS ============
    
    async def _perplexity_generate(self, messages, model, temperature, max_tokens, tools):
        """Generate using Perplexity API"""
        settings = get_settings()
        model_name = self.model_router.map_perplexity_model_name(model or settings.model_search)
        
        response = await self.perplexity_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.model_dump()
    
    async def _perplexity_stream(self, messages, model, temperature, max_tokens, tools):
        """Stream using Perplexity API"""
        settings = get_settings()
        model_name = self.model_router.map_perplexity_model_name(model or settings.model_search)
        
        stream = await self.perplexity_client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    # ============ OLLAMA METHODS ============
    
    async def _ollama_generate(self, messages, model, temperature, max_tokens):
        """Generate using Ollama"""
        settings = get_settings()
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model or settings.ollama_model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature},
            }

            async with session.post(
                f"{settings.ollama_host}/api/chat", json=payload
            ) as resp:
                result = await resp.json()
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": result.get("message", {}).get(
                                    "content", ""
                                ),
                            }
                        }
                    ],
                    "model": model,
                    "provider": "ollama",
                }
    
    async def _ollama_stream(self, messages, model, temperature, max_tokens):
        """Stream using Ollama"""
        settings = get_settings()
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model or settings.ollama_model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature},
            }

            async with session.post(
                f"{settings.ollama_host}/api/chat", json=payload
            ) as resp:
                async for line in resp.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
