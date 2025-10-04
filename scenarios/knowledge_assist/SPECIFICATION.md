# Knowledge-Assist Tool - Technical Specification

**Version:** 1.0
**Status:** Design Phase
**Date:** 2025-10-03

---

## Overview

AI-powered tool for synthesizing insights and generating reports from your extracted knowledge base. Combines local knowledge with web search for comprehensive, up-to-date research.

**Pattern:** Amplifier CLI Tool (code for structure, AI for intelligence)
**Location:** `scenarios/knowledge_assist/`
**Exemplar:** Based on `scenarios/blog_writer/` proven patterns

---

## Core Concept

Transform your local knowledge base from **passive storage** into **active intelligence**:

- Query → Retrieval → Synthesis → Actionable Output
- Local knowledge + Live web search = Comprehensive insights
- Citations included → Verify sources and dig deeper

---

## Operating Modes

### **Mode 1: Research** (Default - MVP Focus)

**Purpose:** General knowledge synthesis for any use case

**Use Cases:**

- Quick Q&A: Topic + specific question
- Research reports: Comprehensive topic exploration
- Blog backing materials: Find relevant concepts for writing
- Idea synthesis: Discover connections between concepts
- Exploration: Open-ended topic investigation

**Output:** Markdown report with synthesis, insights, and citations

**Examples:**

```bash
# Topic overview (open-ended)
make knowledge-assist TOPIC="API authentication patterns"
→ General synthesis of all authentication knowledge

# Specific question about topic
make knowledge-assist TOPIC="authentication" QUESTION="how do OAuth2 and JWT compare for mobile APIs?"
→ Focused answer comparing the two approaches

# Complex investigation
make knowledge-assist TOPIC="AI agents" QUESTION="what error handling and recovery strategies are used?"
→ Targeted research on specific aspects of topic
```

---

### **Mode 2: Code** (Future - Post-MVP)

**Purpose:** Technical pattern catalogs and implementation specs

**Use Cases:**

- Pattern catalog: Technical patterns with examples
- Implementation spec: Detailed specs for specific patterns
- Approach comparison: Compare different implementation strategies
- Best practices: Catalog design patterns from knowledge base

**Output:** Structured markdown with code examples, patterns, and implementation guidance

**Examples:**

```bash
# Pattern catalog
make knowledge-assist MODE=code TOPIC="authentication patterns"
→ Technical catalog of all auth patterns found

# Comparison focus
make knowledge-assist MODE=code TOPIC="authentication" QUESTION="OAuth2 vs JWT trade-offs?"
→ Detailed comparison with implementation guidance
```

**Note:** Code mode is Phase 3 - validate research mode usefulness first

---

## Architecture

### **Pipeline Flow**

```
User Input
    ↓
Parse Intent & Parameters (code)
    ↓
Knowledge Retrieval (code)
    ├─ Query local extractions.jsonl
    ├─ Filter & rank by relevance
    └─ Select top N items
    ↓
Depth Decision (code)
    ├─ Quick (1 stage): Direct synthesis
    └─ Deep (3 stages): Analyze → Structure → Generate
    ↓
AI Synthesis (OpenAI Responses API)
    ├─ Use retrieved knowledge
    ├─ Optional: Augment with web search
    └─ Generate mode-specific output
    ↓
Output Generation (code)
    ├─ Format as markdown
    ├─ Add citations section
    └─ Save to session directory
```

### **Component Structure**

```
scenarios/knowledge_assist/
├── __init__.py
├── __main__.py                  # CLI entry point
├── README.md                    # User guide with examples
├── SPECIFICATION.md             # This document
├── config.py                    # Settings and defaults
├── state.py                     # Session state management
├── knowledge_retriever.py       # Query & filter knowledge base (CODE)
├── synthesis_engine.py          # OpenAI Responses API integration (HYBRID)
├── output_generator.py          # Markdown formatting with citations (CODE)
├── prompts/
│   ├── research_quick.txt       # Single-stage research synthesis
│   ├── research_analyze.txt     # Stage 1: Analyze knowledge
│   ├── research_structure.txt   # Stage 2: Create outline
│   ├── research_generate.txt    # Stage 3: Generate report
│   ├── code_quick.txt           # Single-stage code catalog
│   ├── code_analyze.txt         # Stage 1: Identify patterns
│   ├── code_structure.txt       # Stage 2: Organize catalog
│   └── code_generate.txt        # Stage 3: Generate with examples
└── tests/
    ├── test_knowledge_assist.py
    └── sample_knowledge.jsonl   # Test fixtures
```

---

## CLI Interface

### **Basic Syntax**

```bash
make knowledge-assist TOPIC="subject" [QUESTION="specific aspect"] [MODE=research|code] [OUTPUT=path]
```

### **Parameters**

| Parameter           | Required | Default        | Description                                                             |
| ------------------- | -------- | -------------- | ----------------------------------------------------------------------- |
| `TOPIC`             | Yes      | -              | Subject/domain to research (e.g., "authentication patterns")            |
| `QUESTION`          | No       | -              | Specific question or aspect of interest (e.g., "best for mobile APIs?") |
| `MODE`              | No       | `research`     | Output mode: `research` or `code`                                       |
| `OUTPUT`            | No       | Auto-generated | Output directory path                                                   |
| `MAX_CONCEPTS`      | No       | `30`           | Max concepts to retrieve from knowledge base                            |
| `MAX_RELATIONSHIPS` | No       | `50`           | Max relationships to retrieve                                           |
| `WEB_SEARCH`        | No       | `auto`         | Web search: `auto`, `always`, `never`                                   |
| `RESUME`            | No       | -              | Resume session ID                                                       |

**Note:** `DEPTH` parameter removed for MVP - only quick mode initially

### **Examples**

```bash
# Topic exploration (open-ended)
make knowledge-assist TOPIC="microservices resilience"
→ General synthesis of all knowledge on topic

# Specific question about topic
make knowledge-assist TOPIC="authentication patterns" QUESTION="which is best for mobile APIs?"
→ Focused answer addressing specific question

# Multiple aspects
make knowledge-assist TOPIC="AI agents" QUESTION="how do they handle errors and recover from failures?"
→ Targeted research on specific aspects

# Code pattern catalog
make knowledge-assist MODE=code TOPIC="error handling"
→ Technical catalog of all error handling patterns

# Code with specific focus
make knowledge-assist MODE=code TOPIC="authentication" QUESTION="OAuth2 vs JWT for microservices?"
→ Comparison-focused catalog

# Resume interrupted session
make knowledge-assist RESUME=20251003_1512
```

---

## Data Flow Details

### **Stage 1: Knowledge Retrieval** (Code-Driven)

**Input:** User query string

**Process:**

1. Parse query → extract key terms (simple keyword extraction)
2. Search `extractions.jsonl`:
   - Full-text search on concept names and descriptions
   - Match relationships by subject/object
   - Match insights and patterns
3. Rank results:
   - Exact keyword match: +10 points
   - Partial match: +5 points
   - Importance score: +0-10 points
   - Relationship count: +1 per connection
4. Select top N:
   - Top 30 concepts (configurable)
   - Top 50 relationships (configurable)
   - Top 20 insights
   - Top 15 patterns

**Output:** Filtered knowledge context

```python
{
  "query": "API authentication",
  "retrieved": {
    "concepts": [
      {"name": "OAuth 2.0", "description": "...", "importance": 0.95, "sources": [...]},
      ...
    ],
    "relationships": [
      {"subject": "OAuth 2.0", "predicate": "enables", "object": "delegated access", ...},
      ...
    ],
    "insights": [...],
    "patterns": [...]
  },
  "total_matches": {"concepts": 45, "relationships": 82}
}
```

---

### **Stage 2: Synthesis Decision** (Code Logic)

**Quick Mode** (Default):

- Single AI call
- Direct synthesis
- ~30 seconds
- Good for: Simple questions, pattern lists, quick research

**Deep Mode**:

- 3-stage pipeline
- Higher quality
- ~2-3 minutes
- Good for: Research reports, comprehensive analysis, complex topics

**Web Search Decision** (Code Logic):

```python
if web_search == "auto":
    # Enable if query implies current/latest info
    enable = any(term in query.lower() for term in ["latest", "current", "2025", "recent", "new"])
elif web_search == "always":
    enable = True
else:  # "never"
    enable = False
```

---

## Multi-Stage Synthesis Pipeline

### **Research Mode - Deep Synthesis**

#### **Stage 1: Analyze** (~30 seconds)

**AI Task:** Understand the knowledge and identify themes

**Prompt:** `prompts/research_analyze.txt`

```
You are analyzing a curated knowledge base to answer this question:
{query}

Here is the relevant knowledge retrieved from the database:

CONCEPTS:
{formatted_concepts}

RELATIONSHIPS:
{formatted_relationships}

INSIGHTS:
{formatted_insights}

PATTERNS:
{formatted_patterns}

Your task:
1. Identify the main themes and concepts relevant to the query
2. Note any gaps or questions that web search could help fill
3. List key relationships and patterns that matter
4. Suggest an outline structure for the research report

Output format (JSON):
{
  "main_themes": ["theme1", "theme2", ...],
  "key_concepts": ["concept1", "concept2", ...],
  "knowledge_gaps": ["gap1", "gap2", ...],
  "relevant_patterns": ["pattern1", ...],
  "suggested_outline": ["section1", "section2", ...]
}
```

**Output:** Analysis JSON

---

#### **Stage 2: Augment** (Optional, ~20 seconds)

**Triggered:** If knowledge_gaps exist AND web_search enabled

**AI Task:** Fill gaps with current information

**Prompt:** `prompts/research_augment.txt`

```
You have analyzed a knowledge base and identified these gaps:
{knowledge_gaps}

Use web search to find current, authoritative information on these topics.

For each gap:
1. Search for recent, reliable sources
2. Extract key facts and insights
3. Note the source URLs

Keep responses concise - we're supplementing existing knowledge, not replacing it.

Output format (JSON):
{
  "gap_name": {
    "findings": "...",
    "sources": ["url1", "url2"]
  },
  ...
}
```

**API Call:**

```python
response = client.responses.create(
    model="gpt-4o",  # Note: GPT-5 has web_search compatibility issues
    input=prompt,
    tools=[{"type": "web_search"}]
)
```

**Output:** Web research JSON

---

#### **Stage 3: Generate** (~45 seconds)

**AI Task:** Create comprehensive markdown report

**Prompt:** `prompts/research_generate.txt`

```
Generate a comprehensive research report answering this query:
{query}

You have two sources of information:

LOCAL KNOWLEDGE (from curated knowledge base):
{retrieved_knowledge}

CURRENT INFORMATION (from web search):
{web_research}  # Only if stage 2 ran

ANALYSIS:
{stage1_analysis}

Create a well-structured markdown report with:

1. **Executive Summary** - 2-3 sentences answering the core query

2. **Main Content** - Organized by the suggested outline:
{suggested_outline}

For each section:
- Synthesize insights from local knowledge and web research
- Provide specific examples and details
- Note interesting connections or patterns
- Use clear, direct language

3. **Key Takeaways** - Bulleted list of 3-5 main insights

4. **Citations** - List all sources used:
   - Local knowledge: Article titles/IDs where concepts came from
   - Web research: URLs with brief descriptions

Format: Clean markdown, use headers (##), bullets, and **bold** for emphasis.
Tone: Clear, informative, synthesis-focused (not just summarization).
```

**Output:** Complete markdown report

---

### **Research Mode - Quick Synthesis (MVP)**

**Single Stage** (~30 seconds)

**AI Task:** Direct synthesis without multi-stage analysis

**Prompt:** `prompts/research_quick.txt`

```
You are synthesizing knowledge on this topic:
TOPIC: {topic}
{#if question}SPECIFIC QUESTION: {question}{/if}

KNOWLEDGE FROM YOUR DATABASE:

CONCEPTS:
{formatted_concepts}

RELATIONSHIPS:
{formatted_relationships}

INSIGHTS:
{formatted_insights}

PATTERNS:
{formatted_patterns}

{#if web_results}
CURRENT INFORMATION FROM WEB:
{web_results}
{/if}

Task:
{#if question}
Answer the specific question about this topic, using the knowledge provided.
{else}
Provide a comprehensive overview of this topic, synthesizing the knowledge provided.
{/if}

Format your response as markdown with:

## {Topic Title}

[Main synthesis - 3-5 paragraphs addressing the {question or general topic}]

### Key Insights

- Insight 1
- Insight 2
- Insight 3

### Related Concepts

- Concept and how it relates

## Citations

[Will be added by code - don't generate citations in your response]

Guidelines:
- Be clear and direct
- Synthesize don't just list
- Mention concepts/patterns by name on FIRST reference only
- Focus on answering the question or explaining the topic
- Natural writing, not overly academic
```

**Web Search:** Triggered automatically for queries with temporal terms

**Citation Handling:** Code adds citations section after AI generation (first reference only)

---

### **Code Mode - Deep Synthesis**

#### **Stage 1: Identify** (~30 seconds)

**Prompt:** `prompts/code_analyze.txt`

```
You are cataloging technical patterns from a knowledge base for this query:
{query}

RETRIEVED KNOWLEDGE:
{retrieved_knowledge}

Identify:
1. All relevant code patterns, architectures, or implementation approaches
2. Common themes across the patterns
3. Any gaps where web search for current best practices would help
4. Suggested structure for the pattern catalog

Output format (JSON):
{
  "identified_patterns": [{"name": "...", "description": "...", "source": "..."}],
  "themes": ["theme1", "theme2"],
  "knowledge_gaps": ["gap1", ...],
  "suggested_structure": ["section1", ...]
}
```

---

#### **Stage 2: Augment** (Optional, ~20 seconds)

**Same as Research Mode** - Fill technical gaps with web search

---

#### **Stage 3: Generate** (~45 seconds)

**Prompt:** `prompts/code_generate.txt`

```
Generate a technical pattern catalog for: {query}

SOURCES:
- Local knowledge: {retrieved_knowledge}
- Current practices: {web_research}
- Analysis: {stage1_analysis}

Create a structured markdown catalog with:

1. **Overview** - Brief introduction to the domain

2. **Pattern Catalog** - Organized by {suggested_structure}

For each pattern:
- **Pattern Name**
- **Purpose**: What problem it solves
- **Approach**: How it works
- **Example**: Code snippet or concrete example (if available)
- **Trade-offs**: When to use vs not use
- **Related Patterns**: Connections to other approaches

3. **Decision Matrix** - Table comparing patterns on key dimensions

4. **Recommendations** - When to use each pattern

5. **Further Reading** - Citations to source articles and web resources

Format: Clean markdown optimized for reference/implementation use.
Technical level: Assume intermediate developer knowledge.
```

---

### **Code Mode - Quick Synthesis**

**Single Stage** (~30 seconds)

**Prompt:** `prompts/code_quick.txt`

```
Create a technical pattern list for: {query}

KNOWLEDGE:
{retrieved_knowledge}

Generate a concise catalog with:

**Identified Patterns:**
For each pattern:
- Name and brief description
- When to use it
- Key implementation considerations

**Citations:**
- Source articles from knowledge base

Format as markdown. Be practical and implementation-focused.
```

---

## Technical Specifications

### **OpenAI Integration**

**API:** OpenAI Responses API (NOT Completions API)
**Model:** `gpt-4o` (GPT-5 has web_search compatibility issues as of Oct 2025)
**Python Client:** `openai` package

**Basic Structure:**

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Quick synthesis
response = client.responses.create(
    model="gpt-4o",
    input=prompt,
    tools=[{"type": "web_search"}] if enable_search else []
)

# Access output
output_text = response.output[0].content[0].text
citations = [ann.title for ann in response.output[0].content[0].annotations]

# Multi-stage (with state)
response_stage2 = client.responses.create(
    model="gpt-4o",
    input=stage2_prompt,
    previous_response_id=response.id,  # Preserves context
    tools=[{"type": "web_search"}]
)
```

### **Web Search Integration Strategy**

**When to Use Web Search:**

1. **Auto Mode** (Default):

   - Detect temporal terms: "latest", "current", "2025", "new", "recent"
   - Detect comparative terms: "best", "top", "modern"
   - Enable for deep mode by default

2. **Research Mode:**

   - Stage 1 (Analyze): No search (just analyze local knowledge)
   - Stage 2 (Augment): Search to fill identified gaps
   - Stage 3 (Generate): No search (synthesis only)

3. **Code Mode:**
   - Stage 1 (Identify): No search (catalog local patterns)
   - Stage 2 (Augment): Search for current best practices
   - Stage 3 (Generate): No search (synthesis only)

**Rationale:**

- Focused search in stage 2 prevents information overload
- Stage 1 identifies WHAT to search for
- Stage 3 synthesizes both sources efficiently

---

## Session Management

**Follows blog_writer pattern**

**Session Directory:**

```
.data/knowledge_assist/sessions/{session_id}/
├── session.json          # State and metadata
├── retrieved.json        # Filtered knowledge from database
├── stage1_analysis.json  # Deep mode only
├── stage2_augment.json   # If web search used
└── output.md             # Final generated report
```

**Session State:**

```json
{
  "session_id": "20251003_151230",
  "created_at": "2025-10-03T15:12:30Z",
  "topic": "authentication patterns",
  "question": "which is best for mobile APIs?",
  "mode": "research",
  "web_search_used": true,
  "completed": true,
  "outputs": {
    "retrieved": "retrieved.json",
    "final": "research_report.md"
  },
  "stats": {
    "concepts_retrieved": 30,
    "relationships_retrieved": 50,
    "insights_retrieved": 18,
    "patterns_retrieved": 12,
    "web_sources_found": 5,
    "duration_seconds": 32
  }
}
```

### **Resume Capability**

```bash
# Resume interrupted session
make knowledge-assist RESUME=20251003_151230

# List recent sessions
make knowledge-assist-list

# View session output
make knowledge-assist-show SESSION=20251003_151230
```

---

## Output Format Specifications

### **Research Mode Output**

**File:** `{session_dir}/research_report.md`

```markdown
# Research Report: {topic}

{#if question}**Focus:** {question}{/if}

**Generated:** 2025-10-03 15:30
**Knowledge Base:** 372 articles
**Concepts Retrieved:** 30
**Web Sources:** 5

---

## Summary

[2-3 paragraphs synthesizing knowledge to address the {question or provide topic overview}]

---

## Findings

### {Section 1 from outline}

[Synthesized content combining local knowledge and web research]

**Key Concepts:**

- **Concept Name**: Description and significance
- **Related Pattern**: How it connects

### {Section 2 from outline}

...

---

## Key Takeaways

- Insight 1
- Insight 2
- Insight 3

---

## Citations

### From Knowledge Base

1. **{Article Title/ID}**: Concepts - {list}, Relationships - {list}
2. **{Article Title/ID}**: Patterns - {list}
   ...

### From Web Research

1. [{Source Title}]({URL}) - Brief description
2. [{Source Title}]({URL}) - Brief description
   ...

---

_Generated by knowledge-assist tool | Session: 20251003_151230_
```

---

### **Code Mode Output**

**File:** `{session_dir}/code_catalog.md`

````markdown
# Technical Pattern Catalog: {query}

**Generated:** 2025-10-03 15:30
**Patterns Identified:** 8
**Sources:** 15 articles

---

## Overview

[Brief context on the pattern domain]

---

## Pattern Catalog

### 1. {Pattern Name}

**Purpose:** What problem it solves

**Approach:** How it works (high-level)

**Implementation Example:**

```python
# Code example if available in knowledge base
```
````

**When to Use:**

- Use case 1
- Use case 2

**Trade-offs:**

- ✅ Benefit 1
- ❌ Limitation 1

**Related Patterns:** Links to other patterns in this catalog

**Sources:** [Article IDs from knowledge base]

---

### 2. {Pattern Name}

...

---

## Decision Matrix

| Pattern   | Complexity | Performance | Use When |
| --------- | ---------- | ----------- | -------- |
| Pattern 1 | Low        | High        | ...      |
| Pattern 2 | Medium     | Medium      | ...      |

---

## Recommendations

**For {use case}:** Use Pattern X because...

---

## Citations

[Same format as research mode]

---

_Generated by knowledge-assist tool | Session: 20251003_151230_

```

---

## Approved Decisions (Based on User Feedback)

✅ **API Key:** Get from environment variable or .env file
✅ **Model:** Use `gpt-4o` now, configurable switch for `gpt-5` when compatible
✅ **Output Location:** `.data/knowledge_assist/sessions/` (perfect)
✅ **Build Approach:** MVP first - research quick mode only
✅ **Web Search:** Yes, with proper citation of web sources
✅ **Citations:** End of document only, first reference only (no over-citing)
✅ **Topic/Question:** TOPIC (required) + QUESTION (optional) for clear intent

---

## Implementation Phases

### **Phase 1: MVP - Research Quick Mode** ⭐ **START HERE**

**Scope:**
- Research mode only
- Quick synthesis (single-stage)
- TOPIC + optional QUESTION parameters
- Knowledge retrieval from local extractions.jsonl
- Web search integration (auto-enabled for temporal terms)
- Markdown output with citations
- Session state (minimal - for output tracking)

**Deliverables:**
```

scenarios/knowledge_assist/
├── **init**.py
├── **main**.py # CLI entry
├── config.py # Settings (OpenAI key, model, limits)
├── knowledge_retriever.py # Search & filter knowledge base
├── synthesis_engine.py # OpenAI Responses API calls
├── output_generator.py # Markdown formatting + citations
├── prompts/
│ └── research_quick.txt # Single prompt for MVP
└── README.md # Usage guide

````

**Validation:**
- Can answer topic-only queries: `TOPIC="authentication patterns"`
- Can answer focused questions: `TOPIC="auth" QUESTION="best for mobile?"`
- Web search works when needed
- Citations are accurate and properly formatted
- Output is useful for blog/research/coding input

---

### **Phase 2: Deep Mode** (Future)

**Add if MVP proves valuable:**
- Multi-stage pipeline (analyze → augment → generate)
- Session state management for resume
- Higher quality synthesis

---

### **Phase 3: Code Mode** (Future)

**Add if research mode isn't sufficient for technical use cases:**
- Code-specific prompts
- Pattern catalog formatting
- Technical decision matrices

---

## Code vs AI Boundary

### **Code Handles** (Deterministic)

```python
# knowledge_retriever.py
class KnowledgeRetriever:
    def search(self, query: str, max_concepts: int = 30) -> dict:
        """Search and rank knowledge base entries."""
        # Read extractions.jsonl
        # Parse query terms
        # Score and rank results
        # Return top N

# output_generator.py
class OutputGenerator:
    def generate_markdown(self, synthesis: dict, citations: list) -> str:
        """Format AI output as clean markdown with citations."""
        # Build markdown structure
        # Add citations section
        # Save to file
````

### **AI Handles** (Intelligence)

```python
# synthesis_engine.py
class SynthesisEngine:
    async def synthesize(self, knowledge: dict, query: str, mode: str) -> str:
        """Use OpenAI Responses API to synthesize knowledge."""
        # Build prompt from template
        # Call Responses API
        # Parse response
        # Return synthesis

    async def analyze(self, knowledge: dict, query: str) -> dict:
        """Stage 1: Analyze knowledge and plan structure."""

    async def augment(self, gaps: list) -> dict:
        """Stage 2: Web search to fill gaps."""

    async def generate(self, context: dict, query: str) -> str:
        """Stage 3: Generate final output."""
```

---

## Key Design Decisions

### **1. Two Modes (Research + Code)**

**Rationale:**

- Research mode is general-purpose (handles Q&A, reports, exploration, synthesis)
- Code mode is specialized for technical patterns
- Simpler than 6 modes, covers all use cases
- Clear user expectations

**Trade-off:** Less specificity but more flexibility

---

### **2. Markdown Files (Not Stdout)**

**Rationale:**

- Persistent, referenceable outputs
- Easy to share, edit, incorporate into other tools
- Citations preserved for follow-up reading
- Session history maintains research trail

**Trade-off:** Requires opening files vs immediate console output

---

### **3. OpenAI Responses API (Not Completions)**

**Rationale:**

- Modern, stateful API (released March 2025)
- Built-in web search tool
- Better state management across turns
- 40-80% better cache utilization
- Designed for agentic workflows

**Critical:** Use gpt-4o (not GPT-5 yet due to web_search compatibility issues)

**Trade-off:** Requires OpenAI API key (not Claude), but gains web search capability

---

### **4. Multi-Stage for Deep Mode**

**Rationale:**

- blog_writer proves multi-stage produces better quality
- Stage 1: Understand what we have (analysis)
- Stage 2: Fill gaps (augmentation)
- Stage 3: Synthesize everything (generation)
- Focused prompts > one giant prompt

**Trade-off:** Complexity and time (2-3 min vs 30 sec) but higher quality

---

### **5. Web Search in Stage 2 Only**

**Rationale:**

- Stage 1 identifies WHAT to search for (targeted)
- Unfocused web search = noise and cost
- Local knowledge already comprehensive
- Web search fills specific gaps

**Trade-off:** Won't get web info if stage 1 doesn't identify gaps

---

## Open Questions & Discussion Points

### **1. Model Selection**

**Current Plan:** Use `gpt-4o` due to GPT-5 web_search compatibility issues

**Options:**

- Start with gpt-4o, migrate to GPT-5 when compatible
- Fallback chain: Try GPT-5, fall back to gpt-4o on error
- Make model configurable via CLI parameter

**Question:** Which approach do you prefer?

---

### **2. Web Search Triggering**

**Current Plan:** Auto-detect temporal/comparative terms, or explicit flag

**Options:**

- Always enable (might add noise/cost)
- Never enable by default (user must request)
- Smart auto-detection (current plan)
- Ask user interactively

**Question:** Is auto-detection sufficient or too clever?

---

### **3. Quick vs Deep Default**

**Current Plan:** Quick mode is default (fast, good enough for most)

**Options:**

- Deep by default (better quality, slower)
- Quick by default (faster, user can opt into deep)
- Auto-detect based on query complexity

**Question:** What should the default be?

---

### **4. Output Location**

**Current Plan:** Auto-generated session directory under `.data/knowledge_assist/sessions/`

**Options:**

- Auto-generated (current plan)
- Always prompt user for location
- Allow OUTPUT parameter to override
- Save to current directory

**Question:** Is auto-location with OUTPUT override the right balance?

---

### **5. Citation Format**

**Current Plan:** Separate citations section at end of report

**Options:**

- Inline citations (like academic papers) - [1], [2]
- Footnotes at end
- Separate citations section (current)
- Both inline and end section

**Question:** What's most useful for your workflow?

---

### **6. Phase Approach**

**Current Plan:** Build MVP (Phase 1), then iterate based on usage

**Options:**

- Build everything upfront (might over-engineer)
- MVP first, validate, then expand (current plan)
- Research mode only, add code mode later

**Question:** Should we start with full implementation or MVP first?

---

## Success Criteria

Tool is successful if:

- ✅ Answering a question is faster than manual search
- ✅ Citations let you verify and explore deeper
- ✅ Outputs are useful inputs to other work (blogs, coding, research)
- ✅ Web search genuinely improves quality (not just noise)
- ✅ You actually use it regularly

---

## Next Steps

1. **Review & Refine:** Discuss this spec, adjust based on your feedback
2. **API Setup:** Verify OpenAI API access and key configuration
3. **Create Branch:** Start implementation on feature branch
4. **Phase 1 Implementation:** Build MVP (research quick mode only)
5. **Validate:** Test with real queries, assess quality
6. **Iterate:** Add deep mode, code mode based on learnings

---

## Technical Notes

**Dependencies:**

- `openai` package (Responses API client)
- `click` for CLI
- Standard library for file I/O, JSON parsing
- Existing knowledge base at `.data/knowledge/extractions.jsonl`

**Configuration:**

```python
# config.py
from pydantic_settings import BaseSettings

class KnowledgeAssistConfig(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str  # From OPENAI_API_KEY env var or .env
    model: str = "gpt-4o"  # Switch to "gpt-5" when web_search compatible

    # Retrieval Limits
    max_concepts: int = 30
    max_relationships: int = 50
    max_insights: int = 20
    max_patterns: int = 15

    # Timeouts
    synthesis_timeout: int = 60  # MVP: 60s for quick mode

    # Web Search
    web_search_auto: bool = True  # Auto-detect temporal terms

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

**Citation Strategy:**

- Web sources: Track all URLs from web_search tool
- Local knowledge: Track article IDs where concepts/patterns found
- Output format: Single "Citations" section at end of markdown
- In-text: Mention concepts by name on FIRST reference only (no inline [1] markers)
- Purpose: Enable user to verify and explore deeper, not academic rigor

**Error Handling:**

- OpenAI API failures → log error, save partial progress, exit gracefully
- Web search failures → continue with local knowledge only, note in output
- Empty knowledge retrieval → warn user, still attempt web search
- Invalid TOPIC parameter → error with helpful message

---

## Ready for Implementation

All decisions finalized based on user feedback. Specification complete for MVP (Phase 1: Research Quick Mode).

**Next step:** Create feature branch and begin implementation.
