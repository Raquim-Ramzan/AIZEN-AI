import logging
import platform
from typing import Any

import psutil

from app.core.system_controller import SystemController

logger = logging.getLogger(__name__)


class SystemInfo(SystemController):
    """Handles system information gathering"""

    async def get_system_info(self, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Get comprehensive system information

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with system information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            info = {
                "os": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "architecture": platform.architecture()[0],
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                },
                "hostname": platform.node(),
            }

            return info

        return await self.execute_operation(
            operation_type="system_info",
            description="Get system information",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_cpu_info(
        self, interval: float = 1.0, approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        Get CPU information and usage

        Args:
            interval: Measurement interval for CPU percent
            approval_callback: Approval callback

        Returns:
            Dictionary with CPU information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            cpu_freq = psutil.cpu_freq()
            cpu_times = psutil.cpu_times()

            info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "usage_percent": psutil.cpu_percent(interval=params["interval"]),
                "usage_per_cpu": psutil.cpu_percent(interval=params["interval"], percpu=True),
                "frequency": {
                    "current": cpu_freq.current if cpu_freq else None,
                    "min": cpu_freq.min if cpu_freq else None,
                    "max": cpu_freq.max if cpu_freq else None,
                },
                "times": {
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "idle": cpu_times.idle,
                },
            }

            return info

        return await self.execute_operation(
            operation_type="system_info",
            description="Get CPU information",
            parameters={"interval": interval},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_memory_info(self, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Get memory information and usage

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with memory information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            info = {
                "virtual": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "free": memory.free,
                    "percent": memory.percent,
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent,
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                },
            }

            return info

        return await self.execute_operation(
            operation_type="system_info",
            description="Get memory information",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_disk_info(
        self, path: str = "/", approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        Get disk information and usage

        Args:
            path: Disk path to check
            approval_callback: Approval callback

        Returns:
            Dictionary with disk information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            disk = psutil.disk_usage(params["path"])

            # Get all disk partitions
            partitions = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append(
                        {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": usage.percent,
                            "total_gb": round(usage.total / (1024**3), 2),
                            "used_gb": round(usage.used / (1024**3), 2),
                            "free_gb": round(usage.free / (1024**3), 2),
                        }
                    )
                except PermissionError:
                    continue

            info = {
                "main": {
                    "path": params["path"],
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                },
                "partitions": partitions,
            }

            return info

        return await self.execute_operation(
            operation_type="system_info",
            description="Get disk information",
            parameters={"path": path},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_network_info(self, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Get network information and statistics

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with network information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            net_io = psutil.net_io_counters()
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            # Network interfaces
            interfaces = {}
            for interface_name, addresses in net_if_addrs.items():
                stats = net_if_stats.get(interface_name)
                interfaces[interface_name] = {
                    "addresses": [
                        {
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast,
                        }
                        for addr in addresses
                    ],
                    "is_up": stats.isup if stats else None,
                    "speed": stats.speed if stats else None,
                }

            info = {
                "io_counters": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
                },
                "interfaces": interfaces,
            }

            return info

        return await self.execute_operation(
            operation_type="system_info",
            description="Get network information",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_battery_info(self, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Get battery information (for laptops)

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with battery information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            battery = psutil.sensors_battery()

            if battery is None:
                return {"has_battery": False}

            info = {
                "has_battery": True,
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "seconds_left": battery.secsleft
                if battery.secsleft != psutil.POWER_TIME_UNLIMITED
                else None,
                "minutes_left": battery.secsleft // 60
                if battery.secsleft != psutil.POWER_TIME_UNLIMITED
                else None,
            }

            return info

        return await self.execute_operation(
            operation_type="system_info",
            description="Get battery information",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def get_boot_time(self, approval_callback: callable | None = None) -> dict[str, Any]:
        """
        Get system boot time

        Args:
            approval_callback: Approval callback

        Returns:
            Dictionary with boot time information
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            from datetime import datetime

            boot_timestamp = psutil.boot_time()
            boot_time = datetime.fromtimestamp(boot_timestamp)
            uptime_seconds = (datetime.now() - boot_time).total_seconds()

            info = {
                "boot_timestamp": boot_timestamp,
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": uptime_seconds,
                "uptime_hours": round(uptime_seconds / 3600, 2),
                "uptime_days": round(uptime_seconds / 86400, 2),
            }

            return info

        return await self.execute_operation(
            operation_type="system_info",
            description="Get system boot time",
            parameters={},
            executor=executor,
            approval_callback=approval_callback,
        )


# Global instance
_system_info = None


def get_system_info() -> SystemInfo:
    """Get the global system info instance"""
    global _system_info
    if _system_info is None:
        _system_info = SystemInfo()
    return _system_info
