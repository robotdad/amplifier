# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Parallel Explorer was created through collaborative conversation, so you can create similar tools using the same approach.

## What the Creator Did

The person who "created" this tool didn't write the implementation code. Here's what they actually did:

### Step 1: Found Inspiration and Asked Questions

They discovered an external tool doing something interesting and started with **questions, not requirements**:

> "I like this idea of spinning up multiple worktrees to explore alternate approaches. How is this providing variations from a single idea right now? How might we add this to amplifier?"

**Critical constraint:** "We aren't ready to start implementing yet, let's understand more about how this works right now"

This is the **analysis-first** mindset: understand before building.

### Step 2: Described the Thinking Process

Instead of specifying implementation details, they described **how the tool should think**:

> *"I want to explore multiple implementation approaches in parallel."*
>
> *"The tool should create separate worktrees for each approach, so they can be developed independently."*
>
> *"Each variant should get a clear description of what makes it different - functional vs OOP, simple vs robust, etc."*
>
> *"After implementations are complete, I want to compare them side-by-side to understand trade-offs empirically, not theoretically."*
>
> *"The goal is learning, not finding a 'winner'. Every approach teaches something valuable."*

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 3: Collaborative Design Process

Amplifier helped think through the design using specialized agents:

**Phase 1: Architecture Analysis**
- Used `zen-architect` to analyze the external tool's approach
- Evaluated how it fit with amplifier's existing patterns
- Identified what could be simplified while preserving value

**Phase 2: Path Evaluation**
- Designed three distinct architectural approaches
- Evaluated trade-offs for each path
- Chose based on philosophy alignment, not just features

**Phase 3: Implementation**
- Used `modular-builder` to implement following the chosen design
- Created clean "bricks and studs" architecture
- ~700 lines of working code generated

**Phase 4: Iterative Refinement**
- First refactor: **Removed 70 lines** of unnecessary complexity
- Second refactor: Enhanced with richer context system
- Third refactor: Bug fixes and stability improvements

**Phase 5: Architectural Redesign** (The Big Learning)
- Discovered fundamental flaw: CCSDK was being misused for autonomous building
- zen-architect assessment: "Philosophy alignment 3/10, current path NOT viable"
- Complete rebuild following "code for structure, AI for intelligence"
- Added 4 new modules (**+1,150 lines**): pattern_analyzer, content_generator, tool_builder, structure_validator
- Fixed to use proper amplifier CLI patterns (Python orchestrates, CCSDK generates content)
- Added full quality control (make check + pyright type validation)

**Total time:** Initial design and implementation in one session, three refinement cycles, then one complete architectural redesign when testing revealed the original approach fundamentally didn't work.

**The creator didn't need to know:**
- How to manage git worktrees programmatically
- How to orchestrate multiple Claude Code sessions
- How to implement async/await coordination
- How to structure the data directory
- How to load and merge context files
- How to track experiment progress

### Step 4: Embodied the Philosophy

Every decision was guided by principles from @IMPLEMENTATION_PHILOSOPHY.md and @MODULAR_DESIGN_PHILOSOPHY.md:

- **Ruthless simplicity**: Start with 80/20 solution, iterate toward minimal
- **Modular design**: Clear bricks (worktree manager, orchestrator) with clean interfaces
- **Analysis first**: Deep understanding before any code was written
- **Embrace iteration**: Expect to simplify after learning

The tool wasn't "done" after first implementation - it **evolved** through multiple refinement cycles toward better philosophy alignment.

## How You Can Create Your Own Tool

### 1. Start with Questions, Not Requirements

Ask yourself:
- What existing pattern or tool inspired me?
- How does it work? What's the core value?
- How might this fit with what I already have?
- **Should I even build this?**

**Good starting points:**
- "I saw this tool that does X. How might we adapt that idea?"
- "What if we could Y? How would that work?"
- "This problem keeps coming up. What would a tool look like?"

**Avoid:**
- "Build me exactly this with these features"
- "Use this library to implement X"
- Starting with implementation details

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**The Parallel Explorer's metacognitive recipe:**
1. **Identify variations** - What fundamentally different approaches exist?
2. **Create isolation** - Give each approach space to develop naturally
3. **Execute in parallel** - Let multiple paths explore simultaneously
4. **Compare empirically** - Look at actual implementations, not theories
5. **Learn from differences** - What worked? What didn't? Why?

**Your recipe might be:**
- "First understand X, then create Y based on what you learned"
- "Gather data from sources A, B, C, then synthesize patterns"
- "Compare approaches D and E, document trade-offs"

### 3. Engage in Collaborative Design

Start a conversation with Claude Code describing your goal and thinking process:

**Example from Parallel Explorer:**
```
I like this idea of spinning up multiple worktrees to explore alternate
approaches. How is this providing variations from a single idea right now?
How might we add this to amplifier?

We aren't ready to start implementing yet, let's understand more about
how this works right now.
```

The conversation will naturally involve:
- **zen-architect** - Analyzing the problem and designing the approach
- **amplifier-cli-architect** - Understanding CLI tool patterns
- **modular-builder** - Implementing the design
- **bug-hunter** - Finding and fixing issues in iterations

### 4. Evaluate Multiple Paths

Don't jump to the first solution. Design 2-3 distinct approaches and compare:

**Parallel Explorer evaluated:**
1. **Full SDK automation** - Fully automated but slash command content might be stale
2. **Semi-automated CLI** - Simple but requires manual launch
3. **Hybrid approach** - Balance automation with fresh content (SELECTED)

**The decision criteria:**
- Philosophy alignment (ruthless simplicity)
- Integration with existing patterns
- Maintenance burden
- Value delivered vs complexity added

### 5. Iterate Ruthlessly

The tool will evolve through refinement cycles:

**Parallel Explorer's journey:**
- Initial: 700 lines, working but complex
- Refactor 1: -70 lines, simplified significantly
- Refactor 2: Enhanced with richer context
- Refactor 3: Bug fixes and stability
- **Refactor 4: Complete redesign** - Discovered it didn't actually work, rebuilt from scratch following proper amplifier patterns (+1,150 lines but correct architecture)

Each cycle made it **better aligned** with principles. Sometimes that means getting simpler (refactor 1), sometimes it means rebuilding from scratch when you discover a fundamental flaw (refactor 4).

### 6. Let Philosophy Guide You

Use these questions at every decision point:

1. **Necessity**: "Do we actually need this right now?"
2. **Simplicity**: "What's the simplest way to solve this?"
3. **Directness**: "Can we solve this more directly?"
4. **Value**: "Does the complexity add proportional value?"
5. **Maintenance**: "How easy will this be to understand and change later?"

These questions come from @IMPLEMENTATION_PHILOSOPHY.md and should be your North Star.

## Real Examples: Similar Tool Ideas

Tools that follow the same collaborative creation pattern:

### Beginner-Friendly

**Approach Comparison Evaluator**
- **What it does**: Compares two implementations and documents trade-offs
- **The recipe**: Build variant A → Build variant B → Compare systematically → Document learnings
- **Why it's good**: Simpler than parallel exploration, teaches comparison thinking

**Code Style Variant Generator**
- **What it does**: Generates same functionality in different coding styles
- **The recipe**: Identify styles → Generate variants → Compare readability/maintainability
- **Why it's good**: Concrete comparison of subjective preferences

### Intermediate

**Architecture Pattern Explorer**
- **What it does**: Implements same feature with different architectural patterns
- **The recipe**: Identify patterns → Build each → Compare complexity/flexibility
- **Why it's good**: Makes architectural trade-offs visible through real code

**Performance Variant Tester**
- **What it does**: Generates performance-focused variants and benchmarks them
- **The recipe**: Generate variants → Run benchmarks → Profile bottlenecks → Document findings
- **Why it's good**: Empirical performance comparison, not guesswork

### Advanced

**Multi-Dimension Exploration Matrix**
- **What it does**: Explores multiple dimensions simultaneously (paradigm × complexity × architecture)
- **The recipe**: Define dimensions → Generate matrix of variants → Compare across dimensions
- **Why it's good**: Reveals interactions between choices

**Evolutionary Code Refinement**
- **What it does**: Iteratively refines code through multiple generations, keeping best traits
- **The recipe**: Initial variants → Evaluate quality → Combine best → Mutate → Repeat
- **Why it's good**: Discovers solutions you wouldn't design upfront

## The Key Principles

### 1. You Describe, Amplifier Builds

You need to know:
- What problem you're solving
- How to think through the problem
- What good looks like

You don't need to know how to implement it.

### 2. Metacognitive Recipes Are Powerful

A clear thinking process is all you need:
- "First do A, then B based on what A revealed"
- "Compare X and Y to understand trade-offs"
- "Iterate until criteria Z is met"

The Parallel Explorer's recipe: **Isolate → Execute → Compare → Learn**

### 3. Philosophy as North Star

Every tool should embody:
- **Ruthless simplicity** - Start minimal, remove what doesn't serve
- **Modular design** - Clear bricks with clean interfaces
- **Analysis first** - Understand before building
- **Trust emergence** - Good architecture emerges from simplicity

These aren't suggestions - they're decision criteria.

### 4. Iteration Is Expected

Your first version won't be the final version. That's good!

- First pass: Get it working, prove value
- Second pass: Simplify ruthlessly based on learning
- Third pass: Enhance what matters, remove what doesn't
- Fourth pass: Polish and stabilize

The Parallel Explorer got **simpler** with each iteration, not more complex.

### 5. The Creation Story IS Documentation

The journey of creating the tool teaches as much as the tool itself:
- What questions were asked?
- What approaches were considered?
- Why was this path chosen?
- What was learned through iteration?

This document exists because **how you think about creating tools** is as valuable as the tools themselves.

## Getting Started

1. **Find inspiration** - What problem or pattern sparked your interest?
2. **Ask questions** - How does it work? How might it fit? Should we build it?
3. **Describe thinking** - How should the tool approach the problem?
4. **Start conversation** - Begin a conversation with Claude Code describing your goal
5. **Evaluate paths** - Design multiple approaches, choose deliberately
6. **Iterate ruthlessly** - Simplify after learning, remove what doesn't serve
7. **Share learning** - Document the journey so others can learn your approach

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand the problem domain and be able to describe a thinking process. Amplifier handles implementation.

**Q: How long does it take?**
A: The Parallel Explorer took one deep conversation session for initial design and implementation, then three refinement cycles over a few days.

**Q: What if I don't know how to describe the thinking process?**
A: Start with: "I want a tool that does X. It should first do A, then B, then C." The conversation will help you refine from there.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed and let Amplifier update it. These tools follow "describe and regenerate" rather than "edit line by line."

**Q: How do I know if my idea needs a tool?**
A: Ask yourself:
- Does this involve processing many items with AI?
- Would this be useful repeatedly?
- Is the thinking process clear but tedious to execute manually?
- Would offloading this to a tool free up mental space for higher-level work?

If you answer "yes" to 2+, consider building a tool.

**Q: What if my tool idea is too complex?**
A: Start with the 80/20 version. Build the simplest thing that delivers value. Add complexity only after proving the core value and learning from real use.

## Advanced Pattern: The "Understand First" Approach

The Parallel Explorer demonstrates a powerful pattern:

1. **Encounter interesting idea** (external tool doing parallel exploration)
2. **Request analysis, not implementation** ("understand how this works")
3. **Use zen-architect** to analyze architecture and philosophy
4. **Design multiple paths** (three distinct approaches)
5. **Evaluate deliberately** (trade-offs against principles)
6. **Implement chosen path** (modular-builder generates code)
7. **Iterate toward simplicity** (multiple refinement cycles)

This pattern works for ANY complex tool creation:
- Start with questions, not answers
- Analyze before building
- Design multiple approaches
- Choose based on principles
- Implement minimally
- Refine ruthlessly

## Next Steps

- **Study the parallel explorer tool** to see the principles in action
- **Brainstorm your own tool ideas** - what would make your work easier?
- **Start a conversation** with Claude Code describing your idea and thinking process
- **Embrace iteration** - tools improve through refinement cycles
- **Share your creation** so others can learn from your journey

---

**Remember**: The person who created this tool didn't write the code. They described how to think about the problem. You can do the same.

For usage documentation, see the main [README](README.md).
For more examples, study [blog_writer](../blog_writer/) and [article_illustrator](../article_illustrator/) as exemplars.
