# Amplifier Project Context

This file contains project-specific context and instructions for AI assistants working with Amplifier.

**CRITICAL**: This file appears at every turn of your conversation to keep you anchored as context floods with other ideas. Scan it frequently to stay aligned.

---

## 🎯 Quick Mental Model (Read This First!)

### The 30-Second Version

**Amplifier = Linux Kernel Model for AI Agents**

```
┌─────────────────────────────────────────────────────────────┐
│  amplifier-core (KERNEL)                                     │
│  • Tiny, stable, boring                                      │
│  • Mechanisms ONLY (loading, coordinating, events)           │
│  • NEVER decides policy (which model, how to orchestrate)    │
│  • Changes rarely, backward compatible always                │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │ stable contracts ("studs")
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  MODULES (USERSPACE)                                         │
│  • Providers: LLM backends (Anthropic, OpenAI, Azure, Ollama)│
│  • Tools: Capabilities (filesystem, bash, web, search, task) │
│  • Orchestrators: Execution loops (basic, streaming, events) │
│  • Contexts: Memory (simple, persistent)                     │
│  • Hooks: Observability (logging, redaction, approval)       │
│  • Agents: Config overlays for sub-session delegation        │
│                                                               │
│  Can be swapped, regenerated, evolved independently          │
└─────────────────────────────────────────────────────────────┘
```

**Key Principle**: "The center stays still so the edges can move fast."

---

## 💎 CRITICAL: Respect User Time - Test Before Presenting

**The user's time is their most valuable resource.** When you present work as "ready" or "done", you must have:

1. **Tested it yourself thoroughly** - Don't make the user your QA
2. **Fixed obvious issues** - Syntax errors, import problems, broken logic
3. **Verified it actually works** - Run tests, check structure, validate logic
4. **Only then present it** - "This is ready for your review" means YOU'VE already validated it

**User's role:** Strategic decisions, design approval, business context, stakeholder judgment
**Your role:** Implementation, testing, debugging, fixing issues before engaging user

**Anti-pattern**: "I've implemented X, can you test it and let me know if it works?"
**Correct pattern**: "I've implemented and tested X. Tests pass, structure verified, logic validated. Ready for your review. Here is how you can verify."

**Remember**: Every time you ask the user to debug something you could have caught, you're wasting their time on non-stakeholder work. Be thorough BEFORE engaging them.

---

## Git Commit Message Guidelines

When creating git commit messages, always insert the following at the end of your commit message:

```
🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
```

---

## ⚠️ CRITICAL: Your Responsibility to Keep This File Current

**YOU ARE READING THIS FILE RIGHT NOW. IF YOU MAKE CHANGES TO THE SYSTEM, YOU MUST UPDATE THIS FILE.**

### Why This Matters

This AGENTS.md file is the **anchor point** that appears at every turn of every AI conversation. When you make changes to:

- Architecture or design patterns
- Core philosophies or principles
- Module types or contracts
- Decision-making frameworks
- Event taxonomy or observability patterns
- Key workflows or processes

**You are creating a time bomb for future AI assistants (including yourself in the next conversation).** If this file becomes stale:

1. **Context Poisoning**: Future assistants will be guided by outdated information
2. **Inconsistent Decisions**: They'll make choices based on old patterns that no longer exist
3. **Wasted Effort**: They'll reinvent wheels or undo good work because they didn't know about it
4. **Philosophy Drift**: The core principles will slowly diverge from reality

### When to Update This File

Update AGENTS.md immediately after making these kinds of changes:

| Change Type                | What to Update in AGENTS.md               |
| -------------------------- | ----------------------------------------- |
| **New module type**        | Add to Module Types Reference table       |
| **Changed contract**       | Update Contract column in tables          |
| **New decision framework** | Add to Decision-Making Frameworks section |
| **Philosophy evolution**   | Update Core Philosophy Principles section |
| **New event pattern**      | Add to Canonical Event Taxonomy           |
| **Architecture change**    | Update diagrams and System Flow           |
| **New best practice**      | Add to relevant framework or principle    |
| **Deprecated pattern**     | Remove or mark as obsolete                |

### How to Update

1. **Make your code/doc changes first** (docs first, then code per philosophy)
2. **Before marking task complete**: Review AGENTS.md for outdated info
3. **Update AGENTS.md** to reflect the new reality "as if it always was this way"
4. **Test it**: Ask yourself "If I read this in a fresh conversation, would it guide me correctly?"

### Examples

**Bad** ❌:

- Add new `hooks-security` module type → Don't update AGENTS.md → Future assistant doesn't know it exists

**Good** ✅:

- Add new `hooks-security` module type → Update Module Types Reference table → Add to Hook examples → Future assistant knows it exists and understands its purpose

**Bad** ❌:

- Change from "providers must return JSON" to "providers must return ContentBlocks" → Don't update Provider contract → Future assistant implements wrong interface

**Good** ✅:

- Change provider contract → Update Module Types Reference → Update philosophy if relevant → Future assistant implements correct interface

### Remember

**You are not just coding for now. You are documenting the path for all future AI assistants who will work on this system.**

This file is their map. Don't let the map drift from the territory.

---

### The 3-Minute Version

**1. Think "Bricks & Studs" (LEGO Model)**

- Each module = self-contained "brick" with functionality
- Interfaces = "studs" where bricks connect (stable contracts)
- Regenerate any brick independently without breaking the system
- **Prefer regeneration over editing** - rewrite module from spec, not line edits

**2. Kernel vs. Module Decision Framework**

```
┌─────────────────────────────────────────────────────────────┐
│ "Could two teams want different behavior here?"              │
│                                                               │
│  YES → MODULE (policy at edges)                              │
│  NO  → Maybe kernel (but prove with ≥2 modules first)        │
└─────────────────────────────────────────────────────────────┘
```

**3. Mount Plans = Configuration Contract**

- App layer creates **Mount Plan** (which modules to load, how to configure)
- Kernel validates and loads modules
- Pure mechanism - kernel NEVER decides which modules to use

**4. Event-First Observability**

- Everything important = canonical event (`session:start`, `provider:request`, `tool:execute`, etc.)
- Single JSONL log = source of truth
- Redaction happens BEFORE logging
- Tracing IDs everywhere (session_id, request_id, span_id)

**5. Documentation = Spec, Code = Implementation**

- Docs describe target state "as if it always worked this way"
- Code implements what docs describe
- Major changes: update ALL docs first → get approval → then code
- Prevents "context poisoning" for AI tools

---

## 📚 Essential Reading

Read these files for deep understanding:

- @docs/context/KERNEL_PHILOSOPHY.md - Why the kernel is tiny and boring
- @docs/context/MODULAR_DESIGN_PHILOSOPHY.md - Bricks & studs model
- @docs/context/IMPLEMENTATION_PHILOSOPHY.md - Ruthless simplicity
- @docs/AMPLIFIER_AS_LINUX_KERNEL.md - Linux kernel metaphor as decision tool
- @docs/AMPLIFIER_CONTEXT_GUIDE.md - Complete contributor guide
- @docs/COLLECTIONS_GUIDE.md - Collections system for sharing expertise
- @docs/README.md - Documentation map

For LLM-related work:

- @ai_context/llm-assistant-apis/

---

## 🏗️ Module Types Reference

| Module Type      | Purpose                 | Contract                                                       | Examples                                        | Key Principle                                                      |
| ---------------- | ----------------------- | -------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------ |
| **Provider**     | LLM backends            | `ChatRequest → ChatResponse`                                   | anthropic, openai, azure, ollama, mock          | Preserve all content types (text, tool calls, thinking, reasoning) |
| **Tool**         | Agent capabilities      | `execute(input) → ToolResult`                                  | filesystem, bash, web, search, task             | Non-interference - failures can't crash kernel                     |
| **Orchestrator** | Execution strategy      | `execute(prompt, context, providers, tools, hooks) → response` | basic, streaming, events                        | Pure policy - swap to change behavior                              |
| **Context**      | Memory management       | `add/get/compact messages`                                     | simple (in-memory), persistent (file)           | Deterministic compaction with events                               |
| **Hook**         | Observability & control | `__call__(event, data) → HookResult`                           | logging, backup, redaction, approval, scheduler | Non-blocking - never delay primary flow                            |
| **Agent**        | Config overlay          | Partial mount plan                                             | User-defined personas                           | Sub-session delegation with isolated context                       |

---

## 🎲 Core Architecture

### The Linux Kernel Analogy

| Linux Concept    | Amplifier Analog                 | What This Means                                         |
| ---------------- | -------------------------------- | ------------------------------------------------------- |
| Ring 0 kernel    | `amplifier-core`                 | Export mechanisms, never policy. Tiny & boring.         |
| Syscalls         | Kernel operations                | `create_session()`, `mount()`, `emit()` - few and sharp |
| Loadable drivers | Modules (providers, tools, etc.) | Compete at edges; comply with protocols                 |
| VFS mount points | Module mount points              | Each module = device at a stable path                   |
| Signals/Netlink  | Event bus / hooks                | Kernel emits lifecycle events; hooks observe            |
| /proc & dmesg    | Unified JSONL log                | One canonical structured stream                         |
| Capabilities/LSM | Approval & capability checks     | Deny-by-default, least privilege                        |
| Scheduler        | Orchestrator modules             | Swap strategies by replacing orchestrator               |
| VM/Memory        | Context manager                  | Deterministic compaction with events                    |

**Practical Use**: When design is unclear, ask "What would Linux do?"

- Scheduling? → Orchestrator module (userspace)
- Provider selection? → App layer policy
- Tool behavior? → Tool module
- Security policy? → Hook module

### System Flow

```
┌─────────────┐
│   App/CLI   │ Resolves config → Creates Mount Plan
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  amplifier-core (Kernel)                                │
│  • Validates Mount Plan                                 │
│  • Loads modules via entry points or filesystem         │
│  • Creates Session with Coordinator                     │
│  • Emits lifecycle events                               │
└──────┬──────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│  Session Execution                                      │
│  Orchestrator.execute(prompt, context, providers, tools)│
│    → Provider.complete(messages)                        │
│    → Tool.execute(input)                                │
│    → Context.add/get/compact                            │
│    → Hooks observe all events                           │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Decision-Making Frameworks

### Framework 1: Is This Kernel Work?

```
┌─────────────────────────────────────────────────────────┐
│ Does it implement a MECHANISM many policies could use?  │
│   YES → Might be kernel (but need ≥2 implementations)   │
│   NO  → Definitely module                               │
│                                                          │
│ Does it select, optimize, format, route, plan?          │
│   YES → Module (that's policy)                          │
│   NO  → Might be kernel                                 │
│                                                          │
│ Could it be swapped without rewriting kernel?           │
│   YES → Module                                          │
│   NO  → Maybe kernel                                    │
└─────────────────────────────────────────────────────────┘
```

### Framework 2: Simplicity Questions

When facing implementation decisions:

1. **Necessity**: "Do we actually need this right now?"
2. **Simplicity**: "What's the simplest way to solve this?"
3. **Directness**: "Can we solve this more directly?"
4. **Value**: "Does the complexity add proportional value?"
5. **Maintenance**: "How easy will this be to understand later?"

### Framework 3: Two-Implementation Rule

- Don't add to kernel until **≥2 independent modules** converge on the need
- Prototype at edges first
- Extract to kernel only after proven convergence

### Framework 4: Event-First Decision

- If it's important → emit a canonical event
- If it's not observable → it didn't happen
- Hooks can observe without blocking
- Single JSONL log = source of truth

---

## 🎨 Core Philosophy Principles

### Ruthless Simplicity

- **KISS taken to heart**: As simple as possible, but no simpler
- **Minimize abstractions**: Every layer must justify its existence
- **Start minimal, grow as needed**: Begin with simplest implementation
- **Avoid future-proofing**: Don't build for hypothetical requirements
- **Question everything**: Regularly challenge complexity
- **YAGNI(A) - You Aren't Gonna Need It (Again)**: Aggressively delete stale content, not just avoid creating it. Old docs, deprecated code, "might be useful" references - if it's not actively valuable NOW, delete it. Stale content creates context poisoning.

### Modular Design ("Bricks & Studs")

- **Stable interfaces** ("studs"): Allow independent regeneration
- **Self-contained modules** ("bricks"): Clear responsibilities
- **Regenerate, don't edit**: Rewrite entire module from spec
- **Build in parallel**: Multiple variants simultaneously
- **AI as builder, human as architect**: Specify, don't implement

### Kernel Philosophy

- **Mechanism, not policy**: Kernel provides capabilities, not decisions
- **Small, stable, boring**: Changes rarely, maintains backward compat
- **Don't break modules**: Backward compatibility is sacred
- **Policy at edges**: All decisions in modules
- **Text-first**: Human-readable, diffable, inspectable

### Implementation Philosophy

- **80/20 principle**: One working feature > multiple partial features
- **Vertical slices**: Complete end-to-end paths first
- **Fail fast and visibly**: Meaningful errors, never silent failures
- **Direct approach**: Avoid unnecessary abstractions
- **Test behavior, not implementation**: Integration > unit tests

---

## 📋 Mount Plans: The Configuration Contract

**What**: Dictionary specifying modules to load and their configuration

**Structure**:

```python
{
    "session": {
        "orchestrator": "loop-streaming",  # Required
        "context": "context-persistent"    # Required
    },
    "providers": [
        {"module": "provider-anthropic", "config": {...}}
    ],
    "tools": [
        {"module": "tool-filesystem", "config": {...}}
    ],
    "hooks": [
        {"module": "hooks-logging", "config": {...}}
    ],
    "agents": {
        "agent-name": {...}  # Config overlays, NOT modules to load now
    }
}
```

**Key Points**:

- App layer creates Mount Plan (merges profiles, config files, CLI flags)
- Kernel validates and loads specified modules
- Pure mechanism - kernel never decides WHICH modules
- Agent configs are for future sub-session delegation, not immediate loading

See: `docs/specs/kernel/MOUNT_PLAN_SPECIFICATION.md`

---

## 📡 Canonical Event Taxonomy

Emit these event names consistently:

| Event Pattern                      | When                | Data Includes             |
| ---------------------------------- | ------------------- | ------------------------- |
| `session:start/end`                | Session lifecycle   | session_id, mount plan    |
| `prompt:submit/complete`           | User interaction    | prompt, response          |
| `plan:start/end`                   | Planning phase      | plan details              |
| `provider:request/response/error`  | LLM calls           | messages, tokens, usage   |
| `tool:pre/post/error`              | Tool execution      | tool name, input, result  |
| `context:pre_compact/post_compact` | Memory compaction   | before/after token counts |
| `artifact:write/read`              | File operations     | file path, content hash   |
| `policy:violation`                 | Security/capability | what was attempted        |
| `approval:required/granted/denied` | User approvals      | action, decision          |

**Observability Schema** (JSONL):

```json
{
  "ts": "ISO8601",
  "lvl": "info|warn|error",
  "schema": {"name": "amplifier.log", "ver": "1.0.0"},
  "session_id": "uuid",
  "request_id": "uuid?",
  "span_id": "uuid?",
  "event": "provider:request",
  "component": "orchestrator",
  "module": "provider-anthropic?",
  "status": "success|error?",
  "duration_ms": 123,
  "data": {...},
  "error": {...}
}
```

---

## 🏗️ Project Structure

## Development Guidelines

1. Every module is independently installable
2. Use entry points for module discovery
3. Follow the Tool/Provider/Context interfaces
4. Test modules in isolation before integration
5. Document module contracts in README.md

### Standard Workflow for Major Development

For significant features or system changes, follow this documentation-first process:

1. **Planning**: Reconnaissance → informed proposal → iterate with user on decisions needed → approved plan
2. **Documentation First**: Update ALL docs to target state ("as if it always worked this way") → scrub old references (context poison) → iterate until approved → implementation notes go in `ai_working/` only
3. **Implementation**: Code matches documentation (docs drive code) → update docs if unexpected changes needed → halt for risky decisions
4. **Test as User**: Use actual CLI/tools, verify outputs/logs match expectations → return to earlier phases if issues found
5. **Report & Cleanup**: Summary of work, verification steps for user, clean up temporary files, update task tracking → do not commit unless directed

This prevents context drift and ensures documentation remains the living specification.

### Documentation-First Retcon Technique

The non-code files for this codebase and any of its submodules is to also serve as the source of truth that is the contract the code must fulfill and align to, to support the @ai_context/@MODULAR_DESIGN_PHILOSOPHY.md approach.

In addition, AI tooling counts on these files as a key piece of its context and any conflicts or inconsistencies across the corpus is considered "context poisoning", in that it is possible the AI tooling may load stale content that misleads it into the wrong design or implementation choices and cause it to increase the divergence. For this reason, it is CRITICAL to consistently keep all non-coding files clean, up-to-date, and consistent to drive down any potential context poisoning. This is important enough that it even warrants breaking traditional best practices such as immutable ADRs in favor of "rewriting as if it were always this way" or deleting/scrubbing what is no longer relevant. Same with non-critial backwards compatability, migration, or change tracking.

For major architectural changes where documentation needs to reflect the new reality:

**Process:**

1. **Create documentation index**: Generate list of all non-code, non-git-ignored files to process
2. **Sequential processing**: Use grep-based checklist to process one file at a time
3. **Retcon updates**: Update each file to reflect future state as if it's already implemented
   - No "this will change to X" - write as if X is reality
   - No migration paths or backwards compatibility notes
   - No cruft about how things used to work
   - Just clean, current documentation of how it works
4. **Mark complete**: Update index and move to next file
5. **Report readiness**: When all docs updated, report to user for review
6. **Implement code**: After approval, treat documentation as ground truth and update code to match

**Key principle**: Documentation IS the spec. Code implements what documentation describes.

**Benefits:**

- Documentation stays authoritative (no drift between docs and code)
- Clean state (no historical baggage or migration notes)
- Clear scope (docs define exactly what needs to be implemented)
- Reviewable (user can approve design before implementation)

**Example workflow:**

```bash
# 1. Generate file index
find amplifier-dev -type f \
  \( -name "*.md" -o -name "*.yaml" -o -name "*.toml" \) \
  ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" \
  > /tmp/docs_to_update.txt

# 2. Process each file
NEXT=$(head -1 /tmp/docs_to_update.txt)
# Read, update, save
sed -i '1d' /tmp/docs_to_update.txt  # Remove processed file

# 3. Repeat until empty
# 4. Report readiness
# 5. Await approval
# 6. Implement code to match docs
```

### App-Layer Utilities: The Toolkit Exemplar

**Toolkit as Philosophy Exemplar** (@amplifier-app-cli/toolkit/):

The toolkit teaches building sophisticated AI tools using **metacognitive recipes** - multi-config patterns where code orchestrates thinking and specialized AI configs handle cognitive subtasks.

**What toolkit provides** (CORRECT):

- Structural utilities: `discover_files`, `ProgressReporter`, validation helpers
- Templates showing multi-config metacognitive recipe pattern
- `tutorial_analyzer` exemplar: 6 specialized configs, multi-stage orchestration

**What toolkit does NOT provide** (ANTI-PATTERNS):

- ❌ Session wrappers around `AmplifierSession` (use kernel directly!)
- ❌ Generic state management frameworks (each tool owns its state)
- ❌ LLM response parsing utilities (amplifier-core handles this)
- ❌ Single-config patterns (sophisticated tools need multiple configs!)

**The correct pattern** (multi-config metacognitive recipe):

```python
from amplifier_core import AmplifierSession
from amplifier_app_cli.toolkit import discover_files, ProgressReporter

# Multiple specialized configs (not one!)
ANALYZER_CONFIG = {
    "session": {"orchestrator": "loop-basic"},
    "providers": [{
        "module": "provider-anthropic",
        "source": "git+https://github.com/microsoft/amplifier-module-provider-anthropic@main",
        "config": {"model": "claude-sonnet-4-5", "temperature": 0.3}  # Analytical
    }],
}

SYNTHESIZER_CONFIG = {
    "session": {"orchestrator": "loop-streaming"},
    "providers": [{
        "module": "provider-anthropic",
        "source": "git+https://github.com/microsoft/amplifier-module-provider-anthropic@main",
        "config": {"model": "claude-opus-4-1", "temperature": 0.7}  # Creative
    }],
}

# Code orchestrates thinking across multiple configs
async def analyze_documents(root: Path):
    files = discover_files(root, "**/*.md")  # Toolkit utility
    progress = ProgressReporter(len(files), "Processing")  # Toolkit utility

    # Stage 1: Analytical config
    async with AmplifierSession(config=ANALYZER_CONFIG) as session:
        extractions = []
        for file in files:
            extraction = await session.execute(f"Extract: {file.read_text()}")
            extractions.append(extraction)
            progress.update()

    # Stage 2: Creative config
    async with AmplifierSession(config=SYNTHESIZER_CONFIG) as session:
        synthesis = await session.execute(f"Synthesize: {extractions}")

    return synthesis
```

**Key lessons**:

- **Multi-config pattern**: Each cognitive subtask (analytical, creative, evaluative) gets its own optimized config
- **Code orchestrates**: Decides which config when, manages state, controls flow
- **Structural utilities**: Toolkit provides file/progress/validation helpers, not AI wrappers
- **Use kernel directly**: AmplifierSession with specialized configs, no wrappers

See @docs/TOOLKIT_GUIDE.md and `toolkit/examples/tutorial_analyzer/` for complete guidance.

### Testing Philosophy

**Tests should catch real bugs, not duplicate code inspection**:

- ✅ **Write tests for**: Runtime invariants, edge cases, integration behavior, convention enforcement
- ❌ **Don't test**: Things obvious from reading code (e.g., "does constant FOO exist?", "does FOO equal 'foo'?")

**Examples**:

- Good: Test that ALL_EVENTS has no duplicates (catches copy-paste errors)
- Good: Test that all events follow namespace:action convention (catches typos)
- Bad: Test that SESSION_START constant exists (just read the code)
- Bad: Test that SESSION_START equals "session:start" (redundant with code)

**Principle**: If code inspection is faster than maintaining a test, skip the test.

### Efficient Batch Processing Pattern

When processing large numbers of files (e.g., updating 100+ documentation files), use the grep-based checklist pattern to avoid token waste:

**Pattern:**

```bash
# 1. Generate checklist in file
cat > /tmp/files_to_process.txt << 'EOF'
[ ] file1.md
[ ] file2.md
[ ] file3.md
...
[ ] file100.md
EOF

# 2. In your processing loop:
# Get next uncompleted item (cheap - doesn't read whole file)
NEXT_FILE=$(grep -m1 "^\[ \]" /tmp/files_to_process.txt | sed 's/\[ \] //')

# Process the file
# ... do work ...

# Mark complete (cheap - in-place edit)
sed -i "s/\[ \] $NEXT_FILE/[x] $NEXT_FILE/" /tmp/files_to_process.txt

# Repeat until done
```

**Benefits:**

- Saves massive tokens on large batches (100 files = 5 tokens per iteration vs 1000s)
- Clear progress tracking
- Resumable if interrupted
- No risk of forgetting files

**Use when:**

- Processing 10+ files systematically
- Each file requires similar updates
- Need clear progress visibility
- Want to avoid context drift

### Code Cleanliness

**No meta-commentary in production code**:

- Don't add "added on DATE" comments
- Don't add "vNext" or feature names
- Changelog entries go in CHANGELOG.md, not inline comments
- Code should be clean and self-documenting

### Required Sections in All Submodule/Repo README Files

**CRITICAL:** Every submodule and repo-root README.md must include:

1. **Contributing section** - Standard Microsoft CLA notice
2. **Trademarks section** - Microsoft trademark guidelines

**Template**: copy from `amplifier-dev/README.md`

**When updating README files:** Always verify these sections are present and current.

## Configuration (optional, defined by opinionated app layer)

**Use the profile-based configuration system:**

```bash
# Set your preferred profile
amplifier profile use dev

# Run Amplifier with applied profile
amplifier run --mode chat

# List available profiles
amplifier profile list
```

Profiles available: `foundation`, `base`, `dev`, `production`, `test`, `full`

See [docs/USER_ONBOARDING.md#quick-reference](docs/USER_ONBOARDING.md#quick-reference) for complete configuration documentation.

## Testing

### User-Level Verification (Run After Changes)

**CRITICAL**: Run verification tests after any changes to CLI, libraries, or toolkit:

```bash
# Quick verification (~6 seconds)
cd dev_verification
SKIP_GITHUB_TEST=1 ./run_all_tests.sh

# Full verification before releasing (~3 minutes)
./run_all_tests.sh
```

**What gets tested:**
- All CLI commands work (profile, session, provider, module, collection, source)
- All toolkit utilities work (file ops, progress, validation)
- All libraries install from GitHub
- Documentation examples are executable
- Dead code prevention (deprecated commands removed)

**When to run:**
- ✅ After changes to amplifier-app-cli code
- ✅ After changes to amplifier-profiles, amplifier-config, amplifier-collections, amplifier-module-resolution
- ✅ After toolkit changes
- ✅ Before committing documentation updates
- ✅ Before creating pull requests
- ✅ Before releases

See [dev_verification/README.md](dev_verification/README.md) for details.

### Interactive Testing

Run interactive sessions with specific profiles:

```bash
# Use the full-featured profile
amplifier run --profile full --mode chat
```

Test specific features:

- `/think` - Enable read-only plan mode
- `/tools` - List available tools
- `/status` - Show session information

## Dependency Management

**IMPORTANT**: This project uses `uv` for all Python dependency management.

### Installing UV

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Key Commands

**For single module development:**

```bash
cd amplifier-core
uv pip install -e .        # Install in editable mode
uv sync --dev              # Install with dev dependencies
```

**Adding dependencies:**

```bash
uv add package-name        # Add runtime dependency
uv add --dev pytest        # Add dev dependency
uv lock --upgrade          # Update all dependencies
```

**For cross-module development:**

```bash
# Install module A with editable link to module B
cd amplifier-core
uv pip install -e ../amplifier-module-provider-anthropic
```

**Running tests:**

```bash
uv run pytest              # Run tests with dependencies
```

### Important Guidelines

- **NEVER manually edit `pyproject.toml` dependencies** - always use `uv add`
- To add dependencies: `cd` to the specific project directory and run `uv add <package>`
- This ensures proper dependency resolution and updates both `pyproject.toml` and `uv.lock`
- Each module manages its own dependencies independently
- Lock files (`uv.lock`) are committed for reproducible builds
- No workspace configuration - modules remain independent
- Use `uv pip install -e .` (not `pip install -e .`) for development installs

### Dependency Architecture: Two-Tier System

Amplifier uses a clear separation between build-time and runtime dependencies to enable GitHub installation without PyPI publication.

#### Tier 1: Core Packages (Build-Time)

Core packages (`amplifier-core`, `amplifier-app-cli`, `amplifier`) are installed via `uv tool install` and use **git URLs** in `[tool.uv.sources]`:

```toml
# amplifier-app-cli/pyproject.toml
[project]
dependencies = ["amplifier-core", "click>=8.1.0", ...]

[tool.uv.sources]
amplifier-core = { git = "https://github.com/microsoft/amplifier-core", branch = "main" }
```

**Why git URLs?** They work for both local development and GitHub installation:

```bash
# ✅ Works with git URLs
uv tool install git+https://github.com/microsoft/amplifier@next
uvx --from git+https://github.com/microsoft/amplifier@next amplifier run --profile dev "test"
```

**Avoid path dependencies** in core packages - they break GitHub installation:

```toml
# ❌ Breaks GitHub install
[tool.uv.sources]
amplifier-core = { path = "../amplifier-core", editable = true }
```

#### Tier 2: Module Packages (Runtime)

Module packages (providers, tools, hooks, orchestrators, context) follow the **peer dependency pattern**:

- **No amplifier-core dependency** in their `pyproject.toml`
- Loaded dynamically at runtime from git URLs
- Discovered via entry points: `[project.entry-points."amplifier.modules"]`

**Module sources specified in profiles:**

```yaml
# profiles/foundation.md
providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
    config:
      default_model: claude-sonnet-4-5
```

**Critical**: Every module in a profile **MUST include `source:`** git URL. Missing sources cause runtime failures:

```yaml
# ❌ WRONG - Missing source (module won't load)
providers:
  - module: provider-anthropic
    config:
      debug: true

# ✅ CORRECT - Include source
providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
    config:
      debug: true
```

**Profile inheritance gotcha**: When extending profiles and overriding sections, inherited sources are lost:

```yaml
# base.md has provider with source
providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main

# dev.md extends base
extends: base

# ❌ WRONG - Override without source loses base's source
providers:
  - module: provider-anthropic
    config:
      debug: true  # Module fails to load!

# ✅ CORRECT - Include source when overriding
providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
    config:
      debug: true
```

#### Benefits

- **No PyPI needed**: Git URLs eliminate publishing requirement
- **Consistent everywhere**: Same approach for local dev and production
- **Modular loading**: Runtime loading enables on-demand module installation
- **Independent repos**: Each module evolves independently with own versioning

## Task Workflow, Memory, and Context Management

We track work in Beads instead of Markdown. Run `bd quickstart` to see how, along with local notes in @.beads/README.md.

### Beads Workflow for AI Assistants

**SINGLE SOURCE OF TRUTH**: The ONLY beads directory for this repository is `.beads/` at the amplifier-dev root.

- **Correct location**: `amplifier-dev/.beads/` (relative to repo root)
- **Database file**: `.beads/amplifier-dev.db` (gitignored)
- **JSONL export**: `.beads/amplifier-dev.jsonl` (tracked in git)
- **DO NOT create**: beads directories in submodules (amplifier-app-cli, modules, etc.)
- **DO NOT create**: `bd-issues/` or other alternative tracking directories

**All beads commands run from amplifier-dev root** with explicit database flag.

**CRITICAL**: When making changes to beads tracking, ALWAYS use the project database with explicit flags:

1. **ALWAYS specify the database explicitly**:

   ```bash
   bd --db .beads/amplifier-dev.db <command>
   ```

2. **After ANY beads change** (create, update, close, dep changes):

   ```bash
   # Example: Create an issue
   bd --db .beads/amplifier-dev.db create "Issue title" --type task --priority 1

   # IMMEDIATELY export to JSONL
   bd --db .beads/amplifier-dev.db export -o .beads/amplifier-dev.jsonl
   ```

3. **Why explicit flags matter**:

   - Without `--db`, bd uses `~/.beads/default.db` (WRONG - personal database)
   - Without `-o`, export may go to wrong location
   - Project issues MUST go in `.beads/amplifier-dev.db` → `.beads/amplifier-dev.jsonl`
   - The `.db` file is gitignored, only `.jsonl` is tracked

4. **If project DB doesn't exist yet**:

   ```bash
   # Import JSONL to create DB
   bd --db .beads/amplifier-dev.db import .beads/amplifier-dev.jsonl
   ```

5. **When user is done with beads work**:
   - If user was directly working with beads (`bd create`, `bd list`, etc.)
   - And conversation seems to be moving on to other work
   - Ask: "Would you like me to commit these beads changes before we continue?"

**Complete workflow example:**

```bash
# User: "Create a task for fixing the auth bug"

# 1. Create with explicit DB flag
bd --db .beads/amplifier-dev.db create "Fix authentication timeout bug" \
  --type bug --priority 1

# 2. Export to JSONL immediately with explicit output
bd --db .beads/amplifier-dev.db export -o .beads/amplifier-dev.jsonl

# 3. If user seems done, ask about committing:
# "Would you like me to commit these beads changes now?"
```

**Never skip the export step** - it's how beads changes get saved to disk for git tracking.

**Common mistake**: Running `bd create` without `--db` flag creates issues in your personal `~/.beads/default.db` instead of the project database. Always verify with `grep` that your changes are in `.beads/amplifier-dev.jsonl`.

## Sub-Session Delegation

When delegating tasks via the task tool, sub-sessions inherit configuration from the parent but have isolated conversation context.

### Configuration Inheritance

Sub-sessions inherit from parent:

- Orchestrator (execution loop)
- Context manager (memory strategy)
- Hooks (logging, security, UI)
- Providers (baseline)
- Tools (baseline)
- Session configuration (token limits, etc.)

Sub-sessions override via agent configuration:

- Providers (different model)
- Tools (subset for focus or different tools)
- Orchestrator (custom execution loop if needed)
- Hooks (different observability policies if needed)
- Context (different memory strategy if needed)

### Context Isolation

Sub-sessions start with clean conversation context:

- No access to parent's conversation history
- Only the agent's system instruction + task instruction
- Enables focused task execution without noise

Multi-turn engagement is supported - parent can resume the same sub-session for iterative collaboration by specifying the sub-session ID.

See `docs/AGENT_DELEGATION.md` for complete specification.
