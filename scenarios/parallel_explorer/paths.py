"""Path resolver for parallel experiments.

This module provides centralized path resolution for all parallel experiment
files, ensuring consistent data organization under .data/parallel_explorer/.
"""

from dataclasses import dataclass
from pathlib import Path

from amplifier.config.paths import paths


@dataclass
class ExperimentPaths:
    """Path resolver for parallel experiments.

    All experiment data goes in .data/parallel_explorer/{experiment_name}/
    This includes worktrees, results, and state files.

    Args:
        experiment_name: Unique identifier for the experiment

    Example:
        >>> paths = ExperimentPaths("rate-limiter-exploration")
        >>> paths.ensure_directories()
        >>> worktree = paths.variant_worktree_path("functional")
        >>> # Returns: .data/parallel_explorer/rate-limiter-exploration/worktrees/functional
    """

    experiment_name: str

    @property
    def base_dir(self) -> Path:
        """Base directory for this experiment.

        Returns:
            Path to .data/parallel_explorer/{experiment_name}/
        """
        return paths.data_dir / "parallel_explorer" / self.experiment_name

    @property
    def results_dir(self) -> Path:
        """Directory for variant results.

        Returns:
            Path to {base_dir}/results/
        """
        return self.base_dir / "results"

    @property
    def worktrees_dir(self) -> Path:
        """Directory for git worktrees.

        Returns:
            Path to {base_dir}/worktrees/
        """
        return self.base_dir / "worktrees"

    def variant_worktree_path(self, variant_name: str) -> Path:
        """Path to a specific variant's worktree.

        Args:
            variant_name: Name of the variant

        Returns:
            Path to {worktrees_dir}/{variant_name}/
        """
        return self.worktrees_dir / variant_name

    def variant_result_path(self, variant_name: str) -> Path:
        """Path to a specific variant's result file.

        Args:
            variant_name: Name of the variant

        Returns:
            Path to {results_dir}/{variant_name}.json
        """
        return self.results_dir / f"{variant_name}.json"

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist.

        Creates:
            - base_dir
            - results_dir
            - worktrees_dir
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        self.worktrees_dir.mkdir(exist_ok=True)
