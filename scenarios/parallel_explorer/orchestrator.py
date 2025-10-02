"""
Orchestrator Module: Coordinates parallel Claude SDK sessions for experiments

This module manages the lifecycle of parallel experiments, running multiple
variants concurrently and aggregating results.

Contract:
  Inputs:
    - experiment_name: str (identifier for this experiment)
    - variants: Dict[str, str] (variant_name -> task_variation)
    - max_parallel: int = 3 (concurrent session limit)
    - timeout_minutes: int = 30 (per-variant timeout)

  Outputs:
    - Results dictionary: Dict[str, ExperimentResult]
    - Summary report: str (markdown formatted)

  Side Effects:
    - Creates Claude SDK sessions (REAL implementation)
    - Writes progress to .data/parallel_explorer/{name}/
    - Modifies worktree contents
    - Consumes API quota
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.defensive import parse_llm_json  # Extract JSON from any LLM response
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback  # Intelligent retry with error correction
from amplifier.ccsdk_toolkit.defensive import write_json_with_retry  # Cloud sync-aware file operations
from scenarios.parallel_explorer.paths import ExperimentPaths

logger = logging.getLogger(__name__)


@dataclass
class ExperimentResult:
    """Result data for a single experiment variant"""

    variant_name: str
    status: str  # "pending", "running", "completed", "failed"
    start_time: datetime
    end_time: datetime | None
    worktree_path: Path
    session_id: str | None
    output: str | None
    error: str | None
    metrics: dict[str, Any]  # Lines changed, files modified, etc.


class ParallelOrchestrator:
    """Orchestrates parallel experiment execution across worktrees"""

    def __init__(self, experiment_name: str):
        """Initialize orchestrator with experiment name

        Args:
            experiment_name: Identifier for this experiment
        """
        self.experiment_name = experiment_name
        self.paths = ExperimentPaths(experiment_name)
        self.results: dict[str, ExperimentResult] = {}
        self.semaphore: asyncio.Semaphore | None = None

        # Ensure directories exist
        self.paths.ensure_directories()
        logger.info(f"Initialized orchestrator for experiment: {experiment_name}")
        logger.debug(f"Data directory: {self.paths.base_dir}")

    def load_ultrathink_instructions(self) -> str:
        """Load instructions from .claude/commands/ultrathink-task.md

        Returns:
            Instructions content or error message if file not found
        """
        instruction_path = Path(".claude/commands/ultrathink-task.md")

        if not instruction_path.exists():
            logger.warning(f"Instructions file not found: {instruction_path}")
            return "# Instructions not found\n\nPlease create .claude/commands/ultrathink-task.md"

        try:
            with open(instruction_path, encoding="utf-8") as f:
                instructions = f.read()
                logger.debug(f"Loaded {len(instructions)} chars of instructions")
                return instructions
        except Exception as e:
            logger.error(f"Failed to load instructions: {e}")
            return f"# Error loading instructions\n\n{str(e)}"

    async def run_experiment(
        self, variants: dict[str, str], max_parallel: int = 3, timeout_minutes: int = 30
    ) -> dict[str, ExperimentResult]:
        """Main entry point - runs all variants and returns results

        Args:
            variants: Mapping of variant names to task variations
            max_parallel: Maximum concurrent sessions
            timeout_minutes: Timeout per variant

        Returns:
            Dictionary mapping variant names to results
        """
        logger.info(f"Starting experiment with {len(variants)} variants, max_parallel={max_parallel}")

        # Initialize semaphore for parallel control
        self.semaphore = asyncio.Semaphore(max_parallel)

        # Import worktree manager
        try:
            from scenarios.parallel_explorer.worktree_manager import WorktreeManager

            worktree_mgr = WorktreeManager(self.experiment_name)
        except ImportError:
            logger.error("WorktreeManager not found - using mock paths")
            worktree_mgr = None

        # Create tasks for each variant
        tasks = []
        for variant_name, task_variation in variants.items():
            # Get or create worktree path
            if worktree_mgr:
                worktree_path = worktree_mgr.get_worktree_path(variant_name)
                # Ensure the directory exists
                worktree_path.mkdir(parents=True, exist_ok=True)
            else:
                worktree_path = Path(f"/tmp/worktree_{variant_name}")
                worktree_path.mkdir(parents=True, exist_ok=True)

            # Create result object
            self.results[variant_name] = ExperimentResult(
                variant_name=variant_name,
                status="pending",
                start_time=datetime.now(),
                end_time=None,
                worktree_path=worktree_path,
                session_id=None,
                output=None,
                error=None,
                metrics={},
            )

            # Save initial state
            self.save_progress(variant_name, "pending", {})

            # Create async task
            task = self._run_variant_with_timeout(worktree_path, variant_name, task_variation, timeout_minutes)
            tasks.append(task)

        # Run all tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

        # Generate summary
        summary = self.aggregate_results()
        logger.info(f"Experiment completed. Summary:\n{summary}")

        return self.results

    async def _run_variant_with_timeout(
        self, worktree_path: Path, variant_name: str, task_variation: str, timeout_minutes: int
    ) -> None:
        """Wrapper to run variant with timeout and semaphore control"""
        if self.semaphore is None:
            raise RuntimeError("Semaphore not initialized")
        async with self.semaphore:
            try:
                result = await asyncio.wait_for(
                    self.run_variant(worktree_path, variant_name, task_variation), timeout=timeout_minutes * 60
                )

                # Update result
                self.results[variant_name].status = result["status"]
                self.results[variant_name].output = result.get("output")
                self.results[variant_name].metrics = result.get("metrics", {})
                self.results[variant_name].end_time = datetime.now()

            except TimeoutError:
                logger.error(f"Variant {variant_name} timed out after {timeout_minutes} minutes")
                self.results[variant_name].status = "failed"
                self.results[variant_name].error = f"Timeout after {timeout_minutes} minutes"
                self.results[variant_name].end_time = datetime.now()

            except Exception as e:
                logger.error(f"Variant {variant_name} failed: {e}")
                self.results[variant_name].status = "failed"
                self.results[variant_name].error = str(e)
                self.results[variant_name].end_time = datetime.now()

            # Save final state
            self.save_progress(
                variant_name,
                self.results[variant_name].status,
                {"error": self.results[variant_name].error} if self.results[variant_name].error else {},
            )

    async def run_variant(self, worktree_path: Path, variant_name: str, task_variation: str) -> dict[str, Any]:
        """Run single variant in its worktree - Real CCSDK Implementation with Defensive Utilities

        Args:
            worktree_path: Path to the worktree for this variant
            variant_name: Name of this variant
            task_variation: Task-specific variation instructions

        Returns:
            Dictionary with variant results
        """
        logger.info(f"Starting variant {variant_name} in {worktree_path}")

        # Import CCSDK here to avoid linter issues
        from amplifier.ccsdk_toolkit import ClaudeSession
        from amplifier.ccsdk_toolkit import SessionOptions

        # Update status to running
        self.results[variant_name].status = "running"
        start_time = datetime.now()

        # Generate a session ID
        session_id = f"session_{self.experiment_name}_{variant_name}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        self.results[variant_name].session_id = session_id
        self.save_progress(variant_name, "running", {"session_id": session_id})

        # Load instructions
        instructions = self.load_ultrathink_instructions()

        # Combine task variation with worktree context
        full_prompt = f"{task_variation}\n\nWorking directory: {worktree_path}"

        logger.info(f"Starting Claude session for {variant_name}")
        logger.debug(f"System prompt length: {len(instructions)} chars")
        logger.debug(f"Task variation: {task_variation[:200]}...")

        try:
            # Create session options with ultrathink instructions as system prompt
            options = SessionOptions(
                system_prompt=instructions,
                max_turns=10,  # Reasonable limit for experiments
            )

            # Run the Claude session with retry support
            async with ClaudeSession(options) as session:
                logger.info(f"Claude session active for {variant_name}")

                # Send the task variation with retry and feedback
                response = await retry_with_feedback(func=session.query, prompt=full_prompt, max_retries=3)

                # Extract response defensively
                if hasattr(response, "content"):
                    output = response.content
                else:
                    output = str(response)

                # Try to parse as JSON if it looks like JSON
                if output.strip().startswith("{") or output.strip().startswith("["):
                    parsed_output = parse_llm_json(output, default={"raw": output})
                else:
                    parsed_output = {"content": output}

                logger.info(f"Claude session completed for {variant_name}")

                # Calculate metrics
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                metrics = {
                    "duration_seconds": duration,
                    "status": "completed",
                    "variant": variant_name,
                }

                return {
                    "variant_name": variant_name,
                    "status": "completed",
                    "output": output,
                    "parsed": parsed_output,
                    "metrics": metrics,
                }

        except Exception as e:
            logger.error(f"Claude session failed for {variant_name}: {e}")

            # Calculate duration even on failure
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return {
                "variant_name": variant_name,
                "status": "failed",
                "output": None,
                "error": str(e),
                "metrics": {
                    "duration_seconds": duration,
                    "status": "failed",
                    "variant": variant_name,
                },
            }

    def save_progress(self, variant: str, status: str, data: dict):
        """Save progress to disk for recovery/monitoring - with defensive utilities

        Args:
            variant: Variant name
            status: Current status
            data: Additional data to save
        """
        progress_file = self.paths.results_dir / f"{variant}_progress.json"

        progress_data = {
            "variant": variant,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "experiment": self.experiment_name,
            **data,
        }

        # Always use defensive write (handles cloud sync issues)
        write_json_with_retry(progress_data, progress_file)

        logger.debug(f"Saved progress for {variant}: {status}")

    def aggregate_results(self) -> str:
        """Create markdown summary of all results

        Returns:
            Markdown formatted summary report
        """
        lines = [
            f"# Parallel Experiment Results: {self.experiment_name}",
            f"\nGenerated: {datetime.now().isoformat()}",
            f"\nTotal Variants: {len(self.results)}",
            "",
        ]

        # Count statuses
        status_counts = {}
        for result in self.results.values():
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        lines.append("## Summary")
        for status, count in status_counts.items():
            lines.append(f"- {status}: {count}")

        lines.append("\n## Variant Details\n")

        for variant_name, result in self.results.items():
            lines.append(f"### {variant_name}")
            lines.append(f"- **Status**: {result.status}")
            lines.append(f"- **Worktree**: `{result.worktree_path}`")
            lines.append(f"- **Start**: {result.start_time.isoformat()}")

            if result.end_time:
                duration = (result.end_time - result.start_time).total_seconds()
                lines.append(f"- **Duration**: {duration:.1f} seconds")

            if result.session_id:
                lines.append(f"- **Session ID**: {result.session_id}")

            if result.metrics:
                lines.append("\n**Metrics:**")
                for key, value in result.metrics.items():
                    lines.append(f"  - {key}: {value}")

            if result.output:
                lines.append("\n**Output:**")
                lines.append("```")
                lines.append(result.output[:500])  # Truncate long output
                if len(result.output) > 500:
                    lines.append("... [truncated]")
                lines.append("```")

            if result.error:
                lines.append(f"\n**Error:** {result.error}")

            lines.append("")

        return "\n".join(lines)
