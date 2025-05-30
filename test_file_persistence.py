#!/usr/bin/env python3
"""
Test file persistence with the updated conversation manager
"""

import asyncio
import os
from pathlib import Path
from claude_conversation_manager import ConversationManager

async def test_file_persistence():
    """Test that files persist correctly"""
    print("Testing File Persistence with Updated Code")
    print("=" * 50)
    
    # Create a mock conversation manager
    class MockClaudeInstance:
        def __init__(self, name):
            self.name = name
            self.system_prompt = "Test"
            self.api_key = "test"
            self.mcp_tools_enabled = True
            self.client = None
    
    manager = ConversationManager(
        MockClaudeInstance("Test1"),
        MockClaudeInstance("Test2")
    )
    
    project_dir = Path(__file__).parent.absolute()
    print(f"Project directory: {project_dir}")
    print()
    
    try:
        # Test 1: Write a file with relative path
        print("1. Writing file with relative path 'test_persist.txt':")
        result = await manager.execute_mcp_tool("write_file", {
            "path": "test_persist.txt",
            "content": "This file should persist in the project directory"
        })
        print(result)
        print()
        
        # Test 2: Change directory and write another file
        print("2. Changing directory and writing another file:")
        await manager.execute_mcp_tool("execute_command", {"command": "mkdir -p test_subdir"})
        await manager.execute_mcp_tool("change_directory", {"path": "test_subdir"})
        result = await manager.execute_mcp_tool("write_file", {
            "path": "subdir_file.txt",
            "content": "This should still be in project directory"
        })
        print(result)
        print()
        
        # Test 3: Verify files exist using Python
        print("3. Verifying files with Python os.path.exists():")
        files_to_check = [
            project_dir / "test_persist.txt",
            project_dir / "subdir_file.txt"
        ]
        
        for file_path in files_to_check:
            exists = file_path.exists()
            print(f"   {file_path}: {'EXISTS' if exists else 'NOT FOUND'}")
            if exists:
                print(f"      Content: {file_path.read_text()[:50]}...")
        print()
        
        # Test 4: List files using shell
        print("4. Listing files in project directory:")
        result = await manager.execute_mcp_tool("execute_command", {
            "command": f"ls -la {project_dir} | grep -E '(test_persist|subdir_file)'"
        })
        print(result)
        
        # Cleanup
        print("\n5. Cleaning up test files...")
        for file_path in files_to_check:
            if file_path.exists():
                file_path.unlink()
                print(f"   Removed {file_path}")
        
        # Remove test directory
        test_dir = project_dir / "test_subdir"
        if test_dir.exists():
            test_dir.rmdir()
            print(f"   Removed {test_dir}")
            
    finally:
        # Ensure shell is closed
        manager.shell.close()
        print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_file_persistence()) 