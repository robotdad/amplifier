# Create Your Own Parallel Explorations

## What This Shows

How to structure parallel exploration experiments to compare implementation approaches effectively and learn from empirical comparison.

## The Metacognitive Recipe

Parallel exploration follows this thinking process:

1. **Define the core task** - What needs to be implemented?
2. **Identify orthogonal approaches** - What fundamentally different strategies exist?
3. **Let each approach explore fully** - Don't over-constrain, let solutions breathe
4. **Compare real implementations** - Look at actual code and trade-offs
5. **Learn from differences** - What patterns emerged? What worked better?

This is a **metacognitive recipe** - a structured way of thinking about the problem that the tool then executes.

## Real Example: Rate Limiter Exploration

### The Task
"Implement a rate limiter that allows 100 requests per minute per user"

### Identified Approaches
1. **Token Bucket** - Mathematical elegance, handles bursts
2. **Sliding Window** - Most accurate, more complex
3. **Fixed Window** - Simplest, good enough for most cases

### What We Learned
- Token bucket was elegant but had edge cases with concurrent requests
- Sliding window was most accurate but required Redis (operational complexity)
- Fixed window was "good enough" and had minimal dependencies

### The Decision
We chose **Fixed Window** because:
- Matched our actual requirements (no burst handling needed)
- Minimal operational complexity (no Redis)
- Easy to understand and maintain
- Performance was acceptable for our scale

## Common Exploration Patterns

### Paradigm Comparison
```bash
VARIANTS='{
  "functional":"Pure functions with immutable state",
  "oop":"Classes following SOLID principles",
  "procedural":"Simple procedural code"
}'
```

**When to use**: Greenfield projects where architectural approach is undecided

### Complexity Spectrum
```bash
VARIANTS='{
  "minimal":"Absolute simplest that could work",
  "robust":"Production-ready with error handling",
  "optimized":"Performance-optimized implementation"
}'
```

**When to use**: Understanding trade-offs between simplicity and sophistication

### Algorithm Comparison
```bash
VARIANTS='{
  "algorithm-a":"Quicksort approach",
  "algorithm-b":"Merge sort approach",
  "algorithm-c":"Heap sort approach"
}'
```

**When to use**: Comparing algorithmic approaches for performance/clarity

### Architecture Strategies
```bash
VARIANTS='{
  "monolithic":"Single cohesive module",
  "modular":"Separated into clear components",
  "microservices":"Distributed service architecture"
}'
```

**When to use**: System design decisions with architectural implications

## Tips for Effective Exploration

### 1. Make Variations Truly Orthogonal

❌ **Bad (minor tweaks)**:
```bash
VARIANTS='{
  "v1":"Use Redis with 10 second TTL",
  "v2":"Use Redis with 30 second TTL",
  "v3":"Use Redis with 60 second TTL"
}'
```

✅ **Good (fundamental differences)**:
```bash
VARIANTS='{
  "redis":"Distributed cache with Redis",
  "memory":"In-memory cache (single node)",
  "disk":"Persistent disk-based cache"
}'
```

### 2. Start with 2-3 Variants

Don't try to explore 10 approaches at once. Start small:
- 2 variants: Compare two clear alternatives
- 3 variants: Include a middle-ground option
- 4+ variants: Only if approaches are truly distinct

### 3. Let Implementations Breathe

Don't over-constrain the approaches. Give each variant room to implement naturally:

❌ **Over-constrained**:
"Implement using exactly these 3 classes: Cache, Entry, Eviction"

✅ **Appropriate guidance**:
"Implement a cache with LRU eviction"

### 4. Focus on Learning, Not "Winning"

The goal isn't to find the "best" approach. It's to understand trade-offs:
- What was easier to implement?
- What's more maintainable?
- What performs better?
- What has fewer dependencies?
- What's easier to test?

### 5. Review All Results Before Deciding

Don't just pick the first one that works. Review all implementations:
- Read the code
- Compare complexity
- Consider maintainability
- Think about your team's strengths
- Match to your actual needs

## Creating Your Own Exploration

### Step 1: Define Your Task Clearly

Be specific about what needs to be built:

❌ **Vague**: "Make the API faster"
✅ **Clear**: "Implement caching for the /users endpoint with 5-minute TTL"

### Step 2: Identify Orthogonal Approaches

Brainstorm fundamentally different strategies:
- Different paradigms (functional vs OOP)
- Different algorithms (quicksort vs mergesort)
- Different architectures (monolith vs services)
- Different complexity levels (simple vs robust)

### Step 3: Write Clear Variation Descriptions

Each variant should have a clear, specific description:

```bash
VARIANTS='{
  "token-bucket":"Implement using token bucket algorithm with per-user buckets and 60req/min refill rate",
  "sliding-window":"Use sliding window algorithm with Redis sorted sets for precise rate limiting",
  "fixed-window":"Simple fixed window counters with 1-minute buckets"
}'
```

### Step 4: Run the Exploration

```bash
make parallel-explore \
  NAME=descriptive-experiment-name \
  VARIANTS='{ ... }'
```

### Step 4.5: Using Context for Better Results

For richer implementations, use the two-step process:

#### Option A: Interactive Context Creation
```bash
# First, create context with explore-variants
/explore-variants
> Name: rate-limiter
> Task: Implement rate limiting with 100 req/min limit
> Requirements: Must be thread-safe, support multiple users

# This creates .data/parallel_explorer/rate-limiter/context.json

# Then run parallel-explore (will auto-load context)
make parallel-explore NAME="rate-limiter"
```

#### Option B: Manual Context File
Create a `context.json` file:
```json
{
  "task": "Implement rate limiting",
  "requirements": "100 req/min, thread-safe, multi-user",
  "common_context": "API protection for high-traffic service",
  "variants": {
    "token-bucket": {
      "description": "Token bucket algorithm",
      "approach": "Tokens refill at constant rate",
      "focus_areas": ["burst handling", "fairness"]
    }
  },
  "success_criteria": "Accurate limiting, minimal overhead"
}
```

Then run:
```bash
make parallel-explore NAME="rate-limiter" CONTEXT_FILE="context.json"
```

The context system ensures each variant gets comprehensive instructions, resulting in better implementations.

### Step 5: Analyze Results

Review each implementation:
- Navigate to worktrees: `.data/parallel_explorer/{name}/worktrees/{variant}/`
- Read the code
- Compare complexity
- Test if possible
- Document learnings

### Step 6: Document Your Decision

Create a summary of what you learned and why you chose a particular approach. This helps future team members understand the reasoning.

## Advanced Techniques

### Iterative Refinement

Start broad, then narrow:

**Round 1**: Paradigms
```bash
VARIANTS='{"functional":"...", "oop":"...", "procedural":"..."}'
```

**Round 2**: Refine winning approach
```bash
VARIANTS='{"simple-functional":"...", "advanced-functional":"..."}'
```

### Constraint Exploration

Explore under different constraints:

```bash
# No external dependencies
VARIANTS='{"stdlib-only":"Use only Python standard library", ...}'

# Performance-constrained
VARIANTS='{"sub-100ms":"Must respond under 100ms", ...}'
```

### Hybrid Approaches

After seeing results, combine best aspects:

"Token bucket's burst handling + fixed window's simplicity = hybrid approach"

## Common Pitfalls

### 1. Too Similar Variations
Variations must be fundamentally different, not minor tweaks.

### 2. Over-Constraining
Let each approach implement naturally. Don't force them into the same structure.

### 3. Choosing Too Quickly
Review all results before deciding. The "fastest" implementation might not be the best.

### 4. Ignoring Maintainability
Clever code is fun to write but hard to maintain. Consider your team.

### 5. Forgetting Simplicity
The simplest approach that meets requirements is often the best choice.

## Remember

> "The goal of parallel exploration isn't to find the **best** solution.
> It's to understand the **trade-offs** between solutions."

Every approach has pros and cons. Parallel exploration makes those trade-offs visible through real implementations, not theoretical discussions.

## What's Next?

- Try an exploration with your current project
- Start simple (2-3 variants)
- Focus on learning
- Document what you discover
- Share your findings with the team

---

**The power of parallel exploration is in the learning, not just the result.**