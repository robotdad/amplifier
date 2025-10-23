# Code Implementation Plan: Transcribe Migration

**Generated**: 2025-10-22
**Based on**: Phase 1 plan + Phase 2 documentation
**Source**: scenarios/transcribe (~2660 lines) → 3 new repositories

---

## Summary

Port transcribe functionality from monolithic scenario to modular architecture:
1. **tool-whisper** - Whisper API integration (~250 lines new code)
2. **tool-youtube-dl** - YouTube download + video + screenshots (~400 lines new code)
3. **app-transcribe** - Complete app with Rich CLI (~900 lines new code)

**Total implementation**: ~1550 lines new code (porting + new features)

---

## Repository 1: tool-whisper

**Location**: `robotdad/amplifier-module-tool-whisper`

### Current State
- ✅ Source exists: `scenarios/transcribe/whisper_transcriber/core.py` (159 lines)
- ❌ Missing: Tool protocol wrapper, event emission, pyproject.toml
- ❌ Missing: Tests, entry points

### Files to Create

#### 1. src/amplifier_module_tool_whisper/core.py
**Source**: Port from `scenarios/transcribe/whisper_transcriber/core.py`
**Lines**: ~160 lines (mostly direct port)
**Changes needed**:
- Update imports: `amplifier.utils.logger` → TBD (check amplifier-core)
- Add `.expanduser()` to any path handling
- Keep all existing logic (Whisper API calls, retry, cost estimation)
- Keep `Transcript` and `TranscriptSegment` dataclasses

**Classes**:
- `TranscriptSegment` - Dataclass for segment data
- `Transcript` - Dataclass for full transcript
- `WhisperTranscriber` - Core logic (existing)

#### 2. src/amplifier_module_tool_whisper/whisper_tool.py (NEW)
**Lines**: ~90 lines
**Purpose**: Wrap WhisperTranscriber in Tool protocol

```python
from amplifier_core.tool import Tool  # Or wherever Tool protocol is
from .core import WhisperTranscriber, Transcript

class WhisperTool(Tool):
    """OpenAI Whisper transcription tool."""

    def __init__(self, config: dict):
        self.output_dir = Path(config.get("output_dir", "~/transcripts")).expanduser()
        self.model = config.get("model", "whisper-1")
        self.transcriber = WhisperTranscriber(model=self.model)

    async def execute(self, input_data: dict) -> dict:
        """
        Input: {
            "audio_path": str,
            "language": str?,
            "prompt": str?
        }
        Output: {
            "text": str,
            "segments": [...],
            "duration": float,
            "language": str,
            "cost": float
        }
        """
        # Emit tool:pre event
        # Call transcriber.transcribe()
        # Emit tool:post event
        # Return structured result
```

**Dependencies**:
- amplifier-core (Tool protocol, event emission)
- Need to understand: How to emit events in amplifier-dev

#### 3. pyproject.toml (NEW)
**Lines**: ~40 lines
**Content**:
```toml
[project]
name = "amplifier-module-tool-whisper"
version = "0.1.0"
description = "OpenAI Whisper transcription tool for Amplifier"
dependencies = [
    "amplifier-core",
    "openai>=1.0.0",
]

[project.scripts]
# Entry point for CLI testing (optional)

[project.entry-points."amplifier.modules"]
"tool-whisper" = "amplifier_module_tool_whisper:WhisperTool"

[tool.uv.sources]
amplifier-core = {
    git = "https://github.com/microsoft/amplifier-dev",
    subdirectory = "amplifier-core",
    branch = "main"
}

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### 4. src/amplifier_module_tool_whisper/__init__.py (NEW)
**Lines**: ~5 lines
**Content**:
```python
from .whisper_tool import WhisperTool
from .core import Transcript, TranscriptSegment, WhisperTranscriber

__all__ = ["WhisperTool", "Transcript", "TranscriptSegment", "WhisperTranscriber"]
```

#### 5. tests/test_whisper_tool.py (NEW)
**Lines**: ~100 lines
**Tests**:
- Test WhisperTool initialization
- Test execute() with mocked OpenAI
- Test cost estimation
- Test file size validation (25MB limit)
- Test retry logic
- Test event emission

### Implementation Chunk

**Chunk 1: tool-whisper complete**
- Port core.py (~160 lines)
- Create whisper_tool.py (~90 lines)
- Create pyproject.toml (~40 lines)
- Create __init__.py (~5 lines)
- Create tests (~100 lines)
- **Total**: ~395 lines
- **Commit point**: After tests pass

**Dependencies**: Need to understand amplifier-core Tool protocol first

---

## Repository 2: tool-youtube-dl

**Location**: `robotdad/amplifier-module-tool-youtube-dl`

### Current State
- ✅ Source exists: `scenarios/transcribe/video_loader/core.py` (212 lines)
- ✅ Source exists: `scenarios/transcribe/audio_extractor/core.py` (189 lines)
- ❌ Missing: Video download support (currently audio-only)
- ❌ Missing: Screenshot capture feature (NEW requirement)
- ❌ Missing: Tool protocol wrapper, event emission

### Files to Create

#### 1. src/amplifier_module_tool_youtube_dl/core.py
**Source**: Port from `scenarios/transcribe/video_loader/core.py`
**Lines**: ~350 lines (port + enhancements)
**Changes needed**:
- Port existing logic (212 lines base)
- **Add video download** support (audio_only: False path)
- **Add screenshot capture** using ffmpeg
- Add `.expanduser()` to path handling
- Keep `VideoInfo` dataclass

**Classes**:
- `VideoInfo` - Dataclass (existing)
- `VideoLoader` - Core logic (existing + enhancements)

**New methods to add**:
```python
def capture_screenshot(
    self,
    video_path: Path,
    timestamp: str,  # HH:MM:SS format
    output_path: Path
) -> Path:
    """Capture screenshot at specific timestamp using ffmpeg."""
    # ffmpeg -ss HH:MM:SS -i video.mp4 -frames:v 1 screenshot.jpg
```

#### 2. src/amplifier_module_tool_youtube_dl/audio_utils.py
**Source**: Port from `scenarios/transcribe/audio_extractor/core.py`
**Lines**: ~190 lines (mostly direct port)
**Purpose**: ffmpeg audio operations (extract, compress)

**Decision**: Include audio compression here because:
- YouTube downloads might need compression for Whisper's 25MB limit
- Useful for the tool's consumers
- Self-contained module

#### 3. src/amplifier_module_tool_youtube_dl/youtube_tool.py (NEW)
**Lines**: ~100 lines
**Purpose**: Wrap VideoLoader in Tool protocol

```python
class YouTubeDLTool(Tool):
    """YouTube download tool with video + screenshot support."""

    async def execute(self, input_data: dict) -> dict:
        """
        Input: {
            "url": str,
            "audio_only": bool?,
            "output_filename": str?,
            "use_cache": bool?,
            "capture_screenshot": bool?,
            "screenshot_time": str?  # HH:MM:SS
        }
        Output: {
            "path": str,
            "metadata": VideoInfo,
            "screenshot_path": str?
        }
        """
```

#### 4. pyproject.toml (NEW)
**Lines**: ~45 lines
Similar to tool-whisper but with additional dependencies:
```toml
dependencies = [
    "amplifier-core",
    "yt-dlp>=2024.0.0",
]
```

**Note**: ffmpeg is external dependency (documented in README)

#### 5. tests/test_youtube_tool.py (NEW)
**Lines**: ~150 lines
**Tests**:
- Test metadata extraction (mocked yt-dlp)
- Test audio download with caching
- Test video download
- Test screenshot capture
- Test local file handling
- Test event emission

### Implementation Chunk

**Chunk 2: tool-youtube-dl complete**
- Port core.py + add video/screenshot (~350 lines)
- Port audio_utils.py (~190 lines)
- Create youtube_tool.py (~100 lines)
- Create pyproject.toml (~45 lines)
- Create __init__.py (~8 lines)
- Create tests (~150 lines)
- **Total**: ~843 lines
- **Commit point**: After tests pass

**Dependencies**: Need amplifier-core Tool protocol

---

## Repository 3: app-transcribe

**Location**: `robotdad/amplifier-app-transcribe`

### Current State
- ✅ Source exists: Multiple modules in `scenarios/transcribe/`
- ❌ Missing: Rich CLI, .env support, tool composition
- ❌ Missing: pyproject.toml with git sources to tools

### Files to Create

#### 1. src/amplifier_app_transcribe/pipeline.py
**Source**: Port from `scenarios/transcribe/main.py`
**Lines**: ~350 lines (adapt to use tools)
**Changes**:
- Replace direct WhisperTranscriber → use WhisperTool
- Replace direct VideoLoader → use YouTubeDLTool
- Keep pipeline orchestration logic
- Keep audio_extractor for compression (before passing to WhisperTool)
- Add `.expanduser()` to all paths

**Class**:
```python
class TranscriptionPipeline:
    def __init__(
        self,
        whisper_tool: WhisperTool,
        youtube_tool: YouTubeDLTool,
        state_manager: StateManager,
        enhance: bool = True
    ):
        self.whisper = whisper_tool
        self.youtube = youtube_tool
        self.state = state_manager
        # ... rest of init
```

#### 2. src/amplifier_app_transcribe/state.py
**Source**: Direct port from `scenarios/transcribe/state.py`
**Lines**: ~180 lines (mostly unchanged)
**Changes**:
- Update imports
- Add `.expanduser()` to session_dir path
- Keep checkpoint/resume logic intact

#### 3. src/amplifier_app_transcribe/storage.py
**Source**: Port from `scenarios/transcribe/storage/core.py`
**Lines**: ~370 lines (simplified)
**Changes**:
- Remove dual-directory complexity (just use ~/transcripts)
- Add `.expanduser()` to output_dir
- Keep all format saving (JSON, MD, VTT, SRT)
- Keep insights saving

#### 4. src/amplifier_app_transcribe/formatter.py
**Source**: Port from `scenarios/transcribe/transcript_formatter/core.py`
**Lines**: ~270 lines (direct port)
**No changes** - formatting logic is perfect as-is

#### 5. src/amplifier_app_transcribe/insights.py
**Source**: Combine `insights_generator/`, `summary_generator/`, `quote_extractor/`
**Lines**: ~250 lines (consolidate 3 modules)
**Changes**:
- Combine into single module
- Update imports for new structure

#### 6. src/amplifier_app_transcribe/audio_utils.py
**Source**: Port from `scenarios/transcribe/audio_extractor/core.py`
**Lines**: ~190 lines
**Purpose**: ffmpeg audio compression (needed before Whisper API)

#### 7. src/amplifier_app_transcribe/cli.py (NEW)
**Lines**: ~200 lines
**Purpose**: Rich CLI interface

```python
import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel

console = Console()

@click.command()
@click.argument("sources", nargs=-1)
@click.option("--resume", is_flag=True)
@click.option("--output-dir", type=click.Path())
@click.option("--no-enhance", is_flag=True)
@click.option("--force-download", is_flag=True)
def transcribe(sources, resume, output_dir, no_enhance, force_download):
    """Transcribe videos with beautiful Rich output."""

    # Load .env if exists
    # Initialize tools
    # Run pipeline with Rich progress
    # Display results table
```

#### 8. src/amplifier_app_transcribe/__init__.py (NEW)
**Lines**: ~10 lines

#### 9. src/amplifier_app_transcribe/__main__.py (NEW)
**Lines**: ~5 lines
**Purpose**: Enable `python -m amplifier_app_transcribe`

#### 10. .env.example (NEW)
Already created in templates

#### 11. pyproject.toml (NEW)
**Lines**: ~60 lines
**Content**:
```toml
[project]
name = "amplifier-app-transcribe"
version = "0.1.0"
description = "Turn videos into searchable transcripts"
dependencies = [
    "amplifier-module-tool-whisper",
    "amplifier-module-tool-youtube-dl",
    "anthropic>=0.25.0",
    "click>=8.0",
    "rich>=13.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
transcribe = "amplifier_app_transcribe.cli:transcribe"

[tool.uv.sources]
amplifier-module-tool-whisper = {
    git = "https://github.com/robotdad/amplifier-module-tool-whisper",
    branch = "main"
}
amplifier-module-tool-youtube-dl = {
    git = "https://github.com/robotdad/amplifier-module-tool-youtube-dl",
    branch = "main"
}
```

#### 12. tests/test_pipeline.py (NEW)
**Lines**: ~150 lines
**Tests**:
- Test pipeline orchestration
- Test state management (checkpoint/resume)
- Test error handling

#### 13. tests/test_cli.py (NEW)
**Lines**: ~100 lines
**Tests**:
- Test CLI argument parsing
- Test .env loading
- Test Rich output (mock console)

### Implementation Chunks

**Chunk 3.1: Core App Logic** (~1000 lines)
- pipeline.py (350)
- state.py (180)
- storage.py (370)
- formatter.py (270)
- insights.py (250)
- audio_utils.py (190)
- **Dependencies**: tool-whisper, tool-youtube-dl must exist first
- **Commit**: After integration tests pass

**Chunk 3.2: Rich CLI** (~200 lines)
- cli.py (200)
- __init__.py (10)
- __main__.py (5)
- **Dependencies**: Chunk 3.1
- **Commit**: After manual testing works

**Chunk 3.3: Tests** (~250 lines)
- test_pipeline.py (150)
- test_cli.py (100)
- **Dependencies**: Chunks 3.1, 3.2
- **Commit**: After all tests pass

---

## Implementation Sequencing

### Phase 1: Build Tools (can be parallel, but doing sequential)

**Week 1**:
1. **tool-whisper** (~395 lines, 1-2 days)
   - Port core logic
   - Create Tool wrapper
   - Add tests
   - Verify independently

2. **tool-youtube-dl** (~843 lines, 2-3 days)
   - Port core logic
   - Add video download
   - Add screenshot capture
   - Create Tool wrapper
   - Add tests
   - Verify independently

**Milestone**: Both tools work independently, can be imported

### Phase 2: Build App (depends on Phase 1)

**Week 2**:
3. **app-transcribe Chunk 1** (~1000 lines, 2-3 days)
   - Port all core app logic
   - Wire up tools
   - Integration tests

4. **app-transcribe Chunk 2** (~200 lines, 1 day)
   - Rich CLI
   - .env support
   - Manual testing

5. **app-transcribe Chunk 3** (~250 lines, 1 day)
   - Complete test suite
   - End-to-end validation

**Milestone**: App works via `uvx --from github...`

---

## New Code vs Ported Code

| Module | Ported | New | Total |
|--------|--------|-----|-------|
| tool-whisper | 160 | 235 | 395 |
| tool-youtube-dl | 401 | 442 | 843 |
| app-transcribe | 1070 | 380 | 1450 |
| **Totals** | **1631** | **1057** | **2688** |

**Ported**: Existing logic from scenarios/transcribe
**New**: Tool wrappers, Rich CLI, tests, config files, .env support

---

## Dependencies Analysis

### External Dependencies

**tool-whisper**:
- openai>=1.0.0
- amplifier-core

**tool-youtube-dl**:
- yt-dlp>=2024.0.0
- amplifier-core
- ffmpeg (external binary)

**app-transcribe**:
- tool-whisper (git source)
- tool-youtube-dl (git source)
- anthropic>=0.25.0
- click>=8.0
- rich>=13.0
- python-dotenv>=1.0.0

### Build Order

```
1. tool-whisper (no dependencies except amplifier-core)
2. tool-youtube-dl (no dependencies except amplifier-core)
3. app-transcribe (depends on tools 1 & 2)
```

Tools can be built in parallel, app must wait for tools.

---

## Research Findings ✅ COMPLETED

**Full details**: `ai_working/ddd/research_findings.md`

### 1. Tool Protocol ✅

**Found**: `amplifier-core/amplifier_core/interfaces.py:87-110`

```python
from amplifier_core.interfaces import Tool
from amplifier_core.models import ToolResult

# Protocol requires:
- @property name -> str
- @property description -> str
- async execute(input: dict) -> ToolResult
```

**ToolResult**: Pydantic model with `success`, `output`, `error`

### 2. Event Emission ✅

**Pattern**: Tools DON'T emit events - orchestrator handles it

- Orchestrator emits `tool:pre` before calling execute()
- Orchestrator emits `tool:post` after success
- Orchestrator emits `tool:error` on failure

**Impact**: Keep tools simple, no event code needed

### 3. Logging ✅

**Pattern**: Standard Python logging

```python
import logging
logger = logging.getLogger(__name__)
```

**Migration**: Replace `amplifier.utils.logger.get_logger` with `logging.getLogger`

### 4. Screenshot Capture ✅

**Command**: `ffmpeg -ss HH:MM:SS -i video.mp4 -frames:v 1 -q:v 2 output.jpg`

**Verified**: ffmpeg 7.1.1 available, command tested

```python
subprocess.run([
    "ffmpeg", "-ss", timestamp,
    "-i", str(video), "-frames:v", "1",
    "-q:v", "2", "-y", str(output)
], check=True)
```

---

## Testing Strategy

### Unit Tests

**tool-whisper**:
- Mock OpenAI API calls
- Test cost calculation formula
- Test file size validation
- Test retry behavior
- **Framework**: pytest with mocking

**tool-youtube-dl**:
- Mock yt-dlp calls
- Mock ffmpeg calls
- Test caching logic
- Test screenshot capture
- Test video vs audio paths
- **Framework**: pytest with mocking

**app-transcribe**:
- Test pipeline orchestration (mocked tools)
- Test state management (checkpoint files)
- Test formatting (real inputs → outputs)
- Test CLI parsing
- **Framework**: pytest

### Integration Tests

**app-transcribe end-to-end**:
- Real tool integration (but small test files)
- Test full pipeline with actual ffmpeg
- Test resume capability
- **Use**: Small test audio files (~10 seconds)

### Manual Testing

**Real-world validation**:
```bash
# Test with real YouTube video
uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe "short-video-url"

# Verify:
- Downloads work
- Transcription works
- Rich output looks good
- Files organized correctly
- Resume works (Ctrl+C then re-run)
```

---

## Philosophy Compliance

### Ruthless Simplicity

**What we're keeping simple**:
- ✅ Tools have single responsibility (transcribe OR download)
- ✅ Direct API calls (no elaborate wrappers)
- ✅ Simple dict-based I/O
- ✅ Straightforward error handling

**What we're NOT building** (YAGNI):
- ❌ Multi-provider transcription (just Whisper)
- ❌ Advanced audio editing (just compression)
- ❌ Cloud storage (just local files)
- ❌ User accounts (single-user app)
- ❌ Web interface (CLI first, web later if needed)

### Modular Design

**Bricks (self-contained)**:
- tool-whisper: Can transcribe without knowing about YouTube
- tool-youtube-dl: Can download without knowing about transcription
- app-transcribe: Composes tools without modifying them

**Studs (stable interfaces)**:
- Tool.execute(input: dict) -> dict
- Event emission protocol
- Git sources for distribution

**Regeneratable**:
- ✅ Each module has clear spec (documentation)
- ✅ Could rebuild any module from spec
- ✅ Interfaces stay stable even if implementation changes

---

## Commit Strategy

### tool-whisper

**Commit 1**: Initial implementation
```
feat: Add tool-whisper OpenAI Whisper integration

- Port WhisperTranscriber from scenarios/transcribe
- Wrap in Tool protocol with event emission
- Add cost estimation and retry logic
- Tests passing

Supports: transcription, multiple languages, timestamped segments
Ready for: amplifier profile usage
```

### tool-youtube-dl

**Commit 1**: Initial implementation
```
feat: Add tool-youtube-dl with video + screenshot support

- Port VideoLoader from scenarios/transcribe
- Add video download support (audio_only: False)
- Add screenshot capture at timestamps (NEW)
- Include audio compression utilities
- Wrap in Tool protocol with event emission
- Tests passing

Supports: YouTube download, local files, caching, screenshots
Ready for: amplifier profile usage
```

### app-transcribe

**Commit 1**: Core app logic
```
feat: Add amplifier-app-transcribe core pipeline

- Port pipeline orchestration, state, storage
- Port formatter and insights generation
- Integrate tool-whisper and tool-youtube-dl
- Integration tests passing

Workflow: download → transcribe → format → insights
```

**Commit 2**: Rich CLI
```
feat: Add Rich CLI interface to transcribe app

- Beautiful progress bars and status updates
- Results summary table
- .env file support
- CLI tests passing

Ready for: uvx distribution
```

**Commit 3**: Final polish
```
feat: Complete transcribe app with full test suite

- End-to-end tests
- Documentation verified
- Manual testing complete

Ready for: production use via uvx
```

---

## Risk Assessment

### High Risk

**Risk**: Tool protocol in amplifier-core is complex or undocumented
**Mitigation**: Study existing tools (tool-bash, tool-filesystem) first
**Fallback**: Simplify wrapper, implement minimal protocol

**Risk**: Git sources don't work as expected
**Mitigation**: Test early with `uv sync`
**Fallback**: Adjust source configuration

### Medium Risk

**Risk**: Rich CLI is harder than expected
**Mitigation**: Start simple, enhance iteratively
**Fallback**: Basic CLI first, Rich later

**Risk**: Screenshot capture is complex
**Mitigation**: ffmpeg is well-documented
**Fallback**: Mark as experimental, document limitations

### Low Risk

**Risk**: Porting logic has subtle bugs
**Mitigation**: Comprehensive tests
**Validation**: Compare outputs with original transcribe

---

## Success Criteria

### tool-whisper Ready When:
- [ ] Can be imported: `from amplifier_module_tool_whisper import WhisperTool`
- [ ] Can transcribe audio file and return Transcript
- [ ] Events emitted correctly
- [ ] Tests pass
- [ ] Can be used in amplifier profile

### tool-youtube-dl Ready When:
- [ ] Can download YouTube audio
- [ ] Can download YouTube video
- [ ] Can capture screenshots
- [ ] Metadata extracted correctly
- [ ] Events emitted
- [ ] Tests pass
- [ ] Can be used in amplifier profile

### app-transcribe Ready When:
- [ ] Can run via: `uvx --from git+https://github.com/robotdad/amplifier-app-transcribe transcribe URL`
- [ ] Downloads work
- [ ] Transcription works
- [ ] Rich CLI displays correctly
- [ ] Files organized as documented
- [ ] Resume works after interruption
- [ ] .env file loaded
- [ ] All tests pass

---

## Agent Orchestration

### Primary Agent: modular-builder

Use for each chunk:

**Chunk 1 (tool-whisper)**:
```
Task modular-builder: "Implement tool-whisper according to:
- Specification: ai_working/ddd/templates/tool-whisper/README.md
- Source code: scenarios/transcribe/whisper_transcriber/core.py
- Code plan: ai_working/ddd/code_plan.md section 'Repository 1'

Create complete module with tests in robotdad/amplifier-module-tool-whisper"
```

**Chunk 2 (tool-youtube-dl)**:
```
Task modular-builder: "Implement tool-youtube-dl with video + screenshot support:
- Specification: ai_working/ddd/templates/tool-youtube-dl/README.md
- Source: scenarios/transcribe/video_loader/ and audio_extractor/
- Add screenshot capture feature
- Code plan: ai_working/ddd/code_plan.md section 'Repository 2'"
```

**Chunk 3 (app-transcribe)**:
```
Task modular-builder: "Implement amplifier-app-transcribe:
- Specification: ai_working/ddd/templates/app-transcribe/README.md
- Source: scenarios/transcribe/main.py, state.py, storage/, formatter/, insights/
- Add Rich CLI and .env support
- Code plan: ai_working/ddd/code_plan.md section 'Repository 3'"
```

### Supporting Agents

**test-coverage**: For test planning
```
Task test-coverage: "Suggest comprehensive tests for [module]"
```

**bug-hunter**: If issues arise
```
Task bug-hunter: "Debug [specific issue]"
```

---

## Estimated Effort

### tool-whisper
- **Port core**: 1-2 hours
- **Tool wrapper**: 1-2 hours
- **Tests**: 1-2 hours
- **Total**: 3-6 hours, ~395 lines

### tool-youtube-dl
- **Port core + enhancements**: 2-3 hours
- **Screenshot feature**: 1-2 hours
- **Tool wrapper**: 1-2 hours
- **Tests**: 2-3 hours
- **Total**: 6-10 hours, ~843 lines

### app-transcribe
- **Port core logic**: 3-4 hours
- **Rich CLI**: 2-3 hours
- **Integration**: 1-2 hours
- **Tests**: 2-3 hours
- **Total**: 8-12 hours, ~1450 lines

**Grand Total**: 17-28 hours development time

---

## Pre-Implementation Research

Before starting Chunk 1, research:

1. **amplifier-core Tool protocol** (15 minutes)
   - Find Tool base class or protocol
   - Understand execute() signature
   - Understand event emission

2. **Existing tool examples** (15 minutes)
   - Read tool-bash or tool-filesystem
   - See how they implement protocol
   - Copy patterns

3. **ffmpeg screenshot capture** (10 minutes)
   - Verify command: `ffmpeg -ss HH:MM:SS -i video -frames:v 1 out.jpg`
   - Test locally

**Total research**: ~40 minutes before coding

---

## Next Steps

✅ **Code plan complete**

**Waiting for**:
- User approval of this plan
- Any questions or adjustments

**After approval**:
1. Do pre-implementation research (40 minutes)
2. Run `/ddd:4-code` to start implementation
3. Build tool-whisper first
4. Then tool-youtube-dl
5. Then app-transcribe

---

## Notes

**This plan assumes**:
- amplifier-core Tool protocol is straightforward
- Existing code quality is good (can port directly)
- ffmpeg handles video/screenshots
- Rich library is well-documented

**If assumptions wrong**:
- Adjust plan and get user approval
- Document deviations
- Update templates if needed
