import logging
import os
from pathlib import Path
from typing import Dict, Any, List
from app.tools.base import BaseTool
from app.core.supabase import get_supabase_client

logger = logging.getLogger(__name__)

SAFE_BASE_DIR = "/app/backend/data/user_files"

class FileOpsTool(BaseTool):
    """Safe file operations tool"""
    
    def __init__(self):
        super().__init__()
        self.name = "file_ops"
        self.description = "Read, write, list, and search files in a safe directory"
        self.parameters = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "search"],
                    "description": "File operation to perform"
                },
                "path": {
                    "type": "string",
                    "description": "Relative file path"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for write operation)"
                },
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (for search operation)"
                }
            },
            "required": ["operation"]
        }
        
        # We will use Supabase Storage Bucket 'user_files'
        self.bucket_name = "user_files"
    
    async def execute(self, operation: str, path: str = "", content: str = "", pattern: str = "", user_id: str = "default") -> Dict[str, Any]:
        """Execute file operation via Supabase Storage"""
        # Append user_id prefix to make paths user-specific
        if path:
            path = f"{user_id}/{path.lstrip('/')}"
            
        try:
            if operation == "read":
                return await self._read_file(path)
            elif operation == "write":
                return await self._write_file(path, content)
            elif operation == "list":
                # For list, prefix with user_id
                list_path = f"{user_id}/{path.lstrip('/')}" if path else user_id
                return await self._list_directory(list_path)
            elif operation == "search":
                return {"error": "Search operation not supported on Cloud Storage currently."}
            else:
                return {"error": f"Unknown operation: {operation}"}
        except Exception as e:
            logger.error(f"File operation error: {e}")
            return {"error": str(e)}
            
    async def _read_file(self, path: str) -> Dict[str, Any]:
        """Read file content from Supabase"""
        client = get_supabase_client()
        if not client: return {"error": "Storage client unavailable"}
        
        try:
            response = client.storage.from_(self.bucket_name).download(path)
            # Response is bytes
            content = response.decode("utf-8")
            
            return {
                "operation": "read",
                "path": path,
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            return {"error": f"Read failed: {e}"}
            
    async def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to Supabase Storage"""
        client = get_supabase_client()
        if not client: return {"error": "Storage client unavailable"}
        
        try:
            client.storage.from_(self.bucket_name).upload(
                path,
                content.encode("utf-8"),
                {"upsert": "true"}
            )
            
            return {
                "operation": "write",
                "path": path,
                "size": len(content),
                "success": True
            }
        except Exception as e:
            return {"error": f"Write failed: {e}"}
            
    async def _list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents from Supabase Storage"""
        client = get_supabase_client()
        if not client: return {"error": "Storage client unavailable"}
        
        try:
            response = client.storage.from_(self.bucket_name).list(path)
            
            items = []
            for item in response:
                items.append({
                    "name": item["name"],
                    "type": "directory" if not item.get("id") else "file",
                    "size": item.get("metadata", {}).get("size", 0)
                })
            
            return {
                "operation": "list",
                "path": path,
                "items": items,
                "count": len(items)
            }
        except Exception as e:
            return {"error": f"List failed: {e}"}
