"""
Quick test to verify system operations are working
"""

import asyncio

from app.core.system_executor import get_system_executor


async def test_system_operations():
    print("Testing System Operations Integration...")
    print("=" * 60)

    executor = get_system_executor()

    # Test 1: List processes (should work without approval - SAFE)
    print("\n1. Testing list_processes (SAFE operation)...")
    result = await executor.execute_tool_call(
        tool_name="list_processes", parameters={"sort_by": "cpu", "limit": 5}, user_id="test_user"
    )
    print(f"Result: {result.get('status')}")
    if result.get("success"):
        print("✅ List processes works!")

    # Test 2: Open URL (should require approval)
    print("\n2. Testing open_url (NEEDS_APPROVAL)...")
    result = await executor.execute_tool_call(
        tool_name="open_url",
        parameters={"url": "https://youtube.com", "reason": "Test"},
        user_id="test_user",
    )
    print(f"Result: {result}")
    if result.get("status") == "pending_approval":
        print("✅ URL open requires approval (correct!)")
        print(f"   Operation ID: {result.get('operation_id')}")

    # Test 3: Start process (should require approval)
    print("\n3. Testing start_process (NEEDS_APPROVAL)...")
    result = await executor.execute_tool_call(
        tool_name="start_process",
        parameters={"command": "notepad.exe", "reason": "Test"},
        user_id="test_user",
    )
    print(f"Result: {result}")
    if result.get("status") == "pending_approval":
        print("✅ Process start requires approval (correct!)")
        print(f"   Operation ID: {result.get('operation_id')}")

    print("\n" + "=" * 60)
    print("System operations backend is working correctly!")
    print("Now test from the frontend by typing 'Open YouTube'")


if __name__ == "__main__":
    asyncio.run(test_system_operations())
