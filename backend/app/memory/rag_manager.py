"""
RAG Manager - Central Retrieval-Augmented Generation Orchestration
===================================================================
Coordinates all RAG operations: indexing, retrieval, and context building.
This is the brain of the memory system.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RAGManager:
    """
    Central manager for all RAG (Retrieval-Augmented Generation) operations.
    Coordinates between vector store, core memory, and conversation manager.
    """
    
    def __init__(self, vector_store=None, core_memory=None, conversation_manager=None):
        self.vector_store = vector_store
        self.core_memory = core_memory
        self.conversation_manager = conversation_manager
        
        # Configuration — token budget replaces the old 2000-char cutoff.
        # 1 token ≈ 4 characters for English text (conservative).
        self._chars_per_token = 4
        self.auto_index_enabled = True
        self.auto_summarize_threshold = 20  # Summarize after N messages
    
    def set_dependencies(self, vector_store=None, core_memory=None, conversation_manager=None):
        """Set or update dependencies"""
        if vector_store:
            self.vector_store = vector_store
        if core_memory:
            self.core_memory = core_memory
        if conversation_manager:
            self.conversation_manager = conversation_manager
    
    # =====================================================
    # CONTEXT RETRIEVAL (Used before LLM call)
    # =====================================================
    
    async def get_context_for_query(
        self,
        user_query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        include_memories: bool = True,
        include_past_conversations: bool = True,
        max_items: int = 5,
        use_reranking: bool = True
    ) -> Dict[str, Any]:
        """
        Get all relevant context for a user query with optional reranking.
        This is the main method called before each LLM generation.
        
        Returns:
            {
                "core_memory_context": str,  # Identity, preferences
                "rag_context": str,          # Retrieved facts and past convos
                "full_context": str,         # Combined and formatted
                "metadata": {...}            # Stats about what was retrieved
            }
        """
        from app.core.metrics import get_metrics, Metrics
        
        metrics = get_metrics()
        result = {
            "core_memory_context": "",
            "rag_context": "",
            "full_context": "",
            "metadata": {
                "memory_hits": 0,
                "conversation_hits": 0,
                "total_context_length": 0,
                "reranked": False
            }
        }
        
        # Start timing
        import time
        start_time = time.perf_counter()
        
        # 1. Get core memory context (identity, preferences)
        if self.core_memory:
            try:
                result["core_memory_context"] = await self.core_memory.get_system_prompt_context(user_id)
            except Exception as e:
                logger.error(f"Failed to get core memory context: {e}")
        
        # 2. Get RAG context from vector store
        memories = []
        past_convos = []
        
        if self.vector_store:
            try:
                rag_result = await self.vector_store.retrieve_context(
                    query=user_query,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    max_memories=max_items * 2 if use_reranking else max_items if include_memories else 0,  # Get more for reranking
                    max_conversations=max_items * 2 if use_reranking else max_items if include_past_conversations else 0
                )
                
                memories = rag_result.get("memories", [])
                past_convos = rag_result.get("past_conversations", [])
                
            except Exception as e:
                logger.error(f"Failed to get RAG context: {e}")
        
        # 3. Apply reranking if enabled
        if use_reranking and (memories or past_convos):
            try:
                from app.memory.reranker import get_reranker
                reranker = get_reranker()
                
                if memories:
                    # Convert to format expected by reranker
                    memory_docs = [{"content": m.get("content", m.get("document", "")), **m} for m in memories]
                    memories = await reranker.rerank(user_query, memory_docs, top_k=max_items)
                    result["metadata"]["reranked"] = True
                
                if past_convos:
                    convo_docs = [{"content": c.get("content", c.get("document", "")), **c} for c in past_convos]
                    past_convos = await reranker.rerank(user_query, convo_docs, top_k=max_items)
                    
            except Exception as e:
                logger.warning(f"Reranking failed, using original order: {e}")
        
        # 4. Format context
        result["metadata"]["memory_hits"] = len(memories)
        result["metadata"]["conversation_hits"] = len(past_convos)
        
        rag_parts = []
        if memories:
            memory_text = "RELEVANT MEMORIES:\n" + "\n".join([
                f"- {m.get('content', m.get('document', ''))} (added: {m.get('metadata', {}).get('date_added', 'unknown')})"
                for m in memories[:max_items]
            ])
            rag_parts.append(memory_text)
        
        if past_convos:
            convo_text = "PAST CONVERSATIONS:\n" + "\n".join([
                f"- {c.get('content', c.get('document', ''))[:200]}"
                for c in past_convos[:max_items]
            ])
            rag_parts.append(convo_text)
        
        result["rag_context"] = "\n\n".join(rag_parts)
        
        # 5. Combine contexts
        parts = []
        if result["core_memory_context"]:
            parts.append(result["core_memory_context"])
        if result["rag_context"]:
            parts.append(result["rag_context"])
        
        result["full_context"] = "\n\n".join(parts)
        result["metadata"]["total_context_length"] = len(result["full_context"])
        
        # Truncate if over token budget
        from app.config import get_settings
        budget_tokens = get_settings().rag_context_budget_tokens
        budget_chars = budget_tokens * self._chars_per_token

        if len(result["full_context"]) > budget_chars:
            result["full_context"] = (
                result["full_context"][:budget_chars]
                + "\n[...context truncated to token budget...]"
            )
        
        # Record metrics
        elapsed = time.perf_counter() - start_time
        metrics.observe(Metrics.RAG_LATENCY, elapsed)
        metrics.increment(Metrics.RAG_RETRIEVALS)
        
        return result
    
    # =====================================================
    # POST-CONVERSATION INDEXING
    # =====================================================
    
    async def process_conversation_exchange(
        self,
        user_message: str,
        assistant_response: str,
        conversation_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a conversation exchange after it completes.
        - Extracts and stores facts
        - Indexes the exchange for future retrieval
        - Triggers summarization if needed
        
        This should be called after every message exchange.
        """
        result = {
            "facts_extracted": 0,
            "facts_deduplicated": 0,
            "indexed": False,
            "summarized": False,
            "errors": []
        }
        
        if not self.auto_index_enabled:
            return result
        
        # 1. Extract facts using LLM
        from app.core.metrics import get_metrics, Metrics
        
        metrics = get_metrics()
        extracted_facts = []
        
        if self.core_memory:
            try:
                extracted_facts = await self.core_memory.extract_facts_only(
                    user_id,
                    user_message,
                    assistant_response
                )
            except Exception as e:
                logger.error(f"Fact extraction failed: {e}")
                result["errors"].append(f"fact_extraction: {str(e)}")
        
        # 2. Use smart memory for deduplication before storing
        if extracted_facts:
            try:
                from app.memory.smart_memory import get_smart_memory_manager
                smart_memory = get_smart_memory_manager(self.vector_store, self.core_memory)
                
                for fact_text in extracted_facts:
                    add_result = await smart_memory.add_fact_smart(
                        fact=fact_text,
                        importance="normal",
                        source="conversation"
                    )
                    
                    if add_result["action"] == "added":
                        result["facts_extracted"] += 1
                        metrics.increment(Metrics.FACTS_EXTRACTED)
                    elif add_result["action"] in ("skip", "update"):
                        result["facts_deduplicated"] += 1
                        
            except Exception as e:
                logger.error(f"Smart memory processing failed: {e}")
                # Fallback to direct storage
                for fact_text in extracted_facts:
                    try:
                        await self.core_memory.add_learned_knowledge(user_id, fact_text, "normal", "conversation")
                        result["facts_extracted"] += 1
                except Exception as fallback_err:
                    logger.error(
                        f"Fallback fact storage also failed for fact "
                        f"'{fact_text[:50]}...': {fallback_err}"
                    )
        
        # 3. Index the conversation exchange
        if self.vector_store:
            try:
                doc_id = await self.vector_store.index_conversation_exchange(
                    user_message=user_message,
                    assistant_response=assistant_response,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    metadata=metadata
                )
                result["indexed"] = doc_id is not None
            except Exception as e:
                logger.error(f"Conversation indexing failed: {e}")
                result["errors"].append(f"indexing: {str(e)}")
        
        # 4. Check if summarization is needed
        if self.conversation_manager:
            try:
                messages = await self.conversation_manager.get_messages(conversation_id)
                if len(messages) >= self.auto_summarize_threshold:
                    # Check if we already summarized recently
                    memory = await self.core_memory.get_memory(user_id)
                    summaries = memory.get("conversation_summaries", {})
                    if conversation_id not in summaries:
                        await self.summarize_conversation(conversation_id, user_id)
                        result["summarized"] = True
            except Exception as e:
                logger.error(f"Summarization check failed: {e}")
        
        if result["facts_extracted"] > 0 or result["indexed"]:
            logger.info(f"Processed exchange: {result['facts_extracted']} facts, indexed={result['indexed']}")
        
        return result
    
    # =====================================================
    # CONVERSATION SUMMARIZATION
    # =====================================================
    
    async def summarize_conversation(
        self,
        conversation_id: str,
        user_id: str,
        force: bool = False
    ) -> Optional[str]:
        """
        Generate and store a summary of a conversation.
        Uses LLM to create a concise summary for long-term memory.
        """
        if not self.conversation_manager:
            logger.error("Conversation manager not available for summarization")
            return None
        
        try:
            messages = await self.conversation_manager.get_messages(conversation_id, limit=100)
            
            if len(messages) < 5 and not force:
                logger.debug(f"Conversation {conversation_id} too short for summarization")
                return None
            
            # Build conversation text
            conversation_text = ""
            for msg in messages[-50:]:  # Last 50 messages max
                role = "User" if msg["role"] == "user" else "Aizen"
                content = msg["content"][:200]  # Truncate long messages
                conversation_text += f"{role}: {content}\n"
            
            # Generate summary with LLM
            summary = await self._generate_summary_with_llm(conversation_text)
            
            if summary and self.core_memory:
                await self.core_memory.add_conversation_summary(user_id, conversation_id, summary)
                
                # Also index in vector store
                if self.vector_store:
                    await self.vector_store.index_conversation_summary(
                        summary=summary,
                        conversation_id=conversation_id,
                        message_count=len(messages)
                    )
                
                logger.info(f"Generated summary for conversation {conversation_id}")
                return summary
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            return None
    
    async def _generate_summary_with_llm(self, conversation_text: str) -> Optional[str]:
        """Use Gemini to generate a conversation summary"""
        try:
            import google.generativeai as genai
            from app.config import get_settings
            
            settings = get_settings()
            if not settings.gemini_api_key:
                return None
            
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            prompt = f"""Summarize this conversation in 2-3 sentences, focusing on:
1. Main topics discussed
2. Any important decisions or information shared
3. Key outcomes or conclusions

Conversation:
{conversation_text[:3000]}

Summary:"""

            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=200,
                )
            )
            
            if response.parts and len(response.parts) > 0:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return None
    
    # =====================================================
    # MEMORY SEARCH
    # =====================================================
    
    async def search_all_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all memory sources.
        Returns categorized results.
        """
        results = {
            "vector_memories": [],
            "core_facts": [],
            "past_conversations": [],
            "learned_knowledge": []
        }
        
        # Vector store search
        if self.vector_store:
            try:
                results["vector_memories"] = await self.vector_store.search(query, user_id, limit=limit)
                results["past_conversations"] = await self.vector_store.search_conversations(query, user_id, limit=limit)
            except Exception as e:
                logger.error(f"Vector search failed: {e}")
        
        # Core memory search
        if self.core_memory:
            try:
                results["core_facts"] = await self.core_memory.get_relevant_knowledge(user_id, query, limit=limit)
                memory = await self.core_memory.get_memory(user_id)
                results["learned_knowledge"] = memory.get("learned_knowledge", [])[:limit]
            except Exception as e:
                logger.error(f"Core memory search failed: {e}")
        
        return results
    
    # =====================================================
    # STATISTICS & MAINTENANCE
    # =====================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive RAG statistics"""
        stats = {
            "vector_store": {},
            "core_memory": {},
            "rag_config": {
                "max_context_length": self.max_context_length,
                "auto_index_enabled": self.auto_index_enabled,
                "auto_summarize_threshold": self.auto_summarize_threshold
            }
        }
        
        if self.vector_store:
            stats["vector_store"] = self.vector_store.get_stats()
        
        if self.core_memory:
            stats["core_memory"] = {
                "core_facts_count": len(self.core_memory.memory.get("core_facts", [])),
                "learned_knowledge_count": len(self.core_memory.memory.get("learned_knowledge", [])),
                "summaries_count": len(self.core_memory.memory.get("conversation_summaries", {})),
                "extraction_stats": self.core_memory.get_extraction_stats()
            }
        
        return stats
    
    async def rebuild_vector_index(self, user_id: str) -> Dict[str, int]:
        """
        Rebuild the vector index from core memory.
        Useful after migrations or corruption.
        """
        if not self.vector_store or not self.core_memory:
            return {"error": "Missing dependencies"}
        
        results = {
            "core_facts_indexed": 0,
            "learned_knowledge_indexed": 0,
            "errors": 0
        }
        
        # Clear existing memory collection
        try:
            await self.vector_store.clear(user_id)
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            return {"error": str(e)}
        
        memory = await self.core_memory.get_memory(user_id)
        
        # Re-index core facts
        for fact in memory.get("core_facts", []):
            try:
                await self.vector_store.add_document(
                    content=fact["fact"],
                    user_id=user_id,
                    metadata={
                        "type": "core_fact",
                        "category": fact.get("category", "unknown"),
                        "importance": fact.get("importance", "normal")
                    }
                )
                results["core_facts_indexed"] += 1
            except Exception as e:
                results["errors"] += 1
        
        # Re-index learned knowledge
        for knowledge in memory.get("learned_knowledge", []):
            try:
                await self.vector_store.add_document(
                    content=knowledge["fact"],
                    user_id=user_id,
                    metadata={
                        "type": "learned_knowledge",
                        "importance": knowledge.get("importance", "normal")
                    }
                )
                results["learned_knowledge_indexed"] += 1
            except Exception as e:
                results["errors"] += 1
        
        logger.info(f"Rebuilt vector index for {user_id}: {results}")
        return results


# Singleton instance
_rag_manager: Optional[RAGManager] = None


def get_rag_manager() -> RAGManager:
    """Get or create the RAG manager singleton"""
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager()
    return _rag_manager


def initialize_rag_manager(vector_store, core_memory, conversation_manager=None) -> RAGManager:
    """Initialize the RAG manager with dependencies"""
    global _rag_manager
    _rag_manager = RAGManager(
        vector_store=vector_store,
        core_memory=core_memory,
        conversation_manager=conversation_manager
    )
    logger.info("RAG Manager initialized")
    return _rag_manager
