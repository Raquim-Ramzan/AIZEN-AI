from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base class for all tools"""

    def __init__(self):
        self.name: str = ""
        self.description: str = ""
        self.parameters: dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs) -> dict[str, Any]:
        """Execute the tool"""
        pass

    async def validate(self, **kwargs) -> bool:
        """Validate parameters before execution"""
        required_params = self.parameters.get("required", [])
        for param in required_params:
            if param not in kwargs:
                return False
        return True

    def get_schema(self) -> dict[str, Any]:
        """Get tool schema for LLM function calling"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
