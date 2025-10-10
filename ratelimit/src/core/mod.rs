//! Core types and traits for rate limiting.
//!
//! This module contains the fundamental abstractions used throughout the library:
//! - `RateLimiter` and `ReplenishingRateLimiter` traits
//! - `RateLimitLease` for representing acquisition results
//! - Error types
//! - Statistics types

pub mod error;
pub mod lease;
pub mod metadata;
pub mod statistics;
pub mod traits;

// Re-export commonly used types
pub use error::RateLimitError;
pub use lease::RateLimitLease;
pub use metadata::MetadataName;
pub use statistics::RateLimiterStatistics;
pub use traits::{RateLimiter, ReplenishingRateLimiter};

/// Queue processing order for queued requests
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum QueueProcessingOrder {
    /// Process oldest (first-in) requests first
    OldestFirst,
    /// Process newest (last-in) requests first
    NewestFirst,
}
