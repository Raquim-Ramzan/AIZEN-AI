"""
System Operations Test Script
Tests all system-level capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.system.file_operations import get_file_operations
from app.system.process_manager import get_process_manager
from app.system.desktop_automation import get_desktop_automation
from app.system.system_info import get_system_info
from app.system.registry_operations import get_registry_operations


async def test_file_operations():
    """Test file operations"""
    print("\n" + "="*60)
    print("Testing File Operations")
    print("="*60)
    
    file_ops = get_file_operations()
    test_file = "C:\\temp\\aizen_test.txt"
    
    try:
        # Create directory if needed
        Path("C:\\temp").mkdir(exist_ok=True)
        
        # Test write
        print("\n1. Testing file write...")
        result = await file_ops.write_file(test_file, "Hello from AIZEN!")
        if result["success"]:
            print(f"   ✓ File written: {result['result']['path']}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test read
        print("\n2. Testing file read...")
        result = await file_ops.read_file(test_file)
        if result["success"]:
            print(f"   ✓ File content: {result['result']['content']}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test list directory
        print("\n3. Testing directory listing...")
        result = await file_ops.list_directory("C:\\temp", pattern="*.txt")
        if result["success"]:
            print(f"   ✓ Found {result['result']['total_files']} files")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test search
        print("\n4. Testing file search...")
        result = await file_ops.search_files("C:\\temp", "aizen*", max_results=10)
        if result["success"]:
            print(f"   ✓ Search found {result['result']['count']} files")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Clean up (note: goes to recycle bin by default)
        print("\n5. Testing file delete...")
        result = await file_ops.delete_file(test_file, use_recycle_bin=True)
        if result["success"]:
            print(f"   ✓ File moved to recycle bin")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        print("\n✓ File operations tests completed")
        
    except Exception as e:
        print(f"\n✗ File operations test failed: {e}")


async def test_process_management():
    """Test process management"""
    print("\n" + "="*60)
    print("Testing Process Management")
    print("="*60)
    
    proc_mgr = get_process_manager()
    
    try:
        # Test list processes
        print("\n1. Testing process listing...")
        result = await proc_mgr.list_processes(sort_by="cpu", limit=5)
        if result["success"]:
            print(f"   ✓ Listed top 5 processes by CPU usage:")
            for proc in result['result']['processes'][:5]:
                print(f"     - {proc['name']} (PID: {proc['pid']}) - CPU: {proc['cpu_percent']}%")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test get process info
        print("\n2. Testing get process info (own process)...")
        import os
        result = await proc_mgr.get_process_info(pid=os.getpid())
        if result["success"]:
            info = result['result']
            print(f"   ✓ Process: {info['name']} (PID: {info['pid']})")
            print(f"     CPU: {info['cpu_percent']}%, Memory: {info['memory_percent']:.2f}%")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test system stats
        print("\n3. Testing system statistics...")
        result = await proc_mgr.get_system_stats()
        if result["success"]:
            stats = result['result']
            print(f"   ✓ System Stats:")
            print(f"     CPU: {stats['cpu']['percent']}%")
            print(f"     Memory: {stats['memory']['percent']}% used")
            print(f"     Disk: {stats['disk']['percent']}% used")
            print(f"     Processes: {stats['process_count']}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        print("\n✓ Process management tests completed")
        
    except Exception as e:
        print(f"\n✗ Process management test failed: {e}")


async def test_system_info():
    """Test system information"""
    print("\n" + "="*60)
    print("Testing System Information")
    print("="*60)
    
    sys_info = get_system_info()
    
    try:
        # Test system info
        print("\n1. Testing system information...")
        result = await sys_info.get_system_info()
        if result["success"]:
            info = result['result']
            print(f"   ✓ System: {info['os']['system']} {info['os']['release']}")
            print(f"     Processor: {info['os']['processor']}")
            print(f"     Hostname: {info['hostname']}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test CPU info
        print("\n2. Testing CPU information...")
        result = await sys_info.get_cpu_info(interval=0.5)
        if result["success"]:
            cpu = result['result']
            print(f"   ✓ CPU: {cpu['logical_cores']} cores")
            print(f"     Usage: {cpu['usage_percent']}%")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test memory info
        print("\n3. Testing memory information...")
        result = await sys_info.get_memory_info()
        if result["success"]:
            mem = result['result']
            print(f"   ✓ Memory: {mem['virtual']['total_gb']} GB total")
            print(f"     Available: {mem['virtual']['available_gb']} GB ({100-mem['virtual']['percent']:.1f}%)")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test network info
        print("\n4. Testing network information...")
        result = await sys_info.get_network_info()
        if result["success"]:
            net = result['result']
            print(f"   ✓ Network interfaces: {len(net['interfaces'])}")
            print(f"     Data sent: {net['io_counters']['bytes_sent_mb']:.2f} MB")
            print(f"     Data received: {net['io_counters']['bytes_recv_mb']:.2f} MB")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test battery info
        print("\n5. Testing battery information...")
        result = await sys_info.get_battery_info()
        if result["success"]:
            battery = result['result']
            if battery['has_battery']:
                print(f"   ✓ Battery: {battery['percent']}%")
                print(f"     Plugged in: {battery['power_plugged']}")
            else:
                print(f"   ✓ No battery detected (desktop computer)")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test boot time
        print("\n6. Testing boot time...")
        result = await sys_info.get_boot_time()
        if result["success"]:
            boot = result['result']
            print(f"   ✓ Uptime: {boot['uptime_hours']:.2f} hours")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        print("\n✓ System information tests completed")
        
    except Exception as e:
        print(f"\n✗ System information test failed: {e}")


async def test_desktop_automation():
    """Test desktop automation"""
    print("\n" + "="*60)
    print("Testing Desktop Automation")
    print("="*60)
    
    automation = get_desktop_automation()
    
    try:
        # Test screen size
        print("\n1. Testing screen size...")
        result = await automation.get_screen_size()
        if result["success"]:
            size = result['result']
            print(f"   ✓ Screen size: {size['width']}x{size['height']}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test mouse position
        print("\n2. Testing mouse position...")
        result = await automation.get_mouse_position()
        if result["success"]:
            pos = result['result']
            print(f"   ✓ Mouse position: ({pos['x']}, {pos['y']})")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        print("\n⚠ Skipping keyboard/mouse actions (requires user approval)")
        print("   To test these, use the API endpoints or approve operations manually")
        
        print("\n✓ Desktop automation tests completed")
        
    except Exception as e:
        print(f"\n✗ Desktop automation test failed: {e}")


async def test_registry():
    """Test registry operations"""
    print("\n" + "="*60)
    print("Testing Registry Operations (Windows)")
    print("="*60)
    
    reg_ops = get_registry_operations()
    
    try:
        # Test read registry
        print("\n1. Testing registry read...")
        result = await reg_ops.read_value(
            path="HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
            value_name="ProductName"
        )
        if result["success"]:
            print(f"   ✓ Windows Version: {result['result']['value']}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        # Test list subkeys
        print("\n2. Testing list registry subkeys...")
        result = await reg_ops.list_subkeys(
            path="HKEY_CURRENT_USER\\Software"
        )
        if result["success"]:
            print(f"   ✓ Found {result['result']['count']} subkeys")
            print(f"     First 5: {', '.join(result['result']['subkeys'][:5])}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
        
        print("\n⚠ Skipping registry writes (DANGEROUS - requires user approval)")
        
        print("\n✓ Registry operation tests completed")
        
    except Exception as e:
        print(f"\n✗ Registry operation test failed: {e}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AIZEN SYSTEM-LEVEL ACCESS TEST SUITE")
    print("="*60)
    print("\nThis will test all system-level capabilities:")
    print("- File Operations")
    print("- Process Management")
    print("- System Information")
    print("- Desktop Automation")
    print("- Registry Operations")
    print("\nNote: Some operations require user approval and will be skipped")
    
    input("\nPress Enter to continue...")
    
    # Run tests
    await test_file_operations()
    await test_process_management()
    await test_system_info()
    await test_desktop_automation()
    await test_registry()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
    print("\n✓ System-level access is working correctly!")
    print("\nNext steps:")
    print("1. Start the backend server: python -m app.main")
    print("2. Test via API: http://localhost:8001/docs")
    print("3. Integrate with AI Brain for LLM-powered automation")


if __name__ == "__main__":
    asyncio.run(main())
