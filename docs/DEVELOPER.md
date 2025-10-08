# Amplifier Developer Guide

This guide is for developers who want to build modules for Amplifier or contribute to the core platform.

## Architecture Overview

Amplifier follows a modular architecture inspired by the Linux kernel:
- **Ultra-thin core**: Minimal coordination layer
- **Everything is a module**: Even the agent loop is swappable  
- **Stable interfaces**: APIs never break, only extend
- **Distributed development**: Teams work independently on modules

## Development Setup

### Prerequisites
- Python 3.11+
- Git
- Poetry (recommended) or pip

### Getting Started

```bash
# Install Amplifier
pip install amplifier

# Or install from source
git clone https://github.com/microsoft/amplifier.git
cd amplifier
pip install -e ".[all]"
```

## Creating a Module

### Module Types

1. **Orchestrator Modules** - Control the agent loop
2. **Provider Modules** - Connect to LLM providers
3. **Tool Modules** - Add capabilities (file ops, web, etc.)
4. **Agent Modules** - Specialized sub-agents
5. **Context Modules** - Manage conversation state
6. **Hook Modules** - Extend lifecycle events

### Module Structure

```
amplifier-module-{name}/
├── pyproject.toml          # Module metadata and dependencies
├── README.md               # Module documentation
├── amplifier_mod_{name}/
│   ├── __init__.py        # Module entry point with mount()
│   └── ...                # Implementation files
└── tests/
    └── test_{name}.py     # Module tests
```

### Basic Module Template

```python
# amplifier_mod_example/__init__.py
from typing import Any, Dict, Optional
import logging

from amplifier_core import ModuleCoordinator

logger = logging.getLogger(__name__)

# Module metadata
__version__ = "0.1.0"
__module_type__ = "tool"  # or: orchestrator, provider, agent, context, hooks

async def mount(coordinator: ModuleCoordinator, config: Optional[Dict[str, Any]] = None):
    """Mount function - called when module is loaded.
    
    Args:
        coordinator: The module coordinator for registering components
        config: Module-specific configuration
    """
    config = config or {}
    
    # Register your module's components
    # For tool module:
    tool = MyTool(config)
    await coordinator.mount('tools', tool, name=tool.name)
    
    logger.info(f"Mounted {__module_type__} module: example")
    return None
```

## Module Development Guidelines

### 1. Follow the Interface Contracts

```python
# Tool module example
class MyTool:
    name = "my_tool"
    description = "Does something useful"
    
    async def execute(self, input: Dict[str, Any]) -> ToolResult:
        """Execute the tool."""
        # Your implementation
        return ToolResult(
            success=True,
            output="Tool executed successfully"
        )
```

### 2. Keep Modules Focused

- **Do one thing well** (Unix philosophy)
- Avoid dependencies on other modules
- Use standard interfaces for communication

### 3. Handle Errors Gracefully

```python
async def execute(self, input: Dict[str, Any]) -> ToolResult:
    try:
        # Your logic
        result = await self.do_work(input)
        return ToolResult(success=True, output=result)
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return ToolResult(
            success=False,
            error={'message': str(e)}
        )
```

### 4. Configuration

Modules receive configuration through the mount function:

```python
async def mount(coordinator: ModuleCoordinator, config: Optional[Dict[str, Any]] = None):
    # Use configuration with defaults
    timeout = config.get('timeout', 30) if config else 30
    retries = config.get('retries', 3) if config else 3
```

### 5. Testing

Write comprehensive tests:

```python
import pytest
from amplifier_core.testing import TestCoordinator

@pytest.mark.asyncio
async def test_module_mount():
    coordinator = TestCoordinator()
    config = {'setting': 'value'}
    
    # Test mounting
    await mount(coordinator, config)
    
    # Verify registration
    assert 'my_tool' in coordinator.get_tools()

@pytest.mark.asyncio 
async def test_tool_execution():
    tool = MyTool({})
    result = await tool.execute({'input': 'test'})
    
    assert result.success
    assert 'successfully' in result.output
```

## Contributing to Core

### Core Principles

1. **Never break userspace** - Stable APIs are forever
2. **Code talks** - Working implementations over discussions
3. **Simplicity** - Every line must justify its existence
4. **Performance matters** - Optimize hot paths

### Submitting Changes

1. **Modules**: Submit PRs to individual module repos
2. **Core**: RFC process for API changes
3. **Documentation**: Keep docs in sync with code

### RFC Process

For core API changes:

1. Create RFC document in GitHub Discussions
2. Include:
   - Problem statement
   - Proposed solution
   - Backward compatibility analysis
   - Example usage
3. 2-week comment period
4. Core team review and decision

## Best Practices

### Module Naming
- Use descriptive names: `amplifier-module-{type}-{name}`
- Examples: `amplifier-module-tool-git`, `amplifier-module-agent-reviewer`

### Versioning
- Follow semantic versioning
- Module versions independent of core
- Document breaking changes

### Documentation
- Clear README with examples
- Inline code documentation
- Configuration examples

### Performance
- Profile before optimizing
- Async where beneficial
- Minimize memory usage

## Publishing Modules

### Official Modules
1. High quality and well-tested
2. Submit proposal via GitHub Discussions
3. Core team review
4. Coordinate with maintainers for inclusion

### Community Modules
1. Publish to your own GitHub/PyPI
2. Add to awesome-amplifier list
3. Use `amplifier-module-` prefix

## Resources

- **Core API Docs**: [amplifier-core](https://github.com/microsoft/amplifier-core)
- **Official Modules**: Browse published modules on PyPI with `amplifier-module-` prefix
- **Testing Utils**: `amplifier_core.testing`
- **Discussions**: GitHub Discussions for questions and proposals

## Philosophy

Remember our guiding principles:
- **Ruthless simplicity** - Start minimal, grow as needed
- **Modular blocks** - Build like LEGO bricks
- **Working code** - Ship early, iterate often
- **User focus** - Solve real problems

## Getting Help

- GitHub Discussions: Technical questions
- Module Showcase: Learn from examples
- Core Team: API and architecture questions
