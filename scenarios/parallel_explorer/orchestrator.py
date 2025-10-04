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

from amplifier.ccsdk_toolkit.defensive import write_json_with_retry  # Cloud sync-aware file operations

from .context_manager import ContextManager
from .paths import ExperimentPaths

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
        self.context_manager = ContextManager(experiment_name)
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
        self,
        variants: dict[str, str],
        max_parallel: int = 3,
        timeout_minutes: int = 30,
        task: str | None = None,
        use_context: bool = True,
    ) -> dict[str, ExperimentResult]:
        """Main entry point - runs all variants and returns results

        Args:
            variants: Mapping of variant names to task variations
            max_parallel: Maximum concurrent sessions
            timeout_minutes: Timeout per variant
            task: Base task description (optional, for creating context)
            use_context: Whether to use/create rich context (default True)

        Returns:
            Dictionary mapping variant names to results
        """
        logger.info(f"Starting experiment with {len(variants)} variants, max_parallel={max_parallel}")

        # Try to load existing context first
        context = None
        if use_context:
            context = self.context_manager.load_context()
            if context:
                logger.info("Loaded existing experiment context")
                # Update variants from context if available
                if "variants" in context:
                    # Merge provided variants with context variants
                    for name in variants:
                        if name in context["variants"]:
                            # Context has richer info, keep it as-is
                            continue
                        # Add new variant to context
                        context["variants"][name] = {
                            "description": variants[name],
                            "approach": f"Implement using {name} approach",
                            "focus_areas": [],
                            "context": "",
                        }
            else:
                # Create new context from provided information
                logger.info("Creating new experiment context")
                if task:
                    self.context_manager.create_context(
                        task=task,
                        variants=variants,
                        requirements="Create a working implementation following best practices",
                        success_criteria="Implementation should be functional and well-structured",
                    )
                    context = self.context_manager.load_context()

        # Store context for use in variant execution
        self.context = context

        # Initialize semaphore for parallel control
        self.semaphore = asyncio.Semaphore(max_parallel)

        # Import worktree manager
        try:
            from .worktree_manager import WorktreeManager

            worktree_mgr = WorktreeManager(self.experiment_name)

            # CRITICAL: Actually create the worktrees!
            logger.info(f"Creating worktrees for {len(variants)} variants")
            worktree_paths = worktree_mgr.create_worktrees(list(variants.keys()))
            logger.info(f"Created/found {len(worktree_paths)} worktrees")

        except ImportError:
            logger.error("WorktreeManager not found - using mock paths")
            worktree_mgr = None
        except Exception as e:
            logger.error(f"Failed to create worktrees: {e}")
            worktree_mgr = None

        # Create tasks for each variant
        tasks = []
        for variant_name, task_variation in variants.items():
            # Get or create worktree path
            if worktree_mgr:
                worktree_path = worktree_mgr.get_worktree_path(variant_name)
                # No need to mkdir - worktree creation already did this
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
            async_task = asyncio.create_task(
                self._run_variant_with_timeout(worktree_path, variant_name, task_variation, timeout_minutes)
            )
            tasks.append(async_task)

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
        """Run variant using proper amplifier pattern - code orchestrates, AI generates content.

        Args:
            worktree_path: Path to the worktree for this variant
            variant_name: Name of this variant
            task_variation: Task-specific variation instructions

        Returns:
            Dictionary with variant results
        """
        logger.info(f"Building scenario tool for {variant_name}")

        # Import the new tool builder
        from scenarios.parallel_explorer.structure_validator import validate_tool_structure
        from scenarios.parallel_explorer.tool_builder import build_scenario_tool

        # Update status to running
        self.results[variant_name].status = "running"
        start_time = datetime.now()

        # Generate a session ID
        session_id = f"session_{self.experiment_name}_{variant_name}_{start_time.strftime('%Y%m%d_%H%M%S')}"
        self.results[variant_name].session_id = session_id
        self.save_progress(variant_name, "running", {"session_id": session_id})

        try:
            # Identify exemplars to learn from
            exemplars = [
                worktree_path / "scenarios" / "blog_writer",
                worktree_path / "scenarios" / "article_illustrator",
            ]

            # Prepare requirements from context or task variation
            requirements = {}
            if hasattr(self, "context") and self.context:
                # Extract variant-specific requirements from context
                requirements = self.context.get("variants", {}).get(variant_name, {})
                requirements["task_variation"] = task_variation
                requirements["experiment_name"] = self.experiment_name
                logger.info(f"Using rich context for variant {variant_name}")
            else:
                # Use task variation as base requirements
                requirements = {
                    "task_variation": task_variation,
                    "experiment_name": self.experiment_name,
                    "variant_name": variant_name,
                    "description": f"Variant {variant_name} of {self.experiment_name}",
                }

            # Build the scenario tool with Python orchestration
            tool_path = await build_scenario_tool(
                variant_name=f"{self.experiment_name}_{variant_name}",
                requirements=requirements,
                worktree_path=worktree_path,
                exemplar_paths=exemplars,
            )

            # Validate the generated tool
            is_valid, issues = validate_tool_structure(tool_path)

            if is_valid:
                logger.info(f"Successfully created scenario tool at {tool_path}")

                # Update results
                self.results[variant_name].status = "completed"
                self.results[variant_name].output = f"Created scenario tool at {tool_path}"
                self.results[variant_name].end_time = datetime.now()

                # Save progress
                self.save_progress(
                    variant_name,
                    "completed",
                    {"tool_path": str(tool_path), "duration": (datetime.now() - start_time).total_seconds()},
                )

                return {
                    "status": "completed",
                    "tool_path": str(tool_path),
                    "output": f"Created scenario tool at {tool_path}",
                    "session_id": session_id,
                }
            error_msg = f"Validation failed: {', '.join(issues)}"
            logger.error(f"Tool validation failed for {variant_name}: {error_msg}")

            # Update results
            self.results[variant_name].status = "failed"
            self.results[variant_name].error = error_msg
            self.results[variant_name].end_time = datetime.now()

            # Save progress
            self.save_progress(variant_name, "failed", {"error": error_msg})

            return {"status": "failed", "error": error_msg, "session_id": session_id}

        except Exception as e:
            logger.error(f"Failed to build variant {variant_name}: {e}")

            # Update results
            self.results[variant_name].status = "failed"
            self.results[variant_name].error = str(e)
            self.results[variant_name].end_time = datetime.now()

            # Save progress
            self.save_progress(variant_name, "failed", {"error": str(e)})

            return {"status": "failed", "error": str(e), "session_id": session_id}

    def _validate_implementation(self, worktree_path: Path, variant_name: str) -> bool:
        """Validate that actual implementation files were created.

        Args:
            worktree_path: Path to the worktree
            variant_name: Name of the variant

        Returns:
            True if implementation files exist, False otherwise
        """
        # Check for scenario tool implementation in the expected location
        # The tool should be created at: scenarios/{tool_name}_{variant_name}/
        scenarios_dir = worktree_path / "scenarios"
        tool_name = self.experiment_name.replace("-", "_")
        expected_dir_name = f"{tool_name}_{variant_name}"
        expected_tool_dir = scenarios_dir / expected_dir_name

        # First check if the expected directory exists
        if expected_tool_dir.exists() and expected_tool_dir.is_dir():
            # Check if __init__.py exists (required for a valid scenario tool)
            init_file = expected_tool_dir / "__init__.py"
            if init_file.exists():
                logger.info(f"✓ Found scenario implementation: {expected_dir_name}")

                # Count Python files
                py_files = list(expected_tool_dir.glob("**/*.py"))
                py_files = [f for f in py_files if "__pycache__" not in str(f)]

                if py_files:
                    logger.info(f"  - Contains {len(py_files)} Python files")
                    for f in py_files[:3]:  # Log first 3 files
                        logger.info(f"    • {f.relative_to(expected_tool_dir)}")
                    return True
                logger.warning("  - WARNING: __init__.py exists but no Python content found")
            else:
                logger.warning(f"Expected tool directory exists but missing __init__.py: {expected_tool_dir}")

        # Fallback: Look for any new directories created in scenarios/
        # (in case the naming convention is slightly different)
        if scenarios_dir.exists():
            scenario_dirs = [d for d in scenarios_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]

            # Look for directories that weren't there originally
            original_dirs = {"blog_writer", "article_illustrator", "parallel_explorer"}
            new_dirs = [d for d in scenario_dirs if d.name not in original_dirs]

            for scenario_dir in new_dirs:
                # Check if this directory contains implementation files
                init_file = scenario_dir / "__init__.py"
                if init_file.exists():
                    logger.info(f"Found scenario implementation (unexpected name): {scenario_dir.name}")
                    logger.info(f"  - Expected: {expected_dir_name}")
                    logger.info("  - Consider using the exact naming convention")
                    return True

        # Fallback: Check for any new Python files in the worktree
        # (but be more strict - require at least a few files to indicate real implementation)
        py_files = []
        for file in worktree_path.rglob("*.py"):
            # Exclude .git and __pycache__
            if ".git" not in str(file) and "__pycache__" not in str(file):
                py_files.append(file)

        # Require at least 3 Python files for a valid implementation
        if len(py_files) >= 3:
            logger.info(f"Found {len(py_files)} Python files in worktree for {variant_name}")
            for f in py_files[:3]:  # Log first 3 files
                logger.debug(f"  - {f.relative_to(worktree_path)}")
            return True

        # Check for documentation files (README, docs, etc.)
        doc_patterns = ["*.md", "*.rst", "*.txt"]
        doc_files = []
        for pattern in doc_patterns:
            for file in worktree_path.rglob(pattern):
                if ".git" not in str(file):
                    doc_files.append(file)

        # If we have meaningful documentation (more than just a single file)
        if len(doc_files) > 1:
            logger.info(f"Found {len(doc_files)} documentation files in worktree for {variant_name}")
            for f in doc_files[:3]:
                logger.debug(f"  - {f.relative_to(worktree_path)}")
            return True

        # Check for other code files (JS, TS, etc.)
        code_patterns = ["*.js", "*.ts", "*.jsx", "*.tsx", "*.java", "*.cpp", "*.c", "*.go", "*.rs"]
        code_files = []
        for pattern in code_patterns:
            for file in worktree_path.rglob(pattern):
                if ".git" not in str(file):
                    code_files.append(file)

        if code_files:
            logger.info(f"Found {len(code_files)} code files in worktree for {variant_name}")
            return True

        # Check for configuration files (package.json, requirements.txt, etc.)
        config_patterns = [
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
        ]
        for pattern in config_patterns:
            if (worktree_path / pattern).exists():
                logger.info(f"Found config file {pattern} in worktree for {variant_name}")
                return True

        # Final check: Any files at all (excluding .git)?
        all_files = []
        for item in worktree_path.rglob("*"):
            if item.is_file() and ".git" not in str(item):
                all_files.append(item)

        if all_files:
            logger.warning(f"Found {len(all_files)} files in worktree for {variant_name}")
            logger.info("Files found:")
            for f in all_files[:5]:
                logger.info(f"  - {f.relative_to(worktree_path)}")
            # Consider it successful if any files were created
            return len(all_files) > 0
        logger.error(f"No files created in worktree at all for {variant_name}")
        logger.error(f"Worktree path checked: {worktree_path}")

        return False

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

                # Special highlight for implementation validation
                if "implementation_created" in result.metrics and not result.metrics["implementation_created"]:
                    lines.append("\n⚠️ **WARNING: No implementation files were created!**")

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

        # Defensive check: ensure all items are strings before joining
        for i, line in enumerate(lines):
            if not isinstance(line, str):
                logger.error(f"Non-string found in lines at index {i}: type={type(line)}, value={line}")
                # Convert to string to prevent crash
                lines[i] = str(line)

        return "\n".join(lines)
