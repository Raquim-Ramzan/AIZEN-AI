import logging
from typing import Any

from app.memory.conversation import ConversationManager
from app.memory.core_memory import CoreMemory
from app.memory.vector_store import VectorStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """Unified memory management system"""

    def __init__(
        self,
        vector_store: VectorStore,
        core_memory: CoreMemory,
        conversation_manager: ConversationManager,
    ):
        self.vector_store = vector_store
        self.core_memory = core_memory
        self.conversation_manager = conversation_manager

    async def store_fact(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        """Store a fact in vector store and core memory"""
        # Add to vector store
        fact_id = await self.vector_store.add_document(content, metadata)

        # Add to core memory
        await self.core_memory.add_learned_knowledge(
            fact=content,
            confidence=metadata.get("confidence", 0.9) if metadata else 0.9,
            source=metadata.get("source", "conversation") if metadata else "conversation",
        )

        return fact_id

    async def search_memories(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search relevant memories"""
        results = await self.vector_store.search(query, limit=limit)
        return results

    async def get_context_for_conversation(
        self, conversation_id: str, query: str
    ) -> dict[str, Any]:
        """Get full context for a conversation including core memory and relevant facts"""
        # Get core memory
        core = await self.core_memory.get_memory()

        # Search relevant facts
        relevant_facts = await self.search_memories(query, limit=3)

        # Get conversation history
        messages = await self.conversation_manager.get_messages(conversation_id, limit=10)

        return {
            "core_memory": core,
            "relevant_facts": relevant_facts,
            "conversation_history": messages,
        }

    async def update_user_preference(self, key: str, value: Any):
        """Update user preference in core memory"""
        await self.core_memory.update_user_profile(key, value)

    async def summarize_conversation(self, conversation_id: str) -> str:
        """Create a summary of a conversation"""
        messages = await self.conversation_manager.get_messages(conversation_id)

        # Simple summarization logic
        summary_parts = []
        for msg in messages[-5:]:
            if msg["role"] == "user":
                summary_parts.append(f"User: {msg['content'][:100]}")
            elif msg["role"] == "assistant":
                summary_parts.append(f"Assistant: {msg['content'][:100]}")

        summary = " | ".join(summary_parts)

        # Store summary in core memory
        await self.core_memory.add_conversation_summary(conversation_id, summary)

        return summary
