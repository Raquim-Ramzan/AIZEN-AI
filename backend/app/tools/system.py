import logging
import platform
import psutil
from typing import Dict, Any
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

class SystemTool(BaseTool):
    """System information and monitoring tool"""
    
    def __init__(self):
        super().__init__()
        self.name = "system"
        self.description = "Get system information, monitor resources, and check process status"
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["info", "resources", "processes"],
                    "description": "System operation"
                }
            },
            "required": ["operation"]
        }
    
    async def execute(self, operation: str) -> Dict[str, Any]:
        """Execute system operation"""
        try:
            if operation == "info":
                return await self._get_system_info()
            elif operation == "resources":
                return await self._get_resources()
            elif operation == "processes":
                return await self._get_processes()
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            logger.error(f"System operation error: {e}")
            return {"error": str(e)}
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "operation": "info",
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    
    async def _get_resources(self) -> Dict[str, Any]:
        """Get system resource usage"""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "operation": "resources",
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent
            }
        }
    
    async def _get_processes(self) -> Dict[str, Any]:
        """Get running processes info"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage and get top 10
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        
        return {
            "operation": "processes",
            "top_processes": processes[:10],
            "total_count": len(processes)
        }
