"""
Parallel Experiment Orchestrator

Run multiple implementation approaches in parallel to explore solution spaces.

This module provides tools for:
- Creating isolated git worktrees for experiments
- Running parallel Claude Code SDK sessions with different variations
- Monitoring progress and aggregating results
- Loading fresh ultrathink instructions from source
- Full CCSDK integration for real Claude sessions

Example:
    >>> from scenarios.parallel_explorer import run_parallel_experiment
    >>>
    >>> variants = {
    ...     "functional": "Use pure functions and immutability",
    ...     "oop": "Use classes with SOLID principles"
    ... }
    >>>
    >>> results = await run_parallel_experiment(
    ...     name="rate-limiter",
    ...     variants=variants
    ... )

Each variant runs in a real Claude session with ultrathink methodology.
See README.md for detailed usage and architecture.
"""

import asyncio
from pathlib import Path
from typing import Any

from scenarios.parallel_explorer.orchestrator import ExperimentResult
from scenarios.parallel_explorer.orchestrator import ParallelOrchestrator
from scenarios.parallel_explorer.worktree_manager import WorktreeManager

__version__ = "0.1.0"

__all__ = [
    "WorktreeManager",
    "ParallelOrchestrator",
    "ExperimentResult",
    "run_parallel_experiment",
    "run_from_saved_context",
    "list_experiments",
    "cleanup_experiment",
]


async def run_parallel_experiment(
    name: str,
    variants: dict[str, str],
    max_parallel: int = 3,
    timeout_minutes: int = 30,
) -> dict[str, Any]:
    """
    High-level API for running parallel experiments.

    Args:
        name: Experiment identifier (used for directories and tracking)
        variants: Dictionary mapping variant names to task variations
                 Example: {"functional": "use pure functions", "oop": "use classes"}
        max_parallel: Maximum number of concurrent sessions (default: 3)
        timeout_minutes: Timeout per variant in minutes (default: 30)

    Returns:
        Dictionary of results keyed by variant name, plus summary

    Example:
        >>> results = await run_parallel_experiment(
        ...     name="auth-system",
        ...     variants={
        ...         "simple": "Basic authentication with sessions",
        ...         "jwt": "JWT-based stateless authentication",
        ...         "oauth": "OAuth2 with external providers"
        ...     },
        ...     max_parallel=2
        ... )
        >>> print(results["summary"])
    """
    orchestrator = ParallelOrchestrator(name)

    try:
        results = await orchestrator.run_experiment(
            variants=variants,
            max_parallel=max_parallel,
            timeout_minutes=timeout_minutes,
        )

        # Generate summary
        summary = orchestrator.aggregate_results()

        return {
            "variants": results,
            "summary": summary,
            "experiment_name": name,
        }

    except Exception as e:
        # Save error state and return partial results
        orchestrator.save_progress("_experiment", "failed", {"error": str(e)})
        raise


def list_experiments() -> list[str]:
    """
    List all experiments with saved results.

    Returns:
        List of experiment names (directory names in data/parallel_experiments/)

    Example:
        >>> experiments = list_experiments()
        >>> print(f"Found {len(experiments)} experiments")
        >>> for exp in experiments:
        ...     print(f"  - {exp}")
    """
    from amplifier.config.paths import paths

    experiments_dir = paths.data_dir / "parallel_explorer"

    if not experiments_dir.exists():
        return []

    return [d.name for d in experiments_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]


def cleanup_experiment(name: str, remove_data: bool = True) -> None:
    """
    Remove worktrees and optionally data for an experiment.

    Args:
        name: Experiment name to clean up
        remove_data: If True, also remove data directory (default: True)

    Example:
        >>> cleanup_experiment("old-experiment")  # Remove everything
        >>> cleanup_experiment("keep-data", remove_data=False)  # Keep results

    Note:
        This removes git worktrees and optionally the data directory.
        Use with caution - operation cannot be undone.
    """
    import shutil

    from amplifier.config.paths import paths

    # Clean up worktrees
    manager = WorktreeManager(name)
    manager.cleanup_worktrees()

    # Optionally remove data directory
    if remove_data:
        data_dir = paths.data_dir / "parallel_explorer" / name
        if data_dir.exists():
            shutil.rmtree(data_dir)
            print(f"Removed data directory: {data_dir}")


# Convenience function for synchronous contexts
def run_parallel_experiment_sync(
    name: str,
    variants: dict[str, str],
    max_parallel: int = 3,
    timeout_minutes: int = 30,
) -> dict[str, Any]:
    """
    Synchronous wrapper for run_parallel_experiment.

    Use this when calling from non-async code.

    Example:
        >>> results = run_parallel_experiment_sync(
        ...     name="my-experiment",
        ...     variants={"v1": "approach 1", "v2": "approach 2"}
        ... )
    """
    return asyncio.run(run_parallel_experiment(name, variants, max_parallel, timeout_minutes))


def run_from_saved_context(
    name: str,
    max_parallel: int = 3,
    timeout_minutes: int = 30,
) -> dict[str, Any]:
    """
    Run a parallel experiment using saved context from /explore-variants.

    Args:
        name: Experiment name (must have context.json saved)
        max_parallel: Maximum number of concurrent sessions (default: 3)
        timeout_minutes: Timeout per variant in minutes (default: 30)

    Returns:
        Dictionary of results keyed by variant name, plus summary

    Example:
        >>> # First save context with /explore-variants
        >>> # Then run:
        >>> results = run_from_saved_context("content-engine")
    """
    import json

    from amplifier.config.paths import paths

    # Load saved context
    context_file = paths.data_dir / "parallel_explorer" / name / "context.json"
    if not context_file.exists():
        raise FileNotFoundError(f"No saved context found at {context_file}. Use /explore-variants first.")

    with open(context_file) as f:
        context = json.load(f)

    # Extract variants from context
    variants = {}
    for variant_name, variant_info in context["variants"].items():
        # Use the description as the base prompt
        variants[variant_name] = variant_info.get("description", variant_name)

    # Run the experiment with the loaded variants
    return run_parallel_experiment_sync(name, variants, max_parallel, timeout_minutes)
