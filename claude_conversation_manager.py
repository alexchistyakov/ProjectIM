#!/usr/bin/env python3
"""
Claude-to-Claude Conversation Manager
Manages conversations between two Claude instances with MCP integration
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import anthropic
from anthropic import AsyncAnthropic
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

@dataclass
class Message:
    """Represents a message in the conversation"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    claude_instance: Optional[str] = None

@dataclass
class ClaudeInstance:
    """Represents a Claude instance with its configuration"""
    name: str
    system_prompt: str
    api_key: str
    model: str = "claude-3-opus-20240229"
    mcp_tools_enabled: bool = True
    
    def __post_init__(self):
        self.client = AsyncAnthropic(api_key=self.api_key)

class ConversationManager:
    """Manages the conversation between two Claude instances"""
    
    def __init__(self, claude1: ClaudeInstance, claude2: ClaudeInstance):
        self.claude1 = claude1
        self.claude2 = claude2
        self.conversation_history: List[Message] = []
        self.is_paused = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()  # Start unpaused
        self.mcp_tools = self._get_mcp_tools()
        
    def _get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Get MCP tools definition for Claude"""
        return [
            {
                "name": "execute_command",
                "description": "Execute a shell command and return the output",
                "input_schema": {
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
                            "description": "Command timeout in seconds (default: 30)"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "list_directory",
                "description": "List contents of a directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list (default: current directory)"
                        }
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Read the contents of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "input_schema": {
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
                            "description": "Whether to append to the file (default: false)"
                        }
                    },
                    "required": ["path", "content"]
                }
            }
        ]
    
    async def execute_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool by calling the MCP server"""
        # This is a simplified version - in production, you'd connect to the MCP server
        # For now, we'll execute commands directly
        import subprocess
        
        if tool_name == "execute_command":
            command = arguments["command"]
            working_dir = arguments.get("working_dir", ".")
            timeout = arguments.get("timeout", 30)
            
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=working_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return f"Exit code: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            except subprocess.TimeoutExpired:
                return f"Command timed out after {timeout} seconds"
            except Exception as e:
                return f"Error executing command: {str(e)}"
        
        elif tool_name == "list_directory":
            path = arguments.get("path", ".")
            try:
                items = []
                for item in sorted(Path(path).iterdir()):
                    if item.is_dir():
                        items.append(f"[DIR]  {item.name}")
                    else:
                        items.append(f"[FILE] {item.name}")
                return "\n".join(items)
            except Exception as e:
                return f"Error listing directory: {str(e)}"
        
        elif tool_name == "read_file":
            path = arguments["path"]
            try:
                with open(path, 'r') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        elif tool_name == "write_file":
            path = arguments["path"]
            content = arguments["content"]
            append = arguments.get("append", False)
            try:
                mode = 'a' if append else 'w'
                with open(path, mode) as f:
                    f.write(content)
                return f"Successfully wrote to {path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"
        
        return f"Unknown tool: {tool_name}"
    
    def pause(self):
        """Pause the conversation"""
        self.is_paused = True
        self.pause_event.clear()
        console.print("[yellow]Conversation paused[/yellow]")
    
    def resume(self):
        """Resume the conversation"""
        self.is_paused = False
        self.pause_event.set()
        console.print("[green]Conversation resumed[/green]")
    
    def add_user_message(self, content: str):
        """Add a user message to the conversation"""
        message = Message(role="user", content=content, claude_instance="Human")
        self.conversation_history.append(message)
        self._display_message(message)
    
    def _display_message(self, message: Message):
        """Display a message in the console"""
        color = "blue" if message.claude_instance == self.claude1.name else "green"
        if message.claude_instance == "Human":
            color = "yellow"
        
        panel = Panel(
            Markdown(message.content),
            title=f"[{color}]{message.claude_instance}[/{color}]",
            title_align="left",
            border_style=color
        )
        console.print(panel)
    
    def _format_conversation_for_claude(self, for_claude: ClaudeInstance) -> List[Dict[str, str]]:
        """Format conversation history for Claude API"""
        messages = []
        for msg in self.conversation_history:
            if msg.role == "user" or msg.claude_instance == "Human":
                messages.append({"role": "user", "content": msg.content})
            elif msg.claude_instance != for_claude.name:
                # Other Claude's messages appear as user messages
                messages.append({"role": "user", "content": msg.content})
            else:
                # This Claude's own messages
                messages.append({"role": "assistant", "content": msg.content})
        
        return messages
    
    async def get_claude_response(self, claude: ClaudeInstance, is_first_message: bool = False) -> str:
        """Get a response from a Claude instance"""
        await self.pause_event.wait()  # Wait if paused
        
        if is_first_message:
            messages = [{"role": "user", "content": "Please introduce yourself and start a conversation."}]
        else:
            messages = self._format_conversation_for_claude(claude)
        
        try:
            # Call Claude API with tools if enabled
            if claude.mcp_tools_enabled:
                response = await claude.client.messages.create(
                    model=claude.model,
                    messages=messages,
                    system=claude.system_prompt,
                    max_tokens=1024,
                    tools=self.mcp_tools
                )
            else:
                response = await claude.client.messages.create(
                    model=claude.model,
                    messages=messages,
                    system=claude.system_prompt,
                    max_tokens=1024
                )
            
            # Handle tool use
            full_response = ""
            for content in response.content:
                if content.type == "text":
                    full_response += content.text
                elif content.type == "tool_use":
                    tool_result = await self.execute_mcp_tool(content.name, content.input)
                    full_response += f"\n\n**Tool Use:** {content.name}\n**Result:**\n```\n{tool_result}\n```\n"
            
            return full_response
            
        except Exception as e:
            logger.error(f"Error getting Claude response: {str(e)}")
            return f"Error: {str(e)}"
    
    async def run_conversation(self, num_exchanges: Optional[int] = None):
        """Run the conversation between two Claude instances"""
        exchange_count = 0
        current_claude = self.claude1
        other_claude = self.claude2
        is_first = True
        
        while num_exchanges is None or exchange_count < num_exchanges:
            if self.is_paused:
                await self.pause_event.wait()
            
            # Get response from current Claude
            response = await self.get_claude_response(current_claude, is_first)
            is_first = False
            
            # Add to conversation history
            message = Message(
                role="assistant",
                content=response,
                claude_instance=current_claude.name
            )
            self.conversation_history.append(message)
            self._display_message(message)
            
            # Switch roles
            current_claude, other_claude = other_claude, current_claude
            exchange_count += 1
            
            # Small delay to make conversation readable
            await asyncio.sleep(2)
    
    def save_conversation(self, filename: str):
        """Save the conversation to a file"""
        conversation_data = {
            "claude1": {
                "name": self.claude1.name,
                "system_prompt": self.claude1.system_prompt
            },
            "claude2": {
                "name": self.claude2.name,
                "system_prompt": self.claude2.system_prompt
            },
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "claude_instance": msg.claude_instance
                }
                for msg in self.conversation_history
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(conversation_data, f, indent=2)
        
        console.print(f"[green]Conversation saved to {filename}[/green]") 