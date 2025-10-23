# DDD Plan: Transcribe Migration to Amplifier-Dev

## Problem Statement

**Current State**: The transcribe tool exists in `scenarios/transcribe/` with valuable capabilities (Whisper transcription, YouTube download) but is locked in legacy structure and not reusable by other amplifier workflows.

**User Pain Points**:
- Developers can't add transcription to their amplifier agents
- Users must clone entire repo to use transcribe
- No web interface option
- Transcription logic not shared across scenarios

**What We're Solving**:
1. **Extract reusable capabilities** as amplifier-dev tools (Whisper, YouTube-DL)
2. **Create standalone app** demonstrating tool composition and modern UX
3. **Establish migration pattern** for other scenarios to follow

**User Value**:
- **Tool Users**: Add transcription to any amplifier workflow via profiles
- **App Users**: Run `uvx amplifier-app-transcribe URL` (no clone, no setup)
- **Developers**: Reference implementation for tool extraction pattern
- **Ecosystem**: Grows amplifier-dev's tool library

---

## Proposed Solution

**Three-Repository Architecture** (Tools-First Sequential Approach):

### Repository 1: `microsoft/amplifier-dev/amplifier-module-tool-whisper`
- **What**: OpenAI Whisper API integration as amplifier tool
- **Exports**: `WhisperTool` - Speech-to-text transcription
- **Reusable For**: Meeting transcription, lecture notes, podcast processing, voice memos
- **Distribution**: Git source, entry point discovery
- **Status**: ✅ Repository created

### Repository 2: `microsoft/amplifier-dev/amplifier-module-tool-youtube-dl`
- **What**: YouTube audio/video download wrapper (yt-dlp)
- **Exports**: `YouTubeDLTool` - Download and metadata extraction
- **Reusable For**: Video analysis, content archival, research workflows
- **Distribution**: Git source, entry point discovery
- **Status**: ✅ Repository created

### Repository 3: `microsoft/amplifier-dev/amplifier-app-transcribe`
- **What**: Complete transcription application
- **Composes**: tool-whisper + tool-youtube-dl + app-specific logic
- **Interfaces**: CLI (Rich) + Web (FastAPI, phase 2)
- **Distribution**: uvx (no clone needed)
- **Status**: ✅ Repository created

**Integration Flow**:
```
User → uvx amplifier-app-transcribe URL
  ↓
App downloads automatically (first run)
  ↓
App uses tool-whisper + tool-youtube-dl (via git sources)
  ↓
Pipeline: Download → Transcribe → Format → Insights
  ↓
Beautiful Rich CLI output + organized files
```

---

## Alternatives Considered

### Alternative 1: App-First Monolith
**Approach**: Build app with vendored code, extract tools later
**Rejected Because**:
- Tools not available to others initially
- Risk of tight coupling (harder extraction)
- May never extract (technical debt accumulates)
- Violates "generic capabilities first" principle

### Alternative 2: Parallel Development
**Approach**: Build tools and app simultaneously
**Rejected Because**:
- Coordination overhead for solo developer
- Risk of API misalignment
- More complex integration
- No validation until integration point

### Alternative 3: Single Combined Tool
**Approach**: One `tool-transcribe` with everything
**Rejected Because**:
- Whisper useful without YouTube
- YouTube useful without Whisper
- Violates single responsibility
- Harder to test and maintain

**Why Tools-First Sequential is Best**:
- Clean API boundaries (app validates tools)
- Immediate reusability
- Sequential validation catches issues early
- Natural for solo development
- User already approved this approach

---

## Architecture & Design

### Key Interfaces (The "Studs")

#### WhisperTool API
```python
# Input
{
    "audio_path": str,           # Path to audio file
    "language": str?,            # Optional language code (e.g., "en")
    "prompt": str?,              # Optional prompt to guide transcription
    "output_dir": str?           # Where to save results
}

# Output
{
    "text": str,                 # Full transcript text
    "segments": [                # Timestamped segments
        {
            "id": int,
            "start": float,
            "end": float,
            "text": str
        }
    ],
    "duration": float,           # Audio duration in seconds
    "language": str,             # Detected/specified language
    "cost": float                # API cost in USD
}
```

#### YouTubeDLTool API
```python
# Input
{
    "url": str,                  # YouTube URL
    "audio_only": bool?,         # Default: true
    "output_dir": str?,          # Where to save audio
    "output_filename": str?,     # Custom filename
    "use_cache": bool?           # Default: true
}

# Output
{
    "path": str,                 # Path to downloaded file
    "metadata": {
        "title": str,
        "id": str,
        "duration": float,
        "description": str,
        "uploader": str
    }
}
```

### Module Boundaries

**Tool-Whisper Responsibilities** (Brick #1):
- ✅ Whisper API calls with retry logic
- ✅ Audio file validation (size, format)
- ✅ Cost estimation
- ✅ Error handling (API failures, auth issues)
- ✅ Event emission (`tool:pre/post/error`)
- ❌ NOT: Formatting, insights, storage organization

**Tool-YouTube-DL Responsibilities** (Brick #2):
- ✅ YouTube video metadata extraction
- ✅ Audio download via yt-dlp
- ✅ Caching logic
- ✅ Local file handling (duration, format detection)
- ✅ Event emission
- ❌ NOT: Transcription, processing, user workflows

**App-Transcribe Responsibilities** (Brick #3):
- ✅ Pipeline orchestration (download → transcribe → format)
- ✅ Transcript formatting (paragraphs with timestamps)
- ✅ AI insights generation (summaries + quotes)
- ✅ State management (checkpoint/resume)
- ✅ Output organization (folders, indexes)
- ✅ CLI (Rich) + Web (FastAPI) interfaces
- ❌ NOT: Core transcription/download logic (uses tools)

### Data Models

**Transcript** (from tool-whisper):
```python
@dataclass
class TranscriptSegment:
    id: int
    start: float
    end: float
    text: str

@dataclass
class Transcript:
    text: str
    language: str | None
    duration: float | None
    segments: list[TranscriptSegment]
```

**VideoInfo** (from tool-youtube-dl):
```python
@dataclass
class VideoInfo:
    source: str          # URL or filepath
    type: str            # "url" or "file"
    title: str
    id: str
    duration: float
    description: str = ""
    uploader: str = ""
```

**PipelineState** (app-only):
```python
@dataclass
class VideoProcessingResult:
    video_id: str
    source: str
    status: str          # "success", "failed", "skipped"
    output_dir: str | None
    error: str | None
    duration_seconds: float
    cost_estimate: float

@dataclass
class PipelineState:
    stage: str
    current_video: str | None
    processed_videos: list[VideoProcessingResult]
    # ... checkpoint data for resume
```

---

## Files to Change

### Phase 1: Extract Tools (No docs to change - new repos)

**New Module**: `microsoft/amplifier-dev/amplifier-module-tool-whisper` (repo exists)
- [ ] Create repo structure
- [ ] Port `scenarios/transcribe/whisper_transcriber/core.py` → `src/amplifier_module_tool_whisper/core.py`
- [ ] Create `src/amplifier_module_tool_whisper/whisper_tool.py` (Tool protocol implementation)
- [ ] Create `pyproject.toml` with git sources
- [ ] Create `README.md` documenting tool
- [ ] Create `examples/whisper.md` profile example
- [ ] Create `tests/test_whisper_tool.py`

**New Module**: `microsoft/amplifier-dev/amplifier-module-tool-youtube-dl` (repo exists)
- [ ] Create repo structure
- [ ] Port `scenarios/transcribe/video_loader/core.py` → `src/amplifier_module_tool_youtube_dl/core.py`
- [ ] Create `src/amplifier_module_tool_youtube_dl/youtube_tool.py` (Tool protocol implementation)
- [ ] Create `pyproject.toml` with git sources
- [ ] Create `README.md` documenting tool
- [ ] Create `examples/youtube-dl.md` profile example
- [ ] Create `tests/test_youtube_tool.py`

### Phase 2: Build App (New repo)

**New Module**: `microsoft/amplifier-dev/amplifier-app-transcribe` (repo exists)
- [ ] Create repo structure
- [ ] Create `src/amplifier_app_transcribe/cli.py` (Rich CLI)
- [ ] Port `scenarios/transcribe/main.py` → `src/amplifier_app_transcribe/pipeline.py` (adapted to use tools)
- [ ] Port `scenarios/transcribe/state.py` → `src/amplifier_app_transcribe/state.py`
- [ ] Port `scenarios/transcribe/storage/` → `src/amplifier_app_transcribe/storage.py`
- [ ] Port `scenarios/transcribe/transcript_formatter/` → `src/amplifier_app_transcribe/formatter.py`
- [ ] Port `scenarios/transcribe/insights_generator/` → `src/amplifier_app_transcribe/insights.py`
- [ ] Create `src/amplifier_app_transcribe/web.py` (FastAPI - phase 2)
- [ ] Create `pyproject.toml` with git sources to tools
- [ ] Create `README.md` (user-facing guide)
- [ ] Create `HOW_THIS_APP_WAS_MADE.md` (metacognitive recipe)
- [ ] Create `MIGRATION_NOTES.md` (creation story)
- [ ] Create `tests/test_pipeline.py`
- [ ] Create `tests/test_cli.py`

### Phase 3: Documentation Updates (This repo)

**Files in `amplifier.transcripts2`**:
- [ ] Update `scenarios/README.md` - Add note about transcribe migration
- [ ] Create `scenarios/transcribe/MIGRATION_NOTICE.md` - Point to new location
- [ ] Update `ai_working/SCENARIO_MIGRATION_GUIDE.md` - Add transcribe as case study
- [ ] Update `README.md` - Update transcribe references

---

## Philosophy Alignment

### Ruthless Simplicity

**Start Minimal**:
- ✅ Tools expose only essential operations (transcribe, download)
- ✅ No speculative features (batch processing via app, not tools)
- ✅ App CLI first (web interface in phase 2)
- ✅ State management in app only (tools are stateless)

**Avoid Future-Proofing**:
- ❌ NOT building: Multi-provider transcription (Whisper only for now)
- ❌ NOT building: Complex audio editing (just compression)
- ❌ NOT building: Cloud storage integration (local files only)
- ❌ NOT building: User accounts / auth (single-user app)

**Clear Over Clever**:
- ✅ Direct API calls (no elaborate abstractions)
- ✅ Simple dict-based tool inputs/outputs
- ✅ Explicit error messages
- ✅ Straightforward pipeline flow

### Modular Design

**Bricks (Self-Contained Modules)**:
1. **tool-whisper** - Can transcribe without knowing about YouTube
2. **tool-youtube-dl** - Can download without knowing about transcription
3. **app-transcribe** - Composes tools without modifying them

**Studs (Stable Interfaces)**:
- Tool protocol: `execute(input: dict) -> dict`
- Event protocol: `tool:pre/post/error` with standard payloads
- Git sources: Tools downloadable via standard mechanism
- Entry points: Tools discoverable via `project.entry-points`

**Regeneratable from Spec**:
- ✅ Tool APIs fully specified above
- ✅ Each module has clear responsibilities
- ✅ Could rebuild any module from this plan
- ✅ Contracts preserved even if implementation changes

**Human Architects, AI Builds**:
- ✅ This plan = human architecture
- ✅ AI will implement from specifications
- ✅ Human reviews behavior, not code
- ✅ Can regenerate modules as needed

### Lessons from MODULE_DEVELOPMENT_LESSONS.md

**Git Sources (Not Path Dependencies)**:
```toml
# ✅ In tool pyproject.toml
[tool.uv.sources]
amplifier-core = {
    git = "https://github.com/microsoft/amplifier-dev",
    subdirectory = "amplifier-core",
    branch = "main"
}
```

**Path Handling**:
```python
# ✅ Always expanduser()
output_dir = Path(config.get("output_dir", "~/transcripts")).expanduser()
```

**Capability Registry** (if tools need shared config):
```python
# In app, if needed:
coordinator.register_capability("transcription.config", shared_config)

# Tools can retrieve:
config = coordinator.get_capability("transcription.config")
```

---

## Test Strategy

### Unit Tests

**tool-whisper** (`tests/test_whisper_tool.py`):
- [ ] Test API input validation
- [ ] Test successful transcription (mocked OpenAI)
- [ ] Test cost estimation accuracy
- [ ] Test file size validation (25MB limit)
- [ ] Test retry logic on failures
- [ ] Test event emission

**tool-youtube-dl** (`tests/test_youtube_tool.py`):
- [ ] Test metadata extraction (mocked yt-dlp)
- [ ] Test audio download with caching
- [ ] Test local file handling
- [ ] Test duration detection (ffprobe)
- [ ] Test event emission

**app-transcribe** (`tests/test_pipeline.py`):
- [ ] Test pipeline orchestration
- [ ] Test state management (checkpoint/resume)
- [ ] Test transcript formatting
- [ ] Test insights generation
- [ ] Test error handling and recovery

### Integration Tests

**End-to-End Flow**:
- [ ] Download YouTube audio → Transcribe → Format → Insights
- [ ] Process local audio file → Transcribe → Format → Insights
- [ ] Batch processing with resume on interruption
- [ ] Error handling (invalid URL, API failures, etc.)

### User Testing (Manual)

**CLI Experience**:
```bash
# First run (auto-install)
uvx amplifier-app-transcribe "https://youtube.com/watch?v=..."

# Verify:
- Beautiful Rich progress output
- Clear status messages
- Results table at end
- Files organized correctly
- Resume works after Ctrl+C
```

**As Amplifier Tool**:
```yaml
# Create profile: ~/.amplifier/profiles/transcribe.md
tools:
  - module: tool-whisper
    source: git+https://github.com/robotdad/amplifier-module-tool-whisper@main
  - module: tool-youtube-dl
    source: git+https://github.com/robotdad/amplifier-module-tool-youtube-dl@main
```

```bash
# Test in amplifier session
amplifier run --profile transcribe
> "Transcribe https://youtube.com/watch?v=..."
# Verify tools work in amplifier context
```

---

## Implementation Approach

### Phase 1: Extract Tools (tool-whisper, tool-youtube-dl)

**Priority**: High (blocks app development)

**Steps**:
1. Repositories already created in `microsoft/amplifier-dev`
2. Port core logic from `scenarios/transcribe/`
3. Wrap in Tool protocol
4. Add event emission (`tool:pre/post/error`)
5. Configure git sources in pyproject.toml
6. Write READMEs and examples
7. Test tools independently

**Chunk Breakdown**:
- **Chunk 1.1**: tool-whisper repo setup + core porting (~1-2 hours)
- **Chunk 1.2**: tool-youtube-dl repo setup + core porting (~1-2 hours)
- **Chunk 1.3**: Tests for both tools (~1 hour)

**Dependencies**: None (can start immediately)

**Validation**: Tools work via `amplifier run --profile` with test profile

### Phase 2: Build CLI App

**Priority**: High (user-facing deliverable)

**Steps**:
1. Repository already created in `microsoft/amplifier-dev`
2. Port pipeline logic adapted to use tools
3. Port formatting, insights, storage
4. Build Rich CLI interface
5. Add state management for resume
6. Configure for uvx distribution
7. Test end-to-end

**Chunk Breakdown**:
- **Chunk 2.1**: Repo setup + pipeline porting (~2 hours)
- **Chunk 2.2**: Rich CLI implementation (~2 hours)
- **Chunk 2.3**: State management + resume (~1 hour)
- **Chunk 2.4**: Testing and polish (~1-2 hours)

**Dependencies**: Phase 1 complete (tools exist)

**Validation**: `uvx amplifier-app-transcribe URL` works end-to-end

### Phase 3: Web Interface (Future)

**Priority**: Medium (nice-to-have, not MVP)

**Steps**:
1. Add FastAPI to app dependencies
2. Create `web.py` with API endpoints
3. Reuse pipeline logic from CLI
4. Add progress via SSE or websockets
5. Simple HTML + JavaScript frontend
6. Add `transcribe-web` entry point

**Chunk Breakdown**:
- **Chunk 3.1**: FastAPI backend (~2 hours)
- **Chunk 3.2**: Frontend UI (~3-4 hours)
- **Chunk 3.3**: Progress/status updates (~1 hour)

**Dependencies**: Phase 2 complete (CLI app working)

**Validation**: `uvx --with amplifier-app-transcribe transcribe-web` launches web UI

### Phase 4: Documentation Updates

**Priority**: Low (cleanup)

**Steps**:
1. Update scenario migration guide with transcribe case study
2. Add migration notice to `scenarios/transcribe/`
3. Update main README references

**Dependencies**: Phases 1-2 complete

---

## Success Criteria

### Tools (tool-whisper, tool-youtube-dl)

- ✅ Can be used independently in amplifier sessions
- ✅ Available via profile with `source:` field
- ✅ Auto-download works (git sources)
- ✅ Emit proper events (`tool:pre/post/error`)
- ✅ Tests pass
- ✅ READMEs are clear and complete

### App (amplifier-app-transcribe)

- ✅ Installable via uvx (no clone)
- ✅ Beautiful Rich CLI output
- ✅ Processes YouTube videos successfully
- ✅ Processes local audio files successfully
- ✅ Generates formatted transcripts
- ✅ Generates AI insights (summaries + quotes)
- ✅ Resume works after interruption
- ✅ Files organized logically
- ✅ Error messages are clear and helpful

### Pattern Establishment

- ✅ Other scenarios can follow this migration pattern
- ✅ Tool extraction guidelines documented
- ✅ App composition example exists
- ✅ uvx distribution pattern validated

### User Experience

**Tool User**:
```yaml
# Drop profile in ~/.amplifier/profiles/transcribe.md
# Run: amplifier run --profile transcribe
# Say: "Transcribe this video: <URL>"
# Tools download automatically, transcription works
```

**App User**:
```bash
# Run: uvx amplifier-app-transcribe "https://youtube.com/watch?v=..."
# Beautiful progress output
# Organized results in ~/transcripts/
# Can resume if interrupted
```

---

## Risks & Mitigations

### Risk 1: Tool APIs Don't Meet App Needs

**Mitigation**: Tools-first approach validates APIs before app complexity

**Backup Plan**: Iterate on tool APIs early (easy since in amplifier-dev monorepo)

### Risk 2: Git Sources Don't Work for Private Repos

**Mitigation**: Test git source download early with amplifier-dev subdirectories

**Backup Plan**: Make repos public if distribution issues

### Risk 3: Rich CLI Complexity

**Mitigation**: Rich is well-documented, examples exist

**Backup Plan**: Start with simple CLI, enhance iteratively

### Risk 4: uvx Distribution Issues

**Mitigation**: Test uvx install early in development

**Backup Plan**: Provide `pip install` as fallback

### Risk 5: State Management in Distributed Setup

**Mitigation**: State management stays in app layer, tools are stateless

**Backup Plan**: Document checkpoint files clearly for debugging

---

## Next Steps

### Immediate (Phase 1)

✅ **Plan approved** (this document)
➡️ **Start tool extraction**:
1. Run `/ddd:2-docs` (may be minimal for new repos)
2. Run `/ddd:3-code-plan` for tool-whisper
3. Run `/ddd:4-code` to implement tool-whisper
4. Repeat for tool-youtube-dl
5. Test both tools independently

### After Phase 1 (Phase 2)

➡️ **Build the app**:
1. Create app repo structure
2. Implement CLI with Rich
3. Test end-to-end
4. Document user workflows

### After Phase 2 (Phase 3 - Optional)

➡️ **Add web interface**:
1. FastAPI backend
2. Simple frontend
3. Progress tracking via SSE

### Cleanup (Phase 4)

➡️ **Update documentation**:
1. Migration guide case study
2. Scenario notices
3. README updates

---

## Appendix: Key Decisions

### Decision 1: Two Tools vs One Combined Tool

**Chose**: Two separate tools (Whisper, YouTube-DL)

**Reason**:
- Whisper useful without YouTube (local files, other sources)
- YouTube useful without Whisper (video analysis, archival)
- Single responsibility principle
- Easier to test and maintain

### Decision 2: Tools-First vs App-First

**Chose**: Tools-first sequential

**Reason**:
- Clean API boundaries
- Immediate reusability
- Lower risk
- Philosophy alignment ("generic capabilities first")
- User approved this approach

### Decision 3: Rich vs Simple CLI

**Chose**: Rich for formatting

**Reason**:
- User explicitly requested Rich
- Beautiful progress output
- Better user experience
- Standard for modern Python CLIs
- Not complex to integrate

### Decision 4: CLI-First vs Web-First

**Chose**: CLI first, web later

**Reason**:
- CLI is MVP
- Web is enhancement
- Can reuse pipeline logic
- Iterate based on CLI feedback

### Decision 5: Repository Location

**Chose**: `microsoft/amplifier-dev` subdirectories for all modules

**Reason**:
- Official amplifier-dev location
- Better discoverability
- Part of core amplifier ecosystem
- Repositories already created

---

## Document Status

- **Version**: 1.0
- **Date**: 2025-10-22
- **Status**: Ready for approval
- **Next Phase**: `/ddd:2-docs` after user approval
