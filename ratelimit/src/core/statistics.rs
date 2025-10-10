//! Rate limiter statistics types.

/// A snapshot of rate limiter statistics at a point in time.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RateLimiterStatistics {
    /// Number of permits currently available for immediate acquisition.
    pub current_available_permits: i64,

    /// Number of permits currently in the queue waiting for availability.
    pub current_queued_count: u32,

    /// Total number of successful lease acquisitions since limiter creation.
    pub total_successful_leases: u64,

    /// Total number of failed lease acquisitions since limiter creation.
    pub total_failed_leases: u64,
}

impl RateLimiterStatistics {
    /// Create a new statistics snapshot.
    pub fn new(
        current_available_permits: i64,
        current_queued_count: u32,
        total_successful_leases: u64,
        total_failed_leases: u64,
    ) -> Self {
        Self {
            current_available_permits,
            current_queued_count,
            total_successful_leases,
            total_failed_leases,
        }
    }
}
