# Rust Conversion Plan: .NET System.Threading.RateLimiting

**Date**: 2025-01-10
**Status**: Planning Complete - Ready for Implementation

## Executive Summary

This document outlines the complete plan for converting the .NET System.Threading.RateLimiting library (~4,141 lines of C# code) to Rust. The conversion includes 6 limiter types, comprehensive test suite conversion (~360 tests), and follows modular "bricks & studs" design philosophy.

**Key Decisions:**
- ✅ **Convert tests to Rust** (not FFI) - More maintainable, better async support
- ✅ **Use Tokio ecosystem** - Industry standard async runtime
- ✅ **Modular architecture** - Each limiter is independently regeneratable
- ✅ **9-week phased implementation** - Start with simplest components

**Source Code Location**: `/Users/robotdad/Source/runtime/src/libraries/System.Threading.RateLimiting`

---

## Table of Contents

1. [Source Code Analysis](#1-source-code-analysis)
2. [Rust Architecture Design](#2-rust-architecture-design)
3. [C# to Rust Pattern Mappings](#3-c-to-rust-pattern-mappings)
4. [Testing Strategy](#4-testing-strategy)
5. [Implementation Roadmap](#5-implementation-roadmap)
6. [Technical Challenges](#6-technical-challenges)
7. [Risk Assessment](#7-risk-assessment)
8. [Dependencies](#8-dependencies)
9. [Next Actions](#9-next-actions)

---

## 1. Source Code Analysis

### 1.1 Code Statistics

| Metric | Count | Notes |
|--------|-------|-------|
| **C# Source Lines** | ~4,141 | Production code |
| **Test Lines** | ~9,045 | XUnit tests |
| **Test Methods** | ~360 | Comprehensive coverage |
| **Limiter Types** | 6 | TokenBucket, FixedWindow, SlidingWindow, Concurrency, Chained, Partitioned |
| **Test Files** | 9 | Plus infrastructure |

### 1.2 Component Breakdown

#### Core Components

**Base Classes:**
- `RateLimiter` - Abstract base with acquire methods
- `ReplenishingRateLimiter` - Time-based replenishment
- `RateLimitLease` - Acquisition result with metadata
- `PartitionedRateLimiter<T>` - Key-based partitioning

**Concrete Limiters:**
1. **TokenBucketRateLimiter** (~537 lines)
   - Token bucket algorithm
   - Configurable replenishment rate
   - Auto-replenishment with Timer

2. **FixedWindowRateLimiter** (~450 lines)
   - Fixed time window
   - Window boundary handling

3. **SlidingWindowRateLimiter** (~480 lines)
   - Sliding window segments
   - More accurate than fixed window

4. **ConcurrencyLimiter** (~380 lines)
   - Concurrent request limiting
   - No time component (simplest)

5. **ChainedRateLimiter** (~200 lines)
   - Combines multiple limiters
   - Sequential checking

6. **PartitionedRateLimiter** (~350 lines)
   - Key-based limiter instances
   - Dynamic limiter creation

### 1.3 Key Features

- ✅ Synchronous and asynchronous acquisition
- ✅ Queue management (FIFO/LIFO ordering)
- ✅ Cancellation support
- ✅ Statistics tracking
- ✅ Metadata on leases (RetryAfter)
- ✅ Auto-replenishment with timers
- ✅ Thread-safe operations

---

## 2. Rust Architecture Design

### 2.1 Module Structure

```
crates/
└── ratelimit/
    ├── Cargo.toml
    ├── README.md
    ├── src/
    │   ├── lib.rs                    # Public API exports
    │   │
    │   ├── core/
    │   │   ├── mod.rs
    │   │   ├── traits.rs             # RateLimiter, ReplenishingRateLimiter
    │   │   ├── lease.rs              # RateLimitLease
    │   │   ├── statistics.rs         # RateLimiterStatistics
    │   │   ├── metadata.rs           # Metadata types
    │   │   └── error.rs              # Error types
    │   │
    │   ├── limiters/
    │   │   ├── mod.rs
    │   │   ├── token_bucket.rs       # TokenBucketRateLimiter
    │   │   ├── fixed_window.rs       # FixedWindowRateLimiter
    │   │   ├── sliding_window.rs     # SlidingWindowRateLimiter
    │   │   ├── concurrency.rs        # ConcurrencyLimiter
    │   │   └── chained.rs            # ChainedRateLimiter
    │   │
    │   ├── partitioned/
    │   │   ├── mod.rs
    │   │   ├── partitioned.rs        # PartitionedRateLimiter<T>
    │   │   └── partition.rs          # RateLimitPartition
    │   │
    │   ├── queue/
    │   │   ├── mod.rs
    │   │   └── request_queue.rs      # Internal queue with ordering
    │   │
    │   └── utils/
    │       ├── mod.rs
    │       ├── timer.rs              # Replenishment timer utilities
    │       └── cancellation.rs       # Cancellation helpers
    │
    └── tests/
        ├── common/
        │   ├── mod.rs
        │   └── test_utils.rs         # Test helpers (Utils.cs equivalent)
        │
        ├── token_bucket_tests.rs      # ~1,400 lines
        ├── fixed_window_tests.rs      # ~1,200 lines
        ├── sliding_window_tests.rs    # ~1,300 lines
        ├── concurrency_tests.rs       # ~1,000 lines
        ├── partitioned_tests.rs       # ~500 lines
        └── chained_tests.rs           # ~300 lines
```

### 2.2 Core Trait Design

```rust
use async_trait::async_trait;
use std::time::Duration;
use tokio_util::sync::CancellationToken;

/// Main rate limiter trait
#[async_trait]
pub trait RateLimiter: Send + Sync {
    /// Attempt to acquire permits synchronously (non-blocking)
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError>;

    /// Acquire permits asynchronously, with optional cancellation
    async fn acquire_async(
        &self,
        permit_count: u32,
        cancel_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError>;

    /// Get current statistics
    fn get_statistics(&self) -> RateLimiterStatistics;

    /// Get idle duration (for cleanup managers)
    /// Returns None if limiter is active
    fn idle_duration(&self) -> Option<Duration>;
}

/// Trait for limiters with time-based replenishment
#[async_trait]
pub trait ReplenishingRateLimiter: RateLimiter {
    /// Whether auto-replenishment is enabled
    fn is_auto_replenishing(&self) -> bool;

    /// Replenishment period
    fn replenishment_period(&self) -> Duration;

    /// Manually trigger replenishment
    /// Returns false if auto-replenishment is enabled
    fn try_replenish(&self) -> bool;
}

/// Lease representing acquired permits
pub struct RateLimitLease {
    is_acquired: bool,
    metadata: HashMap<String, Box<dyn Any + Send + Sync>>,
    // Cleanup callback for returning permits (ConcurrencyLimiter)
    on_drop: Option<Box<dyn FnOnce() + Send>>,
}

impl Drop for RateLimitLease {
    fn drop(&mut self) {
        if let Some(cleanup) = self.on_drop.take() {
            cleanup();
        }
    }
}

/// Error types
#[derive(Debug, thiserror::Error)]
pub enum RateLimitError {
    #[error("Request was cancelled")]
    Cancelled,

    #[error("Permit count {0} exceeds limiter capacity {1}")]
    PermitCountExceeded(u32, u32),

    #[error("Limiter has been disposed")]
    Disposed,

    #[error("Invalid parameter: {0}")]
    InvalidParameter(String),
}

/// Statistics snapshot
#[derive(Debug, Clone)]
pub struct RateLimiterStatistics {
    pub current_available_permits: i64,
    pub current_queued_count: u32,
    pub total_successful_leases: u64,
    pub total_failed_leases: u64,
}
```

### 2.3 Example Implementation: TokenBucketRateLimiter

```rust
use parking_lot::Mutex;
use std::sync::Arc;
use tokio::time::{interval, Duration, Instant};

pub struct TokenBucketRateLimiter {
    inner: Arc<Mutex<State>>,
    config: TokenBucketOptions,
    cancel_token: CancellationToken,
    _timer_handle: Option<tokio::task::JoinHandle<()>>,
}

struct State {
    available_tokens: f64,
    queue: VecDeque<QueuedRequest>,
    queue_count: u32,
    last_replenishment: Instant,
    idle_since: Option<Instant>,
    successful_leases: AtomicU64,
    failed_leases: AtomicU64,
}

#[derive(Clone)]
pub struct TokenBucketOptions {
    pub token_limit: u32,
    pub tokens_per_period: u32,
    pub replenishment_period: Duration,
    pub queue_limit: u32,
    pub queue_processing_order: QueueProcessingOrder,
    pub auto_replenishment: bool,
}

impl TokenBucketRateLimiter {
    pub fn new(options: TokenBucketOptions) -> Result<Self, RateLimitError> {
        // Validation
        if options.token_limit == 0 {
            return Err(RateLimitError::InvalidParameter(
                "token_limit must be > 0".into()
            ));
        }

        let state = State {
            available_tokens: options.token_limit as f64,
            queue: VecDeque::new(),
            queue_count: 0,
            last_replenishment: Instant::now(),
            idle_since: Some(Instant::now()),
            successful_leases: AtomicU64::new(0),
            failed_leases: AtomicU64::new(0),
        };

        let inner = Arc::new(Mutex::new(state));
        let cancel_token = CancellationToken::new();

        // Start auto-replenishment if enabled
        let timer_handle = if options.auto_replenishment {
            Some(Self::start_replenishment_timer(
                Arc::clone(&inner),
                options.clone(),
                cancel_token.clone(),
            ))
        } else {
            None
        };

        Ok(Self {
            inner,
            config: options,
            cancel_token,
            _timer_handle: timer_handle,
        })
    }

    fn start_replenishment_timer(
        state: Arc<Mutex<State>>,
        config: TokenBucketOptions,
        cancel: CancellationToken,
    ) -> tokio::task::JoinHandle<()> {
        tokio::spawn(async move {
            let mut interval = interval(config.replenishment_period);
            interval.set_missed_tick_behavior(MissedTickBehavior::Delay);

            loop {
                tokio::select! {
                    _ = interval.tick() => {
                        Self::replenish(&state, &config);
                    }
                    _ = cancel.cancelled() => break,
                }
            }
        })
    }

    fn replenish(state: &Arc<Mutex<State>>, config: &TokenBucketOptions) {
        let mut state = state.lock();

        // Add tokens (up to limit)
        state.available_tokens = (state.available_tokens + config.tokens_per_period as f64)
            .min(config.token_limit as f64);

        state.last_replenishment = Instant::now();

        // Process queued requests
        Self::process_queue(&mut state, config);

        // Update idle tracking
        if state.available_tokens >= config.token_limit as f64 {
            state.idle_since = Some(Instant::now());
        }
    }

    fn process_queue(state: &mut State, config: &TokenBucketOptions) {
        while let Some(request) = Self::peek_next(&state.queue, config) {
            if state.available_tokens >= request.permit_count as f64 {
                let request = Self::dequeue_next(&mut state.queue, config).unwrap();
                state.available_tokens -= request.permit_count as f64;
                state.queue_count -= request.permit_count;

                let lease = RateLimitLease::success();
                let _ = request.response.send(Ok(lease));
            } else {
                break;
            }
        }
    }

    /// Explicit async shutdown (call before dropping for graceful cleanup)
    pub async fn shutdown(&self) {
        self.cancel_token.cancel();
        // Timer task will exit on next tick
    }
}

#[async_trait]
impl RateLimiter for TokenBucketRateLimiter {
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError> {
        if permit_count > self.config.token_limit {
            return Err(RateLimitError::PermitCountExceeded(
                permit_count,
                self.config.token_limit,
            ));
        }

        let mut state = self.inner.lock();

        if state.available_tokens >= permit_count as f64
            && (state.queue_count == 0
                || self.config.queue_processing_order == QueueProcessingOrder::NewestFirst)
        {
            state.available_tokens -= permit_count as f64;
            state.idle_since = None;
            state.successful_leases.fetch_add(1, Ordering::Relaxed);
            Ok(RateLimitLease::success())
        } else {
            state.failed_leases.fetch_add(1, Ordering::Relaxed);
            let retry_after = self.calculate_retry_after(&state, permit_count);
            Ok(RateLimitLease::failed(retry_after))
        }
    }

    async fn acquire_async(
        &self,
        permit_count: u32,
        cancel_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError> {
        // Try immediate acquire first
        {
            let mut state = self.inner.lock();
            if self.try_acquire_immediate(&mut state, permit_count) {
                return Ok(RateLimitLease::success());
            }

            // Check queue limit
            if state.queue_count + permit_count > self.config.queue_limit {
                state.failed_leases.fetch_add(1, Ordering::Relaxed);
                let retry_after = self.calculate_retry_after(&state, permit_count);
                return Ok(RateLimitLease::failed(retry_after));
            }

            // Add to queue
            let (tx, rx) = oneshot::channel();
            state.queue.push_back(QueuedRequest {
                permit_count,
                response: tx,
            });
            state.queue_count += permit_count;

            drop(state); // Release lock before awaiting

            // Wait for response or cancellation
            if let Some(cancel) = cancel_token {
                tokio::select! {
                    result = rx => result.map_err(|_| RateLimitError::Disposed)?,
                    _ = cancel.cancelled() => {
                        // Remove from queue, update counts
                        Err(RateLimitError::Cancelled)
                    }
                }
            } else {
                rx.await.map_err(|_| RateLimitError::Disposed)?
            }
        }
    }

    fn get_statistics(&self) -> RateLimiterStatistics {
        let state = self.inner.lock();
        RateLimiterStatistics {
            current_available_permits: state.available_tokens as i64,
            current_queued_count: state.queue_count,
            total_successful_leases: state.successful_leases.load(Ordering::Relaxed),
            total_failed_leases: state.failed_leases.load(Ordering::Relaxed),
        }
    }

    fn idle_duration(&self) -> Option<Duration> {
        let state = self.inner.lock();
        state.idle_since.map(|since| since.elapsed())
    }
}
```

---

## 3. C# to Rust Pattern Mappings

### 3.1 Threading and Async

| C# Pattern | Rust Equivalent | Implementation Notes |
|------------|-----------------|---------------------|
| `async Task<T>` | `async fn() -> T` | Rust futures are lazy, not eagerly executed |
| `ValueTask<T>` | `impl Future<Output = T>` | Zero-cost abstraction via traits |
| `lock (obj) { ... }` | `let guard = mutex.lock();` | RAII automatic unlock on drop |
| `CancellationToken` | `tokio_util::sync::CancellationToken` | Select-based cancellation |
| `Timer` | `tokio::time::interval()` | Async timer streams |
| `Task.Run()` | `tokio::spawn()` | Spawns on runtime executor |
| `Task.Delay()` | `tokio::time::sleep()` | Async sleep |
| `Task.WhenAny()` | `tokio::select!` | Await multiple futures |

### 3.2 Lifetime Management

| C# Pattern | Rust Equivalent | Notes |
|------------|-----------------|-------|
| `IDisposable` | `Drop` trait | Automatic cleanup, no async |
| `IAsyncDisposable` | Explicit `async fn shutdown()` | No async Drop in Rust yet |
| Garbage collection | `Arc<T>` | Reference counting |
| Weak references | `Weak<T>` | For breaking cycles |
| `using var x = ...` | `let x = ...; drop(x)` or scope | RAII cleanup |

### 3.3 Concurrency Primitives

| C# Pattern | Rust Equivalent | Recommendation |
|------------|-----------------|----------------|
| `object` (locking) | `parking_lot::Mutex<T>` | Faster than `std::sync::Mutex` |
| `Interlocked` | `AtomicU64`, `AtomicI64` | Lock-free atomic operations |
| `SemaphoreSlim` | `tokio::sync::Semaphore` | Async-aware semaphore |
| `Queue<T>` | `VecDeque<T>` | Standard Rust collections |
| `ConcurrentQueue<T>` | `crossbeam::queue::SegQueue` | For multi-producer scenarios |

### 3.4 Error Handling

| C# Pattern | Rust Pattern |
|------------|-------------|
| `throw new Exception()` | `return Err(...)` |
| `try { } catch (E e) { }` | `match result { Ok(v) => ..., Err(e) => ... }` |
| `ArgumentException` | `RateLimitError::InvalidParameter` |
| `ObjectDisposedException` | `RateLimitError::Disposed` |
| `TaskCanceledException` | `RateLimitError::Cancelled` |

---

## 4. Testing Strategy

### 4.1 Recommendation: Convert All Tests to Rust

**Decision: Convert ~360 tests to native Rust** rather than attempting FFI-based testing.

**Rationale:**
1. **FFI is impractical for async**: C#'s `async/await` doesn't map across FFI
2. **Better tooling**: Native `cargo test`, rust-analyzer integration
3. **Easier debugging**: Single language, no FFI boundary confusion
4. **Similar effort**: Converting tests (~150 hours) vs building FFI (~200+ hours)
5. **Long-term maintainability**: Evolves with Rust implementation

### 4.2 Test Portability Analysis

**80% - Highly Portable (Direct 1:1 translation)**
- Basic synchronous acquire/release operations
- Parameter validation tests
- Queue behavior (OldestFirst/NewestFirst)
- Statistics tracking
- Integer overflow edge cases

**15% - Moderate Complexity (Idiom adjustments)**
- Async operations with cancellation
- Time-dependent tests (replenishment timing)
- Concurrent execution patterns

**5% - C#-Specific (Need rethinking)**
- Reflection-based internal testing → Use `#[cfg(test)]` visibility
- Runtime type inspection → Use test-only traits

### 4.3 Test Framework Stack

```toml
[dev-dependencies]
tokio = { version = "1.40", features = ["macros", "test-util", "rt-multi-thread"] }
tokio-util = "0.7"
rstest = "0.18"       # Parameterized tests
proptest = "1.4"      # Property-based testing (bonus)
```

#### Basic Tests
```rust
#[test]
fn can_acquire_resource() {
    let limiter = TokenBucketRateLimiter::new(options);
    let lease = limiter.attempt_acquire(1).unwrap();
    assert!(lease.is_acquired());
}
```

#### Async Tests
```rust
#[tokio::test]
async fn can_acquire_async() {
    let limiter = TokenBucketRateLimiter::new(options);
    let lease = limiter.acquire_async(1, None).await.unwrap();
    assert!(lease.is_acquired());
}
```

#### Time-Dependent Tests
```rust
#[tokio::test(start_paused = true)]
async fn auto_replenishment_works() {
    let limiter = TokenBucketRateLimiter::new(options);
    limiter.attempt_acquire(2); // Consume tokens

    // Fast-forward time without real delay
    tokio::time::advance(Duration::from_secs(10)).await;

    assert_eq!(limiter.get_statistics().current_available_permits, 1);
}
```

#### Cancellation Tests
```rust
#[tokio::test]
async fn can_cancel_acquire() {
    let limiter = Arc::new(TokenBucketRateLimiter::new(options));
    let token = CancellationToken::new();

    let task = limiter.acquire_async(1, Some(token.clone()));
    token.cancel();

    assert!(matches!(task.await, Err(RateLimitError::Cancelled)));
}
```

### 4.4 Test Conversion Timeline

| Phase | Duration | Tests | Focus |
|-------|----------|-------|-------|
| **Phase 1** | Week 1 | 10 | Foundation + representative samples |
| **Phase 2** | Week 2 | 140 | Core limiters (TokenBucket, FixedWindow, SlidingWindow) |
| **Phase 3** | Week 3 | 210 | Advanced features (Concurrency, Partitioned, Chained) |

**Total Effort**: ~150 hours (4 weeks full-time)

---

## 5. Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

**Goals:**
- Establish trait contracts
- Implement error types
- Create basic test framework

**Deliverables:**
```
✓ src/core/traits.rs       - RateLimiter, ReplenishingRateLimiter traits
✓ src/core/lease.rs         - RateLimitLease implementation
✓ src/core/error.rs         - RateLimitError types
✓ src/core/statistics.rs    - RateLimiterStatistics
✓ tests/common/test_utils.rs - Test helper utilities
```

**Success Criteria:**
- Traits compile and are well-documented
- Basic test infrastructure works
- Error types cover all scenarios

---

### Phase 2: Simplest Limiter (Week 3)

**Goal:** Implement **ConcurrencyLimiter** to validate design

**Why This First:**
- No time component (simpler than time-based)
- Validates core trait design
- Tests synchronization primitives
- Proves lease cleanup pattern

**Implementation:**
```rust
pub struct ConcurrencyLimiter {
    inner: Arc<Mutex<State>>,
    config: ConcurrencyLimiterOptions,
}

struct State {
    available_permits: u32,
    queue: VecDeque<QueuedRequest>,
    // ... statistics
}
```

**Tests to Port**: ~40 tests from `ConcurrencyLimiterTests.cs`

**Success Criteria:**
- All 40 tests passing
- Sync and async acquire work
- Queue management correct
- Lease drop returns permits

---

### Phase 3: Time-Based Limiters (Week 4-6)

#### Week 4: TokenBucketRateLimiter

**Why This Next:**
- Most commonly used
- Establishes timer patterns
- Complex but well-understood

**Key Challenges:**
- Auto-replenishment timing
- Fill rate calculations
- Token accumulation logic

**Tests to Port**: ~50 tests from `TokenBucketRateLimiterTests.cs`

#### Week 5: FixedWindowRateLimiter

**Implementation Focus:**
- Window boundary handling
- Window reset logic
- Simpler than TokenBucket (good validation)

**Tests to Port**: ~45 tests

#### Week 6: SlidingWindowRateLimiter

**Implementation Focus:**
- Window segment tracking
- Time-based segment expiration
- Most complex time-based logic

**Tests to Port**: ~48 tests

---

### Phase 4: Composition Patterns (Week 7-8)

#### ChainedRateLimiter

**Implementation:**
```rust
pub struct ChainedRateLimiter {
    limiters: Vec<Box<dyn RateLimiter>>,
}

impl RateLimiter for ChainedRateLimiter {
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError> {
        let mut leases = Vec::new();
        for limiter in &self.limiters {
            match limiter.attempt_acquire(permit_count) {
                Ok(lease) if lease.is_acquired() => leases.push(lease),
                result => return result, // First failure fails entire chain
            }
        }
        Ok(CombinedLease::new(leases))
    }
}
```

**Tests to Port**: ~20 tests

#### PartitionedRateLimiter

**Implementation:**
```rust
pub struct PartitionedRateLimiter<TKey: Hash + Eq> {
    partitions: Arc<Mutex<HashMap<TKey, Box<dyn RateLimiter>>>>,
    factory: Box<dyn Fn(&TKey) -> Box<dyn RateLimiter> + Send + Sync>,
}
```

**Tests to Port**: ~25 tests

---

### Phase 5: Polish & Documentation (Week 9)

**Deliverables:**
- ✅ API documentation (rustdoc)
- ✅ Usage examples
- ✅ README.md
- ✅ Integration tests
- ✅ Performance benchmarks (optional)
- ✅ Migration guide (C# → Rust patterns)

---

## 6. Technical Challenges

### Challenge 1: No Async Drop in Rust

**Problem:**
```csharp
// C# - async disposal works
public async ValueTask DisposeAsync() {
    await _renewTimer?.DisposeAsync();
}
```

**Rust Solution:**
```rust
impl TokenBucketRateLimiter {
    /// Explicit async shutdown (call before dropping)
    pub async fn shutdown(&self) {
        self.cancel_token.cancel();
        if let Some(handle) = self.timer_handle.lock().take() {
            handle.await.ok();
        }
    }
}

impl Drop for TokenBucketRateLimiter {
    fn drop(&mut self) {
        // Synchronous cleanup only
        self.cancel_token.cancel();
        // Timer task exits on next tick
    }
}
```

**Best Practice:** Document that `shutdown()` should be called for graceful cleanup

---

### Challenge 2: Timer Precision and Jitter

**C# Approach**: `Stopwatch` for high precision, configurable jitter handling

**Rust Solution:**
```rust
use tokio::time::{interval, MissedTickBehavior};

let mut interval = interval(replenishment_period);
interval.set_missed_tick_behavior(MissedTickBehavior::Delay);

loop {
    tokio::select! {
        _ = interval.tick() => {
            replenish();
        }
        _ = cancel_token.cancelled() => break,
    }
}
```

**Test Strategy:** Use `#[tokio::test(start_paused = true)]` to control time

---

### Challenge 3: Queue Cancellation Complexity

**Problem:** Cancellation can race with replenishment

**Solution Pattern:**
```rust
struct QueuedRequest {
    permit_count: u32,
    response: oneshot::Sender<Result<RateLimitLease, RateLimitError>>,
}

// In acquire_async:
let (tx, rx) = oneshot::channel();
{
    let mut state = lock.lock();
    state.queue.push_back(QueuedRequest { permit_count, response: tx });
    state.queue_count += permit_count;
}

tokio::select! {
    result = rx => result?,
    _ = cancel_token.cancelled() => {
        // Remove from queue, update counts
        let mut state = lock.lock();
        // Find and remove request
        Err(RateLimitError::Cancelled)
    }
}
```

**Key:** Ensure queue count stays consistent during concurrent cancel/replenish

---

### Challenge 4: Thread Safety Patterns

**State Management:**
```rust
pub struct TokenBucketRateLimiter {
    inner: Arc<Mutex<State>>,        // Shared mutable state
    config: TokenBucketOptions,       // Immutable config (Clone)
    cancel_token: CancellationToken,  // Thread-safe cancel
}
```

**Lock Strategy:**
- Use `parking_lot::Mutex` for performance (no poisoning)
- Minimize critical sections
- Release locks before `.await` points
- Use atomic counters for statistics

---

## 7. Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Async lifetime complexity | Medium | High | Use `Arc` liberally, avoid complex lifetimes |
| Timer precision issues | Low | Medium | Comprehensive time tests with `tokio::time` |
| Test conversion errors | Medium | High | Port tests alongside implementation, verify behavior |
| Cancellation race conditions | Medium | High | Extensive cancellation tests, careful queue management |

### Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Underestimated complexity | Medium | Medium | Phased approach, 2-week contingency buffer |
| Rust learning curve | Low | Medium | Start with simplest components, thorough documentation |
| Test conversion delays | Low | Low | Tests are well-structured, mostly 1:1 portable |

---

## 8. Dependencies

### Required Crates

```toml
[dependencies]
tokio = { version = "1.40", features = ["sync", "time", "rt-multi-thread"] }
tokio-util = { version = "0.7", features = ["time"] }
async-trait = "0.1"
parking_lot = "0.12"
thiserror = "1.0"
futures = "0.3"

[dev-dependencies]
tokio = { version = "1.40", features = ["macros", "test-util"] }
rstest = "0.18"
proptest = "1.4"  # Optional: property-based testing
criterion = "0.5" # Optional: benchmarking
```

### Crate Justifications

| Crate | Purpose | Why This One |
|-------|---------|-------------|
| `tokio` | Async runtime | Industry standard, excellent timer support |
| `async-trait` | Async methods in traits | Required for trait-based async |
| `parking_lot` | Fast mutex | Faster than std, no poisoning |
| `tokio-util` | Cancellation tokens | Select-compatible cancellation |
| `thiserror` | Error handling | Reduces boilerplate |
| `rstest` | Parameterized tests | Cleaner than manual loops |

---

## 9. Next Actions

### Immediate Steps (This Week)

1. **✅ Create this planning document**
2. **Initialize Rust project**
   ```bash
   cd /Users/robotdad/Source/amplifier.ratelimiting
   cargo new --lib ratelimit
   cd ratelimit
   ```

3. **Set up Cargo.toml**
   - Add all required dependencies
   - Configure workspace if needed

4. **Create module structure**
   ```bash
   mkdir -p src/{core,limiters,partitioned,queue,utils}
   mkdir -p tests/common
   ```

5. **Implement Phase 1: Core Infrastructure**
   - Define `RateLimiter` and `ReplenishingRateLimiter` traits
   - Implement `RateLimitLease`
   - Create error types
   - Write first 10 tests

### Week 1 Milestones

- [ ] Project initialized with dependencies
- [ ] Core traits defined and documented
- [ ] `RateLimitLease` implemented
- [ ] Error types complete
- [ ] 10 representative tests passing

### Week 2-3: First Working Limiter

- [ ] `ConcurrencyLimiter` fully implemented
- [ ] 40 tests converted and passing
- [ ] Lease cleanup pattern validated
- [ ] Architecture reviewed

### Success Criteria for Phase 1

1. **Code compiles cleanly**
2. **All tests pass** (`cargo test`)
3. **Documentation complete** (`cargo doc`)
4. **Linting clean** (`cargo clippy`)
5. **Formatting consistent** (`cargo fmt`)

---

## Appendix A: File Locations

### Source Files
- **C# Source**: `/Users/robotdad/Source/runtime/src/libraries/System.Threading.RateLimiting/src/`
- **C# Tests**: `/Users/robotdad/Source/runtime/src/libraries/System.Threading.RateLimiting/tests/`

### Rust Project
- **Project Root**: `/Users/robotdad/Source/amplifier.ratelimiting/ratelimit/`
- **Source**: `src/`
- **Tests**: `tests/`

---

## Appendix B: Key C# Files to Reference

| File | Lines | Purpose |
|------|-------|---------|
| `RateLimiter.cs` | 160 | Base class with acquire methods |
| `RateLimitLease.cs` | 90 | Lease abstraction |
| `TokenBucketRateLimiter.cs` | 537 | Reference implementation |
| `TokenBucketRateLimiterTests.cs` | 1,465 | Comprehensive test examples |

---

## Appendix C: Test Conversion Checklist Template

For each C# test file, track:

```markdown
## TokenBucketRateLimiterTests.cs

- [x] Test count identified: 50
- [x] Async patterns analyzed
- [x] Reflection usage documented
- [ ] Rust test file created
- [ ] Tests ported: 0 / 50
- [ ] Tests passing: 0 / 50
- [ ] Code reviewed
- [ ] CI integration verified
```

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2025-01-10 | 1.0 | Initial conversion plan created |

---

**Status**: Ready for implementation - Phase 1 can begin immediately
