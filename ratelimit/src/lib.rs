//! # RateLimit
//!
//! A Rust port of .NET's `System.Threading.RateLimiting` library.
//!
//! This library provides various rate limiting algorithms for controlling
//! the rate of operations in concurrent applications.
//!
//! ## Features
//!
//! - Multiple limiter types: Token Bucket, Fixed Window, Sliding Window, Concurrency
//! - Synchronous and asynchronous acquisition
//! - Queue management with FIFO/LIFO ordering
//! - Cancellation support
//! - Statistics tracking
//! - Auto-replenishment for time-based limiters

#![warn(missing_docs)]
#![warn(rustdoc::missing_crate_level_docs)]

pub mod core;
pub mod limiters;
pub mod partitioned;
pub mod queue;
pub mod utils;

// Re-export commonly used types
pub use core::{
    error::RateLimitError,
    lease::RateLimitLease,
    statistics::RateLimiterStatistics,
    traits::{RateLimiter, ReplenishingRateLimiter},
    QueueProcessingOrder,
};

// Re-export limiter implementations
pub use limiters::{
    ChainedRateLimiter, ConcurrencyLimiter, ConcurrencyLimiterOptions,
    TokenBucketRateLimiter, TokenBucketRateLimiterOptions,
};
