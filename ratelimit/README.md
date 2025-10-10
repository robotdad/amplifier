# RateLimit - Rust Port of .NET System.Threading.RateLimiting

A Rust port of the .NET `System.Threading.RateLimiting` library, providing various rate limiting algorithms for controlling the rate of operations in concurrent applications.

## Status

🚧 **Under Development** - Phase 1 (Core Infrastructure) Complete

## Features

- ✅ Core trait definitions (`RateLimiter`, `ReplenishingRateLimiter`)
- ✅ Error handling and statistics types
- ✅ Lease system with metadata support
- 🚧 Limiter implementations (coming soon)
  - Token Bucket
  - Fixed Window
  - Sliding Window
  - Concurrency Limiter
  - Chained Limiter
  - Partitioned Limiter

## Installation

```toml
[dependencies]
ratelimit = "0.1"
```

## Quick Start

```rust
use ratelimit::limiters::TokenBucketRateLimiter;
use ratelimit::core::{RateLimiter, TokenBucketOptions, QueueProcessingOrder};
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let limiter = TokenBucketRateLimiter::new(TokenBucketOptions {
        token_limit: 10,
        tokens_per_period: 2,
        replenishment_period: Duration::from_secs(1),
        queue_limit: 5,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: true,
    })?;

    // Synchronous acquire (non-blocking)
    let lease = limiter.attempt_acquire(1)?;
    if lease.is_acquired() {
        // Perform rate-limited operation
        println!("Operation allowed!");
    }

    // Async acquire (waits if necessary)
    let lease = limiter.acquire_async(1, None).await?;
    println!("Permits acquired: {}", lease.is_acquired());

    Ok(())
}
```

## Documentation

Run `cargo doc --open` to view the full API documentation.

## Development Status

See [RUST_CONVERSION_PLAN.md](../RUST_CONVERSION_PLAN.md) for the complete conversion plan and roadmap.

### Phase 1: Core Infrastructure ✅ COMPLETE
- Core traits and types
- Error handling
- Lease system
- Basic test framework

### Phase 2: First Limiter (In Progress)
- [ ] ConcurrencyLimiter implementation
- [ ] ~40 tests converted and passing

### Phase 3-5: Additional Limiters (Planned)
- Token Bucket, Fixed Window, Sliding Window
- Chained and Partitioned limiters

## Testing

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_name
```

## Contributing

This is a direct port of the .NET System.Threading.RateLimiting library. The goal is to maintain API similarity while embracing Rust idioms.

## License

MIT

## References

- [Original .NET Implementation](https://github.com/dotnet/runtime/tree/main/src/libraries/System.Threading.RateLimiting)
- [Conversion Plan](../RUST_CONVERSION_PLAN.md)
