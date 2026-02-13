from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class Message(BaseModel):
    role: str = Field(..., description="Role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., description="User message")
    use_ollama: bool = Field(False, description="Force use of Ollama (backward compatibility)")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None
    # New fields for multi-provider support
    model_provider: Optional[str] = Field(None, description="Specific provider: gemini, groq, perplexity, ollama")
    model_name: Optional[str] = Field(None, description="Specific model name to use")
    preferred_provider: Optional[str] = Field(None, description="Preferred provider if available")

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    role: str = "assistant"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    # New fields for provider info
    provider: Optional[str] = None
    model: Optional[str] = None

class ConversationCreate(BaseModel):
    title: str = Field(..., description="Conversation title")
    metadata: Optional[Dict[str, Any]] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    tool_calls: List[Dict[str, Any]]

class MemoryUpdate(BaseModel):
    key: str
    value: Any
    
class FactStore(BaseModel):
    content: str
    metadata: Optional[Dict[str, Any]] = None

class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt")
    model: Optional[str] = Field("imagen-4-ultra", description="Image model to use")
    size: Optional[str] = Field("1024x1024", description="Image size")
    quality: Optional[str] = Field("standard", description="Image quality: standard or hd")

class ModelSelectRequest(BaseModel):
    task_type: str = Field(..., description="Type of task: coding, chat, search, research, etc.")
    manual_provider: Optional[str] = None
    manual_model: Optional[str] = None

# Core Memory Models
class CoreFactCreate(BaseModel):
    """Model for creating a new core memory fact"""
    fact: str = Field(..., description="The fact or knowledge to remember")
    category: str = Field("learned", description="Category: identity, preference, user_info, learned")
    importance: str = Field("normal", description="Importance: critical, high, normal")

class CoreFactUpdate(BaseModel):
    """Model for updating an existing core memory fact"""
    fact_id: str = Field(..., description="ID of the fact to update")
    new_fact: str = Field(..., description="Updated fact content")

class CoreFactDelete(BaseModel):
    """Model for deleting a core memory fact"""
    fact_id: str = Field(..., description="ID of the fact to delete")

class CoreMemoryClear(BaseModel):
    """Model for clearing core memory"""
    keep_identity: bool = Field(True, description="Keep system identity facts when clearing")

