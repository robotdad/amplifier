# Amplifier

AI-powered modular development platform that brings the power of AI coding assistants to your fingertips.

## 🚀 Quick Start

The fastest way to try Amplifier - no installation required:

```bash
# Run directly with uvx (Python 3.11+ required)
uvx --from git+https://github.com/microsoft/amplifier.git@next amplifier run --profile dev "Create a Python web server"

# Or install globally
uv tool install git+https://github.com/microsoft/amplifier.git@next

# Then run
amplifier run --profile dev "Write a function to parse CSV files"
```

## 🎯 What is Amplifier?

Amplifier is a modular AI development assistant that helps you:

- Generate code with AI assistance
- Work with multiple AI providers (Anthropic Claude, OpenAI GPT, etc.)
- Extend functionality through a rich module ecosystem
- Maintain context across long development sessions

> **Note**: This package is a **reference distribution** that bundles [amplifier-core](https://github.com/microsoft/amplifier-core) (the official kernel) with reference implementations of CLI and modules. The core is stable and official; the CLI and modules serve as working examples that you can use, fork, or replace with your own implementations.

## 📦 Installation Options

### Quick Try (No Installation)

```bash
# Requires Python 3.11+ and uvx
uvx --from git+https://github.com/microsoft/amplifier.git@next amplifier --help
```

### Standard Installation

```bash
# Install with default modules
uv tool install "amplifier[default] @ git+https://github.com/microsoft/amplifier.git@next"

# Install with Anthropic support
uv tool install "amplifier[anthropic] @ git+https://github.com/microsoft/amplifier.git@next"

# Install with all providers
uv tool install "amplifier[all] @ git+https://github.com/microsoft/amplifier.git@next"
```

### Development Installation

```bash
# Clone and install for development
git clone https://github.com/microsoft/amplifier-dev.git
cd amplifier-dev
```

Read README.md in root of `amplifier-dev`

## 🎮 Usage Examples

### Interactive Chat Mode

```bash
# Start an interactive session
amplifier run --mode chat

# With specific provider
amplifier run --mode chat --provider anthropic --model claude-sonnet-4.5
```

### Single Command Mode

```bash
# Execute a single task
amplifier run "Create a REST API with FastAPI"

# Use configuration file
amplifier run --config my-config.toml "Refactor this function"
```

### Module Management

```bash
# List available modules
amplifier module list

# Get module information
amplifier module info loop-basic
```

## ⚙️ Configuration

Amplifier uses profiles for configuration. See what's available:

```bash
# List bundled profiles
amplifier profile list

# Use a profile
amplifier profile apply dev

# Show profile details
amplifier profile show dev
```

### Bundled Profiles

- **foundation** - Absolute minimum (orchestrator, context, provider only)
- **base** - Essential tools (filesystem, bash, logging)
- **dev** - Full development setup (adds web, search, agents, streaming UI)
- **production** - Production-optimized (persistent context, enhanced security)
- **test** - Testing environment (mock provider)
- **full** - All features enabled

### Environment Variables

Set API keys for providers:

```bash
export ANTHROPIC_API_KEY="your-api-key"
export OPENAI_API_KEY="your-api-key"
```

### Custom Profiles

Create custom profiles in `.amplifier/profiles/`:

```bash
# Create custom profile
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

tools:
  - module: tool-custom
---
EOF

# Apply it
amplifier profile apply my-profile
```

See [Profile Authoring Guide](https://github.com/microsoft/amplifier-dev/blob/main/docs/PROFILE_AUTHORING.md) for details.

## 🤖 Agents

Amplifier includes specialized agents for focused tasks:

```bash
# List available agents
amplifier agent list

# Show agent details
amplifier agent show zen-architect
```

### Bundled Agents

- **zen-architect** - System design with ruthless simplicity
- **bug-hunter** - Systematic debugging and issue resolution
- **researcher** - Research and information synthesis
- **modular-builder** - Implementation following modular principles

Agents are loaded via profiles and can be customized at project or user level.

## 🧩 Modules

Amplifier uses a modular architecture. Default modules include:

- **Orchestrators**: Control the AI agent loop

  - `loop-basic`: Standard sequential execution
  - `loop-streaming`: Real-time streaming responses

- **Providers**: Connect to AI models

  - `provider-anthropic`: Claude models
  - `provider-openai`: GPT models

- **Tools**: Extend capabilities
  - `tool-filesystem`: File operations
  - `tool-bash`: Command execution
  - `tool-web`: Web search and fetch
  - `tool-search`: Web search capabilities
  - `tool-task`: Agent delegation

## 📚 Documentation

- [User Guide](./docs/USER_GUIDE.md) - Complete usage documentation
- [Module Catalog](./docs/MODULES.md) - Available modules and their features
- [Configuration Guide](./docs/CONFIG.md) - Detailed configuration options

## 🛠 For Developers

Want to build your own modules or contribute?

- **Core Library**: [microsoft/amplifier-core](https://github.com/microsoft/amplifier-core)
- **Module Development Guide**: [docs/DEVELOPER.md](./docs/DEVELOPER.md)

## 🎉 Getting Started

Ready to amplify your development? Try this:

```bash
# Your first Amplifier command
uvx --from git+https://github.com/microsoft/amplifier.git@next amplifier run --profile dev \
  "Create a Python script that fetches weather data and sends a summary email"
```

Welcome to the future of AI-assisted development! 🚀

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
