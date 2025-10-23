# Code Implementation Plan: Blog Creator Migration

**Generated**: 2025-10-22
**Based on**: Phase 1 plan + Phase 2 documentation + code reconnaissance

---

## Summary

Migrate ~3,800 lines of production-tested code from scenarios/ to amplifier-dev ecosystem:
- Extract 3 reusable modules (image-generation, style-extraction, markdown-utils)
- Create 1 unified app (blog-creator) composing all modules
- Follow amplifier-dev patterns (git sources, capability registry, path expansion)

**Total Scope**: 28 Python files → reorganized into modular structure

---

## Implementation Chunks

### Chunk 1: Module Foundations (Data Models & Protocols)

**Purpose**: Create foundational types that other code depends on
**Why First**: Everything else imports these
**Estimated**: 2-3 hours, ~300 LOC

#### Files to Create:

**amplifier-module-image-generation/src/amplifier_module_image_generation/models.py**
- Source: `scenarios/article_illustrator/models.py` (image-related models)
- Classes: `ImageResult`, `GeneratedImage`, `ImageAlternatives`
- Changes: Simplify to match documented API (ImageResult only for public API)
- Dependencies: None
- Tests: Unit tests for model validation

**amplifier-module-image-generation/src/amplifier_module_image_generation/protocol.py**
- New file based on: `scenarios/article_illustrator/image_generation/clients.py` (Protocol)
- Interface: `ImageProviderProtocol`
- Purpose: Extension point for new providers
- Dependencies: models.py
- Tests: Protocol compliance tests

**amplifier-module-style-extraction/src/amplifier_module_style_extraction/models.py**
- Source: `scenarios/blog_writer/style_extractor/core.py` (StyleProfile class)
- Classes: `StyleProfile` (Pydantic)
- Changes: Add `to_prompt_text()` method
- Dependencies: pydantic
- Tests: Model validation, serialization

**amplifier-module-markdown-utils/src/amplifier_module_markdown_utils/models.py**
- Source: New, based on content_analysis patterns
- Classes: `MarkdownDocument`, `MarkdownSection`
- Purpose: Structure representation
- Dependencies: None
- Tests: Model creation and validation

**Commit Point**: After unit tests pass for all models

---

### Chunk 2: Image Generation Module

**Purpose**: Complete image-generation module
**Why Second**: Self-contained, no dependencies on other new modules
**Estimated**: 4-6 hours, ~600 LOC

#### Files to Migrate:

**1. amplifier-module-image-generation/src/amplifier_module_image_generation/clients.py**
- **Source**: `scenarios/article_illustrator/image_generation/clients.py` (389 LOC)
- **Current**: `ImagenClient`, `DalleClient`, `GptImageClient`
- **Changes Required**:
  - Keep: All three client implementations
  - Add: `.expanduser()` to any config paths
  - Update: Error messages to be more descriptive
  - Keep: Protocol compliance as-is
- **Dependencies**: models.py, protocol.py
- **Tests**: `tests/test_clients.py` - Test each client with mock APIs

**2. amplifier-module-image-generation/src/amplifier_module_image_generation/generator.py**
- **Source**: `scenarios/article_illustrator/image_generation/core.py` (181 LOC)
- **Current**: `ImageGenerator` orchestrator
- **Changes Required**:
  - Rename: `ImageGenerator` stays same
  - Add: Capability registry registration
    ```python
    if coordinator:
        coordinator.register_capability("image_generation.orchestrator", self)
    ```
  - Add: Standalone fallback mode
  - Update: Return `ImageResult` (simplified from `ImageAlternatives`)
  - Keep: Multi-API orchestration, cost tracking, parallel generation
- **Dependencies**: clients.py, models.py
- **Tests**: `tests/test_generator.py` - Orchestration logic, fallback, cost tracking

**3. amplifier-module-image-generation/src/amplifier_module_image_generation/__init__.py**
- **Source**: `scenarios/article_illustrator/image_generation/__init__.py`
- **Changes Required**:
  - Export: `ImageGenerator`, `ImageResult`, `ImageGenerationError`
  - Add: `__all__` list for clean public API
  - Add: `py.typed` marker file for type checking
- **Tests**: Import tests

**Commit Point**: After all image-generation tests pass

---

### Chunk 3: Style Extraction Module

**Purpose**: Complete style-extraction module
**Why Third**: Self-contained, tested pattern from blog_writer
**Estimated**: 3-4 hours, ~250 LOC

#### Files to Migrate:

**1. amplifier-module-style-extraction/src/amplifier_module_style_extraction/extractor.py**
- **Source**: `scenarios/blog_writer/style_extractor/core.py` (188 LOC)
- **Current**: `StyleExtractor` class with LLM-based analysis
- **Changes Required**:
  - Keep: Core extraction logic, defensive parsing, retry with feedback
  - Add: Capability registry registration
    ```python
    if coordinator:
        coordinator.register_capability("style_extraction.analyzer", self)
        coordinator.register_capability("style_extraction.current_profile", profile)
    ```
  - Add: `.expanduser()` for `samples_dir` path
  - Move: `StyleProfile` model to separate models.py (already in Chunk 1)
  - Keep: Default profile fallback, array response handling
- **Dependencies**: models.py (StyleProfile)
- **Tests**: `tests/test_extractor.py` - Extraction logic, fallbacks, error handling

**2. amplifier-module-style-extraction/src/amplifier_module_style_extraction/__init__.py**
- **Source**: `scenarios/blog_writer/style_extractor/__init__.py`
- **Changes Required**:
  - Export: `StyleExtractor`, `StyleProfile`, `StyleExtractionError`
  - Add: `__all__` list
  - Add: `py.typed` marker
- **Tests**: Import tests

**Commit Point**: After all style-extraction tests pass

---

### Chunk 4: Markdown Utils Module

**Purpose**: Consolidate markdown utilities from both tools
**Why Fourth**: Needed by app, consolidates duplicate code
**Estimated**: 4-5 hours, ~450 LOC

#### Files to Migrate and Consolidate:

**1. amplifier-module-markdown-utils/src/amplifier_module_markdown_utils/metadata.py**
- **Source**: `scenarios/blog_writer/state.py` (lines 10-40, ~30 LOC)
- **Functions to Extract**:
  - `extract_title_from_markdown(content: str) -> str | None`
  - `slugify(title: str) -> str`
- **Changes Required**:
  - Rename: `extract_title_from_markdown` → `extract_title`
  - Add: `extract_title_from_file(path: Path)` helper
  - Keep: Implementation as-is (simple, works well)
- **Dependencies**: None
- **Tests**: `tests/test_metadata.py` - Various title formats, slug edge cases

**2. amplifier-module-markdown-utils/src/amplifier_module_markdown_utils/parser.py**
- **Source**: `scenarios/article_illustrator/content_analysis/core.py` (160 LOC, parsing logic)
- **Current**: `ContentAnalyzer` (identifies illustration points)
- **Changes Required**:
  - Extract: Structure parsing logic → `MarkdownParser.parse()`
  - Separate: Illustration identification stays in app (app-specific policy)
  - Create: `MarkdownDocument`, `MarkdownSection` models
  - Simplify: Just parse structure, don't analyze for illustrations
- **Dependencies**: models.py
- **Tests**: `tests/test_parser.py` - Parse various markdown structures

**3. amplifier-module-markdown-utils/src/amplifier_module_markdown_utils/updater.py**
- **Source**: `scenarios/article_illustrator/markdown_update/core.py` (132 LOC)
- **Current**: `MarkdownUpdater` (inserts images)
- **Changes Required**:
  - Keep: Image insertion logic
  - Add: Flexible placement strategies (before/after section, at line)
  - Simplify: Remove article-specific assumptions
  - Generalize: Support any content injection, not just images
- **Dependencies**: parser.py (for finding sections)
- **Tests**: `tests/test_updater.py` - Various insertion scenarios

**4. amplifier-module-markdown-utils/src/amplifier_module_markdown_utils/__init__.py**
- **New File**
- **Exports**: `extract_title`, `slugify`, `MarkdownParser`, `MarkdownImageUpdater`, `MarkdownDocument`, `MarkdownSection`
- **Add**: Capability registry registration for parser, updater
- **Add**: `py.typed` marker

**Commit Point**: After all markdown-utils tests pass

---

### Chunk 5: App Session Management

**Purpose**: Unified state management for both workflow phases
**Why Fifth**: Needed by all app workflows
**Estimated**: 3-4 hours, ~300 LOC

#### Files to Create:

**amplifier-app-blog-creator/src/amplifier_app_blog_creator/session.py**
- **Source**: Consolidate from:
  - `scenarios/blog_writer/state.py` (215 LOC)
  - `scenarios/article_illustrator/state.py` (244 LOC)
- **Current**: Two separate state management systems
- **Changes Required**:
  - Create: Unified `SessionState` with fields for both phases
    ```python
    @dataclass
    class SessionState:
        # Content phase
        stage: str
        iteration: int
        current_draft: str
        style_profile: dict
        source_review: dict
        style_review: dict
        user_feedback: list

        # Illustration phase
        illustration_points: list
        prompts: list
        images: list
        images_generated: int
        total_cost: float

        # Common
        session_id: str
        created_at: str
        max_iterations: int
    ```
  - Create: `SessionManager` class
    - `save()`, `load()`, `mark_complete()` methods
    - JSON checkpoint after every expensive operation
    - Session directory creation with timestamp
  - Add: `.expanduser()` for all path handling
  - Remove: App-specific logic (stays in workflow files)
- **Dependencies**: None (pathlib, json, dataclasses)
- **Tests**: `tests/test_session.py` - Save/load, resume, state transitions

**Commit Point**: After session management tests pass

---

### Chunk 6: App Content Phase (Blog Writer Workflow)

**Purpose**: Content creation workflow using modules
**Why Sixth**: Depends on session + modules
**Estimated**: 6-8 hours, ~1,200 LOC

#### Files to Migrate:

**1. amplifier-app-blog-creator/src/amplifier_app_blog_creator/content_phase.py**
- **Source**: `scenarios/blog_writer/main.py` (BlogPostPipeline class, 452 LOC)
- **Current**: Orchestrates style extraction → draft → reviews → feedback loop
- **Changes Required**:
  - Extract: `BlogPostPipeline` → `ContentPhase` class
  - Update: Import from modules instead of local:
    ```python
    from amplifier_module_style_extraction import StyleExtractor
    ```
  - Add: Capability registry usage:
    ```python
    extractor = coordinator.get_capability("style_extraction.analyzer")
    if not extractor:
        extractor = StyleExtractor()  # Fallback
    ```
  - Update: Use unified SessionManager
  - Keep: Review loop logic, iteration management
  - Remove: CLI code (moves to main.py)
- **Dependencies**: session.py, reviewers/, feedback.py, writer.py
- **Tests**: `tests/test_content_phase.py` - Full workflow, review loops

**2. amplifier-app-blog-creator/src/amplifier_app_blog_creator/writer.py**
- **Source**: `scenarios/blog_writer/blog_writer/core.py` (240 LOC)
- **Current**: `BlogWriter` class
- **Changes Required**:
  - Keep: Initial draft and revision logic
  - Update: Use StyleProfile from module
  - Keep: ClaudeSession integration
  - Add: Better error messages
- **Dependencies**: amplifier_module_style_extraction
- **Tests**: `tests/test_writer.py` - Draft generation, revision

**3. amplifier-app-blog-creator/src/amplifier_app_blog_creator/reviewers/source_reviewer.py**
- **Source**: `scenarios/blog_writer/source_reviewer/core.py` (216 LOC)
- **Current**: `SourceReviewer` class
- **Changes Required**:
  - Keep: Review logic as-is (works well)
  - Update: Defensive parsing imports stay same
  - Add: Better structured output
- **Dependencies**: None (self-contained)
- **Tests**: `tests/test_reviewers.py` - Source accuracy checking

**4. amplifier-app-blog-creator/src/amplifier_app_blog_creator/reviewers/style_reviewer.py**
- **Source**: `scenarios/blog_writer/style_reviewer/core.py` (234 LOC)
- **Current**: `StyleReviewer` class
- **Changes Required**:
  - Keep: Review logic as-is
  - Update: Use StyleProfile from module
- **Dependencies**: amplifier_module_style_extraction (StyleProfile)
- **Tests**: `tests/test_reviewers.py` - Style consistency checking

**5. amplifier-app-blog-creator/src/amplifier_app_blog_creator/feedback.py**
- **Source**: `scenarios/blog_writer/user_feedback/core.py` (247 LOC)
- **Current**: `UserFeedbackHandler` class
- **Changes Required**:
  - Keep: Bracket comment parsing, user interaction
  - Update: Path handling with .expanduser()
  - Simplify: Remove unnecessary complexity
- **Dependencies**: None
- **Tests**: `tests/test_feedback.py` - Comment parsing, user input

**Commit Point**: After content phase tests pass

---

### Chunk 7: App Illustration Phase

**Purpose**: Image generation workflow using modules
**Why Seventh**: Depends on session + image module
**Estimated**: 5-6 hours, ~600 LOC

#### Files to Migrate:

**1. amplifier-app-blog-creator/src/amplifier_app_blog_creator/illustration_phase.py**
- **Source**: Consolidate from:
  - `scenarios/article_illustrator/main.py` (ArticleIllustratorPipeline, 365 LOC)
  - `scenarios/article_illustrator/prompt_generation/core.py` (313 LOC)
- **Current**: Analyze → Prompts → Generate → Insert workflow
- **Changes Required**:
  - Create: `IllustrationPhase` class
  - Update: Import from modules:
    ```python
    from amplifier_module_image_generation import ImageGenerator
    from amplifier_module_markdown_utils import MarkdownImageUpdater
    ```
  - Add: Capability registry usage
  - Consolidate: Prompt generation into this file (app-specific policy)
  - Update: Use unified SessionManager
  - Remove: Separate session management (use unified)
  - Keep: Multi-API support, cost limiting, progress saving
- **Dependencies**: session.py, amplifier_module_image_generation, amplifier_module_markdown_utils
- **Tests**: `tests/test_illustration_phase.py` - Full workflow

**2. amplifier-app-blog-creator/src/amplifier_app_blog_creator/prompts.py** (Optional)
- **Source**: `scenarios/article_illustrator/prompt_generation/core.py` (313 LOC)
- **Decision**: Keep inline in illustration_phase.py or extract?
- **Recommendation**: Extract if >150 LOC, otherwise inline
- **Dependencies**: amplifier_module_markdown_utils (for content analysis)

**Commit Point**: After illustration phase tests pass

---

### Chunk 8: Unified App CLI

**Purpose**: Single entry point combining both workflows
**Why Eighth**: Depends on both content and illustration phases
**Estimated**: 3-4 hours, ~450 LOC

#### Files to Create:

**1. amplifier-app-blog-creator/src/amplifier_app_blog_creator/main.py**
- **Source**: Consolidate from:
  - `scenarios/blog_writer/main.py` (CLI + orchestration, 452 LOC)
  - `scenarios/article_illustrator/main.py` (CLI, 365 LOC)
- **Current**: Two separate CLIs
- **Changes Required**:
  - Create: Unified CLI with click
    ```python
    @click.command()
    @click.option("--idea", required=True)
    @click.option("--writings-dir", required=True)
    @click.option("--illustrate", is_flag=True)
    @click.option("--style", help="Image style")
    @click.option("--resume", is_flag=True)
    ```
  - Create: Unified orchestration:
    ```python
    # Phase 1: Content
    content_phase = ContentPhase(session)
    await content_phase.run(idea, writings_dir)

    # Phase 2: Illustration (optional)
    if illustrate:
        illustration_phase = IllustrationPhase(session)
        await illustration_phase.run(style_params)
    ```
  - Add: Session directory setup with timestamp
  - Add: Proper logging and progress display
  - Remove: Duplicate CLI options (consolidate)
- **Dependencies**: content_phase.py, illustration_phase.py, session.py
- **Tests**: `tests/test_main.py` - CLI argument parsing, workflow orchestration

**2. amplifier-app-blog-creator/src/amplifier_app_blog_creator/__main__.py**
- **Source**: New, based on both __main__.py files
- **Simple**: Just calls main()
- **Tests**: Entry point test

**3. amplifier-app-blog-creator/src/amplifier_app_blog_creator/__init__.py**
- **New File**
- **Exports**: Main entry point
- **Tests**: Package import test

**Commit Point**: After CLI tests pass and manual smoke test works

---

### Chunk 9: Integration Tests

**Purpose**: Verify full workflows end-to-end
**Why Ninth**: All components must exist first
**Estimated**: 3-4 hours

#### Tests to Create:

**1. Module Integration Tests**
- `tests/integration/test_modules_standalone.py` - Each module works independently
- `tests/integration/test_modules_cooperative.py` - Modules work via capability registry

**2. App Integration Tests**
- `tests/integration/test_content_workflow.py` - Full content phase
- `tests/integration/test_illustration_workflow.py` - Full illustration phase
- `tests/integration/test_unified_workflow.py` - Both phases together

**3. Installation Tests**
- `tests/integration/test_git_sources.py` - Modules install from git
- `tests/integration/test_uvx_execution.py` - App runs via uvx

**Commit Point**: After all integration tests pass

---

## Detailed File Mapping

### Module 1: image-generation

| Source | Target | LOC | Changes |
|--------|--------|-----|---------|
| article_illustrator/image_generation/clients.py | clients.py | 389 | Add .expanduser(), protocol compliance |
| article_illustrator/image_generation/core.py | generator.py | 181 | Add capability registry, simplify API |
| article_illustrator/models.py (partial) | models.py | 80 | Extract image models only |
| article_illustrator/image_generation/__init__.py | __init__.py | 10 | Update exports |

**Total**: ~660 LOC

### Module 2: style-extraction

| Source | Target | LOC | Changes |
|--------|--------|-----|---------|
| blog_writer/style_extractor/core.py | extractor.py | 188 | Add capability registry, .expanduser() |
| (extracted from above) | models.py | 50 | StyleProfile with to_prompt_text() |
| blog_writer/style_extractor/__init__.py | __init__.py | 10 | Update exports |

**Total**: ~248 LOC

### Module 3: markdown-utils

| Source | Target | LOC | Changes |
|--------|--------|-----|---------|
| article_illustrator/markdown_update/core.py | updater.py | 132 | Generalize beyond images |
| article_illustrator/content_analysis/core.py | parser.py | 160 | Extract parsing, separate from analysis |
| blog_writer/state.py (partial) | metadata.py | 30 | Extract title/slug functions |
| (new) | models.py | 50 | MarkdownDocument, MarkdownSection |
| (new) | __init__.py | 20 | Exports and capability registry |

**Total**: ~392 LOC

### App: blog-creator

| Source | Target | LOC | Changes |
|--------|--------|-----|---------|
| blog_writer/main.py | content_phase.py | 452 | Extract pipeline, use modules |
| article_illustrator/main.py | illustration_phase.py | 365 | Extract pipeline, use modules |
| blog_writer/blog_writer/core.py | writer.py | 240 | Use modules, capability registry |
| article_illustrator/prompt_generation/core.py | prompts.py or inline | 313 | App-specific prompt logic |
| blog_writer/source_reviewer/core.py | reviewers/source_reviewer.py | 216 | Direct copy, minimal changes |
| blog_writer/style_reviewer/core.py | reviewers/style_reviewer.py | 234 | Use StyleProfile from module |
| blog_writer/user_feedback/core.py | feedback.py | 247 | Direct copy, path expansion |
| blog_writer/state.py + article_illustrator/state.py | session.py | 459 | Consolidate, unify structure |
| (new) | main.py | 200 | Unified CLI |
| (new) | __init__.py + __main__.py | 20 | Package setup |

**Total**: ~2,746 LOC

---

## Dependencies Between Chunks

```
Chunk 1 (Models/Protocols)
  ↓
  ├─→ Chunk 2 (image-generation) ──┐
  ├─→ Chunk 3 (style-extraction) ───┼→ Chunk 5 (Session) ──┐
  └─→ Chunk 4 (markdown-utils) ─────┘                      │
                                                            ↓
                                                    Chunk 6 (Content Phase) ──┐
                                                            ↓                 │
                                                    Chunk 7 (Illustration) ───┼→ Chunk 8 (CLI)
                                                                              │
                                                                              ↓
                                                                        Chunk 9 (Integration Tests)
```

**Sequencing**: Must be sequential due to dependencies. Cannot parallelize.

---

## Implementation Approach

### Per-Module Strategy

**For each module** (Chunks 2-4):

1. Create directory structure:
   ```bash
   mkdir -p src/amplifier_module_{name}/
   mkdir -p tests/
   ```

2. Migrate code files one at a time:
   - Read source file completely
   - Update imports (microsoft core, robotdad modules)
   - Add capability registry code
   - Add .expanduser() to paths
   - Create in target location
   - Write unit tests

3. Create __init__.py with clean exports

4. Test standalone: `uv sync && uv run pytest`

5. Commit when tests pass

### For App (Chunks 5-8):

1. Create session management first (foundation)

2. Migrate content phase (blog_writer workflow)

3. Migrate illustration phase (article_illustrator workflow)

4. Create unified CLI

5. Test each phase independently

6. Test combined workflow

7. Commit when manual acceptance works

---

## Critical Code Patterns to Apply

### Pattern 1: Path Expansion (MANDATORY)

```python
# OLD - scenarios/ code
data_dir = Path(config.get("data_dir", "~/.data"))

# NEW - amplifier-dev code
data_dir = Path(config.get("data_dir", "~/.data")).expanduser()
```

**Apply to**: ALL paths from config, CLI args, or user input

### Pattern 2: Capability Registry

```python
# In module __init__ or class __init__
if coordinator:
    coordinator.register_capability("module.capability_name", object)

# In consuming code
obj = coordinator.get_capability("module.capability_name")
if not obj:
    from amplifier_module_name import Class
    obj = Class()  # Standalone fallback
```

**Apply to**: All modules (register), app (consume)

### Pattern 3: Git Source Imports

```python
# OLD - scenarios/ code (local imports)
from .style_extractor import StyleExtractor
from ..models import ImagePrompt

# NEW - module imports
from amplifier_module_style_extraction import StyleExtractor
from amplifier_module_image_generation.models import ImagePrompt
```

**Apply to**: All cross-module imports

### Pattern 4: Checkpoint Pattern

```python
# After every expensive operation
async def expensive_operation():
    result = await llm_call()  # Expensive

    # Save immediately
    state.result = result
    session_manager.save()  # ← Critical

    return result
```

**Apply to**: LLM calls, image generation, any >10 second operation

---

## Testing Strategy

### Unit Tests (Per Module/File)

**Coverage Goal**: 70%+ for business logic

**Module 1: image-generation**
- `tests/test_clients.py`: Each API client (mock API calls)
- `tests/test_generator.py`: Orchestration, fallback, cost tracking
- `tests/test_models.py`: Data validation

**Module 2: style-extraction**
- `tests/test_extractor.py`: Extraction logic, fallbacks
- `tests/test_models.py`: StyleProfile validation, to_prompt_text()

**Module 3: markdown-utils**
- `tests/test_metadata.py`: Title extraction, slugify edge cases
- `tests/test_parser.py`: Structure parsing
- `tests/test_updater.py`: Image insertion, placement strategies

**App: blog-creator**
- `tests/test_session.py`: State management, save/load
- `tests/test_content_phase.py`: Content workflow
- `tests/test_illustration_phase.py`: Illustration workflow
- `tests/test_writer.py`: Draft generation
- `tests/test_reviewers.py`: Review logic
- `tests/test_feedback.py`: User feedback parsing
- `tests/test_main.py`: CLI and orchestration

### Integration Tests

**Module Integration**:
- Standalone operation (no capability registry)
- Cooperative operation (with capability registry)
- Clean install from git sources

**App Integration**:
- Full content workflow (idea → approved post)
- Full illustration workflow (content → illustrated)
- Resume after interruption
- Error handling (missing API keys, LLM failures)

### Manual Acceptance Tests

**Test Scenarios**:

1. **Content Only**:
   ```bash
   uvx --from git+https://github.com/robotdad/amplifier-dev#subdirectory=amplifier-app-blog-creator \
     blog-creator --idea test_idea.md --writings-dir ~/test_writings/
   ```
   - Verify: Style extracted, draft generated, reviews work, feedback loop
   - Verify: Output saved with slug-based filename

2. **With Illustrations**:
   ```bash
   uvx ... blog-creator --idea test.md --writings-dir ~/writings/ \
     --illustrate --style "minimalist"
   ```
   - Verify: Content phase completes
   - Verify: Images generated and inserted
   - Verify: Final output is illustrated markdown

3. **Resume**:
   - Run test 1, interrupt mid-workflow (Ctrl+C)
   - Resume with `--resume` flag
   - Verify: Continues from checkpoint

4. **Error Handling**:
   - Test with missing API keys
   - Test with no writing samples
   - Test with empty idea file
   - Verify: Graceful errors, helpful messages

---

## Agent Orchestration Plan

### Primary Agent: modular-builder

For each chunk:
```
Task modular-builder: "Implement Chunk N according to code_plan.md

Files to create/migrate:
- [list files]

Follow specifications from:
- amplifier-module-{name}/README.md (API contract)
- code_plan.md (migration details)

Critical patterns:
- Add .expanduser() to all config paths
- Add capability registry registration
- Use git source imports

Test before marking complete.
"
```

### Support Agents

**bug-hunter** (when issues arise):
```
Task bug-hunter: "Debug [specific issue] in [module/file]"
```

**test-coverage** (per chunk):
```
Task test-coverage: "Suggest comprehensive tests for Chunk N"
```

### Sequential Execution

Execute chunks sequentially (dependencies):
- Chunk 1 → tests pass → commit
- Chunk 2 → tests pass → commit
- ... continue through Chunk 9

**Why sequential**: Each chunk depends on previous, parallel would cause conflicts

---

## Philosophy Compliance

### Ruthless Simplicity ✅

**Keeping Simple**:
- Direct imports from modules
- Simple orchestration (no complex state machines)
- Checkpoint pattern (save after expensive ops, that's it)
- Minimal abstraction (classes only when state needed)

**Avoiding Complexity**:
- NOT building: Complex retry frameworks
- NOT building: Advanced caching systems
- NOT building: Over-abstracted interfaces
- NOT building: Speculative features

### Modular Design ✅

**Bricks (Self-Contained)**:
- image-generation: Complete image generation capability
- style-extraction: Complete style analysis
- markdown-utils: Complete markdown processing
- blog-creator: Composes modules into workflow

**Studs (Stable Interfaces)**:
```python
# These contracts allow module regeneration
ImageGenerator.generate(...) -> ImageResult
StyleExtractor.extract_style(...) -> StyleProfile
MarkdownParser.parse(...) -> MarkdownDocument
```

**Regeneratable**: Each module can be rebuilt from:
- README.md (API specification)
- HOW_THIS_MODULE_WAS_MADE.md (design rationale)
- This code plan (migration details)

---

## Commit Strategy

### Module Commits (3 commits, one per module)

**Commit 1: image-generation**
```
feat: Implement image-generation module

Multi-provider image generation with DALL-E, Imagen, GPT-Image-1.

- ImageGenerator orchestrator with automatic fallback
- Three API clients with unified protocol
- Cost tracking and budget limits
- Capability registry integration

Tests: Unit tests for all components
Migrated from: scenarios/article_illustrator/image_generation/
```

**Commit 2: style-extraction**
```
feat: Implement style-extraction module

LLM-powered writing style analysis from samples.

- StyleExtractor with defensive parsing
- StyleProfile Pydantic model
- Capability registry integration
- Graceful fallback to defaults

Tests: Unit tests for extraction and models
Migrated from: scenarios/blog_writer/style_extractor/
```

**Commit 3: markdown-utils**
```
feat: Implement markdown-utils module

Markdown parsing, injection, and metadata extraction.

- MarkdownParser for structure analysis
- MarkdownImageUpdater for content injection
- Title extraction and slugification utilities
- Capability registry integration

Tests: Unit tests for all utilities
Consolidated from: blog_writer + article_illustrator
```

### App Commits (4 commits, incremental workflow)

**Commit 4: Session management**
```
feat(app): Add unified session management

Consolidated state management for both workflow phases.

- SessionState with content + illustration fields
- SessionManager with checkpoint pattern
- Resume capability
- Path expansion throughout

Tests: State persistence and resume
Consolidated from: blog_writer/state.py + article_illustrator/state.py
```

**Commit 5: Content phase**
```
feat(app): Implement content creation workflow

Blog writing with style matching and review cycles.

- ContentPhase orchestrator
- BlogWriter with style integration
- Source and style reviewers
- User feedback handling
- Uses style-extraction module

Tests: Content workflow end-to-end
Migrated from: scenarios/blog_writer/
```

**Commit 6: Illustration phase**
```
feat(app): Implement illustration workflow

AI-powered image generation and markdown integration.

- IllustrationPhase orchestrator
- Prompt generation
- Uses image-generation and markdown-utils modules
- Cost limiting and progress saving

Tests: Illustration workflow end-to-end
Migrated from: scenarios/article_illustrator/
```

**Commit 7: Unified CLI**
```
feat(app): Add unified CLI interface

Single command for complete blog creation workflow.

- Unified CLI with --illustrate flag
- Sequential phase orchestration
- Session management integration
- uvx-compatible entry point

Tests: CLI and full integration
Combines: blog_writer + article_illustrator
```

**Commit 8: Integration tests**
```
test: Add integration test suite

End-to-end tests for modules and app.

- Module standalone and cooperative tests
- Full workflow tests
- Git source installation tests
- uvx execution tests
```

---

## Risk Assessment

### High Risk Changes

**Risk 1: Consolidating State Management**
- **What**: Two different state systems → one unified
- **Mitigation**: Map all fields carefully, test resume thoroughly
- **Fallback**: Keep separate if consolidation breaks

**Risk 2: Import Changes**
- **What**: All imports change from local to module imports
- **Mitigation**: Systematic search-replace, verify with tests
- **Fallback**: None - this is fundamental to migration

**Risk 3: Capability Registry Integration**
- **What**: New pattern, not in original code
- **Mitigation**: Dual-mode (registry + standalone), test both paths
- **Fallback**: Skip registry, just use direct imports

### Medium Risk Changes

**Risk 4: Path Expansion**
- **What**: Adding .expanduser() everywhere
- **Mitigation**: Systematic review, test with ~ paths
- **Impact**: Medium - breaks if missed

**Risk 5: API Surface Simplification**
- **What**: Changing some return types for cleaner APIs
- **Mitigation**: Follow api-contract-designer specs exactly
- **Impact**: Low - internal to new modules

### Dependencies to Watch

**External Libraries**:
- `openai>=1.0.0` - Stable
- `google-genai>=1.0.0` - Check latest version
- `pydantic>=2.0.0` - Stable
- `click>=8.0.0` - Stable
- `aiohttp>=3.9.0` - Stable

**Internal Dependencies**:
- `microsoft/amplifier-core` - Pin to commit initially, test with main regularly
- `amplifier.ccsdk_toolkit` - Unchanged, should work as-is
- `amplifier.utils.logger` - Unchanged

---

## Success Criteria

### Per Module

Code is ready when:
- [ ] All documented APIs implemented
- [ ] Unit tests pass (>70% coverage)
- [ ] Capability registry integration works
- [ ] Standalone mode works (without registry)
- [ ] Can install from git source: `uv pip install git+https://...`
- [ ] Examples in README work when copy-pasted

### For App

Code is ready when:
- [ ] Content phase works end-to-end
- [ ] Illustration phase works end-to-end
- [ ] Combined workflow works
- [ ] Resume from checkpoint works
- [ ] uvx execution works: `uvx --from git+https://... blog-creator ...`
- [ ] Error handling is graceful
- [ ] Manual acceptance tests all pass

### Overall Success

- [ ] All tests passing (`make check`, `uv run pytest`)
- [ ] No regressions in functionality
- [ ] Code follows IMPLEMENTATION_PHILOSOPHY
- [ ] Modules follow MODULAR_DESIGN_PHILOSOPHY
- [ ] Git sources work for all dependencies
- [ ] Documentation matches code exactly
- [ ] Ready for user testing

---

## Estimated Effort

**By Chunk**:
- Chunk 1 (Models): 2-3 hours
- Chunk 2 (image-generation): 4-6 hours
- Chunk 3 (style-extraction): 3-4 hours
- Chunk 4 (markdown-utils): 4-5 hours
- Chunk 5 (Session): 3-4 hours
- Chunk 6 (Content Phase): 6-8 hours
- Chunk 7 (Illustration): 5-6 hours
- Chunk 8 (CLI): 3-4 hours
- Chunk 9 (Integration): 3-4 hours

**Total**: 33-47 hours (aligns with Phase 1 estimate of 33-50 hours)

**Lines of Code**:
- Module code: ~1,300 LOC
- App code: ~2,750 LOC
- Tests: ~1,000 LOC
- **Total**: ~5,050 LOC (includes tests)

---

## Next Steps

### Immediate

✅ **This Plan Complete**
- Detailed file-by-file migration map
- Clear chunk boundaries and dependencies
- Test strategy defined
- Agent orchestration planned

➡️ **User Approval Required**

Please review this code plan:
1. Does the chunk breakdown make sense?
2. Are there missing considerations?
3. Should we parallelize any chunks?
4. Is the test strategy sufficient?

➡️ **After Approval**: `/ddd:4-code`

---

**Plan Status**: Complete - Awaiting User Approval
**Next Action**: Review and approve to proceed to implementation
**File**: `ai_working/ddd/code_plan.md`
