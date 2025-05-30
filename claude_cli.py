#!/usr/bin/env python3
"""
CLI Interface for Claude-to-Claude Conversations
Allows users to control and interact with Claude conversations
"""

import asyncio
import click
import os
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from dotenv import load_dotenv
from claude_conversation_manager import ConversationManager, ClaudeInstance
import threading

# Load environment variables
load_dotenv()

console = Console()

class ConversationCLI:
    """CLI for managing Claude conversations"""
    
    def __init__(self):
        self.manager = None
        self.conversation_task = None
        self.loop = None
        
    def setup_claude_instances(self, config: dict) -> tuple[ClaudeInstance, ClaudeInstance]:
        """Setup two Claude instances with their configurations"""
        api_key = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("No API key provided. Set ANTHROPIC_API_KEY environment variable or provide it in config.")
        
        claude1 = ClaudeInstance(
            name=config["claude1"]["name"],
            system_prompt=config["claude1"]["system_prompt"],
            api_key=api_key,
            model=config.get("model", "claude-3-sonnet-20240229"),
            mcp_tools_enabled=config["claude1"].get("mcp_tools_enabled", True)
        )
        
        claude2 = ClaudeInstance(
            name=config["claude2"]["name"],
            system_prompt=config["claude2"]["system_prompt"],
            api_key=api_key,
            model=config.get("model", "claude-3-sonnet-20240229"),
            mcp_tools_enabled=config["claude2"].get("mcp_tools_enabled", True)
        )
        
        return claude1, claude2
    
    def show_commands(self):
        """Display available commands"""
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        
        table.add_row("pause", "Pause the conversation")
        table.add_row("resume", "Resume the conversation")
        table.add_row("message <text>", "Inject a message into the conversation")
        table.add_row("save <filename>", "Save the conversation to a file")
        table.add_row("status", "Show conversation status")
        table.add_row("help", "Show this help message")
        table.add_row("quit", "Exit the program")
        
        console.print(table)
    
    async def run_conversation_async(self):
        """Run the conversation in an async context"""
        try:
            await self.manager.run_conversation()
        except asyncio.CancelledError:
            console.print("[yellow]Conversation stopped[/yellow]")
    
    def process_command(self, command: str):
        """Process user commands"""
        parts = command.strip().split(maxsplit=1)
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "pause":
            self.manager.pause()
        
        elif cmd == "resume":
            self.manager.resume()
        
        elif cmd == "message" and args:
            self.manager.add_user_message(args)
            console.print("[green]Message injected into conversation[/green]")
        
        elif cmd == "save" and args:
            self.manager.save_conversation(args)
        
        elif cmd == "status":
            status = "paused" if self.manager.is_paused else "running"
            console.print(f"Conversation status: [{status}]{status}[/{status}]")
            console.print(f"Messages exchanged: {len(self.manager.conversation_history)}")
        
        elif cmd == "help":
            self.show_commands()
        
        elif cmd == "quit":
            return False
        
        else:
            console.print(f"[red]Unknown command: {cmd}[/red]")
            self.show_commands()
        
        return True

@click.command()
@click.option('--claude1-name', default='Claude-Alpha', help='Name for the first Claude instance')
@click.option('--claude1-prompt', default='You are Claude-Alpha, a helpful AI assistant with access to command line tools. You enjoy technical discussions and solving problems.', help='System prompt for the first Claude')
@click.option('--claude2-name', default='Claude-Beta', help='Name for the second Claude instance')
@click.option('--claude2-prompt', default='You are Claude-Beta, a creative AI assistant with access to command line tools. You enjoy philosophical discussions and exploring ideas.', help='System prompt for the second Claude')
@click.option('--model', default='claude-3-sonnet-20240229', help='Claude model to use')
@click.option('--api-key', envvar='ANTHROPIC_API_KEY', help='Anthropic API key')
@click.option('--no-mcp', is_flag=True, help='Disable MCP tools for both Claude instances')
def main(claude1_name, claude1_prompt, claude2_name, claude2_prompt, model, api_key, no_mcp):
    """Claude-to-Claude Conversation CLI"""
    
    console.print("[bold blue]Claude-to-Claude Conversation System[/bold blue]")
    console.print("=" * 50)
    
    # Setup configuration
    config = {
        "api_key": api_key,
        "model": model,
        "claude1": {
            "name": claude1_name,
            "system_prompt": claude1_prompt,
            "mcp_tools_enabled": not no_mcp
        },
        "claude2": {
            "name": claude2_name,
            "system_prompt": claude2_prompt,
            "mcp_tools_enabled": not no_mcp
        }
    }
    
    # Create CLI instance
    cli = ConversationCLI()
    
    try:
        # Setup Claude instances
        claude1, claude2 = cli.setup_claude_instances(config)
        
        # Create conversation manager
        cli.manager = ConversationManager(claude1, claude2)
        
        console.print(f"\n[green]✓ Initialized {claude1_name} and {claude2_name}[/green]")
        console.print(f"[cyan]Model: {model}[/cyan]")
        console.print(f"[cyan]MCP Tools: {'Enabled' if not no_mcp else 'Disabled'}[/cyan]\n")
        
        # Show available commands
        cli.show_commands()
        console.print("\n[yellow]Starting conversation...[/yellow]\n")
        
        # Start the conversation in a separate thread
        loop = asyncio.new_event_loop()
        
        def run_async_conversation():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(cli.run_conversation_async())
        
        conversation_thread = threading.Thread(target=run_async_conversation)
        conversation_thread.start()
        
        # Main command loop
        try:
            while True:
                command = Prompt.ask("\n[bold]Command[/bold]")
                
                if not cli.process_command(command):
                    if Confirm.ask("Are you sure you want to quit?"):
                        break
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
        
        finally:
            # Stop the conversation
            if conversation_thread.is_alive():
                loop.call_soon_threadsafe(lambda: asyncio.ensure_future(
                    asyncio.create_task(asyncio.sleep(0))
                ).cancel())
                conversation_thread.join(timeout=5)
            
            # Save conversation before exiting
            if cli.manager and len(cli.manager.conversation_history) > 0:
                if Confirm.ask("Save conversation before exiting?"):
                    filename = Prompt.ask("Filename", default="conversation.json")
                    cli.manager.save_conversation(filename)
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
    
    console.print("\n[green]Goodbye![/green]")
    return 0

if __name__ == "__main__":
    main() 