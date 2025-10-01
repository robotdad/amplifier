# Parallel Experiment

Run multiple implementation approaches in parallel to explore solution spaces and compare different strategies.

## What This Does

This command helps you:
1. **Explore multiple approaches** simultaneously (functional, OOP, reactive, etc.)
2. **Create isolated worktrees** for each variation
3. **Run parallel Claude sessions** with ultrathink methodology
4. **Aggregate and compare results** automatically

## Usage

I'll guide you through setting up a parallel experiment. Here's what I need to know:

### 1. Experiment Name
What should we call this experiment? (Used for organizing worktrees and results)

Example: `rate-limiter-exploration`, `auth-system-variants`

### 2. Base Task
What's the core task you want to explore?

Example: "Implement a rate limiter for API requests"

### 3. Variations
What different approaches should we explore?

You can either:
- **Specify count**: "Generate 3 different approaches"
- **Name specific approaches**: "functional, OOP, event-driven"

## Interactive Setup

Let me gather the information we need:

**Question 1**: What name should we use for this experiment?

*Waiting for your response...*

---

After gathering all requirements, I'll:

1. ✅ Generate detailed approach descriptions for each variant
2. ✅ Create isolated git worktrees
3. ✅ Load fresh ultrathink instructions
4. ✅ Launch parallel Claude sessions
5. ✅ Monitor progress and save results
6. ✅ Generate comparison summary

## Example Session

```
You: /parallel-experiment
Me: What name should we use for this experiment?
You: rate-limiter-strategies
Me: What's the base task to explore?
You: Implement a rate limiter for API requests
Me: How many variations? (or name specific approaches)
You: 3 different approaches
Me: I'll generate 3 distinct implementation strategies...

[Generates approaches via Claude]

Approaches generated:
1. Token Bucket Algorithm
2. Sliding Window with Redis
3. Distributed Rate Limiting

Creating worktrees and launching experiments...

✅ Experiment started!

Worktrees created at:
- ../amplifier-experiments/rate-limiter-strategies/token-bucket/
- ../amplifier-experiments/rate-limiter-strategies/sliding-window/
- ../amplifier-experiments/rate-limiter-strategies/distributed/

Progress: amplifier/data/parallel_experiments/rate-limiter-strategies/
```

## Results

After completion, you'll get:

### Summary Report
Markdown comparison of all approaches:
- Implementation approach used
- Files created/modified
- Key design decisions
- Pros/cons of each approach

### Individual Results
Per-variant details in:
```
amplifier/data/parallel_experiments/{experiment_name}/
├── summary.md              # Overall comparison
├── progress.json           # Current status
└── variants/
    ├── variant1.json       # Detailed results
    ├── variant2.json
    └── variant3.json
```

### Worktrees
Navigate to any worktree to see the implementation:
```bash
cd ../amplifier-experiments/{experiment_name}/{variant}/
```

## Tips

**For Best Results:**
- Use clear, specific task descriptions
- Try genuinely different approaches (not minor variations)
- Let experiments run to completion for fair comparison
- Review all implementations before choosing one

**Recommended Variations:**
- Paradigms: functional vs OOP vs procedural
- Patterns: events vs callbacks vs async/await
- Complexity: simple vs robust vs optimized
- Architecture: monolithic vs modular vs microservices

## Technical Details

### What Happens Behind the Scenes

1. **Variation Generation**: Uses Claude to generate distinct approaches
2. **Worktree Creation**: Creates isolated git worktrees for each variant
3. **Instruction Loading**: Loads latest `/ultrathink-task` instructions
4. **Parallel Execution**: Spawns async Claude sessions (max 3 concurrent)
5. **Progress Tracking**: Saves state after each operation
6. **Result Aggregation**: Compiles comparison report

### Module Integration

This command uses:
- `amplifier.parallel_experiment.orchestrator` - Core orchestration
- `amplifier.parallel_experiment.worktree_manager` - Git worktree management
- Fresh ultrathink instructions from `.claude/commands/ultrathink-task.md`

## Cleanup

After reviewing results, clean up with:
```python
from amplifier.parallel_experiment import cleanup_experiment
cleanup_experiment("experiment-name")  # Removes worktrees and data
```

Or keep data for later reference:
```python
cleanup_experiment("experiment-name", remove_data=False)
```

## Philosophy

This tool embodies:
- **Trust in emergence**: Multiple approaches reveal optimal patterns
- **Empirical comparison**: Real implementations beat theoretical debates
- **Risk mitigation**: If one approach fails, others may succeed
- **Learning acceleration**: Parallel exploration maximizes learning velocity

---

Ready to start? Tell me the experiment name and I'll guide you through the rest!
