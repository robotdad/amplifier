# Module Development Lessons Learned

_Captured: 2025-10-19_

Practical lessons from developing amplifier modules (tool-mcp, tool-skills, context-skills).

---

## Profile System Evolution

### Format Changed: .yaml → .md

Amplifier profiles are now **Markdown with YAML frontmatter**:

```markdown
---
profile:
  name: my-profile

session:
  orchestrator:
    module: loop-basic
---

# My Profile

Documentation goes here...
```

**Key points:**
- Frontmatter = actual config between `---` markers
- Markdown body = embedded documentation (self-documenting profiles)
- Files must be `*.md` not `*.yaml` (loader only searches for `.md`)
- Profile loader: `amplifier-app-cli/profile_system/loader.py` line 63

### Schema Requirements

**Session section must use dict format:**

```yaml
# ❌ Wrong - validation error
session:
  orchestrator: loop-basic
  context: context-simple

# ✅ Correct
session:
  orchestrator:
    module: loop-basic
  context:
    module: context-simple
```

### Naming Convention

**Use suffix pattern** for consistency:
- ✅ `mcp-example`, `skills-example` (feature-variant)
- ❌ `example-mcp`, `example-skills` (inconsistent grouping)

**Filename must match internal name:**
- File: `mcp-example.md`
- Inside: `name: mcp-example`

**Why:** Profile loader matches by name, mismatches cause confusion

---

## Module Distribution

### Git Sources vs Path Dependencies

For modules to work as **standalone git installs**, dependencies must use git sources:

```toml
# ❌ Breaks when downloaded from git
[tool.uv.sources]
amplifier-core = { path = "../../amplifier-dev/amplifier-core", editable = true }

# ✅ Works standalone
[tool.uv.sources]
amplifier-core = { git = "https://github.com/microsoft/amplifier-core", branch = "main" }
```

**Why it matters:**
- Path dependencies only work within directory structure
- Git sources work anywhere
- Enables `source:` fields in profiles

### Profile Source Fields

**Convention from bundled profiles:** Always include `source:` field

```yaml
tools:
  - module: tool-mcp
    source: git+https://github.com/robotdad/amplifier-module-tool-mcp@main
```

**Enables:**
- Auto-download from git (no local clone needed)
- Users just need: GitHub auth + the profile file
- Follows pattern from `base.md`, `dev.md`, `full.md`

**Limitation with private repos:**
- Profile files themselves can't be curled without auth
- Must share files directly or make repos public
- Module download via `source:` works fine with GitHub auth

---

## Avoiding Duplicate Configuration

### The Problem

Two modules (context-skills, tool-skills) both needed same `skills_dirs` config:

```yaml
# ❌ Error-prone duplication
session:
  context:
    config:
      skills_dirs: [~/skills, .amplifier/skills]

tools:
  - module: tool-skills
    config:
      skills_dirs: [~/skills, .amplifier/skills]  # Must match!
```

**Issues:**
- Easy to mismatch paths
- Context knows about skills tool can't load
- Violates DRY principle

### The Solution: Capability Registry

**Use existing kernel infrastructure** (coordinator.py:178-202):

```python
# Module 1: Register capability
coordinator.register_capability("skills.registry", self.skills)
coordinator.register_capability("skills.directories", self.skills_dirs)

# Module 2: Read capability first, fall back to config
skills = coordinator.get_capability("skills.registry")
if skills:
    self.skills = skills  # Reuse!
else:
    self.skills = discover_own()  # Standalone mode
```

**Result:**
```yaml
session:
  context:
    module: context-skills
    config:
      skills_dirs: [~/skills, .amplifier/skills]  # ← Single config

tools:
  - module: tool-skills  # ← No config needed!
```

**Benefits:**
- Configure once in context section
- Tool automatically reuses discovery
- Still works standalone if context not loaded
- Follows kernel philosophy: "Capability registry for inter-module communication"

**Why this works:**
- Doesn't require profile schema changes (attempted top-level `skills:` section failed)
- Uses existing coordinator infrastructure
- Maintains module independence

---

## Path Handling

### Tilde Expansion

**Critical:** `Path()` doesn't expand `~` automatically

```python
# ❌ Looks for literal "~" directory
Path("~/Source/skills")

# ✅ Expands to /Users/username/Source/skills
Path("~/Source/skills").expanduser()
```

**Always use `.expanduser()`** when accepting paths from config.

---

## Documentation Hygiene

### Remove Development Artifacts

Clean examples of **what NOT to include:**

```json
{
  "description": "✅ Working - 7 tools",  // ❌ Status emojis
  "note": "⚠️ Has issues",               // ❌ Testing notes
  "_experimental_servers": {...},        // ❌ Dev sections
  "_comment": "Move when ready"          // ❌ Internal comments
}
```

**Clean version:**
```json
{
  "description": "Code packaging and analysis tools for analyzing codebases"
}
```

**Why:** Examples are user-facing, not internal dev docs

### Product-Agnostic Language

**Reference the ecosystem, not specific products:**

```markdown
❌ "Skills that Claude loads dynamically"
✅ "Skills that agents load dynamically"
```

**Why:** This is Amplifier (works with any provider), not Claude-specific

---

## Testing Workflow

### Local Development Setup

**For testing module changes:**

```bash
# Make changes to module code
cd amplifier-module-tool-mcp

# Reinstall to pick up changes
uv pip install -e . --force-reinstall --no-deps

# Test from amplifier-dev
cd /path/to/amplifier-dev
.venv/bin/amplifier run --profile mcp-example "test"
```

**Key points:**
- Editable installs for development
- Force reinstall picks up code changes
- Test with actual amplifier CLI, not just unit tests

### Profile Testing

**Profiles must be in recognized locations:**

```bash
# ❌ Won't work
amplifier run --profile examples/mcp-example.md

# ✅ Works
cp examples/mcp-example.md .amplifier/profiles/
amplifier run --profile mcp-example
```

**Why:** Profile loader searches `.amplifier/profiles/`, not arbitrary paths

---

## Architecture Insights

### Kernel Philosophy in Practice

**What we learned:**

1. **Coordinator provides infrastructure:** IDs, config, hooks, capabilities
2. **Capability registry enables cooperation:** Modules communicate without dependencies
3. **Mechanism vs Policy:**
   - Coordinator = mechanism (capability registration)
   - Modules = policy (what to register, how to use)

**Example:** Capability registry solved duplicate configuration without:
- Profile schema changes
- Module-to-module dependencies
- Breaking kernel boundaries

### Module Independence vs Cooperation

**Design tension resolved:**

- Modules must work **independently** (can use tool-skills without context-skills)
- Modules should **cooperate** when both present (capability sharing)
- Capability pattern achieves both

**Pattern:**
```python
# Try to cooperate
shared = coordinator.get_capability("x")
if shared:
    use(shared)
else:
    # Fall back to independence
    discover_own()
```

---

## Common Pitfalls

### Git Authentication

**Issue:** Private repos require GitHub auth for git sources

**User needs:**
- `gh auth login` or SSH keys configured
- Collaborator access to repos

**Profile files can't be curled** from private repos - must share directly

### __pycache__ in Git

**If committed before .gitignore:**

```bash
git rm -r --cached module_name/__pycache__
git commit -m "Remove pycache from tracking"
```

**Why it happens:** Files tracked before .gitignore was added stay tracked

### Profile Validation Errors

**Common errors:**

```
session.orchestrator: Input should be a valid dictionary
```

**Fix:** Use dict format with `module:` key, not bare string

---

## Quick Reference

### Module pyproject.toml Template

```toml
[project]
dependencies = ["amplifier-core"]

[tool.uv.sources]
amplifier-core = { git = "https://github.com/microsoft/amplifier-core", branch = "main" }
```

### Example Profile Template

```yaml
---
profile:
  name: feature-example
  version: "1.0.0"
  extends: base

session:
  orchestrator:
    module: loop-basic
  context:
    module: context-simple

tools:
  - module: tool-feature
    source: git+https://github.com/your-org/amplifier-module-tool-feature@main
---

# Feature Example Profile

Documentation goes here...
```

### Tester Distribution

**With public repos:**
- Share: profile .md files + config files
- Users: Drop in `.amplifier/profiles/` and run

**With private repos:**
- Share: files directly (email/Slack)
- Users need: GitHub auth configured

---

## Documentation Best Practices

### Reference Anthropic Standards

When building on Anthropic specifications (like Skills):
- Link to canonical spec: `https://github.com/anthropics/skills`
- Explain how your module enables it: "Brings Anthropic Skills support to Amplifier"
- Show integration examples

### Self-Documenting Profiles

Use markdown section to explain:
- What this enables
- Quick start steps
- Configuration options
- When to use this profile

**Users get one file** that's both config and documentation

---

## Key Takeaways

1. **Maintainer moves fast** - Schema changes without announcement, adapt quickly
2. **Use kernel mechanisms** - Capability registry solves problems without schema changes
3. **Test in real environment** - Unit tests pass but real usage reveals issues
4. **Path dependencies break distribution** - Always use git sources for amplifier-core
5. **Documentation is user-facing** - Remove all internal dev notes and status
6. **Consistency matters** - Naming conventions prevent confusion
7. **Can't assume schema support** - Work with what exists (capability registry) not what would be ideal (top-level `skills:` section)
