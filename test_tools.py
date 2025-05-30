#!/usr/bin/env python3
"""Test the new file tools implementation"""

import asyncio
from claude_conversation_manager import ConversationManager

async def test_tools():
    # Mock tool execution
    manager = ConversationManager(None, None)
    
    # Test read_file
    print("Testing read_file tool...")
    result = await manager.execute_mcp_tool("read_file", {
        "path": "claude_conversation_manager.py",
        "start_line": 1,
        "max_lines": 10
    })
    print(result)
    print("\n" + "="*50 + "\n")
    
    # Test write_file
    print("Testing write_file tool...")
    result = await manager.execute_mcp_tool("write_file", {
        "path": "test_output.txt",
        "content": "This is a test file\nWith multiple lines\nCreated by the write_file tool",
        "mode": "write"
    })
    print(result)

if __name__ == "__main__":
    asyncio.run(test_tools()) 