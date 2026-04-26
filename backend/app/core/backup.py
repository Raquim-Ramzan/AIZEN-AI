"""
Backup Manager for AIZEN
========================
Automated backups for SQLite, ChromaDB, and JSON files.
Supports atomic file writes and data export.
"""

import asyncio
import gzip
import json
import logging
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import aiosqlite

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages automated backups and data integrity.
    """

    def __init__(self, backup_dir: str = None):
        from app.config import get_settings

        settings = get_settings()

        base_dir = Path(settings.sqlite_db).parent.parent
        self.backup_dir = Path(backup_dir) if backup_dir else base_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Paths to backup
        self.sqlite_db = Path(settings.sqlite_db)
        self.chroma_dir = Path(settings.chroma_persist_dir)
        self.core_memory_file = Path(settings.core_memory_file)

        # Settings
        self.max_backups = 10  # Keep last N backups
        self.compress = True

    async def create_full_backup(self) -> dict[str, Any]:
        """
        Create a full backup of all data stores.

        Returns:
            Backup manifest with paths and stats
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        manifest = {
            "timestamp": timestamp,
            "created_at": datetime.now(UTC).isoformat(),
            "backup_path": str(backup_path),
            "components": {},
        }

        # 1. Backup SQLite database
        if self.sqlite_db.exists():
            try:
                sqlite_backup = backup_path / "conversations.db"
                if self.compress:
                    await self._backup_file_compressed(
                        self.sqlite_db, sqlite_backup.with_suffix(".db.gz")
                    )
                    manifest["components"]["sqlite"] = {
                        "path": str(sqlite_backup.with_suffix(".db.gz")),
                        "size": sqlite_backup.with_suffix(".db.gz").stat().st_size
                        if sqlite_backup.with_suffix(".db.gz").exists()
                        else 0,
                    }
                else:
                    shutil.copy2(self.sqlite_db, sqlite_backup)
                    manifest["components"]["sqlite"] = {
                        "path": str(sqlite_backup),
                        "size": sqlite_backup.stat().st_size,
                    }
            except Exception as e:
                manifest["components"]["sqlite"] = {"error": str(e)}
                logger.error(f"SQLite backup failed: {e}")

        # 2. Backup ChromaDB directory
        if self.chroma_dir.exists():
            try:
                chroma_backup = backup_path / "chromadb"
                if self.compress:
                    # Create tar.gz of ChromaDB directory
                    await asyncio.to_thread(
                        shutil.make_archive,
                        str(chroma_backup),
                        "gztar",
                        self.chroma_dir.parent,
                        self.chroma_dir.name,
                    )
                    manifest["components"]["chromadb"] = {
                        "path": str(chroma_backup.with_suffix(".tar.gz"))
                    }
                else:
                    await asyncio.to_thread(shutil.copytree, self.chroma_dir, chroma_backup)
                    manifest["components"]["chromadb"] = {"path": str(chroma_backup)}
            except Exception as e:
                manifest["components"]["chromadb"] = {"error": str(e)}
                logger.error(f"ChromaDB backup failed: {e}")

        # 3. Backup core memory JSON
        if self.core_memory_file.exists():
            try:
                memory_backup = backup_path / "core_memory.json"
                if self.compress:
                    await self._backup_file_compressed(
                        self.core_memory_file, memory_backup.with_suffix(".json.gz")
                    )
                    manifest["components"]["core_memory"] = {
                        "path": str(memory_backup.with_suffix(".json.gz"))
                    }
                else:
                    shutil.copy2(self.core_memory_file, memory_backup)
                    manifest["components"]["core_memory"] = {"path": str(memory_backup)}
            except Exception as e:
                manifest["components"]["core_memory"] = {"error": str(e)}
                logger.error(f"Core memory backup failed: {e}")

        # Save manifest
        manifest_path = backup_path / "manifest.json"
        async with aiofiles.open(manifest_path, "w") as f:
            await f.write(json.dumps(manifest, indent=2))

        # Cleanup old backups
        await self._cleanup_old_backups()

        logger.info(f"Full backup created: {backup_path}")
        return manifest

    async def _backup_file_compressed(self, source: Path, dest: Path):
        """Backup a file with gzip compression"""
        async with aiofiles.open(source, "rb") as f_in:
            content = await f_in.read()

        def compress_and_write(content, dest):
            with gzip.open(dest, "wb") as f_out:
                f_out.write(content)

        await asyncio.to_thread(compress_and_write, content, dest)

    async def _cleanup_old_backups(self):
        """Remove old backups beyond max_backups limit"""
        backups = sorted(
            [d for d in self.backup_dir.iterdir() if d.is_dir() and d.name.startswith("backup_")],
            key=lambda x: x.name,
            reverse=True,
        )

        for old_backup in backups[self.max_backups :]:
            try:
                await asyncio.to_thread(shutil.rmtree, old_backup)
                logger.info(f"Removed old backup: {old_backup}")
            except Exception as e:
                logger.error(f"Failed to remove old backup: {e}")

    async def list_backups(self) -> list[dict[str, Any]]:
        """List available backups"""
        backups = []

        for backup_dir in sorted(self.backup_dir.iterdir(), reverse=True):
            if backup_dir.is_dir() and backup_dir.name.startswith("backup_"):
                manifest_path = backup_dir / "manifest.json"
                if manifest_path.exists():
                    async with aiofiles.open(manifest_path) as f:
                        manifest = json.loads(await f.read())
                        backups.append(manifest)
                else:
                    backups.append(
                        {
                            "timestamp": backup_dir.name.replace("backup_", ""),
                            "backup_path": str(backup_dir),
                            "components": {},
                        }
                    )

        return backups

    async def restore_backup(self, timestamp: str) -> dict[str, Any]:
        """Restore from a backup (dangerous operation!)"""
        backup_path = self.backup_dir / f"backup_{timestamp}"

        if not backup_path.exists():
            return {"error": f"Backup not found: {timestamp}"}

        result = {"timestamp": timestamp, "restored": [], "errors": []}

        # This is a placeholder - actual restore would need careful handling
        logger.warning("Restore operation requested - implement with caution")
        result["message"] = "Restore not implemented for safety. Manual restore recommended."

        return result

    async def export_data(self, format: str = "json") -> Path:
        """
        Export all data to a single file for portability.
        Supports JSON format.
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        export_path = self.backup_dir / f"export_{timestamp}.json"

        export_data = {
            "export_timestamp": datetime.now(UTC).isoformat(),
            "version": "1.0",
            "data": {},
        }

        # Export core memory
        if self.core_memory_file.exists():
            async with aiofiles.open(self.core_memory_file) as f:
                export_data["data"]["core_memory"] = json.loads(await f.read())

        # Export conversations from SQLite
        if self.sqlite_db.exists():
            async with aiosqlite.connect(self.sqlite_db) as db:
                db.row_factory = aiosqlite.Row

                # Export conversations
                cursor = await db.execute("SELECT * FROM conversations")
                conversations = [dict(row) for row in await cursor.fetchall()]
                export_data["data"]["conversations"] = conversations

                # Export messages
                cursor = await db.execute("SELECT * FROM messages")
                messages = [dict(row) for row in await cursor.fetchall()]
                export_data["data"]["messages"] = messages

        # Write export file
        async with aiofiles.open(export_path, "w") as f:
            await f.write(json.dumps(export_data, indent=2, default=str))

        logger.info(f"Data exported to: {export_path}")
        return export_path


class AtomicFileWriter:
    """
    Atomic file writes to prevent corruption.
    Writes to temp file first, then renames atomically.
    """

    @staticmethod
    async def write_json(filepath: Path, data: Any) -> bool:
        """Write JSON file atomically"""
        try:
            # Write to temp file in same directory
            temp_fd, temp_path = tempfile.mkstemp(suffix=".tmp", dir=filepath.parent)
            os.close(temp_fd)
            temp_path = Path(temp_path)

            # Write data to temp file
            async with aiofiles.open(temp_path, "w") as f:
                await f.write(json.dumps(data, indent=2, default=str))

            # Atomic rename
            await asyncio.to_thread(temp_path.replace, filepath)

            return True

        except Exception as e:
            logger.error(f"Atomic write failed: {e}")
            # Cleanup temp file if exists
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
            raise

    @staticmethod
    async def write_text(filepath: Path, content: str) -> bool:
        """Write text file atomically"""
        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix=".tmp", dir=filepath.parent)
            os.close(temp_fd)
            temp_path = Path(temp_path)

            async with aiofiles.open(temp_path, "w") as f:
                await f.write(content)

            await asyncio.to_thread(temp_path.replace, filepath)

            return True

        except Exception as e:
            logger.error(f"Atomic write failed: {e}")
            if "temp_path" in locals() and temp_path.exists():
                temp_path.unlink()
            raise


# Singleton
_backup_manager: BackupManager | None = None


def get_backup_manager() -> BackupManager:
    """Get or create backup manager"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager


# Convenience function for atomic JSON writes
async def atomic_json_write(filepath: Path, data: Any) -> bool:
    """Convenience wrapper for atomic JSON writes"""
    return await AtomicFileWriter.write_json(filepath, data)
