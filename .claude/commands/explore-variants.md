---
description: Brainstorm variant approaches for parallel exploration
category: experiments
allowed-tools: []
---

Brainstorm and generate variant implementation approaches for a given task before running parallel experiments. This command creates rich context for better implementation results.

## Usage

```
/explore-variants
```

Interactive brainstorming session to generate implementation variants for parallel exploration.

## What It Does

Helps you identify diverse implementation approaches by:
- Analyzing the problem space
- Suggesting paradigm variations (functional, OOP, reactive)
- Proposing architectural patterns
- Creating rich context for each variant
- Saving context for use with `parallel-explore`
- Outputting structured JSON for immediate use

## Enhanced Context Creation

When generating variants, also:
1. Ask for the experiment name
2. Capture base task description
3. Define requirements and constraints
4. Create variant-specific approaches and focus areas
5. Save context to `.data/parallel_explorer/{name}/context.json`

## Example Interactive Session

```
/explore-variants
> Experiment name: cache-layer
> Task: Build a high-performance cache layer for API responses
> Requirements: Must handle 10K requests/sec, support TTL, be horizontally scalable

Generating variants with rich context...

Output:
{
  "in-memory": {
    "description": "Local memory cache with TTL support",
    "approach": "Use Python dict with timestamp tracking for TTL",
    "focus_areas": ["performance", "memory efficiency"],
    "context": "Best for single-instance deployments"
  },
  "redis": {
    "description": "Redis-backed distributed cache",
    "approach": "Leverage Redis features with connection pooling",
    "focus_areas": ["scalability", "reliability"],
    "context": "Ideal for multi-instance deployments"
  },
  "hybrid": {
    "description": "Two-tier cache with local and remote layers",
    "approach": "L1 cache in-memory, L2 in Redis with smart invalidation",
    "focus_areas": ["latency optimization", "consistency"],
    "context": "Balances performance with scalability"
  }
}

✅ Context saved to: .data/parallel_explorer/cache-layer/context.json

Run exploration with one of these commands:

Option A - Slash command (direct):
   /parallel-explore cache-layer

Option B - Slash command (interactive):
   /parallel-explore
   > Name: cache-layer

Option C - Make command:
   make parallel-explore NAME="cache-layer"

To review saved context:
   cat .data/parallel_explorer/cache-layer/context.json
```

## Output Format

### Simple Format (backward compatible)
```json
{
  "variant-name": "Brief description of approach",
  "variant2": "Another approach description"
}
```

### Rich Context Format
```json
{
  "variant-name": {
    "description": "Brief description",
    "approach": "Detailed implementation approach",
    "focus_areas": ["area1", "area2"],
    "context": "Additional context"
  }
}
```

## Context File Structure

The saved context includes:
- Experiment name and task
- Detailed requirements
- Common context across variants
- Rich variant specifications
- Success criteria

## Integration

Output can be passed directly to:
- `/parallel-explore` command (will auto-load saved context)
- `make parallel-explore NAME=experiment-name` (uses saved context)
- Direct JSON usage for manual execution

## Managing Multiple Experiments

You can prepare multiple experiments before running them:

```bash
# Prepare experiment 1
/explore-variants
> Name: auth-system
> Task: Build authentication
[saves to .data/parallel_explorer/auth-system/context.json]

# Prepare experiment 2
/explore-variants
> Name: cache-layer
> Task: Build caching
[saves to .data/parallel_explorer/cache-layer/context.json]

# Later, run whichever you're ready for:
/parallel-explore auth-system
/parallel-explore cache-layer
```

Each experiment gets its own directory and can be iterated on independently.

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

## Tips

1. **Be specific** about requirements and constraints
2. **Include technical details** that will help implementation
3. **Define success criteria** clearly
4. **Consider diverse approaches** (not just variations of the same idea)
5. **Save experiment name** consistently for context reuse