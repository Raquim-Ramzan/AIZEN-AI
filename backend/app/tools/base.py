from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.parameters: Dict[str, Any] = {}
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool"""
        pass
    
    async def validate(self, **kwargs) -> bool:
        """Validate parameters before execution"""
        required_params = self.parameters.get("required", [])
        for param in required_params:
            if param not in kwargs:
                return False
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
