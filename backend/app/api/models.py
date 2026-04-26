from typing import Any

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(..., description="Role: user, assistant, system, tool")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str = Field(..., description="User message")
    use_ollama: bool = Field(False, description="Force use of Ollama (backward compatibility)")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    # New fields for multi-provider support
    model_provider: str | None = Field(
        None, description="Specific provider: gemini, groq, perplexity, ollama"
    )
    model_name: str | None = Field(None, description="Specific model name to use")
    preferred_provider: str | None = Field(None, description="Preferred provider if available")


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    role: str = "assistant"
    tool_calls: list[dict[str, Any]] | None = None
    # New fields for provider info
    provider: str | None = None
    model: str | None = None


class ConversationCreate(BaseModel):
    title: str = Field(..., description="Conversation title")
    metadata: dict[str, Any] | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any]


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: str
    metadata: dict[str, Any]
    tool_calls: list[dict[str, Any]]


class MemoryUpdate(BaseModel):
    key: str
    value: Any


class FactStore(BaseModel):
    content: str
    metadata: dict[str, Any] | None = None


class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: dict[str, Any]


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt")
    model: str | None = Field("imagen-4-ultra", description="Image model to use")
    size: str | None = Field("1024x1024", description="Image size")
    quality: str | None = Field("standard", description="Image quality: standard or hd")


class ModelSelectRequest(BaseModel):
    task_type: str = Field(..., description="Type of task: coding, chat, search, research, etc.")
    manual_provider: str | None = None
    manual_model: str | None = None


# Core Memory Models
class CoreFactCreate(BaseModel):
    """Model for creating a new core memory fact"""

    fact: str = Field(..., description="The fact or knowledge to remember")
    category: str = Field(
        "learned", description="Category: identity, preference, user_info, learned"
    )
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
