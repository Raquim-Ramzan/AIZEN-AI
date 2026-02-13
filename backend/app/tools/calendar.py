import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from app.tools.base import BaseTool

logger = logging.getLogger(__name__)

class CalendarTool(BaseTool):
    """Calendar and task management tool"""
    
    def __init__(self):
        super().__init__()
        self.name = "calendar"
        self.description = "Schedule reminders, manage tasks, and track deadlines"
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["create_reminder", "list_reminders", "create_task", "list_tasks"],
                    "description": "Calendar operation"
                },
                "title": {
                    "type": "string",
                    "description": "Reminder or task title"
                },
                "time": {
                    "type": "string",
                    "description": "Time for reminder (ISO format)"
                },
                "description": {
                    "type": "string",
                    "description": "Task description"
                }
            },
            "required": ["operation"]
        }
        
        # In-memory storage (should be replaced with database)
        self.reminders = []
        self.tasks = []
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Execute calendar operation"""
        try:
            if operation == "create_reminder":
                return await self._create_reminder(kwargs.get("title"), kwargs.get("time"))
            elif operation == "list_reminders":
                return await self._list_reminders()
            elif operation == "create_task":
                return await self._create_task(kwargs.get("title"), kwargs.get("description"))
            elif operation == "list_tasks":
                return await self._list_tasks()
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            logger.error(f"Calendar operation error: {e}")
            return {"error": str(e)}
    
    async def _create_reminder(self, title: str, time: str) -> Dict[str, Any]:
        """Create a reminder"""
        try:
            reminder_time = datetime.fromisoformat(time) if time else datetime.now(timezone.utc) + timedelta(hours=1)
            
            reminder = {
                "id": len(self.reminders) + 1,
                "title": title,
                "time": reminder_time.isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.reminders.append(reminder)
            
            return {
                "operation": "create_reminder",
                "reminder": reminder,
                "success": True
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _list_reminders(self) -> Dict[str, Any]:
        """List all reminders"""
        return {
            "operation": "list_reminders",
            "reminders": self.reminders,
            "count": len(self.reminders)
        }
    
    async def _create_task(self, title: str, description: str = "") -> Dict[str, Any]:
        """Create a task"""
        task = {
            "id": len(self.tasks) + 1,
            "title": title,
            "description": description,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.tasks.append(task)
        
        return {
            "operation": "create_task",
            "task": task,
            "success": True
        }
    
    async def _list_tasks(self) -> Dict[str, Any]:
        """List all tasks"""
        return {
            "operation": "list_tasks",
            "tasks": self.tasks,
            "count": len(self.tasks)
        }
