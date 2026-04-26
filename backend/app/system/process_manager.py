import logging
import subprocess
from collections.abc import Callable
from typing import Any

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from app.core.system_controller import SystemController

logger = logging.getLogger(__name__)


class ProcessManager(SystemController):
    """Handles process management operations"""

    async def list_processes(
        self,
        sort_by: str = "cpu",
        limit: int | None = None,
        approval_callback: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """
        List all running processes

        Args:
            sort_by: Sort by 'cpu', 'memory', 'name', or 'pid'
            limit: Limit number of results
            approval_callback: Approval callback

        Returns:
            Dictionary with process list
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            if not HAS_PSUTIL:
                return {"error": "psutil not available in this environment"}

            processes = []

            for proc in psutil.process_iter(
                ["pid", "name", "username", "cpu_percent", "memory_percent"]
            ):
                try:
                    pinfo = proc.info
                    processes.append(
                        {
                            "pid": pinfo["pid"],
                            "name": pinfo["name"],
                            "username": pinfo["username"],
                            "cpu_percent": pinfo["cpu_percent"] or 0,
                            "memory_percent": pinfo["memory_percent"] or 0,
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort processes
            if params["sort_by"] == "cpu":
                processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
            elif params["sort_by"] == "memory":
                processes.sort(key=lambda x: x["memory_percent"], reverse=True)
            elif params["sort_by"] == "name":
                processes.sort(key=lambda x: x["name"])
            elif params["sort_by"] == "pid":
                processes.sort(key=lambda x: x["pid"])

            # Apply limit
            if params["limit"]:
                processes = processes[: params["limit"]]

            return {
                "processes": processes,
                "count": len(processes),
                "total_running": len(list(psutil.process_iter())),
            }

        return await self.execute_operation(
            operation_type="process_list",
            description="List running processes",
            parameters={"sort_by": sort_by, "limit": limit},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_process_info(
        self,
        pid: int | None = None,
        name: str | None = None,
        approval_callback: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """
        Get detailed information about a process

        Args:
            pid: Process ID
            name: Process name (if PID not provided)
            approval_callback: Approval callback

        Returns:
            Dictionary with process information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            if not HAS_PSUTIL:
                return {"error": "psutil not available in this environment"}
            if params["pid"]:
                try:
                    proc = psutil.Process(params["pid"])
                except psutil.NoSuchProcess:
                    raise ValueError(f"Process with PID {params['pid']} not found") from None
            elif params["name"]:
                # Find process by name
                found = False
                for proc in psutil.process_iter(["name"]):
                    if proc.info["name"] == params["name"]:
                        found = True
                        break
                if not found:
                    raise ValueError(f"Process '{params['name']}' not found")
            else:
                raise ValueError("Either pid or name must be provided")

            # Get detailed info
            with proc.oneshot():
                info = {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "username": proc.username(),
                    "create_time": proc.create_time(),
                    "cpu_percent": proc.cpu_percent(interval=0.1),
                    "memory_percent": proc.memory_percent(),
                    "memory_info": {"rss": proc.memory_info().rss, "vms": proc.memory_info().vms},
                    "num_threads": proc.num_threads(),
                    "exe": proc.exe() if proc.exe() else None,
                    "cwd": proc.cwd() if proc.cwd() else None,
                    "cmdline": proc.cmdline(),
                }

            return info

        return await self.execute_operation(
            operation_type="process_info",
            description=f"Get process info: {pid or name}",
            parameters={"pid": pid, "name": name},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def start_process(
        self,
        command: str,
        args: list[str] | None = None,
        cwd: str | None = None,
        wait: bool = False,
        approval_callback: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """
        Start a new process

        Args:
            command: Command to execute
            args: Command arguments
            cwd: Working directory
            wait: Wait for process to complete
            approval_callback: Approval callback

        Returns:
            Dictionary with process information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            cmd = [params["command"]]
            if params["args"]:
                cmd.extend(params["args"])

            if params["wait"]:
                # Wait for completion
                result = subprocess.run(cmd, cwd=params["cwd"], capture_output=True, text=True)
                return {
                    "command": params["command"],
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            else:
                # Start and detach
                proc = subprocess.Popen(
                    cmd, cwd=params["cwd"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                return {"command": params["command"], "pid": proc.pid, "started": True}

        return await self.execute_operation(
            operation_type="process_start",
            description=f"Start process: {command}",
            parameters={"command": command, "args": args, "cwd": cwd, "wait": wait},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def kill_process(
        self,
        pid: int | None = None,
        name: str | None = None,
        force: bool = False,
        approval_callback: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """
        Terminate a process

        Args:
            pid: Process ID
            name: Process name (if PID not provided)
            force: Use force kill (SIGKILL)
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            if not HAS_PSUTIL:
                return {"error": "psutil not available in this environment"}
            terminated = []

            if params["pid"]:
                try:
                    proc = psutil.Process(params["pid"])
                    proc_name = proc.name()

                    if params["force"]:
                        proc.kill()
                    else:
                        proc.terminate()

                    terminated.append({"pid": params["pid"], "name": proc_name})
                except psutil.NoSuchProcess:
                    raise ValueError(f"Process with PID {params['pid']} not found") from None

            elif params["name"]:
                # Find and kill all processes with this name
                found = False
                for proc in psutil.process_iter(["name"]):
                    if proc.info["name"] == params["name"]:
                        found = True
                        try:
                            if params["force"]:
                                proc.kill()
                            else:
                                proc.terminate()

                            terminated.append({"pid": proc.pid, "name": proc.info["name"]})
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                if not found:
                    raise ValueError(f"Process '{params['name']}' not found")
            else:
                raise ValueError("Either pid or name must be provided")

            return {"terminated": terminated, "count": len(terminated), "force": params["force"]}

        return await self.execute_operation(
            operation_type="process_kill",
            description=f"Kill process: {pid or name}",
            parameters={"pid": pid, "name": name, "force": force},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_system_stats(
        self, approval_callback: Callable[..., Any] | None = None
    ) -> dict[str, Any]:
        """
        Get overall system statistics

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with system stats
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            if not HAS_PSUTIL:
                return {"error": "psutil not available in this environment"}
            # CPU stats
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()

            # Memory stats
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk stats
            disk = psutil.disk_usage("/")

            # Network stats
            net_io = psutil.net_io_counters()

            return {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "per_cpu": cpu_percent,
                    "count": psutil.cpu_count(),
                    "frequency": {
                        "current": cpu_freq.current if cpu_freq else None,
                        "min": cpu_freq.min if cpu_freq else None,
                        "max": cpu_freq.max if cpu_freq else None,
                    },
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                },
                "process_count": len(list(psutil.process_iter())),
            }

        return await self.execute_operation(
            operation_type="system_info",
            description="Get system statistics",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )


# Global instance
_process_manager = None


def get_process_manager() -> ProcessManager:
    """Get the global process manager instance"""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager
