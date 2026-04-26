"""
Security Manager for System Operations
Handles operation classification, approval workflows, logging, and safety checks.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OperationRiskLevel(Enum):
    """Risk levels for system operations"""

    SAFE = "safe"  # Auto-execute
    NEEDS_APPROVAL = "needs_approval"  # User confirmation required
    DANGEROUS = "dangerous"  # Explicit approval with warnings


class OperationStatus(Enum):
    """Status of system operations"""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SystemOperation:
    """Represents a system operation"""

    id: str
    operation_type: str  # e.g., "file_delete", "process_kill", "registry_write"
    description: str
    risk_level: OperationRiskLevel
    parameters: dict[str, Any]
    status: OperationStatus = OperationStatus.PENDING
    timestamp: str = ""
    result: Any | None = None
    error: str | None = None
    user_id: str | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        data["status"] = self.status.value
        return data


class SecurityManager:
    """Manages security and safety for all system operations"""

    # System-wide operation classifications
    RISK_CLASSIFICATIONS = {
        # File Operations
        "file_read": OperationRiskLevel.SAFE,
        "file_list": OperationRiskLevel.SAFE,
        "file_search": OperationRiskLevel.SAFE,
        "file_write": OperationRiskLevel.NEEDS_APPROVAL,
        "file_create": OperationRiskLevel.NEEDS_APPROVAL,
        "file_delete": OperationRiskLevel.DANGEROUS,
        "file_move": OperationRiskLevel.NEEDS_APPROVAL,
        # Process Operations
        "process_list": OperationRiskLevel.SAFE,
        "process_info": OperationRiskLevel.SAFE,
        "process_start": OperationRiskLevel.NEEDS_APPROVAL,
        "process_kill": OperationRiskLevel.DANGEROUS,
        # Screen Operations
        "screen_capture": OperationRiskLevel.SAFE,
        "screen_record": OperationRiskLevel.NEEDS_APPROVAL,
        # Desktop Automation
        "keyboard_type": OperationRiskLevel.NEEDS_APPROVAL,
        "mouse_click": OperationRiskLevel.NEEDS_APPROVAL,
        "mouse_move": OperationRiskLevel.SAFE,
        "window_manage": OperationRiskLevel.NEEDS_APPROVAL,
        # System Info
        "system_info": OperationRiskLevel.SAFE,
        "system_monitor": OperationRiskLevel.SAFE,
        # Registry Operations
        "registry_read": OperationRiskLevel.SAFE,
        "registry_write": OperationRiskLevel.DANGEROUS,
        "registry_delete": OperationRiskLevel.DANGEROUS,
    }

    # Protected paths that require extra caution
    PROTECTED_PATHS = [
        "C:\\Windows\\System32",
        "C:\\Windows\\SysWOW64",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
    ]

    # Critical processes that should not be killed
    PROTECTED_PROCESSES = [
        "System",
        "Registry",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "services.exe",
        "lsass.exe",
        "winlogon.exe",
        "explorer.exe",
        "dwm.exe",
        "svchost.exe",
    ]

    def __init__(self, log_dir: str = "./data/security_logs"):
        """Initialize security manager"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Operation tracking
        self.pending_operations: dict[str, SystemOperation] = {}
        self.operation_history: list[SystemOperation] = []

        # User preferences (can be loaded from DB)
        self.user_whitelist: list[str] = []
        self.user_blacklist: list[str] = []
        self.remember_choices: dict[str, bool] = {}  # operation_type -> auto_approve

        # Rate limiting
        self.operation_counts: dict[str, int] = {}
        self.rate_limits = {
            "keyboard_type": 100,  # Max 100 keyboard operations per session
            "mouse_click": 100,
            "file_delete": 50,
        }

        logger.info("SecurityManager initialized")

    def classify_operation(
        self, operation_type: str, parameters: dict[str, Any]
    ) -> OperationRiskLevel:
        """
        Classify an operation's risk level

        Args:
            operation_type: Type of operation
            parameters: Operation parameters

        Returns:
            Risk level for the operation
        """
        # Get base classification
        base_risk = self.RISK_CLASSIFICATIONS.get(operation_type, OperationRiskLevel.NEEDS_APPROVAL)

        # Elevate risk based on parameters
        if operation_type.startswith("file_"):
            path = parameters.get("path", "")
            if any(str(path).startswith(protected) for protected in self.PROTECTED_PATHS):
                # Operations on protected paths are always dangerous
                return OperationRiskLevel.DANGEROUS

            # Check blacklist
            if path in self.user_blacklist:
                return OperationRiskLevel.DANGEROUS

        elif operation_type == "process_kill":
            process_name = parameters.get("process_name", "")
            if process_name in self.PROTECTED_PROCESSES:
                logger.warning(f"Attempt to kill protected process: {process_name}")
                return OperationRiskLevel.DANGEROUS

        return base_risk

    def check_rate_limit(self, operation_type: str) -> bool:
        """
        Check if operation is within rate limits

        Args:
            operation_type: Type of operation

        Returns:
            True if within limits, False if exceeded
        """
        if operation_type not in self.rate_limits:
            return True

        current_count = self.operation_counts.get(operation_type, 0)
        limit = self.rate_limits[operation_type]

        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for {operation_type}: {current_count}/{limit}")
            return False

        return True

    def requires_approval(self, operation: SystemOperation) -> bool:
        """
        Check if operation requires user approval

        Args:
            operation: System operation

        Returns:
            True if approval required
        """
        # Check if user has "remember my choice" for this operation type
        if operation.operation_type in self.remember_choices:
            return not self.remember_choices[operation.operation_type]

        # Safe operations don't need approval
        if operation.risk_level == OperationRiskLevel.SAFE:
            return False

        # Everything else needs approval
        return True

    async def request_approval(
        self, operation: SystemOperation, approval_callback: Callable | None = None
    ) -> bool:
        """
        Request user approval for an operation

        Args:
            operation: System operation
            approval_callback: Optional callback to handle approval UI

        Returns:
            True if approved, False if denied
        """
        logger.info(f"Requesting approval for operation: {operation.id}")

        # Store in pending operations
        self.pending_operations[operation.id] = operation

        # If callback provided, use it (for WebSocket-based approval)
        if approval_callback:
            try:
                approved = await approval_callback(operation)
                return approved
            except Exception as e:
                logger.error(f"Error in approval callback: {e}")
                return False

        # Default: wait for manual approval via API
        # This will be handled by the approve_operation method
        operation.status = OperationStatus.PENDING

        # Wait for approval (with timeout)
        timeout = 60  # 60 seconds
        start_time = asyncio.get_event_loop().time()

        while operation.status == OperationStatus.PENDING:
            await asyncio.sleep(0.5)
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning(f"Approval timeout for operation: {operation.id}")
                operation.status = OperationStatus.DENIED
                return False

        return operation.status == OperationStatus.APPROVED

    def approve_operation(self, operation_id: str, approved: bool, remember: bool = False):
        """
        Approve or deny a pending operation

        Args:
            operation_id: ID of the operation
            approved: Whether to approve (True) or deny (False)
            remember: Whether to remember this choice for this operation type
        """
        if operation_id not in self.pending_operations:
            logger.warning(f"Operation not found: {operation_id}")
            return

        operation = self.pending_operations[operation_id]
        operation.status = OperationStatus.APPROVED if approved else OperationStatus.DENIED

        # Remember choice if requested
        if remember:
            self.remember_choices[operation.operation_type] = approved
            logger.info(f"Remembered choice for {operation.operation_type}: {approved}")

        logger.info(f"Operation {operation_id} {'approved' if approved else 'denied'}")

    def log_operation(self, operation: SystemOperation):
        """
        Log an operation to audit trail

        Args:
            operation: System operation to log
        """
        # Add to history
        self.operation_history.append(operation)

        # Update rate limit counter
        op_type = operation.operation_type
        self.operation_counts[op_type] = self.operation_counts.get(op_type, 0) + 1

        # Write to log file
        log_file = self.log_dir / f"operations_{datetime.now().strftime('%Y%m%d')}.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(operation.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to write operation log: {e}")

    def get_operation_history(self, limit: int = 100) -> list[dict]:
        """
        Get recent operation history

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of operations as dictionaries
        """
        recent = self.operation_history[-limit:]
        return [op.to_dict() for op in recent]

    def get_pending_operations(self) -> list[dict]:
        """Get all pending operations"""
        return [op.to_dict() for op in self.pending_operations.values()]

    def is_path_safe(self, path: str) -> bool:
        """
        Check if a path is safe to operate on

        Args:
            path: File or directory path

        Returns:
            True if safe, False if protected
        """
        path_str = str(Path(path).resolve())

        # Check protected paths
        for protected in self.PROTECTED_PATHS:
            if path_str.startswith(protected):
                return False

        # Check user blacklist
        if path_str in self.user_blacklist:
            return False

        return True


# Global security manager instance
_security_manager = None


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager
