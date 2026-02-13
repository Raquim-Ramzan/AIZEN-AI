"""
AIZEN Memory Module
====================
Provides persistent memory, vector search, and RAG capabilities.
"""

from .vector_store import VectorStore, get_vector_store
from .core_memory import CoreMemory, get_core_memory
from .conversation import ConversationManager, get_conversation_manager
from .rag_manager import RAGManager, get_rag_manager, initialize_rag_manager
from .reranker import Reranker, get_reranker
from .smart_memory import SmartMemoryManager, get_smart_memory_manager
from .history_manager import HistoryManager, SlidingWindowHistory, get_history_manager

__all__ = [
    # Core memory components
    "VectorStore",
    "get_vector_store",
    "CoreMemory", 
    "get_core_memory",
    "ConversationManager",
    "get_conversation_manager",
    # RAG components
    "RAGManager",
    "get_rag_manager",
    "initialize_rag_manager",
    # Advanced memory features
    "Reranker",
    "get_reranker",
    "SmartMemoryManager",
    "get_smart_memory_manager",
    "HistoryManager",
    "SlidingWindowHistory",
    "get_history_manager",
]
