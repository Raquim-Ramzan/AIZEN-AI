"""
System Controller - Base class for all system-level operations
Coordinates between different system modules and enforces security
"""

import logging
import subprocess
import uuid
from collections.abc import Callable
from typing import Any

from app.core.security_manager import (
    OperationStatus,
    SecurityManager,
    SystemOperation,
    get_security_manager,
)

logger = logging.getLogger(__name__)


class SystemController:
    """
    Base controller for system-level operations
    All system modules inherit from this class
    """

    def __init__(self, security_manager: SecurityManager | None = None):
        """Initialize system controller"""
        self.security_manager = security_manager or get_security_manager()
        logger.info(f"{self.__class__.__name__} initialized")

    async def execute_operation(
        self,
        operation_type: str,
        description: str,
        parameters: dict[str, Any],
        executor: Callable,
        approval_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """
        Execute a system operation with security checks

        Args:
            operation_type: Type of operation (e.g., "file_delete")
            description: Human-readable description
            parameters: Operation parameters
            executor: Async function that performs the actual operation
            approval_callback: Optional callback for approval UI

        Returns:
            Dictionary with success status and result/error
        """
        # Generate operation ID
        operation_id = str(uuid.uuid4())

        # Classify operation risk
        risk_level = self.security_manager.classify_operation(operation_type, parameters)

        # Create operation record
        operation = SystemOperation(
            id=operation_id,
            operation_type=operation_type,
            description=description,
            risk_level=risk_level,
            parameters=parameters,
        )

        try:
            # Check rate limits
            if not self.security_manager.check_rate_limit(operation_type):
                operation.status = OperationStatus.FAILED
                operation.error = "Rate limit exceeded"
                self.security_manager.log_operation(operation)
                return {
                    "success": False,
                    "error": "Rate limit exceeded for this operation",
                    "operation_id": operation_id,
                }

            # Check if approval is required
            if self.security_manager.requires_approval(operation):
                logger.info(f"Operation requires approval: {operation_id}")
                approved = await self.security_manager.request_approval(
                    operation, approval_callback
                )

                if not approved:
                    operation.status = OperationStatus.DENIED
                    self.security_manager.log_operation(operation)
                    return {
                        "success": False,
                        "error": "Operation denied by user",
                        "operation_id": operation_id,
                    }

            # Execute the operation
            operation.status = OperationStatus.EXECUTING
            logger.info(f"Executing operation: {operation_id} - {description}")

            result = await executor(parameters)

            # Mark as completed
            operation.status = OperationStatus.COMPLETED
            operation.result = result

            # Log operation
            self.security_manager.log_operation(operation)

            return {"success": True, "result": result, "operation_id": operation_id}

        except Exception as e:
            logger.error(f"Operation failed: {operation_id} - {str(e)}", exc_info=True)
            operation.status = OperationStatus.FAILED
            operation.error = str(e)
            self.security_manager.log_operation(operation)

            return {"success": False, "error": str(e), "operation_id": operation_id}

    def execute_powershell(
        self, script: str, timeout: int = 30, capture_output: bool = True
    ) -> dict[str, Any]:
        """
        Execute a PowerShell script safely

        Args:
            script: PowerShell script to execute
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr

        Returns:
            Dictionary with returncode, stdout, stderr
        """
        try:
            logger.debug(f"Executing PowerShell script: {script[:100]}...")

            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=capture_output,
                text=True,
                timeout=timeout,
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else None,
                "stderr": result.stderr if capture_output else None,
            }

        except subprocess.TimeoutExpired:
            logger.error(f"PowerShell script timed out after {timeout}s")
            return {"success": False, "error": f"Script timed out after {timeout} seconds"}
        except Exception as e:
            logger.error(f"PowerShell execution failed: {e}")
            return {"success": False, "error": str(e)}

    def execute_cmd(self, command: str, timeout: int = 30, shell: bool = True) -> dict[str, Any]:
        """
        Execute a command prompt command

        Args:
            command: Command to execute
            timeout: Timeout in seconds
            shell: Whether to use shell

        Returns:
            Dictionary with returncode, stdout, stderr
        """
        try:
            logger.debug(f"Executing command: {command}")

            result = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, shell=shell
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s")
            return {"success": False, "error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"success": False, "error": str(e)}
