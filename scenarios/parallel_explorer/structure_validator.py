"""Validate generated scenario tools.

This module validates that generated scenario tools have the correct
structure, can be imported, and have functional CLI interfaces.
"""

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path


def validate_tool_structure(tool_path: Path) -> tuple[bool, list[str]]:
    """Check tool has required files and structure.

    Args:
        tool_path: Path to the scenario tool directory

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check if path exists and is a directory
    if not tool_path.exists():
        issues.append(f"Tool directory does not exist: {tool_path}")
        return False, issues

    if not tool_path.is_dir():
        issues.append(f"Tool path is not a directory: {tool_path}")
        return False, issues

    # Required files for a minimal tool
    required_files = {
        "__init__.py": "Module initialization file",
        "main.py": "Main implementation file",
    }

    # Check for required files
    for file_name, description in required_files.items():
        file_path = tool_path / file_name
        if not file_path.exists():
            issues.append(f"Missing required file: {file_name} ({description})")

    # Check if either __main__.py exists or main.py has if __name__ == "__main__"
    has_entry_point = False
    main_file = tool_path / "main.py"
    dunder_main = tool_path / "__main__.py"

    if dunder_main.exists():
        has_entry_point = True
    elif main_file.exists():
        try:
            content = main_file.read_text()
            if 'if __name__ == "__main__":' in content:
                has_entry_point = True
        except Exception:
            issues.append("Cannot read main.py to check for entry point")

    if not has_entry_point:
        issues.append("No entry point found (__main__.py or if __name__ block in main.py)")

    # Check for README
    if not (tool_path / "README.md").exists():
        issues.append("Missing README.md documentation")

    # Check __init__.py exports
    init_file = tool_path / "__init__.py"
    if init_file.exists():
        try:
            content = init_file.read_text()
            if "__all__" not in content and "from" not in content and "import" not in content:
                issues.append("__init__.py appears empty or incomplete")
        except Exception:
            issues.append("Cannot validate __init__.py content")

    # Check for at least one Python file with actual code
    has_code = False
    for py_file in tool_path.glob("*.py"):
        try:
            content = py_file.read_text()
            # Look for function or class definitions
            if "def " in content or "class " in content:
                has_code = True
                break
        except Exception:
            continue

    if not has_code:
        issues.append("No Python code found (no functions or classes defined)")

    return len(issues) == 0, issues


def validate_imports(tool_path: Path) -> bool:
    """Verify tool can be imported.

    Args:
        tool_path: Path to the scenario tool directory

    Returns:
        True if tool can be imported successfully
    """
    # Add parent directory to path so we can import the module
    parent_dir = tool_path.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

    module_name = tool_path.name

    try:
        # Try to import the module
        spec = importlib.util.spec_from_file_location(module_name, tool_path / "__init__.py")

        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True
        return False

    except Exception as e:
        # Import failed
        print(f"Import validation failed: {e}")
        return False
    finally:
        # Clean up sys.path
        if str(parent_dir) in sys.path:
            sys.path.remove(str(parent_dir))


def check_cli_interface(tool_path: Path) -> bool:
    """Verify CLI command works.

    Args:
        tool_path: Path to the scenario tool directory

    Returns:
        True if CLI interface works
    """
    try:
        # Try running the tool with --help
        result = subprocess.run(
            [sys.executable, "-m", tool_path.name, "--help"],
            cwd=tool_path.parent,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Check if help text was displayed
        if result.returncode == 0 and ("usage" in result.stdout.lower() or "help" in result.stdout.lower()):
            return True

        # Also try running main.py directly
        main_file = tool_path / "main.py"
        if main_file.exists():
            result = subprocess.run(
                [sys.executable, str(main_file), "--help"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return True

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

    return False


def validate_syntax(file_path: Path) -> tuple[bool, str | None]:
    """Validate Python syntax of a file.

    Args:
        file_path: Path to Python file to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path) as f:
            source = f.read()

        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def validate_all_syntax(tool_path: Path) -> dict[str, tuple[bool, str | None]]:
    """Validate syntax of all Python files in tool.

    Args:
        tool_path: Path to the scenario tool directory

    Returns:
        Dictionary mapping file names to validation results
    """
    results = {}

    for py_file in tool_path.glob("**/*.py"):
        relative_path = py_file.relative_to(tool_path)
        is_valid, error = validate_syntax(py_file)
        results[str(relative_path)] = (is_valid, error)

    return results


def check_dependencies(tool_path: Path) -> list[str]:
    """Check for missing dependencies in the tool.

    Args:
        tool_path: Path to the scenario tool directory

    Returns:
        List of potentially missing dependencies
    """
    missing = []
    imports_to_check = set()

    # Scan all Python files for imports
    for py_file in tool_path.glob("**/*.py"):
        try:
            content = py_file.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_to_check.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports_to_check.add(node.module.split(".")[0])
        except Exception:
            continue

    # Check if imports can be resolved
    for module_name in imports_to_check:
        # Skip standard library modules
        if module_name in sys.stdlib_module_names:
            continue

        try:
            __import__(module_name)
        except ImportError:
            missing.append(module_name)

    return missing
