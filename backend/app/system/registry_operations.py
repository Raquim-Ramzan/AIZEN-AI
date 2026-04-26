import logging
from typing import Any

from app.core.system_controller import SystemController

logger = logging.getLogger(__name__)

try:
    import winreg

    HAS_WINREG = True
except ImportError:
    logger.warning("winreg not found. Registry operations disabled.")
    HAS_WINREG = False

    # Define dummy winreg for Linux compatibility during import
    class MockWinreg:
        HKEY_CLASSES_ROOT = 0
        HKEY_CURRENT_USER = 1
        HKEY_LOCAL_MACHINE = 2
        HKEY_USERS = 3
        HKEY_CURRENT_CONFIG = 4
        REG_SZ = 1
        REG_EXPAND_SZ = 2
        REG_BINARY = 3
        REG_DWORD = 4
        REG_QWORD = 5
        REG_MULTI_SZ = 6

    winreg = MockWinreg()


# Registry hive constants
HKEY_MAP = {
    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKCR": winreg.HKEY_CLASSES_ROOT,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_USERS": winreg.HKEY_USERS,
    "HKU": winreg.HKEY_USERS,
    "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
    "HKCC": winreg.HKEY_CURRENT_CONFIG,
}

# Registry value type constants
REG_TYPE_MAP = {
    "REG_SZ": winreg.REG_SZ,
    "REG_EXPAND_SZ": winreg.REG_EXPAND_SZ,
    "REG_BINARY": winreg.REG_BINARY,
    "REG_DWORD": winreg.REG_DWORD,
    "REG_QWORD": winreg.REG_QWORD,
    "REG_MULTI_SZ": winreg.REG_MULTI_SZ,
}


class RegistryOperations(SystemController):
    """Handles Windows Registry operations"""

    def _parse_registry_path(self, path: str) -> tuple:
        """
        Parse registry path into hive and subkey

        Args:
            path: Registry path (e.g., "HKEY_LOCAL_MACHINE\\Software\\Microsoft")

        Returns:
            Tuple of (hive, subkey)
        """
        parts = path.split("\\", 1)
        hive_name = parts[0]
        subkey = parts[1] if len(parts) > 1 else ""

        hive = HKEY_MAP.get(hive_name.upper())
        if hive is None:
            raise ValueError(f"Invalid registry hive: {hive_name}")

        return hive, subkey

    async def read_value(
        self, path: str, value_name: str = "", approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        Read a registry value

        Args:
            path: Registry key path
            value_name: Name of the value (empty string for default value)
            approval_callback: Approval callback

        Returns:
            Dictionary with registry value
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            hive, subkey = self._parse_registry_path(params["path"])

            try:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
                try:
                    value, value_type = winreg.QueryValueEx(key, params["value_name"])

                    # Convert type to string
                    type_name = "unknown"
                    for name, type_val in REG_TYPE_MAP.items():
                        if type_val == value_type:
                            type_name = name
                            break

                    return {
                        "path": params["path"],
                        "value_name": params["value_name"],
                        "value": value,
                        "type": type_name,
                        "type_code": value_type,
                    }
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                raise FileNotFoundError(f"Registry key not found: {params['path']}")
            except Exception as e:
                raise Exception(f"Failed to read registry value: {str(e)}")

        return await self.execute_operation(
            operation_type="registry_read",
            description=f"Read registry: {path}\\{value_name}",
            parameters={"path": path, "value_name": value_name},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def write_value(
        self,
        path: str,
        value_name: str,
        value: Any,
        value_type: str = "REG_SZ",
        approval_callback: callable | None = None,
    ) -> dict[str, Any]:
        """
        Write a registry value

        Args:
            path: Registry key path
            value_name: Name of the value
            value: Value to write
            value_type: Type of value (REG_SZ, REG_DWORD, etc.)
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            hive, subkey = self._parse_registry_path(params["path"])

            reg_type = REG_TYPE_MAP.get(params["value_type"].upper())
            if reg_type is None:
                raise ValueError(f"Invalid registry value type: {params['value_type']}")

            try:
                # Create/open key with write access
                key = winreg.CreateKey(hive, subkey)
                try:
                    winreg.SetValueEx(key, params["value_name"], 0, reg_type, params["value"])
                    return {
                        "path": params["path"],
                        "value_name": params["value_name"],
                        "value": params["value"],
                        "type": params["value_type"],
                        "written": True,
                    }
                finally:
                    winreg.CloseKey(key)
            except Exception as e:
                raise Exception(f"Failed to write registry value: {str(e)}")

        return await self.execute_operation(
            operation_type="registry_write",
            description=f"Write registry: {path}\\{value_name}",
            parameters={
                "path": path,
                "value_name": value_name,
                "value": value,
                "value_type": value_type,
            },
            executor=executor,
            approval_callback=approval_callback,
        )

    async def delete_value(
        self, path: str, value_name: str, approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        Delete a registry value

        Args:
            path: Registry key path
            value_name: Name of the value to delete
            approval_callback: Approval callback

        Returns:
            Dictionary with operation result
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            hive, subkey = self._parse_registry_path(params["path"])

            try:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_SET_VALUE)
                try:
                    winreg.DeleteValue(key, params["value_name"])
                    return {
                        "path": params["path"],
                        "value_name": params["value_name"],
                        "deleted": True,
                    }
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Registry value not found: {params['path']}\\{params['value_name']}"
                )
            except Exception as e:
                raise Exception(f"Failed to delete registry value: {str(e)}")

        return await self.execute_operation(
            operation_type="registry_delete",
            description=f"Delete registry value: {path}\\{value_name}",
            parameters={"path": path, "value_name": value_name},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def list_subkeys(
        self, path: str, approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        List all subkeys in a registry key

        Args:
            path: Registry key path
            approval_callback: Approval callback

        Returns:
            Dictionary with subkey list
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            hive, subkey = self._parse_registry_path(params["path"])

            try:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
                try:
                    subkeys = []
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkeys.append(subkey_name)
                            i += 1
                        except OSError:
                            break

                    return {"path": params["path"], "subkeys": subkeys, "count": len(subkeys)}
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                raise FileNotFoundError(f"Registry key not found: {params['path']}")
            except Exception as e:
                raise Exception(f"Failed to list subkeys: {str(e)}")

        return await self.execute_operation(
            operation_type="registry_read",
            description=f"List registry subkeys: {path}",
            parameters={"path": path},
            executor=executor,
            approval_callback=approval_callback,
        )

    async def list_values(
        self, path: str, approval_callback: callable | None = None
    ) -> dict[str, Any]:
        """
        List all values in a registry key

        Args:
            path: Registry key path
            approval_callback: Approval callback

        Returns:
            Dictionary with value list
        """

        async def executor(params: dict[str, Any]) -> dict[str, Any]:
            hive, subkey = self._parse_registry_path(params["path"])

            try:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
                try:
                    values = []
                    i = 0
                    while True:
                        try:
                            value_name, value_data, value_type = winreg.EnumValue(key, i)

                            # Convert type to string
                            type_name = "unknown"
                            for name, type_val in REG_TYPE_MAP.items():
                                if type_val == value_type:
                                    type_name = name
                                    break

                            values.append(
                                {
                                    "name": value_name,
                                    "value": value_data,
                                    "type": type_name,
                                    "type_code": value_type,
                                }
                            )
                            i += 1
                        except OSError:
                            break

                    return {"path": params["path"], "values": values, "count": len(values)}
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                raise FileNotFoundError(f"Registry key not found: {params['path']}")
            except Exception as e:
                raise Exception(f"Failed to list values: {str(e)}")

        return await self.execute_operation(
            operation_type="registry_read",
            description=f"List registry values: {path}",
            parameters={"path": path},
            executor=executor,
            approval_callback=approval_callback,
        )


# Global instance
_registry_operations = None


def get_registry_operations() -> RegistryOperations:
    """Get the global registry operations instance"""
    global _registry_operations
    if _registry_operations is None:
        _registry_operations = RegistryOperations()
    return _registry_operations
