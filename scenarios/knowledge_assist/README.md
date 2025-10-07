# Knowledge Assistant

AI-powered tool for synthesizing insights and generating research reports from your extracted knowledge base. Combines local knowledge with optional web search for comprehensive, up-to-date research.

## Overview

Transform your local knowledge base from **passive storage** into **active intelligence**:

- Query → Retrieval → Synthesis → Actionable Output
- Local knowledge + Live web search = Comprehensive insights
- Citations included → Verify sources and dig deeper

## Installation

Requires OpenAI API key set in environment or `.env` file:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Basic Topic Exploration

```bash
# General synthesis on a topic
make knowledge-assist TOPIC="authentication patterns"
```

### Specific Question

```bash
# Focused answer to specific question
make knowledge-assist TOPIC="authentication" QUESTION="best practices for mobile APIs?"
```

### With Temporal Terms (Auto Web Search)

```bash
# Web search auto-enabled for terms like "latest", "current", "2025"
make knowledge-assist TOPIC="latest OAuth 2025 updates"
```

### Deep Mode (Higher Quality, Longer Processing)

```bash
# Run 3-stage deep synthesis pipeline (2-3 minutes)
make knowledge-assist TOPIC="authentication patterns" DEPTH=deep

# Resume interrupted deep session
make knowledge-assist RESUME=20250103_143022
```

## Usage

### Command Syntax

```bash
make knowledge-assist TOPIC="subject" [QUESTION="specific aspect"] [DEPTH=quick|deep] [MODE=research|code] [RESUME=session_id]
```

### Parameters

| Parameter  | Required | Description                                             | Example                       |
| ---------- | -------- | ------------------------------------------------------- | ----------------------------- |
| `TOPIC`    | Yes*     | Subject/domain to research                              | "microservices patterns"      |
| `QUESTION` | No       | Specific question or aspect of interest                 | "best for high availability?" |
| `DEPTH`    | No       | Synthesis depth: quick (~30s) or deep (~2-3min)        | "deep"                        |
| `MODE`     | No       | Output mode: research (default) or code                 | "code"                        |
| `RESUME`   | Yes*     | Resume interrupted session by ID                        | "20250103_143022"             |

*Either `TOPIC` or `RESUME` is required

### Examples

#### 1. Open-Ended Topic Exploration

```bash
make knowledge-assist TOPIC="microservices resilience"
```

Generates comprehensive overview of all knowledge on microservices resilience patterns, including:

- Key concepts and relationships
- Related patterns and insights
- Citations from knowledge base

#### 2. Specific Question About Topic

```bash
make knowledge-assist TOPIC="API design" QUESTION="what are the trade-offs between REST and GraphQL?"
```

Generates focused analysis addressing the specific comparison question.

#### 3. Multiple Aspects

```bash
make knowledge-assist TOPIC="AI agents" QUESTION="how do they handle errors and recover from failures?"
```

Targeted research on specific aspects of the topic.

#### 4. Latest Information (Web Search)

```bash
make knowledge-assist TOPIC="authentication patterns" QUESTION="what are the latest OAuth 2025 security recommendations?"
```

Automatically enables web search due to temporal terms ("latest", "2025") and combines with local knowledge.

#### 5. Deep Mode Research

```bash
# Comprehensive 3-stage analysis (2-3 minutes)
make knowledge-assist TOPIC="distributed systems" QUESTION="how to achieve consistency?" DEPTH=deep
```

#### 6. Code Mode - Pattern Catalog

```bash
# Generate implementation-ready pattern catalog
make knowledge-assist MODE=code TOPIC="authentication patterns"

# Code mode with specific question
make knowledge-assist MODE=code TOPIC="error handling" QUESTION="retry vs circuit breaker?"

# Code mode with deep analysis
make knowledge-assist MODE=code TOPIC="caching strategies" DEPTH=deep
```

The code mode generates:
- **Pattern Library**: Named patterns with purpose, implementation approach, and trade-offs
- **Decision Matrix**: Comparison table for choosing between approaches
- **Code Examples**: Implementation-ready snippets with language-specific syntax
- **Implementation Roadmap**: Phased approach from quick wins to advanced patterns
- **Anti-Patterns**: Common mistakes and better alternatives

Generates publication-quality report with deeper analysis, gap filling, and comprehensive coverage.

## Synthesis Modes

### Quick Mode (Default)

- **Duration**: ~30 seconds
- **Process**: Single-pass synthesis
- **Output**: 1-2 page concise report
- **Best for**: Quick answers, daily research, exploration

```bash
make knowledge-assist TOPIC="your topic"  # Quick is default
```

### Deep Mode

- **Duration**: 2-3 minutes
- **Process**: 3-stage pipeline
  1. **Analysis Stage**: Identify themes and knowledge gaps
  2. **Augmentation Stage**: Fill gaps with web research (if needed)
  3. **Generation Stage**: Create comprehensive report
- **Output**: 2-3 page detailed report with deeper insights
- **Best for**: Important research, documentation, strategic decisions

```bash
make knowledge-assist TOPIC="your topic" DEPTH=deep
```

### Resume Capability

Deep mode sessions can be resumed if interrupted:

```bash
# Start deep session
make knowledge-assist TOPIC="complex topic" DEPTH=deep
# ... if interrupted ...

# Resume from where it left off
make knowledge-assist RESUME=20250103_143022
```

Stage results are saved incrementally, so you won't lose progress.

## Output Format

### Report Structure

Generated markdown reports include:

1. **Title & Metadata**

   - Topic and optional question
   - Generation timestamp
   - Statistics (concepts retrieved, web sources used)

2. **Main Synthesis**

   - Comprehensive answer to question or topic overview
   - 3-5 paragraphs of synthesized insights

3. **Key Insights**

   - Bulleted list of main takeaways
   - Highlights important patterns and connections

4. **Related Concepts**

   - Relevant concepts from knowledge base
   - How they relate to the topic

5. **Citations**
   - Local knowledge sources (articles, concepts used)
   - Web sources (if web search was used)
   - First reference only (no over-citing)

### Session Directory

```
.data/knowledge_assist/sessions/{timestamp}/
├── session.json         # Metadata and statistics
├── research_report.md   # Generated report
└── retrieved.json       # Raw retrieved knowledge
```

## Web Search

### Auto-Detection

Web search is automatically enabled when queries contain temporal terms:

- "latest", "current", "recent", "new"
- Year references ("2025", "2024")
- Comparative terms ("best", "top", "modern")

### Manual Control

```bash
# Force web search (not yet implemented in MVP)
make knowledge-assist TOPIC="authentication" WEB_SEARCH=always

# Disable web search (not yet implemented in MVP)
make knowledge-assist TOPIC="authentication" WEB_SEARCH=never
```

## Configuration

Settings are read from environment variables or `.env` file:

### Required

```bash
OPENAI_API_KEY=your-api-key-here
```

### Optional

```bash
# Model selection (default: gpt-4o)
KNOWLEDGE_ASSIST_MODEL=gpt-4o  # or gpt-5 when compatible

# Retrieval limits
KNOWLEDGE_ASSIST_MAX_CONCEPTS=30
KNOWLEDGE_ASSIST_MAX_RELATIONSHIPS=50

# Temperature for synthesis (0.0-2.0, default: 0.7)
KNOWLEDGE_ASSIST_TEMPERATURE=0.7
```

## How It Works

### 1. Knowledge Retrieval (Code)

- Searches `.data/knowledge/extractions.jsonl`
- Filters by topic + optional question keywords
- Ranks by relevance scoring
- Returns top N concepts, relationships, insights, patterns

### 2. Synthesis (AI)

- Uses OpenAI Responses API (gpt-4o)
- Single-stage quick synthesis for MVP
- Optional web search integration
- Generates markdown output

### 3. Output Generation (Code)

- Formats synthesis as clean markdown
- Adds citations section at end
- Saves to session directory
- Tracks statistics and metadata

## Tips for Best Results

### Topic Selection

- **Be specific**: "OAuth 2.0 patterns" vs "authentication"
- **Use domain terms**: Use terminology from your knowledge base
- **Multiple terms**: "microservices resilience patterns" captures multiple concepts

### Question Formulation

- **Open-ended**: "what are the key considerations?"
- **Comparative**: "how does X compare to Y?"
- **Targeted**: "what are the trade-offs?"
- **Practical**: "when should I use X?"

### Output Quality

- First run might be slower as knowledge base is loaded
- More specific topics = more focused results
- Web search works best with temporal queries
- Citations help you verify and explore deeper

## Limitations (MVP)

Current MVP limitations:

- **Single-stage synthesis only**: No deep mode with multi-stage analysis
- **Research mode only**: No code mode for technical pattern catalogs
- **No resume capability**: Each run is independent
- **Manual web search control**: Not yet implemented (auto-detection only)

These features may be added based on usage and feedback.

## Troubleshooting

### "No content returned from synthesis"

- Check OpenAI API key is set correctly
- Verify API key has credits/permissions
- Check network connectivity

### "No knowledge retrieved"

- Verify topic uses terms from your knowledge base
- Check `.data/knowledge/extractions.jsonl` exists and has content
- Try broader topic terms

### Web search not working

- Ensure topic/question contains temporal terms
- Check OpenAI API supports web search (gpt-4o does)
- Future: Manual `WEB_SEARCH=always` flag

## Examples from Real Use

### Example 1: Technical Pattern Research

**Input:**

```bash
make knowledge-assist TOPIC="circuit breaker pattern" QUESTION="when should I use it vs retry logic?"
```

**Output:** 3-page markdown report with:

- Explanation of circuit breaker and retry logic
- Comparison table of use cases
- Recommendations based on failure patterns
- Citations to 12 articles from knowledge base

### Example 2: Open-Ended Exploration

**Input:**

```bash
make knowledge-assist TOPIC="microservices observability"
```

**Output:** Comprehensive overview covering:

- Key observability concepts (metrics, logs, traces)
- Common patterns and tools
- Integration approaches
- Real-world examples from knowledge base

### Example 3: Latest Practices

**Input:**

```bash
make knowledge-assist TOPIC="API security" QUESTION="what are the latest 2025 best practices?"
```

**Output:** Report combining:

- Local knowledge base articles on API security
- Latest 2025 recommendations from web search
- Synthesis of evolving best practices
- Both local and web citations

## Advanced Usage

### Custom Output Location

```bash
make knowledge-assist TOPIC="authentication" OUTPUT=~/research/auth-patterns
```

### Programmatic Usage

```python
from scenarios.knowledge_assist import KnowledgeAssist

# Initialize
assistant = KnowledgeAssist()

# Generate research
result = assistant.research(
    topic="microservices patterns",
    question="best for high availability?"
)

# Access output
print(result.output_path)
print(result.tokens_used)
```

## Future Enhancements

Based on MVP validation, potential additions:

- **Deep mode**: Multi-stage synthesis for higher quality
- **Code mode**: Technical pattern catalogs with examples
- **Resume capability**: Pick up interrupted sessions
- **Manual web search control**: Force enable/disable
- **Export formats**: PDF, HTML, presentation slides
- **Interactive mode**: Iterative refinement with follow-up questions

## Support

For issues or feature requests:

1. Check SPECIFICATION.md for detailed design
2. Review session logs in `.data/knowledge_assist/sessions/`
3. Submit issues with session ID and query details

## License

Part of the Amplifier project.
