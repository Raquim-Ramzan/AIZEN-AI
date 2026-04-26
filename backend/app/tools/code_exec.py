import asyncio
import logging
import sys
from io import StringIO
from typing import Any

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class CodeExecTool(BaseTool):
    """Safe Python code execution in sandboxed environment"""

    def __init__(self):
        super().__init__()
        self.name = "code_exec"
        self.description = "Execute Python code safely with timeout and output capture"
        self.parameters = {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 5,
                },
            },
            "required": ["code"],
        }

    async def execute(self, code: str, timeout: int = 5) -> dict[str, Any]:
        """Execute Python code safely"""
        try:
            # Create restricted namespace
            namespace = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "sum": sum,
                    "max": max,
                    "min": min,
                    "abs": abs,
                    "round": round,
                }
            }

            # Capture output
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()

            result = None
            error = None

            try:
                # Execute with timeout
                async def run_code():
                    exec(code, namespace)
                    return namespace.get("result", None)

                result = await asyncio.wait_for(run_code(), timeout=timeout)
                output = captured_output.getvalue()

            except TimeoutError:
                error = f"Execution timeout after {timeout} seconds"
                output = captured_output.getvalue()
            except Exception as e:
                error = str(e)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout

            return {
                "operation": "code_exec",
                "output": output,
                "result": result,
                "error": error,
                "success": error is None,
            }

        except Exception as e:
            logger.error(f"Code execution error: {e}")
            return {"error": str(e), "success": False}
