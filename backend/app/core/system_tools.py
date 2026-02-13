"""
System Operation Tools for AI Brain
Defines all system operations as callable tools for the AI assistant
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SystemToolCategory(Enum):
    """Categories of system tools"""
    FILE = "file"
    PROCESS = "process"
    DESKTOP = "desktop"
    SYSTEM_INFO = "system_info"
    WEB = "web"


# Tool definitions in OpenAI function calling format
SYSTEM_TOOLS = [
    # ============ WEB / URL OPERATIONS ============
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Open a URL in the default web browser. Use this when user wants to open a website, search something online, or view web content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to open (e.g., 'https://youtube.com', 'https://google.com/search?q=python')"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why opening this URL"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current information, facts, or news using Perplexity AI. Use this when you need up-to-date information that you don't have in your training data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    
    # ============ PROCESS OPERATIONS ============
    {
        "type": "function",
        "function": {
            "name": "start_process",
            "description": "Launch an application or executable. Use this to open programs like notepad, calculator, or any installed application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Name or path of the executable (e.g., 'notepad.exe', 'calc.exe', 'C:\\Program Files\\Chrome\\chrome.exe')"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional command-line arguments"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why starting this process"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_processes",
            "description": "Get a list of currently running processes. Use this when user asks about running applications, system status, or what's using resources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sort_by": {
                        "type": "string",
                        "enum": ["cpu", "memory", "name", "pid"],
                        "description": "How to sort the process list"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of processes to return (default 10)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "kill_process",
            "description": "Terminate a running process. DANGEROUS - use with caution. Only use when explicitly requested by user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Process name (e.g., 'chrome.exe', 'notepad.exe')"
                    },
                    "pid": {
                        "type": "integer",
                        "description": "Process ID (alternative to name)"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Use force kill (default false for graceful termination)"
                    }
                },
                "required": []
            }
        }
    },
    
    # ============ FILE OPERATIONS ============
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Use when user wants to see file contents or analyze a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path to the file"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default utf-8)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates the file if it doesn't exist. Use when user wants to save or create a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path to the file"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "create_dirs": {
                        "type": "boolean",
                        "description": "Create parent directories if they don't exist"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files matching a pattern. Use when user wants to find files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_path": {
                        "type": "string",
                        "description": "Directory to start searching from"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "File pattern (e.g., '*.py', '*.txt', 'report*')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return"
                    }
                },
                "required": ["start_path", "pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file. DANGEROUS - requires approval. Use only when explicitly requested.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Full path to the file to delete"
                    },
                    "use_recycle_bin": {
                        "type": "boolean",
                        "description": "Move to recycle bin instead of permanent delete (safer)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    
    # ============ SYSTEM INFO ============
    {
        "type": "function",
        "function": {
            "name": "get_system_stats",
            "description": "Get current system statistics (CPU, memory, disk usage). Use when user asks about system performance or resource usage.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cpu_info",
            "description": "Get detailed CPU information and usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "interval": {
                        "type": "number",
                        "description": "Measurement interval in seconds"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_memory_info",
            "description": "Get detailed memory and swap usage information.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_disk_info",
            "description": "Get disk usage information for a specific path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to check disk usage (e.g., 'C:\\')"
                    }
                },
                "required": []
            }
        }
    },
    
    # ============ DESKTOP AUTOMATION ============
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text using keyboard automation. Use when user wants to automate typing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    },
                    "interval": {
                        "type": "number",
                        "description": "Delay between keystrokes in seconds"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a specific key or key combination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key or keys to press (e.g., ['ctrl', 'c'] for copy)"
                    }
                },
                "required": ["keys"]
            }
        }
    },
]


def get_tools_by_category(category: Optional[SystemToolCategory] = None) -> List[Dict[str, Any]]:
    """Get tools filtered by category or all tools"""
    if category is None:
        return SYSTEM_TOOLS
    
    # Filter by category (based on function name prefix)
    category_prefixes = {
        SystemToolCategory.FILE: ["read_file", "write_file", "search_files", "delete_file"],
        SystemToolCategory.PROCESS: ["start_process", "list_processes", "kill_process"],
        SystemToolCategory.DESKTOP: ["type_text", "press_key"],
        SystemCategory.SYSTEM_INFO: ["get_system_stats", "get_cpu_info", "get_memory_info", "get_disk_info"],
        SystemToolCategory.WEB: ["open_url", "search_web"],
    }
    
    prefixes = category_prefixes.get(category, [])
    return [tool for tool in SYSTEM_TOOLS if tool["function"]["name"] in prefixes]


def get_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific tool by its function name"""
    for tool in SYSTEM_TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None
