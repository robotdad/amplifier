//! Metadata name constants for rate limit leases.

/// Common metadata names used in rate limit leases.
pub struct MetadataName;

impl MetadataName {
    /// Suggested retry-after duration for failed acquisitions.
    ///
    /// Type: `Duration`
    pub const RETRY_AFTER: &'static str = "RetryAfter";
}
