# Knowledge Assistant: Your AI Research Partner

**Transform your knowledge base into actionable research reports in seconds.**

## The Problem

You have 376 articles, documents, and notes in your knowledge base, but:
- **Finding relevant content takes forever** - Scattered across files, hard to search comprehensively
- **Synthesis requires mental heavy-lifting** - Manually connecting dots across dozens of documents
- **Information gets stale quickly** - Your knowledge from 2024 doesn't include 2025 developments
- **Citations are tedious to track** - Remembering where each insight came from is nearly impossible

## The Solution

Knowledge Assistant is an AI-powered research tool that:

1. **Searches your entire knowledge base** - Retrieves all relevant concepts, patterns, and insights
2. **Synthesizes comprehensive reports** - Connects ideas across documents into coherent narratives
3. **Augments with web search** - Automatically adds latest information when needed
4. **Includes proper citations** - Every claim linked to its source for verification
5. **Adapts to your needs** - Quick summaries or deep research based on your requirements

**The result**: Publication-quality research reports from your knowledge base in under 30 seconds.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
make knowledge-assist TOPIC="authentication patterns"
```

The tool will:
1. Search your knowledge base for relevant content
2. Synthesize insights into a cohesive report
3. Add web search if temporal terms detected
4. Generate markdown with citations
5. Save to timestamped session directory

### Your First Research Report

1. **Ensure you have a knowledge base** - Check that `.data/knowledge/extractions.jsonl` exists with your extracted content

2. **Pick a topic you care about** - Something with good coverage in your knowledge base:

```bash
# See what topics you have
grep -o '"text":"[^"]*"' .data/knowledge/extractions.jsonl | head -20
```

3. **Run your first query**:

```bash
make knowledge-assist TOPIC="microservices patterns"
```

4. **Review the output** - Find your report in:
   - `.data/knowledge_assist/sessions/{timestamp}/research_report.md`
   - Session metadata in `session.json`
   - Retrieved knowledge in `retrieved.json`

5. **Try a specific question** - Get focused answers:

```bash
make knowledge-assist \
  TOPIC="authentication" \
  QUESTION="what are the trade-offs between OAuth2 and JWT?"
```

## Usage Examples

### Basic: Quick Topic Research

```bash
make knowledge-assist TOPIC="API design patterns"
```

**What happens**:
- Retrieves all API design content from knowledge base
- Synthesizes key patterns and principles
- Generates 1-2 page overview
- Includes citations to source documents
- Takes ~30 seconds

### Advanced: Deep Mode with Specific Question

```bash
make knowledge-assist \
  TOPIC="distributed systems" \
  QUESTION="how to achieve consistency?" \
  DEPTH=deep
```

**What happens**:
- Three-stage analysis pipeline (2-3 minutes)
- Identifies themes and knowledge gaps
- Augments with web research if needed
- Generates comprehensive 2-3 page report
- Resumable if interrupted

### Resume: Continue Interrupted Session

```bash
# Start deep analysis
make knowledge-assist TOPIC="complex topic" DEPTH=deep
# ... if interrupted ...

# Resume where you left off
make knowledge-assist RESUME=20250103_143022
```

**What happens**:
- Loads saved session state
- Continues from last completed stage
- Preserves all previous work
- No duplicate processing

## How It Works

### The Pipeline

```
Topic + Question
      ↓
[Search Knowledge Base] ──→ concepts, patterns, insights
      ↓
[Check for Temporal Terms] ──→ enable web search if needed
      ↓
[AI Synthesis] ──→ GPT-4o generates comprehensive report
      ↓
[Format Output] ──→ markdown with citations
      ↓
Research Report
```

### Key Components

- **Knowledge Retriever**: Searches `.data/knowledge/extractions.jsonl` using relevance scoring
- **Synthesis Engine**: OpenAI integration with Responses API for optional web search
- **Output Generator**: Formats clean markdown with proper citations
- **Session Manager**: Tracks progress and enables resume capability

### Why It Works

**Code handles the structure**:
- Efficient JSONL searching and ranking
- Session state management
- File I/O and error handling
- Citation tracking and formatting

**AI handles the intelligence**:
- Understanding conceptual relationships
- Synthesizing coherent narratives
- Identifying knowledge gaps
- Incorporating web search naturally

This separation means fast, reliable retrieval (code) with intelligent synthesis (AI).

## Configuration

### Command-Line Parameters

```bash
# Required (one of these)
TOPIC="subject"              # Research topic
RESUME="session_id"          # Resume interrupted session

# Optional
QUESTION="specific aspect"   # Focused question about topic
DEPTH=quick|deep            # Synthesis depth (default: quick)
MODE=research|code          # Output mode (default: research)
OUTPUT="path/to/output"     # Custom output location
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your-api-key-here

# Optional
KNOWLEDGE_ASSIST_MODEL=gpt-4o           # AI model
KNOWLEDGE_ASSIST_MAX_CONCEPTS=30        # Retrieval limit
KNOWLEDGE_ASSIST_MAX_RELATIONSHIPS=50   # Relationship limit
KNOWLEDGE_ASSIST_TEMPERATURE=0.7        # Creativity (0.0-2.0)
```

### Output Structure

```
.data/knowledge_assist/sessions/{timestamp}/
├── session.json           # Metadata and statistics
├── research_report.md     # Generated report
├── retrieved.json        # Raw retrieved knowledge
└── stage_*.json          # Deep mode stage outputs (if applicable)
```

## Synthesis Modes

### Quick Mode (Default)
- **Duration**: ~30 seconds
- **Best for**: Daily research, quick answers, exploration
- **Output**: 1-2 page focused report

### Deep Mode
- **Duration**: 2-3 minutes
- **Best for**: Important research, documentation, strategic decisions
- **Process**:
  1. Analysis Stage - Identify themes and gaps
  2. Augmentation Stage - Fill gaps with web research
  3. Generation Stage - Create comprehensive report
- **Output**: 2-3 page detailed analysis

### Code Mode (Phase 3)
- **Duration**: 1-2 minutes
- **Best for**: Technical implementation guidance
- **Output**: Pattern catalog with:
  - Named patterns with implementation details
  - Decision matrices for choosing approaches
  - Code examples in multiple languages
  - Common anti-patterns to avoid

## Troubleshooting

### "No content returned from synthesis"

**Problem**: OpenAI API issues

**Solution**:
- Check API key is set correctly
- Verify API has credits
- Check network connectivity

### "No knowledge retrieved for topic"

**Problem**: Topic doesn't match knowledge base content

**Solution**:
- Use terms that appear in your documents
- Check `.data/knowledge/extractions.jsonl` exists
- Try broader topic terms

### "Session not found for resume"

**Problem**: Invalid session ID

**Solution**:
- Check session ID format (YYYYMMDD_HHMMSS)
- List available sessions: `ls .data/knowledge_assist/sessions/`
- Start fresh without RESUME parameter

### Web search not triggering

**Problem**: Temporal terms not detected

**Solution**:
- Include words like "latest", "2025", "current", "recent"
- Future: Use WEB_SEARCH=always flag (not yet implemented)

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - The story of how this tool was created
- **[SPECIFICATION.md](./SPECIFICATION.md)** - Complete technical specification
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework powering these tools
- **[Knowledge Extractor](../knowledge_extractor/)** - Build your knowledge base

## What's Next?

Knowledge Assistant demonstrates the power of AI-augmented research:

1. **Use it** - Generate research reports from your knowledge base
2. **Extend it** - Add new modes like code generation or presentation creation
3. **Learn from it** - See how minimal code can orchestrate powerful AI
4. **Build your own** - Describe your workflow to Amplifier and watch it come to life

---

**Built iteratively using Amplifier** - From initial MVP to deep mode to code patterns, each phase emerged from describing what we wanted. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for the full story.