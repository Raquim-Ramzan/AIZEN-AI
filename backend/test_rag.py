"""
RAG System Integration Test
============================
Tests the complete RAG pipeline: indexing, retrieval, and context building.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_rag_system():
    """Test the RAG system end-to-end"""
    print("=" * 60)
    print("AIZEN RAG System Integration Test")
    print("=" * 60)

    # Import components
    print("\n[1/6] Importing components...")
    from app.memory.conversation import ConversationManager
    from app.memory.core_memory import CoreMemory
    from app.memory.rag_manager import initialize_rag_manager
    from app.memory.vector_store import VectorStore

    print("[OK] All imports successful")

    # Initialize vector store
    print("\n[2/6] Initializing Vector Store...")
    vector_store = VectorStore()
    await vector_store.initialize()
    print(f"[OK] Vector Store initialized - {vector_store.get_stats()}")

    # Initialize core memory
    print("\n[3/6] Initializing Core Memory...")
    core_memory = CoreMemory(vector_store=vector_store)
    await core_memory.initialize()
    print(f"[OK] Core Memory initialized - {len(core_memory.memory.get('core_facts', []))} facts")

    # Initialize conversation manager
    print("\n[4/6] Initializing Conversation Manager...")
    conv_manager = ConversationManager()
    await conv_manager.initialize()
    print("[OK] Conversation Manager initialized")

    # Initialize RAG Manager
    print("\n[5/6] Initializing RAG Manager...")
    rag_manager = initialize_rag_manager(
        vector_store=vector_store, core_memory=core_memory, conversation_manager=conv_manager
    )
    print("[OK] RAG Manager initialized")

    # Test RAG operations
    print("\n[6/6] Testing RAG Operations...")

    # Test context retrieval
    print("\n  Testing context retrieval...")
    context = await rag_manager.get_context_for_query(
        user_query="What do you remember about me?",
        include_memories=True,
        include_past_conversations=True,
    )
    print(
        f"  [OK] Context retrieved: {context['metadata']['memory_hits']} memories, "
        f"{context['metadata']['conversation_hits']} past convos"
    )
    print(f"  Context length: {context['metadata']['total_context_length']} chars")

    # Test conversation exchange processing
    print("\n  Testing conversation exchange processing...")
    result = await rag_manager.process_conversation_exchange(
        user_message="My name is Test User and I work as a developer",
        assistant_response="Nice to meet you, Test User! It's great to hear you work as a developer.",
        conversation_id="test-conv-123",
    )
    print(
        f"  [OK] Exchange processed: {result['facts_extracted']} facts extracted, "
        f"indexed={result['indexed']}"
    )

    # Get stats
    print("\n  RAG System Stats:")
    stats = rag_manager.get_stats()
    print(f"  - Vector Store: {stats.get('vector_store', {})}")
    print(f"  - Core Memory: {stats.get('core_memory', {})}")
    print(f"  - RAG Config: {stats.get('rag_config', {})}")

    print("\n" + "=" * 60)
    print("[SUCCESS] All RAG system tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_rag_system())
