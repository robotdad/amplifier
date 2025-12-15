# Migrating from Collections to Bundles

**Purpose**: Guide for converting existing `amplifier-collection-*` repositories to the new `amplifier-bundle-*` format.

---

## Why Migrate?

**Bundles** replace **collections** as the primary way to package and share Amplifier configurations:

| Aspect        | Collections (deprecated)                        | Bundles (current)              |
| ------------- | ----------------------------------------------- | ------------------------------ |
| Format        | Python package with pyproject.toml              | Markdown with YAML frontmatter |
| Loading       | `amplifier collection add ...`                  | `amplifier --bundle ...`       |
| Configuration | `[tool.amplifier.collection]` in pyproject.toml | YAML in bundle.md frontmatter  |
| Naming        | `amplifier-collection-*`                        | `amplifier-bundle-*`           |
| Philosophy    | Python package                                  | Configuration file             |

**Key insight**: Bundles are configuration, not Python packages. This simplifies distribution and composition.

---

## Migration Overview

Converting a collection to a bundle involves:

1. Create `bundle.md` with YAML frontmatter
2. Verify agent frontmatter format
3. Delete collection-specific artifacts
4. Update README for bundle loading
5. Optionally rename repository

---

## Step-by-Step Migration

### Step 1: Create bundle.md

Replace `pyproject.toml [tool.amplifier.collection]` with `bundle.md`:

**Before (collection pyproject.toml)**:

```toml
[tool.amplifier.collection]
name = "my-collection"
description = "What this collection provides"
modules = [{ type = "tool", path = "modules/tool-foo" }]
agents = [{ name = "my-agent", path = "agents/my-agent.md" }]
```

**After (bundle.md)**:

```yaml
---
bundle:
  name: my-bundle
  version: 1.0.0
  description: What this bundle provides

tools:
  - module: tool-foo
    source: ./modules/tool-foo

agents:
  include:
    - my-bundle:my-agent
---

# System Instructions

[Your system prompt content here]

Reference documentation: @my-bundle:docs/GUIDE.md
```

### Step 2: Verify Agent Frontmatter

Agents need `meta:` frontmatter (not `agent:` or other formats):

**Correct format**:

```yaml
---
meta:
  name: my-agent
  description: "Agent description with examples..."
---
# Agent Instructions

[Agent content here]
```

**Check your agent files** in `agents/` directory for correct frontmatter.

### Step 3: Delete Collection Artifacts

Remove these files/directories entirely:

```bash
# Python package namespace directory
rm -rf amplifier_collection_*/

# Profiles directory (replaced by bundle)
rm -rf profiles/

# Root pyproject.toml (bundles don't need it)
rm pyproject.toml

# Lock file (generated from pyproject.toml)
rm uv.lock

# Manifest (not needed)
rm MANIFEST.in

# Build artifacts
rm -rf *.egg-info/
rm -rf dist/
rm -rf build/
```

**Important**: Bundles are configuration, not Python packages. The root `pyproject.toml` is not needed. Only modules inside `modules/` retain their own `pyproject.toml`.

### Step 4: Update README

Change usage instructions from collection installation to bundle loading:

**Before (collection)**:

```bash
# Add the collection
amplifier collection add git+https://github.com/org/amplifier-collection-foo@main

# Use a profile from the collection
amplifier run --profile collection-foo:default "prompt"
```

**After (bundle)**:

```bash
# Load the bundle directly
amplifier --bundle git+https://github.com/org/amplifier-bundle-foo@main run "prompt"

# Or load from local path
amplifier --bundle ./bundle.md run "prompt"
```

**Include in another bundle**:

```yaml
includes:
  - bundle: git+https://github.com/org/amplifier-bundle-foo@main
```

### Step 5: Rename Repository (optional)

Follow the naming convention:

- Old: `amplifier-collection-*`
- New: `amplifier-bundle-*`

Example: `amplifier-collection-recipes` → `amplifier-bundle-recipes`

---

## Migration Checklist

Before migration:

- [ ] Understand current collection structure
- [ ] Identify all modules in `modules/`
- [ ] Identify all agents in `agents/`
- [ ] Note any profile configurations

During migration:

- [ ] Create `bundle.md` with tools and agents
- [ ] Verify agent `meta:` frontmatter
- [ ] Delete `amplifier_collection_*` directory
- [ ] Delete `profiles/` directory
- [ ] Delete root `pyproject.toml`
- [ ] Delete `uv.lock`
- [ ] Delete `MANIFEST.in` if present
- [ ] Delete build artifacts (`*.egg-info`, `dist/`, `build/`)

After migration:

- [ ] Update README with bundle loading syntax
- [ ] Test bundle loads: `amplifier --bundle ./bundle.md run "test"`
- [ ] Verify agents load correctly
- [ ] Verify tools execute correctly
- [ ] Consider renaming repository

---

## Mapping Collection Concepts to Bundles

### Modules

**Collection**:

```toml
[tool.amplifier.collection]
modules = [
    { type = "tool", path = "modules/tool-foo" },
    { type = "hook", path = "modules/hooks-bar" }
]
```

**Bundle**:

```yaml
tools:
  - module: tool-foo
    source: ./modules/tool-foo

hooks:
  - module: hooks-bar
    source: ./modules/hooks-bar
```

### Agents

**Collection**:

```toml
[tool.amplifier.collection]
agents = [
    { name = "helper", path = "agents/helper.md" }
]
```

**Bundle**:

```yaml
agents:
  include:
    - my-bundle:helper
```

Note: Agent files stay in `agents/` directory with `meta:` frontmatter.

### Profiles

**Collection profiles** defined configuration sets. **Bundles** replace this with:

- Bundle composition via `includes:`
- Configuration via `config:` blocks on modules
- Variant bundles for different configurations

**Collection profile**:

```yaml
# profiles/dev.yaml
providers:
  - module: provider-anthropic
    config:
      debug: true
```

**Bundle equivalent** (variant bundle or inline config):

```yaml
# bundle.md for dev variant
providers:
  - module: provider-anthropic
    source: git+https://github.com/microsoft/amplifier-module-provider-anthropic@main
    config:
      debug: true
```

---

## Example Migration: amplifier-collection-recipes

### Before (collection structure)

```
amplifier-collection-recipes/
├── amplifier_collection_recipes/     # Python namespace (DELETE)
│   └── __init__.py
├── profiles/                         # Profiles (DELETE)
│   └── default.yaml
├── agents/
│   ├── recipe-author.md
│   └── result-validator.md
├── modules/
│   └── tool-recipes/
│       ├── pyproject.toml           # Keep (module's own config)
│       └── amplifier_module_tool_recipes/
├── docs/
├── examples/
├── templates/
├── pyproject.toml                   # Root package config (DELETE)
├── uv.lock                          # Lock file (DELETE)
├── MANIFEST.in                      # Manifest (DELETE)
└── README.md
```

### After (bundle structure)

```
amplifier-bundle-recipes/
├── bundle.md                        # NEW: Bundle definition
├── agents/
│   ├── recipe-author.md             # Unchanged (verify meta: frontmatter)
│   └── result-validator.md
├── modules/
│   └── tool-recipes/
│       ├── pyproject.toml           # Unchanged (module's own config)
│       └── amplifier_module_tool_recipes/
├── docs/
├── examples/
├── templates/
└── README.md                        # Updated: bundle loading syntax
```

### Key Changes

1. **Created**: `bundle.md` with YAML frontmatter defining tools and agents
2. **Deleted**: `amplifier_collection_recipes/`, `profiles/`, root `pyproject.toml`, `uv.lock`, `MANIFEST.in`
3. **Unchanged**: `agents/`, `modules/`, `docs/`, `examples/`, `templates/`
4. **Updated**: `README.md` with bundle loading instructions

---

## Reference

For creating new bundles from scratch, see the [Bundle Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_GUIDE.md) in amplifier-foundation.
