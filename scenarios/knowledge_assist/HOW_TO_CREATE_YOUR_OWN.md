# How to Create Your Own Tool Like This

**You don't need to code. You just need to describe your thinking process.**

This document shows how Knowledge Assistant was created through simple conversations, so you can build powerful tools the same way.

## What the Creator Did

The person who created this tool didn't write code. Here's what they actually did:

### Step 1: Described What They Wanted

They started a conversation with Amplifier and described their goal:

> *"I want to generate research papers from my knowledge base. I have hundreds of articles saved, and I want to query them and get comprehensive reports with proper citations."*

The thinking process was straightforward:
1. "Search the knowledge base for relevant content"
2. "Synthesize the findings into a cohesive report"
3. "Include citations to source materials"
4. "Support both quick summaries and deep analysis"

That's it. No technical specifications, no architecture diagrams, just a clear description of the desired workflow.

### Step 2: Let Amplifier Build the MVP

Amplifier took this description and:
- Created the core retrieval system
- Built the synthesis engine with OpenAI
- Added citation tracking
- Implemented session management
- Built the CLI interface

**First working version ready to test.**

### Step 3: Iterated Through Real Use

The tool evolved as issues were discovered:

**Example: Citations weren't clear**
- Problem: Citations were just dumped at the end
- Described fix: "Add inline [1], [2] markers like academic papers"
- Amplifier implemented it

**Example: Needed deeper analysis**
- Described: "For important research, run three stages: analyze themes, augment with web search, then generate"
- Amplifier built the 3-stage pipeline

**Example: Results weren't relevant**
- Described: "Phrase matches should score higher than individual words"
- Amplifier implemented phrase-based relevance scoring

**Example: Wanted technical patterns**
- Described: "Generate pattern catalogs with code examples and decision matrices"
- Amplifier created code mode

### Step 4: Refined Until It Worked

Each iteration followed the same pattern:
1. Use the tool
2. Notice something that could be better
3. Describe what you want
4. Amplifier implements it
5. Test again

## What Actually Happened

### The Real Process

1. **Human described the need** - In natural language, not code
2. **Human outlined the thinking** - How should the tool approach the problem?
3. **Amplifier built it** - Using specialized agents for architecture and implementation
4. **Human tested and provided feedback** - "This doesn't work right" or "Can we add X?"
5. **Amplifier iterated** - Fixed issues, added features, improved quality

### The Human Didn't Need to Know

- How to implement async/await patterns
- How to structure a Python package
- How to handle file I/O with retries
- How to integrate with OpenAI's API
- How to manage session state
- Which libraries to use for what

### What the Human Did Provide

- **Clear problem description**: "I need to research topics from my knowledge base"
- **Thinking process**: "Search → Retrieve → Synthesize → Format → Output"
- **Quality feedback**: "Citations aren't clear enough"
- **Feature ideas**: "Add web search for current information"
- **Iteration guidance**: "Make deep mode resumable"

## How You Can Create Your Own Tool

### 1. Start with a Real Need

Ask yourself:
- What task do I do repeatedly?
- What process could be automated?
- What would save me significant time?

**Examples that led to real tools:**
- "I need to write blog posts from rough notes" → Blog Writer
- "I need illustrations for my articles" → Article Illustrator
- "I need to review code for security issues" → Security Reviewer

### 2. Describe Your Thinking Process

Not the implementation, but how YOU think about the problem:

**Good examples:**
- "First I search for relevant information, then I identify patterns, then I synthesize conclusions"
- "I read the article, identify key sections, create image descriptions, generate images"
- "I analyze code, look for security patterns, check against best practices, generate report"

**Bad examples:**
- "Use SQLite to store data" (too technical)
- "Create a class hierarchy for..." (implementation detail)
- "Make it fast" (too vague)

### 3. Start the Conversation

```bash
claude
```

Then describe your tool:

```
I need a tool that [describes goal].

The thinking process should be:
1. [First step in your mental process]
2. [Second step]
3. [Third step]
...

For example, given [input example], it should [expected behavior].
```

### 4. Iterate Based on Testing

When you try the tool:
- "The output isn't formatted well"
- "It's missing important information"
- "This edge case breaks it"
- "Could it also do X?"

Just describe the issue naturally. Amplifier will fix it.

### 5. Let It Evolve

Knowledge Assistant didn't become powerful overnight. It evolved:
- **MVP**: Basic search and synthesis
- **Version 2**: Deep mode with stages
- **Version 3**: Web search integration
- **Version 4**: Code pattern generation
- **Version 5**: Improved relevance scoring

Each iteration came from describing what was missing.

## Real Examples from Knowledge Assistant Evolution

### Example 1: Adding Resume Capability

**Human said**: "Deep mode takes a while. If it fails partway through, we lose everything. Can we make it resumable?"

**Amplifier implemented**:
```python
# Automatic checkpoint after each stage
self._save_checkpoint(stage="analysis", data=analysis_results)

# Resume from saved state
if resume_session:
    state = self._load_checkpoint(session_id)
    continue_from_stage(state.last_completed_stage)
```

**Human didn't write any code.**

### Example 2: Web Search Integration

**Human said**: "When someone asks about 'latest updates', we should search the web since local knowledge might be outdated."

**Amplifier implemented**:
- Temporal term detection regex
- Responses API integration
- Citation merging logic
- Seamless blending in prompts

**Human just described the need.**

### Example 3: Better Relevance Scoring

**Human said**: "Single word matching isn't good enough. 'authentication patterns' should match documents containing that exact phrase better than documents with just 'authentication' or just 'patterns'."

**Amplifier implemented**:
- Phrase extraction and matching
- Weighted scoring algorithm
- Multi-level relevance calculation

**Human provided the insight, not the code.**

## Key Lessons Learned

### 1. Start Simple, Evolve Naturally

The MVP had just:
- Basic search
- Simple synthesis
- Basic output

Everything else came from real usage and feedback.

### 2. Describe Problems, Not Solutions

Say "results aren't relevant enough" not "implement TF-IDF scoring."
Say "needs current information" not "integrate with search API."

### 3. Trust the Process

Amplifier handles:
- Architecture decisions
- Library selection
- Error handling
- Performance optimization
- Code quality

You handle:
- Defining the need
- Describing the workflow
- Testing and feedback
- Deciding what's good enough

### 4. Iteration Is Power

Knowledge Assistant improved through multiple iterations:
- Each added a small improvement
- Each was driven by actual usage
- Each built on previous work

## Your Turn

Ready to create your own tool? Here's your checklist:

1. **Identify a repetitive task** you do regularly
2. **Write down your thinking process** step by step
3. **Describe it to Amplifier** in natural language
4. **Test the first version** with real data
5. **Iterate based on what you learn**

Remember: The best tools come from real needs, not imagined ones. Knowledge Assistant exists because someone had 376 articles and needed a better way to use them. What's your 376 articles?

## Share Back

If you create something useful:
1. Document what it does (like our README)
2. Document how you created it (like this file)
3. Consider contributing to scenarios/

The best part? The next person can learn from your tool and create something even better.

---

**The meta-lesson**: This entire tool came from describing a thinking process, not writing code. The power isn't in the AI's code generation—it's in your ability to clearly describe how you think about a problem. That's the real magic.