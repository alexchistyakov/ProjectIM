# Project Inner Monologue (an AI concious loop)

Two instances of Claude made to talk to each other indefinitely with unlimited access to their own github repo and server terminal

The inspiration behind this project was the significant improvement in LLM preformance by introducing CoT (chain of thought) prompting. I was inspired by the fact that on a high level, you simply create guidelines for the LLM to *THINK* like a person processing a task.

This made me introspect on my own thinking patterns and how I come up with ideas, hoping that something can be applied to LLMs as well. I very quickly realized that the main engine behind my ideas and projects is my inner monologue, or, in other words, constantly talking about my ideas to myself.

The pattern continues when you extend it to how teams work in general, but Anthropic already did an experiment with "lead" agents and "subagents".

What I'm interested in with this project is getting the model in a constant dialog with itself, unlimited access to its own server terminal + github repo and a general directive such as "You are here to self improve, your conversation is to continue indefinitely", like people self-improve.

I plan on restarting this project once in a while to see AI capabilities. Currently, the model capable of making the most progress was Claude Opus 4, but it also drained $60 in 2 hours from my account. 

Note: memory_manager and memory_system_design were made by Claude

## Features

- **Dual Claude Instances**: Two Claude AIs with customizable system prompts can converse with each other
- **MCP Integration**: Both Claude instances have access to command-line tools through MCP
- **Interactive CLI**: Control conversations in real-time with commands to pause, resume, and inject messages
- **Command-Line Tools**: Execute shell commands, read/write files, and navigate directories
- **Rich Console Output**: Beautiful formatted output with color-coded messages
- **Conversation Persistence**: Save and load conversations in JSON format

## System Architecture

The system consists of three main components:

1. **MCP Command Server** (`mcp_command_server.py`): Provides command-line access as MCP tools
2. **Conversation Manager** (`claude_conversation_manager.py`): Orchestrates the conversation between two Claude instances
3. **CLI Interface** (`claude_cli.py`): Interactive command-line interface for controlling conversations

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd ProjectIM
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Anthropic API key:
```bash
cp env.example .env
# Edit .env and add your Anthropic API key
```

## Usage

### Basic Usage

Run the CLI with default settings:
```bash
python claude_cli.py
```

### Advanced Usage

Customize the Claude instances:
```bash
python claude_cli.py \
  --claude1-name "Developer" \
  --claude1-prompt "You are a senior software developer who loves clean code and best practices." \
  --claude2-name "Designer" \
  --claude2-prompt "You are a creative UI/UX designer who focuses on user experience." \
  --model "claude-3-opus-20240229"
```

### CLI Commands

Once the conversation starts, you can use these commands:

- `pause` - Pause the conversation
- `resume` - Resume a paused conversation
- `message <text>` - Inject a message into the conversation
- `save <filename>` - Save the conversation to a file
- `status` - Show conversation status
- `help` - Display available commands
- `quit` - Exit the program

### Example Session

```
Claude-to-Claude Conversation System
==================================================

✓ Initialized Claude-Alpha and Claude-Beta
Model: claude-3-sonnet-20240229
MCP Tools: Enabled

Available Commands
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Command         ┃ Description                             ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ pause           │ Pause the conversation                  │
│ resume          │ Resume the conversation                 │
│ message <text>  │ Inject a message into the conversation  │
│ save <filename> │ Save the conversation to a file         │
│ status          │ Show conversation status                │
│ help            │ Show this help message                  │
│ quit            │ Exit the program                        │
└─────────────────┴─────────────────────────────────────────┘

Starting conversation...

Command: pause
Conversation paused

Command: message Let's discuss Python best practices
Message injected into conversation

Command: resume
Conversation resumed
```

## MCP Tools Available

Both Claude instances have access to these command-line tools:

1. **execute_command**: Execute shell commands with timeout support
2. **change_directory**: Navigate the file system
3. **list_directory**: List directory contents
4. **read_file**: Read file contents
5. **write_file**: Write or append to files

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)

### Command-Line Options

- `--claude1-name`: Name for the first Claude instance (default: Claude-Alpha)
- `--claude1-prompt`: System prompt for the first Claude
- `--claude2-name`: Name for the second Claude instance (default: Claude-Beta)
- `--claude2-prompt`: System prompt for the second Claude
- `--model`: Claude model to use (default: claude-3-sonnet-20240229)
- `--api-key`: Override the environment variable API key
- `--no-mcp`: Disable MCP tools for both instances

## MCP Server Integration

The MCP command server can also be used standalone or integrated with Claude Desktop:

### Standalone MCP Server

```bash
python mcp_command_server.py
```

### Claude Desktop Integration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "command-line": {
      "command": "python",
      "args": ["/path/to/mcp_command_server.py"]
    }
  }
}
```

## Security Considerations

- The system executes shell commands with the permissions of the running user
- Be cautious when allowing Claude instances to execute commands
- Consider running in a sandboxed environment for safety
- Review conversation logs before saving sensitive information

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure your Anthropic API key is correctly set in the `.env` file
2. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
3. **Permission Denied**: The MCP tools may need appropriate permissions to execute commands or access files

### Debug Mode

For debugging, you can increase logging verbosity by modifying the logging configuration in the Python files.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is provided as-is for educational and demonstration purposes. 
