"""Git worktree manager for parallel experiments.

Manages creation, listing, and cleanup of git worktrees for isolated parallel experiments.
Each experiment gets its own set of worktrees for different variants.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class WorktreeManager:
    """Manages git worktrees for parallel experiments.

    Creates and manages worktrees in ../amplifier-experiments/{base_name}/{variant}/
    structure for isolated parallel development.
    """

    def __init__(self, base_name: str, repo_root: Path = Path.cwd()):
        """Initialize worktree manager for an experiment.

        Args:
            base_name: Experiment identifier (e.g., "feature-auth")
            repo_root: Root of the git repository (defaults to current directory)
        """
        self.base_name = base_name
        self.repo_root = repo_root.resolve()
        self.experiments_root = self.repo_root.parent / "amplifier-experiments"
        self.experiment_dir = self.experiments_root / base_name

        logger.info(f"WorktreeManager initialized for experiment: {base_name}")
        logger.debug(f"Repository root: {self.repo_root}")
        logger.debug(f"Experiments directory: {self.experiments_root}")

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

        for variant in variants:
            worktree_path = self.get_worktree_path(variant)

            # Check if worktree already exists
            if worktree_path.exists():
                logger.info(f"Worktree already exists: {worktree_path}")
                worktree_paths.append(worktree_path)
                continue

            # Create parent directory if needed
            worktree_path.parent.mkdir(parents=True, exist_ok=True)

            # Create the worktree
            branch_name = f"{self.base_name}-{variant}"
            cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch]

            try:
                logger.info(f"Creating worktree: {worktree_path}")
                result = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True, check=True)
                logger.debug(f"Git output: {result.stdout}")
                worktree_paths.append(worktree_path)

            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create worktree for {variant}: {e.stderr}")
                # Continue with other variants
                continue

        return worktree_paths

    def list_worktrees(self) -> list[dict[str, str]]:
        """List all worktrees for this experiment.

        Returns:
            List of dictionaries with worktree information:
            - path: Absolute path to worktree
            - branch: Branch name
            - variant: Variant identifier
        """
        worktrees = []

        try:
            # Get all worktrees from git
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse git worktree output
            current_worktree = {}
            for line in result.stdout.strip().split("\n"):
                if line.startswith("worktree "):
                    if current_worktree:
                        # Check if this worktree belongs to our experiment
                        path = Path(current_worktree.get("path", ""))
                        if self.experiment_dir in path.parents:
                            variant = path.name
                            current_worktree["variant"] = variant
                            worktrees.append(current_worktree)
                    current_worktree = {"path": line[9:]}
                elif line.startswith("branch "):
                    current_worktree["branch"] = line[7:]
                elif not line:
                    # Empty line marks end of worktree entry
                    if current_worktree:
                        path = Path(current_worktree.get("path", ""))
                        if self.experiment_dir in path.parents:
                            variant = path.name
                            current_worktree["variant"] = variant
                            worktrees.append(current_worktree)
                    current_worktree = {}

            # Handle last worktree if any
            if current_worktree:
                path = Path(current_worktree.get("path", ""))
                if self.experiment_dir in path.parents:
                    variant = path.name
                    current_worktree["variant"] = variant
                    worktrees.append(current_worktree)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list worktrees: {e.stderr}")

        return worktrees

    def cleanup_worktrees(self) -> None:
        """Remove all worktrees for this experiment.

        Removes all git worktrees associated with this experiment and
        deletes the experiment directory.
        """
        worktrees = self.list_worktrees()

        for worktree in worktrees:
            path = worktree["path"]
            try:
                logger.info(f"Removing worktree: {path}")
                subprocess.run(
                    ["git", "worktree", "remove", path, "--force"],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to remove worktree {path}: {e.stderr}")

        # Clean up experiment directory if empty
        if self.experiment_dir.exists():
            try:
                self.experiment_dir.rmdir()
                logger.info(f"Removed experiment directory: {self.experiment_dir}")
            except OSError:
                logger.debug(f"Experiment directory not empty: {self.experiment_dir}")

    def get_worktree_path(self, variant: str) -> Path:
        """Get path for a specific variant's worktree.

        Args:
            variant: Variant identifier (e.g., "simple")

        Returns:
            Path object for the worktree location
        """
        return self.experiment_dir / variant
