"""
Context Manager Module: Manages rich context for parallel experiments

This module handles the storage and retrieval of comprehensive experiment
context to ensure each variant receives sufficient information for
successful implementation.

Contract:
  Inputs:
    - create_context: name (str), task (str), variants (dict), common_context (str)
    - load_context: name (str)
    - get_variant_prompt: context (dict), variant_name (str)

  Outputs:
    - create_context: None (saves to disk)
    - load_context: dict (full context structure)
    - get_variant_prompt: str (complete prompt with all context)

  Side Effects:
    - Writes context files to .data/parallel_explorer/{name}/
    - Creates directories as needed

  Dependencies:
    - pathlib: File system operations
    - json: Context serialization
    - logging: Debug and error reporting
"""

import logging
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit.defensive import read_json_with_retry
from amplifier.ccsdk_toolkit.defensive import write_json_with_retry

from .paths import ExperimentPaths

logger = logging.getLogger(__name__)

# Context schema for reference
CONTEXT_SCHEMA = {
    "experiment_name": "Name of the experiment (used for tool naming)",
    "task": "Base task description",
    "output_type": "Always 'scenario_tool' - generates amplifier CLI tools",
    "tool_prefix": "Prefix for make commands (e.g., 'content' → 'make content-analyze')",
    "requirements": "Detailed requirements for the implementation (can be string or list)",
    "common_context": "Shared knowledge and constraints across all variants",
    "variants": {
        "variant_name": {
            "description": "Brief one-line description",
            "approach": "Detailed approach to take for this variant",
            "focus_areas": ["Primary focus area", "Secondary focus area"],
            "cli_command": "Suggested make command (e.g., 'content-analyze')",
            "main_features": ["feature1", "feature2"],  # Guides module structure
            "context": "Variant-specific context and implementation hints",
            "constraints": "Optional variant-specific constraints",
        }
    },
    "success_criteria": "What makes a good implementation",
    "technical_requirements": "Optional technical specifications",
}


class ContextManager:
    """Manages experiment context for parallel explorations"""

    def __init__(self, experiment_name: str):
        """Initialize context manager for an experiment

        Args:
            experiment_name: Identifier for this experiment
        """
        self.experiment_name = experiment_name
        self.paths = ExperimentPaths(experiment_name)
        self.paths.ensure_directories()

    def create_context(
        self,
        task: str,
        variants: dict[str, Any],
        requirements: str | None = None,
        common_context: str | None = None,
        success_criteria: str | None = None,
        technical_requirements: str | None = None,
    ) -> Path:
        """Create and save comprehensive experiment context

        Args:
            task: Base task description
            variants: Dictionary of variant configurations
            requirements: Detailed requirements (optional)
            common_context: Shared context across variants (optional)
            success_criteria: What makes implementation successful (optional)
            technical_requirements: Technical specs (optional)

        Returns:
            Path to the saved context file
        """
        # Enhance variants if they're simple strings
        enriched_variants = {}
        for name, variant_data in variants.items():
            if isinstance(variant_data, str):
                # Convert simple string to rich structure
                enriched_variants[name] = {
                    "description": variant_data,
                    "approach": f"Implement using {name} approach: {variant_data}",
                    "focus_areas": [name, "best practices"],
                    "context": "",
                }
            else:
                # Already rich structure
                enriched_variants[name] = variant_data

        # Build context structure
        context = {
            "experiment_name": self.experiment_name,
            "task": task,
            "requirements": requirements or "Create a working implementation following best practices",
            "common_context": common_context or "",
            "variants": enriched_variants,
            "success_criteria": success_criteria
            or "Implementation should be functional, well-structured, and follow the specified approach",
            "technical_requirements": technical_requirements or "",
        }

        # Save context
        context_file = self.paths.base_dir / "context.json"
        write_json_with_retry(context, context_file)
        logger.info(f"Created context for experiment '{self.experiment_name}' with {len(variants)} variants")
        logger.debug(f"Context saved to: {context_file}")
        return context_file

    def load_context(self) -> dict[str, Any] | None:
        """Load experiment context from disk

        Returns:
            Context dictionary or None if not found
        """
        context_file = self.paths.base_dir / "context.json"

        if not context_file.exists():
            logger.warning(f"No context file found at {context_file}")
            return None

        try:
            context = read_json_with_retry(context_file)
            logger.info(f"Loaded context for experiment '{self.experiment_name}'")
            return context
        except Exception as e:
            logger.error(f"Failed to load context: {e}")
            return None

    def get_variant_prompt(self, context: dict[str, Any], variant_name: str, worktree_path: Path) -> str:
        """Generate comprehensive prompt for a variant

        Args:
            context: Full experiment context
            variant_name: Name of the variant to generate prompt for
            worktree_path: Path to the git worktree for this variant

        Returns:
            Complete prompt string with all context and instructions
        """
        if variant_name not in context.get("variants", {}):
            logger.error(f"Variant '{variant_name}' not found in context")
            return f"ERROR: Variant {variant_name} not found"

        variant = context["variants"][variant_name]

        # Build comprehensive prompt
        prompt_parts = [
            "You are implementing a variant of a parallel exploration experiment.",
            "",
            "## BASE TASK",
            f"{context.get('task', 'No task specified')}",
            "",
        ]

        # Add requirements if present
        if context.get("requirements"):
            prompt_parts.append("## REQUIREMENTS")
            requirements = context.get("requirements")
            if isinstance(requirements, str):
                prompt_parts.append(requirements)
            elif isinstance(requirements, list):
                for req in requirements:
                    prompt_parts.append(f"- {req}")
            else:
                prompt_parts.append(str(requirements))
            prompt_parts.append("")

        # Add common context if present
        if context.get("common_context"):
            prompt_parts.append("## COMMON CONTEXT (applies to all variants)")

            # Handle both string and dict formats
            common_context = context.get("common_context")
            if isinstance(common_context, str):
                prompt_parts.append(common_context)
            elif isinstance(common_context, dict):
                for key, value in common_context.items():
                    if isinstance(value, list):
                        prompt_parts.append(f"**{key.replace('_', ' ').title()}**: {', '.join(value)}")
                    else:
                        prompt_parts.append(f"**{key.replace('_', ' ').title()}**: {value}")
            prompt_parts.append("")

        # Add variant-specific information
        prompt_parts.extend(
            [
                f"## YOUR VARIANT: {variant_name}",
                f"**Description**: {variant.get('description', 'No description')}",
                "",
                "## APPROACH TO FOLLOW",
                variant.get("approach", "Implement using your best judgment"),
                "",
            ]
        )

        # Add focus areas
        if variant.get("focus_areas"):
            prompt_parts.extend(
                [
                    "## FOCUS AREAS",
                    "Prioritize these aspects in your implementation:",
                ]
            )
            for area in variant["focus_areas"]:
                prompt_parts.append(f"- {area}")
            prompt_parts.append("")

        # Add variant-specific context
        if variant.get("context"):
            prompt_parts.extend(
                [
                    "## VARIANT-SPECIFIC CONTEXT",
                    variant["context"],
                    "",
                ]
            )

        # Add constraints if any
        if variant.get("constraints"):
            prompt_parts.extend(
                [
                    "## CONSTRAINTS",
                    variant["constraints"],
                    "",
                ]
            )

        # Add success criteria
        if context.get("success_criteria"):
            prompt_parts.append("## SUCCESS CRITERIA")
            success_criteria = context.get("success_criteria")
            if isinstance(success_criteria, str):
                prompt_parts.append(success_criteria)
            elif isinstance(success_criteria, list):
                for criterion in success_criteria:
                    prompt_parts.append(f"- {criterion}")
            else:
                prompt_parts.append(str(success_criteria))
            prompt_parts.append("")

        # Add technical requirements
        if context.get("technical_requirements"):
            prompt_parts.append("## TECHNICAL REQUIREMENTS")
            technical_requirements = context.get("technical_requirements")
            if isinstance(technical_requirements, str):
                prompt_parts.append(technical_requirements)
            elif isinstance(technical_requirements, list):
                for req in technical_requirements:
                    prompt_parts.append(f"- {req}")
            else:
                prompt_parts.append(str(technical_requirements))
            prompt_parts.append("")

        # Add tool naming information
        tool_name = f"{context.get('experiment_name', 'unknown')}_{variant_name}"

        # CRITICAL: Add explicit scenario tool instructions
        prompt_parts.extend(
            [
                "## SCENARIO TOOL IMPLEMENTATION",
                f"You are creating a complete amplifier scenario tool at: scenarios/{tool_name}/",
                "",
                "## LEARN FROM EXEMPLARS",
                f"Study these working examples in your worktree at {worktree_path}:",
                "- **scenarios/blog_writer/** - Multi-stage content generation with state management",
                "- **scenarios/article_illustrator/** - Pipeline pattern with session resumability",
                "",
                "These tools demonstrate the scenario tool pattern:",
                "- Python package structure (__init__.py, __main__.py, main.py, state.py)",
                "- CLI interface using click",
                "- State management for resumability",
                "- Comprehensive documentation (README.md, HOW_TO_CREATE_YOUR_OWN.md)",
                "- Modular feature directories",
                "",
                "## YOUR IMPLEMENTATION",
                f"Create your tool at: {worktree_path}/scenarios/{tool_name}/",
                "",
                "Follow the patterns you observe in the examples while implementing your variant's approach.",
                "Your tool should match their structure and quality, adapted to your specific use case.",
                "",
                "Key paths:",
                f"- Work in: {worktree_path}",
                f"- Create at: scenarios/{tool_name}/",
                "- Study: scenarios/blog_writer/ and scenarios/article_illustrator/",
                "",
                "Begin by reading the example tools, then build yours following their patterns.",
            ]
        )

        # Defensive check: ensure all items are strings before joining
        for i, part in enumerate(prompt_parts):
            if not isinstance(part, str):
                logger.error(f"Non-string found at index {i}: type={type(part)}, value={part}")
                # Convert to string to prevent crash
                prompt_parts[i] = str(part)

        return "\n".join(prompt_parts)

    def update_variant(self, variant_name: str, updates: dict[str, Any]) -> bool:
        """Update a specific variant's context

        Args:
            variant_name: Name of variant to update
            updates: Dictionary of updates to apply

        Returns:
            True if successful, False otherwise
        """
        context = self.load_context()
        if not context:
            logger.error("No context to update")
            return False

        if variant_name not in context.get("variants", {}):
            logger.error(f"Variant '{variant_name}' not found")
            return False

        # Apply updates
        context["variants"][variant_name].update(updates)

        # Save updated context
        context_file = self.paths.base_dir / "context.json"
        write_json_with_retry(context, context_file)
        logger.info(f"Updated variant '{variant_name}' context")
        return True

    def export_context_to_markdown(self) -> str:
        """Export context to markdown format for human review

        Returns:
            Markdown formatted context
        """
        context = self.load_context()
        if not context:
            return "# No Context Found"

        lines = [
            f"# Experiment: {self.experiment_name}",
            "",
            "## Task",
            context.get("task", "No task specified"),
            "",
        ]

        if context.get("requirements"):
            lines.extend(["## Requirements", context["requirements"], ""])

        if context.get("common_context"):
            lines.extend(["## Common Context", context["common_context"], ""])

        lines.extend(["## Variants", ""])
        for name, variant in context.get("variants", {}).items():
            lines.extend(
                [
                    f"### {name}",
                    f"**Description**: {variant.get('description', 'N/A')}",
                    "",
                    f"**Approach**: {variant.get('approach', 'N/A')}",
                    "",
                ]
            )

            if variant.get("focus_areas"):
                lines.append("**Focus Areas**:")
                for area in variant["focus_areas"]:
                    lines.append(f"- {area}")
                lines.append("")

            if variant.get("context"):
                lines.extend(["**Context**:", variant["context"], ""])

        if context.get("success_criteria"):
            lines.extend(["## Success Criteria", context["success_criteria"], ""])

        return "\n".join(lines)


# Convenience functions for simple usage
def save_experiment_context(
    experiment_name: str,
    task: str,
    variants: dict[str, Any],
    **kwargs,
) -> None:
    """Quick function to save experiment context

    Args:
        experiment_name: Name of the experiment
        task: Base task description
        variants: Variant configurations
        **kwargs: Additional context fields
    """
    manager = ContextManager(experiment_name)
    manager.create_context(task, variants, **kwargs)


def load_experiment_context(experiment_name: str) -> dict[str, Any] | None:
    """Quick function to load experiment context

    Args:
        experiment_name: Name of the experiment

    Returns:
        Context dictionary or None
    """
    manager = ContextManager(experiment_name)
    return manager.load_context()
