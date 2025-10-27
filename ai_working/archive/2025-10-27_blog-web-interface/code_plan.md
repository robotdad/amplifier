# Code Implementation Plan - Blog Creator Web Interface

**Generated:** 2025-10-26
**Based on:** Phase 1 plan + Phase 2 approved documentation + zen-architect architectural review

---

## Summary

Implement web interface as thin adapter layer over existing core/ business logic. 8 implementation chunks executed sequentially, each independently testable and committable.

**Scope:** ~2,600 LOC across 25+ new files (routes, templates, static assets)
**Approach:** Sequential implementation (stage dependencies require order)
**Philosophy:** Ruthless simplicity + modular design (web/ as thin brick)

**Architectural Decisions (zen-architect approved):**
1. Extend SessionState for in-session credentials (no disk writes)
2. ProgressAdapter pattern for SSE (async queue bridge from sync callbacks)
3. CDN-hosted CodeMirror (no bundle bloat, textarea fallback)
4. Browser auto-open with graceful degradation
5. Minimal design tokens (not over-engineered for 5 pages)
6. Single implementation path (no variants initially)

---

## Current State vs Target State

**Current State:**
- ✅ core/ module complete and tested (Phase 1)
- ✅ cli/ module complete and tested (Phase 1)
- ✅ SessionManager working with file-based persistence
- ✅ BlogCreatorWorkflow with progress callbacks
- ⚠️ web/ directory exists but empty (only README.md)
- ⚠️ No web dependencies in pyproject.toml
- ⚠️ main.py only dispatches to CLI

**Target State (from approved docs):**
- web/ module as full adapter with FastAPI
- Mode selection: `--mode web` or `--mode cli`
- Stage 0: Configuration for env vars (in-session only)
- Stages 1-4: Setup, Progress, Review, Complete
- SSE progress streaming
- CodeMirror rich editing
- Browser auto-open
- Design system with warm aesthetic

**Gap:** Entire web/ implementation (~2,600 LOC)

---

## Refined Implementation Chunks

**Zen-architect refinement:** Merged project setup chunks, split editor/review, removed vague "polish" chunk

### Chunk 1: Foundation & Mode Dispatch

**Scope:** 3-4 hours
**Files:** 7 files
**Dependencies:** None

**Purpose:** Set up FastAPI infrastructure, mode selection, browser auto-open

### Chunk 2: Design System

**Scope:** 2-3 hours
**Files:** 5 files
**Dependencies:** Chunk 1

**Purpose:** Base template, design tokens, layout primitives

### Chunk 3: Stage 0 - Configuration

**Scope:** 3-4 hours
**Files:** 3 files
**Dependencies:** Chunk 1, 2

**Purpose:** Env var configuration, validation, in-session storage

### Chunk 4: Stage 1 - Setup

**Scope:** 4-5 hours
**Files:** 4 files
**Dependencies:** Chunk 3

**Purpose:** File path inputs, validation, preview

### Chunk 5: Stage 2 - Progress with SSE

**Scope:** 5-6 hours
**Files:** 4 files
**Dependencies:** Chunk 4

**Purpose:** Real-time progress streaming (highest complexity)

### Chunk 6: Stage 3 - Markdown Editor

**Scope:** 4-5 hours
**Files:** 3 files
**Dependencies:** Chunk 5

**Purpose:** CodeMirror integration, editing, auto-save

### Chunk 7: Stage 3 - Review Drawer

**Scope:** 3-4 hours
**Files:** 2 files
**Dependencies:** Chunk 6

**Purpose:** Review panel, issue display, actions

### Chunk 8: Stage 4 - Complete

**Scope:** 2-3 hours
**Files:** 2 files
**Dependencies:** Chunk 7

**Purpose:** Success state, download, restart

**Total Estimated Time:** 26-36 hours

---

## Chunk 1: Foundation & Mode Dispatch

### Files to Modify

#### File: `pyproject.toml`

**Current State:**
```toml
dependencies = [
    "amplifier-module-style-extraction",
    "amplifier-module-image-generation",
    "amplifier-module-markdown-utils",
    "anthropic>=0.25.0",
    "click>=8.0.0",
    "pydantic>=2.0.0",
    "pydantic-ai>=0.0.14",
    "python-dotenv>=1.0.0",
]
```

**Required Changes:**
Add web dependencies

**Specific Modifications:**
```toml
dependencies = [
    # ... existing deps ...
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "jinja2>=3.1.0",
    "python-markdown>=3.6.0",
    "bleach>=6.0.0",
    "starlette>=0.37.0",  # For SessionMiddleware
]
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/main.py`

**Current State:**
```python
def main():
    """Entry point dispatches to CLI."""
    return cli_main()
```

**Required Changes:**
Add mode detection and dispatch to web or CLI

**Specific Modifications:**
```python
import sys
from .cli.main import main as cli_main

def main():
    """Entry point - dispatch to CLI or web based on --mode flag."""
    # Quick mode detection before Click parsing
    if "--mode" in sys.argv:
        mode_idx = sys.argv.index("--mode")
        if mode_idx + 1 < len(sys.argv):
            mode = sys.argv[mode_idx + 1]
            if mode == "web":
                from .web.main import main as web_main
                return web_main()

    # Default: CLI mode
    return cli_main()
```

**Dependencies:** Requires web/main.py to exist

**Agent:** modular-builder

---

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/__init__.py`

**Purpose:** Web module exports

**Content:**
```python
"""Web interface module for blog creator."""

from .app import app
from .main import main

__all__ = ["app", "main"]
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/app.py`

**Purpose:** FastAPI application with browser auto-open

**Exports:** `app` (FastAPI instance)

**Dependencies:** None (base FastAPI)

**Implementation:**
```python
"""FastAPI application for blog creator web interface."""

import logging
import webbrowser
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env if present (for local development)
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup: Log that server is ready
    logger.info("Blog Creator web server started")
    yield
    # Shutdown: cleanup if needed
    logger.info("Blog Creator web server shutting down")

app = FastAPI(lifespan=lifespan)

# Session middleware for in-memory credentials
app.add_middleware(
    SessionMiddleware,
    secret_key="blog-creator-session-key",  # Runtime only
    max_age=1800  # 30 minutes
)

# Static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Templates
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

# Import routes (after app creation)
from .routes import configuration, sessions, progress, content

app.include_router(configuration.router)
app.include_router(sessions.router)
app.include_router(progress.router)
app.include_router(content.router)
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/main.py`

**Purpose:** Web mode entry point with browser auto-open

**Exports:** `main()` function

**Dependencies:** app.py

**Implementation:**
```python
"""Web mode entry point."""

import logging
import os
import threading
import time
import webbrowser
from pathlib import Path

import click
import uvicorn

logger = logging.getLogger(__name__)


def open_browser_delayed(url: str, delay: float = 1.5):
    """Open browser after server starts."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        logger.info(f"Opened browser to {url}")
    except Exception as e:
        logger.warning(f"Could not auto-open browser: {e}")
        print(f"\n🌐 Open your browser to: {url}\n")


@click.command()
@click.option("--no-browser", is_flag=True, help="Don't auto-open browser")
@click.option("--port", type=int, default=8000, help="Server port (default: 8000)")
@click.option("--host", type=str, default="localhost", help="Server host (default: localhost)")
def main(no_browser: bool, port: int, host: str):
    """Start blog creator web interface."""
    url = f"http://{host}:{port}"

    # Launch browser in background thread
    if not no_browser:
        thread = threading.Thread(
            target=open_browser_delayed,
            args=(url,),
            daemon=True
        )
        thread.start()
    else:
        print(f"\n🌐 Server starting at: {url}\n")

    # Start server
    uvicorn.run(
        "amplifier_app_blog_creator.web.app:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/routes/__init__.py`

**Purpose:** Routes package initialization

**Content:**
```python
"""Web routes."""

__all__ = []
```

**Agent:** modular-builder

---

### Testing for Chunk 1

**Manual test:**
```bash
cd amplifier-app-blog-creator
uv sync  # Install new dependencies
uv run blog-creator --mode web --no-browser

# Expected:
# - Server starts without errors
# - Logs show "http://localhost:8000"
# - Can manually navigate to URL
# - (No routes yet, will 404)

# Test browser open:
uv run blog-creator --mode web

# Expected:
# - Browser opens automatically
# - Shows 404 (expected - no routes yet)
```

**Success Criteria:**
- ✅ Dependencies install via uv sync
- ✅ Server starts without errors
- ✅ Browser opens automatically (macOS/Linux/Windows)
- ✅ `--mode cli` still works (no regressions)
- ✅ `--no-browser` flag works

**Commit Point:** After manual tests pass

---

## Chunk 2: Design System

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/templates/base.html`

**Purpose:** Base HTML layout for all pages

**Exports:** Jinja2 blocks (title, content, scripts)

**Implementation:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Blog Creator{% endblock %}</title>
    <link rel="stylesheet" href="/static/css/tokens.css">
    <link rel="stylesheet" href="/static/css/layout.css">
    <link rel="stylesheet" href="/static/css/components.css">
</head>
<body>
    <div class="app-layout">
        {% include "components/header.html" %}

        <main class="main-content">
            {% block content %}{% endblock %}
        </main>

        {% include "components/footer.html" %}
    </div>

    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/templates/components/header.html`

**Purpose:** Persistent header with logo

**Implementation:**
```html
<header class="header">
    <div class="header-content">
        <div class="logo">Blog Creator</div>
        {% if show_stage_indicator %}
            {% include "components/stage-indicator.html" %}
        {% endif %}
    </div>
</header>
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/templates/components/footer.html`

**Purpose:** Minimal footer

**Implementation:**
```html
<footer class="footer">
    <div class="footer-content">
        <span>Blog Creator</span>
        {% if iteration %}
            <span>Iteration: {{ iteration }} of {{ max_iterations }}</span>
        {% endif %}
    </div>
</footer>
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/templates/components/stage-indicator.html`

**Purpose:** Progress indicator showing current stage

**Implementation:**
```html
<nav class="stage-indicator" aria-label="Progress">
    <!-- Will implement in Chunk 3+ when we have actual stages -->
    <div class="stages">
        {% for stage in ["Configuration", "Setup", "Progress", "Review", "Complete"] %}
            <span class="stage {% if current_stage == stage %}current{% endif %}">
                {{ stage }}
            </span>
            {% if not loop.last %}<span class="arrow">→</span>{% endif %}
        {% endfor %}
    </div>
</nav>
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/static/css/tokens.css`

**Purpose:** Design tokens (colors, spacing, typography, shadows, motion)

**Content:** Minimal token set from AESTHETIC-GUIDE.md

**Implementation:**
```css
:root {
    /* Colors - Surfaces */
    --color-bg-primary: hsl(30, 15%, 97%);
    --color-bg-secondary: hsl(30, 20%, 99%);
    --color-bg-tertiary: hsl(30, 10%, 95%);
    --color-border: hsl(30, 10%, 88%);

    /* Colors - Accent */
    --color-accent: #D4943B;
    --color-accent-hover: hsl(35, 65%, 50%);

    /* Colors - Text */
    --color-text-primary: hsl(30, 10%, 20%);
    --color-text-secondary: hsl(30, 8%, 45%);
    --color-text-tertiary: hsl(30, 6%, 60%);

    /* Colors - Semantic */
    --color-success: hsl(140, 50%, 45%);
    --color-warning: hsl(35, 80%, 55%);
    --color-error: hsl(5, 70%, 55%);
    --color-info: hsl(210, 50%, 50%);

    /* Spacing (8px base) */
    --space-xs: 0.5rem;
    --space-sm: 1rem;
    --space-md: 1.5rem;
    --space-lg: 2rem;
    --space-xl: 3rem;

    /* Typography */
    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;

    /* Corners */
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;

    /* Shadows */
    --shadow-card: 0 2px 4px hsl(30deg 10% 20% / 0.06),
                   0 4px 12px hsl(30deg 10% 20% / 0.04),
                   0 8px 24px hsl(30deg 10% 20% / 0.03);

    --shadow-button: 0 1px 2px hsl(30deg 10% 20% / 0.08),
                     0 2px 8px hsl(30deg 10% 20% / 0.06),
                     0 4px 16px hsl(30deg 10% 20% / 0.04);

    /* Motion */
    --duration-quick: 250ms;
    --duration-standard: 350ms;
    --duration-slow: 500ms;
    --easing-spring: cubic-bezier(0.34, 1.35, 0.64, 1);
    --easing-standard: cubic-bezier(0.4, 0, 0.2, 1);
}

/* Dark mode support (future) */
@media (prefers-reduced-motion: reduce) {
    :root {
        --duration-quick: 0.01ms;
        --duration-standard: 0.01ms;
        --duration-slow: 0.01ms;
    }
}
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/static/css/layout.css`

**Purpose:** Grid system, app layout structure

**Implementation:**
```css
/* Base reset and typography */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: var(--font-family);
    font-size: 16px;
    line-height: 1.5;
    color: var(--color-text-primary);
    background: var(--color-bg-primary);
}

/* App layout */
.app-layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.main-content {
    flex: 1;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: var(--space-xl);
}

/* Header */
.header {
    height: 64px;
    background: var(--color-bg-secondary);
    border-bottom: 1px solid var(--color-border);
    box-shadow: var(--shadow-card);
}

.header-content {
    max-width: 1200px;
    height: 100%;
    margin: 0 auto;
    padding: 0 var(--space-md);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text-primary);
}

/* Footer */
.footer {
    height: 48px;
    background: var(--color-bg-tertiary);
    border-top: 1px solid var(--color-border);
}

.footer-content {
    max-width: 1200px;
    height: 100%;
    margin: 0 auto;
    padding: 0 var(--space-md);
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    color: var(--color-text-tertiary);
}

/* Card layouts */
.card {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-card);
    padding: var(--space-xl);
}

.card-centered {
    max-width: 600px;
    margin: 0 auto;
}
```

**Agent:** modular-builder

---

### Testing for Chunk 2

**Manual test:**
```bash
# Create a simple test route to verify templates work
# Add to app.py temporarily:
@app.get("/test")
async def test_template(request: Request):
    return templates.TemplateResponse("base.html", {
        "request": request
    })

uv run blog-creator --mode web
# Navigate to http://localhost:8000/test
# Expected: Base template renders with header/footer, design tokens applied
```

**Success Criteria:**
- ✅ Base template renders
- ✅ Design tokens load (warm colors visible)
- ✅ Header and footer visible
- ✅ No console errors

**Commit Point:** After templates render correctly

---

## Chunk 3: Stage 0 - Configuration

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/routes/configuration.py`

**Purpose:** Environment variable configuration and validation

**Exports:** FastAPI router with `/`, `/configure` endpoints

**Dependencies:** app.py, templates

**Implementation:**
```python
"""Configuration routes for environment variables."""

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import anthropic

from ...web.app import templates

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Entry point - check if API key configured."""
    # Check environment
    has_env_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    # Check session
    has_session_key = bool(request.session.get("ANTHROPIC_API_KEY"))

    if has_env_key or has_session_key:
        # Configured, go to workflow
        return RedirectResponse("/sessions/new", status_code=303)

    # Need configuration
    return RedirectResponse("/configure", status_code=303)


@router.get("/configure", response_class=HTMLResponse)
async def show_configuration(request: Request):
    """Show configuration form."""
    return templates.TemplateResponse(
        "configuration.html",
        {
            "request": request,
            "missing_vars": ["ANTHROPIC_API_KEY"],
        }
    )


@router.post("/configure")
async def validate_and_save(
    request: Request,
    ANTHROPIC_API_KEY: Annotated[str, Form()],
):
    """Validate API key and store in session."""
    # Basic format check
    if not ANTHROPIC_API_KEY.startswith("sk-ant-"):
        return HTMLResponse(
            '''<div id="config-feedback" class="feedback-error">
                <span class="error-icon">⚠</span>
                <span>API key should start with "sk-ant-"</span>
            </div>''',
            status_code=400
        )

    # Validate key works
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        # Test call
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": "test"}]
        )

        # Success - store in session
        request.session["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY

        return HTMLResponse(
            '''<div id="config-feedback" class="feedback-success">
                <span class="feedback-icon">✓</span>
                <span>API key validated! Redirecting...</span>
            </div>
            <script>
                setTimeout(() => {
                    window.location.href = "/sessions/new";
                }, 1000);
            </script>''',
            status_code=200
        )

    except anthropic.AuthenticationError:
        return HTMLResponse(
            '''<div id="config-feedback" class="feedback-error">
                <span class="error-icon">⚠</span>
                <span>Invalid API key - authentication failed</span>
            </div>''',
            status_code=400
        )
    except Exception as e:
        logger.error(f"API key validation error: {e}")
        return HTMLResponse(
            f'''<div id="config-feedback" class="feedback-error">
                <span class="error-icon">⚠</span>
                <span>Error: {str(e)}</span>
            </div>''',
            status_code=500
        )
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/templates/configuration.html`

**Purpose:** Configuration form UI

**Dependencies:** base.html, components.css

**Implementation:**
See component-designer output from earlier (full HTML template with form, help sidebar, security note)

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/static/css/components.css`

**Purpose:** Component-specific styles

**Implementation:**
Includes styles for:
- Configuration form
- Input fields
- Buttons (primary, secondary)
- Feedback messages
- Help sidebar

**Agent:** modular-builder

---

### Extension Required

#### File: `src/amplifier_app_blog_creator/core/workflow.py`

**Current State:**
```python
def __init__(self, session_manager: SessionManager, progress_callback=None):
    self.session = session_manager
    self.progress_callback = progress_callback
```

**Required Changes:**
Add support for retrieving API key from session

**Specific Modifications:**
```python
def __init__(self, session_manager: SessionManager, progress_callback=None, credentials: dict | None = None):
    self.session = session_manager
    self.progress_callback = progress_callback
    self.credentials = credentials or {}

def _get_api_key(self) -> str:
    """Get API key from credentials or environment."""
    return (
        self.credentials.get("ANTHROPIC_API_KEY") or
        os.getenv("ANTHROPIC_API_KEY") or
        ""
    )
```

**Agent:** modular-builder

**IMPORTANT:** This is a MINIMAL change to core/. Just adding credential pass-through, no business logic.

---

### Testing for Chunk 3

**Manual test:**
```bash
uv run blog-creator --mode web

# Should open to /configure
# Enter invalid key → See validation error
# Enter valid key → See success, redirect to /sessions/new (404 for now)

# Test env var skip:
export ANTHROPIC_API_KEY="sk-ant-..."
uv run blog-creator --mode web
# Should skip /configure, go straight to /sessions/new
```

**Success Criteria:**
- ✅ Configuration form renders
- ✅ API key validation works
- ✅ Invalid keys show helpful errors
- ✅ Valid keys redirect to workflow
- ✅ Env vars bypass configuration
- ✅ Credentials stored in-session only

**Commit Point:** After configuration flow works end-to-end

---

## Chunk 4: Stage 1 - Setup

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/routes/sessions.py`

**Purpose:** Session creation and file validation

**Exports:** Router with `/sessions/new`, `/sessions/{id}/validate-path`, `/sessions/{id}/preview-file`

**Dependencies:** templates, SessionManager

**Implementation:**
```python
"""Session management routes."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ...session import SessionManager
from ...web.app import templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")


class PathValidationRequest(BaseModel):
    path: str
    type: str  # "file" or "directory"


class PathValidationResponse(BaseModel):
    valid: bool
    type: str | None = None
    word_count: int | None = None
    file_count: int | None = None
    error: str | None = None


@router.get("/new", response_class=HTMLResponse)
async def new_session(request: Request):
    """Create new session and show setup page."""
    # Create session
    session_mgr = SessionManager()
    request.session["session_id"] = session_mgr.state.session_id

    return templates.TemplateResponse(
        "setup.html",
        {
            "request": request,
            "session_id": session_mgr.state.session_id,
        }
    )


@router.post("/{session_id}/validate-path")
async def validate_path(
    session_id: str,
    path: Annotated[str, Form()],
    type: Annotated[str, Form()],
):
    """Validate file or directory path."""
    try:
        p = Path(path).expanduser()

        if not p.exists():
            return HTMLResponse(
                '''<div class="feedback feedback-invalid">
                    <span class="feedback-icon">⚠</span>
                    Path does not exist
                </div>''',
                status_code=200
            )

        if type == "file":
            if not p.is_file():
                return HTMLResponse(
                    '''<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        Path is not a file
                    </div>''',
                    status_code=200
                )

            if p.suffix not in [".md", ".txt"]:
                return HTMLResponse(
                    '''<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        File must be .md or .txt
                    </div>''',
                    status_code=200
                )

            content = p.read_text()
            word_count = len(content.split())

            return HTMLResponse(
                f'''<div class="feedback feedback-valid">
                    <span class="feedback-icon">✓</span>
                    Valid - {word_count} words
                </div>''',
                status_code=200
            )

        elif type == "directory":
            if not p.is_dir():
                return HTMLResponse(
                    '''<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        Path is not a directory
                    </div>''',
                    status_code=200
                )

            md_files = list(p.glob("*.md"))
            file_count = len(md_files)

            if file_count == 0:
                return HTMLResponse(
                    '''<div class="feedback feedback-invalid">
                        <span class="feedback-icon">⚠</span>
                        No .md files found
                    </div>''',
                    status_code=200
                )

            return HTMLResponse(
                f'''<div class="feedback feedback-valid">
                    <span class="feedback-icon">✓</span>
                    Valid - {file_count} samples found
                </div>''',
                status_code=200
            )

    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return HTMLResponse(
            f'''<div class="feedback feedback-invalid">
                <span class="feedback-icon">⚠</span>
                Error: {str(e)}
            </div>''',
            status_code=500
        )


@router.post("/{session_id}/start-workflow")
async def start_workflow(
    request: Request,
    session_id: str,
    idea_path: Annotated[str, Form()],
    writings_dir: Annotated[str, Form()],
    instructions: Annotated[str | None, Form()] = None,
):
    """Start the blog creation workflow."""
    # TODO: Implement in Chunk 5 (Progress)
    return RedirectResponse(f"/sessions/{session_id}/progress", status_code=303)
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/templates/setup.html`

**Purpose:** Setup stage UI (file inputs, previews, start button)

**Dependencies:** base.html, path-input component styles

**Implementation:**
Uses PathInput and FilePreview components from COMPONENT_SPECS.md

**Agent:** modular-builder

---

### Testing for Chunk 4

**Manual test:**
```bash
uv run blog-creator --mode web

# Complete configuration (if needed)
# Should land on /sessions/new (Setup page)

# Test path validation:
# - Enter invalid path → See error
# - Enter valid file → See validation
# - Enter valid directory → See file count

# Click "Start Creation" → Redirect to /progress (404 for now)
```

**Success Criteria:**
- ✅ Setup page renders
- ✅ Path validation works for files
- ✅ Path validation works for directories
- ✅ File preview shows content
- ✅ Start button redirects to progress

**Commit Point:** After setup flow works

---

## Chunk 5: Stage 2 - Progress with SSE

**SIMPLIFIED: Just message streaming, no complex progress state**

**Key Insight:** CLI only shows text messages ("Analyzing writing samples..."), not progress bars or time estimates. Web should match this simple pattern.

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/routes/progress.py`

**Purpose:** SSE message streaming (simple string updates)

**Exports:** Router with `/sessions/{id}/progress` SSE endpoint

**Implementation:**
Simple message queue - just push strings from progress_callback

```python
"""Progress streaming via Server-Sent Events."""

import asyncio
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ...core.workflow import BlogCreatorWorkflow
from ...session import SessionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sessions")


class MessageQueue:
    """Simple message queue for SSE streaming."""

    def __init__(self):
        self.queue = asyncio.Queue()

    def add_message(self, message: str):
        """Sync callback from core/stages - just push the message."""
        asyncio.create_task(self.queue.put(message))

    async def stream(self):
        """Async SSE generator - yield messages as they arrive."""
        while True:
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=30.0)
                yield {"data": message}
            except asyncio.TimeoutError:
                # Keepalive
                yield {"comment": "keepalive"}


@router.get("/{session_id}/progress")
async def stream_progress(session_id: str):
    """SSE stream of workflow messages."""
    message_queue = MessageQueue()

    async def run_workflow():
        """Run workflow in background, messages stream to client."""
        session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
        workflow = BlogCreatorWorkflow(
            session_mgr,
            progress_callback=message_queue.add_message  # Just push messages
        )

        # Get parameters
        idea_path = Path(session_mgr.state.idea_path)
        writings_dir = Path(session_mgr.state.writings_dir)
        brain_dump = idea_path.read_text()

        try:
            # Run all stages
            await workflow.run_style_extraction(writings_dir)
            await workflow.run_draft_generation(brain_dump, session_mgr.state.additional_instructions)
            await workflow.run_review()

            # Signal completion
            message_queue.add_message("COMPLETE")

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            message_queue.add_message(f"ERROR: {str(e)}")

    # Start workflow in background
    asyncio.create_task(run_workflow())

    # Stream messages to client
    return EventSourceResponse(message_queue.stream())
```

**Dependencies:** `sse-starlette>=2.1.0` (add to pyproject.toml)

**Agent:** modular-builder

**Note:** Simplified from original complex progress tracking - just streams text messages from core/stages

---

#### File: `src/amplifier_app_blog_creator/web/templates/progress.html`

**Purpose:** Progress visualization UI

**Implementation:**
```html
{% extends "base.html" %}

{% block content %}
<div class="progress-container">
    <h1>Creating Your Post...</h1>

    <div class="progress-card">
        <div class="spinner"></div>
        <p id="status-message">Starting workflow...</p>
    </div>
</div>

<script>
const sessionId = "{{ session_id }}";
const eventSource = new EventSource(`/sessions/${sessionId}/progress`);

eventSource.onmessage = function(event) {
    const message = event.data;

    if (message === "COMPLETE") {
        eventSource.close();
        window.location.href = `/sessions/${sessionId}/review`;
    } else if (message.startsWith("ERROR:")) {
        document.getElementById('status-message').textContent = message;
        document.querySelector('.spinner').style.display = 'none';
        eventSource.close();
    } else {
        // Just update the message
        document.getElementById('status-message').textContent = message;
    }
};

eventSource.onerror = function(event) {
    console.error("Connection error:", event);
    document.getElementById('status-message').textContent = "Connection lost - please refresh";
    eventSource.close();
};
</script>
{% endblock %}
```

**Agent:** modular-builder

---

### Testing for Chunk 5

**Test:**
```bash
uv run blog-creator --mode web

# Complete configuration
# Enter valid paths on setup
# Click "Start Creation"

# Expected:
# - Redirect to /progress
# - See "Starting workflow..."
# - Messages update: "Analyzing writing samples..."
# - Then: "Style extraction complete"
# - Then: "Generating draft..."
# - Then: "Draft complete (2793 characters)"
# - Then: "Reviewing draft for accuracy..."
# - Then: "Review complete (2 issues found)"
# - Then: Redirect to /review

# Total time: ~30-40 seconds
# Messages should appear as stages complete (no delay)
```

**Success Criteria:**
- ✅ SSE connection establishes
- ✅ Messages stream from core/stages callbacks
- ✅ Messages display in real-time
- ✅ Workflow completes and redirects
- ✅ Error handling if workflow fails

**Commit Point:** After message streaming works end-to-end

---

## Chunk 6: Stage 3 - Markdown Editor

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/routes/content.py`

**Purpose:** Markdown rendering and draft operations

**Exports:** `/render-markdown`, `/sessions/{id}/draft` (GET/PUT)

**Implementation:**
```python
"""Content operations - markdown rendering and draft management."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Request, Body
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import markdown
import bleach

from ...session import SessionManager
from ...web.app import templates

logger = logging.getLogger(__name__)
router = APIRouter()


class RenderMarkdownRequest(BaseModel):
    content: str


class RenderMarkdownResponse(BaseModel):
    html: str


@router.post("/render-markdown")
async def render_markdown(req: RenderMarkdownRequest):
    """Render markdown to sanitized HTML."""
    # Convert markdown
    html = markdown.markdown(
        req.content,
        extensions=['fenced_code', 'tables', 'nl2br']
    )

    # Sanitize for XSS protection
    safe_html = bleach.clean(
        html,
        tags=bleach.ALLOWED_TAGS + ['p', 'pre', 'code', 'h1', 'h2', 'h3', 'table', 'tr', 'td', 'th'],
        attributes=bleach.ALLOWED_ATTRIBUTES
    )

    return {"html": safe_html}


@router.get("/sessions/{session_id}/draft")
async def get_draft(session_id: str):
    """Get current draft content."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    return {"content": session_mgr.state.current_draft}


@router.put("/sessions/{session_id}/draft")
async def update_draft(
    session_id: str,
    content: Annotated[str, Body(embed=True)]
):
    """Update draft content (auto-save)."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    session_mgr.update_draft(content)
    session_mgr.save()
    return {"saved": True}
```

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/templates/review.html`

**Purpose:** Editor UI with CodeMirror

**Implementation:**
```html
{% extends "base.html" %}

{% block content %}
<div class="review-container">
    <div class="editor-workspace">
        <div class="editor-toolbar">
            <button onclick="togglePreview()" class="toolbar-button">
                <span id="preview-icon">👁️</span> Preview
            </button>
        </div>

        <div id="editor-container"></div>
        <div id="markdown-preview" style="display: none;"></div>
    </div>

    <div class="review-actions">
        <button class="button button-secondary" onclick="openReviewDrawer()">
            Review Issues <span id="issue-count"></span>
        </button>
        <button class="button button-primary" onclick="approve()">
            Approve & Finalize
        </button>
    </div>
</div>

<!-- Load CodeMirror from vendored bundle -->
<script src="/static/js/codemirror.min.js"></script>
<link rel="stylesheet" href="/static/css/codemirror.css">
<script src="/static/js/codemirror-markdown.min.js"></script>

<script>
const editor = CodeMirror(document.getElementById('editor-container'), {
    value: {{ draft | tojson }},
    mode: 'markdown',
    lineNumbers: true,
    lineWrapping: true,
    theme: 'default'
});

// Auto-save on change
let saveTimeout;
editor.on('change', () => {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
        const content = editor.getValue();
        await fetch('/sessions/{{ session_id }}/draft', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content})
        });
    }, 1000);
});

function togglePreview() {
    const editorEl = document.getElementById('editor-container');
    const previewEl = document.getElementById('markdown-preview');
    const icon = document.getElementById('preview-icon');

    if (previewEl.style.display === 'none') {
        // Show preview
        editorEl.style.display = 'none';
        previewEl.style.display = 'block';
        icon.textContent = '✏️';

        // Render markdown
        fetch('/render-markdown', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({content: editor.getValue()})
        })
        .then(r => r.json())
        .then(data => {
            previewEl.innerHTML = data.html;
        });
    } else {
        // Show editor
        editorEl.style.display = 'block';
        previewEl.style.display = 'none';
        icon.textContent = '👁️';
    }
}
</script>
{% endblock %}
```

**Agent:** modular-builder

---

### Testing for Chunk 6

**Manual test:**
```bash
# After completing workflow (Chunk 5)
# Should land on /sessions/{id}/review

# Test editor:
# - Draft loads in CodeMirror
# - Can edit content
# - Syntax highlighting visible
# - Line numbers show
# - Auto-save works (check network tab)

# Test preview:
# - Click preview button
# - Markdown renders as HTML
# - Click again to return to editor
```

**Success Criteria:**
- ✅ CodeMirror loads from CDN
- ✅ Draft content populates editor
- ✅ Syntax highlighting works
- ✅ Auto-save triggers on changes
- ✅ Preview toggle works
- ✅ Markdown renders correctly

**Commit Point:** After editor works end-to-end

---

## Chunk 7: Stage 3 - Review Drawer

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/routes/sessions.py` (extend)

**Add endpoints:**
```python
@router.get("/{session_id}/review-data")
async def get_review_data(session_id: str):
    """Get review results for current draft."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    return {
        "source_issues": session_mgr.state.source_review.get("issues", []),
        "style_issues": session_mgr.state.style_review.get("issues", []),
        "iteration": session_mgr.state.iteration,
        "max_iterations": session_mgr.state.max_iterations,
    }


@router.post("/{session_id}/approve")
async def approve_draft(session_id: str):
    """Finalize approved draft."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))

    # Save final draft
    final_path = session_mgr.save_final_post()

    return {"download_path": str(final_path)}
```

**Agent:** modular-builder

---

#### Update: `src/amplifier_app_blog_creator/web/templates/review.html`

**Add review drawer component:**

Slide-out panel from right with review results (from COMPONENT_SPECS.md ReviewDrawer)

**Agent:** modular-builder

---

### Testing for Chunk 7

**Manual test:**
```bash
# On review page
# Click "Review Issues" button

# Expected:
# - Drawer slides in from right (350ms)
# - Shows source issues
# - Shows style issues
# - Shows iteration count
# - Actions: Approve, Regenerate

# Click Approve → Redirect to /complete
```

**Success Criteria:**
- ✅ Drawer animation smooth
- ✅ Review data loads
- ✅ Issues display correctly
- ✅ Approve action works
- ✅ Keyboard shortcut (Cmd/Ctrl+R) toggles drawer

**Commit Point:** After review workflow complete

---

## Chunk 8: Stage 4 - Complete

### Files to Create

#### File: `src/amplifier_app_blog_creator/web/templates/complete.html`

**Purpose:** Success state with download

**Implementation:**
Uses SuccessState component from COMPONENT_SPECS.md

**Agent:** modular-builder

---

#### File: `src/amplifier_app_blog_creator/web/routes/sessions.py` (extend)

**Add endpoint:**
```python
@router.get("/{session_id}/download")
async def download_final_post(session_id: str):
    """Download final blog post."""
    session_mgr = SessionManager(Path(f".data/blog_creator/{session_id}"))
    final_path = session_mgr.session_dir / f"{session_mgr.state.slug}.md"

    if not final_path.exists():
        raise HTTPException(404, "Final post not found")

    return FileResponse(
        final_path,
        filename=final_path.name,
        media_type="text/markdown"
    )
```

**Agent:** modular-builder

---

### Testing for Chunk 8

**Manual test:**
```bash
# After approving draft
# Should land on /sessions/{id}/complete

# Expected:
# - Checkmark animates in
# - Stats count up
# - Download button visible

# Click Download
# - File downloads as .md
# - Content matches final draft

# Click "Start New Post"
# - Returns to /configure or /sessions/new
```

**Success Criteria:**
- ✅ Success page renders
- ✅ Celebration animation plays
- ✅ Download works
- ✅ Restart flow works

**Commit Point:** After complete workflow end-to-end

---

## Agent Orchestration Strategy

### Primary Agent: modular-builder

Use for ALL implementation chunks:

```bash
Task modular-builder: "Implement Chunk [N]: [Name]

Reference:
- ai_working/ddd/code_plan.md (this file)
- Approved documentation in README.md and web/README.md
- Component specs in ai_working/blog_web_interface/COMPONENT_SPECS.md
- Design tokens in .design/AESTHETIC-GUIDE.md

Implement all files listed in Chunk [N] section.
Run tests to verify.
Report when ready for commit."
```

### Support Agents

**bug-hunter** - If issues arise during implementation:
```bash
Task bug-hunter: "Debug SSE streaming issue in progress.py

Error: [describe error]
Expected: [expected behavior]
Actual: [actual behavior]"
```

**test-coverage** - For test planning:
```bash
Task test-coverage: "Suggest comprehensive tests for web/routes/sessions.py

Functions to test:
- validate_path()
- start_workflow()
- approve_draft()

What edge cases should we cover?"
```

---

## Testing Strategy

### Unit Tests

**File: `tests/web/test_routes_sessions.py`**
- Test path validation (valid files, invalid paths, wrong types)
- Test session creation
- Test draft operations (get, update)

**File: `tests/web/test_routes_configuration.py`**
- Test API key validation (valid, invalid, network errors)
- Test session storage
- Test env var detection

**File: `tests/web/test_message_queue.py`**
- Test MessageQueue callback capture
- Test async queue behavior
- Test SSE event generation

### Integration Tests

**File: `tests/web/test_workflow_integration.py`**
- Test complete workflow: configure → setup → progress → review → complete
- Test with real SessionManager and BlogCreatorWorkflow
- Verify no regressions in core/

### User Testing Plan

**Commands to run:**
```bash
# Test 1: Basic workflow
export ANTHROPIC_API_KEY="sk-ant-..."
uv run blog-creator --mode web

# Follow workflow:
# 1. See setup page (env var set, skip config)
# 2. Enter paths
# 3. Start workflow
# 4. Watch progress
# 5. Edit draft
# 6. Approve
# 7. Download

# Test 2: Configuration flow
unset ANTHROPIC_API_KEY
uv run blog-creator --mode web

# Expected:
# 1. See configuration page
# 2. Enter API key
# 3. Validate (makes API call)
# 4. Proceed to setup

# Test 3: CLI still works
uv run blog-creator --idea test.md --writings-dir posts/
# Expected: CLI works unchanged
```

---

## Philosophy Compliance Verification

### Ruthless Simplicity ✅

**What we're building:**
- Thin adapter layer (web/ has NO business logic)
- Reuses all core/ (zero duplication)
- HTMX over React (simpler, less JavaScript)
- SSE over WebSockets (one-way is sufficient)
- CDN CodeMirror (no build step)
- Extend SessionState (don't create new session manager)

**What we're NOT building:**
- User accounts (local-only tool)
- Database (file-based sessions work)
- Complex state management (server owns state)
- Multiple design variants (single path initially)
- Advanced editor features (basic editing sufficient)

**Clear over clever:**
- Server-rendered templates (straightforward)
- HTMX attributes for interactions (declarative)
- Simple ProgressAdapter (async queue pattern)
- Standard FastAPI patterns (no custom abstractions)

### Modular Design ✅

**Bricks:**
- core/ (existing, unchanged)
- cli/ (existing, unchanged)
- web/ (new, independent)

**Studs (interfaces remain stable):**
- BlogCreatorWorkflow API unchanged
- SessionManager API unchanged (minimal extension)
- Progress callback signature unchanged

**Regeneratable:**
- Can rebuild web/ from route specs + component specs
- Can rebuild templates from wireframes
- Core/ interface never changes

---

## Commit Strategy

**Commit 1: Foundation & Mode Dispatch**
```
feat(web): Add FastAPI foundation and mode selection

- Add web dependencies to pyproject.toml
- Create web/ module structure
- Implement mode dispatcher in main.py
- Add browser auto-open in web/main.py
- Create base FastAPI app with middleware

Tests: Server starts, browser opens, mode selection works
```

**Commit 2: Design System**
```
feat(web): Add design tokens and base templates

- Create base.html layout
- Add design tokens (colors, spacing, shadows)
- Create header/footer components
- Add layout CSS primitives

Tests: Templates render with warm aesthetic
```

**Commit 3: Configuration Stage**
```
feat(web): Add API key configuration (Stage 0)

- Create configuration form UI
- Implement API key validation
- Add in-session credential storage
- Support .env file loading

Tests: Configuration flow works, API key validates
```

**Commit 4: Setup Stage**
```
feat(web): Add file input stage (Stage 1)

- Create setup page with path inputs
- Implement file/directory validation
- Add file preview functionality
- Wire up workflow start

Tests: Path validation works, file preview shows
```

**Commit 5: Progress with SSE**
```
feat(web): Add real-time progress (Stage 2)

- Implement SSE progress streaming
- Create ProgressAdapter for async/sync bridge
- Add progress visualization UI
- Wire up workflow execution

Tests: SSE streams progress, workflow completes
```

**Commit 6: Markdown Editor**
```
feat(web): Add rich markdown editor (Stage 3)

- Integrate CodeMirror from CDN
- Implement auto-save functionality
- Add preview toggle
- Create markdown rendering endpoint

Tests: Editor loads, auto-save works, preview renders
```

**Commit 7: Review Drawer**
```
feat(web): Add review panel (Stage 3)

- Create slide-out review drawer
- Display source/style issues
- Add approve/regenerate actions
- Implement keyboard shortcut

Tests: Drawer slides, review data loads, actions work
```

**Commit 8: Complete Stage**
```
feat(web): Add success state (Stage 4)

- Create success page with celebration
- Implement download functionality
- Add restart workflow action

Tests: Success page shows, download works, restart works
```

---

## Risk Assessment

### LOW RISK: SSE Message Streaming (Chunk 5) - REVISED

**Simplified approach:** Just stream text messages (not complex progress state)

**What we're doing:**
- MessageQueue with simple async queue
- Push strings from progress_callback
- Display messages as they arrive (no progress bars/time estimates)
- Matches CLI behavior exactly

**Mitigation:**
- Simple pattern (just strings, no complex state)
- Keepalive pings (30s timeout)
- Error handling for workflow exceptions
- Test with real workflow

**Contingency:** Fall back to polling if any issues (2-second interval)

**Risk reduced from HIGH → LOW due to simplification**

---

### LOW RISK: CodeMirror Integration (Chunk 6) - REVISED

**Vendored approach:** Include CodeMirror bundle in package (~250KB)

**What we're doing:**
- Download and vendor CodeMirror 5.65.16
- Include in static/js/ directory
- Load from local file (not CDN)
- No external dependencies at runtime

**Mitigation:**
- One-time build step to create bundle
- Pin version for stability
- Test with large drafts (5000+ words)
- Custom CSS for warm theme

**Benefits:**
- ✅ Works offline
- ✅ Works behind firewalls
- ✅ Faster load (local file)
- ✅ Version locked

**Risk reduced from MEDIUM → LOW due to vendoring**

---

### LOW RISK: Browser Auto-Open (Chunk 1)

**What could go wrong:**
- Doesn't work in headless environments (CI, Docker)
- User has no default browser set
- Windows/Linux edge cases

**Mitigation:**
- Graceful degradation (print URL)
- Test on all platforms
- `--no-browser` flag available

**Contingency:** Already handled - just prints URL

---

### LOW RISK: Session State Extension (Chunk 3)

**What could go wrong:**
- Credentials accidentally serialized to disk
- Session expiry loses credentials
- Multiple tabs share session incorrectly

**Mitigation:**
- Use `field(repr=False)` on credentials
- Exclude from JSON serialization explicitly
- SessionMiddleware handles per-browser-session isolation
- Test credential isolation

**Contingency:** Separate credential dict in app state (not SessionState)

---

## Success Criteria

### Code Implementation Complete When:

**Functional:**
- [ ] All 8 chunks implemented
- [ ] All endpoints return expected responses
- [ ] All templates render correctly
- [ ] SSE progress streaming works
- [ ] CodeMirror editor functional
- [ ] Complete workflow end-to-end works
- [ ] CLI mode still works (`--mode cli`)

**Quality:**
- [ ] All tests passing (`uv run pytest`)
- [ ] No type errors (`uv run pyright`)
- [ ] Design matches AESTHETIC-GUIDE.md
- [ ] Accessibility requirements met (WCAG AA)
- [ ] No console errors in browser
- [ ] Smooth 60fps animations

**Philosophy:**
- [ ] web/ is thin adapter (no business logic)
- [ ] core/ unchanged (zero modifications except credential pass-through)
- [ ] Simplicity maintained (HTMX over complex JS)
- [ ] Modular design (clear bricks and studs)

---

## Next Steps

✅ Code plan complete and detailed
⏳ **Awaiting user approval**

**Questions for user:**
1. Approve 8-chunk implementation approach?
2. Approve SessionState extension for credentials?
3. Approve ProgressAdapter pattern for SSE?
4. Approve CDN-hosted CodeMirror (with textarea fallback)?
5. Any concerns about 27-35 hour estimate?

**When approved, run:** `/ddd:4-code`

This will execute Chunk 1, verify with tests, get your commit approval, then proceed to Chunk 2, and so on.

---

## Supporting Documents

**Design specifications:**
- `ai_working/blog_web_interface/DESIGN_VISION.md`
- `ai_working/blog_web_interface/DESIGN_REFINEMENTS.md`
- `ai_working/blog_web_interface/COMPONENT_SPECS.md`
- `.design/AESTHETIC-GUIDE.md`

**Architecture guidance:**
- zen-architect output (in this session)
- component-designer output (ConfigurationStage)

**Approved documentation (the spec):**
- `README.md`
- `HOW_I_BUILT_THIS.md`
- `MIGRATION_NOTES.md`
- `src/amplifier_app_blog_creator/web/README.md`
