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
import subprocess
import pty
import select
import termios
import tty
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set to DEBUG for troubleshooting
# logger.setLevel(logging.DEBUG)

console = Console()

class PersistentShell:
    """Maintains a persistent shell session"""
    
    def __init__(self, working_dir: str = None):
        # Create a pseudo-terminal
        self.master, slave = pty.openpty()
        
        # Set up environment with minimal prompt to avoid issues
        env = os.environ.copy()
        env['PS1'] = '$ '  # Simple prompt without backslash escaping
        env['PS2'] = '> '
        env['TERM'] = 'dumb'  # Avoid terminal control sequences
        
        # Start bash in non-interactive mode initially
        self.shell = subprocess.Popen(
            ['/bin/bash', '--norc', '--noprofile'],  # Skip RC files
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=working_dir,
            env=env,
            universal_newlines=False,
            preexec_fn=os.setsid
        )
        os.close(slave)
        self.current_dir = working_dir or os.getcwd()
        
        # Set up the prompt explicitly
        self._setup_shell()
        
    def _setup_shell(self):
        """Setup the shell with proper prompt"""
        # Send commands to set up the shell
        setup_commands = [
            "PS1='$ '",  # Set simple prompt
            "PS2='> '",
            "set +o history",  # Disable history expansion
            "stty -echo",  # Disable echo to avoid seeing commands twice
        ]
        
        for cmd in setup_commands:
            os.write(self.master, (cmd + '\n').encode())
            time.sleep(0.1)
        
        # Clear any output from setup
        self._clear_output(timeout=0.5)
        
    def _clear_output(self, timeout=0.5):
        """Clear any pending output from the shell"""
        import fcntl
        
        # Set non-blocking mode
        flags = fcntl.fcntl(self.master, fcntl.F_GETFL)
        fcntl.fcntl(self.master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ready, _, _ = select.select([self.master], [], [], 0.1)
                if ready:
                    os.read(self.master, 4096)
                else:
                    break
            except OSError:
                break
                
        # Restore blocking mode
        fcntl.fcntl(self.master, fcntl.F_SETFL, flags)
        
    def execute_command(self, command: str, timeout: int = 30) -> str:
        """Execute a command in the persistent shell"""
        # Clear any pending output first
        self._clear_output(timeout=0.1)
        
        # Send command with unique marker
        marker = f"__MARKER_{int(time.time()*1000)}__"
        full_command = f"{command}; echo {marker}$?"
        os.write(self.master, (full_command + '\n').encode())
        
        # Read output
        output = []
        start_time = time.time()
        marker_found = False
        exit_code = None
        
        while time.time() - start_time < timeout:
            ready, _, _ = select.select([self.master], [], [], 0.1)
            if ready:
                try:
                    chunk = os.read(self.master, 4096).decode('utf-8', errors='replace')
                    
                    # Look for our marker
                    if marker in chunk:
                        marker_found = True
                        # Extract exit code and output before marker
                        parts = chunk.split(marker)
                        if len(parts) >= 2:
                            output.append(parts[0])
                            # Try to extract exit code
                            exit_code_part = parts[1].split('\n')[0].strip()
                            if exit_code_part.isdigit():
                                exit_code = int(exit_code_part)
                        break
                    else:
                        output.append(chunk)
                        
                except OSError as e:
                    if e.errno == 5:  # Input/output error
                        return "Shell process terminated"
                    raise
            else:
                # Check if process is still alive
                if self.shell.poll() is not None:
                    return "Shell process terminated"
        
        if not marker_found:
            return f"Command timed out after {timeout} seconds"
            
        # Join output and clean it up
        result = ''.join(output)
        
        # Remove the command echo if present
        lines = result.split('\n')
        if lines and command in lines[0]:
            lines = lines[1:]
        result = '\n'.join(lines).strip()
        
        # Add exit code info if command failed
        if exit_code and exit_code != 0:
            result += f"\n[Exit code: {exit_code}]"
            
        return result
    
    def close(self):
        """Close the shell session"""
        if hasattr(self, 'shell') and self.shell.poll() is None:
            try:
                # Send exit command
                os.write(self.master, b'exit\n')
                time.sleep(0.1)
            except:
                pass
            
            # Terminate if still running
            if self.shell.poll() is None:
                self.shell.terminate()
                self.shell.wait()
                
        if hasattr(self, 'master'):
            try:
                os.close(self.master)
            except:
                pass

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
        
        # Initialize persistent shell
        project_dir = Path(__file__).parent.absolute()
        self.shell = PersistentShell(str(project_dir))
        self.current_dir = str(project_dir)
        logger.info(f"Initialized persistent shell in {self.current_dir}")
        
    def __del__(self):
        """Cleanup shell on deletion"""
        if hasattr(self, 'shell'):
            self.shell.close()
            logger.info("Closed persistent shell")
        
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
                "name": "change_directory",
                "description": "Change the current working directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to change to"
                        }
                    },
                    "required": ["path"]
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
        """Execute an MCP tool using the persistent shell"""
        
        # Get the project directory (where this script is located)
        project_dir = Path(__file__).parent.absolute()
        
        if tool_name == "execute_command":
            command = arguments["command"]
            timeout = arguments.get("timeout", 30)
            
            try:
                # Execute in persistent shell
                output = self.shell.execute_command(command, timeout)
                return f"Command: {command}\nOutput:\n{output}"
            except Exception as e:
                return f"Error executing command: {str(e)}"
        
        elif tool_name == "change_directory":
            path = arguments["path"]
            try:
                # Convert relative paths to absolute paths based on current directory
                if not Path(path).is_absolute():
                    path = Path(self.current_dir) / path
                    
                # Change directory in persistent shell
                output = self.shell.execute_command(f"cd {path} && pwd", 5)
                
                # Check if successful
                if "No such file or directory" not in output and "not found" not in output:
                    # Update current directory
                    pwd_output = output.strip()
                    if pwd_output and pwd_output.startswith('/'):
                        self.current_dir = pwd_output
                    return f"Changed directory to {self.current_dir}"
                else:
                    return f"Error: {output}"
            except Exception as e:
                return f"Error changing directory: {str(e)}"
        
        elif tool_name == "list_directory":
            path = arguments.get("path", ".")
            try:
                # Use ls command in the persistent shell
                if path == ".":
                    command = "ls -la"
                else:
                    command = f"ls -la {path}"
                    
                output = self.shell.execute_command(command, 5)
                return f"Directory listing:\n{output}"
            except Exception as e:
                return f"Error listing directory: {str(e)}"
        
        elif tool_name == "read_file":
            path = arguments["path"]
            try:
                # Use cat command in the persistent shell
                output = self.shell.execute_command(f"cat {path}", 10)
                return f"File contents of {path}:\n{output}"
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        elif tool_name == "write_file":
            path = arguments["path"]
            content = arguments["content"]
            append = arguments.get("append", False)
            try:
                # Escape content for shell
                escaped_content = content.replace("'", "'\"'\"'")
                
                # Create parent directory if needed
                parent_dir = Path(path).parent
                if parent_dir != Path('.'):
                    self.shell.execute_command(f"mkdir -p {parent_dir}", 5)
                
                # Write file using echo or cat
                if append:
                    command = f"echo '{escaped_content}' >> {path}"
                else:
                    command = f"echo '{escaped_content}' > {path}"
                
                output = self.shell.execute_command(command, 10)
                
                # Verify file was written
                verify_output = self.shell.execute_command(f"ls -la {path}", 5)
                
                return f"Wrote to {path}\nVerification:\n{verify_output}"
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
            
            # Log the response structure for debugging
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response attributes: {dir(response)}")
            
            # Handle tool use - the response structure is a Message object
            full_response = ""
            
            # Check if response has content attribute
            if hasattr(response, 'content'):
                for content_block in response.content:
                    if hasattr(content_block, 'type'):
                        if content_block.type == "text":
                            full_response += content_block.text
                        elif content_block.type == "tool_use":
                            # Execute the tool
                            tool_result = await self.execute_mcp_tool(content_block.name, content_block.input)
                            full_response += f"\n\n**Tool Use:** {content_block.name}\n**Result:**\n```\n{tool_result}\n```\n"
                    else:
                        # Handle cases where content_block might be a string
                        full_response += str(content_block)
            else:
                # Fallback for different response structures
                logger.warning(f"Unexpected response structure: {response}")
                full_response = str(response)
            
            # If we got no response, return a default message
            if not full_response:
                full_response = "I apologize, but I couldn't generate a proper response."
            
            return full_response
            
        except AttributeError as e:
            logger.error(f"AttributeError in get_claude_response: {str(e)}")
            logger.error(f"Response object: {response if 'response' in locals() else 'No response object'}")
            return f"Error accessing response attributes: {str(e)}"
        except Exception as e:
            logger.error(f"Error getting Claude response: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
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