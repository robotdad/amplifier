//! Partitioned rate limiting for key-based scenarios.
//!
//! Allows different rate limits per partition key (e.g., per user, per IP address).

mod partitioned_impl;

pub use partitioned_impl::{
    PartitionedRateLimiter,
    create_per_key_token_bucket,
    create_per_key_concurrency,
    create_per_key_fixed_window,
    create_per_key_sliding_window,
};