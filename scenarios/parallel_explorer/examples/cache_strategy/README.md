# Example: Cache Strategy Exploration

## The Task

Implement a caching layer for frequently accessed user profile data to reduce database load.

## Approaches Explored

### 1. In-Memory Dictionary
**Description**: Simplest possible cache

```python
# Concept: Python dict as cache
# No eviction (rely on bounded size)
# No TTL (update on write)
# Process-local only
```

**Pros**:
- Zero dependencies
- Extremely fast
- Trivial to implement and test

**Cons**:
- No eviction strategy (unbounded growth)
- Not shared across processes
- No TTL support

### 2. LRU with Size Limits
**Description**: Production-ready in-memory cache

```python
# Concept: functools.lru_cache or custom LRU
# Automatic eviction of old entries
# Size-bounded (prevent memory issues)
# Still process-local
```

**Pros**:
- Built-in eviction (LRU)
- Size-bounded (memory safe)
- Still zero external dependencies
- Good for single-process apps

**Cons**:
- Still not distributed
- No cross-process sharing
- Manual cache invalidation needed

### 3. Redis Distributed Cache
**Description**: Distributed caching with Redis

```python
# Concept: Redis as shared cache
# TTL support built-in
# Shared across all processes
# Proper cache invalidation
```

**Pros**:
- Distributed (shared state)
- Built-in TTL
- Scalable
- Industry-standard solution

**Cons**:
- Requires Redis infrastructure
- Network latency on cache hits
- More moving parts
- Operational complexity

## Results

### Implementation Time
- In-Memory Dict: 10 minutes
- LRU with Limits: 30 minutes
- Redis Cache: 2 hours (including setup)

### Performance (hits/second)
- In-Memory Dict: 500,000/sec
- LRU with Limits: 450,000/sec
- Redis Cache: 50,000/sec (network overhead)

### Memory Safety
- In-Memory Dict: ❌ Unbounded growth
- LRU with Limits: ✅ Size-limited
- Redis Cache: ✅ TTL + eviction policies

### Distribution
- In-Memory Dict: ❌ Process-local
- LRU with Limits: ❌ Process-local
- Redis Cache: ✅ Shared across processes

## Decision

We chose **LRU with Size Limits** because:

1. **Our deployment model**: Single-process application (no need for distributed cache)
2. **Performance requirements**: Cache hits need to be ultra-fast
3. **Simplicity**: No external dependencies to manage
4. **Memory safety**: Size limits prevent unbounded growth

We explicitly decided NOT to use Redis because:
- Single process = no need for distributed cache
- 10x performance difference matters for our use case
- Operational simplicity is valuable

## Key Learnings

1. **Don't over-engineer**: Redis is great but unnecessary for single-process apps
2. **Measure what matters**: Network latency killed Redis performance for our use case
3. **Simple is often enough**: LRU + size limits solved 100% of our requirements
4. **Consider operations**: Managing Redis adds ongoing operational burden

## Evolution Path

If we scale to multiple processes:
1. ✅ Start with LRU (we did this)
2. Monitor cache hit rates across processes
3. If misses are problematic, then add Redis
4. Keep LRU as local L1 cache, Redis as L2

This incremental approach means we only add complexity when we need it.

## Command Used

```bash
make parallel-explore \
  NAME=cache-strategy \
  VARIANTS='{
    "dict":"Simple Python dict cache",
    "lru":"LRU cache with size limits",
    "redis":"Distributed Redis cache"
  }'
```

## Experiment Results Location

```
.data/parallel_explorer/cache-strategy/
├── results/
│   ├── dict_progress.json
│   ├── lru_progress.json
│   └── redis_progress.json
└── worktrees/
    ├── dict/
    ├── lru/
    └── redis/
```

---

**Lesson**: Parallel exploration prevented premature optimization. We almost went straight to Redis because "that's what you do for caching" but the empirical comparison showed LRU was perfect for our needs. Saved weeks of Redis operational overhead.
