# Parallel Explorer: Compare Implementation Approaches in Parallel

**Find the best solution by exploring multiple approaches simultaneously.**

## The Problem

You have implementation choices to make, but:
- **Choosing is hard** - Functional vs OOP vs reactive - which is best for your use case?
- **Serial exploration is slow** - Try one approach, wait for results, then try another...
- **Theory vs reality** - What sounds good on paper may not work in practice
- **No empirical comparison** - Hard to compare approaches objectively without building them all

## The Solution

Parallel Explorer is a tool that:

1. **Creates isolated worktrees** - Each approach gets its own clean git workspace
2. **Runs parallel Claude sessions** - Multiple implementations happen simultaneously
3. **Applies ultrathink methodology** - Each session gets full ultrathink instructions for quality
4. **Compares real results** - See actual implementations, not theoretical discussions
5. **Generates comparison reports** - Understand trade-offs empirically

**The result**: Empirical comparison of real implementations in a fraction of the time.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
make parallel-explore \
  NAME=rate-limiter \
  VARIANTS='{"functional":"pure functions","oop":"classes with SOLID"}'
```

The tool will:
1. Create isolated worktrees for each variant
2. Spawn parallel Claude sessions with ultrathink
3. Monitor progress and save results
4. Generate comparison report
5. Leave implementations ready to review

### Your First Exploration

1. **Define your task**:
```bash
TASK="Implement a rate limiter for API requests"
```

2. **Choose approaches to compare**:
```bash
VARIANTS='{
  "token-bucket":"Token bucket algorithm with refill rate",
  "sliding-window":"Sliding window with Redis backend",
  "fixed-window":"Fixed window counters (simple)"
}'
```

3. **Run the exploration**:
```bash
make parallel-explore \
  NAME=rate-limiter \
  VARIANTS='{"token-bucket":"Token bucket algorithm","sliding-window":"Sliding window with Redis","fixed-window":"Simple fixed window"}'
```

4. **Review results** in `.data/parallel_explorer/rate-limiter/`

## Usage Examples

### Basic: Comparing Paradigms

```bash
make parallel-explore \
  NAME=auth-system \
  VARIANTS='{
    "functional":"Pure functions with immutable state",
    "oop":"Classes with SOLID principles",
    "procedural":"Simple procedural approach"
  }'
```

**What happens**:
- Creates 3 worktrees for isolated development
- Spawns 3 Claude sessions in parallel
- Each implements the auth system differently
- Generates comparison showing trade-offs
- All implementations saved for review

### Advanced: Architecture Trade-offs

```bash
make parallel-explore \
  NAME=caching \
  VARIANTS='{
    "simple":"In-memory dictionary with no eviction",
    "lru":"LRU eviction with configurable size limits",
    "redis":"Distributed Redis cache with TTL"
  }'
```

**What happens**:
- Same parallel workflow
- Each variant explores different complexity levels
- Results show performance vs complexity trade-offs
- Real code to evaluate, not just theory

### Algorithm Comparison

```bash
make parallel-explore \
  NAME=search \
  VARIANTS='{
    "binary-tree":"Binary search tree implementation",
    "hash-table":"Hash table with collision handling",
    "trie":"Prefix tree for string searching"
  }'
```

**What happens**:
- Three different data structures implemented
- Each optimized for different use cases
- Compare actual code complexity and performance
- Understand when to use each approach

## How It Works

### The Pipeline

```
Your Task + Variations
         ↓
[Create Worktrees]
         ↓
[Load Ultrathink Instructions]
         ↓
[Spawn Parallel Claude Sessions]
         ↓
[Monitor & Save Progress]
         ↓
[Generate Comparison Report]
         ↓
    Results
```

### Key Components

- **WorktreeManager**: Creates isolated git worktrees for each variant
- **ParallelOrchestrator**: Coordinates parallel Claude sessions with real CCSDK
- **ExperimentPaths**: Manages file locations in `.data/` directory
- **Defensive Utilities**: Handles LLM failures gracefully with retry logic

### Why It Works

**Code handles the structure**:
- Worktree creation and management
- Parallel session orchestration
- Progress tracking and state management
- Result aggregation and reporting

**AI handles the intelligence**:
- Understanding task requirements
- Implementing different approaches
- Making design decisions
- Evaluating trade-offs

This separation means the tool is both reliable (structured code) and creative (AI implementation).

## Results Location

All experiment data goes to:
```
.data/parallel_explorer/{experiment-name}/
├── progress.json               # Overall progress tracking
├── summary.md                  # Comparison report
└── variants/
    ├── functional.json         # Variant-specific results
    ├── oop.json
    └── reactive.json
```

Worktrees with actual code:
```
.data/parallel_explorer/{experiment-name}/worktrees/
├── functional/                 # Full git worktree
├── oop/
└── reactive/
```

## Cleanup

```bash
# Remove experiment data and worktrees
make parallel-explore-cleanup NAME=rate-limiter

# Or use Python
from scenarios.parallel_explorer import cleanup_experiment
cleanup_experiment("rate-limiter")
```

## Configuration

### Command-Line Options

```python
# From Python with custom options
from scenarios.parallel_explorer import run_parallel_experiment

await run_parallel_experiment(
    name="my-experiment",
    variants={"v1": "approach 1", "v2": "approach 2"},
    max_parallel=3,  # Limit concurrent sessions
    base_branch="main"  # Branch to create worktrees from
)
```

### Make Options

```bash
# All options
make parallel-explore \
  NAME=experiment \
  VARIANTS='{"v1":"desc1","v2":"desc2"}' \
  MAX_PARALLEL=3 \
  BASE_BRANCH=main
```

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Create your own parallel explorations
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework powering this
- **[Scenario Tools](../)** - More tools like this

## What's Next?

This tool demonstrates parallel exploration with Amplifier:

1. **Use it** - Compare implementation approaches empirically
2. **Learn from it** - See how parallel exploration accelerates learning
3. **Build your own** - Apply this pattern to other exploration tasks
4. **Share back** - Let others learn from your experiments!

---

**Built with minimal input using Amplifier** - Parallel exploration through structured orchestration and real CCSDK integration.