"""
Conversation Namer Module
Uses lightweight LLM to generate meaningful conversation titles
"""

import logging
from datetime import datetime

import google.generativeai as genai

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ConversationNamer:
    """Generates meaningful conversation titles using LLM"""

    def __init__(self):
        self.model = None
        if settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                # Use Gemini 3 Flash Preview for fast title generation (2026 standard)
                self.model = genai.GenerativeModel("gemini-3-flash-preview")
                logger.info("ConversationNamer initialized with Gemini Flash")
            except Exception as e:
                logger.warning(f"Failed to initialize ConversationNamer: {e}")

    async def generate_title(self, first_message: str) -> str:
        """
        Generate a short, descriptive title for a conversation

        Args:
            first_message: The first user message in the conversation

        Returns:
            A short title (max 5 words)
        """
        # If no model available, use fallback
        if not self.model:
            return self._fallback_title(first_message)

        try:
            prompt = f"""Generate a short, descriptive title (max 5 words) for a conversation that starts with: "{first_message}"

Examples:
- "Write a Python sorting function" → "Python Sorting Function"
- "Help me plan a trip to Paris" → "Paris Trip Planning"
- "What's the weather today?" → "Weather Information"
- "Open YouTube" → "YouTube Access"
- "Tell me about AI" → "AI Discussion"
- "How do I fix this bug?" → "Bug Fixing Help"
- "Hello!" → "Friendly Chat"
- "What's your name?" → "Introduction"

Return ONLY the title, nothing else. No quotes, no explanation."""

            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower temperature for more consistent output
                    max_output_tokens=20,
                ),
            )

            title = response.text.strip()

            # Clean up the title
            title = title.strip("\"'")  # Remove quotes
            title = title.split("\n")[0]  # Take only first line

            # Ensure it's not too long
            words = title.split()
            if len(words) > 6:
                title = " ".join(words[:5])

            # Ensure it's not empty
            if not title:
                return self._fallback_title(first_message)

            logger.info(f"Generated title: {title}")
            return title

        except Exception as e:
            logger.error(f"Error generating conversation title: {e}")
            return self._fallback_title(first_message)

    def _fallback_title(self, first_message: str) -> str:
        """Fallback title generation if LLM fails"""
        # Take first 40 characters of message
        if len(first_message) > 40:
            title = first_message[:37] + "..."
        else:
            title = first_message

        # Clean up
        title = title.strip()
        if not title:
            title = f"Chat {datetime.now().strftime('%b %d')}"

        return title


# Global instance
_namer = None


def get_conversation_namer() -> ConversationNamer:
    """Get the global conversation namer instance"""
    global _namer
    if _namer is None:
        _namer = ConversationNamer()
    return _namer
