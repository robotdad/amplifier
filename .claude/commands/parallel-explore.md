---
description: Execute parallel experiments across git worktrees
category: experiments
allowed-tools: ["Bash", "SlashCommand"]
---

Execute multiple implementation approaches in parallel using git worktrees to find optimal solutions through empirical comparison. Now with enhanced context support for better implementation results.

## Usage

```
/parallel-explore [experiment-name]
```

Examples:
- `/parallel-explore` - Interactive mode, asks for name
- `/parallel-explore cache-layer` - Direct mode, uses saved context for "cache-layer"

Interactive setup guides you through:
1. Experiment name (for organizing worktrees/results)
2. Base task description (if no saved context)
3. Number or types of variations to explore

## Enhanced Context Support

The command now:
- **Loads saved context** from `/explore-variants` if available
- **Creates rich context** for better variant implementations
- **Provides detailed instructions** to each variant
- **Ensures worktree isolation** with explicit path guidance

## What It Does

- Checks for existing context in `.data/parallel_explorer/{name}/context.json`
- Creates isolated git worktrees for each variant approach
- Provides comprehensive prompts with full context to each variant
- Delegates to `parallel-orchestrator` agent for coordination
- Runs concurrent experiments with ultrathink methodology
- Validates that files are created in the correct worktree
- Aggregates results for comparison
- Preserves all implementations in separate worktrees

## Examples

### Basic exploration
```
/parallel-explore
> Name: rate-limiter
> Task: Implement API rate limiting with Redis backend
> Variations: 3
```

### Named approaches with context
```
# First, generate variants with context
/explore-variants
> Name: auth-system
> Task: Build secure authentication module
> Requirements: JWT-based, refresh tokens, rate limiting

# Then run parallel exploration (will use saved context)
/parallel-explore
> Name: auth-system  # Uses saved context automatically
```

### Direct with pre-saved context
```
/parallel-explore
> Name: cache-layer  # If context exists, it will be loaded
> Variations: [will use variants from context]
```

## Context Loading Priority

1. **Saved context** (`.data/parallel_explorer/{name}/context.json`) - Highest priority
2. **Command-line context** (if provided via `--context-file`)
3. **Interactive input** - Fallback if no context exists

## Delegation Details

The `parallel-orchestrator` agent receives:
- Full experiment context (task, requirements, success criteria)
- Variant-specific instructions (approach, focus areas, constraints)
- Explicit worktree paths and creation instructions
- Validation to ensure files are created correctly

## Troubleshooting

### Files created in wrong location
- Context now includes explicit `cd` commands
- Validation checks actual worktree contents
- Clear instructions about where to create files

### Insufficient context
- Use `/explore-variants` first to create rich context
- Check `.data/parallel_explorer/{name}/context.json` exists
- Review context with `cat .data/parallel_explorer/{name}/context.json`

### Validation failures
- New validation checks any files in worktree (not specific paths)
- Supports Python, documentation, config, and other code files
- Logs detailed information about what was found

## View Available Experiments

To see what experiments have saved context:
```bash
ls -la .data/parallel_explorer/
```
Each directory represents an experiment with saved context.

## Note on Command Names

The commands are:
- `/explore-variants` - for brainstorming variant approaches
- `/parallel-explore` - for running parallel experiments

While the naming isn't perfectly symmetric (historical reasons), think of it as:
- First you "explore variants" (brainstorm)
- Then you "parallel explore" (execute in parallel)

Future versions may introduce aliases for consistency.

## See Also

- `/explore-variants` - Create rich context before running
- `make parallel-explore NAME=experiment` - Direct CLI with context
- `make parallel-explore-results` - View experiment results
- `make parallel-explore-cleanup` - Remove experiment data