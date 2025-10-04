"""Generate file content using CCSDK with focused prompts.

This module handles the AI-powered content generation for scenario tools.
It builds focused prompts for specific file types and uses CCSDK to generate
complete, working implementations following amplifier patterns.
"""

import json
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions


async def generate_file_content(
    file_type: str,
    tool_name: str,
    requirements: dict[str, Any],
    patterns: dict[str, Any]
) -> str:
    """Generate complete content for one file using CCSDK.

    Args:
        file_type: Type of file to generate ("__main__", "main", "config", "README", etc.)
        tool_name: Name of the tool being created
        requirements: Requirements and specifications for the tool
        patterns: Patterns extracted from exemplar tools

    Returns:
        Generated file content as a string
    """
    # Build focused prompt for this specific file
    prompt = build_generation_prompt(
        file_type=file_type,
        context={
            "tool_name": tool_name,
            "requirements": requirements,
            "patterns": patterns
        }
    )

    # Use ClaudeSession to generate content
    options = SessionOptions(
        system_prompt="You are an expert Python developer creating amplifier scenario tools.",
        retry_attempts=2
    )

    try:
        async with ClaudeSession(options) as session:
            response = await session.query(prompt)
            content = response.content.strip()

            # Strip markdown code block wrappers if present
            if content.startswith("```"):
                # Remove opening ``` or ```python/```markdown
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines)

            return content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to generate {file_type} content: {e}")


def build_generation_prompt(file_type: str, context: dict[str, Any]) -> str:
    """Build focused prompt for specific file type.

    Args:
        file_type: Type of file to generate
        context: Context including tool name, requirements, and patterns

    Returns:
        Focused prompt string for CCSDK
    """
    tool_name = context["tool_name"]
    requirements = context.get("requirements", {})
    patterns = context.get("patterns", {})

    # Base context for all file types
    base_context = f"""
You are creating a file for an amplifier scenario tool named '{tool_name}'.

Requirements:
{json.dumps(requirements, indent=2)}

CRITICAL: Use ONLY these verified CCSDK imports (from blog_writer/article_illustrator):
```python
from amplifier.ccsdk_toolkit import ClaudeSession
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.ccsdk_toolkit.defensive import retry_with_feedback
from amplifier.utils.logger import get_logger
```

Standard CCSDK pattern:
```python
options = SessionOptions(system_prompt="...", retry_attempts=2)
async with ClaudeSession(options) as session:
    response = await session.query(prompt)
    return response.content.strip()
```

DO NOT use: CCSDKFactory, agent_client, async_client, or any other invented APIs.
ONLY use the imports shown above.
"""

    # File-specific prompts
    prompts = {
        "__init__": f"""{base_context}

Generate a complete __init__.py file for this scenario tool.
The file should:
1. Include a module docstring describing the tool's purpose
2. Import and export the main entry point function(s)
3. Define __all__ with public exports
4. Follow the amplifier pattern seen in scenarios like blog_writer

Return ONLY the Python code, no explanations.""",

        "__main__": f"""{base_context}

Generate a complete __main__.py file for this scenario tool.
The file should:
1. Import the main function from the appropriate module
2. Include the standard if __name__ == "__main__": pattern
3. Set up any necessary asyncio event loop if the tool is async
4. Follow Click CLI patterns if appropriate

Return ONLY the Python code, no explanations.""",

        "main": f"""{base_context}

Generate the main implementation file for this scenario tool.
The file should:
1. Implement the core functionality based on the requirements
2. Use Click decorators for CLI if appropriate
3. Include proper logging setup
4. Follow async/await patterns if needed
5. Use CCSDK for AI operations
6. Include comprehensive docstrings

CLI patterns from exemplars:
{json.dumps(patterns.get("cli_patterns", [])[:5], indent=2)}

Return ONLY the Python code, no explanations.""",

        "config": f"""{base_context}

Generate a config.py file for this scenario tool.
The file should:
1. Define configuration constants
2. Include any environment variable handling
3. Set up logging configuration
4. Define default values and settings
5. Use Pydantic models if appropriate for configuration

Return ONLY the Python code, no explanations.""",

        "README": f"""{base_context}

Generate a comprehensive README.md file for this scenario tool.
The file should include:
1. Tool name and purpose
2. Installation instructions
3. Usage examples with command-line syntax
4. Configuration options
5. How it works section
6. Requirements/dependencies
7. Example output

Follow the structure of successful amplifier scenario tools like blog_writer.

Return ONLY the Markdown content, no explanations.""",

        "core_logic": f"""{base_context}

Generate the core logic implementation for this scenario tool.
The file should:
1. Implement the main business logic based on requirements
2. Include helper functions and utilities
3. Use proper error handling
4. Include async functions if appropriate
5. Integrate with CCSDK for AI operations
6. Follow the single responsibility principle

Return ONLY the Python code, no explanations.""",

        "HOW_TO_CREATE": f"""{base_context}

Generate a HOW_TO_CREATE_YOUR_OWN.md file for this scenario tool.

This document teaches others HOW THE TOOL WAS CREATED, not how to use it.

Follow the EXACT pattern from scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md:
1. Start with: "You don't need to be a programmer. You just need to describe what you want."
2. Section: "What the Creator Did" - describe the thinking process
3. Section: "How You Can Create Your Own Tool" - 6-step process
4. Section: "Real Examples" - beginner/intermediate/advanced tool ideas
5. Section: "Key Principles" - metacognitive recipe
6. Emphasize the collaborative creation process
7. Focus on the thinking/approach, not implementation details

Study scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md and scenarios/article_illustrator/HOW_TO_CREATE_YOUR_OWN.md
before generating to match their style and structure exactly.

Return ONLY the Markdown content, no explanations."""
    }

    # Return the appropriate prompt or a generic one
    if file_type in prompts:
        return prompts[file_type]
    return f"""{base_context}

Generate a complete {file_type} file for this scenario tool.
Follow amplifier patterns and best practices.
Make it functional and ready to use.

Return ONLY the code/content, no explanations."""


def build_ccsdk_prompt(tool_name: str, requirements: dict[str, Any]) -> str:
    """Build a comprehensive CCSDK prompt for tool generation.

    Args:
        tool_name: Name of the tool to generate
        requirements: Full requirements for the tool

    Returns:
        Formatted prompt for CCSDK
    """
    return f"""Create an amplifier scenario tool named '{tool_name}'.

Requirements:
{json.dumps(requirements, indent=2)}

The tool should:
1. Follow amplifier scenario patterns (like blog_writer, article_illustrator)
2. Use Click for CLI interface
3. Include proper logging
4. Use CCSDK for AI operations
5. Be fully functional and ready to use
6. Include proper error handling
7. Have clear documentation

Generate a complete, working implementation."""


async def generate_variant_implementation(
    variant_name: str,
    task_variation: str,
    base_requirements: dict[str, Any]
) -> str:
    """Generate implementation for a specific variant.

    Args:
        variant_name: Name of the variant
        task_variation: Specific variation of the task
        base_requirements: Base requirements for all variants

    Returns:
        Generated implementation code
    """
    prompt = f"""
Create a variant implementation for '{variant_name}'.

Task Variation: {task_variation}

Base Requirements:
{json.dumps(base_requirements, indent=2)}

This variant should:
1. Implement the specific approach described in the task variation
2. Be different from other variants in meaningful ways
3. Follow amplifier patterns
4. Be fully functional

Generate the complete implementation code.
"""

    options = SessionOptions(
        system_prompt="You are an expert Python developer creating amplifier scenario tools.",
        retry_attempts=2
    )

    try:
        async with ClaudeSession(options) as session:
            response = await session.query(prompt)
            return response.content.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to generate variant implementation: {e}")
