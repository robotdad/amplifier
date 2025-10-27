# DDD Plan: Blog Creator Web Interface (Phase 2 MVP)

**Status:** Planning Complete - Awaiting User Approval
**Created:** 2025-10-26
**Feature:** Web UI for blog creator with rich markdown editor and real-time progress

---

## Problem Statement

The blog creator CLI is functional and tested, but:

1. **Limited visual engagement** - Console output can't show rich previews or sophisticated progress
2. **Clunky feedback mechanism** - Editing files for feedback is inefficient compared to in-browser editing
3. **Hard to demo** - CLI doesn't impress tech-savvy executives
4. **No live preview** - Can't see rendered markdown while editing
5. **Barrier for non-CLI users** - Some users prefer web interfaces

**User Value:**

- **First-time users:** Visual guidance through workflow, clear progress visibility
- **Power users:** Rich markdown editor with keyboard shortcuts, efficient iteration
- **Executives:** Polished, professional interface demonstrating technical excellence
- **All users:** Better editing experience with live preview and syntax highlighting

---

## Proposed Solution

**Add web layer parallel to existing CLI** using FastAPI + HTMX + Jinja2 (Python-only stack for uvx distribution).

### High-Level Architecture

```
amplifier-app-blog-creator/
├── core/              # UNCHANGED - Pure business logic
│   ├── stages/        # extract_style, generate_draft, review_draft, revise_draft
│   ├── workflow.py    # BlogCreatorWorkflow orchestrator
│   └── models.py      # StyleProfile, ReviewResult, RevisionFeedback
│
├── cli/               # UNCHANGED - CLI adapter
│   ├── main.py        # CLI entry point
│   ├── ui.py          # CLI display
│   └── input_handler.py
│
└── web/               # NEW - Web adapter (pure UI layer)
    ├── app.py         # FastAPI application
    ├── routes/        # HTTP endpoints
    │   ├── sessions.py    # Session CRUD + workflow stages
    │   ├── progress.py    # SSE progress streaming
    │   └── content.py     # File preview, markdown rendering
    ├── static/
    │   ├── css/
    │   │   ├── tokens.css      # Design tokens (colors, shadows, motion)
    │   │   ├── layout.css      # Grid system, page layouts
    │   │   └── components.css  # Component styles
    │   └── js/
    │       ├── htmx.min.js     # HTMX library (vendored)
    │       ├── codemirror.bundle.js  # CodeMirror editor
    │       └── app.js          # Custom interactions
    └── templates/
        ├── base.html       # Base layout
        ├── setup.html      # Stage 1: Input collection
        ├── progress.html   # Stage 2: AI processing
        ├── review.html     # Stage 3: Edit & review
        └── complete.html   # Stage 4: Success state
```

### Key Design Decisions

**1. Primary Usage via uvx (No Installation)**
```bash
uvx --from git+https://github.com/robotdad/amplifier-app-blog-creator blog-creator --mode web
```

**2. Environment Variable Configuration (Stage 0)**
- App checks for ANTHROPIC_API_KEY on startup
- If missing, shows friendly configuration screen before workflow
- In-session configuration (stored in memory only, never saved to disk)
- Validates API key works before proceeding
- Supports .env file for local development
- Security-focused (password field, visibility toggle)

**3. Mode Selection via --mode Flag**
```bash
blog-creator --mode web    # Opens browser, runs web UI (recommended)
blog-creator --mode cli    # Traditional CLI
```

**4. Reuse Existing Core Logic**
- No changes to `core/` module (tested and working)
- Web layer is pure adapter (like CLI is)
- Same `BlogCreatorWorkflow` used by both interfaces

**5. Browser Auto-Open**
- Python `webbrowser` module (cross-platform)
- Opens on server startup
- Fallback: print URL if open fails
- `--no-browser` flag to disable

**6. Single-Page App with Stage Progression**
- HTMX handles dynamic updates
- Smooth transitions between stages
- Persistent header with stage indicator

**7. Rich Markdown Editor**
- CodeMirror 6 for editing
- Syntax highlighting, line numbers
- Preview toggle (source ↔ rendered)
- Auto-save via HTMX

**8. Real-Time Progress via SSE**
- Server-Sent Events stream progress
- Updates progress bars, subtask lists
- Time estimates and actual durations
- Smooth animations, no page reloads

**9. Slide-Out Review Drawer**
- Full-width editor by default
- Review panel slides in from right
- Future-proofs for chat integration (Phase 3)
- Keyboard shortcut: Cmd/Ctrl + R

**10. File Path Input Flexibility**
- Text input (type or paste paths)
- Browse button (native file picker)
- Drag-and-drop (modern UX)
- Real-time validation with visual feedback

**11. Content Preview**
- Collapsible preview of idea file
- List of writing samples with metadata
- View-only for MVP (editing deferred)
- Transparency in what AI is analyzing

---

## Alternatives Considered

### Alternative 1: React SPA with Python Backend

**Approach:** React frontend + FastAPI backend API

**Pros:**
- Rich client-side interactions
- Modern development patterns
- Component libraries available

**Cons:**
- ❌ Requires Node.js build step (violates Python-only constraint)
- ❌ More complex deployment (two stacks)
- ❌ Harder for uvx distribution
- ❌ Over-engineering for MVP scope

**Rejected:** Violates "Python-only for uvx distribution" requirement

---

### Alternative 2: Streamlit

**Approach:** Use Streamlit framework for web UI

**Pros:**
- Python-only (✅)
- Quick to build
- Good for data apps

**Cons:**
- ❌ Opinionated framework (limited customization)
- ❌ Hard to achieve "sophisticated warmth" aesthetic
- ❌ Difficult to integrate CodeMirror
- ❌ SSE progress patterns awkward
- ❌ Won't impress executives (looks like prototype)

**Rejected:** Can't achieve design quality requirements

---

### Alternative 3: FastAPI + Vanilla HTML/CSS (No HTMX)

**Approach:** Traditional multi-page app with form submissions

**Pros:**
- Simple, no JavaScript framework
- Easy to understand

**Cons:**
- ❌ Page reloads break flow
- ❌ No smooth transitions
- ❌ Progress updates require polling
- ❌ Less modern feel
- ❌ More server-side logic for UI state

**Rejected:** User experience not smooth enough, won't impress executives

---

### Alternative 4: FastAPI + HTMX (CHOSEN) ✅

**Approach:** Server-rendered templates with HTMX for dynamic updates

**Pros:**
- ✅ Python-only (FastAPI, Jinja2, Uvicorn)
- ✅ Progressive enhancement (works without JS)
- ✅ Smooth UX without page reloads
- ✅ Simple mental model (server renders HTML)
- ✅ SSE for real-time progress
- ✅ Can achieve polished aesthetic
- ✅ Easy uvx distribution

**Cons:**
- Learning curve for HTMX (minimal)
- Custom CSS needed (no framework)

**CHOSEN:** Best balance of simplicity, power, and Python-only constraint

---

## Architecture & Design

### Key Interfaces ("Studs")

**1. Mode Dispatcher (main.py)**
```python
def main():
    """Entry point dispatches to CLI or Web based on --mode flag."""
    # Parse mode from sys.argv before click
    if "--mode" in sys.argv and "web" in sys.argv:
        return web_main()
    else:
        return cli_main()
```

**2. Web Application (web/app.py)**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")
```

**3. Session API (web/routes/sessions.py)**
```python
POST   /sessions                     # Create new session
GET    /sessions/{id}                # Get session state
POST   /sessions/{id}/validate-path  # Validate file/dir path
GET    /sessions/{id}/preview-file   # Preview file content
POST   /sessions/{id}/start-workflow # Begin Stage 1 & 2
GET    /sessions/{id}/review         # Get review data
POST   /sessions/{id}/approve        # Finalize draft
POST   /sessions/{id}/regenerate     # Re-run with edits
PUT    /sessions/{id}/draft          # Update draft content (auto-save)
```

**4. Progress Stream (web/routes/progress.py)**
```python
GET    /sessions/{id}/progress       # SSE stream

Event format:
{
    "stage": "style_extraction",
    "progress": 60,
    "message": "Analyzing writing samples...",
    "subtasks": [
        {"name": "post-1.md", "status": "completed"},
        {"name": "post-2.md", "status": "active"},
        {"name": "post-3.md", "status": "pending"}
    ],
    "time_estimate": "3 seconds remaining"
}
```

**5. Workflow Wrapper (Connects FastAPI to BlogCreatorWorkflow)**
```python
class WebWorkflowAdapter:
    """Adapts BlogCreatorWorkflow for web context with SSE progress."""

    def __init__(self, session_id: str):
        self.session = SessionManager(Path(f".data/blog_creator/{session_id}"))
        self.progress_queue = asyncio.Queue()
        self.workflow = BlogCreatorWorkflow(
            self.session,
            progress_callback=self._progress_callback
        )

    def _progress_callback(self, message: str):
        """Capture progress for SSE streaming."""
        self.progress_queue.put_nowait({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    async def stream_progress(self):
        """SSE generator for progress updates."""
        while True:
            try:
                update = await asyncio.wait_for(
                    self.progress_queue.get(),
                    timeout=30.0
                )
                yield f"data: {json.dumps(update)}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
```

### Module Boundaries

**web/** (NEW - Pure UI adapter)
- Depends on: `core/`, `session.py`
- Exports: FastAPI app, routes, templates
- NO business logic
- NO changes to core

**core/** (UNCHANGED)
- Already perfect for web layer
- Async functions with progress callbacks
- Returns typed models
- No UI dependencies

**cli/** (UNCHANGED)
- Continues to work independently
- Unaffected by web layer

### Data Models

**Using existing models from core/models.py:**
- `StyleProfile` - Writing style characteristics
- `ReviewResult` - Combined review feedback
- `RevisionFeedback` - User feedback structure

**New models for web (web/models.py):**
```python
class SessionCreateRequest(BaseModel):
    """Request to create new session."""
    idea_path: str
    writings_dir: str
    additional_instructions: str | None = None

class PathValidationResponse(BaseModel):
    """Response from path validation."""
    valid: bool
    type: Literal["file", "directory"] | None = None
    word_count: int | None = None
    file_count: int | None = None
    error: str | None = None

class FilePreviewResponse(BaseModel):
    """File content preview."""
    content: str
    word_count: int
    char_count: int
    truncated: bool
```

---

## Files to Change

### Non-Code Files (Phase 2: Documentation)

**In amplifier-app-blog-creator/:**

- [ ] `README.md` - Add web mode documentation
  - New "Web Interface" section before "Quick Start"
  - Add `--mode web` examples
  - Document browser auto-open
  - Add screenshots/wireframes (optional)
  - Update architecture section with web/ module

- [ ] `HOW_I_BUILT_THIS.md` - Document Phase 2 web layer
  - Add "Adding Web Interface" section
  - Explain adapter pattern (web parallel to CLI)
  - Document technology choices (FastAPI + HTMX)
  - Explain why no changes to core/

- [ ] `MIGRATION_NOTES.md` - Add Phase 2 notes
  - Document web layer addition
  - Note: No breaking changes to CLI
  - Note: Uses same core/ logic as CLI

**New documentation files:**

- [ ] `src/amplifier_app_blog_creator/web/README.md`
  - Web module overview
  - Architecture explanation
  - Template structure
  - Route documentation

- [ ] `.design/AESTHETIC-GUIDE.md` - Already created (review and finalize)

**In ai_working/ (temporary):**

- [ ] `ai_working/blog_web_interface/DESIGN_VISION.md` - Already created
- [ ] `ai_working/blog_web_interface/DESIGN_REFINEMENTS.md` - Already created
- [ ] `ai_working/blog_web_interface/COMPONENT_SPECS.md` - Already created

---

### Code Files (Phase 4: Implementation)

**NEW files to create:**

**Configuration:**
- [ ] `.env.example` - Example environment variables file

**Entry point:**
- [ ] `src/amplifier_app_blog_creator/web/__init__.py` - Web module exports
- [ ] `src/amplifier_app_blog_creator/web/app.py` - FastAPI application
- [ ] `src/amplifier_app_blog_creator/web/main.py` - Web mode entry point

**Routes:**
- [ ] `src/amplifier_app_blog_creator/web/routes/__init__.py`
- [ ] `src/amplifier_app_blog_creator/web/routes/configuration.py` - Env var config + validation
- [ ] `src/amplifier_app_blog_creator/web/routes/sessions.py` - Session management + workflow
- [ ] `src/amplifier_app_blog_creator/web/routes/progress.py` - SSE progress stream
- [ ] `src/amplifier_app_blog_creator/web/routes/content.py` - File preview, markdown rendering

**Models:**
- [ ] `src/amplifier_app_blog_creator/web/models.py` - Web-specific request/response models

**Adapter:**
- [ ] `src/amplifier_app_blog_creator/web/workflow_adapter.py` - Wraps BlogCreatorWorkflow for web

**Templates:**
- [ ] `src/amplifier_app_blog_creator/web/templates/base.html` - Base layout
- [ ] `src/amplifier_app_blog_creator/web/templates/components/header.html`
- [ ] `src/amplifier_app_blog_creator/web/templates/components/footer.html`
- [ ] `src/amplifier_app_blog_creator/web/templates/components/stage-indicator.html`
- [ ] `src/amplifier_app_blog_creator/web/templates/configuration.html` - Stage 0: Env var config
- [ ] `src/amplifier_app_blog_creator/web/templates/setup.html` - Stage 1: Input collection
- [ ] `src/amplifier_app_blog_creator/web/templates/progress.html` - Stage 2: AI processing
- [ ] `src/amplifier_app_blog_creator/web/templates/review.html` - Stage 3: Edit & review
- [ ] `src/amplifier_app_blog_creator/web/templates/complete.html` - Stage 4: Success

**Static assets:**
- [ ] `src/amplifier_app_blog_creator/web/static/css/tokens.css` - Design tokens
- [ ] `src/amplifier_app_blog_creator/web/static/css/layout.css` - Grid, page layouts
- [ ] `src/amplifier_app_blog_creator/web/static/css/components.css` - Component styles
- [ ] `src/amplifier_app_blog_creator/web/static/js/htmx.min.js` - HTMX library (vendored)
- [ ] `src/amplifier_app_blog_creator/web/static/js/codemirror.bundle.js` - CodeMirror (vendored)
- [ ] `src/amplifier_app_blog_creator/web/static/js/app.js` - Custom JavaScript

**MODIFIED files:**

- [ ] `src/amplifier_app_blog_creator/main.py` - Add mode dispatcher
  - Parse `--mode` flag
  - Dispatch to cli_main() or web_main()

- [ ] `pyproject.toml` - Add web dependencies
  - fastapi>=0.115.0
  - uvicorn[standard]>=0.30.0
  - jinja2>=3.1.0
  - python-markdown>=3.6.0
  - python-dotenv>=1.0.0 (already present - for .env support)
  - bleach>=6.0.0 (XSS protection)

**UNCHANGED files (existing and working):**

- ✅ All files in `core/` - Perfect as-is, no changes needed
- ✅ All files in `cli/` - Unaffected by web layer
- ✅ `session.py` - Works for both CLI and web
- ✅ `reviewers/` - Used by core/, no changes
- ✅ `utils/` - Shared utilities, no changes
- ✅ `vendored_toolkit/` - Shared, no changes

---

## Philosophy Alignment

### Ruthless Simplicity ✅

**Start minimal:**
- Web layer is thin adapter (like CLI)
- Reuses all core/ logic (no duplication)
- MVP scope: happy path only (Setup → Progress → Review → Complete)
- No user accounts, no databases, no complex state
- File-based sessions (already working)

**Avoid future-proofing:**
- Not building: Multi-user support, auth, cloud storage
- Not building: Chat feedback (deferred to Phase 3)
- Not building: Mobile optimization (desktop/laptop focus)
- Not building: Advanced editor features (just core editing)

**Clear over clever:**
- HTMX is simpler than React (server-rendered HTML)
- SSE simpler than WebSockets (one-way communication sufficient)
- Jinja2 templates (straightforward server-side rendering)
- No complex state management (server owns state)

**Question everything:**
- Do we need a frontend framework? NO (HTMX sufficient)
- Do we need a CSS framework? NO (custom CSS, full control)
- Do we need a database? NO (file-based sessions work)
- Do we need websockets? NO (SSE sufficient for progress)

### Modular Design ✅

**Bricks (self-contained modules):**

1. **core/** - Business logic brick
   - Interface: Async stage functions
   - Already complete, tested, working
   - Regeneratable from stage signatures

2. **cli/** - CLI adapter brick
   - Interface: Click commands
   - Consumes core/ via BlogCreatorWorkflow
   - Independent of web/

3. **web/** - Web adapter brick (NEW)
   - Interface: FastAPI routes
   - Consumes core/ via BlogCreatorWorkflow
   - Independent of CLI/
   - Templates, static assets, routes
   - Regeneratable from route specs + component specs

**Studs (stable interfaces - UNCHANGED):**

1. `BlogCreatorWorkflow` methods
   - `run_style_extraction(writings_dir) → StyleProfile`
   - `run_draft_generation(brain_dump, instructions) → str`
   - `run_review() → ReviewResult`
   - `run_revision(feedback) → str`

2. Session state model (SessionState dataclass)
   - Already defined and working
   - Both CLI and web use same structure

3. Progress callback signature
   - `Callable[[str], None]`
   - Web captures for SSE, CLI prints to console

**Regeneratable:**
- Could rebuild web/ from route specs + component specs
- Could rebuild templates from wireframes
- Core/ interface remains stable (studs don't change)

### Architectural Integrity ✅

**Preserve patterns:**
- Async/await throughout (core/ is async, web will be async)
- File-based session state (already works)
- Progress callbacks (already implemented)
- Stage-based workflow (already refactored)

**Simplify implementation:**
- Web layer has NO business logic (pure adapter)
- Templates are simple Jinja2 (no complex templating)
- Routes delegate to BlogCreatorWorkflow
- SSE is basic asyncio.Queue pattern

**End-to-end thinking:**
- Complete user journey: land on page → create blog → download
- All stages working end-to-end before polish
- Vertical slice: Setup → Progress → Review → Complete

---

## Test Strategy

### Manual Testing (Primary Validation)

**Test 1: Basic workflow**
```bash
cd amplifier-dev/amplifier-app-blog-creator
uvx blog-creator --mode web

# Should:
# ✅ Server starts
# ✅ Browser opens to http://localhost:8000
# ✅ Setup page loads with warm aesthetic
# ✅ Can enter paths (text + browse)
# ✅ Can start workflow
# ✅ See real-time progress
# ✅ Rich editor loads with draft
# ✅ Can approve and download
```

**Test 2: Cross-platform browser open**
```bash
# macOS
uvx blog-creator --mode web
# ✅ Opens in default browser (Safari/Chrome/Firefox)

# Linux (if available)
uvx blog-creator --mode web
# ✅ Opens via xdg-open

# Windows/WSL (if available)
uvx blog-creator --mode web
# ✅ Opens in Windows default browser
```

**Test 3: File path validation**
- Type valid path → ✅ Shows validation
- Type invalid path → ⚠ Shows error
- Use browse button → ✅ Path populated
- Drag file → ✅ Path populated

**Test 4: Real-time progress**
- Start workflow → ✅ See progress bars update
- Stage 1 completes → ✅ Card collapses with checkmark
- Stage 2 active → ✅ Shimmer effect visible
- Time estimates → ✅ Count down accurately

**Test 5: Rich editor**
- Draft loads → ✅ Syntax highlighting works
- Edit content → ✅ Changes save automatically
- Toggle preview → ✅ Smooth transition
- Review drawer → ✅ Slides in smoothly

**Test 6: Success celebration**
- Approve draft → ✅ Checkmark animates in
- Stats count up → ✅ Smooth animation
- Download works → ✅ File downloads correctly

### Integration Tests (Minimal)

**Test workflow adapter:**
```python
# tests/web/test_workflow_adapter.py
@pytest.mark.asyncio
async def test_adapter_progress_streaming():
    """Test progress callback captures to queue."""
    adapter = WebWorkflowAdapter("test_session")

    # Simulate progress
    adapter._progress_callback("Test message")

    # Should be in queue
    update = await adapter.progress_queue.get()
    assert update["message"] == "Test message"
```

**Test route responses:**
```python
# tests/web/test_routes.py
def test_create_session(client):
    """Test session creation endpoint."""
    response = client.post("/sessions", json={
        "idea_path": "/path/to/idea.md",
        "writings_dir": "/path/to/posts/"
    })
    assert response.status_code == 200
    assert "session_id" in response.json()
```

### Accessibility Testing

**Keyboard navigation:**
- Tab through all interactive elements
- Focus indicators visible
- Drawer opens with Cmd/Ctrl + R

**Screen reader:**
- Semantic HTML (`<header>`, `<main>`, `<nav>`)
- ARIA labels on controls
- Progress announcements (aria-live)

**Reduced motion:**
- All animations respect `prefers-reduced-motion`
- Fallback to instant transitions

**Color contrast:**
- All text ≥4.5:1 (validated in design tokens)
- UI elements ≥3:1

---

## Implementation Approach

### Phase 2 (Docs) - Update Documentation

**Goal:** Document web layer as if it already exists

**README.md updates:**
- Add "Web Interface" section
- Document `--mode web` flag
- Add web-specific examples
- Update architecture diagram

**HOW_I_BUILT_THIS.md updates:**
- Add "Phase 2: Web Layer" section
- Document adapter pattern
- Explain technology choices

**MIGRATION_NOTES.md updates:**
- Add Phase 2 entry
- Note: No breaking changes to CLI
- Note: Reuses core/ logic

**New web/README.md:**
- Web module overview
- Route documentation
- Template structure
- Static asset organization

---

### Phase 4 (Code) - Implementation Order

**Chunk 1: Project Setup (1-2 hours)**

Tasks:
- Update pyproject.toml with web dependencies
- Run `uv sync` to install dependencies
- Create web/ directory structure
- Vendor HTMX and CodeMirror libraries
- Create empty template/static files

Success: Directory structure exists, dependencies installed

---

**Chunk 2: FastAPI Foundation (2-3 hours)**

Tasks:
- Create web/app.py with FastAPI application
- Add static file serving
- Add Jinja2 template configuration
- Create base.html template (header, footer, layout)
- Create tokens.css with design tokens
- Create basic layout.css

Success: Server starts, base template renders, design tokens loaded

---

**Chunk 3: Mode Dispatcher + Browser Open (1 hour)**

Tasks:
- Update main.py with mode detection
- Create web/main.py entry point
- Add webbrowser.open() on startup
- Add --no-browser flag
- Test cross-platform browser open

Success: `uvx blog-creator --mode web` opens browser automatically

---

**Chunk 4: Configuration Stage (2-3 hours)**

Tasks:
- Create configuration.html template
- Implement ConfigurationStage component (HTML + CSS)
- Create /configure POST endpoint with API key validation
- Add environment variable checking on app startup
- Implement in-session credential storage (memory only)
- Support .env file loading for local development
- Wire up redirect to Setup after successful config

Success: Can configure API key, validates it works, proceeds to Setup

---

**Chunk 5: Setup Stage (3-4 hours)**

Tasks:
- Create setup.html template
- Implement PathInput component (HTML + CSS)
- Create /sessions POST endpoint
- Implement path validation endpoint
- Add file preview functionality
- Create FilePreview component
- Wire up "Start Creation" button

Success: Can enter paths, see validation, preview files, start workflow

---

**Chunk 6: Progress Stage with SSE (4-5 hours)**

Tasks:
- Create progress.html template
- Implement ProgressStage component (HTML + CSS)
- Create WebWorkflowAdapter class
- Implement /progress SSE endpoint
- Create /start-workflow endpoint
- Wire up SSE client-side
- Add progress bar animations

Success: Can start workflow, see real-time progress through all stages

---

**Chunk 7: Rich Markdown Editor (4-5 hours)**

Tasks:
- Create review.html template
- Integrate CodeMirror 6 bundle
- Implement editor initialization
- Add preview toggle functionality
- Implement auto-save endpoint (PUT /draft)
- Create markdown rendering endpoint
- Style editor toolbar

Success: Editor loads draft, syntax highlighting works, preview toggles smoothly

---

**Chunk 8: Review Drawer (3-4 hours)**

Tasks:
- Create ReviewDrawer component (HTML + CSS)
- Implement slide-in animation
- Create /review endpoint (returns review data)
- Display source and style issues
- Add action buttons (Approve, Regenerate)
- Implement keyboard shortcut (Cmd/Ctrl + R)
- Wire up approve/regenerate actions

Success: Drawer slides in, shows issues, actions work

---

**Chunk 9: Success State (2-3 hours)**

Tasks:
- Create complete.html template
- Implement SuccessState component
- Add celebration animation sequence
- Create download endpoint
- Wire up "Start New Post" action
- Add stats count-up animation

Success: Celebration plays, download works, can start new post

---

**Chunk 10: Polish & Refinement (3-4 hours)**

Tasks:
- Add all micro-interactions (hover states, button effects)
- Implement magnetic button effect
- Add smooth stage transitions
- Test reduced-motion support
- Verify accessibility (keyboard nav, screen readers)
- Add error handling and edge cases
- Performance optimization (ensure 60fps)

Success: All interactions refined, accessibility verified, smooth performance

---

**Chunk 11: Integration Testing (2-3 hours)**

Tasks:
- Test complete workflow end-to-end
- Test with real content
- Test error cases (invalid paths, AI failures)
- Test resume functionality (if time permits)
- Verify CLI still works (`--mode cli`)
- Cross-browser testing (Chrome, Firefox, Safari)

Success: Full workflow works reliably, no regressions in CLI

---

**Total Estimated Time: 27-35 hours**

---

## Success Criteria

### Functional Requirements

✅ Runs via uvx with no installation required
✅ Checks for ANTHROPIC_API_KEY on startup
✅ Shows configuration screen if env vars missing
✅ Validates API key works before proceeding
✅ Stores credentials in-session only (never saved to disk)
✅ Supports .env file for local development
✅ Browser opens automatically on startup
✅ Can enter file paths via text input, browse, or drag-drop
✅ Path validation shows real-time feedback
✅ Can preview idea and writing samples before starting
✅ Real-time progress streams via SSE during AI processing
✅ Rich markdown editor with syntax highlighting and line numbers
✅ Preview toggle switches between source and rendered HTML
✅ Review drawer slides in with issues and actions
✅ Can approve draft and download final post
✅ Success state shows celebration animation
✅ CLI mode unaffected (`--mode cli` still works)

### Quality Requirements

✅ Design matches AESTHETIC-GUIDE.md (warm confidence aesthetic)
✅ All components match COMPONENT_SPECS.md
✅ WCAG AA accessibility (4.5:1 contrast, keyboard nav, screen readers)
✅ Smooth 60fps animations
✅ Reduced motion support
✅ Touch targets ≥44px
✅ Works on macOS, Linux, Windows/WSL
✅ Cross-browser compatible (Chrome, Firefox, Safari, Edge)

### Impression Goals

✅ Tech-savvy executives: "This is polished and professional"
✅ First-time users: "This is clear and welcoming"
✅ Power users: "This is efficient and respects my time"
✅ Designers: "This shows attention to detail and craft"

---

## Dependencies

### New Dependencies (Phase 4)

```toml
[project]
dependencies = [
    # ... existing deps ...
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "jinja2>=3.1.0",
    "python-markdown>=3.6.0",
    "python-dotenv>=1.0.0",  # Already present
    "bleach>=6.0.0",
]
```

**Rationale:**
- `fastapi` - Modern async web framework
- `uvicorn` - ASGI server (includes websockets for SSE)
- `jinja2` - Template engine
- `python-markdown` - Markdown to HTML conversion
- `python-dotenv` - .env file support (already in dependencies)
- `bleach` - HTML sanitization (XSS protection)

**Vendored assets:**
- HTMX (~14KB minified) - No npm install, just copy
- CodeMirror 6 bundle (~200KB) - Build once, vendor

---

## Risks & Mitigations

### Risk: Web Layer Adds Too Much Complexity

**Likelihood:** Medium
**Impact:** High

**Mitigation:**
- Keep web layer as thin adapter (NO business logic)
- Reuse core/ exactly as-is (proven and tested)
- Follow SSE example from IMPLEMENTATION_PHILOSOPHY.md
- Review against ruthless simplicity at each chunk

---

### Risk: SSE Progress Streaming Difficult

**Likelihood:** Low
**Impact:** Medium

**Mitigation:**
- Use simple asyncio.Queue pattern
- Reference SSE example from philosophy docs
- Test SSE endpoint independently before integrating
- Fallback: polling if SSE proves complex (unlikely)

---

### Risk: CodeMirror Integration Complex

**Likelihood:** Medium
**Impact:** Medium

**Mitigation:**
- Vendor pre-built bundle (no build step needed)
- Start with minimal config
- Add features incrementally
- Fallback: simpler textarea if CodeMirror proves difficult

---

### Risk: Cross-Platform Browser Open Fails

**Likelihood:** Low
**Impact:** Low

**Mitigation:**
- Python webbrowser module is standard library
- Works on all platforms
- Graceful fallback: print URL to console
- User can manually navigate

---

### Risk: HTMX Learning Curve

**Likelihood:** Medium
**Impact:** Low

**Mitigation:**
- HTMX is simple (HTML attributes for AJAX)
- Start with basic patterns (hx-post, hx-get, hx-target)
- Reference HTMX documentation
- Can fall back to standard forms if needed

---

### Risk: Design Vision Not Fully Realized

**Likelihood:** Medium
**Impact:** Medium

**Mitigation:**
- Component specs are detailed and complete
- Design tokens defined precisely
- Reference AESTHETIC-GUIDE.md during implementation
- Iterate in chunks (can refine as we go)
- User reviews in phases (not all-or-nothing)

---

## Timeline Estimate

**Phase 2 (Docs):** 2-3 hours
- Update README, HOW_I_BUILT_THIS, MIGRATION_NOTES
- Create web/README.md
- Review design docs

**Phase 3 (Code Plan):** 1-2 hours
- Detailed code implementation plan
- Chunk breakdown
- Right-sizing validation

**Phase 4 (Code Implementation):** 25-32 hours
- 10 chunks as outlined above
- Includes testing per chunk
- Includes refinement

**Phase 5 (Testing & Verification):** 3-4 hours
- End-to-end testing
- Accessibility audit
- Cross-browser testing
- CLI regression testing

**Phase 6 (Cleanup):** 1-2 hours
- Remove temporary files from ai_working/
- Final verification
- Documentation review

**Total: 32-43 hours** (spread over 1-2 weeks)

---

## Next Steps

### Approval Checklist

Before proceeding to Phase 2 (Documentation), verify:

- [ ] Problem clearly framed (user value articulated)
- [ ] Architecture makes sense (web/ parallel to cli/)
- [ ] Approach aligns with philosophy (ruthless simplicity, modular design)
- [ ] File changes reasonable (not too many, not too few)
- [ ] Component specs comprehensive (11 components fully defined)
- [ ] Test strategy sufficient (manual + accessibility + integration)
- [ ] Timeline acceptable (32-43 hours)
- [ ] Risks identified and mitigated
- [ ] Design vision approved (sophisticated warmth)
- [ ] Ready to proceed with documentation updates

---

### User Decisions Needed

Please confirm:

1. **Technology stack:** FastAPI + HTMX + Jinja2 (Python-only) ✅ or changes?
2. **Scope:** Happy path MVP (defer chat to Phase 3) ✅ or include chat now?
3. **Design aesthetic:** "Sophisticated warmth" as documented ✅ or refinements?
4. **Component specs:** 11 components as defined ✅ or additions?
5. **Timeline:** 32-43 hours acceptable ✅ or needs adjustment?

---

### When Approved

**Next command:** `/ddd:2-docs`

This will:
- Update all non-code files to reflect web layer
- Use retcon writing (as if already exists)
- Prevent context poisoning
- Create web/README.md
- Prepare for Phase 4 code implementation

The plan will guide all subsequent phases.

---

## Supporting Documents

**Design specifications:**
- `/ai_working/blog_web_interface/DESIGN_VISION.md` - Overall design philosophy
- `/ai_working/blog_web_interface/DESIGN_REFINEMENTS.md` - User feedback integrated
- `/ai_working/blog_web_interface/COMPONENT_SPECS.md` - Detailed component specs
- `/.design/AESTHETIC-GUIDE.md` - Visual system (colors, shadows, motion)

**Reference architecture:**
- `amplifier-app-blog-creator/src/amplifier_app_blog_creator/core/` - Business logic to wrap
- `amplifier-app-blog-creator/src/amplifier_app_blog_creator/cli/` - Pattern to follow

**Philosophy foundation:**
- `@ai_context/IMPLEMENTATION_PHILOSOPHY.md` - Ruthless simplicity
- `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md` - Bricks and studs
- `@ai_context/design/` - Design philosophy and principles

---

## Philosophy Validation

### Ruthless Simplicity ✅

**Questions:**
1. **Necessity:** Do we need this? → YES (better UX, impresses executives, enables future features)
2. **Simplicity:** Simplest approach? → YES (thin adapter, reuse core/, HTMX over React)
3. **Directness:** More direct solution? → NO (web UI is direct way to solve visual/editing limitations)
4. **Value:** Complexity justified? → YES (25-32 hours for significantly better UX is proportional)
5. **Maintenance:** Easy to understand? → YES (familiar patterns: FastAPI routes, Jinja templates, CSS)

### Modular Design ✅

**Bricks:**
- core/ (existing, unchanged)
- cli/ (existing, unchanged)
- web/ (new, independent)

**Studs:**
- BlogCreatorWorkflow interface (unchanged)
- SessionState model (unchanged)
- Progress callback (unchanged)

**Regeneratable:**
- Could rebuild web/ from route specs + component specs
- Core interface remains stable

### Design for Humans ✅

**Accessibility:**
- WCAG AA compliance throughout
- Keyboard navigation
- Screen reader support
- Reduced motion support
- Touch targets ≥44px

**User Experience:**
- First-time users: Visual guidance
- Power users: Keyboard shortcuts
- All users: Rich editing, live preview
- Executives: Professional polish

---

**This plan is ready for your review and approval.**
