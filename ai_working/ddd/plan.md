# DDD Plan: Blog Creator Migration to Amplifier-Dev

**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft - Awaiting Approval

---

## Problem Statement

**Current State**: Two valuable scenario tools (blog_writer and article_illustrator) exist as standalone applications in `scenarios/` with ~3,800 lines of production-tested code. They solve real problems but are:
- Not reusable by other applications
- Don't follow amplifier-dev patterns (git sources, capability registry, module structure)
- Duplicate code (markdown processing, state management)
- Missed opportunity to contribute to ecosystem

**User Impact**:
- Content creators: No unified workflow (run two separate commands)
- Developers: Can't reuse image generation or style extraction in their apps
- Community: No reference implementation for building amplifier modules

**What Success Looks Like**:
- Content creators: One command generates complete illustrated blog posts
- Developers: Can `import amplifier_module_image_generation` in any app
- Community: Complete exemplar for module development and migration patterns

---

## Proposed Solution

### High-Level Approach

Extract three reusable modules and create one unified app, following amplifier-dev ecosystem patterns:

```
Reusable Modules (robotdad/amplifier-dev):
├─ amplifier-module-image-generation
│  └─ Multi-API orchestration (DALL-E, Imagen, GPT-Image-1)
├─ amplifier-module-style-extraction
│  └─ Writing style analysis from samples
└─ amplifier-module-markdown-utils
   └─ Parsing, injection, metadata extraction

Unified App (robotdad/amplifier-dev):
└─ amplifier-app-blog-creator
   ├─ Phase 1: Content creation (blog_writer workflow)
   ├─ Phase 2: Optional illustration (article_illustrator workflow)
   └─ Uses all three modules via git sources
```

**Key Decisions**:
- ✅ Unified app (not separate tools) - Workflow dependency is strong
- ✅ 3 modules (validated by api-contract-designer with clean interfaces)
- ✅ Git sources only (no path dependencies) - Enables frictionless sharing
- ✅ Capability registry pattern - Modules cooperate when present, work standalone
- ✅ Microsoft core dependency - Don't modify microsoft repos, depend on them

---

## Alternatives Considered

### Alternative 1: Simplify to 1 Module (zen-architect's recommendation)
- Push markdown/images to amplifier-core as capabilities
- Only extract blog-style as module
- Wait for 3+ consumers before extracting more

**Pros**: Ruthlessly simple, less to maintain
**Cons**: Can't modify microsoft/amplifier-core, delays reusability
**Decision**: Not viable - we don't control microsoft repos

### Alternative 2: Keep Tools Separate
- Two apps: blog-writer + article-illustrator
- Each depends on shared modules

**Pros**: Simpler individual apps
**Cons**: Awkward workflow handoff, duplicate state management
**Decision**: Rejected - Unified workflow is better UX

### Alternative 3: Monolithic App (no modules)
- One app with all code vendored

**Pros**: Simplest migration
**Cons**: No reusability, misses ecosystem contribution opportunity
**Decision**: Rejected - Doesn't align with amplifier-dev philosophy

---

## Architecture & Design

### Key Interfaces ("Studs")

From api-contract-designer agent analysis:

**1. Image Generation Module**
```python
class ImageGenerator:
    async def generate(
        self,
        prompt: str,
        output_path: Path,
        *,
        preferred_api: str | None = None,
        params: dict | None = None,
    ) -> ImageResult

@dataclass
class ImageResult:
    success: bool
    api_used: str
    cost: float
    local_path: Path
    error: str | None = None
```

**2. Style Extraction Module**
```python
class StyleExtractor:
    async def extract_style(self, samples_dir: Path) -> StyleProfile

class StyleProfile(BaseModel):
    tone: str
    vocabulary_level: str
    sentence_structure: str
    paragraph_length: str
    voice: str
    common_phrases: list[str]
    writing_patterns: list[str]
    examples: list[str]

    def to_prompt_text(self) -> str
```

**3. Markdown Utils Module**
```python
# Functions for simple operations
def extract_title(content: str) -> str | None
def slugify(text: str) -> str

# Classes for complex operations
class MarkdownParser:
    def parse(self, content: str) -> MarkdownDocument

class MarkdownImageUpdater:
    def insert_image(
        self,
        content: str,
        image_path: str,
        alt_text: str,
        *,
        placement: Literal["before_section", "after_section", "at_line"] = "at_line"
    ) -> str
```

### Module Boundaries

**Clear Separation of Concerns**:

| Module | Responsibility | Does NOT Handle |
|--------|---------------|-----------------|
| image-generation | Multi-API orchestration, cost tracking, provider selection | Image prompt creation, content analysis |
| style-extraction | Writing style analysis, LLM-driven extraction | Content generation, review logic |
| markdown-utils | Parsing, metadata, image insertion | Content analysis, LLM operations |
| blog-creator (app) | Workflow orchestration, user interaction, reviews | Low-level module operations |

**Dependencies**:
```
amplifier-module-image-generation
└─ Depends on: microsoft/amplifier-core (git source)

amplifier-module-style-extraction
└─ Depends on: microsoft/amplifier-core (git source)

amplifier-module-markdown-utils
└─ Depends on: microsoft/amplifier-core (git source)

amplifier-app-blog-creator
├─ Depends on: microsoft/amplifier-core (git source)
├─ Depends on: robotdad/amplifier-module-image-generation (git source)
├─ Depends on: robotdad/amplifier-module-style-extraction (git source)
└─ Depends on: robotdad/amplifier-module-markdown-utils (git source)
```

### Data Models

**Image Generation**:
- `ImageResult`: success, api_used, cost, local_path, error
- `ImageProviderProtocol`: Interface for adding new APIs

**Style Extraction**:
- `StyleProfile` (Pydantic): tone, vocabulary, sentence_structure, paragraph_length, voice, phrases, patterns, examples

**Markdown Utils**:
- `MarkdownDocument`: title, sections, raw_content
- `MarkdownSection`: title, level, line_number, content

**Blog Creator App**:
- `SessionState`: stage, iteration, current_draft, style_profile, reviews, user_feedback
- `IdeaInput`: path, content, additional_instructions
- `IllustrationConfig`: max_images, style_params, cost_limit, apis

---

## Files to Change

### Non-Code Files (Phase 2: Documentation)

#### Module 1: image-generation

- [ ] `amplifier-module-image-generation/README.md` - Create from scratch
- [ ] `amplifier-module-image-generation/pyproject.toml` - Create with git sources
- [ ] `amplifier-module-image-generation/HOW_THIS_MODULE_WAS_MADE.md` - Migration story
- [ ] `amplifier-module-image-generation/examples/basic_usage.py` - Usage examples

#### Module 2: style-extraction

- [ ] `amplifier-module-style-extraction/README.md` - Create from scratch
- [ ] `amplifier-module-style-extraction/pyproject.toml` - Create with git sources
- [ ] `amplifier-module-style-extraction/HOW_THIS_MODULE_WAS_MADE.md` - Migration story
- [ ] `amplifier-module-style-extraction/examples/basic_usage.py` - Usage examples

#### Module 3: markdown-utils

- [ ] `amplifier-module-markdown-utils/README.md` - Create from scratch
- [ ] `amplifier-module-markdown-utils/pyproject.toml` - Create with git sources
- [ ] `amplifier-module-markdown-utils/HOW_THIS_MODULE_WAS_MADE.md` - Migration story
- [ ] `amplifier-module-markdown-utils/examples/basic_usage.py` - Usage examples

#### App: blog-creator

- [ ] `amplifier-app-blog-creator/README.md` - Create from scratch
- [ ] `amplifier-app-blog-creator/pyproject.toml` - Create with git sources
- [ ] `amplifier-app-blog-creator/HOW_I_BUILT_THIS.md` - Creation story
- [ ] `amplifier-app-blog-creator/MIGRATION_NOTES.md` - From scenarios/ lessons
- [ ] `amplifier-app-blog-creator/.amplifier/profiles/blog-creator.md` - Profile with git sources

#### Documentation Updates

- [ ] `ai_working/SCENARIO_MIGRATION_GUIDE.md` - Add lessons learned
- [ ] `amplifier-dev/AGENTS.md` - Update if patterns change
- [ ] `scenarios/blog_writer/README.md` - Add deprecation notice pointing to new location
- [ ] `scenarios/article_illustrator/README.md` - Add deprecation notice pointing to new location

### Code Files (Phase 4: Implementation)

#### Module 1: image-generation

Source files to migrate from `scenarios/article_illustrator/`:
- [ ] `image_generation/core.py` → `src/amplifier_module_image_generation/generator.py`
- [ ] `image_generation/clients.py` → `src/amplifier_module_image_generation/clients.py`
- [ ] `image_generation/__init__.py` → `src/amplifier_module_image_generation/__init__.py`
- [ ] `models.py` (image-related) → `src/amplifier_module_image_generation/models.py`

New files to create:
- [ ] `src/amplifier_module_image_generation/py.typed` - Type marker
- [ ] `tests/test_generator.py` - Unit tests
- [ ] `tests/test_clients.py` - Client tests

**Key Changes Required**:
- Update imports: `from amplifier.utils.logger` → stay same (microsoft core)
- Add `.expanduser()` to all config paths
- Register capabilities: `coordinator.register_capability("image_generation.orchestrator", self)`
- Add fallback for standalone mode

#### Module 2: style-extraction

Source files to migrate from `scenarios/blog_writer/`:
- [ ] `style_extractor/core.py` → `src/amplifier_module_style_extraction/extractor.py`
- [ ] `style_extractor/__init__.py` → `src/amplifier_module_style_extraction/__init__.py`

New files to create:
- [ ] `src/amplifier_module_style_extraction/models.py` - StyleProfile model
- [ ] `src/amplifier_module_style_extraction/py.typed` - Type marker
- [ ] `tests/test_extractor.py` - Unit tests

**Key Changes Required**:
- Keep Pydantic models
- Add capability registration
- Add `.expanduser()` for paths

#### Module 3: markdown-utils

Source files to migrate from both tools:
- [ ] `article_illustrator/markdown_update/core.py` → `src/amplifier_module_markdown_utils/updater.py`
- [ ] `article_illustrator/content_analysis/core.py` (markdown parsing) → `src/amplifier_module_markdown_utils/parser.py`
- [ ] `blog_writer/state.py` (extract_title, slugify) → `src/amplifier_module_markdown_utils/metadata.py`

New files to create:
- [ ] `src/amplifier_module_markdown_utils/__init__.py` - Public API
- [ ] `src/amplifier_module_markdown_utils/models.py` - Data models
- [ ] `src/amplifier_module_markdown_utils/py.typed` - Type marker
- [ ] `tests/test_parser.py` - Parser tests
- [ ] `tests/test_updater.py` - Updater tests
- [ ] `tests/test_metadata.py` - Metadata tests

**Key Changes Required**:
- Consolidate from two sources
- Unified interface design
- Add capability registration

#### App: blog-creator

Source files to migrate and combine:
- [ ] `blog_writer/main.py` + `article_illustrator/main.py` → `src/amplifier_app_blog_creator/main.py`
- [ ] `blog_writer/blog_writer/core.py` → `src/amplifier_app_blog_creator/content_phase.py`
- [ ] `article_illustrator/prompt_generation/core.py` → `src/amplifier_app_blog_creator/illustration_phase.py`
- [ ] `blog_writer/source_reviewer/core.py` → `src/amplifier_app_blog_creator/reviewers/source_reviewer.py`
- [ ] `blog_writer/style_reviewer/core.py` → `src/amplifier_app_blog_creator/reviewers/style_reviewer.py`
- [ ] `blog_writer/user_feedback/core.py` → `src/amplifier_app_blog_creator/feedback.py`
- [ ] `blog_writer/state.py` + `article_illustrator/state.py` → `src/amplifier_app_blog_creator/session.py`

New files to create:
- [ ] `src/amplifier_app_blog_creator/__init__.py`
- [ ] `src/amplifier_app_blog_creator/__main__.py`
- [ ] `tests/test_content_phase.py`
- [ ] `tests/test_illustration_phase.py`
- [ ] `tests/test_session.py`

**Key Changes Required**:
- Unified CLI with `--skip-illustrations` flag
- Import from robotdad modules (not vendored code)
- Single session state spanning both phases
- Capability registry usage for modules

---

## Philosophy Alignment

### Ruthless Simplicity ✅

**Start Minimal**:
- Extract only proven patterns (3,800 LOC already tested in production)
- Don't add features during migration
- Module interfaces are minimal (1-2 public methods each)

**Avoid Future-Proofing**:
- Not building: Batch processing, advanced caching, provider routing logic
- Not adding: Hypothetical features, complex configuration systems
- Using: Simple dataclasses, direct function calls, minimal abstraction

**Question Everything**:
- Do we need 3 modules? YES - Clean boundaries validated by api-contract-designer
- Do we need unified app? YES - Workflow dependency is strong
- Do we need capability registry? YES - Follows integration-specialist patterns

**Clear Over Clever**:
- Direct imports, not dynamic loading
- Async where needed (network I/O), sync otherwise
- Explicit error handling, not swallowed exceptions

### Modular Design ✅

**Bricks (Self-Contained Modules)**:
- image-generation: Fully functional without other modules
- style-extraction: Fully functional without other modules
- markdown-utils: Fully functional without other modules

**Studs (Stable Interfaces)**:
```python
# These contracts allow regeneration without breaking consumers
ImageGenerator.generate() -> ImageResult
StyleExtractor.extract_style() -> StyleProfile
MarkdownParser.parse() -> MarkdownDocument
```

**Regeneratable from Spec**:
- Each module has comprehensive README as specification
- HOW_THIS_MODULE_WAS_MADE.md captures creation story
- Can rebuild entire module from docs

**Human Architects, AI Builds**:
- This DDD plan = architectural blueprint
- Agent feedback validates design
- Implementation phase follows specification exactly

### Integration Patterns ✅

**Git Sources (Not Path Dependencies)**:
```toml
[tool.uv.sources]
amplifier-core = {
    git = "https://github.com/microsoft/amplifier-dev",
    subdirectory = "amplifier-core",
    branch = "main"
}
```

**Capability Registry Pattern**:
```python
# Module registers
coordinator.register_capability("image_generation.orchestrator", self)

# App uses
generator = coordinator.get_capability("image_generation.orchestrator")
if not generator:
    from amplifier_module_image_generation import ImageGenerator
    generator = ImageGenerator()  # Standalone fallback
```

**Path Expansion (Critical)**:
```python
# ALWAYS use .expanduser()
data_dir = Path(config.get("data_dir", "~/.data")).expanduser()
```

---

## Test Strategy

### Unit Tests

**Per Module**:
- image-generation: Test each API client independently, orchestrator logic
- style-extraction: Test StyleProfile validation, extraction logic with mock LLM
- markdown-utils: Test parsers, updaters, metadata extractors with sample markdown

**Coverage Goal**: 70%+ for business logic

### Integration Tests

**Module Integration**:
- Test modules with real amplifier-core imports
- Verify capability registry cooperation
- Test standalone mode (no capability available)

**App Integration**:
- Full content phase workflow
- Full illustration phase workflow
- Combined workflow (content → images)
- State persistence and resume

### User Testing

**Manual Acceptance Tests**:
1. Create blog post from idea (content only)
2. Create blog post with illustrations (full workflow)
3. Interrupt and resume session
4. Use with different writing samples
5. Use with different image APIs (DALL-E, Imagen, GPT-Image-1)

**Success Criteria**:
- Generates blog post matching author's style
- Illustrates with contextually relevant images
- Can resume after interruption
- Handles errors gracefully (missing API keys, LLM failures)

---

## Implementation Approach

### Phase 2: Documentation (First - Critical for DDD)

**Order**: All docs BEFORE any code

1. **Module READMEs** (following file crawling pattern):
   - Create checklist of all 3 module READMEs
   - Process one at a time
   - Document: Purpose, Installation, Usage, API Reference, Examples
   - Include: HOW_THIS_MODULE_WAS_MADE.md for each

2. **App README and Documentation**:
   - amplifier-app-blog-creator/README.md
   - HOW_I_BUILT_THIS.md (creation story)
   - MIGRATION_NOTES.md (lessons from scenarios/)

3. **Profile with Git Sources**:
   - .amplifier/profiles/blog-creator.md
   - Markdown format with YAML frontmatter
   - Source fields for all robotdad modules

4. **Update Scenario Tool READMEs**:
   - Add deprecation notice
   - Point to new amplifier-dev locations

5. **Context Document Updates**:
   - ai_working/SCENARIO_MIGRATION_GUIDE.md (add lessons)
   - amplifier-dev/AGENTS.md (if patterns changed)

**Deliverable**: Complete documentation set approved before writing code

### Phase 3: Code Planning

**Create Implementation Checklist**:
- List all Python files to create/migrate
- Identify dependencies and import changes
- Plan test file structure
- Document tricky migration points

**Chunk the Work**:
- Module 1: image-generation (simplest, fewest dependencies)
- Module 2: style-extraction (medium complexity)
- Module 3: markdown-utils (consolidation from two sources)
- App: blog-creator (most complex, depends on all modules)

**Right-Size Check**:
- Can each module be implemented in <500 lines?
- Can app be implemented in <1000 lines?
- If no, split into smaller pieces

### Phase 4: Code Implementation

**Order of Implementation**:

1. **Module 1: image-generation** (~400 LOC)
   - Migrate clients.py with path expansion
   - Migrate core.py orchestrator
   - Add capability registration
   - Create tests
   - Verify clean install from git source

2. **Module 2: style-extraction** (~300 LOC)
   - Migrate extractor.py
   - Extract StyleProfile to models.py
   - Add capability registration
   - Create tests
   - Verify clean install

3. **Module 3: markdown-utils** (~400 LOC)
   - Create parser.py (from article_illustrator)
   - Create updater.py (from article_illustrator)
   - Create metadata.py (from blog_writer)
   - Unify interfaces
   - Create tests
   - Verify clean install

4. **App: blog-creator** (~2700 LOC)
   - Create session.py (unified state)
   - Create content_phase.py (blog_writer workflow)
   - Create illustration_phase.py (article_illustrator workflow)
   - Create reviewers/ (source, style)
   - Create feedback.py
   - Create main.py (unified CLI)
   - Create tests
   - Verify full workflow

**Per-File Pattern**:
- Read source file completely
- Update imports (microsoft core, robotdad modules)
- Add .expanduser() to paths
- Add capability registration
- Update tests
- Commit incrementally

### Phase 5: Testing & Verification

**Verification Steps**:
1. Clean venv test: `rm -rf .venv && uv sync`
2. Each module: `uv run pytest tests/`
3. App workflow tests: `uv run pytest tests/test_*.py`
4. Manual acceptance: Run actual blog creation
5. Resume test: Interrupt and continue
6. Profile test: Use via amplifier CLI

**Success Criteria**:
- All tests pass
- Clean install from git sources works
- Full workflow completes end-to-end
- Can interrupt and resume
- Examples in READMEs work when copy-pasted

---

## Success Criteria

### Technical Success

- [ ] All modules install cleanly via git sources
- [ ] All tests pass (unit + integration)
- [ ] Full blog creation workflow works end-to-end
- [ ] Can interrupt and resume sessions
- [ ] Capability registry cooperation works
- [ ] Standalone module mode works
- [ ] Profile-based usage works
- [ ] Zero path dependencies (all git sources)

### Quality Success

- [ ] Code follows IMPLEMENTATION_PHILOSOPHY (ruthless simplicity)
- [ ] Modules follow MODULAR_DESIGN_PHILOSOPHY (bricks and studs)
- [ ] Documentation is complete and accurate
- [ ] Examples work when copy-pasted
- [ ] Error messages are helpful
- [ ] No context poisoning (docs consistent)

### User Success

- [ ] Content creator creates illustrated blog post in one command
- [ ] Developer imports module and uses it successfully
- [ ] Community member reads HOW_THIS_MODULE_WAS_MADE and understands approach
- [ ] Migration guide updated with lessons learned

---

## Risks & Mitigations

### Risk 1: Dependency Version Conflicts

**Risk**: microsoft/amplifier-core changes incompatibly
**Likelihood**: Medium
**Impact**: High
**Mitigation**: Pin to specific commit initially, test with main regularly

### Risk 2: Module Boundaries Wrong

**Risk**: Need to refactor boundaries after implementation
**Likelihood**: Low (agent validation)
**Impact**: Medium
**Mitigation**: api-contract-designer validated interfaces, can adjust if needed

### Risk 3: GitHub Auth Issues

**Risk**: Private repos require auth, installation friction
**Likelihood**: High
**Impact**: Low
**Mitigation**: Document clearly in READMEs, consider public repos

### Risk 4: Context Poisoning During Migration

**Risk**: Stale scenario docs mislead future work
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**: Add deprecation notices immediately, update regularly

### Risk 5: Testing Coverage Gaps

**Risk**: Miss edge cases in migration
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**: Manual acceptance tests catch gaps, iterate

---

## Timeline Estimate

**Phase 2 (Documentation)**: 8-12 hours
- Module READMEs: 2-3 hours per module (6-9 hours)
- App documentation: 1-2 hours
- Profile creation: 30 min
- Context updates: 30 min

**Phase 3 (Code Planning)**: 1-2 hours
- Create checklists
- Identify tricky spots

**Phase 4 (Implementation)**: 20-30 hours
- Module 1 (image-generation): 4-6 hours
- Module 2 (style-extraction): 3-5 hours
- Module 3 (markdown-utils): 4-6 hours
- App (blog-creator): 8-12 hours
- Integration fixes: 1-3 hours

**Phase 5 (Testing)**: 4-6 hours
- Automated tests: 2-3 hours
- Manual acceptance: 2-3 hours

**Total**: 33-50 hours

---

## Next Steps

### Immediate (Phase 1 Complete)

✅ **This Plan**
- [ ] Review with user
- [ ] Get approval on architecture
- [ ] Confirm 3-module approach
- [ ] Confirm unified app approach

➡️ **Next**: `/ddd:2-docs` - Update ALL non-code files

### After Documentation Approval

➡️ **Then**: `/ddd:3-code-plan` - Detailed implementation checklist
➡️ **Then**: `/ddd:4-code` - Implement following specification
➡️ **Then**: `/ddd:5-finish` - Test, verify, cleanup

---

## Questions for User

Before proceeding to Phase 2:

1. **Architecture Approval**: Does the 3-module + unified app approach make sense?
2. **Scope Confirmation**: Is migration the right scope (no new features during migration)?
3. **Timeline Acceptable**: 33-50 hour estimate reasonable?
4. **Priority**: Implement modules in parallel or sequentially?
5. **Testing**: Manual acceptance sufficient or need automated integration tests?

---

**Plan Status**: Draft - Awaiting User Review

**Next Action**: Review this plan, provide feedback, approve to proceed to Phase 2

**File**: `ai_working/ddd/plan.md`
