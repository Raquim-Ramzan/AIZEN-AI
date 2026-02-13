"""
Audit Logger for AIZEN
=======================
Persists all operations and events to SQLite for accountability.
Provides structured logging with correlation IDs.
"""

import logging
import json
import uuid
import aiosqlite
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
from contextvars import ContextVar
from enum import Enum
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Context variable for request correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class EventType(str, Enum):
    """Types of auditable events"""
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    TOOL_EXECUTION = "tool_execution"
    TOOL_APPROVAL = "tool_approval"
    FACT_EXTRACTION = "fact_extraction"
    MEMORY_UPDATE = "memory_update"
    RAG_RETRIEVAL = "rag_retrieval"
    ERROR = "error"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"


class AuditLogger:
    """Persistent audit logging to SQLite"""
    
    def __init__(self, db_path: Optional[str] = None):
        base_dir = Path(settings.sqlite_db).parent
        self.db_path = db_path or str(base_dir / "audit_log.db")
        self._initialized = False
    
    async def initialize(self):
        """Initialize audit log database"""
        if self._initialized:
            return
        
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id TEXT PRIMARY KEY,
                    correlation_id TEXT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    details TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for common queries
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_correlation 
                ON audit_log(correlation_id)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
                ON audit_log(timestamp)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_event_type 
                ON audit_log(event_type)
            """)
            
            await db.commit()
        
        self._initialized = True
        logger.info("Audit logger initialized")
    
    async def log(
        self,
        event_type: EventType,
        details: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Log an auditable event.
        
        Returns:
            Event ID
        """
        if not self._initialized:
            await self.initialize()
        
        event_id = str(uuid.uuid4())
        corr_id = correlation_id or correlation_id_var.get() or str(uuid.uuid4())[:8]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO audit_log (id, correlation_id, event_type, timestamp, user_id, details, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                corr_id,
                event_type.value,
                datetime.now(timezone.utc).isoformat(),
                user_id,
                details,
                json.dumps(metadata) if metadata else None
            ))
            await db.commit()
        
        # Also log to standard logger with structured format
        log_entry = {
            "event_id": event_id,
            "correlation_id": corr_id,
            "event_type": event_type.value,
            "details": details[:200],  # Truncate for console
            "user_id": user_id
        }
        logger.info(f"AUDIT: {json.dumps(log_entry)}")
        
        return event_id
    
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit events"""
        if not self._initialized:
            await self.initialize()
        
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type.value)
        
        if correlation_id:
            query += " AND correlation_id = ?"
            params.append(correlation_id)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "correlation_id": row["correlation_id"],
                    "event_type": row["event_type"],
                    "timestamp": row["timestamp"],
                    "user_id": row["user_id"],
                    "details": row["details"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None
                }
                for row in rows
            ]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        if not self._initialized:
            await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Total events
            cursor = await db.execute("SELECT COUNT(*) FROM audit_log")
            total = (await cursor.fetchone())[0]
            
            # Events by type
            cursor = await db.execute("""
                SELECT event_type, COUNT(*) as count 
                FROM audit_log 
                GROUP BY event_type
            """)
            by_type = {row[0]: row[1] for row in await cursor.fetchall()}
            
            # Events in last 24 hours
            cursor = await db.execute("""
                SELECT COUNT(*) FROM audit_log 
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            last_24h = (await cursor.fetchone())[0]
            
            return {
                "total_events": total,
                "events_by_type": by_type,
                "events_last_24h": last_24h
            }


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


async def get_audit_logger() -> AuditLogger:
    """Get or create audit logger singleton"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
        await _audit_logger.initialize()
    return _audit_logger


def set_correlation_id(corr_id: str):
    """Set correlation ID for current context"""
    correlation_id_var.set(corr_id)


def get_correlation_id() -> str:
    """Get current correlation ID"""
    return correlation_id_var.get() or str(uuid.uuid4())[:8]
