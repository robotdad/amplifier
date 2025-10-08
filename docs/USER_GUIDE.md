# Amplifier User Guide

## Getting Started

Amplifier is an AI-powered development assistant that helps you write code, debug problems, and build software using modular AI components.

## Installation

### Quick Start (No Installation)
```bash
# Try it immediately with uvx
uvx --from git+https://github.com/microsoft/amplifier.git amplifier run "Hello, Amplifier!"
```

### Standard Installation
```bash
pip install git+https://github.com/microsoft/amplifier.git
```

## Basic Usage

### Running Commands

Execute a single AI task:
```bash
amplifier run "Create a Python function to validate email addresses"
```

### Interactive Mode

Start a conversation:
```bash
amplifier run --mode chat
```

In chat mode:
- Type your requests naturally
- The AI maintains context across the conversation
- Type `exit` or press Ctrl+C to quit

### Using Different AI Providers

#### Anthropic Claude
```bash
export ANTHROPIC_API_KEY="your-key"
amplifier run --provider anthropic --model claude-sonnet-4.5 "Your prompt"
```

#### OpenAI GPT
```bash
export OPENAI_API_KEY="your-key"
amplifier run --provider openai --model gpt-4 "Your prompt"
```

## Configuration

### Creating a Configuration File

Initialize a default configuration:
```bash
amplifier init
```

This creates `amplifier.toml` with default settings.

### Configuration Options

```toml
[provider]
name = "anthropic"  # AI provider to use
model = "claude-sonnet-4.5"  # Specific model

[session]
max_tokens = 100000  # Maximum context size
auto_compact = true  # Automatically compress long conversations
```

### Using Custom Configuration

```bash
amplifier run --config my-config.toml "Your prompt"
```

## Working with Modules

### Listing Modules
```bash
# See all installed modules
amplifier module list

# Filter by type
amplifier module list --type agent
```

### Module Information
```bash
amplifier module info loop-basic
```

## Common Workflows

### Code Generation
```bash
amplifier run "Create a REST API with FastAPI that manages a todo list"
```

### Code Review
```bash
amplifier run "Review this code for security issues: [paste code]"
```

### Debugging
```bash
amplifier run "Debug this error: [paste error message and context]"
```

### Learning
```bash
amplifier run --mode chat
> Explain how async/await works in Python
> Show me an example with multiple concurrent tasks
> How do I handle errors in async code?
```

## Tips and Tricks

1. **Be Specific**: More detailed prompts get better results
2. **Use Chat Mode**: For complex tasks requiring back-and-forth
3. **Save Configurations**: Create different configs for different projects
4. **Check Module Docs**: Each module may have specific features

## Troubleshooting

### API Key Issues
Ensure your API keys are set:
```bash
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
```

### Module Not Found
Check installed modules:
```bash
amplifier module list
```

### Context Too Long
The system automatically compacts when approaching limits. You can also:
- Start a new session
- Use a configuration with higher `max_tokens`

## Getting Help

- GitHub Issues: https://github.com/microsoft/amplifier/issues
- Discussions: https://github.com/microsoft/amplifier/discussions
