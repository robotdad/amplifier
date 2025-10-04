"""Extract patterns from exemplar scenario tools.

This module analyzes existing scenario tools to extract their structure,
coding patterns, and conventions. It provides the intelligence needed
to understand what makes a good amplifier scenario tool.
"""

import ast
import re
from pathlib import Path
from typing import Any


def analyze_exemplars(exemplar_paths: list[Path]) -> dict[str, Any]:
    """Extract structure and coding patterns from exemplar scenarios.

    Args:
        exemplar_paths: List of paths to exemplar scenario tools

    Returns:
        Dictionary containing extracted patterns and structures
    """
    patterns = {
        "common_files": {},
        "import_patterns": set(),
        "cli_patterns": [],
        "class_patterns": [],
        "logging_patterns": [],
        "config_patterns": [],
    }

    for path in exemplar_paths:
        if not path.exists():
            continue

        # Analyze directory structure
        tool_structure = identify_key_files(path)
        for file_type, file_path in tool_structure.items():
            if file_type not in patterns["common_files"]:
                patterns["common_files"][file_type] = []
            patterns["common_files"][file_type].append(file_path)

            # Extract coding patterns from each file
            if file_path and file_path.exists():
                file_patterns = extract_coding_patterns(file_path)
                patterns["import_patterns"].update(file_patterns.get("imports", []))
                patterns["cli_patterns"].extend(file_patterns.get("cli_patterns", []))
                patterns["class_patterns"].extend(file_patterns.get("classes", []))
                patterns["logging_patterns"].extend(file_patterns.get("logging", []))
                patterns["config_patterns"].extend(file_patterns.get("config", []))

    # Convert sets to lists for JSON serialization
    patterns["import_patterns"] = list(patterns["import_patterns"])

    return patterns


def identify_key_files(tool_path: Path) -> dict[str, Path | None]:
    """Map tool structure to identify which files exist and their roles.

    Args:
        tool_path: Path to the scenario tool directory

    Returns:
        Dictionary mapping file types to their paths
    """
    structure = {
        "__init__": None,
        "__main__": None,
        "main": None,
        "config": None,
        "README": None,
        "cli_entry": None,
        "core_logic": None,
    }

    # Check for standard files
    if (tool_path / "__init__.py").exists():
        structure["__init__"] = tool_path / "__init__.py"

    if (tool_path / "__main__.py").exists():
        structure["__main__"] = tool_path / "__main__.py"

    if (tool_path / "main.py").exists():
        structure["main"] = tool_path / "main.py"

    if (tool_path / "config.py").exists():
        structure["config"] = tool_path / "config.py"

    if (tool_path / "README.md").exists():
        structure["README"] = tool_path / "README.md"

    # Look for CLI entry point patterns
    for file_path in tool_path.glob("*.py"):
        content = file_path.read_text()
        if "if __name__ == '__main__':" in content or "@click.command" in content:
            structure["cli_entry"] = file_path

        # Identify core logic files (those with main functions/classes)
        if "async def main" in content or "def main" in content or "class" in content:
            if not structure["core_logic"]:
                structure["core_logic"] = file_path

    return structure


def extract_coding_patterns(file_path: Path) -> dict[str, Any]:
    """Extract import patterns, class structures, and CLI patterns from a file.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        Dictionary containing extracted patterns
    """
    patterns = {"imports": [], "cli_patterns": [], "classes": [], "logging": [], "config": [], "async_patterns": []}

    try:
        content = file_path.read_text()

        # Extract imports using regex (more reliable than AST for partial files)
        import_pattern = r"^(from\s+[\w\.]+\s+import\s+.+|import\s+[\w\.]+.*)$"
        imports = re.findall(import_pattern, content, re.MULTILINE)
        patterns["imports"] = imports

        # Extract CLI patterns
        if "@click" in content:
            cli_patterns = re.findall(r"@click\.\w+\([^)]*\)", content)
            patterns["cli_patterns"] = cli_patterns

        # Extract logging patterns
        if "logger" in content or "logging" in content:
            log_patterns = re.findall(r"logger\.\w+\([^)]*\)", content)[:3]  # Sample
            patterns["logging"] = log_patterns

        # Check for async patterns
        if "async def" in content:
            patterns["async_patterns"].append("async/await")
        if "asyncio" in content:
            patterns["async_patterns"].append("asyncio")

        # Try to parse with AST for class structure
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                        "has_init": any(m.name == "__init__" for m in node.body if isinstance(m, ast.FunctionDef)),
                    }
                    patterns["classes"].append(class_info)
        except SyntaxError:
            # File might have syntax issues or be incomplete
            pass

        # Extract configuration patterns
        if "Config" in content or "config" in content.lower():
            config_patterns = re.findall(r"(class\s+\w*Config.*:|config\s*=\s*{)", content)
            patterns["config"] = config_patterns[:3]  # Sample

    except Exception:
        # If file can't be read or analyzed, return empty patterns
        pass

    return patterns


def extract_tool_metadata(tool_path: Path) -> dict[str, Any]:
    """Extract metadata about the tool from its files.

    Args:
        tool_path: Path to the scenario tool

    Returns:
        Dictionary with tool metadata
    """
    metadata = {
        "name": tool_path.name,
        "has_tests": (tool_path / "tests").exists() or (tool_path / "test.py").exists(),
        "has_readme": (tool_path / "README.md").exists(),
        "file_count": len(list(tool_path.glob("*.py"))),
        "is_async": False,
        "uses_click": False,
        "uses_ccsdk": False,
    }

    # Check for async and library usage
    for py_file in tool_path.glob("*.py"):
        try:
            content = py_file.read_text()
            if "async def" in content or "asyncio" in content:
                metadata["is_async"] = True
            if "@click" in content or "import click" in content:
                metadata["uses_click"] = True
            if "ccsdk" in content or "from amplifier.ccsdk" in content:
                metadata["uses_ccsdk"] = True
        except Exception:
            continue

    return metadata
