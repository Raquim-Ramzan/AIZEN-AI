"""
Reranker for AIZEN RAG Pipeline
================================
Cloud-efficient reranking using Gemini's embedding similarity.

Instead of making an additional LLM generation call (which adds 600-1200ms
and is architecturally circular when Gemini is also the generator), we use
embedding cosine-similarity scoring. This is:
  - ~10x faster (single batch embed call vs. full generation)
  - Deterministic and cache-friendly
  - Architecturally sound (embeddings ≠ generation)

For production at scale, swap this for a dedicated reranking API
(Cohere Rerank, Jina Reranker, or Voyage AI).
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
import google.generativeai as genai
from app.config import get_settings
from app.core.cache import get_llm_response_cache

logger = logging.getLogger(__name__)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)


class Reranker:
    """
    Embedding-based reranker for improving retrieval precision.

    Embeds the query and each document, then scores by cosine similarity.
    Uses the same Gemini embedding model as the vector store for consistency.
    """

    def __init__(self):
        self.model_name = "text-embedding-004"
        self._initialized = False

    def initialize(self):
        """Initialize the reranker"""
        settings = get_settings()
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self._initialized = True
            logger.info("Reranker initialized with Gemini embeddings (non-LLM)")

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on embedding similarity to query.

        Args:
            query: User query
            documents: List of retrieved documents with 'content' field
            top_k: Number of documents to return
            min_score: Minimum relevance score (0-1)

        Returns:
            Reranked documents with added 'rerank_score' field
        """
        if not documents:
            return []

        if not self._initialized:
            # Return documents as-is with original scores
            return documents[:top_k]

        try:
            # Embed the query
            query_result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=query,
                task_type="retrieval_query",
            )
            query_embedding = query_result["embedding"]

            # Batch-embed all documents in a single API call
            doc_texts = [
                doc.get("content", doc.get("text", str(doc)))[:1000]
                for doc in documents
            ]
            doc_result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=doc_texts,
                task_type="retrieval_document",
            )
            doc_embeddings = doc_result["embedding"]
            # Single doc returns a flat list
            if doc_texts and not isinstance(doc_embeddings[0], list):
                doc_embeddings = [doc_embeddings]

            # Score each document by cosine similarity
            for i, doc in enumerate(documents):
                doc["rerank_score"] = _cosine_similarity(
                    query_embedding, doc_embeddings[i]
                )

            # Sort by rerank score descending
            documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            # Filter by minimum score and return top_k
            filtered = [
                d for d in documents if d.get("rerank_score", 0) >= min_score
            ]
            logger.debug(
                f"Reranked {len(documents)} documents → {len(filtered)} above threshold"
            )
            return filtered[:top_k]

        except Exception as e:
            logger.warning(f"Reranking failed: {e}. Returning original order.")
            for doc in documents:
                doc["rerank_score"] = doc.get("distance", 1.0)
            return documents[:top_k]

    async def score_single(self, query: str, document: str) -> float:
        """
        Score a single query-document pair using embedding similarity.
        """
        if not self._initialized:
            return 0.5

        # Check cache
        cache = get_llm_response_cache()
        cache_key = cache._make_key(query[:100], document[:100])
        hit, cached_score = cache.get(cache_key)
        if hit:
            return cached_score

        try:
            query_result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=query,
                task_type="retrieval_query",
            )
            doc_result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=document[:1000],
                task_type="retrieval_document",
            )
            score = _cosine_similarity(
                query_result["embedding"], doc_result["embedding"]
            )
            # Normalize: cosine sim is [-1, 1], clamp to [0, 1]
            score = max(0.0, min(1.0, score))

            cache.set(cache_key, score)
            return score

        except Exception as e:
            logger.warning(f"Single scoring failed: {e}")
            return 0.5


# Singleton
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """Get or create reranker instance"""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
        _reranker.initialize()
    return _reranker
