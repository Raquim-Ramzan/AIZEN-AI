import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ModelProvider(str, Enum):
    """Available AI model providers"""
    GEMINI = "gemini"
    GROQ = "groq"
    PERPLEXITY = "perplexity"
    OLLAMA = "ollama"

class TaskType(str, Enum):
    """Task types for intelligent routing"""
    CODING = "coding"
    COMPLEX_REASONING = "complex_reasoning"
    GENERAL_CHAT = "general_chat"
    WEB_SEARCH = "web_search"
    DEEP_RESEARCH = "deep_research"
    IMAGE_GENERATION = "image_generation"
    FAST_STREAMING = "fast_streaming"
    SIMPLE_QUERY = "simple_query"
    FILE_OPERATION = "file_operation"
    CODE_EXECUTION = "code_execution"
    CALENDAR_TASK = "calendar_task"
    SYSTEM_OPERATION = "system_operation"
    MULTI_STEP = "multi_step"

class ModelRouter:
    """Intelligent model routing system for multi-provider AI"""
    
    def __init__(self):
        self.settings = get_settings()
        self._initialize_routing_table()
    
    def _initialize_routing_table(self):
        """Initialize task-to-model routing table"""
        self.routing_table = {
            TaskType.CODING: {
                "provider": ModelProvider.GEMINI,
                "model": self.settings.model_coding,
                "fallback": [(ModelProvider.GROQ, "llama-3.3-70b-versatile"), (ModelProvider.OLLAMA, self.settings.ollama_model)]
            },
            TaskType.COMPLEX_REASONING: {
                "provider": ModelProvider.GEMINI,
                "model": self.settings.model_reasoning,
                "fallback": [(ModelProvider.GROQ, "llama-3.3-70b-versatile"), (ModelProvider.OLLAMA, self.settings.ollama_model)]
            },
            TaskType.GENERAL_CHAT: {
                "provider": ModelProvider.GEMINI,
                "model": self.settings.model_chat,
                "fallback": [(ModelProvider.GROQ, "groq/compound"), (ModelProvider.OLLAMA, self.settings.ollama_model)]
            },
            TaskType.WEB_SEARCH: {
                "provider": ModelProvider.PERPLEXITY,
                "model": self.settings.model_search,
                "fallback": [(ModelProvider.GEMINI, self.settings.model_chat), (ModelProvider.OLLAMA, self.settings.ollama_model)]
            },
            TaskType.DEEP_RESEARCH: {
                "provider": ModelProvider.PERPLEXITY,
                "model": self.settings.model_research,
                "fallback": [(ModelProvider.PERPLEXITY, self.settings.model_search), (ModelProvider.GEMINI, self.settings.model_reasoning)]
            },
            TaskType.FAST_STREAMING: {
                "provider": ModelProvider.GROQ,
                "model": self.settings.model_fast_streaming,
                "fallback": [(ModelProvider.GEMINI, self.settings.model_chat), (ModelProvider.OLLAMA, self.settings.ollama_model)]
            },
            TaskType.SIMPLE_QUERY: {
                "provider": ModelProvider.GEMINI,
                "model": self.settings.model_chat,
                "fallback": [(ModelProvider.OLLAMA, self.settings.ollama_model)]
            },
            TaskType.CODE_EXECUTION: {
                "provider": ModelProvider.GEMINI,
                "model": self.settings.model_coding,
                "fallback": [(ModelProvider.OLLAMA, self.settings.ollama_model)]
            },
        }
    
    def select_model(
        self,
        task_type: TaskType,
        manual_provider: Optional[ModelProvider] = None,
        manual_model: Optional[str] = None
    ) -> Tuple[ModelProvider, str]:
        """
        Select the optimal model for a given task type.
        
        Args:
            task_type: Type of task to perform
            manual_provider: Optional manual provider override
            manual_model: Optional manual model override
            
        Returns:
            Tuple of (provider, model_name)
        """
        # Manual override takes precedence
        if manual_provider and manual_model:
            logger.info(f"Using manual model selection: {manual_provider}/{manual_model}")
            return (manual_provider, manual_model)
        
        # Get routing info for task type
        route = self.routing_table.get(task_type)
        if not route:
            logger.warning(f"No routing info for task type {task_type}, defaulting to general chat")
            route = self.routing_table[TaskType.GENERAL_CHAT]
        
        provider = route["provider"]
        model = route["model"]
        
        # Check if provider is available
        if self._is_provider_available(provider):
            logger.info(f"Selected {provider}/{model} for task type {task_type}")
            return (provider, model)
        
        # Try fallback chain
        for fallback_provider, fallback_model in route.get("fallback", []):
            if self._is_provider_available(fallback_provider):
                logger.info(f"Using fallback {fallback_provider}/{fallback_model} for task type {task_type}")
                return (fallback_provider, fallback_model)
        
        # Last resort: Ollama
        logger.warning(f"All providers unavailable for {task_type}, falling back to Ollama")
        return (ModelProvider.OLLAMA, self.settings.ollama_model)
    
    def _is_provider_available(self, provider: ModelProvider) -> bool:
        """Check if a provider is configured and available"""
        if provider == ModelProvider.GEMINI:
            return bool(self.settings.gemini_api_key)
        elif provider == ModelProvider.GROQ:
            return bool(self.settings.groq_api_key)
        elif provider == ModelProvider.PERPLEXITY:
            return bool(self.settings.perplexity_api_key)
        elif provider == ModelProvider.OLLAMA:
            return True  # Ollama is always "available" (will be checked at runtime)
        return False
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of all available models by provider"""
        available = {
            "gemini": {
                "available": self._is_provider_available(ModelProvider.GEMINI),
                "models": [
                    {"name": "gemini-3-flash", "description": "2026 standard for high-volume chat and coding"},
                    {"name": "gemini-3.1-pro", "description": "The peak of reasoning and agentic workflows"},
                    {"name": "gemini-3-pro-preview", "description": "Advanced reasoning (legacy preview)"},
                ]
            },
            "groq": {
                "available": self._is_provider_available(ModelProvider.GROQ),
                "models": [
                    {"name": "llama-3.3-70b-versatile", "description": "Large model for complex reasoning"},
                    {"name": "groq/compound", "description": "Optimized for ultra-fast streaming"},
                    {"name": "groq/compound-mini", "description": "Smaller, faster compound model"},
                ]
            },
            "perplexity": {
                "available": self._is_provider_available(ModelProvider.PERPLEXITY),
                "models": [
                    {"name": "sonar-pro", "description": "Advanced search with citations"},
                    {"name": "sonar-deep-research", "description": "Comprehensive research tasks"},
                    {"name": "sonar-reasoning", "description": "Reasoning with search"},
                    {"name": "sonar-reasoning-pro", "description": "Advanced reasoning with search"},
                ]
            },
            "ollama": {
                "available": True,
                "models": [
                    {"name": self.settings.ollama_model, "description": "Local offline model"},
                ]
            }
        }
        return available
    
    def get_routing_info(self) -> Dict[TaskType, Dict[str, Any]]:
        """Get the current routing configuration"""
        return {
            task_type: {
                "primary_provider": route["provider"],
                "primary_model": route["model"],
                "fallback_chain": route.get("fallback", [])
            }
            for task_type, route in self.routing_table.items()
        }
    
    def map_gemini_model_name(self, model_name: str) -> str:
        """Map user-friendly model names to Gemini API model names"""
        model_mapping = {
            "gemini-3-flash-preview": "models/gemini-3-flash-preview",
            "gemini-3.1-pro-preview": "models/gemini-3.1-pro-preview",
            "gemini-3-pro-preview": "models/gemini-3-pro-preview",
            "text-embedding-004": "models/text-embedding-004",
            "imagen-4-ultra": "models/imagen-4-ultra",
        }
        mapped = model_mapping.get(model_name, model_name)
        if not mapped.startswith("models/"):
            mapped = f"models/{mapped}"
        return mapped
    
    def map_groq_model_name(self, model_name: str) -> str:
        """Map user-friendly model names to Groq API model names"""
        model_mapping = {
            "groq-compound": "groq/compound",
            "groq-compound-mini": "groq/compound-mini",
            "llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant": "llama-3.1-8b-instant",
        }
        return model_mapping.get(model_name, model_name)
    
    def map_perplexity_model_name(self, model_name: str) -> str:
        """Map user-friendly model names to Perplexity API model names"""
        model_mapping = {
            "sonar-pro": "sonar-pro",
            "sonar": "sonar",
            "sonar-reasoning": "sonar-reasoning",
            "sonar-reasoning-pro": "sonar-reasoning-pro",
            "sonar-deep-research": "sonar-deep-research",
        }
        return model_mapping.get(model_name, model_name)
