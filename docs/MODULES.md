# Amplifier Module Catalog

Amplifier's modular architecture allows you to mix and match capabilities. This page catalogs available modules—both reference implementations and community contributions.

> **Note**: Module links point to GitHub repositories. We're moving fast, so some may be temporarily unavailable as we reorganize.

---

## Reference Implementation Modules

These modules are maintained as part of the Amplifier project and serve as both working implementations and examples for building your own.

### Orchestrators

Control the AI agent execution loop.

| Module | Description | Repository |
|--------|-------------|------------|
| **loop-basic** | Standard sequential execution - simple request/response flow | [amplifier-module-loop-basic](https://github.com/microsoft/amplifier-module-loop-basic) |
| **loop-streaming** | Real-time streaming responses with extended thinking support | [amplifier-module-loop-streaming](https://github.com/microsoft/amplifier-module-loop-streaming) |
| **loop-events** | Event-driven orchestrator with hook integration | [amplifier-module-loop-events](https://github.com/microsoft/amplifier-module-loop-events) |

### Providers

Connect to AI model providers.

| Module | Description | Repository |
|--------|-------------|------------|
| **provider-anthropic** | Anthropic Claude integration (Sonnet 4.5, Opus, etc.) | [amplifier-module-provider-anthropic](https://github.com/microsoft/amplifier-module-provider-anthropic) |
| **provider-openai** | OpenAI GPT integration | [amplifier-module-provider-openai](https://github.com/microsoft/amplifier-module-provider-openai) |
| **provider-azure-openai** | Azure OpenAI with managed identity support | [amplifier-module-provider-azure-openai](https://github.com/microsoft/amplifier-module-provider-azure-openai) |
| **provider-ollama** | Local Ollama models | [amplifier-module-provider-ollama](https://github.com/microsoft/amplifier-module-provider-ollama) |
| **provider-mock** | Mock provider for testing | [amplifier-module-provider-mock](https://github.com/microsoft/amplifier-module-provider-mock) |

### Tools

Extend AI capabilities with actions.

| Module | Description | Repository |
|--------|-------------|------------|
| **tool-filesystem** | File operations (read, write, edit, list) | [amplifier-module-tool-filesystem](https://github.com/microsoft/amplifier-module-tool-filesystem) |
| **tool-bash** | Shell command execution | [amplifier-module-tool-bash](https://github.com/microsoft/amplifier-module-tool-bash) |
| **tool-web** | Web search and content fetching | [amplifier-module-tool-web](https://github.com/microsoft/amplifier-module-tool-web) |
| **tool-search** | Web search capabilities | [amplifier-module-tool-search](https://github.com/microsoft/amplifier-module-tool-search) |
| **tool-task** | Agent delegation (sub-session spawning) | [amplifier-module-tool-task](https://github.com/microsoft/amplifier-module-tool-task) |

### Context Managers

Manage conversation state and history.

| Module | Description | Repository |
|--------|-------------|------------|
| **context-simple** | In-memory context with automatic compaction | [amplifier-module-context-simple](https://github.com/microsoft/amplifier-module-context-simple) |
| **context-persistent** | File-backed persistent context across sessions | [amplifier-module-context-persistent](https://github.com/microsoft/amplifier-module-context-persistent) |

### Hooks

Extend lifecycle events and observability.

| Module | Description | Repository |
|--------|-------------|------------|
| **hooks-logging** | Unified JSONL event logging to per-session files | [amplifier-module-hooks-logging](https://github.com/microsoft/amplifier-module-hooks-logging) |
| **hooks-redaction** | Privacy-preserving data redaction | [amplifier-module-hooks-redaction](https://github.com/microsoft/amplifier-module-hooks-redaction) |
| **hooks-approval** | Interactive approval for sensitive operations | [amplifier-module-hooks-approval](https://github.com/microsoft/amplifier-module-hooks-approval) |
| **hooks-backup** | Automatic session backup | [amplifier-module-hooks-backup](https://github.com/microsoft/amplifier-module-hooks-backup) |
| **hooks-streaming-ui** | Real-time UI updates during streaming | [amplifier-module-hooks-streaming-ui](https://github.com/microsoft/amplifier-module-hooks-streaming-ui) |
| **hooks-scheduler-cost-aware** | Cost-aware model routing | [amplifier-module-hooks-scheduler-cost-aware](https://github.com/microsoft/amplifier-module-hooks-scheduler-cost-aware) |
| **hooks-scheduler-heuristic** | Heuristic-based model selection | [amplifier-module-hooks-scheduler-heuristic](https://github.com/microsoft/amplifier-module-hooks-scheduler-heuristic) |

---

## Using Modules

### In Profiles

Modules are loaded via profiles (recommended):

```yaml
# ~/.amplifier/profiles/my-profile.md
---
profile:
  name: my-profile
  extends: base

tools:
  - module: tool-web
    source: git+https://github.com/microsoft/amplifier-module-tool-web@main
  - module: tool-custom
    source: git+https://github.com/you/your-custom-tool@main
---
```

### Command Line

```bash
# See installed modules
amplifier module list

# Get module details
amplifier module show tool-filesystem
```

---

## Community Modules

> **⚠️ CRITICAL SECURITY WARNING**
>
> Community modules execute arbitrary code in your environment with full access to your filesystem, network, and credentials.
>
> - **Only use modules from sources you absolutely trust**
> - **Review module code before installation** - read every line
> - **Understand what the module does** - don't trust descriptions alone
> - **Use at your own risk** - no warranties, guarantees, or security vetting
> - **Assume malicious intent** until proven otherwise
>
> You are responsible for what runs on your machine. When in doubt, don't install it.

### Contributing Your Modules

Built something cool? Share it with the community!

**To add your module to this catalog:**

1. **Build your module** - See [DEVELOPER.md](./DEVELOPER.md) for guidance
2. **Publish to GitHub** - Make your code publicly reviewable
3. **Test thoroughly** - Ensure it works with current Amplifier versions
4. **Submit a PR** - Add your module to the "Community Modules" section below with:
   - Module name and description
   - GitHub repository link
   - Your name/organization
   - Compatible Amplifier version
   - **Clear documentation** in your repo's README

**Module submission guidelines:**
- Must follow Amplifier module conventions
- Must include comprehensive README
- Must include tests
- Must specify compatible Amplifier versions
- Source code must be publicly available for review

### Community-Contributed Modules

*No community modules yet - be the first to contribute!*

**Example entry format:**
```markdown
- **tool-git** by @username - Git operations and repository management
  - Repository: https://github.com/username/amplifier-module-tool-git
  - Compatible: Amplifier 0.1.x
  - Status: Active
```

---

## Building Your Own Modules

Amplifier can help you build Amplifier modules! See [DEVELOPER.md](./DEVELOPER.md) for how to use AI to create custom modules with minimal manual coding.

The modular architecture makes it easy to:
- Extend capabilities with new tools
- Add support for new AI providers
- Create domain-specific agents
- Build custom interfaces (web, mobile, voice)
- Experiment with new orchestration strategies

---

## Module Architecture

All modules follow the same pattern:

1. **Entry point**: Implement `mount(coordinator, config)` function
2. **Registration**: Register capabilities with the coordinator
3. **Isolation**: Handle errors gracefully, never crash the kernel
4. **Contracts**: Follow one of the stable interfaces (Tool, Provider, Hook, etc.)

For technical details, see:
- [amplifier-core](https://github.com/microsoft/amplifier-core) - Kernel interfaces and protocols
- [amplifier-dev docs](https://github.com/microsoft/amplifier-dev/tree/main/docs) - Architecture guides

---

**Ready to build?** Check out [DEVELOPER.md](./DEVELOPER.md) to get started!
