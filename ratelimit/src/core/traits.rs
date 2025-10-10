//! Core rate limiter traits.

use crate::core::{RateLimitError, RateLimitLease, RateLimiterStatistics};
use async_trait::async_trait;
use std::time::Duration;
use tokio_util::sync::CancellationToken;

/// Main rate limiter trait.
///
/// This trait defines the interface for all rate limiters in the library.
/// Implementations must be thread-safe (`Send + Sync`).
#[async_trait]
pub trait RateLimiter: Send + Sync {
    /// Attempt to acquire permits synchronously (non-blocking).
    ///
    /// Returns immediately with either a successful or failed lease.
    /// Does not queue if permits are unavailable.
    ///
    /// # Arguments
    ///
    /// * `permit_count` - Number of permits to acquire
    ///
    /// # Returns
    ///
    /// A `RateLimitLease` indicating success or failure with metadata
    ///
    /// # Errors
    ///
    /// * `PermitCountExceeded` - Requested permits exceed limiter capacity
    /// * `Disposed` - Limiter has been disposed
    /// * `InvalidParameter` - Invalid permit count (e.g., negative)
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError>;

    /// Acquire permits asynchronously, with optional cancellation.
    ///
    /// If permits are not immediately available, the request will be queued
    /// (if queue capacity allows) and completed when permits become available.
    ///
    /// # Arguments
    ///
    /// * `permit_count` - Number of permits to acquire
    /// * `cancel_token` - Optional cancellation token to abort the request
    ///
    /// # Returns
    ///
    /// A `RateLimitLease` when permits are acquired or acquisition fails
    ///
    /// # Errors
    ///
    /// * `Cancelled` - Request was cancelled via the cancellation token
    /// * `PermitCountExceeded` - Requested permits exceed limiter capacity
    /// * `Disposed` - Limiter has been disposed
    async fn acquire_async(
        &self,
        permit_count: u32,
        cancel_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError>;

    /// Get a snapshot of the current rate limiter statistics.
    ///
    /// Returns current state including available permits, queue count,
    /// and counters for successful/failed leases.
    fn get_statistics(&self) -> RateLimiterStatistics;

    /// Get the duration for which the limiter has had all permits available.
    ///
    /// Returns `None` if the limiter is currently in use (has acquired permits
    /// or queued requests). Used by limiter managers for cleanup of idle limiters.
    fn idle_duration(&self) -> Option<Duration>;
}

/// Trait for rate limiters with time-based replenishment.
///
/// Extends `RateLimiter` with methods for time-based permit replenishment.
#[async_trait]
pub trait ReplenishingRateLimiter: RateLimiter {
    /// Returns `true` if auto-replenishment is enabled.
    ///
    /// When enabled, permits are automatically replenished on a timer.
    /// When disabled, `try_replenish()` must be called manually.
    fn is_auto_replenishing(&self) -> bool;

    /// Get the replenishment period.
    ///
    /// Indicates how frequently permits are added (if auto-replenishment is enabled)
    /// or the period for manual replenishment calculations.
    fn replenishment_period(&self) -> Duration;

    /// Manually trigger replenishment.
    ///
    /// Returns `false` if auto-replenishment is enabled (manual replenishment disabled).
    /// Returns `true` if replenishment was triggered.
    ///
    /// This method is useful for testing or custom replenishment schedules.
    fn try_replenish(&self) -> bool;
}

/// Factory function type for creating limiters in partitioned scenarios.
pub type LimiterFactory<TKey> = Box<dyn Fn(&TKey) -> Box<dyn RateLimiter> + Send + Sync>;
