# RateLimit - Rust Port of .NET System.Threading.RateLimiting

A Rust port of the .NET `System.Threading.RateLimiting` library, providing various rate limiting algorithms for controlling the rate of operations in concurrent applications.

## Status

✅ **v1.0.0 - Production Ready** - All 6 Core Limiters Complete

## Features

- ✅ **ConcurrencyLimiter** - Manage concurrent access to resources
- ✅ **TokenBucketRateLimiter** - Token bucket algorithm with time-based replenishment
- ✅ **FixedWindowRateLimiter** - Fixed time window rate limiting
- ✅ **SlidingWindowRateLimiter** - Sliding window with segment tracking (more accurate)
- ✅ **ChainedRateLimiter** - Combine multiple limiters (all must approve)
- ✅ **PartitionedRateLimiter** - Per-key rate limiting (e.g., per-user, per-IP)

### Additional Features
- ✅ Synchronous and asynchronous acquisition
- ✅ Queue management with FIFO/LIFO ordering
- ✅ Cancellation support via tokio CancellationToken
- ✅ Statistics tracking
- ✅ Auto & manual replenishment for time-based limiters
- ✅ Metadata on leases (RetryAfter hints)
- ✅ Clean architecture following Rust idioms

## Installation

```toml
[dependencies]
ratelimit = "0.1"
```

## Quick Start

### TokenBucketRateLimiter - Time-based Token Bucket

```rust
use ratelimit::{TokenBucketRateLimiter, TokenBucketRateLimiterOptions, QueueProcessingOrder};
use std::sync::Arc;
use std::time::Duration;

#[tokio::main]
async fn main() {
    let limiter = Arc::new(TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 10,
        tokens_per_period: 2,
        replenishment_period: Duration::from_secs(1),
        queue_limit: 5,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: true,
    }).unwrap());

    // Spawn replenishment timer for auto-replenishment
    let timer_clone = Arc::clone(&limiter);
    tokio::spawn(async move {
        timer_clone.run_replenishment_timer().await;
    });

    // Synchronous acquire (non-blocking)
    let lease = limiter.attempt_acquire(1).unwrap();
    if lease.is_acquired() {
        println!("Operation allowed!");
    }

    // Async acquire (waits if necessary)
    let lease = limiter.acquire_async(1, None).await.unwrap();
    println!("Permits acquired!");
}
```

### ConcurrencyLimiter - Manage Concurrent Access

```rust
use ratelimit::{ConcurrencyLimiter, ConcurrencyLimiterOptions, QueueProcessingOrder};
use std::sync::Arc;

#[tokio::main]
async fn main() {
    let limiter = Arc::new(ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 10,  // Allow 10 concurrent operations
        queue_limit: 5,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
    }).unwrap());

    // Spawn queue processor
    let queue_clone = Arc::clone(&limiter);
    tokio::spawn(async move {
        queue_clone.run_queue_processor().await;
    });

    // Acquire permit
    let lease = limiter.acquire_async(1, None).await.unwrap();
    // Perform operation
    // Permit automatically returned when lease is dropped
}
```

### ChainedRateLimiter - Combine Multiple Policies

```rust
use ratelimit::{ChainedRateLimiter, ConcurrencyLimiter, TokenBucketRateLimiter};
use std::sync::Arc;

// Create per-user token bucket limiter
let user_limiter = Arc::new(TokenBucketRateLimiter::new(...).unwrap());

// Create global concurrency limiter
let global_limiter = Arc::new(ConcurrencyLimiter::new(...).unwrap());

// Chain them - both must approve
let chained = ChainedRateLimiter::new(vec![
    user_limiter as Arc<dyn RateLimiter>,
    global_limiter as Arc<dyn RateLimiter>,
]).unwrap();

let lease = chained.attempt_acquire(1).unwrap();
// Succeeds only if BOTH limiters approve
```

### PartitionedRateLimiter - Per-Key Rate Limiting

```rust
use ratelimit::{PartitionedRateLimiter, create_per_key_token_bucket, QueueProcessingOrder};
use std::time::Duration;

// Create per-user rate limiter
let limiter = create_per_key_token_bucket(
    |user_id: &String| user_id.clone(),  // Partition by user ID
    10,                                   // 10 tokens per user
    5,                                    // 5 tokens per period
    Duration::from_secs(1),              // 1 second window
    QueueProcessingOrder::OldestFirst,
);

// Different users get independent limits
let user1_lease = limiter.attempt_acquire(&"user1".to_string(), 1).unwrap();
let user2_lease = limiter.attempt_acquire(&"user2".to_string(), 1).unwrap();
// Both succeed - separate limits per user
```

## Documentation

Run `cargo doc --open` to view the full API documentation.

## All Limiters Implemented

### ✅ ConcurrencyLimiter
Manage concurrent access with a fixed number of permits. Permits are returned when leases are dropped.

**Use case**: Limit concurrent database connections, API calls, or worker threads.

### ✅ TokenBucketRateLimiter
Time-based token bucket algorithm. Tokens replenish periodically and are consumed (not returned).

**Use case**: API rate limiting with burst capacity (e.g., 100 requests/minute with bucket of 20).

### ✅ FixedWindowRateLimiter
Fixed time windows with permit resets. All permits reset at once when the window expires.

**Use case**: Simple time-based limiting (e.g., 1000 requests per hour).

### ✅ SlidingWindowRateLimiter
Sliding window with segment tracking. More accurate than fixed windows - segments expire individually.

**Use case**: Accurate rate limiting without burst at window boundaries.

### ✅ ChainedRateLimiter
Combines multiple limiters. All limiters must approve before granting access.

**Use case**: Apply multiple policies (e.g., per-user + global limit).

### ✅ PartitionedRateLimiter
Per-key rate limiting with dynamic limiter creation. Each partition key gets its own limiter instance.

**Use case**: Per-user or per-IP rate limiting with independent limits.

## Testing

```bash
# Run all tests (58 tests)
cargo test

# Run with output
cargo test -- --nocapture

# Run specific limiter tests
cargo test --test concurrency_tests
cargo test --test token_bucket_tests

# Run specific test
cargo test test_name
```

**Test Coverage**: 58 tests, 100% passing
- Concurrency: 19 tests
- TokenBucket: 10 tests
- FixedWindow: 7 tests
- SlidingWindow: 10 tests
- Chained: 18 tests
- Doc tests: 6 tests

## Contributing

This is a direct port of the .NET System.Threading.RateLimiting library. The goal is to maintain API similarity while embracing Rust idioms.

## License

MIT

## Performance

All limiters use efficient data structures and minimal locking:
- `parking_lot::Mutex` for fast synchronization
- `tokio::sync::mpsc` unbounded channels for events
- VecDeque for FIFO queue management
- Zero-cost abstractions with trait objects

## Architecture

The library follows a clean channel-based event pattern:
- Simple cleanup callbacks (≤ 3 lines)
- Single queue processor per limiter
- Background tasks for replenishment
- No nested callbacks
- Clear separation of concerns

See [RUST_CONVERSION_PLAN.md](../RUST_CONVERSION_PLAN.md) for architecture details.

## References

- [Original .NET Implementation](https://github.com/dotnet/runtime/tree/main/src/libraries/System.Threading.RateLimiting)
- [Conversion Plan](../RUST_CONVERSION_PLAN.md)
- [Final Status](../FINAL_STATUS.md)
