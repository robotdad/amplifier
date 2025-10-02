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
from scenarios.parallel_explorer.context_manager import ContextManager
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
            from scenarios.parallel_explorer.worktree_manager import WorktreeManager

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

        # Generate prompt using context if available
        if hasattr(self, "context") and self.context:
            # Use rich context to generate comprehensive prompt
            full_prompt = self.context_manager.get_variant_prompt(self.context, variant_name, worktree_path)
            logger.info(f"Using rich context for variant {variant_name}")
        else:
            # Fallback to simple prompt with explicit worktree instructions
            full_prompt = f"""{task_variation}

## CRITICAL WORKTREE INSTRUCTIONS
1. You are working in a git worktree at: {worktree_path}
2. IMMEDIATELY run this command first: cd {worktree_path}
3. Create ALL files under this directory: {worktree_path}
4. Example file paths:
   - {worktree_path}/implementation.py
   - {worktree_path}/README.md
   - {worktree_path}/tests/
5. DO NOT create files anywhere else

Your current working directory should be: {worktree_path}
When creating files, use paths relative to the worktree directory."""

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

                # CRITICAL: Validate that code was actually generated
                implementation_created = self._validate_implementation(worktree_path, variant_name)

                # Calculate metrics
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()

                # Determine actual status based on implementation validation
                actual_status = "completed" if implementation_created else "failed"
                if not implementation_created:
                    logger.error(f"Variant {variant_name} marked as failed: No implementation files created")

                metrics = {
                    "duration_seconds": duration,
                    "status": actual_status,
                    "variant": variant_name,
                    "implementation_created": implementation_created,
                }

                return {
                    "variant_name": variant_name,
                    "status": actual_status,
                    "output": output,
                    "parsed": parsed_output,
                    "metrics": metrics,
                    "error": None if implementation_created else "No implementation files created in worktree",
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
                    "implementation_created": False,
                },
            }

    def _validate_implementation(self, worktree_path: Path, variant_name: str) -> bool:
        """Validate that actual implementation files were created.

        Args:
            worktree_path: Path to the worktree
            variant_name: Name of the variant

        Returns:
            True if implementation files exist, False otherwise
        """
        # More flexible validation - check for any substantial files created in the worktree
        # Exclude .git directory and common system files

        # First, check for Python files anywhere in the worktree
        py_files = []
        for file in worktree_path.rglob("*.py"):
            # Exclude .git directory
            if ".git" not in str(file):
                py_files.append(file)

        if py_files:
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
