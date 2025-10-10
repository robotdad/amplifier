//! Chained rate limiter implementation.
//!
//! Combines multiple rate limiters in sequence where ALL must approve before granting access.

use crate::core::{RateLimitError, RateLimitLease, RateLimiter, RateLimiterStatistics};
use async_trait::async_trait;
use std::sync::Arc;
use std::time::Duration;
use tokio_util::sync::CancellationToken;

/// A rate limiter that chains multiple limiters together.
///
/// All limiters must successfully acquire permits for the overall acquisition to succeed.
/// If any limiter fails, all previously acquired permits are released.
///
/// # Example
///
/// ```no_run
/// use ratelimit::limiters::{
///     ChainedRateLimiter, TokenBucketRateLimiter, TokenBucketRateLimiterOptions,
///     ConcurrencyLimiter, ConcurrencyLimiterOptions
/// };
/// use ratelimit::core::{RateLimiter, QueueProcessingOrder};
/// use std::sync::Arc;
/// use std::time::Duration;
///
/// // Create a per-user token bucket limiter
/// let user_options = TokenBucketRateLimiterOptions {
///     tokens_per_period: 10,
///     token_limit: 10,
///     replenishment_period: Duration::from_secs(1),
///     auto_replenishment: true,
///     queue_limit: 0,
///     queue_processing_order: QueueProcessingOrder::OldestFirst,
/// };
/// let user_limiter = Arc::new(TokenBucketRateLimiter::new(user_options).unwrap());
///
/// // Create a global concurrency limiter
/// let global_options = ConcurrencyLimiterOptions {
///     permit_limit: 100,
///     queue_limit: 0,
///     queue_processing_order: QueueProcessingOrder::OldestFirst,
/// };
/// let global_limiter = Arc::new(ConcurrencyLimiter::new(global_options).unwrap());
///
/// // Chain them together
/// let chained = ChainedRateLimiter::new(vec![user_limiter, global_limiter]).unwrap();
///
/// // Both limiters must approve for acquisition to succeed
/// let lease = chained.attempt_acquire(1).unwrap();
/// ```
#[derive(Clone)]
pub struct ChainedRateLimiter {
    /// The ordered list of limiters to check
    limiters: Vec<Arc<dyn RateLimiter>>,
}

impl ChainedRateLimiter {
    /// Create a new chained rate limiter.
    ///
    /// # Arguments
    ///
    /// * `limiters` - The limiters to chain together (must have at least one)
    ///
    /// # Returns
    ///
    /// A new `ChainedRateLimiter` or an error if no limiters provided
    ///
    /// # Errors
    ///
    /// * `InvalidParameter` - If the limiters vector is empty
    pub fn new(limiters: Vec<Arc<dyn RateLimiter>>) -> Result<Self, RateLimitError> {
        if limiters.is_empty() {
            return Err(RateLimitError::InvalidParameter(
                "Must provide at least 1 limiter".to_string(),
            ));
        }

        Ok(Self { limiters })
    }

    /// Get the number of limiters in the chain.
    pub fn limiter_count(&self) -> usize {
        self.limiters.len()
    }
}

#[async_trait]
impl RateLimiter for ChainedRateLimiter {
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError> {
        let mut acquired_leases = Vec::with_capacity(self.limiters.len());

        // Try to acquire from each limiter in order
        for (index, limiter) in self.limiters.iter().enumerate() {
            match limiter.attempt_acquire(permit_count) {
                Ok(lease) if lease.is_acquired() => {
                    acquired_leases.push(lease);
                }
                Ok(lease) => {
                    // Failed lease - clean up and return first failure with metadata
                    drop(acquired_leases); // Release all previously acquired

                    // Add metadata about which limiter failed
                    return Ok(lease.with_metadata("FailedLimiterIndex", index));
                }
                Err(e) => {
                    // Error - clean up and propagate
                    drop(acquired_leases); // Release all previously acquired
                    return Err(e);
                }
            }
        }

        // All succeeded - return combined lease
        Ok(CombinedLease::create(acquired_leases))
    }

    async fn acquire_async(
        &self,
        permit_count: u32,
        cancel_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError> {
        let mut acquired_leases = Vec::with_capacity(self.limiters.len());

        // Try to acquire from each limiter in order
        for (index, limiter) in self.limiters.iter().enumerate() {
            match limiter.acquire_async(permit_count, cancel_token.clone()).await {
                Ok(lease) if lease.is_acquired() => {
                    acquired_leases.push(lease);
                }
                Ok(lease) => {
                    // Failed lease - clean up and return first failure
                    drop(acquired_leases); // Release all previously acquired

                    // Add metadata about which limiter failed
                    return Ok(lease.with_metadata("FailedLimiterIndex", index));
                }
                Err(e) => {
                    // Error - clean up and propagate
                    drop(acquired_leases); // Release all previously acquired
                    return Err(e);
                }
            }
        }

        // All succeeded - return combined lease
        Ok(CombinedLease::create(acquired_leases))
    }

    fn get_statistics(&self) -> RateLimiterStatistics {
        if self.limiters.is_empty() {
            return RateLimiterStatistics::new(0, 0, 0, 0);
        }

        // Start with the first limiter's stats
        let mut combined_stats = self.limiters[0].get_statistics();

        // Aggregate statistics from remaining limiters
        for limiter in &self.limiters[1..] {
            let stats = limiter.get_statistics();

            // Take minimum of available permits (bottleneck)
            combined_stats.current_available_permits = combined_stats
                .current_available_permits
                .min(stats.current_available_permits);

            // Take maximum of queued counts (worst case)
            combined_stats.current_queued_count = combined_stats
                .current_queued_count
                .max(stats.current_queued_count);

            // Sum successes and failures (all contribute)
            combined_stats.total_successful_leases += stats.total_successful_leases;
            combined_stats.total_failed_leases += stats.total_failed_leases;
        }

        combined_stats
    }

    fn idle_duration(&self) -> Option<Duration> {
        // We're idle if ALL limiters are idle
        let mut min_idle_duration: Option<Duration> = None;

        for limiter in &self.limiters {
            match limiter.idle_duration() {
                Some(duration) => {
                    min_idle_duration = Some(match min_idle_duration {
                        Some(min) => min.min(duration),
                        None => duration,
                    });
                }
                None => {
                    // At least one limiter is not idle
                    return None;
                }
            }
        }

        min_idle_duration
    }
}

/// Helper struct to create a combined lease that releases all inner leases when dropped.
struct CombinedLease;

impl CombinedLease {
    /// Create a successful lease that will release all inner leases when dropped.
    fn create(leases: Vec<RateLimitLease>) -> RateLimitLease {
        // Return a success lease with cleanup that drops all inner leases
        RateLimitLease::success_with_cleanup(move || {
            // Simply dropping the vector will trigger Drop for each lease,
            // which will call their individual cleanup callbacks
            drop(leases);
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::QueueProcessingOrder;
    use crate::limiters::{ConcurrencyLimiter, ConcurrencyLimiterOptions, TokenBucketRateLimiter, TokenBucketRateLimiterOptions};

    #[test]
    fn test_empty_limiters_error() {
        let result = ChainedRateLimiter::new(vec![]);
        assert!(matches!(
            result,
            Err(RateLimitError::InvalidParameter(_))
        ));
    }

    #[test]
    fn test_single_limiter() {
        let options = ConcurrencyLimiterOptions {
            permit_limit: 5,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter = Arc::new(ConcurrencyLimiter::new(options).unwrap());
        let chained = ChainedRateLimiter::new(vec![limiter.clone()]).unwrap();

        // Should behave like the single limiter
        let lease = chained.attempt_acquire(1).unwrap();
        assert!(lease.is_acquired());
    }

    #[test]
    fn test_multiple_limiters_all_succeed() {
        let concurrency_options = ConcurrencyLimiterOptions {
            permit_limit: 5,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter1 = Arc::new(ConcurrencyLimiter::new(concurrency_options).unwrap());

        let token_options = TokenBucketRateLimiterOptions {
            tokens_per_period: 10,
            token_limit: 10,
            replenishment_period: Duration::from_secs(1),
            auto_replenishment: false,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter2 = Arc::new(TokenBucketRateLimiter::new(token_options).unwrap());

        let chained = ChainedRateLimiter::new(vec![limiter1, limiter2]).unwrap();

        // Both have capacity, should succeed
        let lease = chained.attempt_acquire(1).unwrap();
        assert!(lease.is_acquired());
    }

    #[test]
    fn test_multiple_limiters_first_fails() {
        // First limiter has no capacity - will fail validation
        // So use permit_limit 1 but acquire all permits first
        let options1 = ConcurrencyLimiterOptions {
            permit_limit: 1,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter1 = Arc::new(ConcurrencyLimiter::new(options1).unwrap());

        // Acquire the only permit to make it unavailable
        let _lease1 = limiter1.attempt_acquire(1).unwrap();

        let options2 = ConcurrencyLimiterOptions {
            permit_limit: 5,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter2 = Arc::new(ConcurrencyLimiter::new(options2).unwrap());

        let chained = ChainedRateLimiter::new(vec![limiter1, limiter2]).unwrap();

        // First limiter has no capacity, should fail
        let lease = chained.attempt_acquire(1).unwrap();
        assert!(!lease.is_acquired());

        // Check metadata indicates first limiter failed
        let failed_index = lease.try_get_metadata::<usize>("FailedLimiterIndex");
        assert_eq!(failed_index, Some(&0));
    }

    #[test]
    fn test_multiple_limiters_second_fails() {
        let options1 = ConcurrencyLimiterOptions {
            permit_limit: 5,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter1 = Arc::new(ConcurrencyLimiter::new(options1).unwrap());

        // Second limiter has no capacity
        let options2 = ConcurrencyLimiterOptions {
            permit_limit: 1,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter2 = Arc::new(ConcurrencyLimiter::new(options2).unwrap());
        // Acquire the only permit to make it unavailable
        let _lease2 = limiter2.attempt_acquire(1).unwrap();

        let chained = ChainedRateLimiter::new(vec![limiter1.clone(), limiter2]).unwrap();

        // First succeeds but second fails
        let lease = chained.attempt_acquire(1).unwrap();
        assert!(!lease.is_acquired());

        // Check metadata indicates second limiter failed
        let failed_index = lease.try_get_metadata::<usize>("FailedLimiterIndex");
        assert_eq!(failed_index, Some(&1));

        // Verify first limiter's permit was returned (it should still have 5 available)
        let stats = limiter1.get_statistics();
        assert_eq!(stats.current_available_permits, 5);
    }

    #[test]
    fn test_statistics_aggregation() {
        let options1 = ConcurrencyLimiterOptions {
            permit_limit: 5,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter1 = Arc::new(ConcurrencyLimiter::new(options1).unwrap());

        let options2 = ConcurrencyLimiterOptions {
            permit_limit: 10,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter2 = Arc::new(ConcurrencyLimiter::new(options2).unwrap());

        let chained = ChainedRateLimiter::new(vec![limiter1, limiter2]).unwrap();

        let stats = chained.get_statistics();
        // Should take minimum available (5)
        assert_eq!(stats.current_available_permits, 5);
    }

    #[tokio::test]
    async fn test_acquire_async() {
        let options1 = ConcurrencyLimiterOptions {
            permit_limit: 5,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter1 = Arc::new(ConcurrencyLimiter::new(options1).unwrap());

        let options2 = ConcurrencyLimiterOptions {
            permit_limit: 10,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter2 = Arc::new(ConcurrencyLimiter::new(options2).unwrap());

        let chained = ChainedRateLimiter::new(vec![limiter1, limiter2]).unwrap();

        let lease = chained.acquire_async(1, None).await.unwrap();
        assert!(lease.is_acquired());
    }

    #[tokio::test]
    async fn test_acquire_async_with_cancellation() {
        // Create a limiter with no available permits to force queueing
        let options1 = ConcurrencyLimiterOptions {
            permit_limit: 1,
            queue_limit: 10, // Allow queueing
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter1 = Arc::new(ConcurrencyLimiter::new(options1).unwrap());

        // Acquire all permits so the next request must queue
        let _lease = limiter1.attempt_acquire(1).unwrap();

        let options2 = ConcurrencyLimiterOptions {
            permit_limit: 10,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
        };
        let limiter2 = Arc::new(ConcurrencyLimiter::new(options2).unwrap());

        let chained = ChainedRateLimiter::new(vec![limiter1, limiter2]).unwrap();

        let cancel_token = CancellationToken::new();

        // Start the acquire which should queue
        let acquire_task = tokio::spawn({
            let chained = chained.clone();
            let cancel_token = cancel_token.clone();
            async move {
                chained.acquire_async(1, Some(cancel_token)).await
            }
        });

        // Give it time to start waiting
        tokio::time::sleep(Duration::from_millis(10)).await;

        // Then cancel
        cancel_token.cancel();

        let result = acquire_task.await.unwrap();
        assert!(matches!(result, Err(RateLimitError::Cancelled)));
    }
}