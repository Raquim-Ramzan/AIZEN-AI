"""
Smart Memory Manager for AIZEN
===============================
LLM-powered memory management with:
- Semantic deduplication (finds similar facts)
- Date tracking for all memories
- LLM-based memory updates/overrides
- Clustering for efficient fact scaling
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import asyncio
import json
import uuid
import google.generativeai as genai
from app.config import get_settings
from app.core.cache import get_embedding_cache

logger = logging.getLogger(__name__)
settings = get_settings()


class SmartMemoryManager:
    """
    Intelligent memory management with LLM-powered deduplication and updates.
    """
    
    # Similarity threshold for considering facts as duplicates
    SIMILARITY_THRESHOLD = 0.85
    
    # Max facts to compare for deduplication (performance limit)
    MAX_COMPARISON_FACTS = 50
    
    def __init__(self, vector_store=None, core_memory=None):
        self.vector_store = vector_store
        self.core_memory = core_memory
        self.model_name = "gemini-2.5-flash"
        self._initialized = False
    
    def initialize(self):
        """Initialize the manager"""
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self._initialized = True
            logger.info("Smart Memory Manager initialized")
    
    async def add_fact_smart(
        self,
        fact: str,
        importance: str = "normal",
        source: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a fact with smart deduplication and date tracking.
        
        1. Check for semantically similar existing facts
        2. If similar found, use LLM to decide: merge, update, or keep both
        3. Add date tracking to all facts
        
        Returns:
            Result with action taken (added, updated, merged, skipped)
        """
        result = {
            "action": "none",
            "fact": fact,
            "date_added": datetime.now(timezone.utc).isoformat(),
            "similar_facts": [],
            "updated_fact": None
        }
        
        # 1. Find similar existing facts
        similar_facts = await self._find_similar_facts(fact)
        result["similar_facts"] = similar_facts
        
        if similar_facts:
            # 2. Use LLM to decide what to do
            decision = await self._llm_decide_merge(fact, similar_facts)
            result["action"] = decision["action"]
            
            if decision["action"] == "skip":
                # Fact already exists, no action needed
                logger.info(f"Skipping duplicate fact: {fact[:50]}...")
                return result
            
            elif decision["action"] == "update":
                # Update existing fact with new information
                updated = await self._update_existing_fact(
                    fact_id=decision["target_fact_id"],
                    new_info=fact,
                    merged_content=decision.get("merged_content")
                )
                result["updated_fact"] = updated
                logger.info(f"Updated existing fact with new info")
                return result
            
            elif decision["action"] == "add":
                # Different enough, add as new
                pass  # Continue to add
        
        # 3. Add new fact with date tracking
        fact_with_date = self._create_dated_fact(fact, importance, source, metadata)
        
        if self.core_memory:
            await self.core_memory.add_learned_knowledge(
                fact=fact_with_date["content"],
                importance=importance,
                source=source
            )
        
        if self.vector_store:
            await self.vector_store.add_document(
                fact_with_date["content"],
                metadata={
                    "type": "fact",
                    "date_added": fact_with_date["date_added"],
                    "importance": importance,
                    "source": source,
                    **(metadata or {})
                }
            )
        
        result["action"] = "added"
        result["updated_fact"] = fact_with_date
        logger.info(f"Added new fact: {fact[:50]}...")
        
        return result
    
    def _create_dated_fact(
        self,
        fact: str,
        importance: str,
        source: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a fact entry with date tracking"""
        now = datetime.now(timezone.utc)
        
        return {
            "id": str(uuid.uuid4()),
            "content": fact,
            "date_added": now.isoformat(),
            "date_formatted": now.strftime("%Y-%m-%d"),
            "importance": importance,
            "source": source,
            "metadata": metadata or {}
        }
    
    async def _find_similar_facts(self, fact: str) -> List[Dict[str, Any]]:
        """Find semantically similar existing facts"""
        if not self.vector_store:
            return []
        
        try:
            # Query vector store for similar documents
            results = self.vector_store.memory_collection.query(
                query_texts=[fact],
                n_results=self.MAX_COMPARISON_FACTS,
                include=["documents", "metadatas", "distances"]
            )
            
            similar = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i]
                    # Convert distance to similarity (for cosine, smaller is more similar)
                    similarity = 1 - distance if distance <= 1 else 1 / (1 + distance)
                    
                    if similarity >= self.SIMILARITY_THRESHOLD:
                        meta = results["metadatas"][0][i] if results["metadatas"] else {}
                        similar.append({
                            "id": results["ids"][0][i] if results["ids"] else None,
                            "content": doc,
                            "similarity": similarity,
                            "date_added": meta.get("date_added", "unknown"),
                            "metadata": meta
                        })
            
            return similar
            
        except Exception as e:
            logger.error(f"Error finding similar facts: {e}")
            return []
    
    async def _llm_decide_merge(
        self,
        new_fact: str,
        similar_facts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use LLM to decide how to handle similar facts.
        
        Returns:
            action: "skip" | "update" | "add"
            target_fact_id: ID of fact to update (if action is "update")
            merged_content: New merged content (if action is "update")
        """
        if not self._initialized or not similar_facts:
            return {"action": "add"}
        
        # Format similar facts for LLM
        similar_formatted = []
        for i, sf in enumerate(similar_facts[:5]):  # Limit to 5 for prompt size
            similar_formatted.append(
                f"[{i}] (Date: {sf.get('date_added', 'unknown')}) {sf['content']}"
            )
        
        similar_str = "\n".join(similar_formatted)
        
        prompt = f"""You are a memory management system. Analyze if a new fact should be added, merged with existing facts, or skipped.

NEW FACT: {new_fact}

EXISTING SIMILAR FACTS:
{similar_str}

Decide:
1. SKIP - if the new fact contains no new information (already fully captured)
2. UPDATE - if the new fact has newer/updated information that should replace or merge with an existing fact
3. ADD - if the new fact is different enough to warrant a separate entry

Output your decision in this exact JSON format:
{{
    "action": "skip|update|add",
    "target_index": 0,  // only if action is "update", the index of the fact to update
    "merged_content": "...",  // only if action is "update", the new merged content
    "reason": "brief explanation"
}}

Important: For UPDATE actions, preserve dates where relevant. If the new fact has more recent information, make sure to include that date context in the merged content.

JSON response:"""

        try:
            model = genai.GenerativeModel(self.model_name)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500
                )
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            # Handle potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            decision = json.loads(response_text)
            
            # Map target_index to actual fact ID
            if decision.get("action") == "update" and "target_index" in decision:
                idx = decision["target_index"]
                if 0 <= idx < len(similar_facts):
                    decision["target_fact_id"] = similar_facts[idx].get("id")
            
            return decision
            
        except Exception as e:
            logger.warning(f"LLM decision failed: {e}. Defaulting to add.")
            return {"action": "add"}
    
    async def _update_existing_fact(
        self,
        fact_id: str,
        new_info: str,
        merged_content: Optional[str]
    ) -> Dict[str, Any]:
        """Update an existing fact with new information"""
        now = datetime.now(timezone.utc)
        
        content = merged_content or new_info
        
        # Update in vector store
        if self.vector_store and fact_id:
            try:
                self.vector_store.memory_collection.update(
                    ids=[fact_id],
                    documents=[content],
                    metadatas=[{
                        "type": "fact",
                        "date_updated": now.isoformat(),
                        "source": "llm_merge"
                    }]
                )
            except Exception as e:
                logger.error(f"Failed to update fact in vector store: {e}")
        
        return {
            "id": fact_id,
            "content": content,
            "date_updated": now.isoformat()
        }
    
    async def cluster_facts(self, facts: List[Dict[str, Any]], n_clusters: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Cluster facts into categories for efficient retrieval.
        Uses LLM to create meaningful clusters.
        """
        if not facts or not self._initialized:
            return {"uncategorized": facts}
        
        # Format facts for LLM
        facts_formatted = "\n".join([
            f"[{i}] {f.get('content', f.get('fact', str(f)))[:200]}"
            for i, f in enumerate(facts[:50])  # Limit
        ])
        
        prompt = f"""Organize these facts into {n_clusters} logical categories.

FACTS:
{facts_formatted}

Output as JSON with category names as keys and lists of fact indices as values.
Example:
{{
    "Personal Info": [0, 3, 7],
    "Preferences": [1, 4],
    "Technical Knowledge": [2, 5, 6]
}}

JSON:"""

        try:
            model = genai.GenerativeModel(self.model_name)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=500
                )
            )
            
            response_text = response.text.strip()
            if "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            clusters_indices = json.loads(response_text)
            
            # Convert indices to actual facts
            clusters = {}
            for category, indices in clusters_indices.items():
                clusters[category] = [facts[i] for i in indices if i < len(facts)]
            
            return clusters
            
        except Exception as e:
            logger.warning(f"Clustering failed: {e}")
            return {"uncategorized": facts}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics"""
        return {
            "initialized": self._initialized,
            "similarity_threshold": self.SIMILARITY_THRESHOLD,
            "max_comparison_facts": self.MAX_COMPARISON_FACTS
        }


# Singleton
_smart_memory_manager: Optional[SmartMemoryManager] = None


def get_smart_memory_manager(vector_store=None, core_memory=None) -> SmartMemoryManager:
    """Get or create smart memory manager"""
    global _smart_memory_manager
    if _smart_memory_manager is None:
        _smart_memory_manager = SmartMemoryManager(vector_store, core_memory)
        _smart_memory_manager.initialize()
    return _smart_memory_manager
