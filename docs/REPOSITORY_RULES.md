# Amplifier Repository Awareness Rules

**Last Updated**: 2025-10-31
**Purpose**: Define where documentation belongs and what can reference what

---

## Overview

Amplifier uses a modular repository architecture with clear boundaries. This document defines the awareness hierarchy to ensure documentation lives in the right place and prevents context poisoning through duplication.

**Core Principles**:
1. **Single source of truth** - Content lives in ONE place
2. **Link, don't duplicate** - Other repos link via GitHub URLs
3. **Respect awareness** - Don't reference what you're not aware of
4. **Challenge necessity** - Only create content that provides unique value
5. **Docs are contract** - Documentation defines what code must implement

---

## The Complete Hierarchy

### Entry Point
**amplifier** (microsoft/amplifier@next)
- **Purpose**: Main entry point for users and developers
- **Can Reference**: Everything (it's the entry point)
- **Referenced By**: All other repos (as the canonical "how to get started")
- **Contains**:
  - Getting started guide
  - Overview of ecosystem
  - Links to all components (via GitHub URLs)
  - Repository rules (this document)

### Kernel
**amplifier-core** (microsoft/amplifier-core)
- **Purpose**: Ultra-thin kernel providing mechanisms only
- **Can Reference**: ONLY amplifier@next
- **Referenced By**: Everything (it's the kernel)
- **CANNOT Reference**: Any libraries, modules, apps (they don't exist to kernel)
- **Contains**:
  - Kernel philosophy
  - Core mechanisms (session, coordinator, events)
  - Kernel contracts (Mount Plan, events, protocols)
  - Specifications

### Libraries (Provide APIs)

**amplifier-profiles** (microsoft/amplifier-profiles)
- **Purpose**: Profile and agent loading, inheritance, Mount Plan compilation
- **Can Reference**: amplifier-core, amplifier@next, amplifier-collections
- **Referenced By**: Applications (amplifier-app-cli, etc.)
- **CANNOT Be Referenced By**: amplifier-core
- **Contains**:
  - ProfileLoader, AgentLoader, AgentResolver APIs
  - Profile/Agent schemas and protocols
  - Profile authoring guide (user-facing)
  - Agent authoring guide (user-facing)
  - System design and architecture
  - All profile/agent concepts and examples

**amplifier-collections** (microsoft/amplifier-collections)
- **Purpose**: Collections system for shareable expertise bundles
- **Can Reference**: amplifier-core, amplifier@next, amplifier-module-resolution
- **Referenced By**: Applications, amplifier-profiles
- **CANNOT Be Referenced By**: amplifier-core
- **Contains**:
  - CollectionResolver API
  - Collection installation and discovery
  - Collection authoring guide
  - Collection format specification

**amplifier-config** (microsoft/amplifier-config)
- **Purpose**: Configuration management (settings, scopes, paths)
- **Can Reference**: amplifier-core, amplifier@next
- **Referenced By**: Applications
- **CANNOT Be Referenced By**: amplifier-core
- **Contains**:
  - ConfigManager, ConfigPaths APIs
  - Scope system (user, project, local)
  - Settings management
  - deep_merge utility

**amplifier-module-resolution** (microsoft/amplifier-module-resolution)
- **Purpose**: Module source resolution (git, file, package)
- **Can Reference**: amplifier-core, amplifier@next
- **Referenced By**: Applications, amplifier-collections
- **CANNOT Be Referenced By**: amplifier-core
- **Contains**:
  - StandardModuleSourceResolver API
  - GitSource, FileSource, PackageSource
  - Module installation and caching
  - Source resolution specification

### Applications (Consume Libraries)

**amplifier-app-cli** (microsoft/amplifier-app-cli)
- **Purpose**: Reference CLI application
- **Can Reference**: All libraries, modules, core
- **Referenced By**: Nothing (it's an endpoint)
- **Contains**:
  - CLI command reference
  - App-specific implementation docs (agent delegation, etc.)
  - Toolkit utilities for building sophisticated tools
  - How THIS app uses libraries

### Collections (Shareable Bundles)

**amplifier-collection-design-intelligence**
**amplifier-collection-***
- **Purpose**: Bundles of profiles, agents, context, tools, modules
- **Can Reference**: Modules, libraries (looser rules, evolving)
- **Referenced By**: Applications (via collection:name syntax)
- **Contains**:
  - Profiles, agents, context, scenario tools, modules
  - Collection-specific documentation

### Modules (Kernel Extensions)

**Context Managers**:
- amplifier-module-context-persistent
- amplifier-module-context-simple

**Hooks**:
- amplifier-module-hooks-approval
- amplifier-module-hooks-backup
- amplifier-module-hooks-logging
- amplifier-module-hooks-redaction
- amplifier-module-hooks-scheduler-cost-aware
- amplifier-module-hooks-scheduler-heuristic
- amplifier-module-hooks-streaming-ui

**Orchestrators**:
- amplifier-module-loop-basic
- amplifier-module-loop-events
- amplifier-module-loop-streaming

**Providers**:
- amplifier-module-provider-anthropic
- amplifier-module-provider-azure-openai
- amplifier-module-provider-mock
- amplifier-module-provider-ollama
- amplifier-module-provider-openai

**Tools**:
- amplifier-module-tool-bash
- amplifier-module-tool-filesystem
- amplifier-module-tool-search
- amplifier-module-tool-task
- amplifier-module-tool-web

**All Modules**:
- **Referenced By**: Apps/libraries via mount plans
- **Can Reference**: ONLY amplifier-core, possibly amplifier@next
- **CANNOT Reference**: Other modules, libraries, apps (unaware of peers)
- **Contains**: Module implementation, module-specific documentation

---

## What Goes Where: Decision Tree

### Is it a kernel contract/mechanism?
→ **amplifier-core** (`docs/specs/`)

**Examples**:
- Mount Plan specification
- Event taxonomy
- Core protocols
- Session forking contract

### Is it library API documentation?
→ **amplifier-{library}** (`README.md`, `docs/`)

**What lives in library repos**:
- Complete API reference
- User guides for library concepts
- System design and architecture
- All examples and patterns
- Schemas and protocols

**Libraries**:
- **amplifier-profiles** - Profile/agent system (ALL profile/agent docs)
- **amplifier-collections** - Collections system (ALL collection docs)
- **amplifier-config** - Configuration (ALL config docs)
- **amplifier-module-resolution** - Module sources (ALL resolution docs)

### Is it app-specific implementation?
→ **amplifier-app-cli** (or other app) (`README.md`, `docs/`)

**Examples**:
- Command reference
- CLI-specific behavior (search paths, env vars)
- How THIS app uses libraries
- Toolkit utilities

### Is it user/dev entry point?
→ **amplifier@next** (`README.md`, `docs/`)

**What lives here**:
- Getting started (thin overview)
- Ecosystem overview
- Links to detailed docs (via GitHub URLs)
- Repository rules (this document)
- NO duplicate content from libraries

### Is it module-specific?
→ **amplifier-module-{name}** (`README.md`)

**Examples**:
- Module implementation details
- Module configuration options
- Module-specific usage examples

---

## Content Ownership Examples

### Example 1: Profile System

**Owner**: amplifier-profiles library

**What lives there**:
- ProfileLoader API documentation
- "What are profiles?" conceptual explanation
- "How do I create profiles?" user guide (PROFILE_AUTHORING.md)
- Profile schemas and validation
- Inheritance and overlay merging design
- All profile examples and patterns

**What links there**:
- amplifier@next README - Links to profile authoring guide via GitHub URL
- amplifier-app-cli README - Links to profile API docs via GitHub URL
- Other docs reference via GitHub URLs

**What does NOT live elsewhere**:
- ❌ Profile authoring guide in amplifier@next (just link)
- ❌ Profile concepts in app-cli docs (just link)
- ❌ Duplicated profile examples (just link)

### Example 2: Mount Plan Contract

**Owner**: amplifier-core

**What lives there**:
- Mount Plan specification (kernel contract)
- Format and structure
- Validation rules

**What links there**:
- amplifier-profiles - Compiles profiles to this format
- Module docs - Modules are mounted via this contract

**Why this works**:
- Kernel contract lives in kernel
- Libraries reference kernel contracts

### Example 3: Agent Delegation

**Conceptual docs owner**: amplifier-profiles library
**Implementation docs owner**: amplifier-app-cli

**amplifier-profiles contains**:
- "What are agents?" concepts
- Agent schemas and formats
- Agent authoring guide
- AgentLoader/AgentResolver API

**amplifier-app-cli contains**:
- How CLI resolves agents (search paths)
- CLI-specific features (environment variables)
- CLI commands (agent list, agent show)
- Links to amplifier-profiles for concepts

**Why split**:
- Concepts = library's domain
- Implementation = app's domain
- Clear separation of concerns

---

## Link Patterns

### External Links (GitHub URLs)

**Use when**: Referencing authoritative docs in other repos

**Format**:
```markdown
**→ [Profile Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md)**

For details on collections, see [amplifier-collections](https://github.com/microsoft/amplifier-collections).
```

**Why**:
- Always points to latest version
- Clear it's external documentation
- Users can follow link to authoritative source
- No duplication

### Internal Links (Relative)

**Use when**: Referencing docs within same repo

**Format**:
```markdown
See [System Design](docs/DESIGN.md) for architecture details.
```

**Why**:
- Works in local clones
- Simpler for same-repo references

---

## Anti-Patterns (Common Mistakes to Avoid)

### ❌ WRONG: Duplicate Content

```markdown
<!-- In amplifier@next README -->
## Creating Profiles

Profiles are YAML configuration files with frontmatter...
[500 lines of duplicated profile documentation]
```

**Problem**: Duplication causes context poisoning when content diverges

**Fix**: Link to authoritative source
```markdown
## Creating Profiles

**→ [Profile Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md)**
```

### ❌ WRONG: Core References Library

```markdown
<!-- In amplifier-core/README.md -->
For profile configuration, see amplifier-profiles library.
```

**Problem**: Core shouldn't know libraries exist

**Fix**: Don't mention libraries in core docs (core only knows itself and entry point)

### ❌ WRONG: Module References Other Module

```markdown
<!-- In amplifier-module-tool-bash/README.md -->
Works well with amplifier-module-tool-filesystem.
```

**Problem**: Modules don't know about peer modules

**Fix**: Don't reference other modules by name

### ❌ WRONG: Library References App

```markdown
<!-- In amplifier-profiles/README.md -->
Used by amplifier-app-cli for profile management.
```

**Problem**: Library shouldn't know about specific apps

**Fix**: Generic language
```markdown
Used by applications for profile management.
```

### ❌ WRONG: Local File Link to External Repo

```markdown
<!-- In amplifier@next README -->
See [Profile Guide](../amplifier-profiles/docs/PROFILE_AUTHORING.md)
```

**Problem**: Assumes local multi-repo structure, breaks for users who clone single repo

**Fix**: Use GitHub URL
```markdown
**→ [Profile Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md)**
```

---

## Validation Checklist

Before creating/moving documentation:

- [ ] **Ownership**: Is this the right repository for this content?
- [ ] **Awareness**: Does this respect the hierarchy?
- [ ] **Duplication**: Is this duplicating content from another repo?
- [ ] **Necessity**: Does this provide unique value, or can users follow links?
- [ ] **Links**: Are external references via GitHub URLs?
- [ ] **Contract**: Is this documentation the contract (vs implementation)?

---

## Content Distribution Examples

### User Wants to Create a Profile

**Journey**:
1. Start at amplifier@next README
2. See "Creating Profiles" section
3. Click link to amplifier-profiles/docs/PROFILE_AUTHORING.md
4. Read complete authoring guide
5. Reference API docs in amplifier-profiles/README.md as needed

**Why this works**:
- Entry point guides user
- Authoritative docs in library
- No duplication

### Developer Building an App

**Journey**:
1. Start at amplifier@next README
2. See "For Developers" section with library links
3. Click link to amplifier-profiles
4. Read ProfileLoader API documentation
5. Reference design docs as needed

**Why this works**:
- Entry point provides discovery
- Library provides complete API docs
- App examples show integration

### Contributor to amplifier-profiles

**Journey**:
1. Clone amplifier-profiles repo
2. Read README for API overview
3. Read docs/DESIGN.md for architecture
4. Read code with docs as contract
5. Make changes maintaining contracts

**Why this works**:
- All profile/agent knowledge in one repo
- Complete context for contributors
- Docs define contracts code must implement

---

## Maintenance

### When Adding New Documentation

**Process**:
1. **Identify owner**: Where does this content belong?
2. **Check for duplication**: Does this exist elsewhere?
3. **Add to owner repo**: Put it in the right place
4. **Update links**: Add links from other repos via GitHub URLs
5. **Update this doc**: If new patterns emerge

**Example**:
```
# Adding collection authoring guide
1. Owner: amplifier-collections (it's about collections)
2. Check: Does amplifier-profiles mention this? (no)
3. Add: amplifier-collections/docs/AUTHORING.md
4. Link: Update amplifier@next to link to it
5. Update: Note in this doc if needed
```

### When Moving Documentation

**Process**:
1. **Find all references**: Grep for links to old location
2. **Update to GitHub URLs**: Replace with external links
3. **Verify hierarchy**: Ensure moves respect awareness
4. **Test links**: Verify all links work
5. **Delete old location**: Remove from original repo

### Regular Audits

**Quarterly review**:
- Search for duplicated content (`grep -r "same content"`)
- Verify awareness rules followed
- Check for broken links
- Update examples and patterns

---

## Summary Reference

**Repository Types**:
- **Entry Point**: amplifier@next - Links to everything
- **Kernel**: amplifier-core - Contracts and mechanisms only
- **Libraries**: amplifier-{profiles,collections,config,module-resolution} - APIs and guides
- **Applications**: amplifier-app-cli - Implementation and commands
- **Collections**: amplifier-collection-* - Bundled expertise
- **Modules**: amplifier-module-* - Isolated kernel extensions

**Content Flow**:
- Authoritative source → Single repo (library or core)
- Other repos → Link via GitHub URLs
- NO duplication
- Challenge necessity of all content

**Awareness Rules**:
- Entry point can reference all ✅
- Core references nothing except entry ✅
- Libraries reference core + entry (+ other libs if needed) ✅
- Apps reference libs + modules + core ✅
- Modules reference only core (+ possibly entry) ✅
- No circular references ✅

**Philosophy**:
- Docs are contract, code is implementation
- Maximum DRY eliminates context poisoning
- Users can follow links to find details
- Each repo is self-contained for its domain

---

**For questions about where content belongs, use the decision tree above or ask in discussions.**
