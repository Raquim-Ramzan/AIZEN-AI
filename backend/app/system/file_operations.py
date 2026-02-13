"""
File Operations Module
Handles file system operations with security checks
"""

import os
import shutil
import glob
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import chardet

from app.core.system_controller import SystemController

logger = logging.getLogger(__name__)


class FileOperations(SystemController):
    """Handles file system operations"""
    
    async def read_file(
        self,
        path: str,
        encoding: Optional[str] = None,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Read contents of a file
        
        Args:
            path: Path to file
            encoding: Optional encoding (auto-detect if None)
            approval_callback: Approval callback
            
        Returns:
            Dictionary with file contents
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            file_path = Path(params["path"])
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not file_path.is_file():
                raise ValueError(f"Path is not a file: {file_path}")
            
            # Detect encoding if not provided
            if params["encoding"] is None:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    detected_encoding = result['encoding'] or 'utf-8'
            else:
                detected_encoding = params["encoding"]
            
            # Read file
            with open(file_path, 'r', encoding=detected_encoding) as f:
                content = f.read()
            
            return {
                "path": str(file_path),
                "content": content,
                "encoding": detected_encoding,
                "size": file_path.stat().st_size
            }
        
        return await self.execute_operation(
            operation_type="file_read",
            description=f"Read file: {path}",
            parameters={"path": path, "encoding": encoding},
            executor=executor,
            approval_callback=approval_callback
        )
    
    async def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_dirs: bool = True,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Write content to a file
        
        Args:
            path: Path to file
            content: Content to write
            encoding: File encoding
            create_dirs: Create parent directories if they don't exist
            approval_callback: Approval callback
            
        Returns:
            Dictionary with operation result
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            file_path = Path(params["path"])
            
            # Create parent directories if needed
            if params["create_dirs"]:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding=params["encoding"]) as f:
                f.write(params["content"])
            
            return {
                "path": str(file_path),
                "size": file_path.stat().st_size
            }
        
        return await self.execute_operation(
            operation_type="file_write",
            description=f"Write file: {path}",
            parameters={
                "path": path,
                "content": content,
                "encoding": encoding,
                "create_dirs": create_dirs
            },
            executor=executor,
            approval_callback=approval_callback
        )
    
    async def create_file(
        self,
        path: str,
        content: str = "",
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Create a new file"""
        return await self.write_file(path, content, approval_callback=approval_callback)
    
    async def delete_file(
        self,
        path: str,
        use_recycle_bin: bool = True,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Delete a file
        
        Args:
            path: Path to file
            use_recycle_bin: Move to recycle bin instead of permanent delete
            approval_callback: Approval callback
            
        Returns:
            Dictionary with operation result
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            file_path = Path(params["path"])
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if params["use_recycle_bin"]:
                # Use PowerShell to move to recycle bin
                ps_script = f'''
                Add-Type -AssemblyName Microsoft.VisualBasic
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                    "{file_path}",
                    'OnlyErrorDialogs',
                    'SendToRecycleBin'
                )
                '''
                result = self.execute_powershell(ps_script)
                if not result["success"]:
                    raise Exception(f"Failed to delete file: {result.get('error')}")
            else:
                # Permanent delete
                file_path.unlink()
            
            return {
                "path": str(file_path),
                "deleted": True,
                "recycled": params["use_recycle_bin"]
            }
        
        return await self.execute_operation(
            operation_type="file_delete",
            description=f"Delete file: {path}",
            parameters={"path": path, "use_recycle_bin": use_recycle_bin},
            executor=executor,
            approval_callback=approval_callback
        )
    
    async def list_directory(
        self,
        path: str,
        recursive: bool = False,
        pattern: str = "*",
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        List contents of a directory
        
        Args:
            path: Directory path
            recursive: List recursively
            pattern: Glob pattern for filtering
            approval_callback: Approval callback
            
        Returns:
            Dictionary with directory listing
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            dir_path = Path(params["path"])
            
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            
            if not dir_path.is_dir():
                raise ValueError(f"Path is not a directory: {dir_path}")
            
            files = []
            dirs = []
            
            if params["recursive"]:
                pattern_path = dir_path / "**" / params["pattern"]
                matches = glob.glob(str(pattern_path), recursive=True)
            else:
                pattern_path = dir_path / params["pattern"]
                matches = glob.glob(str(pattern_path))
            
            for item_path in matches:
                item = Path(item_path)
                info = {
                    "name": item.name,
                    "path": str(item),
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime,
                    "is_file": item.is_file()
                }
                
                if item.is_file():
                    files.append(info)
                else:
                    dirs.append(info)
            
            return {
                "path": str(dir_path),
                "files": files,
                "directories": dirs,
                "total_files": len(files),
                "total_dirs": len(dirs)
            }
        
        return await self.execute_operation(
            operation_type="file_list",
            description=f"List directory: {path}",
            parameters={
                "path": path,
                "recursive": recursive,
                "pattern": pattern
            },
            executor=executor,
            approval_callback=approval_callback
        )
    
    async def search_files(
        self,
        start_path: str,
        pattern: str,
        max_results: int = 100,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Search for files matching a pattern
        
        Args:
            start_path: Starting directory
            pattern: Search pattern (glob)
            max_results: Maximum number of results
            approval_callback: Approval callback
            
        Returns:
            Dictionary with search results
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            search_path = Path(params["start_path"])
            
            if not search_path.exists():
                raise FileNotFoundError(f"Directory not found: {search_path}")
            
            pattern_path = search_path / "**" / params["pattern"]
            matches = glob.glob(str(pattern_path), recursive=True)
            
            results = []
            for match in matches[:params["max_results"]]:
                item = Path(match)
                if item.is_file():
                    results.append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime
                    })
            
            return {
                "query": params["pattern"],
                "search_path": str(search_path),
                "results": results,
                "count": len(results),
                "truncated": len(matches) > params["max_results"]
            }
        
        return await self.execute_operation(
            operation_type="file_search",
            description=f"Search files: {pattern} in {start_path}",
            parameters={
                "start_path": start_path,
                "pattern": pattern,
                "max_results": max_results
            },
            executor=executor,
            approval_callback=approval_callback
        )
    
    async def create_directory(
        self,
        path: str,
        parents: bool = True,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Create a directory
        
        Args:
            path: Directory path
            parents: Create parent directories
            approval_callback: Approval callback
            
        Returns:
            Dictionary with operation result
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            dir_path = Path(params["path"])
            dir_path.mkdir(parents=params["parents"], exist_ok=True)
            
            return {
                "path": str(dir_path),
                "created": True
            }
        
        return await self.execute_operation(
            operation_type="file_create",
            description=f"Create directory: {path}",
            parameters={"path": path, "parents": parents},
            executor=executor,
            approval_callback=approval_callback
        )
    
    async def copy_file(
        self,
        source: str,
        destination: str,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Copy a file or directory
        
        Args:
            source: Source path
            destination: Destination path
            approval_callback: Approval callback
            
        Returns:
            Dictionary with operation result
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            src = Path(params["source"])
            dst = Path(params["destination"])
            
            if not src.exists():
                raise FileNotFoundError(f"Source not found: {src}")
            
            if src.is_file():
                shutil.copy2(src, dst)
            else:
                shutil.copytree(src, dst)
            
            return {
                "source": str(src),
                "destination": str(dst),
                "copied": True
            }
        
        return await self.execute_operation(
            operation_type="file_write",
            description=f"Copy {source} to {destination}",
            parameters={"source": source, "destination": destination},
            executor=executor,
            approval_callback=approval_callback
        )
    
    async def move_file(
        self,
        source: str,
        destination: str,
        approval_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Move a file or directory
        
        Args:
            source: Source path
            destination: Destination path
            approval_callback: Approval callback
            
        Returns:
            Dictionary with operation result
        """
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            src = Path(params["source"])
            dst = Path(params["destination"])
            
            if not src.exists():
                raise FileNotFoundError(f"Source not found: {src}")
            
            shutil.move(str(src), str(dst))
            
            return {
                "source": str(src),
                "destination": str(dst),
                "moved": True
            }
        
        return await self.execute_operation(
            operation_type="file_move",
            description=f"Move {source} to {destination}",
            parameters={"source": source, "destination": destination},
            executor=executor,
            approval_callback=approval_callback
        )


# Global instance
_file_operations = None


def get_file_operations() -> FileOperations:
    """Get the global file operations instance"""
    global _file_operations
    if _file_operations is None:
        _file_operations = FileOperations()
    return _file_operations
