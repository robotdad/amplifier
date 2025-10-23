# Scenario Migration Guide: Legacy to Amplifier-Dev

> **Purpose:** Migrate an existing scenario/app from legacy Amplifier to new amplifier-dev architecture
> **Audience:** Anyone migrating scenarios in a fresh session
> **Status:** Living document - add lessons learned after each migration

---

## Prerequisites: Study These First

Before migrating, understand the target architecture:

### Core Philosophy (30 minutes)
- `@amplifier-dev/docs/context/KERNEL_PHILOSOPHY.md` - Mechanism vs policy, tiny kernel
- `@amplifier-dev/docs/context/IMPLEMENTATION_PHILOSOPHY.md` - Ruthless simplicity
- `@amplifier-dev/docs/context/MODULAR_DESIGN_PHILOSOPHY.md` - Bricks and studs

### Architecture (20 minutes)
- `@amplifier-dev/docs/AMPLIFIER_AS_LINUX_KERNEL.md` - Linux kernel metaphor
- `@amplifier-dev/AMPLIFIER_CONTEXT_GUIDE.md` - Quick reference

### Module Development (15 minutes)
- `@amplifier-dev/MODULE_DEVELOPMENT_LESSONS.md` - Practical lessons from building modules
  - **Critical:** Lines 70-88 on git sources vs path dependencies
  - Lines 135-174 on capability registry pattern
  - Lines 177-192 on path handling

**Total study time:** ~1 hour to ground yourself in the new world

---

## Migration Process

### Step 0: Analyze the Existing Scenario

**Understand what you're migrating:**

1. **What problem does it solve?** (from README)
2. **What's the thinking process?** (the "metacognitive recipe" from HOW_TO_CREATE_YOUR_OWN.md if it exists)
3. **What stages/components exist?** (code structure)
4. **What dependencies does it have?** (imports, external libraries)
5. **What reusable patterns exist?** (state management, multi-stage pipeline)

**Document your findings:**
```
Problem: [What user need does this solve?]
Recipe: [The thinking process - step 1, step 2, etc.]
Stages: [List the components/stages]
Dependencies: [Old amplifier imports, external libs]
Patterns: [State management? Resume/interrupt? Multi-stage?]
```

---

### Step 1: Create New Repository

**Repository naming convention:**
```
amplifier-app-{purpose}
# Examples:
amplifier-app-blog-writer
amplifier-app-transcribe
amplifier-app-knowledge-synthesizer
```

**Initialize structure:**
```bash
mkdir amplifier-app-{name}
cd amplifier-app-{name}
git init

# Create basic structure
mkdir -p src/{app_name}
mkdir -p .amplifier/profiles
touch pyproject.toml
touch README.md
touch HOW_THIS_APP_WAS_MADE.md  # Recipe/thinking process doc
```

---

### Step 2: Setup Dependencies with Git Sources

**Critical pattern for shareable apps:**

Path dependencies only work within a specific directory structure.
Git sources work anywhere and enable frictionless sharing.

**Create `pyproject.toml`:**
```toml
[project]
name = "amplifier-app-{name}"
version = "0.1.0"
description = "{What this app does}"
dependencies = [
    "amplifier-core",
    # Add specific modules you need:
    # "amplifier-module-providers-anthropic",
    # "amplifier-app-cli",  # If building CLI
]

[tool.uv.sources]
# ✅ Use git sources, NOT path dependencies
amplifier-core = {
    git = "https://github.com/microsoft/amplifier-dev",
    subdirectory = "amplifier-core",
    branch = "main"
}

# Add other modules with same pattern:
# amplifier-module-providers-anthropic = {
#     git = "https://github.com/microsoft/amplifier-dev",
#     subdirectory = "amplifier-module-providers-anthropic",
#     branch = "main"
# }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Why this matters:**
- Anyone can clone your app repo and run it
- No "you must put this next to that" instructions
- Dependencies download automatically
- Works with public or private repos (if user has auth)

---

### Step 3: Map Legacy Imports to New APIs

**Common legacy patterns → new amplifier-dev:**

```python
# Legacy import (old amplifier)
from amplifier.utils.logger import get_logger

# New import (amplifier-dev)
from amplifier_core.logging import get_logger  # Or wherever it actually is

# Pattern: Check amplifier-dev source to find new locations
# 1. Grep for the function/class name
# 2. Check module __init__.py files
# 3. Read module README.md for API docs
```

**Finding new APIs:**
```bash
# In amplifier-dev repo
cd amplifier-dev
grep -r "get_logger" --include="*.py"
# Follow the breadcrumbs to new location
```

**Document the mapping:**
```
Legacy → New
- amplifier.utils.logger → amplifier_core.logging
- amplifier.utils.state → [vendor your own or use module]
- [add mappings as you discover them]
```

---

### Step 4: Identify What to Include in Your App vs Use from Modules

**Decision framework:**

| Pattern | Decision | Rationale |
|---------|----------|-----------|
| **State management for your app** | Include in your app | App-specific, not reusable |
| **LLM retry/defensive patterns** | Check if module exists | Generic, potentially reusable |
| **Domain logic** (blog writing, transcription) | Include in your app | App-specific |
| **Generic utilities** (file I/O, path handling) | Check amplifier-dev | Might be in core/modules |

**Including in your app means copying the code into your project:**
```
src/your_app/
├── main.py           # Your app logic
├── state.py          # App-specific state management (you write this)
└── utils.py          # App-specific utilities (you write this)
```

**Using modules means importing from amplifier-dev:**
```python
# If a module provides what you need
from amplifier_module_workflow_state import StateManager  # If it exists
```

**When in doubt:** Include code in your app first, extract to amplifier-dev module later if pattern emerges across multiple apps.

**Note for advanced users:** If you recognize something that should be a module (generic, reusable across apps), you can build it as a module instead. But this is optional - most migrations should just include everything in the app for simplicity.

---

### Step 5: Handle Path Expansion

**Critical: Python's Path() doesn't expand `~` automatically:**

```python
# ❌ WRONG - Path() doesn't expand ~
Path("~/Source/data")

# ✅ CORRECT - Always expanduser()
Path("~/Source/data").expanduser()

# Apply to all config paths:
data_dir = Path(config.get("data_dir", "~/.data")).expanduser()
```

**Where to apply:**
- Any path from config files
- Any path from CLI arguments
- Any path from environment variables

---

### Step 6: Preserve the Metacognitive Recipe

**This is the soul of the app - don't lose it!**

Create `HOW_THIS_APP_WAS_MADE.md` in your new repo:

```markdown
# How This App Was Made

## The Problem
[What user need does this solve?]

## The Solution: A Metacognitive Recipe

This app embodies a structured thinking process:

1. **Stage 1:** [First, understand X...]
2. **Stage 2:** [Then, do Y based on what you learned...]
3. **Stage 3:** [Check if Z meets criteria...]
4. **Stage 4:** [Refine based on feedback...]

## Why This Recipe Works

[Explain the reasoning behind the stages]

## Code Structure Maps to Recipe

- Stage 1 → `src/stage1.py`
- Stage 2 → `src/stage2.py`
- etc.

## Lessons Learned Building This

[Migration notes]
[What worked well]
[What was tricky]
```

**This document shows:**
- How to think about the problem
- Why this structure makes sense
- How others can adapt the pattern

---

### Step 7: Create Profile for Sharing (if applicable)

**If you want others to use your app via amplifier CLI:**

The power of profiles with `source:` fields is that users can just drop your profile file into their `.amplifier/profiles/` directory and modules download automatically from git.

Create `.amplifier/profiles/{app-name}.md`:

```yaml
---
profile:
  name: {app-name}
  version: "1.0.0"

session:
  orchestrator:
    module: loop-basic
    source: git+https://github.com/microsoft/amplifier-dev@main#subdirectory=amplifier-module-loop-basic
  context:
    module: context-simple

tools:
  - module: tool-bash
  - module: tool-filesystem
  - module: tool-{your-app}
    source: git+https://github.com/you/amplifier-app-{name}@main#subdirectory=src
    config:
      # Your app-specific config

providers:
  - module: provider-anthropic
---

# {App Name} Profile

## What This Profile Does

[Explanation]

## Quick Start

**Installation:**
```bash
# User just copies your profile file to their profiles directory
cp {app-name}.md ~/.amplifier/profiles/

# Modules download automatically when first used
amplifier run --profile {app-name} "task description"
```

## Configuration

[Any config options]
```

**Why this matters:**
- Users don't need to clone your repo
- They just need the profile file
- Modules download automatically via git sources
- Frictionless sharing

**Note:** Most scenario apps will be standalone CLIs, not profile-based.
Profiles are for when you want to leverage amplifier's orchestration.

---

### Step 8: Write Migration README

**Document what you did for future reference:**

**Note:** For migrated apps, `MIGRATION_NOTES.md` serves as your "creation story" - showing how you brought the app into the new amplifier-dev world. It's equivalent to `HOW_I_BUILT_THIS.md` for apps built from scratch.

Create `MIGRATION_NOTES.md` in your new repo:

```markdown
# Migration Notes: Legacy → Amplifier-Dev

## Original Scenario
- Source: [path or description]
- Date migrated: [date]

## Key Changes

### Dependencies
- Changed: [old imports] → [new imports]
- Added: [new modules]
- Removed: [deprecated dependencies]

### Architecture Changes
- [What structural changes you made]

### API Mappings
| Legacy | New |
|--------|-----|
| [old]  | [new] |

## Challenges & Solutions

### Challenge 1: [Description]
**Solution:** [What you did]

### Challenge 2: [Description]
**Solution:** [What you did]

## Testing Verification

- [ ] App installs cleanly via `uv sync`
- [ ] Core functionality works
- [ ] State management works (if applicable)
- [ ] Path handling works with `~` expansion
- [ ] Dependencies resolve via git sources

## Lessons Learned

[What you learned doing this migration]
[Add these back to SCENARIO_MIGRATION_GUIDE.md]
```

---

### Step 9: Verify and Test

**Checklist before considering migration complete:**

```bash
# Clean environment test
rm -rf .venv
uv sync
# Should install all dependencies from git sources

# Run the app
[your run command]

# Test core workflows
[test scenario 1]
[test scenario 2]

# Test path handling
# Try with ~ paths
# Try with relative paths
# Try with absolute paths

# Test state management (if applicable)
# Interrupt and resume
# Check checkpoint files

# Test error handling
# What happens on API failures?
# What happens on bad inputs?
```

---

## Common Patterns & Solutions

### Pattern: Multi-Stage Pipeline

**Legacy approach:**
```python
def run_pipeline():
    result1 = stage1()
    result2 = stage2(result1)
    result3 = stage3(result2)
    return result3
```

**New approach (with state management):**
```python
class Pipeline:
    def __init__(self, state_manager):
        self.state = state_manager

    async def run(self):
        stage = self.state.current_stage

        if stage == "initialized":
            await self.stage1()
            self.state.advance("stage1_complete")

        if stage == "stage1_complete":
            await self.stage2()
            self.state.advance("stage2_complete")

        # etc.
```

### Pattern: Retry & Defensive LLM Calls

**Check if amplifier-dev has utilities:**
```bash
grep -r "retry" amplifier-dev/ --include="*.py"
# Look for retry decorators or utilities
```

**If not, vendor your own:**
```python
async def retry_llm_call(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### Pattern: File I/O with Progress

**Keep user-facing progress logging:**
```python
from amplifier_core.logging import get_logger
logger = get_logger(__name__)

def process_files(files):
    logger.info(f"Processing {len(files)} files...")
    for i, file in enumerate(files):
        logger.info(f"  [{i+1}/{len(files)}] {file.name}")
        # process
```

---

## Git Sources Deep Dive

**Why git sources matter:**

**Without git sources:**
```toml
[tool.uv.sources]
amplifier-core = { path = "../../amplifier-dev/amplifier-core" }
```
**Problem:** Only works if:
- You clone amplifier-dev
- You clone this app
- You put them in specific relative positions
- Everyone who uses your app must do the same

**With git sources:**
```toml
[tool.uv.sources]
amplifier-core = {
    git = "https://github.com/microsoft/amplifier-dev",
    subdirectory = "amplifier-core"
}
```
**Benefit:**
- User clones your app repo
- Runs `uv sync`
- Dependencies download automatically from git
- Works anywhere, no directory coordination

**For private repos:**
- User needs GitHub auth (`gh auth login`)
- Still works fine, just requires auth
- Enables sharing without making repos public

---

## Lessons Learned Section

> **Note:** After each migration, add lessons here. This section grows over time.

### Migration 1: Blog Creator (blog_writer + article_illustrator) - 2025-10-22

**What worked:**
- Agent consultation (zen-architect, api-contract-designer, integration-specialist) validated design before implementation
- DDD process caught microsoft vs robotdad distinction early
- File crawling pattern for systematic documentation creation
- Git sources enable frictionless module sharing
- Capability registry pattern allows module cooperation without tight coupling

**What was tricky:**
- TOML syntax: Inline tables can't have newlines, use table format `[tool.uv.sources.module]`
- Understanding microsoft repos (can't modify) vs robotdad repos (we create)
- Deciding unified app vs separate tools (workflow dependency was key signal)
- Module boundary decisions (3 modules vs pushing to core vs keeping in app)

**API mappings discovered:**
- No API changes needed - amplifier utilities unchanged from scenarios/
- `from amplifier.utils.logger import get_logger` - stays same
- `from amplifier.ccsdk_toolkit import ClaudeSession` - stays same
- New imports: Module-specific (e.g., `from amplifier_module_style_extraction import StyleExtractor`)

**Key Patterns Established:**
- **3-module extraction**: When consolidating multiple tools, look for reusable components
- **Unified workflow**: Sequential workflow dependencies suggest unified app design
- **Git source format**: `git+https://github.com/org/repo@branch#subdirectory=path`
- **Profile structure**: Markdown with YAML frontmatter, source fields for all robotdad modules

**Lessons for Future Migrations:**
1. Consult agents before designing - saves rework
2. Use DDD for major migrations - documentation-first prevents mistakes
3. Check microsoft vs custom repos early - affects architecture decisions
4. File crawling scales well - processed ~20 doc files systematically
5. Profile with git sources is powerful - users just need the .md file

---

## Quick Reference

### Study Checklist
- [ ] KERNEL_PHILOSOPHY.md - understand mechanism vs policy
- [ ] IMPLEMENTATION_PHILOSOPHY.md - ruthless simplicity
- [ ] MODULAR_DESIGN_PHILOSOPHY.md - bricks and studs
- [ ] AMPLIFIER_CONTEXT_GUIDE.md - quick reference

### Migration Checklist
- [ ] Create new repo with `amplifier-app-{name}` naming
- [ ] Setup pyproject.toml with git sources
- [ ] Map legacy imports to new APIs
- [ ] Add .expanduser() to all path handling
- [ ] Preserve metacognitive recipe in HOW_THIS_APP_WAS_MADE.md
- [ ] Create MIGRATION_NOTES.md documenting what changed
- [ ] Test installation from clean environment
- [ ] Document lessons learned

### Files Every Migrated App Should Have
- `README.md` - What this app does, how to use it
- `HOW_THIS_APP_WAS_MADE.md` - The thinking process/recipe
- `MIGRATION_NOTES.md` - What changed from legacy (your creation story)
- `pyproject.toml` - Dependencies with git sources
- `src/{app}/` - The app code
- `.amplifier/profiles/{app-name}.md` - (optional) Profile with git sources for sharing

**Note:** For apps built from scratch, use `HOW_I_BUILT_THIS.md` instead of `MIGRATION_NOTES.md` to capture the conversation/creation story. See `BUILDING_NEW_APPS_WITH_AMPLIFIER.md` for guidance.

---

## Need Help?

**API not found?**
1. Grep amplifier-dev for function/class name
2. Check module README files
3. Document the mapping when you find it

**Pattern not clear?**
1. Check if similar pattern exists in amplifier-dev examples
2. Vendor your own implementation
3. Document it for future extractions

**Git sources not working?**
1. Verify GitHub auth: `gh auth status`
2. Check repository access
3. Verify subdirectory path is correct

---

**Remember:** This guide improves with each migration. Add your lessons learned!
