# Parallel Explorer: Explore Alternative Scenario Tool Implementations

**Compare different approaches to building amplifier scenario tools by implementing them in parallel.**

## The Problem

You want to build an amplifier scenario tool, but:
- **Choosing an approach is hard** - Should it be simple or feature-rich? Which features matter most?
- **Serial exploration is slow** - Build one approach, test it, then maybe try another...
- **Theory vs reality** - What sounds good on paper may not work in practice
- **No empirical comparison** - Hard to compare approaches objectively without building them

## The Solution

Parallel Explorer creates multiple complete scenario tools (like blog_writer, article_illustrator) using different approaches simultaneously, so you can compare real implementations and choose the best fit.

## What It Generates

**Input**: A tool idea with requirements and 2-3 variant approaches

**Output**: Complete, working scenario tools at `scenarios/{tool}_{variant}/` including:
- Python package structure (`__init__.py`, `__main__.py`, `main.py`)
- CLI interface with click
- Core implementation modules
- Comprehensive documentation (README.md, HOW_TO_CREATE_YOUR_OWN.md)
- Following blog_writer/article_illustrator patterns

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Recommended Workflow: Using /explore-variants

**Step 1**: Start an interactive session to capture your idea:

```
/explore-variants
```

Claude Code will guide you through defining:
- Tool name and purpose
- Key requirements
- Common context (shared across variants)
- Variant approaches with their unique focuses

This creates `.data/parallel_explorer/{name}/context.json`

**Step 2**: Run the parallel exploration:

```bash
make parallel-explore NAME="your-tool-name"
```

The system loads your context and generates multiple complete scenario tools in parallel.

### Manual Workflow: Create context.json

For full control, create `.data/parallel_explorer/{name}/context.json` manually:

```json
{
  "experiment_name": "content-analyzer",
  "task": "Build a tool that analyzes content for readability and engagement",
  "tool_prefix": "analyze",
  "requirements": [
    "Accept markdown files as input",
    "Generate readability scores",
    "Identify engagement patterns",
    "Provide actionable feedback"
  ],
  "common_context": {
    "input_format": "Markdown files",
    "output_format": "JSON report with recommendations",
    "target_users": "Content creators and bloggers"
  },
  "variants": {
    "metrics-focused": {
      "description": "Quantitative analysis with readability metrics",
      "approach": "Calculate Flesch-Kincaid, sentiment scores, and engagement metrics. Provide numerical ratings and statistical analysis.",
      "cli_command": "analyze-metrics",
      "main_features": [
        "readability_scoring",
        "sentiment_analysis",
        "engagement_metrics"
      ],
      "focus_areas": [
        "statistical accuracy",
        "comprehensive metrics",
        "data visualization"
      ]
    },
    "narrative-focused": {
      "description": "Qualitative analysis of story structure and flow",
      "approach": "Analyze narrative arc, pacing, and emotional journey. Provide storytelling feedback and structural recommendations.",
      "cli_command": "analyze-narrative",
      "main_features": [
        "story_arc_analysis",
        "pacing_evaluation",
        "emotional_flow"
      ],
      "focus_areas": [
        "narrative structure",
        "reader engagement",
        "storytelling quality"
      ]
    }
  },
  "success_criteria": [
    "Provides actionable, specific feedback",
    "Identifies concrete improvement opportunities",
    "Output is clear and easy to understand"
  ]
}
```

Then run:
```bash
make parallel-explore NAME="content-analyzer"
```

## Understanding context.json Structure

### Required Fields

**`experiment_name`**: Used for directory and tool naming
- Example: `"meeting-summarizer"` → creates `meeting_summarizer_executive`, `meeting_summarizer_technical`

**`task`**: High-level description of what the tool should do
- Be specific and clear
- Example: `"Build a meeting notes summarizer tool that extracts decisions and actions"`

**`tool_prefix`**: Prefix for make commands (future use)
- Example: `"meeting"` → suggests `make meeting-exec`, `make meeting-tech`

**`requirements`**: List of specific capabilities the tool must have
- Be concrete and testable
- Example: `["Take markdown input", "Extract decisions", "Generate summary"]`

**`common_context`**: Information shared across all variants
- Input/output formats
- Target users
- Constraints or assumptions
- Example:
  ```json
  {
    "input_format": "Markdown file with meeting notes",
    "output_format": "Structured markdown summary",
    "target_audience": "Team members reviewing meeting outcomes"
  }
  ```

**`variants`**: Dictionary of approaches to explore (2-3 recommended)

Each variant needs:
- **`description`**: One-line summary of this approach
- **`approach`**: Detailed explanation of how this variant differs
- **`cli_command`**: Suggested command name
- **`main_features`**: List of 2-4 key features (guides module structure)
- **`focus_areas`**: What this variant prioritizes

Optional per variant:
- **`context`**: Additional variant-specific guidance
- **`constraints`**: Specific limitations for this variant

### Optional Fields

**`success_criteria`**: List of what makes a good implementation
- Helps guide the quality of generated tools
- Example: `["Clear output", "Accurate extraction", "Easy to use"]`

**`technical_requirements`**: Specific technical constraints
- Example: `["Python 3.11+", "Use click for CLI", "Async/await patterns"]`

## Complete Realistic Example

### Scenario: Build a Code Review Assistant

**Goal**: Create a tool that helps review pull requests, but explore two different approaches - one focused on code quality, one focused on architecture patterns.

**Step 1**: Create `.data/parallel_explorer/code-reviewer/context.json`:

```json
{
  "experiment_name": "code-reviewer",
  "task": "Build a code review assistant that analyzes pull requests and provides feedback",
  "tool_prefix": "review",
  "requirements": [
    "Accept git diff or file paths as input",
    "Analyze code for issues and improvements",
    "Generate structured feedback",
    "Prioritize findings by importance",
    "Provide specific, actionable recommendations"
  ],
  "common_context": {
    "input_format": "Git diff, file paths, or directory",
    "output_format": "Markdown report with prioritized findings",
    "target_users": "Developers reviewing or submitting PRs",
    "review_scope": "Focus on Python code in amplifier projects"
  },
  "variants": {
    "quality-focused": {
      "description": "Code quality reviewer emphasizing maintainability and best practices",
      "approach": "Analyze code for readability, naming conventions, complexity, test coverage, and maintainability. Prioritize issues that affect long-term code health. Flag technical debt and suggest refactorings.",
      "cli_command": "review-quality",
      "main_features": [
        "complexity_analysis",
        "naming_review",
        "test_coverage_check",
        "maintainability_scoring"
      ],
      "focus_areas": [
        "code readability",
        "maintainability",
        "best practices compliance",
        "technical debt identification"
      ],
      "context": "Best for teams prioritizing long-term maintainability over short-term velocity"
    },
    "architecture-focused": {
      "description": "Architecture reviewer emphasizing design patterns and system structure",
      "approach": "Analyze code for architectural patterns, modularity, dependency management, and design principles. Evaluate how changes fit into overall system design. Identify pattern violations or improvement opportunities.",
      "cli_command": "review-arch",
      "main_features": [
        "pattern_detection",
        "modularity_analysis",
        "dependency_review",
        "design_principles_check"
      ],
      "focus_areas": [
        "architectural consistency",
        "modularity",
        "design patterns",
        "system-level impacts"
      ],
      "context": "Best for teams with established architecture wanting to maintain design coherence"
    }
  },
  "success_criteria": [
    "Identifies real, actionable issues (not theoretical)",
    "Prioritizes findings by actual impact",
    "Feedback is specific with examples",
    "Recommendations are concrete and achievable",
    "Output helps developers improve code"
  ],
  "technical_requirements": [
    "Python 3.11+",
    "Use click for CLI interface",
    "Integrate with git for diff parsing",
    "Use CCSDK for AI-powered analysis"
  ]
}
```

**Step 2**: Run the exploration:

```bash
make parallel-explore NAME="code-reviewer"
```

**Step 3**: Review the results:

```bash
# Two complete scenario tools created
ls .data/parallel_explorer/code-reviewer/worktrees/quality-focused/scenarios/code_reviewer_quality_focused/
ls .data/parallel_explorer/code-reviewer/worktrees/architecture-focused/scenarios/code_reviewer_architecture_focused/

# Each has full structure:
# - __init__.py, __main__.py, main.py
# - CLI with click
# - Core analysis modules
# - README.md
# - HOW_TO_CREATE_YOUR_OWN.md
```

**Step 4**: Test both tools with a real PR:

```bash
cd .data/parallel_explorer/code-reviewer/worktrees/quality-focused
python -m scenarios.code_reviewer_quality_focused --diff ../../../sample.diff

cd ../architecture-focused
python -m scenarios.code_reviewer_architecture_focused --diff ../../../sample.diff
```

**Step 5**: Compare the outputs and choose your preferred approach (or combine best aspects of both).

## Why Rich Context Matters

**Simple approach (doesn't work well)**:
```bash
VARIANTS='{"simple":"basic implementation","advanced":"full features"}'
```

This gives Claude almost no guidance about:
- What the tool actually does
- What features matter
- How variants should differ
- What success looks like

**Rich context (works well)**:
```json
{
  "task": "Specific tool description",
  "requirements": ["Concrete requirement 1", "Concrete requirement 2"],
  "variants": {
    "variant1": {
      "description": "Clear one-liner",
      "approach": "Detailed explanation of this variant's unique angle",
      "main_features": ["feature1", "feature2"],
      "focus_areas": ["what matters most for this variant"]
    }
  }
}
```

This provides:
- Clear goal and boundaries
- Specific requirements to implement
- Guidance on how variants should differ
- Context for making implementation decisions

**Result**: Better quality tools that actually implement what you intended.

## How It Works

### The Flow

```
1. Define Context
   ├─> Use /explore-variants (interactive)
   └─> Or create context.json (manual)
         ↓
2. Run Exploration
   └─> make parallel-explore NAME="tool-name"
         ↓
3. For Each Variant (in parallel):
   ├─> Create git worktree
   ├─> Analyze blog_writer & article_illustrator patterns
   ├─> Generate scenario tool files (Python orchestrates, CCSDK generates content)
   ├─> Run make check for quality control
   └─> Validate structure and imports
         ↓
4. Review Results
   └─> Compare implementations in worktrees
```

### Key Architecture

**Code for Structure** (Python):
- Creates worktrees
- Orchestrates file generation
- Runs quality checks
- Validates completeness

**AI for Intelligence** (CCSDK):
- Generates file content
- Implements business logic
- Writes documentation
- Adapts patterns from exemplars

This separation ensures reliability (structured orchestration) while enabling creativity (AI-generated implementations).

## Results & Comparison

### What Gets Created

```
.data/parallel_explorer/{experiment}/
├── context.json                    # Your requirements
├── results/
│   ├── {variant1}_progress.json   # Build progress
│   └── {variant2}_progress.json
└── worktrees/
    ├── {variant1}/                # Full git worktree
    │   └── scenarios/{tool}_{variant1}/  # Complete scenario tool
    └── {variant2}/
        └── scenarios/{tool}_{variant2}/  # Complete scenario tool
```

Each scenario tool is a complete, working implementation you can:
- Import and use immediately
- Copy to main project scenarios/
- Study to understand the approach
- Extend or modify as needed

### Comparing Variants

**What to Compare**:
1. **Code complexity** - Which is easier to understand and maintain?
2. **Feature completeness** - Which better implements the requirements?
3. **Documentation quality** - Which is better explained?
4. **CLI usability** - Which has better command-line interface?
5. **Actual functionality** - Run both with real inputs, compare outputs

**How to Choose**:
- Not about "best" - about "best for your needs"
- Consider your team's skills and preferences
- Think about maintenance burden
- Match to actual use case requirements
- You can combine best aspects from multiple variants

## Cleanup

### List Experiments

```bash
make parallel-explore-list
```

### View Results

```bash
make parallel-explore-results NAME="experiment-name"
```

### Clean Up

```bash
# Remove worktrees and data (keeps git branches)
make parallel-explore-cleanup NAME="experiment-name"

# Also delete git branches
make parallel-explore-cleanup NAME="experiment-name" DELETE_BRANCHES=true
```

The cleanup command will show you which branches exist and how to delete them.

## Advanced Usage

### From Python

```python
from scenarios.parallel_explorer import run_parallel_experiment

# With saved context
results = run_from_saved_context("tool-name")

# Or programmatically
results = await run_parallel_experiment(
    name="tool-name",
    variants={
        "variant1": "description1",
        "variant2": "description2"
    },
    max_parallel=2,
    timeout_minutes=15
)
```

### Customizing Context

You can edit `.data/parallel_explorer/{name}/context.json` before running to:
- Add more requirements
- Refine variant approaches
- Add success criteria
- Specify technical constraints

## Tips for Success

### 1. Be Specific in Requirements

❌ **Vague**: `["Process files", "Generate output"]`

✅ **Specific**: `["Accept markdown files as input", "Extract key concepts using AI", "Generate structured JSON with findings", "Provide confidence scores for each finding"]`

### 2. Make Variants Meaningfully Different

❌ **Too similar**:
```json
{
  "fast": "Optimize for speed",
  "faster": "Optimize even more for speed"
}
```

✅ **Orthogonal approaches**:
```json
{
  "speed-optimized": "Prioritize performance, use caching and async processing",
  "accuracy-focused": "Prioritize correctness, use multiple validation passes"
}
```

### 3. Provide Rich Context

The more context you provide, the better the generated tools:
- What problem does this solve?
- Who will use it?
- What's the expected workflow?
- What makes a good vs poor implementation?

### 4. Start with 2 Variants

Don't try to explore 5 approaches at once:
- 2 variants: Compare clear alternatives
- 3 variants: Add a middle-ground option
- 4+ variants: Only if approaches are truly distinct

## Example: Meeting Summarizer

See `.data/parallel_explorer/meeting-summarizer/context.json` for a complete real example showing:
- Clear task definition
- Specific requirements list
- Rich common context
- Two well-differentiated variants (executive vs technical)
- Concrete success criteria

This example demonstrates the level of detail needed for high-quality tool generation.

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Learn how parallel_explorer was created
- **[blog_writer](../blog_writer/)** - Example scenario tool this generates
- **[article_illustrator](../article_illustrator/)** - Another scenario tool pattern

## Troubleshooting

### "VARIANTS required" error

You need to either:
1. Create context.json first using /explore-variants
2. Or provide VARIANTS directly: `make parallel-explore NAME="test" VARIANTS='{"v1":"desc"}'`

### "Branch already exists" error

Previous run left git branches. Clean them up:
```bash
make parallel-explore-cleanup NAME="experiment" DELETE_BRANCHES=true
```

### Generated tools have import errors

The quality control now catches these during generation. If you see import errors:
1. Check the error message for which import failed
2. File an issue - this shouldn't happen with current validation

### Tools created but don't match requirements

The variant `approach` field is critical - be very specific about what makes each variant unique and what it should prioritize.

---

**Built with amplifier** - Exploring scenario tool approaches through parallel implementation and empirical comparison.
