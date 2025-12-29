# Amplifier Ecosystem Overview

## What is Amplifier?

Amplifier is a **modular AI agent framework** built on the Linux kernel philosophy: a tiny, stable kernel that provides mechanisms only, with all policies and features living at the edges as replaceable modules.

**Core Principle**: "The center stays still so the edges can move fast."

## The Ecosystem

### Entry Point (amplifier)
The main repository providing:
- User-facing documentation
- Getting started guides
- Ecosystem overview
- Repository governance rules

### Kernel (amplifier-core)
The ultra-thin kernel (~2,600 lines) providing:
- Session lifecycle management
- Module loading/unloading
- Event system and hooks
- Coordinator infrastructure
- Stable contracts and protocols

**Key insight**: The kernel provides MECHANISMS, never POLICIES.

### Foundation Library (amplifier-foundation)
The primary library for building applications:
- Bundle primitives (composition, validation)
- Reference bundles and behaviors
- Best-practice examples
- Shared utilities

### Modules
Swappable capabilities that plug into the kernel:

| Type | Purpose | Examples |
|------|---------|----------|
| **Provider** | LLM backends | anthropic, openai, azure, ollama |
| **Tool** | Agent capabilities | filesystem, bash, web, search, task |
| **Orchestrator** | Execution strategy | loop-basic, loop-streaming, loop-events |
| **Context** | Memory management | context-simple, context-persistent |
| **Hook** | Observability/control | logging, redaction, approval |

### Bundles
Composable configuration packages combining:
- Providers, tools, orchestrators
- Behaviors (reusable capability sets)
- Agents (specialized personas)
- Context files

### Recipes (requires recipes bundle)
Multi-step AI agent orchestration for repeatable workflows:
- Declarative YAML workflow definitions
- Context accumulation across agent handoffs
- Approval gates for human-in-loop checkpoints
- Resumability after interruption

**Generic recipes available in the recipes bundle:**
- `repo-activity-analysis.yaml` - Analyze any GitHub repo (defaults to current directory, since yesterday)
- `multi-repo-activity-report.yaml` - Analyze multiple repos and synthesize a report

**Amplifier ecosystem usage:** See @amplifier:context/recipes-usage.md for how to use these recipes with MODULES.md to analyze Amplifier ecosystem repos.

## The Philosophy

### Mechanism, Not Policy
The kernel provides capabilities; modules decide behavior.

**Litmus test**: "Could two teams want different behavior?" → If yes, it's policy → Module, not kernel.

### Bricks & Studs (LEGO Model)
- Each module is a self-contained "brick"
- Interfaces are "studs" where bricks connect
- Regenerate any brick independently
- Stable interfaces enable composition

### Ruthless Simplicity
- As simple as possible, but no simpler
- Every abstraction must justify its existence
- Start minimal, grow as needed
- Don't build for hypothetical futures

### Event-First Observability
- If it's important, emit an event
- Single JSONL log as source of truth
- Hooks observe without blocking
- Tracing IDs enable correlation

## Getting Started Paths

### For Users
1. Start with @amplifier:docs/USER_ONBOARDING.md
2. Choose a profile/bundle from foundation
3. Run `amplifier run` with your chosen configuration

### For App Developers
1. Study @foundation:examples/ for patterns
2. Read @foundation:docs/BUNDLE_GUIDE.md for composition
3. Build your app using bundle primitives

### For Module Developers
1. Understand kernel contracts via @core:docs/
2. Follow module protocols
3. Test modules in isolation before integration

### For Contributors
1. Read @amplifier:docs/REPOSITORY_RULES.md for governance
2. Understand the dependency hierarchy
3. Contribute to the appropriate repository
