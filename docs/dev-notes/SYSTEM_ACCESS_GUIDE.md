# System-Level Access Features - Complete Guide

## 🎯 Overview

AIZEN now has **kernel-level/system-level access** capabilities, allowing it to perform advanced system operations including:

- **File Operations**: Read, write, create, delete, search files and directories
- **Process Management**: List, start, stop, and monitor processes
- **Desktop Automation**: Control keyboard, mouse, and windows
- **System Monitoring**: Track CPU, memory, disk, network, and battery status
- **Registry Operations**: Read and write Windows Registry (with extra security)

## 🔒 Security Architecture

All system operations go through a comprehensive security layer:

### Operation Risk Levels

1. **SAFE** - Auto-execute (e.g., reading files, listing processes, getting system info)
2. **NEEDS_APPROVAL** - User confirmation required (e.g., writing files, typing text)
3. **DANGEROUS** - Explicit approval with warnings (e.g., deleting files, killing processes, modifying registry)

### Safety Features

- ✅ **Operation Classification**: Every operation is classified by risk level
- ✅ **User Approval Workflow**: Dangerous operations require explicit confirmation
- ✅ **Comprehensive Logging**: All operations logged with timestamps and results
- ✅ **Rate Limiting**: Prevents runaway automation scripts
- ✅ **Protected Paths**: System directories (Windows, Program Files) have extra protection
- ✅ **Protected Processes**: Critical system processes cannot be killed
- ✅ **Recycle Bin**: File deletions use recycle bin by default (not permanent delete)

## 📁 File Operations

### Read a File

```python
# Via Python API
from app.system.file_operations import get_file_operations

file_ops = get_file_operations()
result = await file_ops.read_file("C:\\Users\\Documents\\test.txt")
# Returns: {success: True, result: {content, encoding, size}}
```

```bash
# Via REST API
POST /api/system/file/read
{
  "path": "C:\\Users\\Documents\\test.txt",
  "encoding": "utf-8"  # Optional, auto-detected if not provided
}
```

### Write a File

```python
result = await file_ops.write_file(
    path="C:\\Users\\Documents\\new.txt",
    content="Hello, World!",
    create_dirs=True
)
```

```bash
POST /api/system/file/write
{
  "path": "C:\\Users\\Documents\\new.txt",
  "content": "Hello, World!",
  "create_dirs": true
}
```

### Delete a File

```python
result = await file_ops.delete_file(
    path="C:\\Users\\Documents\\old.txt",
    use_recycle_bin=True  # Safer than permanent delete
)
```

### Search Files

```python
result = await file_ops.search_files(
    start_path="C:\\Projects",
    pattern="*.py",  # Find all Python files
    max_results=100
)
# Returns: {results: [{name, path, size, modified}]}
```

## 💻 Process Management

### List Running Processes

```python
from app.system.process_manager import get_process_manager

proc_mgr = get_process_manager()
result = await proc_mgr.list_processes(
    sort_by="cpu",  # or "memory", "name", "pid"
    limit=10
)
```

```bash
GET /api/system/process/list?sort_by=cpu&limit=10
```

### Get Process Info

```python
result = await proc_mgr.get_process_info(pid=1234)
# Or by name
result = await proc_mgr.get_process_info(name="chrome.exe")
```

### Start a Process

```python
result = await proc_mgr.start_process(
    command="notepad.exe",
    args=["C:\\test.txt"],
    wait=False  # Don't wait for completion
)
```

### Kill a Process (Dangerous - Requires Approval)

```python
result = await proc_mgr.kill_process(
    name="notepad.exe",
    force=False  # Use gentle terminate, not force kill
)
```

### Get System Statistics

```python
result = await proc_mgr.get_system_stats()
# Returns: {cpu, memory, swap, disk, network, process_count}
```

## ⌨️🖱️ Desktop Automation

### Type Text

```python
from app.system.desktop_automation import get_desktop_automation

automation = get_desktop_automation()
result = await automation.type_text(
    text="Hello, World!",
    interval=0.01  # Delay between keystrokes
)
```

### Press Keys

```python
# Single key
await automation.press_key(key="enter")

# Hotkey combination
await automation.hotkey("ctrl", "c")  # Copy
await automation.hotkey("ctrl", "v")  # Paste
await automation.hotkey("win", "r")   # Run dialog
```

### Mouse Control

```python
# Click at position
await automation.click(x=100, y=200, button='left')

# Move mouse
await automation.move_mouse(x=500, y=300, duration=0.5)

# Drag
await automation.drag_mouse(x=600, y=400)

# Scroll
await automation.scroll(clicks=5)  # Scroll up
await automation.scroll(clicks=-5)  # Scroll down

# Get current position
pos = await automation.get_mouse_position()
# Returns: {x: 123, y: 456}
```

### Screen Information

```python
# Get screen size
size = await automation.get_screen_size()
# Returns: {width: 1920, height: 1080}

# Locate image on screen
result = await automation.locate_on_screen(
    image_path="button.png",
    confidence=0.9
)
# Returns: {found: True, left, top, width, height, center_x, center_y}
```

## 📊 System Information

### Get System Info

```python
from app.system.system_info import get_system_info

sys_info = get_system_info()

# Complete system information
info = await sys_info.get_system_info()
# Returns: {os, python, hostname}

# CPU info
cpu = await sys_info.get_cpu_info(interval=1.0)
# Returns: {physical_cores, logical_cores, usage_percent, frequency, ...}

# Memory info
memory = await sys_info.get_memory_info()
# Returns: {virtual: {total, available, used, free, percent}, swap: {...}}

# Disk info
disk = await sys_info.get_disk_info(path="C:\\")
# Returns: {main: {total, used, free, percent}, partitions: [...]}

# Network info
network = await sys_info.get_network_info()
# Returns: {io_counters: {bytes_sent, bytes_recv, ...}, interfaces: {...}}

# Battery info (laptops)
battery = await sys_info.get_battery_info()
# Returns: {has_battery, percent, power_plugged, minutes_left}

# Boot time and uptime
boot = await sys_info.get_boot_time()
# Returns: {boot_time, uptime_seconds, uptime_hours, uptime_days}
```

## 🔧 Windows Registry Operations

⚠️ **DANGEROUS** - All registry writes require explicit approval

### Read Registry Value

```python
from app.system.registry_operations import get_registry_operations

reg_ops = get_registry_operations()

result = await reg_ops.read_value(
    path="HKEY_CURRENT_USER\\Software\\Microsoft\\Windows",
    value_name="CurrentVersion"
)
# Returns: {value, type, type_code}
```

### Write Registry Value

```python
result = await reg_ops.write_value(
    path="HKEY_CURRENT_USER\\Software\\MyApp",
    value_name="Setting1",
    value="MyValue",
    value_type="REG_SZ"  # String type
)
```

### List Registry Subkeys

```python
result = await reg_ops.list_subkeys(
    path="HKEY_LOCAL_MACHINE\\Software"
)
# Returns: {subkeys: [...], count}
```

### List Registry Values

```python
result = await reg_ops.list_values(
    path="HKEY_CURRENT_USER\\Software\\MyApp"
)
# Returns: {values: [{name, value, type}], count}
```

## 🔐 Approval Workflow

When a dangerous operation is requested:

1. Operation is created and marked as PENDING
2. Frontend receives approval request via WebSocket
3. User sees approval dialog with operation details
4. User approves or denies
5. Operation executes (if approved) or is cancelled (if denied)

### Approve an Operation

```bash
POST /api/system/approve
{
  "operation_id": "abc-123",
  "approved": true,
  "remember": false  # Remember this choice for this operation type
}
```

### Get Pending Operations

```bash
GET /api/system/operations/pending
```

### Get Operation History

```bash
GET /api/system/operations/history?limit=100
```

## 📝 Operation Logging

All operations are logged to: `backend/data/security_logs/operations_YYYYMMDD.jsonl`

Each log entry contains:
- `id`: Unique operation ID
- `operation_type`: Type of operation
- `description`: Human-readable description
- `risk_level`: SAFE, NEEDS_APPROVAL, or DANGEROUS
- `parameters`: Operation parameters
- `status`: PENDING, APPROVED, DENIED, EXECUTING, COMPLETED, FAILED
- `timestamp`: When operation was created
- `result`: Operation result (if successful)
- `error`: Error message (if failed)

## 🚨 Protected Resources

### Protected Paths (Always DANGEROUS)

- `C:\\Windows\\System32`
- `C:\\Windows\\SysWOW64`
- `C:\\Program Files`
- `C:\\Program Files (x86)`

### Protected Processes (Cannot be killed)

- System, Registry, smss.exe, csrss.exe, wininit.exe
- services.exe, lsass.exe, winlogon.exe, explorer.exe
- dwm.exe, svchost.exe

## 🎮 Example LLM-Powered Workflows

### Example 1: Find and Analyze Python Files

```
User: "Find all Python files in my Projects folder and tell me their total size"

AIZEN:
1. Calls file_operations.search_files("C:\\Projects", "*.py")
2. Calculates total size from results
3. Responds: "I found 42 Python files totaling 1.2 MB"
```

### Example 2: Open Notepad and Type

```
User: "Open Notepad and type Hello World"

AIZEN:
1. Calls process_manager.start_process("notepad.exe")
2. Waits 500ms for notepad to open
3. Calls desktop_automation.type_text("Hello World")
```

### Example 3: System Health Check

```
User: "How's my computer doing?"

AIZEN:
1. Calls process_manager.get_system_stats()
2. Analyzes CPU, memory, disk usage
3. Responds: "Your CPU is at 25%, memory at 60%, and you have 120GB free disk space. Everything looks healthy!"
```

## 🧪 Testing

Test endpoints using the FastAPI interactive docs:

```
http://localhost:8001/docs
```

Or use curl/Postman:

```bash
# Test file read
curl -X POST http://localhost:8001/api/system/file/read \
  -H "Content-Type: application/json" \
  -d '{"path": "C:\\test.txt"}'

# Test process list
curl http://localhost:8001/api/system/process/list?sort_by=cpu&limit=5

# Test system info
curl http://localhost:8001/api/system/info/cpu
```

## 🔄 Rate Limits

To prevent runaway scripts:

- `keyboard_type`: 100 operations per session
- `mouse_click`: 100 operations per session
- `file_delete`: 50 operations per session

Rate limits can be configured in `security_manager.py`.

## 🚀 Next Steps

Integration with AIZEN's AI Brain is next! This will allow:
- Natural language → System operations
- Multi-step workflows planned by LLM
- Intelligent error handling and alternatives
- Context-aware automation

Example:
```
User: "Clean up my Downloads folder by moving PDFs to Documents"

AIZEN:
1. Plans workflow: list Downloads, filter PDFs, create Documents/PDFs folder, move files
2. Executes each step with approval for file moves
3. Reports: "Moved 12 PDF files to Documents\\PDFs"
```

## 📖 API Reference

All endpoints are documented at:
```
http://localhost:8001/docs
```

Key endpoint prefixes:
- `/api/system/file/*` - File operations
- `/api/system/process/*` - Process management
- `/api/system/automation/*` - Desktop automation
- `/api/system/info/*` - System information
- `/api/system/registry/*` - Registry operations
- `/api/system/operations/*` - Operation management
- `/api/system/approve` - Approve operations
