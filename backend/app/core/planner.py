import logging
from typing import List, Dict, Any, Optional, Tuple
import json
from app.core.model_router import TaskType, ModelRouter, ModelProvider

logger = logging.getLogger(__name__)

class TaskPlanner:
    """Task planning and orchestration with intelligent model routing"""
    
    def __init__(self):
        self.task_registry = {}
        self.model_router = ModelRouter()
    
    async def analyze_intent(self, user_message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze user intent using AI-powered classification.
        Uses Gemini 2.5 Flash for fast, cheap, and accurate intent detection.
        """
        # Default intent
        intent = {
            "task_type": TaskType.SIMPLE_QUERY,
            "requires_tools": False,
            "tools_needed": [],
            "complexity": "low",
            "steps": []
        }
        
        # Use AI to classify the task type
        classified_type = await self._classify_task_with_ai(user_message)
        
        # Map AI classification to task types and set appropriate flags
        if classified_type == "CODING":
            intent["task_type"] = TaskType.CODING
            intent["complexity"] = "high"
            intent["requires_tools"] = False
        
        elif classified_type == "REASONING":
            intent["task_type"] = TaskType.COMPLEX_REASONING
            intent["complexity"] = "high"
        
        elif classified_type == "SEARCH":
            intent["task_type"] = TaskType.WEB_SEARCH
            intent["requires_tools"] = True
            intent["tools_needed"] = ["web_search"]
            intent["complexity"] = "medium"
        
        elif classified_type == "RESEARCH":
            intent["task_type"] = TaskType.DEEP_RESEARCH
            intent["requires_tools"] = True
            intent["tools_needed"] = ["web_search"]
            intent["complexity"] = "high"
        
        elif classified_type == "FILE":
            intent["task_type"] = TaskType.FILE_OPERATION
            intent["requires_tools"] = True
            intent["tools_needed"] = ["file_ops"]
        
        elif classified_type == "EXECUTE":
            intent["task_type"] = TaskType.CODE_EXECUTION
            intent["requires_tools"] = True
            intent["tools_needed"] = ["code_exec"]
            intent["complexity"] = "high"
        
        elif classified_type == "CALENDAR":
            intent["task_type"] = TaskType.CALENDAR_TASK
            intent["requires_tools"] = True
            intent["tools_needed"] = ["calendar"]
        
        elif classified_type == "IMAGE":
            intent["task_type"] = TaskType.IMAGE_GENERATION
            intent["requires_tools"] = False
            intent["complexity"] = "medium"
        
        else:  # CHAT or unknown
            intent["task_type"] = TaskType.GENERAL_CHAT
            intent["complexity"] = "low"
        
        return intent
    
    async def _classify_task_with_ai(self, user_message: str) -> str:
        """
        Use Gemini 2.5 Flash to classify the task type.
        Fast, cheap, and accurate AI-powered classification.
        
        Returns one of: CODING, REASONING, SEARCH, RESEARCH, FILE, EXECUTE, CALENDAR, IMAGE, CHAT
        """
        try:
            import google.generativeai as genai
            from app.config import get_settings
            
            settings = get_settings()
            
            # Only use AI classification if Gemini is configured
            if not settings.gemini_api_key:
                # Fallback to keyword-based if no API key
                return self._classify_with_keywords(user_message)
            
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            classification_prompt = f"""You are a task classifier. Analyze the user's message and classify it into ONE category.

User message: "{user_message}"

Respond with ONLY ONE WORD from these options:
- CODING: Writing, debugging, or explaining code (any programming language)
- REASONING: Complex analysis, comparisons, pros/cons, logical deduction
- SEARCH: Looking up current information, news, facts, "what is", "who is"
- RESEARCH: Deep investigation, comprehensive analysis, thorough study
- FILE: File operations (read, write, save, open files)
- EXECUTE: Running or executing code
- CALENDAR: Scheduling, reminders, appointments, time management  
- IMAGE: Generating, creating, or editing images
- CHAT: General conversation, greetings, simple questions

Respond with ONLY the category word, nothing else."""

            response = model.generate_content(
                classification_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent classification
                    max_output_tokens=10,  # We only need one word
                )
            )
            
            # Check if response has valid parts before accessing .text
            if not response.parts or len(response.parts) == 0:
                logger.warning(f"AI response has no parts (possibly quota exceeded or blocked), falling back to keywords")
                return self._classify_with_keywords(user_message)
            
            classification = response.text.strip().upper()
            
            # Validate response
            valid_types = ["CODING", "REASONING", "SEARCH", "RESEARCH", "FILE", "EXECUTE", "CALENDAR", "IMAGE", "CHAT"]
            if classification in valid_types:
                logger.info(f"AI classified '{user_message[:50]}...' as: {classification}")
                return classification
            else:
                logger.warning(f"Invalid AI classification: {classification}, defaulting to CHAT")
                return "CHAT"
                
        except Exception as e:
            # Handle quota exceeded, blocked content, or any other API errors
            logger.error(f"AI classification failed: {e}, falling back to keyword matching")
            return self._classify_with_keywords(user_message)
    
    def _classify_with_keywords(self, user_message: str) -> str:
        """Fallback keyword-based classification if AI is unavailable"""
        message_lower = user_message.lower()
        
        # Coding keywords
        if any(word in message_lower for word in [
            "write code", "code for", "code me", "function", "class for", "implement",
            "debug", "fix code", "refactor", "python", "javascript", "c++", "calculator"
        ]):
            return "CODING"
        
        # Search keywords
        elif any(word in message_lower for word in [
            "search", "find", "look up", "google", "what is", "who is", "latest"
        ]):
            return "SEARCH"
        
        # Reasoning keywords  
        elif any(word in message_lower for word in [
            "analyze", "compare", "evaluate", "pros and cons"
        ]):
            return "REASONING"
        
        # Default to chat
        return "CHAT"
    
    async def create_execution_plan(self, intent: Dict[str, Any], user_message: str) -> List[Dict[str, Any]]:
        """Create step-by-step execution plan"""
        plan = []
        
        if intent["task_type"] == TaskType.WEB_SEARCH:
            plan = [
                {
                    "step": 1,
                    "action": "search_web",
                    "tool": "web_search",
                    "parameters": {"query": user_message}
                },
                {
                    "step": 2,
                    "action": "analyze_results",
                    "tool": None,
                    "parameters": {}
                },
                {
                    "step": 3,
                    "action": "generate_response",
                    "tool": None,
                    "parameters": {}
                }
            ]
        elif intent["task_type"] == TaskType.CODE_EXECUTION:
            plan = [
                {
                    "step": 1,
                    "action": "extract_code",
                    "tool": None,
                    "parameters": {}
                },
                {
                    "step": 2,
                    "action": "execute_code",
                    "tool": "code_exec",
                    "parameters": {}
                },
                {
                    "step": 3,
                    "action": "format_result",
                    "tool": None,
                    "parameters": {}
                }
            ]
        elif intent["task_type"] == TaskType.DEEP_RESEARCH:
            plan = [
                {
                    "step": 1,
                    "action": "initial_search",
                    "tool": "web_search",
                    "parameters": {"query": user_message}
                },
                {
                    "step": 2,
                    "action": "deep_analysis",
                    "tool": None,
                    "parameters": {}
                },
                {
                    "step": 3,
                    "action": "synthesize_findings",
                    "tool": None,
                    "parameters": {}
                }
            ]
        else:
            # Simple query - direct response
            plan = [
                {
                    "step": 1,
                    "action": "generate_response",
                    "tool": None,
                    "parameters": {}
                }
            ]
        
        return plan
    
    async def select_model_provider(
        self,
        intent: Dict[str, Any],
        manual_provider: Optional[str] = None,
        manual_model: Optional[str] = None
    ) -> Tuple[ModelProvider, str]:
        """
        Select the optimal model provider and model for the given intent.
        Replaces the old should_use_ollama() method.
        
        Returns:
            Tuple of (provider, model_name)
        """
        # Manual selection takes precedence
        if manual_provider and manual_model:
            try:
                provider_enum = ModelProvider(manual_provider)
                return (provider_enum, manual_model)
            except ValueError:
                logger.warning(f"Invalid manual provider: {manual_provider}")
        
        # Get task type from intent
        task_type = intent.get("task_type", TaskType.SIMPLE_QUERY)
        
        # Use model router for intelligent selection
        provider, model = self.model_router.select_model(task_type)
        
        logger.info(f"Selected {provider}/{model} for task type {task_type}")
        return (provider, model)
    
    # Keep for backward compatibility
    async def should_use_ollama(self, intent: Dict[str, Any]) -> bool:
        """
        Deprecated: Use select_model_provider() instead.
        Kept for backward compatibility.
        """
        provider, _ = await self.select_model_provider(intent)
        return provider == ModelProvider.OLLAMA
