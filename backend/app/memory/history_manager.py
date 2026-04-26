"""
History Manager for AIZEN
=========================
Manages conversation history with:
- Bounded context windows
- Smart summarization for long conversations
- Token counting approximation
"""

import logging
from datetime import UTC, datetime
from typing import Any

import google.generativeai as genai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HistoryManager:
    """
    Manages conversation history with bounded windows and summarization.
    Prevents unbounded history from consuming too many tokens.
    """

    # Approximate tokens per character (for English text)
    TOKENS_PER_CHAR = 0.25

    # Maximum context window in tokens
    MAX_CONTEXT_TOKENS = 30000  # Leave room for response

    # When to trigger summarization (% of max tokens)
    SUMMARIZE_THRESHOLD = 0.7

    # Number of recent messages to preserve (not summarized)
    PRESERVE_RECENT = 10

    def __init__(self):
        self.model_name = "gemini-2.5-flash"
        self._initialized = False

    def initialize(self):
        """Initialize the manager"""
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self._initialized = True
            logger.info("History Manager initialized")

    def estimate_tokens(self, messages: list[dict[str, str]]) -> int:
        """Estimate token count for messages"""
        total_chars = sum(
            len(msg.get("content", "")) + len(msg.get("role", "")) for msg in messages
        )
        return int(total_chars * self.TOKENS_PER_CHAR)

    async def prepare_history(
        self, messages: list[dict[str, str]], max_tokens: int | None = None
    ) -> dict[str, Any]:
        """
        Prepare conversation history for LLM input.

        Strategies:
        1. If under threshold, return as-is
        2. If over threshold, summarize older messages
        3. Always preserve most recent messages

        Args:
            messages: Full conversation history
            max_tokens: Optional override for max tokens

        Returns:
            - prepared_messages: Messages ready for LLM
            - summary: Optional summary of older messages
            - original_count: Number of original messages
            - token_estimate: Estimated tokens
        """
        max_tokens = max_tokens or self.MAX_CONTEXT_TOKENS
        current_tokens = self.estimate_tokens(messages)

        result = {
            "prepared_messages": messages,
            "summary": None,
            "original_count": len(messages),
            "token_estimate": current_tokens,
            "was_summarized": False,
        }

        # Check if under threshold
        if current_tokens <= max_tokens * self.SUMMARIZE_THRESHOLD:
            return result

        # Need to reduce history
        logger.info(f"History too long ({current_tokens} tokens). Summarizing...")

        # Split into recent (preserve) and older (summarize)
        if len(messages) <= self.PRESERVE_RECENT:
            # Can't summarize, just truncate
            result["prepared_messages"] = messages[-self.PRESERVE_RECENT :]
            result["token_estimate"] = self.estimate_tokens(result["prepared_messages"])
            return result

        older_messages = messages[: -self.PRESERVE_RECENT]
        recent_messages = messages[-self.PRESERVE_RECENT :]

        # Summarize older messages
        summary = await self._summarize_messages(older_messages)
        result["summary"] = summary
        result["was_summarized"] = True

        # Create new message list with summary + recent
        if summary:
            summary_message = {
                "role": "system",
                "content": f"[CONVERSATION SUMMARY - Earlier messages summarized below]\n{summary}\n[END SUMMARY - Recent messages follow]",
            }
            result["prepared_messages"] = [summary_message] + recent_messages
        else:
            result["prepared_messages"] = recent_messages

        result["token_estimate"] = self.estimate_tokens(result["prepared_messages"])

        return result

    async def _summarize_messages(self, messages: list[dict[str, str]]) -> str | None:
        """Summarize a list of messages"""
        if not self._initialized or not messages:
            return None

        # Format messages
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")[:500]  # Truncate long messages
            formatted.append(f"{role}: {content}")

        conversation = "\n".join(formatted)

        prompt = f"""Summarize this conversation, preserving key information, decisions, and context that might be relevant for continuing the discussion.

CONVERSATION:
{conversation}

Provide a concise summary (max 500 words) that captures:
1. Main topics discussed
2. Key information shared (names, preferences, facts)
3. Any decisions or conclusions reached
4. Important context for continuing

SUMMARY:"""

        try:
            model = genai.GenerativeModel(self.model_name)
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3, max_output_tokens=800
                ),
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None

    def truncate_to_tokens(
        self, messages: list[dict[str, str]], max_tokens: int
    ) -> list[dict[str, str]]:
        """Simple truncation: keep newest messages up to token limit"""
        result = []
        current_tokens = 0

        # Start from newest
        for msg in reversed(messages):
            msg_tokens = self.estimate_tokens([msg])
            if current_tokens + msg_tokens > max_tokens:
                break
            result.insert(0, msg)
            current_tokens += msg_tokens

        return result

    def get_stats(self) -> dict[str, Any]:
        """Get manager statistics"""
        return {
            "initialized": self._initialized,
            "max_context_tokens": self.MAX_CONTEXT_TOKENS,
            "summarize_threshold": self.SUMMARIZE_THRESHOLD,
            "preserve_recent": self.PRESERVE_RECENT,
        }


# Sliding window for real-time message tracking
class SlidingWindowHistory:
    """
    Maintains a sliding window of recent messages.
    Useful for WebSocket connections where messages accumulate.
    """

    def __init__(self, max_messages: int = 100, max_tokens: int = 20000):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: list[dict[str, str]] = []
        self.history_manager = HistoryManager()

    def add_message(self, role: str, content: str):
        """Add a message to the window"""
        self.messages.append(
            {"role": role, "content": content, "timestamp": datetime.now(UTC).isoformat()}
        )

        # Enforce limits
        self._enforce_limits()

    def _enforce_limits(self):
        """Enforce message and token limits"""
        # Message count limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

        # Token limit
        while self.history_manager.estimate_tokens(self.messages) > self.max_tokens:
            if len(self.messages) > 1:
                self.messages.pop(0)
            else:
                break

    def get_messages(self) -> list[dict[str, str]]:
        """Get current messages (without timestamps for LLM)"""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def clear(self):
        """Clear history"""
        self.messages = []


# Singleton
_history_manager: HistoryManager | None = None


def get_history_manager() -> HistoryManager:
    """Get or create history manager"""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
        _history_manager.initialize()
    return _history_manager
