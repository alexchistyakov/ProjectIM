#!/usr/bin/env python3
"""
MCP Server for Command Line Access
Provides tools for executing shell commands and managing the command line environment
"""

import os
import subprocess
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import mcp.server.stdio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the MCP server instance
server = Server("command-line-server")

# Store the current working directory
current_dir = os.getcwd()

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available command line tools"""
    return [
        Tool(
            name="execute_command",
            description="Execute a shell command and return the output",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute"
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Working directory for command execution (optional)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Command timeout in seconds (default: 30)",
                        "default": 30
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="change_directory",
            description="Change the current working directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The directory path to change to"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="list_directory",
            description="List contents of a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (default: current directory)",
                        "default": "."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="read_file",
            description="Read the contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "append": {
                        "type": "boolean",
                        "description": "Whether to append to the file (default: false)",
                        "default": False
                    }
                },
                "required": ["path", "content"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    """Handle tool calls for command line operations"""
    global current_dir
    
    try:
        if name == "execute_command":
            command = arguments["command"]
            working_dir = arguments.get("working_dir", current_dir)
            timeout = arguments.get("timeout", 30)
            
            logger.info(f"Executing command: {command} in {working_dir}")
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                
                output = f"Command: {command}\n"
                output += f"Exit code: {process.returncode}\n"
                if stdout:
                    output += f"STDOUT:\n{stdout.decode('utf-8')}\n"
                if stderr:
                    output += f"STDERR:\n{stderr.decode('utf-8')}\n"
                
                return [TextContent(type="text", text=output)]
                
            except asyncio.TimeoutError:
                process.terminate()
                await process.wait()
                return [TextContent(type="text", text=f"Command timed out after {timeout} seconds")]
        
        elif name == "change_directory":
            path = arguments["path"]
            
            # Resolve the path
            new_path = Path(path).expanduser().resolve()
            
            if not new_path.exists():
                return [TextContent(type="text", text=f"Directory does not exist: {path}")]
            
            if not new_path.is_dir():
                return [TextContent(type="text", text=f"Path is not a directory: {path}")]
            
            current_dir = str(new_path)
            os.chdir(current_dir)
            
            return [TextContent(type="text", text=f"Changed directory to: {current_dir}")]
        
        elif name == "list_directory":
            path = arguments.get("path", current_dir)
            
            target_path = Path(path).expanduser().resolve()
            
            if not target_path.exists():
                return [TextContent(type="text", text=f"Directory does not exist: {path}")]
            
            if not target_path.is_dir():
                return [TextContent(type="text", text=f"Path is not a directory: {path}")]
            
            items = []
            for item in sorted(target_path.iterdir()):
                if item.is_dir():
                    items.append(f"[DIR]  {item.name}")
                else:
                    size = item.stat().st_size
                    items.append(f"[FILE] {item.name} ({size} bytes)")
            
            output = f"Contents of {target_path}:\n" + "\n".join(items)
            return [TextContent(type="text", text=output)]
        
        elif name == "read_file":
            path = arguments["path"]
            
            file_path = Path(path).expanduser().resolve()
            
            if not file_path.exists():
                return [TextContent(type="text", text=f"File does not exist: {path}")]
            
            if not file_path.is_file():
                return [TextContent(type="text", text=f"Path is not a file: {path}")]
            
            try:
                content = file_path.read_text(encoding='utf-8')
                return [TextContent(type="text", text=f"Contents of {path}:\n{content}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error reading file: {str(e)}")]
        
        elif name == "write_file":
            path = arguments["path"]
            content = arguments["content"]
            append = arguments.get("append", False)
            
            file_path = Path(path).expanduser().resolve()
            
            try:
                mode = 'a' if append else 'w'
                with open(file_path, mode, encoding='utf-8') as f:
                    f.write(content)
                
                action = "Appended to" if append else "Wrote to"
                return [TextContent(type="text", text=f"{action} file: {path}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error writing file: {str(e)}")]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Run the MCP server"""
    logger.info("Starting Command Line MCP Server")
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="command-line-server",
                server_version="1.0.0"
            )
        )

if __name__ == "__main__":
    asyncio.run(main()) 