# Parallel Orchestration Architecture - Path 1: Full SDK Automation

**Status**: Alternative approach (not implemented)
**Date**: 2025-10-01
**Context**: Documented for future reference while implementing Path 3 (Hybrid approach)

## Overview

Path 1 represents full automation using Claude Code SDK (CCSDK) with extracted ultrathink logic. This approach prioritizes automation and clean SDK integration over using the actual `/ultrathink-task` slash command.

## Architecture

```
User in Claude Code → /parallel-experiment command (interactive)
                    ↓
                Gathers requirements via conversation
                    ↓
            Launches Python CCSDK tool
                    ↓
        Creates N worktrees + N async SDK sessions
                    ↓
    Each session uses extracted ultrathink prompt
                    ↓
            Monitors & reports results
```

## Implementation Design

### Module Structure

```
amplifier/ccsdk_toolkit/parallel_experiment/
├── __init__.py
├── orchestrator.py       # Main parallel execution logic
├── worktree_manager.py   # Git worktree operations
├── variation_generator.py # Generate approach descriptions
└── result_aggregator.py  # Collect and compare results
```

### Core Orchestrator

```python
# amplifier/ccsdk_toolkit/parallel_experiment/orchestrator.py
import asyncio
from pathlib import Path
from typing import List
from amplifier.ccsdk_toolkit import ClaudeSession

class ParallelExperiment:
    """Orchestrate parallel Claude sessions for exploring variations"""

    def __init__(self):
        # Extract ultrathink prompt once at initialization
        self.ultrathink_prompt = self._load_ultrathink_prompt()

    def _load_ultrathink_prompt(self) -> str:
        """Extract ultrathink instructions from slash command"""
        command_path = Path(".claude/commands/ultrathink-task.md")
        if command_path.exists():
            return command_path.read_text()
        else:
            # Fallback to embedded ultrathink logic
            return self._get_default_ultrathink_prompt()

    async def run_variant(
        self,
        worktree: str,
        base_task: str,
        variation: str
    ) -> dict:
        """Run one experiment variant using SDK"""
        session = ClaudeSession(
            system_prompt=self.ultrathink_prompt,
            working_directory=worktree
        )

        full_task = f"""
        Base Task: {base_task}

        Your Approach: {variation}

        Please implement this task using the approach described above.
        Apply ultrathink methodology throughout.
        """

        response = await session.send_message(full_task)

        # Save completion marker
        completion_file = Path(worktree) / "DONE.md"
        completion_file.write_text(response.text)

        return {
            "worktree": worktree,
            "variation": variation,
            "response": response.text,
            "files_created": self._count_files_created(worktree),
        }

    async def orchestrate(
        self,
        base_task: str,
        variations: List[str]
    ) -> List[dict]:
        """Run all variants in parallel"""
        # Create worktrees
        worktrees = []
        for i, variation in enumerate(variations):
            worktree = self._create_worktree(f"exp-{i}")
            worktrees.append(worktree)

        print(f"Created {len(worktrees)} worktrees")
        print(f"Launching {len(variations)} parallel experiments...")

        # Launch parallel SDK sessions
        tasks = [
            self.run_variant(wt, base_task, var)
            for wt, var in zip(worktrees, variations)
        ]

        # Execute in parallel with progress updates
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate and report
        return self._aggregate_results(results)

    def _create_worktree(self, name: str) -> str:
        """Create git worktree using subprocess"""
        # Implementation delegates to git commands
        pass

    def _count_files_created(self, worktree: str) -> int:
        """Count files created/modified in worktree"""
        # Implementation uses git status
        pass

    def _aggregate_results(self, results: List[dict]) -> dict:
        """Aggregate results into comparison report"""
        pass
```

### Variation Generator

```python
# amplifier/ccsdk_toolkit/parallel_experiment/variation_generator.py

async def generate_variations(base_task: str, count: int) -> List[str]:
    """Use Claude to generate N distinct approaches"""
    session = ClaudeSession()

    prompt = f"""
    Generate {count} distinctly different implementation approaches for:
    {base_task}

    For each approach, provide:
    1. Name (e.g., "Functional Approach", "Event-Driven")
    2. Description of the approach
    3. Key implementation guidelines

    Make each approach genuinely different in philosophy and technique.
    """

    response = await session.send_message(prompt)
    return parse_variations(response.text)
```

### Claude Code Command

```markdown
<!-- .claude/commands/parallel-experiment.md -->
# Parallel Experiment

I'll help you explore multiple implementation approaches in parallel.

## Setup

Let me gather some information:

1. **What task would you like to explore?**
   Please describe the implementation task clearly.

2. **How many variations would you like?**
   Recommended: 3-5 different approaches

3. **Any specific approaches you want included?**
   (e.g., "functional", "OOP", "reactive", "event-driven")

## Execution

Based on your input, I'll:
- Generate {N} distinct implementation approaches
- Create {N} isolated worktrees
- Launch {N} parallel Claude SDK sessions
- Monitor progress and aggregate results

## Example

Task: "Implement a rate limiter"
Variations: 3
Approaches: Auto-generated or specified

Result: 3 parallel implementations exploring different techniques
```

## Advantages

### ✅ Fully Automated
- No manual steps required
- User types command, gets results
- Progress monitoring built-in

### ✅ True Parallelism
- Multiple asyncio tasks run concurrently
- Efficient use of API calls
- Results collected automatically

### ✅ Clean SDK Integration
- Uses CCSDK patterns throughout
- Follows amplifier toolkit conventions
- Easy to extend and maintain

### ✅ Deterministic Execution
- Predictable behavior
- Robust error handling
- Progress checkpoints

## Disadvantages

### ❌ Not Using Actual Slash Command
- Extracts prompt text, doesn't invoke `/ultrathink-task`
- If slash command updates, must manually sync
- Loses the "command invocation" semantics

### ❌ Requires SDK Session Support for Working Directory
- Need to verify SDK can change working directory per session
- May need workarounds if not supported

### ❌ One-time Extraction
- Ultrathink prompt extracted at initialization
- Changes to slash command not picked up mid-run
- Requires tool restart to get updates

## Implementation Effort

**Estimated Complexity**: Medium

**Components to Build**:
1. Orchestrator core (asyncio parallel execution) - 200 lines
2. Worktree manager (git operations) - 100 lines
3. Variation generator (Claude API calls) - 50 lines
4. Result aggregator (comparison logic) - 100 lines
5. Claude Code command (markdown) - 50 lines

**Total**: ~500 lines of code

## When to Use Path 1

Consider this approach when:
- Full automation is the top priority
- OK with extracted prompt vs command invocation
- Want clean SDK-based architecture
- Planning to extend with more features
- Comfortable with asyncio patterns

## Why Path 3 Was Chosen Instead

Path 3 (Hybrid approach) was selected because it:
- Loads ultrathink instructions fresh from source
- Guarantees using latest command content
- Maintains determinism of instruction set
- Still provides full automation
- Better aligns with "use the command" requirement

## Migration Path

If Path 3 proves insufficient, migrating to Path 1 involves:
1. Remove dynamic loading of slash command file
2. Extract prompt once at initialization
3. Add caching mechanism
4. Update documentation

Migration effort: ~4 hours

## References

- Original parallel-prototype-testing repo analysis
- amplifier-cli-architect recommendations
- CCSDK toolkit patterns
- asyncio parallel execution patterns

## Related Documents

- `ai_working/decisions/` - Architectural decision records
- `amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md` - CCSDK patterns
- `.claude/commands/ultrathink-task.md` - Source of ultrathink logic
