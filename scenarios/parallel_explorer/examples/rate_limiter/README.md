# Example: Rate Limiter Exploration

## The Task

Implement a rate limiter that allows 100 requests per minute per user.

## Approaches Explored

### 1. Token Bucket
**Description**: Mathematical elegance with token refill

```python
# Concept: Users have a bucket of tokens
# Tokens refill at constant rate (100/minute)
# Each request consumes one token
# Allows natural burst handling
```

**Pros**:
- Handles bursts naturally
- Mathematically elegant
- Well-understood algorithm

**Cons**:
- Edge cases with concurrent access
- Requires atomic operations
- State management complexity

### 2. Sliding Window
**Description**: Most accurate rate limiting with Redis

```python
# Concept: Track exact timestamps in sorted set
# Count requests in last 60 seconds
# Remove old entries on each check
# Precise but complex
```

**Pros**:
- Most accurate rate limiting
- No edge cases with window boundaries
- Distributed-friendly (Redis)

**Cons**:
- Requires Redis (operational complexity)
- More storage per user
- Slower due to sorted set operations

### 3. Fixed Window
**Description**: Simple counter with time buckets

```python
# Concept: Count requests in current minute
# Reset counter at minute boundary
# Simple, fast, mostly accurate
```

**Pros**:
- Extremely simple
- Fast (O(1) operations)
- Minimal dependencies

**Cons**:
- Window boundary edge case (can allow 200 req in 2 seconds)
- Less accurate than sliding window
- Not suitable for strict requirements

## Results

### Implementation Complexity
- Token Bucket: Medium (concurrency handling)
- Sliding Window: High (Redis integration)
- Fixed Window: Low (straightforward counter)

### Operational Complexity
- Token Bucket: Low (in-memory)
- Sliding Window: High (requires Redis cluster)
- Fixed Window: Low (in-memory)

### Accuracy
- Token Bucket: High (with proper locking)
- Sliding Window: Highest (precise timestamps)
- Fixed Window: Medium (window boundary issue)

## Decision

We chose **Fixed Window** because:

1. **Matched our needs**: We don't have strict accuracy requirements
2. **Operational simplicity**: No Redis to manage
3. **Performance**: Fastest implementation (O(1))
4. **Maintainability**: Easy for team to understand

The window boundary edge case was acceptable for our use case (API rate limiting where occasional burst is fine).

## Key Learnings

1. **Simplest != worst**: Fixed window had the "known limitation" but was the best choice for our context
2. **Operational cost matters**: Redis adds significant complexity
3. **Theory vs practice**: Sliding window is "most accurate" but not worth the operational cost
4. **Context is king**: The "best" solution depends entirely on your requirements

## Command Used

```bash
make parallel-explore \
  NAME=rate-limiter-comparison \
  VARIANTS='{
    "token-bucket":"Token bucket algorithm with per-user buckets",
    "sliding-window":"Sliding window with Redis sorted sets",
    "fixed-window":"Simple fixed window counters"
  }'
```

## Experiment Results Location

```
.data/parallel_explorer/rate-limiter-comparison/
├── results/
│   ├── token-bucket_progress.json
│   ├── sliding-window_progress.json
│   └── fixed-window_progress.json
└── worktrees/
    ├── token-bucket/
    ├── sliding-window/
    └── fixed-window/
```

---

**Lesson**: Parallel exploration showed us that the "textbook best" solution (sliding window) wasn't the right choice for our context. The empirical comparison revealed that fixed window's simplicity outweighed its theoretical limitations.
