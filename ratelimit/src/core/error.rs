//! Error types for rate limiting operations.

use thiserror::Error;

/// Errors that can occur during rate limiting operations.
#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum RateLimitError {
    /// The request was cancelled via a cancellation token.
    #[error("Request was cancelled")]
    Cancelled,

    /// The requested permit count exceeds the limiter's capacity.
    ///
    /// Contains (requested, capacity).
    #[error("Permit count {0} exceeds limiter capacity {1}")]
    PermitCountExceeded(u32, u32),

    /// The rate limiter has been disposed and can no longer be used.
    #[error("Limiter has been disposed")]
    Disposed,

    /// An invalid parameter was provided.
    #[error("Invalid parameter: {0}")]
    InvalidParameter(String),

    /// Queue limit has been exceeded.
    #[error("Queue limit exceeded")]
    QueueLimitExceeded,
}
