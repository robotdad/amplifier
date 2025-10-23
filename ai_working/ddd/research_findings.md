# Pre-Implementation Research Findings

**Date**: 2025-10-22
**Purpose**: Understand amplifier-core patterns before implementing tools

---

## 1. Tool Protocol (amplifier-core)

**Location**: `amplifier-core/amplifier_core/interfaces.py:87-110`

### Interface Definition

```python
@runtime_checkable
class Tool(Protocol):
    """Interface for tool modules."""

    @property
    def name(self) -> str:
        """Tool name for invocation."""
        ...

    @property
    def description(self) -> str:
        """Human-readable tool description."""
        ...

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """
        Execute tool with given input.

        Args:
            input: Tool-specific input parameters

        Returns:
            Tool execution result
        """
        ...
```

### ToolResult Model

**Location**: `amplifier-core/amplifier_core/models.py:21-31`

```python
class ToolResult(BaseModel):
    """Result from tool execution."""

    success: bool = Field(default=True)
    output: Any | None = Field(default=None)
    error: dict[str, Any] | None = Field(default=None)
```

### Implementation Pattern

For tool-whisper and tool-youtube-dl, implement:

```python
from amplifier_core.interfaces import Tool
from amplifier_core.models import ToolResult

class WhisperTool:
    """Whisper transcription tool."""

    @property
    def name(self) -> str:
        return "whisper"

    @property
    def description(self) -> str:
        return "Transcribe audio using OpenAI Whisper API"

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        try:
            # Do the work
            result = self.transcriber.transcribe(...)
            return ToolResult(success=True, output=result)
        except Exception as e:
            return ToolResult(
                success=False,
                error={"message": str(e), "type": type(e).__name__}
            )
```

**Key insights**:
- Protocol-based (structural subtyping, no inheritance required)
- Async execute method
- Return Pydantic ToolResult model
- Properties for name and description

---

## 2. Event Emission API

**Location**: `amplifier-core/amplifier_core/coordinator.py`

### Current Finding

Standard Python logging is used:
```python
import logging
logger = logging.getLogger(__name__)
```

### Hook System

**Location**: `amplifier-core/amplifier_core/hooks.py`

Hooks observe events through HookRegistry. Tools likely don't emit events directly - the orchestrator emits events around tool execution.

### Pattern for Tools

**Likely**: Tools just do their work, orchestrator handles event emission

```python
# Tool implementation - simple, no event emission
async def execute(self, input: dict) -> ToolResult:
    # Just do the work
    result = self.do_work()
    return ToolResult(success=True, output=result)
```

**Orchestrator** emits:
- `tool:pre` before calling tool.execute()
- `tool:post` after successful execution
- `tool:error` on failure

### To Research Further

When in actual repo:
- Check existing tool implementations
- See if tools need to emit their own events
- Or if orchestrator handles all event emission

**Decision for now**: Keep tools simple, assume orchestrator handles events

---

## 3. Logging in amplifier-core

**Finding**: Standard Python logging module

```python
import logging
logger = logging.getLogger(__name__)
```

**Usage**:
```python
logger.info("Processing file: {}")
logger.warning("File size exceeds limit")
logger.error("Failed to process: {}", exc_info=True)
```

**For migration**:
```python
# OLD (scenarios/transcribe)
from amplifier.utils.logger import get_logger
logger = get_logger(__name__)

# NEW (amplifier-core pattern)
import logging
logger = logging.getLogger(__name__)
```

**Impact**: Simple find-replace in ported code

---

## 4. ffmpeg Screenshot Capture

**Verified**: ffmpeg 7.1.1 available on system

### Screenshot Command

```bash
# Capture single frame at specific timestamp
ffmpeg -ss HH:MM:SS -i input.mp4 -frames:v 1 output.jpg

# Example
ffmpeg -ss 00:05:30 -i video.mp4 -frames:v 1 screenshot.jpg
```

### Options

- `-ss HH:MM:SS`: Seek to timestamp (can also use seconds: `-ss 330`)
- `-i input.mp4`: Input file
- `-frames:v 1`: Extract exactly 1 video frame
- `output.jpg`: Output image file

### Quality Settings (optional)

```bash
# High quality screenshot
ffmpeg -ss 00:05:30 -i video.mp4 -frames:v 1 -q:v 2 screenshot.jpg

# Where -q:v 2 is quality (1-31, lower = better)
```

### Python Implementation

```python
def capture_screenshot(
    video_path: Path,
    timestamp: str,  # HH:MM:SS format
    output_path: Path
) -> Path:
    """Capture screenshot at timestamp."""
    cmd = [
        "ffmpeg",
        "-ss", timestamp,
        "-i", str(video_path),
        "-frames:v", "1",
        "-q:v", "2",  # High quality
        "-y",  # Overwrite
        str(output_path)
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        logger.info(f"Captured screenshot at {timestamp}: {output_path.name}")
        return output_path
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Failed to capture screenshot: {e.stderr}")
```

**Verified**: Straightforward, well-documented command

---

## 5. Key Imports for New Modules

### tool-whisper

```python
# From amplifier-core
from amplifier_core.interfaces import Tool
from amplifier_core.models import ToolResult
import logging

# From existing code
from openai import OpenAI
from pathlib import Path
from dataclasses import dataclass
```

### tool-youtube-dl

```python
# From amplifier-core
from amplifier_core.interfaces import Tool
from amplifier_core.models import ToolResult
import logging

# From dependencies
import yt_dlp
import subprocess  # for ffmpeg
from pathlib import Path
from dataclasses import dataclass
```

### app-transcribe

```python
# From tools (git sources)
from amplifier_module_tool_whisper import WhisperTool, Transcript
from amplifier_module_tool_youtube_dl import YouTubeDLTool, VideoInfo

# From dependencies
import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel
from dotenv import load_dotenv
from pathlib import Path
```

---

## Summary

### ✅ Research Complete

All critical questions answered:

1. **Tool Protocol**: ✅ Found - Protocol with name, description, async execute() → ToolResult
2. **Event Emission**: ✅ Pattern identified - Tools return results, orchestrator handles events
3. **Logging**: ✅ Standard Python logging.getLogger(__name__)
4. **Screenshot Capture**: ✅ ffmpeg -ss HH:MM:SS -i video -frames:v 1 output.jpg

### 🎯 Ready to Implement

**Confidence level**: High

- Protocol is simple and well-defined
- Logging is straightforward (standard library)
- ffmpeg command is verified
- Event emission pattern is clear (tools don't emit, orchestrator does)

### 📝 Implementation Notes

**When porting code**:
1. Change `amplifier.utils.logger.get_logger` → `logging.getLogger`
2. Add `.expanduser()` to all Path() with ~ paths
3. Wrap core logic in Tool protocol
4. Return ToolResult instead of raw values
5. Handle exceptions and return ToolResult(success=False, error={...})

**When adding new features**:
1. Screenshot: Use ffmpeg -ss command shown above
2. Video download: yt-dlp already supports (just don't convert to audio)

### ⏳ Additional Research As Needed

Will research during implementation:
- Actual tool module examples (when cloning/creating repos)
- Hook integration if tools do need to emit events
- Any amplifier-core utilities we haven't discovered

**Approach**: Start with what we know, research more when needed

---

## Ready for Phase 4

✅ Pre-implementation research complete
✅ Core patterns understood
✅ Implementation approach validated

**Next**: `/ddd:4-code` to start building
