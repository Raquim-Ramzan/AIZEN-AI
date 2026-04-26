"""
System Operations API Routes
REST endpoints for system-level operations
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.security_manager import get_security_manager
from app.system.desktop_automation import get_desktop_automation
from app.system.file_operations import get_file_operations
from app.system.process_manager import get_process_manager
from app.system.registry_operations import get_registry_operations
from app.system.system_info import get_system_info

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system"])


# Request/Response Models
class FileReadRequest(BaseModel):
    path: str
    encoding: str | None = None


class FileWriteRequest(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"
    create_dirs: bool = True


class FileDeleteRequest(BaseModel):
    path: str
    use_recycle_bin: bool = True


class DirectoryListRequest(BaseModel):
    path: str
    recursive: bool = False
    pattern: str = "*"


class FileSearchRequest(BaseModel):
    start_path: str
    pattern: str
    max_results: int = 100


class ProcessStartRequest(BaseModel):
    command: str
    args: list[str] | None = None
    cwd: str | None = None
    wait: bool = False


class ProcessKillRequest(BaseModel):
    pid: int | None = None
    name: str | None = None
    force: bool = False


class KeyboardTypeRequest(BaseModel):
    text: str
    interval: float = 0.0


class KeyPressRequest(BaseModel):
    key: str
    presses: int = 1
    interval: float = 0.0


class HotkeyRequest(BaseModel):
    keys: list[str]


class MouseClickRequest(BaseModel):
    x: int | None = None
    y: int | None = None
    clicks: int = 1
    interval: float = 0.0
    button: str = "left"


class MouseMoveRequest(BaseModel):
    x: int
    y: int
    duration: float = 0.0


class RegistryReadRequest(BaseModel):
    path: str
    value_name: str = ""


class RegistryWriteRequest(BaseModel):
    path: str
    value_name: str
    value: Any
    value_type: str = "REG_SZ"


class ApprovalRequest(BaseModel):
    operation_id: str
    approved: bool
    remember: bool = False


# File Operations Endpoints
@router.post("/file/read")
async def read_file(request: FileReadRequest):
    """Read a file"""
    try:
        file_ops = get_file_operations()
        result = await file_ops.read_file(request.path, request.encoding)
        return result
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/file/write")
async def write_file(request: FileWriteRequest):
    """Write to a file"""
    try:
        file_ops = get_file_operations()
        result = await file_ops.write_file(
            request.path, request.content, request.encoding, request.create_dirs
        )
        return result
    except Exception as e:
        logger.error(f"Failed to write file: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/file/delete")
async def delete_file(request: FileDeleteRequest):
    """Delete a file"""
    try:
        file_ops = get_file_operations()
        result = await file_ops.delete_file(request.path, request.use_recycle_bin)
        return result
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/file/list")
async def list_directory(request: DirectoryListRequest):
    """List directory contents"""
    try:
        file_ops = get_file_operations()
        result = await file_ops.list_directory(request.path, request.recursive, request.pattern)
        return result
    except Exception as e:
        logger.error(f"Failed to list directory: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/file/search")
async def search_files(request: FileSearchRequest):
    """Search for files"""
    try:
        file_ops = get_file_operations()
        result = await file_ops.search_files(
            request.start_path, request.pattern, request.max_results
        )
        return result
    except Exception as e:
        logger.error(f"Failed to search files: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Process Management Endpoints
@router.get("/process/list")
async def list_processes(sort_by: str = "cpu", limit: int | None = None):
    """List running processes"""
    try:
        proc_mgr = get_process_manager()
        result = await proc_mgr.list_processes(sort_by, limit)
        return result
    except Exception as e:
        logger.error(f"Failed to list processes: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/process/info")
async def get_process_info(pid: int | None = None, name: str | None = None):
    """Get process information"""
    try:
        proc_mgr = get_process_manager()
        result = await proc_mgr.get_process_info(pid, name)
        return result
    except Exception as e:
        logger.error(f"Failed to get process info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/process/start")
async def start_process(request: ProcessStartRequest):
    """Start a process"""
    try:
        proc_mgr = get_process_manager()
        result = await proc_mgr.start_process(
            request.command, request.args, request.cwd, request.wait
        )
        return result
    except Exception as e:
        logger.error(f"Failed to start process: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/process/kill")
async def kill_process(request: ProcessKillRequest):
    """Kill a process"""
    try:
        proc_mgr = get_process_manager()
        result = await proc_mgr.kill_process(request.pid, request.name, request.force)
        return result
    except Exception as e:
        logger.error(f"Failed to kill process: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/process/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        proc_mgr = get_process_manager()
        result = await proc_mgr.get_system_stats()
        return result
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Desktop Automation Endpoints
@router.post("/automation/type")
async def type_text(request: KeyboardTypeRequest):
    """Type text"""
    try:
        automation = get_desktop_automation()
        result = await automation.type_text(request.text, request.interval)
        return result
    except Exception as e:
        logger.error(f"Failed to type text: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/automation/press")
async def press_key(request: KeyPressRequest):
    """Press a key"""
    try:
        automation = get_desktop_automation()
        result = await automation.press_key(request.key, request.presses, request.interval)
        return result
    except Exception as e:
        logger.error(f"Failed to press key: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/automation/hotkey")
async def press_hotkey(request: HotkeyRequest):
    """Press a hotkey combination"""
    try:
        automation = get_desktop_automation()
        result = await automation.hotkey(*request.keys)
        return result
    except Exception as e:
        logger.error(f"Failed to press hotkey: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/automation/click")
async def click_mouse(request: MouseClickRequest):
    """Click mouse"""
    try:
        automation = get_desktop_automation()
        result = await automation.click(
            request.x, request.y, request.clicks, request.interval, request.button
        )
        return result
    except Exception as e:
        logger.error(f"Failed to click mouse: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/automation/move")
async def move_mouse(request: MouseMoveRequest):
    """Move mouse"""
    try:
        automation = get_desktop_automation()
        result = await automation.move_mouse(request.x, request.y, request.duration)
        return result
    except Exception as e:
        logger.error(f"Failed to move mouse: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/automation/mouse_position")
async def get_mouse_position():
    """Get mouse position"""
    try:
        automation = get_desktop_automation()
        result = await automation.get_mouse_position()
        return result
    except Exception as e:
        logger.error(f"Failed to get mouse position: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/automation/screen_size")
async def get_screen_size():
    """Get screen size"""
    try:
        automation = get_desktop_automation()
        result = await automation.get_screen_size()
        return result
    except Exception as e:
        logger.error(f"Failed to get screen size: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# System Information Endpoints
@router.get("/info/system")
async def get_system_information():
    """Get system information"""
    try:
        sys_info = get_system_info()
        result = await sys_info.get_system_info()
        return result
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/info/cpu")
async def get_cpu_information(interval: float = 1.0):
    """Get CPU information"""
    try:
        sys_info = get_system_info()
        result = await sys_info.get_cpu_info(interval)
        return result
    except Exception as e:
        logger.error(f"Failed to get CPU info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/info/memory")
async def get_memory_information():
    """Get memory information"""
    try:
        sys_info = get_system_info()
        result = await sys_info.get_memory_info()
        return result
    except Exception as e:
        logger.error(f"Failed to get memory info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/info/disk")
async def get_disk_information(path: str = "/"):
    """Get disk information"""
    try:
        sys_info = get_system_info()
        result = await sys_info.get_disk_info(path)
        return result
    except Exception as e:
        logger.error(f"Failed to get disk info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/info/network")
async def get_network_information():
    """Get network information"""
    try:
        sys_info = get_system_info()
        result = await sys_info.get_network_info()
        return result
    except Exception as e:
        logger.error(f"Failed to get network info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/info/battery")
async def get_battery_information():
    """Get battery information"""
    try:
        sys_info = get_system_info()
        result = await sys_info.get_battery_info()
        return result
    except Exception as e:
        logger.error(f"Failed to get battery info: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Registry Operations Endpoints (Windows only)
@router.post("/registry/read")
async def read_registry_value(request: RegistryReadRequest):
    """Read a registry value"""
    try:
        reg_ops = get_registry_operations()
        result = await reg_ops.read_value(request.path, request.value_name)
        return result
    except Exception as e:
        logger.error(f"Failed to read registry: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/registry/write")
async def write_registry_value(request: RegistryWriteRequest):
    """Write a registry value"""
    try:
        reg_ops = get_registry_operations()
        result = await reg_ops.write_value(
            request.path, request.value_name, request.value, request.value_type
        )
        return result
    except Exception as e:
        logger.error(f"Failed to write registry: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/registry/subkeys")
async def list_registry_subkeys(path: str):
    """List registry subkeys"""
    try:
        reg_ops = get_registry_operations()
        result = await reg_ops.list_subkeys(path)
        return result
    except Exception as e:
        logger.error(f"Failed to list subkeys: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/registry/values")
async def list_registry_values(path: str):
    """List registry values"""
    try:
        reg_ops = get_registry_operations()
        result = await reg_ops.list_values(path)
        return result
    except Exception as e:
        logger.error(f"Failed to list values: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Security & Approval Endpoints
@router.post("/approve")
async def approve_operation(request: ApprovalRequest):
    """Approve or deny a pending operation"""
    try:
        from app.core.system_executor import get_system_executor

        security_mgr = get_security_manager()
        get_system_executor()

        # Get the pending operation
        if request.operation_id not in security_mgr.pending_operations:
            raise HTTPException(status_code=404, detail="Operation not found")

        operation = security_mgr.pending_operations[request.operation_id]

        # Approve or deny
        security_mgr.approve_operation(request.operation_id, request.approved, request.remember)

        # If approved, execute the operation
        if request.approved:
            logger.info(f"Executing approved operation: {request.operation_id}")

            # Get the tool name and parameters from the operation
            operation.parameters.get("_tool_name")
            tool_params = {k: v for k, v in operation.parameters.items() if k != "_tool_name"}

            # Execute the actual operation based on operation type
            result = None
            if operation.operation_type == "url_open":
                import webbrowser

                url = tool_params.get("url")
                webbrowser.open(url)
                result = {"url": url, "opened": True}
            elif operation.operation_type == "process_start":
                proc_mgr = get_process_manager()
                result = await proc_mgr.start_process(
                    command=tool_params.get("command"), args=tool_params.get("args", []), wait=False
                )
            elif operation.operation_type == "file_write":
                file_ops = get_file_operations()
                result = await file_ops.write_file(
                    path=tool_params.get("path"),
                    content=tool_params.get("content"),
                    create_dirs=tool_params.get("create_dirs", True),
                )
            elif operation.operation_type == "file_delete":
                file_ops = get_file_operations()
                result = await file_ops.delete_file(
                    path=tool_params.get("path"),
                    use_recycle_bin=tool_params.get("use_recycle_bin", True),
                )
            elif operation.operation_type == "process_kill":
                proc_mgr = get_process_manager()
                result = await proc_mgr.kill_process(
                    pid=tool_params.get("pid"),
                    name=tool_params.get("name"),
                    force=tool_params.get("force", False),
                )
            elif operation.operation_type == "keyboard_type":
                automation = get_desktop_automation()
                result = await automation.type_text(
                    text=tool_params.get("text"), interval=tool_params.get("interval", 0.01)
                )

            # Update operation with result
            from app.core.security_manager import OperationStatus

            operation.status = OperationStatus.COMPLETED
            operation.result = result
            security_mgr.log_operation(operation)

            # Remove from pending
            del security_mgr.pending_operations[request.operation_id]

            return {"success": True, "operation_id": request.operation_id, "result": result}
        else:
            # Remove from pending if denied
            del security_mgr.pending_operations[request.operation_id]
            return {"success": True, "operation_id": request.operation_id, "denied": True}

    except Exception as e:
        logger.error(f"Failed to approve operation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/operations/pending")
async def get_pending_operations():
    """Get all pending operations"""
    try:
        security_mgr = get_security_manager()
        operations = security_mgr.get_pending_operations()
        return {"operations": operations}
    except Exception as e:
        logger.error(f"Failed to get pending operations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/operations/history")
async def get_operation_history(limit: int = 100):
    """Get operation history"""
    try:
        security_mgr = get_security_manager()
        history = security_mgr.get_operation_history(limit)
        return {"operations": history, "count": len(history)}
    except Exception as e:
        logger.error(f"Failed to get operation history: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
