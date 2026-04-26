"""
Cloud Vector Store with Supabase + FastEmbed
============================================
Replaces ChromaDB and Gemini Embeddings with Supabase pgvector and FastEmbed.
This provides a scalable, cloud-native vector store with low-latency local embeddings.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastembed import TextEmbedding

from app.config import get_settings
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

# Relevance thresholds (lower distance = more relevant)
RELEVANCE_THRESHOLD_STRICT = 0.5  # Very relevant
RELEVANCE_THRESHOLD_NORMAL = 0.75  # Reasonably relevant
RELEVANCE_THRESHOLD_LOOSE = 1.0  # Somewhat relevant


class VectorStore:
    """Supabase vector store with support for Local (FastEmbed) or Cloud (Google) embeddings"""

    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.provider = "local"  # "local" or "google"
        self.model_name = ""
        self.dimensions = 384  # Default for bge-small

    async def initialize(self):
        """Initialize Supabase client and embedding provider"""
        settings = get_settings()
        self.model_name = settings.model_embedding or "BAAI/bge-small-en-v1.5"
        self.dimensions = 384  # Fixed for our Supabase schema

        try:
            self.client = get_supabase_client()
            if not self.client:
                logger.error("Supabase client not initialized. Vector store will be disabled.")
                return

            # Determine provider
            if "text-embedding" in self.model_name.lower():
                self.provider = "google"
                logger.info(f"Using Cloud Embeddings (Google): {self.model_name}")

                # Verify Gemini key
                if not settings.gemini_api_key:
                    logger.warning(
                        "GEMINI_API_KEY missing for cloud embeddings. Falling back to local."
                    )
                    self.provider = "local"
                    self.model_name = "BAAI/bge-small-en-v1.5"
            else:
                self.provider = "local"
                logger.info(f"Using Local Embeddings (FastEmbed): {self.model_name}")

            # Initialize local model if needed
            if self.provider == "local":
                logger.info(f"Loading local embedding model: {self.model_name}")
                try:
                    self.embedding_model = TextEmbedding(model_name=self.model_name)
                except Exception as local_e:
                    if settings.gemini_api_key:
                        logger.warning(
                            f"Failed to load local model '{self.model_name}': {local_e}. Falling back to Google Cloud."
                        )
                        self.provider = "google"
                        self.model_name = "text-embedding-004"
                    else:
                        raise local_e

            logger.info(f"Vector store initialized with {self.provider} provider and Supabase")

        except Exception as e:
            logger.error(f"Failed to initialize Vector Store: {e}")
            raise

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using the selected provider"""
        if self.provider == "local":
            return self._embed_local(texts)
        else:
            return self._embed_google(texts)

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using FastEmbed locally"""
        if not self.embedding_model:
            logger.error("Local embedding model not loaded")
            return [[0.0] * self.dimensions for _ in texts]

        try:
            embeddings_gen = self.embedding_model.embed(texts)
            return [embedding.tolist() for embedding in embeddings_gen]
        except Exception as e:
            logger.error(f"FastEmbed embedding error: {e}")
            return [[0.0] * self.dimensions for _ in texts]

    def _embed_google(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Google Generative AI Cloud API (fixed to 384d)"""
        try:
            import google.generativeai as genai

            settings = get_settings()
            genai.configure(api_key=settings.gemini_api_key)

            # Google supports batch embedding and custom dimensionality
            # We force 384 to match the Supabase VECTOR(384) schema
            result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=texts,
                task_type="retrieval_document",
                output_dimensionality=384,
            )

            return result["embeddings"] if "embeddings" in result else result["embedding"]
        except Exception as e:
            logger.error(f"Google Cloud embedding error: {e}")
            return [[0.0] * 384 for _ in texts]

    # =====================================================
    # MEMORY COLLECTION METHODS (Facts, Knowledge)
    # =====================================================

    async def add_document(
        self, content: str, user_id: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Add a document to the memories table"""
        if not self.client:
            return ""

        try:
            doc_id = str(uuid.uuid4())
            meta = metadata or {}

            # Generate embedding locally
            embedding = self._embed_texts([content])[0]

            data = {
                "id": doc_id,
                "user_id": user_id,
                "content": content,
                "metadata": meta,
                "embedding": embedding,
            }

            self.client.table("memories").insert(data).execute()
            logger.info(f"Added memory document: {content[:50]}...")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise

    async def add_documents(
        self, contents: list[str], user_id: str, metadatas: list[dict[str, Any]] | None = None
    ) -> list[str]:
        """Add multiple documents to memories table"""
        if not self.client or not contents:
            return []

        try:
            doc_ids = [str(uuid.uuid4()) for _ in contents]

            # Generate embeddings in batch locally
            embeddings = self._embed_texts(contents)

            records = []
            for i, content in enumerate(contents):
                meta = metadatas[i] if metadatas and i < len(metadatas) else {}
                records.append(
                    {
                        "id": doc_ids[i],
                        "user_id": user_id,
                        "content": content,
                        "metadata": meta,
                        "embedding": embeddings[i],
                    }
                )

            self.client.table("memories").insert(records).execute()
            logger.info(f"Added {len(doc_ids)} memory documents")
            return doc_ids
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        filter_metadata: dict[str, Any] | None = None,
        relevance_threshold: float = RELEVANCE_THRESHOLD_NORMAL,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents using Supabase RPC pgvector similarity search.
        """
        if not self.client:
            return []

        try:
            # 1. Generate query embedding locally
            query_embedding = self._embed_texts([query])[0]

            # 2. Call Supabase RPC function 'match_memories'
            response = self.client.rpc(
                "match_memories",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 1.0 - relevance_threshold,  # Convert distance to similarity
                    "match_count": limit,
                    "p_user_id": user_id,
                },
            ).execute()

            results = response.data
            formatted_results = []

            for item in results:
                formatted_results.append(
                    {
                        "id": item["id"],
                        "content": item["content"],
                        "metadata": item["metadata"],
                        "distance": 1.0 - item["similarity"],  # Convert similarity back to distance
                        "relevance_score": item["similarity"],
                    }
                )

            if formatted_results:
                logger.info(f"Found {len(formatted_results)} relevant results for: {query[:50]}...")

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    # =====================================================
    # CONVERSATION COLLECTION METHODS (RAG)
    # =====================================================

    async def index_conversation_exchange(
        self,
        user_message: str,
        assistant_response: str,
        conversation_id: str,
        user_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Index a conversation exchange for future retrieval.
        Using the 'memories' table but with specific metadata type.
        """
        try:
            response_preview = (
                assistant_response[:500] if len(assistant_response) > 500 else assistant_response
            )
            combined_text = f"User asked: {user_message}\nAizen responded: {response_preview}"

            meta = metadata or {}
            meta.update(
                {
                    "conversation_id": conversation_id,
                    "user_message": user_message[:200],
                    "type": "conversation_exchange",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            return await self.add_document(combined_text, user_id, meta)

        except Exception as e:
            logger.error(f"Failed to index conversation: {e}")
            return None

    async def index_conversation_summary(
        self, summary: str, conversation_id: str, user_id: str, message_count: int
    ) -> str:
        """Index a conversation summary for long-term memory"""
        try:
            meta = {
                "conversation_id": conversation_id,
                "type": "conversation_summary",
                "message_count": message_count,
                "timestamp": datetime.now(UTC).isoformat(),
            }
            return await self.add_document(summary, user_id, meta)

        except Exception as e:
            logger.error(f"Failed to index summary: {e}")
            return None

    async def search_conversations(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        relevance_threshold: float = RELEVANCE_THRESHOLD_NORMAL,
        exclude_conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search past conversations for relevant context.
        """
        # Search all memories and filter in python for now
        # For production, an RPC function like 'match_conversation_exchanges' can be created
        results = await self.search(query, user_id, limit * 3, None, relevance_threshold)

        filtered_results = []
        for res in results:
            meta = res.get("metadata", {})
            if meta.get("type") in ["conversation_exchange", "conversation_summary"]:
                if (
                    exclude_conversation_id
                    and meta.get("conversation_id") == exclude_conversation_id
                ):
                    continue
                filtered_results.append(res)
                if len(filtered_results) >= limit:
                    break

        return filtered_results

    # =====================================================
    # COMBINED RAG RETRIEVAL
    # =====================================================

    async def retrieve_context(
        self,
        query: str,
        user_id: str,
        conversation_id: str | None = None,
        max_memories: int = 3,
        max_conversations: int = 3,
    ) -> dict[str, Any]:
        """
        Unified context retrieval for RAG.
        Searches both memory and past conversations.
        """
        context = {"memories": [], "past_conversations": [], "formatted_context": ""}

        # Search all memories to get both facts and conversations
        all_results = await self.search(
            query,
            user_id,
            limit=max_memories + max_conversations * 2,
            relevance_threshold=RELEVANCE_THRESHOLD_NORMAL,
        )

        memories = []
        past_convs = []

        for res in all_results:
            meta = res.get("metadata", {})
            if meta.get("type") in ["conversation_exchange", "conversation_summary"]:
                if exclude_conversation_id := conversation_id:
                    if meta.get("conversation_id") == exclude_conversation_id:
                        continue
                if len(past_convs) < max_conversations:
                    past_convs.append(res)
            else:
                if len(memories) < max_memories:
                    memories.append(res)

        context["memories"] = memories
        context["past_conversations"] = past_convs

        # Format for LLM injection
        parts = []

        if memories:
            parts.append("=== RELEVANT KNOWLEDGE ===")
            for mem in memories:
                importance = mem.get("metadata", {}).get("importance", "normal")
                parts.append(f"• [{importance.upper()}] {mem['content']}")

        if past_convs:
            parts.append("\n=== RELEVANT PAST CONVERSATIONS ===")
            for conv in past_convs:
                user_msg = conv.get("metadata", {}).get("user_message", "")
                parts.append(f"• Previous exchange: {user_msg[:100]}...")

        context["formatted_context"] = "\n".join(parts) if parts else ""

        return context

    # =====================================================
    # MAINTENANCE METHODS
    # =====================================================

    async def delete_document(self, doc_id: str, user_id: str):
        """Delete a document from memory collection with user validation"""
        if not self.client:
            return
        try:
            self.client.table("memories").delete().eq("id", doc_id).eq("user_id", user_id).execute()
            logger.info(f"Deleted document {doc_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")

    async def clear(self, user_id: str):
        """Clear all documents for a user"""
        if not self.client:
            return
        try:
            self.client.table("memories").delete().eq("user_id", user_id).execute()
            logger.info(f"Vector store cleared for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")

    def get_stats(self, user_id: str) -> dict[str, Any]:
        """Get vector store statistics for a user"""
        if not self.client:
            return {}
        try:
            # We would need to execute count queries, this is a simplified version
            resp = (
                self.client.table("memories")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .execute()
            )
            count = resp.count if hasattr(resp, "count") and resp.count is not None else 0

            return {"total_memories": count, "embedding_model": self.model_name}
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Singleton instance
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the VectorStore singleton"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
