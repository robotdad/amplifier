# Amplifier User Guide

Complete guide to using Amplifier for AI-assisted development.

> **Note**: Amplifier is under active development. Some features and commands may change. Links to external repositories (amplifier-core, amplifier-app-cli) may break as we reorganize.

---

## Installation

### Quick Start (No Installation)

```bash
# Try immediately with uvx
uvx --from git+https://github.com/microsoft/amplifier.git@next amplifier run "Hello, Amplifier!"
```

### Global Installation

```bash
# Install as a tool
uv tool install git+https://github.com/microsoft/amplifier.git@next

# Verify installation
amplifier --version
```

### Prerequisites

- **Python 3.11+**
- **UV package manager** - [Installation guide](https://github.com/astral-sh/uv)
- **API key** - For your chosen AI provider (Anthropic recommended for now)

---

## Configuration

### Setting API Keys

```bash
# Anthropic Claude (recommended for early preview)
export ANTHROPIC_API_KEY="your-api-key"

# OpenAI (requires custom profile setup currently)
export OPENAI_API_KEY="your-api-key"

# Azure OpenAI
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
```

### Understanding Profiles

Profiles are pre-configured toolboxes that bundle providers, tools, agents, and settings. Think of them like Docker Compose files for your AI environment.

```bash
# See what profiles are available
amplifier profile list

# View profile details
amplifier profile show dev

# Set your preferred profile
amplifier profile default --set dev
```

**Bundled Profiles:**

| Profile | Purpose | When to Use |
|---------|---------|-------------|
| `foundation` | Bare minimum | Testing core functionality |
| `base` | Essential tools | Basic tasks, minimal overhead |
| `dev` | Full development | Daily development (**default & recommended**) |
| `production` | Production-ready | Persistent context, enhanced security |
| `test` | Testing | Mock provider for integration tests |
| `full` | Everything | Exploring all features |

### Creating Custom Profiles

```bash
# Create profile directory
mkdir -p ~/.amplifier/profiles

# Create profile file
cat > ~/.amplifier/profiles/my-profile.md << 'EOF'
---
profile:
  name: my-profile
  version: 1.0.0
  description: My custom configuration
  extends: dev

providers:
  - module: provider-anthropic
    config:
      model: claude-opus-4

session:
  context:
    config:
      max_tokens: 200000  # Larger context
---

# My Custom Profile

Additional documentation here.
EOF

# Use your profile
amplifier run --profile my-profile "Your prompt"
```

---

## Basic Usage

### Single Command Mode

Execute one task and exit:

```bash
# Generate code
amplifier run "Create a Python function to parse CSV files"

# Get explanations
amplifier run "Explain how async/await works in Python with examples"

# Debug errors
amplifier run "Debug this TypeError: 'NoneType' object is not subscriptable in [code snippet]"

# Code review
amplifier run "Review this code for security issues: [paste code]"
```

### Interactive Chat Mode

Start a conversation with persistent context:

```bash
# Launch chat mode
amplifier

# Or explicitly
amplifier run --mode chat
```

**Chat commands:**
- `/help` - Show available commands
- `/tools` - List available tools
- `/status` - Show session information
- `/think` - Enable plan mode (read-only)
- `/do` - Disable plan mode (allow modifications)
- `exit` or `Ctrl+C` - Quit

**Example conversation:**
```
> Explain dependency injection in Python

[AI explains concept]

> Show me an example with a real-world use case

[AI provides code example]

> How would I test this?

[AI shows testing patterns]

> exit
```

---

## Working with Agents

Agents are specialized AI sub-sessions focused on specific tasks. The dev profile includes four agents:

### Using Agents

```bash
# Let the AI decide when to use agents
amplifier run "Design a caching layer for my API"
# The AI might use zen-architect for design

# Request specific agents
amplifier run "Use bug-hunter to debug this error: [paste stack trace]"
amplifier run "Use researcher to find best practices for async error handling"
```

### Bundled Agents

**zen-architect** - Architecture and design
- Analyzes problems before implementing
- Designs system architecture
- Reviews code for simplicity and philosophy compliance

**bug-hunter** - Debugging expert
- Systematic hypothesis-driven debugging
- Tracks down errors efficiently
- Fixes issues without adding complexity

**researcher** - Content synthesis
- Researches best practices
- Analyzes documentation
- Synthesizes information from multiple sources

**modular-builder** - Implementation specialist
- Builds code from specifications
- Creates self-contained modules
- Follows modular design principles

---

## Session Management

Sessions are automatically saved and organized by project.

### Listing Sessions

```bash
# Show sessions for current project
amplifier session list

# Show all sessions across all projects
amplifier session list --all-projects

# Show sessions for specific project
amplifier session list --project /path/to/other/project
```

### Session Details

```bash
# Show session metadata
amplifier session show <session-id>

# Show full transcript
amplifier session show <session-id> --detailed
```

### Resuming Sessions

```bash
# Continue where you left off
amplifier session resume <session-id>

# Resume with different profile
amplifier session resume <session-id> --profile full
```

### Cleanup

```bash
# Remove old sessions (30 days default)
amplifier session cleanup

# Remove sessions older than 7 days
amplifier session cleanup --days 7
```

### Where Are Sessions Stored?

Sessions are stored in `~/.amplifier/projects/<project-slug>/sessions/` where the project slug is based on your current working directory.

Example: Working in `/home/user/repos/myapp` stores sessions in:
`~/.amplifier/projects/-home-user-repos-myapp/sessions/`

Each session contains:
- `transcript.jsonl` - Message history
- `events.jsonl` - All events (tool calls, approvals, etc.)
- `metadata.json` - Session info (profile, model, timestamps)

---

## Advanced Usage

### Using Different Providers

```bash
# Override provider on command line
amplifier run --provider openai --model gpt-4o "Your prompt"

# Or create a profile
cat > ~/.amplifier/profiles/openai.md << 'EOF'
---
profile:
  name: openai
  extends: base

providers:
  - module: provider-openai
    source: git+https://github.com/microsoft/amplifier-module-provider-openai@main
    config:
      model: gpt-4o
---
EOF

amplifier run --profile openai "Your prompt"
```

### Module Management

```bash
# List installed modules
amplifier module list

# Filter by type
amplifier module list --type tool

# Get module information
amplifier module show loop-streaming
```

---

## Troubleshooting

### "No providers mounted"

**Cause**: Missing API key or profile doesn't include a provider

**Solution**:
```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"

# Use a profile that includes a provider
amplifier run --profile dev "test"
```

### "Module not found"

**Cause**: Module not installed or profile missing git source

**Solution**: Modules are fetched dynamically from git sources specified in profiles. Check that your profile includes `source:` fields:

```yaml
tools:
  - module: tool-filesystem
    source: git+https://github.com/microsoft/amplifier-module-tool-filesystem@main
```

### Sessions Not Showing

**Cause**: Sessions are project-scoped

**Solution**:
```bash
# Show all sessions across projects
amplifier session list --all-projects

# Or navigate to the project directory
cd /path/to/project
amplifier session list
```

### API Rate Limits

If you hit rate limits, you can:
- Switch to a different provider
- Use a profile with cost-aware scheduling
- Reduce max_tokens in your profile

---

## Tips & Best Practices

1. **Be specific** - More context = better results
2. **Use chat mode** - For complex, multi-turn tasks
3. **Try agents** - Let specialized agents handle focused work
4. **Leverage sessions** - Resume complex work later
5. **Experiment with profiles** - Find the configuration that works for you

---

## What's Next

- **See available modules**: [MODULES.md](./MODULES.md)
- **Build your own**: [DEVELOPER.md](./DEVELOPER.md)
- **Deep dive**: [amplifier-core](https://github.com/microsoft/amplifier-core) for kernel architecture
