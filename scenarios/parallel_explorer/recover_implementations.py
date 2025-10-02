#!/usr/bin/env python3
"""
Recovery script for parallel explorer experiments.

This script helps recover implementations from worktrees when experiments fail
to copy implementations back to the main scenarios directory.
"""

import shutil
import sys
from pathlib import Path


def recover_implementations(experiment_name: str, dry_run: bool = True):
    """Recover implementations from worktrees to scenarios directory.

    Args:
        experiment_name: Name of the experiment
        dry_run: If True, only show what would be copied without actually doing it
    """
    from scenarios.parallel_explorer.paths import ExperimentPaths

    paths = ExperimentPaths(experiment_name)

    if not paths.worktrees_dir.exists():
        print(f"No worktrees directory found at {paths.worktrees_dir}")
        return

    print(f"Recovering implementations from: {paths.worktrees_dir}")
    print(f"Mode: {'DRY RUN' if dry_run else 'ACTUAL COPY'}")
    print("-" * 60)

    recovered = 0
    failed = 0

    # Check each worktree
    for worktree_path in paths.worktrees_dir.iterdir():
        if not worktree_path.is_dir():
            continue

        variant_name = worktree_path.name
        print(f"\nVariant: {variant_name}")

        # Look for implementation directories
        scenarios_dir = worktree_path / "scenarios"
        if not scenarios_dir.exists():
            print("  ❌ No scenarios directory found")
            failed += 1
            continue

        # Find content_engine implementations
        for impl_dir in scenarios_dir.iterdir():
            if impl_dir.is_dir() and impl_dir.name.startswith("content_engine"):
                # Check if it has actual content
                py_files = list(impl_dir.glob("*.py"))
                if not py_files:
                    print(f"  ⚠️  {impl_dir.name} exists but has no Python files")
                    continue

                # Destination in main scenarios
                dest_dir = Path.cwd() / "scenarios" / impl_dir.name

                if dest_dir.exists():
                    print(f"  ⚠️  Destination already exists: {dest_dir}")
                    print("     Skipping to avoid overwrite")
                    continue

                print(f"  ✅ Found implementation: {impl_dir.name}")
                print(f"     {len(py_files)} Python files")
                print(f"     Would copy to: {dest_dir}")

                if not dry_run:
                    try:
                        shutil.copytree(impl_dir, dest_dir)
                        print("     ✓ Copied successfully")
                        recovered += 1
                    except Exception as e:
                        print(f"     ✗ Copy failed: {e}")
                        failed += 1
                else:
                    recovered += 1

    print("\n" + "=" * 60)
    print(f"Summary: {recovered} implementations {'would be' if dry_run else 'were'} recovered")
    if failed > 0:
        print(f"         {failed} variants had no implementations")

    if dry_run:
        print("\nRun with --execute to actually copy the implementations")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python recover_implementations.py <experiment-name> [--execute]")
        print("\nExample:")
        print("  python recover_implementations.py content-engine-exploration          # Dry run")
        print("  python recover_implementations.py content-engine-exploration --execute # Actually copy")
        sys.exit(1)

    experiment_name = sys.argv[1]
    dry_run = "--execute" not in sys.argv

    recover_implementations(experiment_name, dry_run)


if __name__ == "__main__":
    main()
