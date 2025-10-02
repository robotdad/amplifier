"""Git worktree manager for parallel experiments.

Manages creation, listing, and cleanup of git worktrees for isolated parallel experiments.
Each experiment gets its own set of worktrees for different variants.
"""

import logging
import subprocess
from pathlib import Path

from scenarios.parallel_explorer.paths import ExperimentPaths

logger = logging.getLogger(__name__)


class WorktreeManager:
    """Manages git worktrees for parallel experiments.

    Creates and manages worktrees in .data/parallel_explorer/{experiment_name}/worktrees/{variant}/
    structure for isolated parallel development.
    """

    def __init__(self, experiment_name: str, repo_root: Path = Path.cwd()):
        """Initialize worktree manager for an experiment.

        Args:
            experiment_name: Experiment identifier (e.g., "feature-auth")
            repo_root: Root of the git repository (defaults to current directory)
        """
        self.experiment_name = experiment_name
        self.repo_root = repo_root.resolve()
        self.paths = ExperimentPaths(experiment_name)

        # Ensure worktree directory exists
        self.paths.ensure_directories()

        logger.info(f"WorktreeManager initialized for experiment: {experiment_name}")
        logger.debug(f"Repository root: {self.repo_root}")
        logger.debug(f"Worktrees directory: {self.paths.worktrees_dir}")

    def create_worktrees(self, variants: list[str], base_branch: str = "main") -> list[Path]:
        """Create worktrees for each variant.

        Creates git worktrees for each variant in the experiment, based on the
        specified base branch. Skips worktrees that already exist.

        Args:
            variants: List of variant identifiers (e.g., ["simple", "robust"])
            base_branch: Branch to create worktrees from (default: "main")

        Returns:
            List of paths to created/existing worktrees
        """
        worktree_paths = []

        # Use current branch if not on main
        current_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        # If we're not on main, use the current branch as base
        if base_branch == "main" and current_branch != "main":
            logger.info(f"Using current branch '{current_branch}' as base instead of 'main'")
            base_branch = current_branch

        for variant in variants:
            worktree_path = self.get_worktree_path(variant)

            # Check if worktree already exists
            if worktree_path.exists() and (worktree_path / ".git").exists():
                logger.info(f"Worktree already exists: {worktree_path}")
                worktree_paths.append(worktree_path)
                continue

            # Create parent directory if needed
            worktree_path.parent.mkdir(parents=True, exist_ok=True)

            # Create the worktree
            branch_name = f"{self.experiment_name}-{variant}"
            cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch]

            try:
                logger.info(f"Creating worktree: {worktree_path}")
                logger.debug(f"Command: {' '.join(cmd)}")
                result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
                logger.debug(f"Git output: {result.stdout}")
                worktree_paths.append(worktree_path)

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create worktree for {variant}: {e.stderr}")
                # Try to create without new branch (in case branch already exists)
                cmd_no_branch = ["git", "worktree", "add", str(worktree_path), base_branch]
                try:
                    logger.info("Retrying without creating new branch...")
                    result = subprocess.run(
                        cmd_no_branch, cwd=self.repo_root, capture_output=True, text=True, check=True
                    )
                    logger.debug(f"Git output: {result.stdout}")
                    worktree_paths.append(worktree_path)
                except subprocess.CalledProcessError as e2:
                    logger.error(f"Also failed without new branch: {e2.stderr}")
                    # Continue with other variants
                    continue

        return worktree_paths

    def cleanup_worktrees(self) -> None:
        """Remove all worktrees for this experiment."""
        if not self.paths.worktrees_dir.exists():
            logger.info("No worktrees directory to clean up")
            return

        for worktree_path in self.paths.worktrees_dir.iterdir():
            if worktree_path.is_dir():
                try:
                    logger.info(f"Removing worktree: {worktree_path}")
                    subprocess.run(
                        ["git", "worktree", "remove", str(worktree_path), "--force"],
                        cwd=self.repo_root,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to remove worktree {worktree_path}: {e.stderr}")

        # Clean up empty worktrees directory
        try:
            self.paths.worktrees_dir.rmdir()
            logger.info(f"Removed worktrees directory: {self.paths.worktrees_dir}")
        except OSError:
            pass  # Directory not empty or doesn't exist

    def get_worktree_path(self, variant: str) -> Path:
        """Get path for a specific variant's worktree.

        Args:
            variant: Variant identifier (e.g., "simple")

        Returns:
            Path object for the worktree location
        """
        return self.paths.variant_worktree_path(variant)
