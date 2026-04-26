"""
Cloud Core Memory System with Supabase
======================================
Persistent memory for identity, preferences, and learned knowledge.
Replaces core_memory.json with a Postgres `profiles` table.
"""

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any, Optional

from app.config import get_settings
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

# Default core identity facts
DEFAULT_CORE_FACTS = [
    {"fact": "You are AIZEN", "category": "identity", "importance": "critical", "source": "system"},
    {
        "fact": "You are a cloud-based AI Assistant",
        "category": "identity",
        "importance": "critical",
        "source": "system",
    },
]


class CoreMemory:
    """
    Core memory backed by Supabase `profiles` table.
    Supports multiple users instantly.
    """

    def __init__(self, vector_store=None):
        self.client = None
        self.vector_store = vector_store
        self._llm_extractor_enabled = True

    def set_vector_store(self, vector_store):
        """Set the vector store for semantic memory operations"""
        self.vector_store = vector_store

    async def initialize(self):
        """Initialize Supabase client"""
        try:
            self.client = get_supabase_client()
            if not self.client:
                logger.error("Supabase client not initialized. Core memory disabled.")
        except Exception as e:
            logger.error(f"Failed to initialize core memory: {e}")

    async def _get_or_create_profile(self, user_id: str) -> dict[str, Any]:
        """Fetch a user's profile or create a default one"""
        if not self.client:
            return self._create_default_memory()

        try:
            response = self.client.table("profiles").select("*").eq("user_id", user_id).execute()
            if response.data and len(response.data) > 0:
                profile = response.data[0]
                # Ensure memory is parsed from content
                if isinstance(profile.get("content"), str):
                    try:
                        memory = json.loads(profile["content"])
                    except:
                        memory = self._create_default_memory()
                else:
                    memory = self._create_default_memory()
                return memory
            else:
                # Create new
                memory = self._create_default_memory()
                self.client.table("profiles").insert(
                    {"user_id": user_id, "content": json.dumps(memory), "metadata": {}}
                ).execute()
                return memory
        except Exception as e:
            logger.error(f"Failed to get/create profile for {user_id}: {e}")
            return self._create_default_memory()

    async def _save_profile(self, user_id: str, memory: dict[str, Any]):
        """Save a user's profile to Supabase"""
        if not self.client:
            return

        try:
            memory["updated_at"] = datetime.now(UTC).isoformat()
            self.client.table("profiles").update(
                {"content": json.dumps(memory), "updated_at": memory["updated_at"]}
            ).eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"Failed to save profile for {user_id}: {e}")

    def _create_default_memory(self) -> dict[str, Any]:
        """Create default memory structure"""
        return {
            "user_profile": {
                "name": "User",
                "preferences": {},
                "important_facts": [],
                "learned_behaviors": [],
            },
            "core_facts": [
                {**fact, "id": f"system_{i}", "timestamp": datetime.now(UTC).isoformat()}
                for i, fact in enumerate(DEFAULT_CORE_FACTS)
            ],
            "learned_knowledge": [],
            "skills_unlocked": [
                "web_search",
                "file_operations",
                "code_execution",
                "calendar",
                "system_info",
                "system_operations",
            ],
            "conversation_summaries": {},
            "extraction_stats": {
                "total_extractions": 0,
                "successful_llm_extractions": 0,
                "fallback_extractions": 0,
            },
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

    async def get_memory(self, user_id: str) -> dict[str, Any]:
        """Get full core memory for user"""
        return await self._get_or_create_profile(user_id)

    async def get_core_facts(self, user_id: str) -> list[dict[str, Any]]:
        """Get all core facts (identity and learned)"""
        memory = await self._get_or_create_profile(user_id)
        facts = memory.get("core_facts", []).copy()
        facts.extend(memory.get("learned_knowledge", []))
        return facts

    async def get_system_prompt_context(self, user_id: str) -> str:
        """Get core memory formatted for system prompt injection."""
        memory = await self._get_or_create_profile(user_id)
        context_parts = []

        # Add identity facts
        identity_facts = [
            f for f in memory.get("core_facts", []) if f.get("category") == "identity"
        ]
        if identity_facts:
            context_parts.append("=== CORE IDENTITY ===")
            for fact in identity_facts:
                context_parts.append(f"• {fact['fact']}")

        # Add user preferences
        user_prefs = memory.get("user_profile", {}).get("preferences", {})
        if user_prefs:
            context_parts.append("\n=== USER PREFERENCES ===")
            for key, value in user_prefs.items():
                context_parts.append(f"• {key}: {value}")

        # Add learned knowledge (non-identity facts, sorted by importance)
        learned = memory.get("learned_knowledge", [])
        # Prioritize high importance facts
        high_importance = [f for f in learned if f.get("importance") in ["critical", "high"]]
        normal_importance = [f for f in learned if f.get("importance") not in ["critical", "high"]]

        combined = high_importance[:5] + normal_importance[:5]  # Max 10 facts

        if combined:
            context_parts.append("\n=== LEARNED KNOWLEDGE ===")
            for entry in combined:
                importance = entry.get("importance", "normal")
                prefix = "⭐ " if importance in ["critical", "high"] else "• "
                context_parts.append(f"{prefix}{entry['fact']}")

        # Add non-identity core facts
        other_facts = [
            f
            for f in memory.get("core_facts", [])
            if f.get("category") != "identity" and f.get("source") != "system"
        ]
        if other_facts:
            context_parts.append("\n=== IMPORTANT FACTS ===")
            for fact in other_facts[:5]:
                context_parts.append(f"• {fact['fact']}")

        # Add user profile name
        user_name = memory.get("user_profile", {}).get("name", "")
        if user_name:
            context_parts.append("\n=== USER INFO ===")
            context_parts.append(f"• User's name: {user_name}")

        return "\n".join(context_parts)

    async def update_user_profile(self, user_id: str, key: str, value: Any):
        """Update user profile field"""
        memory = await self._get_or_create_profile(user_id)
        if "user_profile" not in memory:
            memory["user_profile"] = {}
        memory["user_profile"][key] = value
        await self._save_profile(user_id, memory)
        logger.info(f"Updated user profile for {user_id}: {key}")

    async def add_core_fact(
        self,
        user_id: str,
        fact: str,
        category: str = "learned",
        importance: str = "normal",
        source: str = "conversation",
    ) -> dict[str, Any] | None:
        """Add a core fact to permanent memory"""
        memory = await self._get_or_create_profile(user_id)
        if "core_facts" not in memory:
            memory["core_facts"] = []

        # Check for duplicates (case-insensitive)
        existing_facts = {f["fact"].lower() for f in memory["core_facts"]}
        if fact.lower() in existing_facts:
            logger.debug(f"Fact already exists: {fact[:50]}...")
            return None

        fact_entry = {
            "id": f"fact_{datetime.now(UTC).timestamp()}",
            "fact": fact,
            "category": category,
            "importance": importance,
            "source": source,
            "timestamp": datetime.now(UTC).isoformat(),
            "confidence": 0.9,
        }

        memory["core_facts"].append(fact_entry)
        await self._save_profile(user_id, memory)

        # Also add to vector store if available
        if self.vector_store:
            try:
                await self.vector_store.add_document(
                    content=fact,
                    user_id=user_id,
                    metadata={"type": "core_fact", "category": category, "importance": importance},
                )
            except Exception as e:
                logger.error(f"Failed to add fact to vector store: {e}")

        logger.info(f"Added core fact [{importance}] for {user_id}: {fact[:50]}...")
        return fact_entry

    async def update_core_fact(self, user_id: str, fact_id: str, new_fact: str) -> bool:
        """Update an existing core fact"""
        memory = await self._get_or_create_profile(user_id)
        for fact in memory.get("core_facts", []):
            if fact.get("id") == fact_id:
                fact["fact"] = new_fact
                fact["updated_at"] = datetime.now(UTC).isoformat()
                await self._save_profile(user_id, memory)
                logger.info(f"Updated core fact {fact_id} for {user_id}")
                return True
        return False

    async def delete_core_fact(self, user_id: str, fact_id: str) -> bool:
        """Delete a core fact by ID"""
        memory = await self._get_or_create_profile(user_id)
        if "core_facts" not in memory:
            return False

        original_len = len(memory["core_facts"])
        memory["core_facts"] = [f for f in memory["core_facts"] if f.get("id") != fact_id]

        if len(memory["core_facts"]) < original_len:
            await self._save_profile(user_id, memory)
            logger.info(f"Deleted core fact {fact_id} for {user_id}")
            return True
        return False

    async def clear_all_facts(self, user_id: str, keep_identity: bool = True):
        """Clear all core facts, optionally keeping identity facts"""
        memory = await self._get_or_create_profile(user_id)
        if keep_identity:
            memory["core_facts"] = [
                f for f in memory.get("core_facts", []) if f.get("source") == "system"
            ]
        else:
            memory["core_facts"] = []

        memory["learned_knowledge"] = []
        await self._save_profile(user_id, memory)
        logger.info(f"Cleared core facts for {user_id}")

    async def add_learned_knowledge(
        self,
        user_id: str,
        fact: str,
        confidence: float = 0.9,
        source: str = "conversation",
        importance: str = "normal",
    ) -> dict[str, Any]:
        """Add learned knowledge (less permanent than core facts)"""
        memory = await self._get_or_create_profile(user_id)

        # Check for semantic duplicates
        existing = [k["fact"].lower() for k in memory.get("learned_knowledge", [])]
        if fact.lower() in existing:
            logger.debug(f"Knowledge already exists: {fact[:50]}...")
            return None

        knowledge_entry = {
            "id": f"knowledge_{datetime.now(UTC).timestamp()}",
            "fact": fact,
            "timestamp": datetime.now(UTC).isoformat(),
            "confidence": confidence,
            "source": source,
            "importance": importance,
        }

        if "learned_knowledge" not in memory:
            memory["learned_knowledge"] = []

        memory["learned_knowledge"].append(knowledge_entry)

        # Keep only last 100 entries, but prioritize high importance
        if len(memory["learned_knowledge"]) > 100:
            importance_order = {"critical": 0, "high": 1, "normal": 2}
            memory["learned_knowledge"].sort(
                key=lambda x: (
                    importance_order.get(x.get("importance", "normal"), 2),
                    x.get("timestamp", ""),
                )
            )
            memory["learned_knowledge"] = memory["learned_knowledge"][:100]

        await self._save_profile(user_id, memory)

        # Add to vector store
        if self.vector_store:
            try:
                await self.vector_store.add_document(
                    content=fact,
                    user_id=user_id,
                    metadata={
                        "type": "learned_knowledge",
                        "importance": importance,
                        "source": source,
                    },
                )
            except Exception as e:
                logger.error(f"Failed to add knowledge to vector store: {e}")

        logger.info(f"Added learned knowledge for {user_id}: {fact[:50]}...")
        return knowledge_entry

    # =====================================================
    # LLM-BASED FACT EXTRACTION
    # =====================================================

    async def extract_facts_only(
        self, user_id: str, user_message: str, assistant_response: str
    ) -> list[str]:
        """Extract facts from conversation without storing them."""
        memory = await self._get_or_create_profile(user_id)
        if "extraction_stats" not in memory:
            memory["extraction_stats"] = {
                "total_extractions": 0,
                "successful_llm_extractions": 0,
                "fallback_extractions": 0,
            }
        memory["extraction_stats"]["total_extractions"] += 1

        extracted_facts = []
        settings = get_settings()

        if self._llm_extractor_enabled and settings.gemini_api_key:
            llm_facts = await self._extract_facts_with_llm(user_message, assistant_response)
            if llm_facts:
                memory["extraction_stats"]["successful_llm_extractions"] += 1
                extracted_facts = [f.get("fact", str(f)) for f in llm_facts]

        if not extracted_facts:
            memory["extraction_stats"]["fallback_extractions"] += 1
            regex_facts = await self._extract_facts_with_regex(user_message)
            extracted_facts = [f.get("fact", str(f)) for f in regex_facts]

        await self._save_profile(user_id, memory)
        return extracted_facts

    async def extract_and_store_facts(
        self, user_id: str, user_message: str, assistant_response: str
    ) -> list[dict[str, Any]]:
        """Extract important facts from conversation using LLM and store them."""
        memory = await self._get_or_create_profile(user_id)
        extracted_facts = []
        settings = get_settings()

        if "extraction_stats" not in memory:
            memory["extraction_stats"] = {
                "total_extractions": 0,
                "successful_llm_extractions": 0,
                "fallback_extractions": 0,
            }
        memory["extraction_stats"]["total_extractions"] += 1

        if self._llm_extractor_enabled and settings.gemini_api_key:
            llm_facts = await self._extract_facts_with_llm(user_message, assistant_response)
            if llm_facts:
                memory["extraction_stats"]["successful_llm_extractions"] += 1
                extracted_facts = llm_facts

        if not extracted_facts:
            memory["extraction_stats"]["fallback_extractions"] += 1
            extracted_facts = await self._extract_facts_with_regex(user_message)

        await self._save_profile(user_id, memory)

        stored_facts = []
        for extracted in extracted_facts:
            result = await self.add_learned_knowledge(
                user_id=user_id,
                fact=extracted["fact"],
                importance=extracted.get("importance", "normal"),
                source="conversation_extraction",
            )
            if result:
                stored_facts.append(result)

        if stored_facts:
            logger.info(f"Extracted and stored {len(stored_facts)} facts for {user_id}")

        return stored_facts

    async def _extract_facts_with_llm(
        self, user_message: str, assistant_response: str
    ) -> list[dict[str, Any]]:
        """Use Gemini to intelligently extract important facts from conversation."""
        try:
            settings = get_settings()
            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")

            extraction_prompt = f"""Analyze this conversation exchange and extract important facts worth remembering long-term.
User said: "{user_message}"
Assistant responded: "{assistant_response[:500]}"

Extract ONLY facts that are:
1. Personal information about the user (name, job, preferences, habits)
2. Explicit requests to remember something
3. Important context that should persist across conversations
4. User's preferences or dislikes

Respond ONLY with valid JSON array. If nothing worth remembering, return empty array [].
Format: [{{"fact": "clear statement", "category": "user_info|preference|explicit_memory", "importance": "high|normal"}}]
JSON output:"""

            response = model.generate_content(
                extraction_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1, max_output_tokens=500
                ),
            )

            if not response.parts or len(response.parts) == 0:
                return []

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()

            if not response_text or response_text == "[]":
                return []

            facts = json.loads(response_text)
            validated_facts = []
            for fact in facts:
                if isinstance(fact, dict) and "fact" in fact:
                    validated_facts.append(
                        {
                            "fact": fact["fact"],
                            "category": fact.get("category", "learned"),
                            "importance": fact.get("importance", "normal"),
                        }
                    )
            return validated_facts

        except Exception as e:
            logger.debug(f"LLM extraction failed: {e}")
            return []

    async def _extract_facts_with_regex(self, user_message: str) -> list[dict[str, Any]]:
        """Fallback regex-based extraction if LLM is unavailable"""
        patterns = [
            (
                r"(?:i am|i'm|my name is|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
                "user_info",
                "high",
            ),
            (r"(?:i prefer|i like|i love|my favorite)\s+(.+?)(?:\.|$|,)", "preference", "normal"),
            (r"(?:i hate|i don't like|i dislike)\s+(.+?)(?:\.|$|,)", "preference", "normal"),
            (r"(?:i work as|i am a|i'm a|my job is)\s+(.+?)(?:\.|$|,)", "user_info", "high"),
            (r"(?:i live in|i'm from|i'm based in)\s+(.+?)(?:\.|$|,)", "user_info", "normal"),
            (
                r"(?:remember that|don't forget|keep in mind that)\s+(.+?)(?:\.|$)",
                "explicit_memory",
                "high",
            ),
        ]

        message_lower = user_message.lower()
        extracted_facts = []

        for pattern, category, importance in patterns:
            matches = re.findall(pattern, user_message, re.IGNORECASE)
            for match in matches:
                if len(match) > 3:
                    fact = match.strip()
                    if category == "user_info":
                        fact = f"User {fact}" if not fact.lower().startswith("user") else fact
                    elif category == "preference":
                        if (
                            "prefer" in message_lower
                            or "like" in message_lower
                            or "love" in message_lower
                        ):
                            fact = f"User likes/prefers {fact}"
                        elif "hate" in message_lower or "don't like" in message_lower:
                            fact = f"User dislikes {fact}"

                    extracted_facts.append(
                        {"fact": fact, "category": category, "importance": importance}
                    )
        return extracted_facts

    async def add_conversation_summary(self, user_id: str, conversation_id: str, summary: str):
        """Add conversation summary"""
        memory = await self._get_or_create_profile(user_id)
        if "conversation_summaries" not in memory:
            memory["conversation_summaries"] = {}

        memory["conversation_summaries"][conversation_id] = {
            "summary": summary,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if len(memory["conversation_summaries"]) > 50:
            sorted_keys = sorted(
                memory["conversation_summaries"].keys(),
                key=lambda k: memory["conversation_summaries"][k]["timestamp"],
            )
            for key in sorted_keys[:-50]:
                del memory["conversation_summaries"][key]

        if self.vector_store:
            try:
                await self.vector_store.index_conversation_summary(
                    summary=summary,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    message_count=0,
                )
            except Exception as e:
                logger.error(f"Failed to index summary in vector store: {e}")

        await self._save_profile(user_id, memory)
        logger.info(f"Added conversation summary for {conversation_id}")

    async def get_relevant_knowledge(
        self, user_id: str, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get relevant knowledge using keyword matching"""
        memory = await self._get_or_create_profile(user_id)
        query_lower = query.lower()
        relevant = []

        for entry in memory.get("core_facts", []):
            if any(word in entry["fact"].lower() for word in query_lower.split()):
                relevant.append(entry)

        for entry in memory.get("learned_knowledge", []):
            if any(word in entry["fact"].lower() for word in query_lower.split()):
                relevant.append(entry)

        importance_order = {"critical": 0, "high": 1, "normal": 2}
        relevant.sort(
            key=lambda x: (
                importance_order.get(x.get("importance", "normal"), 2),
                -x.get("confidence", 0.5),
            )
        )

        return relevant[:limit]

    async def add_preference(self, user_id: str, key: str, value: Any):
        """Add user preference"""
        memory = await self._get_or_create_profile(user_id)
        if "user_profile" not in memory:
            memory["user_profile"] = {}
        if "preferences" not in memory["user_profile"]:
            memory["user_profile"]["preferences"] = {}

        memory["user_profile"]["preferences"][key] = value
        await self._save_profile(user_id, memory)

        if self.vector_store:
            try:
                await self.vector_store.add_document(
                    content=f"User preference: {key} = {value}",
                    user_id=user_id,
                    metadata={"type": "preference", "key": key},
                )
            except Exception as e:
                logger.error(f"Failed to add preference to vector store: {e}")

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        """Get all user preferences"""
        memory = await self._get_or_create_profile(user_id)
        return memory.get("user_profile", {}).get("preferences", {})

    def get_extraction_stats(self, user_id: str) -> dict[str, int]:
        """Get fact extraction statistics"""
        # Note: Since this is synchronous and we don't have memory cached here,
        # it's better to fetch it if needed or just return a default
        return {"total_extractions": 0, "successful_llm_extractions": 0, "fallback_extractions": 0}


# Singleton instance
_core_memory: Optional["CoreMemory"] = None


def get_core_memory() -> "CoreMemory":
    """Get or create the CoreMemory singleton"""
    global _core_memory
    if _core_memory is None:
        _core_memory = CoreMemory()
    return _core_memory
