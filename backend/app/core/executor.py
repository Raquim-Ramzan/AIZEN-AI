import asyncio
import logging
from typing import Any

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Execute tools based on plan"""

    def __init__(self):
        self.tools: dict[str, BaseTool] = {}
        self.execution_history = []

    def register_tool(self, tool: BaseTool):
        """Register a tool for execution"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    async def execute_tool(self, tool_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Execute a single tool"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}

        tool = self.tools[tool_name]

        try:
            # Validate parameters
            if not await tool.validate(**parameters):
                return {"error": f"Invalid parameters for tool '{tool_name}'"}

            # Execute tool
            result = await tool.execute(**parameters)

            # Log execution
            self.execution_history.append(
                {
                    "tool": tool_name,
                    "parameters": parameters,
                    "result": result,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )

            return result

        except Exception as e:
            logger.error(f"Tool execution error for '{tool_name}': {e}")
            return {"error": str(e)}

    async def execute_plan(self, plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute a multi-step plan"""
        results = []

        for step in plan:
            tool_name = step.get("tool")
            if tool_name:
                result = await self.execute_tool(tool_name, step.get("parameters", {}))
                results.append({"step": step["step"], "action": step["action"], "result": result})
            else:
                # Non-tool step (e.g., analysis, formatting)
                results.append(
                    {
                        "step": step["step"],
                        "action": step["action"],
                        "result": {"status": "skipped"},
                    }
                )

        return results

    async def execute_parallel(self, tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute multiple tools in parallel"""
        tasks = []

        for call in tool_calls:
            task = self.execute_tool(call["tool"], call["parameters"])
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        formatted_results = []
        for _i, result in enumerate(results):
            if isinstance(result, Exception):
                formatted_results.append({"error": str(result)})
            else:
                formatted_results.append(result)

        return formatted_results

    def get_available_tools(self) -> list[dict[str, Any]]:
        """Get list of available tools"""
        return [
            {"name": tool.name, "description": tool.description, "parameters": tool.parameters}
            for tool in self.tools.values()
        ]
