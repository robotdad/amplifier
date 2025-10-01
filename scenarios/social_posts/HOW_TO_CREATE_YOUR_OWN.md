# How to Create Your Own AI-Powered Tool

This guide explains how to create your own AI-powered content transformation tool using the pattern demonstrated in this Social Media Post Generator.

## The Metacognitive Recipe Pattern

The key to building effective AI tools is the **metacognitive recipe** - a structured approach to problem-solving that mimics how experts think:

### Our Recipe: "Understand → Create → Refine"

1. **Understand** - Deeply analyze the input to extract its essence
2. **Create** - Generate output that captures that essence in a new form
3. **Refine** - Review and improve the output for quality

This pattern works because it separates concerns and allows each stage to focus on doing one thing well.

## The Modular Architecture

### Brick and Stud Philosophy

Think of your tool as LEGO blocks:

- **Bricks** = Self-contained modules with one clear responsibility
- **Studs** = Public interfaces that other bricks connect to
- **Regeneratable** = Each brick can be rebuilt without breaking connections

### Why This Matters

1. **AI-Friendly** - Each module fits in a single LLM context
2. **Testable** - Clear boundaries make testing straightforward
3. **Maintainable** - Changes are isolated to specific modules
4. **Extensible** - Easy to add new stages or modify existing ones

## Building Your Own Tool

### Step 1: Define Your Recipe

First, identify your transformation pattern. Ask yourself:

1. What understanding do I need from the input?
2. What creation/transformation should happen?
3. What refinement would improve quality?

**Example Recipes:**

- **Code Documentation**: Analyze → Document → Verify
- **Data Reporting**: Extract → Visualize → Annotate
- **Content Translation**: Parse → Translate → Localize
- **Email Drafting**: Context → Compose → Polish

### Step 2: Design Your Modules

For each stage in your recipe, create a module:

```python
# Stage 1: Analyzer Module
class ContentAnalyzer:
    async def analyze(self, input_path: Path) -> AnalysisResult:
        # Extract key information
        pass

# Stage 2: Generator Module
class OutputGenerator:
    async def generate(self, analysis: AnalysisResult) -> GeneratedOutput:
        # Transform based on analysis
        pass

# Stage 3: Reviewer Module
class QualityReviewer:
    async def review(self, output: GeneratedOutput) -> ReviewedOutput:
        # Score and improve
        pass
```

### Step 3: Add State Management

Enable interruption recovery with session-based state:

```python
@dataclass
class PipelineState:
    stage: str = "initialized"
    analysis_results: dict = field(default_factory=dict)
    generated_output: dict = field(default_factory=dict)
    review_results: dict = field(default_factory=dict)

class StateManager:
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.state_file = session_dir / "state.json"
        self.state = self._load_state()

    def update_stage(self, stage: str):
        self.state.stage = stage
        self.save()
```

### Step 4: Create the Orchestrator

Wire everything together in a main pipeline:

```python
class Pipeline:
    def __init__(self, state_manager: StateManager):
        self.state = state_manager
        self.analyzer = ContentAnalyzer()
        self.generator = OutputGenerator()
        self.reviewer = QualityReviewer()

    async def run(self, input_path: Path) -> bool:
        # Resume from saved stage
        stage = self.state.state.stage

        if stage == "initialized":
            await self._analyze()
            stage = self.state.state.stage

        if stage == "analyzed":
            await self._generate()
            stage = self.state.state.stage

        if stage == "generated":
            await self._review()

        self.state.mark_complete()
        return True
```

### Step 5: Add CLI Interface

Make it user-friendly with Click:

```python
@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--param", help="Custom parameter")
@click.option("--resume", is_flag=True, help="Resume from saved state")
def main(input_path: Path, param: str, resume: bool):
    """Your tool description here."""

    # Create state manager
    session_dir = None
    if resume:
        session_dir = find_latest_session()
    state_manager = StateManager(session_dir)

    # Run pipeline
    pipeline = Pipeline(state_manager)
    success = asyncio.run(pipeline.run(input_path))

    return 0 if success else 1
```

## Practical Example: Email Newsletter Generator

Let's design a tool that transforms blog posts into email newsletters:

### 1. Define the Recipe

**"Extract → Format → Personalize"**
- Extract: Pull key points and calls-to-action
- Format: Structure as newsletter with sections
- Personalize: Add greetings and customization

### 2. Module Structure

```
email_newsletter/
├── content_extractor/     # Extract key points, CTAs
│   └── core.py
├── newsletter_formatter/  # Create newsletter structure
│   └── core.py
├── personalizer/         # Add personal touches
│   └── core.py
├── state.py             # Session management
├── main.py             # Orchestrator
└── README.md          # Documentation
```

### 3. Key Interfaces

```python
@dataclass
class ExtractedContent:
    key_points: list[str]
    call_to_action: str
    tone: str

@dataclass
class FormattedNewsletter:
    subject_line: str
    sections: list[NewsletterSection]
    footer: str

@dataclass
class PersonalizedNewsletter:
    final_content: str
    personalization_tokens: dict
    send_time_recommendation: str
```

## Best Practices

### 1. Keep Modules Focused

Each module should do ONE thing well:
- ❌ `ContentProcessor` (too vague)
- ✅ `ToneAnalyzer` (specific purpose)

### 2. Use Dataclasses for Interfaces

Clear data structures make modules interoperable:

```python
@dataclass
class ModuleOutput:
    """Clear, documented structure."""
    result: str
    metadata: dict
    confidence: float
```

### 3. Make State Recoverable

Save after each major operation:

```python
async def _process_stage(self):
    result = await self.processor.process()
    self.state.set_stage_result(result)
    self.state.update_stage("processed")  # Saves automatically
```

### 4. Provide Clear Feedback

Show progress and what's happening:

```python
logger.info("📊 Analyzing content structure...")
logger.info(f"  Found {len(sections)} sections")
logger.info(f"  Detected tone: {tone}")
```

### 5. Handle Errors Gracefully

Anticipate API failures and provide recovery:

```python
try:
    response = await self.llm_call(prompt)
except Exception as e:
    logger.error(f"LLM call failed: {e}")
    logger.info("You can resume with --resume flag")
    return False
```

## Common Patterns to Reuse

### Pattern 1: LLM Response Parsing

```python
def _extract_json(self, response: str) -> dict:
    # Remove markdown blocks
    response = re.sub(r"```(?:json)?\n?", "", response)

    # Find JSON object
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if match:
        return json.loads(match.group())

    return {}
```

### Pattern 2: Slugified Output Names

```python
def create_output_filename(title: str) -> str:
    slug = slugify(title)  # Remove special chars, lowercase
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{slug}_{timestamp}.md"
```

### Pattern 3: Parallel Processing

```python
async def process_multiple(items: list) -> list:
    tasks = [process_item(item) for item in items]
    return await asyncio.gather(*tasks)
```

## Testing Your Tool

### 1. Create Sample Data

Always include test data:

```
tests/
├── sample_input.md
├── expected_output.json
└── test_pipeline.py
```

### 2. Test Each Module Independently

```python
async def test_analyzer():
    analyzer = ContentAnalyzer()
    result = await analyzer.analyze(Path("tests/sample.md"))
    assert result.tone in ["professional", "casual", "technical"]
```

### 3. Test Full Pipeline

```python
async def test_end_to_end():
    pipeline = Pipeline(StateManager())
    success = await pipeline.run(Path("tests/sample.md"))
    assert success
    assert Path(".data/session/output.md").exists()
```

## Deployment Considerations

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=your-key
OUTPUT_DIR=./output
MAX_RETRIES=3
```

### Configuration Options

```python
@dataclass
class Config:
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000

config = Config()  # Load from env or file
```

## Next Steps

1. **Start Simple** - Build a basic version first
2. **Iterate** - Add features based on real usage
3. **Get Feedback** - Share with users early
4. **Refine** - Improve based on what you learn

Remember: The best tool is one that solves a real problem. Start with your own needs, build something useful, then share it with others who face the same challenge.

## Resources

- **This Tool's Source** - Study the implementation
- **Blog Writer Example** - Another pattern to learn from
- **Amplifier Docs** - Framework documentation
- **OpenAI Docs** - API capabilities and limits

Happy building! 🚀