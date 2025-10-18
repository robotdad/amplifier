# Amplifier

**AI-powered modular development assistant - currently in early preview.**

> [!CAUTION]
> This project is a research demonstrator. It is in early development and may change significantly. Using permissive AI tools on your computer requires careful attention to security considerations and careful human supervision, and even then things can still go wrong. Use it with caution, and at your own risk, we have NOT built in the safety systems yet. We are performing our _active exploration_ in the open for others to join in the conversation and exploration, not as a product or "official release".

---

## What is Amplifier?

Amplifier brings AI assistance to your command line with a modular, extensible architecture. More info to follow here shortly, for our earlier exploration that this will be racing to supercede, check out [our original version](https://github.com/microsoft/amplifier).

**This CLI is _just one_ interface**—the reference implementation. The real power is the modular platform underneath. Soon you'll see web interfaces, mobile apps, voice-driven coding, and even Amplifier-to-Amplifier collaborative experiences. The community will build interfaces tailored to their workflows, mixing and matching modules dynamically to craft custom AI experiences.

---

## Quick Start (3 Steps to Your First AI Interaction)

### 1. Install UV

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Set Your API Key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

> **Note**: We've done most of our early testing with Anthropic Claude. Other providers (OpenAI, Azure OpenAI, Ollama) are supported but may require custom profiles or additional setup. We're rapidly improving the out-of-box experience—expect this to be easier next week!

### 3. Run Amplifier

```bash
# Try it instantly (no installation)
uvx --from git+https://github.com/microsoft/amplifier.git@next amplifier run "tell me about your agents and what kinds of tasks you might be able to help with"

# Or start a conversation
uvx --from git+https://github.com/microsoft/amplifier.git@next amplifier
```

**That's it!** You now have an AI coding assistant at your fingertips.

---

## What Can Amplifier Do?

First of all, this still VERY early and we have not brought _most_ of our features over from our prior version yet, so keep your expectations low and we'll get it ramped up very quickly over the next week or two. Consider this just an early sneak peek.

- **Generate code** - From simple functions to full applications
- **Debug problems** - Systematic error resolution with the bug-hunter agent
- **Design systems** - Architecture planning with the zen-architect agent
- **Research solutions** - Find patterns and best practices with the researcher agent
- **Build modules** - Use Amplifier to create new Amplifier modules (yes, really!)

**Additional features over prior version:**

- **Modular**: Swap AI providers, tools, and behaviors like LEGO bricks
- **Profile-based**: Pre-configured toolboxes for different scenarios
- **Session persistence**: Pick up where you left off, even across projects
- **Extensible**: Build your own modules, interfaces, or entire custom experiences

---

## Installation Options

### Instant Try (Recommended for Testing)

```bash
# No installation, runs directly
uvx --from git+https://github.com/microsoft/amplifier.git@next amplifier run "Your prompt"
```

### Global Tool Install

```bash
# Install once, run anywhere
uv tool install git+https://github.com/microsoft/amplifier.git@next

# Then use
amplifier run "Your prompt"
amplifier  # Start chat mode
```

---

## Basic Usage

### Single Commands

```bash
# Get quick answers
amplifier run "Explain async/await in Python"

# Generate code
amplifier run "Create a REST API for a todo app with FastAPI"

# Debug issues
amplifier run "Why does this code throw a TypeError: [paste code]"
```

### Interactive Chat Mode

```bash
# Start a conversation
amplifier

# Or explicitly
amplifier run --mode chat
```

In chat mode:

- Context persists across messages
- Use `/help` for special commands
- Type `exit` or Ctrl+C to quit

### Using Profiles

Profiles are pre-configured toolboxes for different scenarios:

```bash
# See available profiles
amplifier profile list

# Use a specific profile
amplifier run --profile dev "Your prompt"

# Set default for your project (the directory you launch `amplifier` from)
amplifier profile default --set dev
```

**Bundled profiles:**

- `foundation` - Absolute minimum (provider + orchestrator only)
- `base` - Essential tools (filesystem, bash, logging)
- `dev` - Full development setup (web, search, agents) - **Default & recommended**
- `production` - "Production" minded exploration (persistent context, early command safety)
- `full` - Everything enabled

### Working with Agents

Specialized agents for focused tasks:

```bash
# Let the AI delegate to specialized agents
amplifier run "Design a caching layer with careful consideration"
# The AI will use zen-architect when appropriate

# Or request specific agents
amplifier run "Use bug-hunter to debug this error: [paste error]"
```

**Bundled agents:**

- **zen-architect** - System design with ruthless simplicity
- **bug-hunter** - Systematic debugging
- **researcher** - Content research and synthesis
- **modular-builder** - Code implementation

---

## Sessions & Persistence

Every interaction is automatically saved:

```bash
# List your recent sessions (current project only)
amplifier session list

# See all sessions across all projects
amplifier session list --all-projects

# View session details
amplifier session show <session-id>

# Resume a previous session
amplifier session resume <session-id>
```

Sessions are project-scoped—when you're in `/home/user/myapp`, you see only `myapp` sessions. Change directories, see different sessions. Your work stays organized.

---

## What's Next

- **Learn more**: [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - Complete usage guide
- **See modules**: [docs/MODULES.md](docs/MODULES.md) - Available modules catalog
- **Build with AI**: [docs/DEVELOPER.md](docs/DEVELOPER.md) - Use Amplifier to build modules

> **Note**: Amplifier is under active development. Links may break as we evolve. If you encounter issues, please report them.

---

## The Vision

**Today**: A powerful CLI for AI-assisted development.

**Tomorrow**: A platform where:

- **Multiple interfaces** coexist - CLI, web, mobile, voice, IDE plugins
- **Community modules** extend capabilities infinitely
- **Dynamic mixing** - Amplifier composes custom solutions from available modules
- **AI builds AI** - Use Amplifier to create new modules with minimal manual coding
- **Collaborative AI** - Amplifier instances work together on complex tasks

The modular foundation we're building today enables all of this. You're getting in early on something that's going to fundamentally change how we work with AI.

---

## Current State (Be Aware)

This is an **early preview release**:

- APIs are stabilizing but may change
- Some features are experimental
- Documentation is catching up with code
- We're moving fast—breaking changes happen

**What works well today:**

- ✅ Core AI interactions (Anthropic Claude)
- ✅ Profile-based configuration
- ✅ Agent delegation
- ✅ Session persistence
- ✅ Module loading from git sources

**What's rough around the edges:**

- ⚠️ Other providers need more testing
- ⚠️ Some error messages could be clearer
- ⚠️ Documentation is incomplete in places
- ⚠️ Installation experience will improve significantly

**Join us on this journey!** Fork, experiment, build modules, share feedback. This is the ground floor.

---

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
