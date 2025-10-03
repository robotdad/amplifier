"""Orchestrate scenario tool creation - main entry point.

This module coordinates the creation of scenario tools using the
"code for structure, AI for intelligence" pattern. Python handles
directory creation and file writing, while CCSDK generates content.
"""

import logging
from pathlib import Path
from typing import Any

from scenarios.parallel_explorer.content_generator import generate_file_content
from scenarios.parallel_explorer.pattern_analyzer import analyze_exemplars
from scenarios.parallel_explorer.structure_validator import validate_imports
from scenarios.parallel_explorer.structure_validator import validate_tool_structure

logger = logging.getLogger(__name__)


async def build_scenario_tool(
    variant_name: str,
    requirements: dict[str, Any],
    worktree_path: Path,
    exemplar_paths: list[Path] | None = None
) -> Path:
    """Build complete scenario tool following amplifier patterns.

    This is the main orchestration function that coordinates the entire
    tool creation process using the principle of "code for structure,
    AI for intelligence".

    Args:
        variant_name: Name for the variant/tool being created
        requirements: Requirements and specifications for the tool
        worktree_path: Path to the git worktree
        exemplar_paths: Optional list of exemplar scenario tools to analyze

    Returns:
        Path to the created tool directory

    Raises:
        ValueError: If tool creation fails validation
        RuntimeError: If file generation fails
    """
    logger.info(f"Building scenario tool: {variant_name}")

    # Step 1: Analyze exemplars to extract patterns
    if not exemplar_paths:
        # Default exemplars if none provided
        exemplar_paths = [
            worktree_path / "scenarios" / "blog_writer",
            worktree_path / "scenarios" / "article_illustrator"
        ]

    logger.info("Analyzing exemplar scenarios for patterns...")
    patterns = analyze_exemplars(exemplar_paths)
    logger.info(f"Extracted patterns from {len(exemplar_paths)} exemplars")

    # Step 2: Create directory structure (Python handles structure)
    tool_dir = worktree_path / "ai_working" / "experiments" / variant_name
    tool_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created tool directory at {tool_dir}")

    # Step 3: Determine which files to generate based on patterns and requirements
    files_to_generate = determine_files_to_generate(patterns, requirements)
    logger.info(f"Will generate {len(files_to_generate)} files")

    # Step 4: Generate each file using CCSDK (AI handles content)
    for file_type, file_name in files_to_generate.items():
        logger.info(f"Generating {file_type}: {file_name}")

        try:
            # Generate content using CCSDK
            content = await generate_file_content(
                file_type=file_type,
                tool_name=variant_name,
                requirements=requirements,
                patterns=patterns
            )

            # Write the generated content (Python handles I/O)
            file_path = tool_dir / file_name
            file_path.write_text(content)
            logger.info(f"Written {file_name} ({len(content)} bytes)")

        except Exception as e:
            logger.error(f"Failed to generate {file_type}: {e}")
            raise RuntimeError(f"File generation failed for {file_type}: {e}")

    # Step 5: Validate the generated tool
    logger.info("Validating generated tool structure...")
    is_valid, issues = validate_tool_structure(tool_dir)

    if not is_valid:
        logger.error(f"Validation failed: {issues}")
        raise ValueError(f"Tool validation failed: {', '.join(issues)}")

    # Additional validation checks
    if not validate_imports(tool_dir):
        logger.warning("Import validation failed - tool may have dependency issues")

    logger.info(f"Successfully created scenario tool at {tool_dir}")
    return tool_dir


def determine_files_to_generate(
    patterns: dict[str, Any],
    requirements: dict[str, Any]
) -> dict[str, str]:
    """Determine which files need to be generated based on patterns and requirements.

    Args:
        patterns: Extracted patterns from exemplars
        requirements: Tool requirements

    Returns:
        Dictionary mapping file types to file names
    """
    files = {
        "__init__": "__init__.py",
        "main": "main.py",
        "README": "README.md"
    }

    # Check if __main__.py is commonly used in exemplars
    if patterns.get("common_files", {}).get("__main__"):
        files["__main__"] = "__main__.py"

    # Check if config.py is needed
    if patterns.get("config_patterns") or "config" in str(requirements).lower():
        files["config"] = "config.py"

    # Check if separate core logic file is used
    if patterns.get("common_files", {}).get("core_logic"):
        # Only add if it's different from main.py
        core_files = patterns["common_files"]["core_logic"]
        for f in core_files:
            if f and f.name != "main.py":
                files["core_logic"] = "core.py"
                break

    return files


async def build_minimal_tool(
    tool_name: str,
    tool_dir: Path,
    requirements: dict[str, Any]
) -> None:
    """Build a minimal working scenario tool.

    This creates the absolute minimum files needed for a functioning tool.

    Args:
        tool_name: Name of the tool
        tool_dir: Directory to create the tool in
        requirements: Tool requirements
    """
    tool_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal __init__.py
    init_content = f'''"""
{tool_name} - Minimal scenario tool
"""

from .main import main

__all__ = ["main"]
'''
    (tool_dir / "__init__.py").write_text(init_content)

    # Create minimal main.py
    main_content = f'''"""
Main implementation for {tool_name}
"""

import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--input", "-i", required=True, help="Input for processing")
def main(input):
    """Process input according to requirements."""
    logger.info(f"Processing: {{input}}")

    # Implementation based on requirements:
    # {requirements}

    print(f"Processed: {{input}}")
    return 0


if __name__ == "__main__":
    main()
'''
    (tool_dir / "main.py").write_text(main_content)

    # Create minimal README
    readme_content = f"""# {tool_name}

Minimal scenario tool implementation.

## Usage

```bash
python -m {tool_name} --input "test"
```

## Requirements

{requirements}
"""
    (tool_dir / "README.md").write_text(readme_content)


async def build_from_template(
    tool_name: str,
    tool_dir: Path,
    template_path: Path,
    requirements: dict[str, Any]
) -> None:
    """Build a tool by copying and adapting a template.

    Args:
        tool_name: Name of the new tool
        tool_dir: Directory to create the tool in
        template_path: Path to template scenario tool
        requirements: Tool requirements
    """
    import shutil

    # Copy template structure
    if template_path.exists():
        shutil.copytree(template_path, tool_dir, dirs_exist_ok=True)

        # Update files with new tool name
        for py_file in tool_dir.glob("*.py"):
            content = py_file.read_text()
            # Replace template references with new tool name
            content = content.replace(template_path.name, tool_name)
            py_file.write_text(content)

        logger.info(f"Created tool from template: {template_path.name}")
    else:
        logger.warning(f"Template not found: {template_path}")
        await build_minimal_tool(tool_name, tool_dir, requirements)
