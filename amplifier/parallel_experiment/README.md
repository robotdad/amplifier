# Parallel Experiment Orchestrator

**Purpose**: Run multiple implementation approaches in parallel to explore solution spaces efficiently.

**Pattern**: Hybrid automation (Path 3) - Fresh instruction loading with full SDK automation

## Architecture

This module provides a clean, modular system for running parallel experiments:

```
User → Claude Code Command → ParallelOrchestrator
                                    ↓
                    Creates N worktrees (WorktreeManager)
                                    ↓
                    Spawns N async Claude sessions
                                    ↓
                Each loads fresh ultrathink instructions
                                    ↓
                    Monitors & aggregates results
```

## Modules (Bricks)

### worktree_manager.py
**Purpose**: Manages git worktrees for isolated experiments

**Contract**:
- Inputs: experiment name, variant names, base branch
- Outputs: worktree paths
- Side Effects: Creates git worktrees, modifies filesystem

### orchestrator.py
**Purpose**: Coordinates parallel execution and aggregates results

**Contract**:
- Inputs: experiment name, variants (name → task variation)
- Outputs: results dictionary, markdown summary
- Side Effects: Creates Claude sessions, saves progress, writes results

## Usage

### From Python

```python
from amplifier.parallel_experiment import run_parallel_experiment

# Define variations
variants = {
    "functional": "Implement using pure functions and immutability",
    "oop": "Implement using classes with SOLID principles",
    "reactive": "Implement using event-driven reactive patterns"
}

# Run experiment
results = await run_parallel_experiment(
    name="rate-limiter-exploration",
    variants=variants,
    max_parallel=3
)

# Results include paths to worktrees and summaries
for variant, result in results.items():
    print(f"{variant}: {result.status}")
    print(f"  Path: {result.worktree_path}")
    print(f"  Metrics: {result.metrics}")
```

### From Claude Code

```
/parallel-experiment rate-limiter functional:pure-functions oop:solid-classes reactive:events
```

### From Make

```bash
make parallel-experiment NAME=auth VARIANTS='{"simple":"basic impl","robust":"production-ready"}'
```

## Key Features

### ✅ Fresh Instruction Loading
- Loads `.claude/commands/ultrathink-task.md` on each variant execution
- Guarantees using latest command content
- No stale instruction caching

### ✅ Parallel Execution
- True async parallelism via asyncio
- Configurable concurrency limit
- Progress tracking per variant

### ✅ Robust State Management
- Saves progress after every operation
- Recoverable from failures
- Preserves partial results

### ✅ Clean Separation
- Each variant in isolated git worktree
- No cross-contamination of experiments
- Easy comparison of approaches

## File Structure

```
amplifier/data/parallel_experiments/
└── {experiment_name}/
    ├── progress.json          # Current state
    ├── summary.md            # Results summary
    └── variants/
        ├── functional.json   # Per-variant results
        ├── oop.json
        └── reactive.json
```

## Data Directory

Progress and results saved to:
```
amplifier/data/parallel_experiments/{experiment_name}/
```

Worktrees created at:
```
../amplifier-experiments/{experiment_name}/{variant}/
```

## Module Design Principles

Following amplifier philosophy:

### Ruthless Simplicity
- Direct subprocess calls to git (no gitpython dependency)
- Simple JSON for state (no database)
- File-based coordination (no complex event system)
- ~500 lines total across all modules

### Modular Design
- Clear "bricks and studs" architecture
- Each module independently testable
- Regeneratable components with stable contracts

### Graceful Degradation
- Continues with other variants if one fails
- Saves partial results always
- Clear error messages and logging

## Real Claude SDK Integration

The orchestrator uses the full Claude Code SDK (CCSDK) for real parallel sessions:

```python
# Real implementation in orchestrator.py
async def run_variant(self, ...):
    from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions

    # Load fresh ultrathink instructions
    instructions = self.load_ultrathink_instructions()

    # Create real Claude session
    options = SessionOptions(system_prompt=instructions, max_turns=20)
    async with ClaudeSession(options) as session:
        response = await session.query(task_prompt)
        return process_response(response)
```

Each variant runs in a real Claude session with ultrathink methodology applied.

## Testing

### Unit Tests
```bash
# Test worktree operations
pytest tests/test_worktree_manager.py

# Test orchestration logic
pytest tests/test_orchestrator.py
```

### Integration Test
```bash
# Run end-to-end with mock
make parallel-experiment NAME=test VARIANTS='{"v1":"simple","v2":"complex"}'

# Monitor progress
tail -f amplifier/data/parallel_experiments/test/progress.json

# View results
cat amplifier/data/parallel_experiments/test/summary.md
```

## Extension Points

### Custom Variation Generators
```python
from amplifier.parallel_experiment.orchestrator import ParallelOrchestrator

class CustomOrchestrator(ParallelOrchestrator):
    def generate_variations(self, base_task: str, count: int):
        """Custom logic to generate variations"""
        # Use Claude to generate, or load from templates
        pass
```

### Custom Result Aggregators
```python
def custom_aggregator(results: dict) -> str:
    """Custom aggregation logic"""
    # Generate visualizations, charts, comparisons
    pass

orchestrator.aggregate_results = custom_aggregator
```

## Future Enhancements

Potential additions (not in MVP):
- Real-time progress streaming to UI
- Automatic result visualization
- Integration with knowledge synthesis
- Multi-repo experiments
- Comparison tooling

## Dependencies

### Required
- Python 3.11+
- git
- asyncio (built-in)
- Claude Code SDK (claude-code-sdk)
- Claude CLI installed and configured

### Optional
- amplifier.utils.file_io (for robust writes)

## Philosophy Alignment

This module embodies:
- **Trust in emergence**: Multiple approaches reveal optimal patterns
- **Present-moment focus**: Solves current exploration needs simply
- **Ruthless simplicity**: No unnecessary abstractions
- **Modular design**: Clear bricks with defined interfaces

## References

- `ai_working/parallel_orchestration_path1.md` - Alternative approach
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md` - Design principles
- `ai_context/MODULAR_DESIGN_PHILOSOPHY.md` - Modular patterns
- Original inspiration: `parallel-prototype-testing` repository
