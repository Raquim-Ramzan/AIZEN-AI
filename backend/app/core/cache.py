"""
Caching Layer for AIZEN
========================
Implements in-memory caching with LRU eviction for:
- Embeddings (expensive API calls)
- Intent classifications
- LLM responses

Uses functools.lru_cache for simplicity (no Redis dependency).
For distributed setups, swap with Redis.
"""

import logging
import hashlib
import json
from functools import lru_cache
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import asyncio
from collections import OrderedDict
import threading

logger = logging.getLogger(__name__)


class AsyncLRUCache:
    """Thread-safe async LRU cache with TTL support"""
    
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    def _make_key(self, *args, **kwargs) -> str:
        """Create hashable key from arguments"""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Tuple[bool, Any]:
        """Get value from cache. Returns (hit, value)"""
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                # Check TTL
                if (datetime.now(timezone.utc) - timestamp).total_seconds() < self.ttl_seconds:
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._stats["hits"] += 1
                    return True, value
                else:
                    # Expired
                    del self._cache[key]
            
            self._stats["misses"] += 1
            return False, None
    
    def set(self, key: str, value: Any):
        """Set value in cache"""
        with self._lock:
            # Remove oldest if at capacity
            while len(self._cache) >= self.maxsize:
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1
            
            self._cache[key] = (value, datetime.now(timezone.utc))
    
    def clear(self):
        """Clear cache"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            return {
                **self._stats,
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "hit_rate": self._stats["hits"] / total if total > 0 else 0
            }


# Global cache instances
_embedding_cache = AsyncLRUCache(maxsize=5000, ttl_seconds=86400)  # 24 hours
_intent_cache = AsyncLRUCache(maxsize=1000, ttl_seconds=1800)  # 30 minutes
_llm_response_cache = AsyncLRUCache(maxsize=500, ttl_seconds=600)  # 10 minutes


def get_embedding_cache() -> AsyncLRUCache:
    """Get embedding cache instance"""
    return _embedding_cache


def get_intent_cache() -> AsyncLRUCache:
    """Get intent classification cache instance"""
    return _intent_cache


def get_llm_response_cache() -> AsyncLRUCache:
    """Get LLM response cache instance"""
    return _llm_response_cache


def cache_embedding(text: str) -> str:
    """Create cache key for embedding"""
    return hashlib.sha256(text.encode()).hexdigest()[:32]


async def cached_embedding(text: str, embed_func) -> List[float]:
    """
    Get cached embedding or compute and cache.
    
    Args:
        text: Text to embed
        embed_func: Async function that takes text and returns embedding
    """
    cache = get_embedding_cache()
    key = cache_embedding(text)
    
    hit, value = cache.get(key)
    if hit:
        return value
    
    # Compute embedding
    embedding = await asyncio.to_thread(embed_func, text)
    cache.set(key, embedding)
    return embedding


def get_all_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        "embedding_cache": _embedding_cache.get_stats(),
        "intent_cache": _intent_cache.get_stats(),
        "llm_response_cache": _llm_response_cache.get_stats()
    }


def clear_all_caches():
    """Clear all caches"""
    _embedding_cache.clear()
    _intent_cache.clear()
    _llm_response_cache.clear()
    logger.info("All caches cleared")
