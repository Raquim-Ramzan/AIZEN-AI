"""
System Operation Executor
Handles execution of system operations triggered by AI tool calls
"""

import logging
import uuid
import webbrowser
from typing import Dict, Any, Optional
from app.core.security_manager import (
    get_security_manager,
    SystemOperation,
    OperationRiskLevel,
    OperationStatus
)
from app.system.file_operations import get_file_operations
from app.system.process_manager import get_process_manager
from app.system.desktop_automation import get_desktop_automation
from app.system.system_info import get_system_info

logger = logging.getLogger(__name__)


class SystemOperationExecutor:
    """Executes system operations with security approval workflow"""
    
    def __init__(self):
        self.security_manager = get_security_manager()
        self.file_ops = get_file_operations()
        self.process_mgr = get_process_manager()
        self.desktop_auto = get_desktop_automation()
        self.system_info = get_system_info()
    
    async def execute_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool call with security approval
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            user_id: User requesting the operation
            
        Returns:
            Result dict with status, operation_id, and result/error
        """
        logger.info(f"Executing tool: {tool_name} with params: {parameters}")
        
        # Map tool names to handlers
        handlers = {
            "open_url": self._open_url,
            "start_process": self._start_process,
            "list_processes": self._list_processes,
            "kill_process": self._kill_process,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "search_files": self._search_files,
            "delete_file": self._delete_file,
            "get_system_stats": self._get_system_stats,
            "get_cpu_info": self._get_cpu_info,
            "get_memory_info": self._get_memory_info,
            "get_disk_info": self._get_disk_info,
            "type_text": self._type_text,
            "press_key": self._press_key,
            "search_web": self._search_web,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
        
        try:
            return await handler(parameters, user_id)
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ WEB OPERATIONS ============
    
    async def _open_url(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Open a URL in the default browser"""
        url = params.get("url")
        reason = params.get("reason", "User requested")
        
        # Create operation
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="url_open",
            description=f"Open URL: {url}",
            risk_level=OperationRiskLevel.NEEDS_APPROVAL,
            parameters={"url": url, "reason": reason},
            user_id=user_id
        )
        
        # Check if approval is required
        if self.security_manager.requires_approval(op):
            # Store as pending and return
            self.security_manager.pending_operations[op.id] = op
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "pending_approval",
                "message": f"Approval required to open {url}"
            }
        
        # Execute if auto-approved
        try:
            webbrowser.open(url)
            op.status = OperationStatus.COMPLETED
            op.result = {"url": url, "opened": True}
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": {"url": url, "opened": True}
            }
        except Exception as e:
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _search_web(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Search the web using Perplexity AI"""
        query = params.get("query")
        
        # Create operation
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="web_search",
            description=f"Search web for: {query}",
            risk_level=OperationRiskLevel.SAFE,
            parameters={"query": query},
            user_id=user_id
        )
        
        try:
            from app.core.brain import AIBrain, ModelProvider
            brain = AIBrain()
            await brain.initialize()
            
            messages = [
                {"role": "system", "content": "You are a web search assistant. Provide search results for the given query."},
                {"role": "user", "content": query}
            ]
            
            # Use Perplexity via AIBrain
            response = await brain.generate(
                messages=messages,
                provider=ModelProvider.PERPLEXITY
            )
            
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "No results found.")
            
            op.status = OperationStatus.COMPLETED
            op.result = {"query": query, "results": content}
            self.security_manager.log_operation(op)
            
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": content
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }

    # ============ PROCESS OPERATIONS ============
    
    async def _start_process(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Start a process"""
        command = params.get("command")
        args = params.get("args", [])
        reason = params.get("reason", "User requested")
        
        # Create operation
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="process_start",
            description=f"Start process: {command}",
            risk_level=OperationRiskLevel.NEEDS_APPROVAL,
            parameters={"command": command, "args": args, "reason": reason},
            user_id=user_id
        )
        
        if self.security_manager.requires_approval(op):
            self.security_manager.pending_operations[op.id] = op
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "pending_approval",
                "message": f"Approval required to start {command}"
            }
        
        # Execute
        try:
            result = await self.process_mgr.start_process(command=command, args=args, wait=False)
            op.status = OperationStatus.COMPLETED
            op.result = result
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _list_processes(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """List running processes (safe operation)"""
        sort_by = params.get("sort_by", "cpu")
        limit = params.get("limit", 10)
        
        try:
            result = await self.process_mgr.list_processes(sort_by=sort_by, limit=limit)
            return {
                "success": True,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _kill_process(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Kill a process (dangerous operation)"""
        name = params.get("name")
        pid = params.get("pid")
        force = params.get("force", False)
        
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="process_kill",
            description=f"Kill process: {name or pid}",
            risk_level=OperationRiskLevel.DANGEROUS,
            parameters={"name": name, "pid": pid, "force": force},
            user_id=user_id
        )
        
        if self.security_manager.requires_approval(op):
            self.security_manager.pending_operations[op.id] = op
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "pending_approval",
                "message": f"Approval required to kill process {name or pid}"
            }
        
        try:
            result = await self.process_mgr.kill_process(name=name, pid=pid, force=force)
            op.status = OperationStatus.COMPLETED
            op.result = result
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ FILE OPERATIONS ============
    
    async def _read_file(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Read file (safe operation)"""
        path = params.get("path")
        encoding = params.get("encoding", "utf-8")
        
        try:
            result = await self.file_ops.read_file(path=path, encoding=encoding)
            return {
                "success": True,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _write_file(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Write to file (needs approval)"""
        path = params.get("path")
        content = params.get("content")
        create_dirs = params.get("create_dirs", True)
        
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="file_write",
            description=f"Write to file: {path}",
            risk_level=OperationRiskLevel.NEEDS_APPROVAL,
            parameters={"path": path, "content_length": len(content), "create_dirs": create_dirs},
            user_id=user_id
        )
        
        if self.security_manager.requires_approval(op):
            self.security_manager.pending_operations[op.id] = op
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "pending_approval",
                "message": f"Approval required to write to {path}"
            }
        
        try:
            result = await self.file_ops.write_file(path=path, content=content, create_dirs=create_dirs)
            op.status = OperationStatus.COMPLETED
            op.result = result
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _search_files(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Search for files (safe operation)"""
        start_path = params.get("start_path")
        pattern = params.get("pattern")
        max_results = params.get("max_results", 100)
        
        try:
            result = await self.file_ops.search_files(start_path=start_path, pattern=pattern, max_results=max_results)
            return {
                "success": True,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _delete_file(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Delete file (dangerous operation)"""
        path = params.get("path")
        use_recycle_bin = params.get("use_recycle_bin", True)
        
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="file_delete",
            description=f"Delete file: {path}",
            risk_level=OperationRiskLevel.DANGEROUS,
            parameters={"path": path, "use_recycle_bin": use_recycle_bin},
            user_id=user_id
        )
        
        if self.security_manager.requires_approval(op):
            self.security_manager.pending_operations[op.id] = op
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "pending_approval",
                "message": f"Approval required to delete {path}"
            }
        
        try:
            result = await self.file_ops.delete_file(path=path, use_recycle_bin=use_recycle_bin)
            op.status = OperationStatus.COMPLETED
            op.result = result
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ SYSTEM INFO ============
    
    async def _get_system_stats(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Get system stats (safe operation)"""
        try:
            result = await self.process_mgr.get_system_stats()
            return {
                "success": True,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_cpu_info(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Get CPU info (safe operation)"""
        interval = params.get("interval", 1.0)
        
        try:
            result = await self.system_info.get_cpu_info(interval=interval)
            return {
                "success": True,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_memory_info(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Get memory info (safe operation)"""
        try:
            result = await self.system_info.get_memory_info()
            return {
                "success": True,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_disk_info(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Get disk info (safe operation)"""
        path = params.get("path", "C:\\")
        
        try:
            result = await self.system_info.get_disk_info(path=path)
            return {
                "success": True,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # ============ DESKTOP AUTOMATION ============
    
    async def _type_text(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Type text (needs approval)"""
        text = params.get("text")
        interval = params.get("interval", 0.01)
        
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="keyboard_type",
            description=f"Type text ({len(text)} chars)",
            risk_level=OperationRiskLevel.NEEDS_APPROVAL,
            parameters={"text_length": len(text), "interval": interval},
            user_id=user_id
        )
        
        if self.security_manager.requires_approval(op):
            self.security_manager.pending_operations[op.id] = op
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "pending_approval",
                "message": "Approval required to type text"
            }
        
        try:
            result = await self.desktop_auto.type_text(text=text, interval=interval)
            op.status = OperationStatus.COMPLETED
            op.result = result
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _press_key(self, params: Dict[str, Any], user_id: Optional[str]) -> Dict[str, Any]:
        """Press keys (needs approval)"""
        keys = params.get("keys", [])
        
        op = SystemOperation(
            id=str(uuid.uuid4()),
            operation_type="keyboard_type",
            description=f"Press keys: {', '.join(keys)}",
            risk_level=OperationRiskLevel.NEEDS_APPROVAL,
            parameters={"keys": keys},
            user_id=user_id
        )
        
        if self.security_manager.requires_approval(op):
            self.security_manager.pending_operations[op.id] = op
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "pending_approval",
                "message": f"Approval required to press keys: {', '.join(keys)}"
            }
        
        try:
            # Execute hotkey
            if len(keys) > 1:
                result = await self.desktop_auto.hotkey(*keys)
            else:
                result = await self.desktop_auto.press_key(key=keys[0])
            
            op.status = OperationStatus.COMPLETED
            op.result = result
            self.security_manager.log_operation(op)
            return {
                "success": True,
                "operation_id": op.id,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            op.status = OperationStatus.FAILED
            op.error = str(e)
            self.security_manager.log_operation(op)
            return {
                "success": False,
                "error": str(e)
            }


# Global executor instance
_executor = None


def get_system_executor() -> SystemOperationExecutor:
    """Get the global system operation executor instance"""
    global _executor
    if _executor is None:
        _executor = SystemOperationExecutor()
    return _executor
