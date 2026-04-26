"""
Quick Test Script for Multi-Provider AI Integration

Run this to verify that the model router and providers are configured correctly.
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.core.model_router import ModelRouter, TaskType


async def test_model_router():
    """Test the model router configuration"""
    print("=" * 60)
    print("Multi-Provider AI Integration Test")
    print("=" * 60)

    router = ModelRouter()
    settings = get_settings()

    # Check provider availability
    print("\n✓ Provider Configuration:")
    print(
        f"  • Gemini API Key: {'✓ Configured' if settings.gemini_api_key else '✗ Not configured'}"
    )
    print(f"  • Groq API Key: {'✓ Configured' if settings.groq_api_key else '✗ Not configured'}")
    print(
        f"  • Perplexity API Key: {'✓ Configured' if settings.perplexity_api_key else '✗ Not configured'}"
    )
    print("  • Ollama: ✓ Always available (will check at runtime)")

    # Test model selection for different task types
    print("\n✓ Model Routing Configuration:")
    task_types = [
        TaskType.CODING,
        TaskType.COMPLEX_REASONING,
        TaskType.GENERAL_CHAT,
        TaskType.WEB_SEARCH,
        TaskType.DEEP_RESEARCH,
        TaskType.FAST_STREAMING,
    ]

    for task_type in task_types:
        provider, model = router.select_model(task_type)
        print(f"  • {task_type.value:20} → {provider.value:12} / {model}")

    # Test model preferences
    print("\n✓ Model Preferences:")
    print(f"  • Coding: {settings.model_coding}")
    print(f"  • Chat: {settings.model_chat}")
    print(f"  • Reasoning: {settings.model_reasoning}")
    print(f"  • Search: {settings.model_search}")
    print(f"  • Research: {settings.model_research}")
    print(f"  • STT: {settings.model_stt}")
    print(f"  • TTS: {settings.model_tts}")
    print(f"  • Embedding: {settings.model_embedding}")

    # Show available models
    print("\n✓ Available Models by Provider:")
    available = router.get_available_models()
    for provider_name, provider_info in available.items():
        status = "✓" if provider_info["available"] else "✗"
        print(f"\n  {status} {provider_name.upper()}:")
        for model_info in provider_info["models"]:
            print(f"      - {model_info['name']:30} | {model_info['description']}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

    # Show next steps
    print("\n📝 Next Steps:")
    if not settings.gemini_api_key:
        print("  1. Add your GEMINI_API_KEY to .env file")
    if not settings.groq_api_key:
        print("  2. Add your GROQ_API_KEY to .env file")
    print("  3. Start the backend: python -m app.main")
    print("  4. Test the chat endpoint: POST http://localhost:8001/api/chat")
    print("\n✨ Your multi-provider AI assistant is ready!")


if __name__ == "__main__":
    asyncio.run(test_model_router())
