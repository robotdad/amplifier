use crate::{RateLimiter, RateLimitLease, RateLimiterStatistics, RateLimitError, QueueProcessingOrder};
use std::collections::HashMap;
use std::hash::Hash;
use std::sync::Arc;
use std::time::Duration;
use parking_lot::Mutex;
use tokio_util::sync::CancellationToken;

/// Type alias for the partitioner function that maps resources to partition keys and limiters.
type PartitionerFn<TResource, TKey> = dyn Fn(&TResource) -> (TKey, Arc<dyn RateLimiter>) + Send + Sync;

/// A rate limiter that partitions resources and applies different rate limit policies per partition.
///
/// This limiter creates separate rate limiter instances for each unique partition key,
/// allowing different rate limiting policies to be applied based on resource characteristics
/// (e.g., per-user, per-IP, per-tenant).
///
/// # Type Parameters
/// - `TResource`: The type of resource being rate limited
/// - `TKey`: The partition key type (must be hashable and cloneable)
///
/// # Example
/// ```no_run
/// use ratelimit::{PartitionedRateLimiter, TokenBucketRateLimiter, TokenBucketRateLimiterOptions, RateLimiter, QueueProcessingOrder};
/// use std::sync::Arc;
/// use std::time::Duration;
///
/// // Create a partitioned limiter that limits per-user
/// let limiter = PartitionedRateLimiter::new(
///     |user_id: &String| {
///         // Each user gets their own token bucket with 100 requests per minute
///         let options = TokenBucketRateLimiterOptions::new(100, 100, Duration::from_secs(60), 1, QueueProcessingOrder::OldestFirst, false).unwrap();
///         (
///             user_id.clone(),
///             Arc::new(TokenBucketRateLimiter::new(options).unwrap()) as Arc<dyn RateLimiter>
///         )
///     }
/// );
///
/// // Different users get separate rate limits
/// let lease1 = limiter.attempt_acquire(&"user1".to_string(), 1);
/// let lease2 = limiter.attempt_acquire(&"user2".to_string(), 1);
/// ```
pub struct PartitionedRateLimiter<TResource, TKey>
where
    TKey: Hash + Eq + Clone + Send + Sync + 'static,
    TResource: Send + Sync,
{
    /// Map of partition keys to their corresponding rate limiters
    limiters: Arc<Mutex<HashMap<TKey, Arc<dyn RateLimiter>>>>,

    /// Function that maps a resource to a partition key and creates a limiter for new keys
    partitioner: Arc<PartitionerFn<TResource, TKey>>,

    /// Optional idle time limit for limiter cleanup (not implemented in v1)
    #[allow(dead_code)]
    idle_time_limit: Duration,
}

impl<TResource, TKey> PartitionedRateLimiter<TResource, TKey>
where
    TKey: Hash + Eq + Clone + Send + Sync + 'static,
    TResource: Send + Sync,
{
    /// Creates a new partitioned rate limiter.
    ///
    /// # Arguments
    /// - `partitioner`: Function that maps resources to partition keys and creates limiters
    ///
    /// The partitioner function should return a tuple of:
    /// - The partition key for the resource
    /// - A new rate limiter instance to use for that partition (if not already cached)
    pub fn new<F>(partitioner: F) -> Self
    where
        F: Fn(&TResource) -> (TKey, Arc<dyn RateLimiter>) + Send + Sync + 'static,
    {
        Self::with_idle_limit(partitioner, Duration::from_secs(10))
    }

    /// Creates a new partitioned rate limiter with custom idle time limit.
    ///
    /// # Arguments
    /// - `partitioner`: Function that maps resources to partition keys and creates limiters
    /// - `idle_time_limit`: How long a limiter can be idle before cleanup (not implemented in v1)
    pub fn with_idle_limit<F>(partitioner: F, idle_time_limit: Duration) -> Self
    where
        F: Fn(&TResource) -> (TKey, Arc<dyn RateLimiter>) + Send + Sync + 'static,
    {
        Self {
            limiters: Arc::new(Mutex::new(HashMap::new())),
            partitioner: Arc::new(partitioner),
            idle_time_limit,
        }
    }

    /// Gets or creates a rate limiter for the given resource.
    ///
    /// If a limiter already exists for the partition key, it is returned.
    /// Otherwise, a new limiter is created using the partitioner function.
    fn get_limiter(&self, resource: &TResource) -> Arc<dyn RateLimiter> {
        let (key, new_limiter) = (self.partitioner)(resource);

        let mut limiters = self.limiters.lock();

        limiters
            .entry(key)
            .or_insert_with(|| new_limiter)
            .clone()
    }

    /// Attempts to acquire a lease for the given resource.
    ///
    /// This delegates to the rate limiter for the resource's partition.
    pub fn attempt_acquire(&self, resource: &TResource, permit_count: u32) -> Result<RateLimitLease, RateLimitError> {
        let limiter = self.get_limiter(resource);
        limiter.attempt_acquire(permit_count)
    }

    /// Asynchronously acquires a lease for the given resource.
    ///
    /// This delegates to the rate limiter for the resource's partition.
    pub async fn acquire_async(
        &self,
        resource: &TResource,
        permit_count: u32,
        cancellation_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError> {
        let limiter = self.get_limiter(resource);
        limiter.acquire_async(permit_count, cancellation_token).await
    }

    /// Gets statistics for the given resource's partition.
    ///
    /// This delegates to the rate limiter for the resource's partition.
    pub fn get_statistics(&self, resource: &TResource) -> RateLimiterStatistics {
        let limiter = self.get_limiter(resource);
        limiter.get_statistics()
    }


    /// Gets the number of active partitions.
    pub fn partition_count(&self) -> usize {
        let limiters = self.limiters.lock();
        limiters.len()
    }

    /// Clears all cached limiters.
    ///
    /// This can be useful for testing or when you want to reset all rate limits.
    pub fn clear(&self) {
        let mut limiters = self.limiters.lock();
        limiters.clear();
    }
}

/// Factory function for creating simple per-key token bucket limiters.
///
/// This is a convenience function for the common case of creating token bucket
/// limiters with the same configuration for each partition key.
///
/// # Example
/// ```no_run
/// use ratelimit::{PartitionedRateLimiter, create_per_key_token_bucket, QueueProcessingOrder};
/// use std::time::Duration;
///
/// let limiter = PartitionedRateLimiter::new(
///     create_per_key_token_bucket::<String>(100, 100, Duration::from_secs(60), 1, QueueProcessingOrder::OldestFirst, false)
/// );
/// ```
pub fn create_per_key_token_bucket<TKey>(
    token_limit: u32,
    tokens_per_period: u32,
    replenishment_period: Duration,
    queue_limit: u32,
    queue_processing_order: QueueProcessingOrder,
    auto_replenishment: bool,
) -> impl Fn(&TKey) -> (TKey, Arc<dyn RateLimiter>) + Send + Sync + 'static
where
    TKey: Clone + Hash + Eq + Send + Sync + 'static,
{
    move |key: &TKey| {
        use crate::{TokenBucketRateLimiter, TokenBucketRateLimiterOptions};

        let options = TokenBucketRateLimiterOptions::new(
            token_limit,
            tokens_per_period,
            replenishment_period,
            queue_limit,
            queue_processing_order,
            auto_replenishment,
        ).expect("Failed to create token bucket options");

        (
            key.clone(),
            Arc::new(TokenBucketRateLimiter::new(options).expect("Failed to create token bucket limiter")) as Arc<dyn RateLimiter>,
        )
    }
}

/// Factory function for creating simple per-key concurrency limiters.
///
/// This is a convenience function for the common case of creating concurrency
/// limiters with the same configuration for each partition key.
///
/// # Example
/// ```no_run
/// use ratelimit::{PartitionedRateLimiter, create_per_key_concurrency, QueueProcessingOrder};
///
/// let limiter = PartitionedRateLimiter::new(
///     create_per_key_concurrency::<String>(10, 5, QueueProcessingOrder::OldestFirst) // 10 concurrent, queue 5
/// );
/// ```
pub fn create_per_key_concurrency<TKey>(
    permit_limit: u32,
    queue_limit: u32,
    queue_processing_order: QueueProcessingOrder,
) -> impl Fn(&TKey) -> (TKey, Arc<dyn RateLimiter>) + Send + Sync + 'static
where
    TKey: Clone + Hash + Eq + Send + Sync + 'static,
{
    move |key: &TKey| {
        use crate::{ConcurrencyLimiter, ConcurrencyLimiterOptions};

        let options = ConcurrencyLimiterOptions::new(permit_limit, queue_limit, queue_processing_order)
            .expect("Failed to create concurrency options");

        (
            key.clone(),
            Arc::new(ConcurrencyLimiter::new(options).expect("Failed to create concurrency limiter")) as Arc<dyn RateLimiter>,
        )
    }
}

/// Factory function for creating simple per-key fixed window limiters.
///
/// This is a convenience function for the common case of creating fixed window
/// limiters with the same configuration for each partition key.
///
/// # Example
/// ```no_run
/// use ratelimit::{PartitionedRateLimiter, create_per_key_fixed_window, QueueProcessingOrder};
/// use std::time::Duration;
///
/// let limiter = PartitionedRateLimiter::new(
///     create_per_key_fixed_window::<String>(100, Duration::from_secs(60), 10, QueueProcessingOrder::OldestFirst, false)
/// );
/// ```
pub fn create_per_key_fixed_window<TKey>(
    permit_limit: u32,
    window: Duration,
    queue_limit: u32,
    queue_processing_order: QueueProcessingOrder,
    auto_replenishment: bool,
) -> impl Fn(&TKey) -> (TKey, Arc<dyn RateLimiter>) + Send + Sync + 'static
where
    TKey: Clone + Hash + Eq + Send + Sync + 'static,
{
    move |key: &TKey| {
        use crate::{FixedWindowRateLimiter, FixedWindowRateLimiterOptions};

        let options = FixedWindowRateLimiterOptions::new(
            permit_limit,
            window,
            queue_limit,
            queue_processing_order,
            auto_replenishment,
        ).expect("Failed to create fixed window options");

        (
            key.clone(),
            Arc::new(FixedWindowRateLimiter::new(options).expect("Failed to create fixed window limiter")) as Arc<dyn RateLimiter>,
        )
    }
}

/// Factory function for creating simple per-key sliding window limiters.
///
/// This is a convenience function for the common case of creating sliding window
/// limiters with the same configuration for each partition key.
///
/// # Example
/// ```no_run
/// use ratelimit::{PartitionedRateLimiter, create_per_key_sliding_window, QueueProcessingOrder};
/// use std::time::Duration;
///
/// let limiter = PartitionedRateLimiter::new(
///     create_per_key_sliding_window::<String>(100, Duration::from_secs(60), 10, 10, QueueProcessingOrder::OldestFirst, false)
/// );
/// ```
pub fn create_per_key_sliding_window<TKey>(
    permit_limit: u32,
    window: Duration,
    segments_per_window: u32,
    queue_limit: u32,
    queue_processing_order: QueueProcessingOrder,
    auto_replenishment: bool,
) -> impl Fn(&TKey) -> (TKey, Arc<dyn RateLimiter>) + Send + Sync + 'static
where
    TKey: Clone + Hash + Eq + Send + Sync + 'static,
{
    move |key: &TKey| {
        use crate::{SlidingWindowRateLimiter, SlidingWindowRateLimiterOptions};

        let options = SlidingWindowRateLimiterOptions {
            permit_limit,
            window,
            segments_per_window,
            queue_limit,
            queue_processing_order,
            auto_replenishment,
        };

        (
            key.clone(),
            Arc::new(SlidingWindowRateLimiter::new(options)) as Arc<dyn RateLimiter>,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{TokenBucketRateLimiter, TokenBucketRateLimiterOptions};
    use std::time::Duration;

    #[test]
    fn test_partitioned_creates_separate_limiters() {
        // Create a partitioned limiter that gives each key 2 permits
        let limiter = PartitionedRateLimiter::new(|key: &String| {
            let options = TokenBucketRateLimiterOptions::new(2, 2, Duration::from_secs(60), 0, QueueProcessingOrder::OldestFirst, false)
                .expect("Failed to create options");
            (
                key.clone(),
                Arc::new(TokenBucketRateLimiter::new(options).expect("Failed to create limiter")) as Arc<dyn RateLimiter>,
            )
        });

        // User1 should get 2 permits
        let lease1 = limiter.attempt_acquire(&"user1".to_string(), 1).unwrap();
        assert!(lease1.is_acquired());
        let lease2 = limiter.attempt_acquire(&"user1".to_string(), 1).unwrap();
        assert!(lease2.is_acquired());
        let lease3 = limiter.attempt_acquire(&"user1".to_string(), 1).unwrap();
        assert!(!lease3.is_acquired()); // Should fail - user1 is out of permits

        // User2 should have their own separate 2 permits
        let lease4 = limiter.attempt_acquire(&"user2".to_string(), 1).unwrap();
        assert!(lease4.is_acquired());
        let lease5 = limiter.attempt_acquire(&"user2".to_string(), 1).unwrap();
        assert!(lease5.is_acquired());
        let lease6 = limiter.attempt_acquire(&"user2".to_string(), 1).unwrap();
        assert!(!lease6.is_acquired()); // Should fail - user2 is out of permits

        // Should have 2 partitions
        assert_eq!(limiter.partition_count(), 2);
    }

    #[test]
    fn test_partitioned_reuses_existing_limiters() {
        let limiter = PartitionedRateLimiter::new(|key: &String| {
            let options = TokenBucketRateLimiterOptions::new(3, 3, Duration::from_secs(60), 0, QueueProcessingOrder::OldestFirst, false)
                .expect("Failed to create options");
            (
                key.clone(),
                Arc::new(TokenBucketRateLimiter::new(options).expect("Failed to create limiter")) as Arc<dyn RateLimiter>,
            )
        });

        // Acquire permits for same user multiple times
        let _lease1 = limiter.attempt_acquire(&"user1".to_string(), 1);
        assert_eq!(limiter.partition_count(), 1);

        let _lease2 = limiter.attempt_acquire(&"user1".to_string(), 1);
        assert_eq!(limiter.partition_count(), 1); // Should still be 1

        let _lease3 = limiter.attempt_acquire(&"user1".to_string(), 1);
        assert_eq!(limiter.partition_count(), 1); // Should still be 1

        // Now a different user
        let _lease4 = limiter.attempt_acquire(&"user2".to_string(), 1);
        assert_eq!(limiter.partition_count(), 2); // Now should be 2
    }

    #[tokio::test]
    async fn test_factory_functions() {
        // Test token bucket factory
        let tb_limiter = PartitionedRateLimiter::new(
            create_per_key_token_bucket::<String>(5, 5, Duration::from_secs(60), 0, QueueProcessingOrder::OldestFirst, false)
        );
        let lease = tb_limiter.attempt_acquire(&"test".to_string(), 1).unwrap();
        assert!(lease.is_acquired());

        // Test concurrency factory
        let cc_limiter = PartitionedRateLimiter::new(
            create_per_key_concurrency::<u32>(2, 5, QueueProcessingOrder::OldestFirst)
        );
        let lease = cc_limiter.attempt_acquire(&42u32, 1).unwrap();
        assert!(lease.is_acquired());

        // Test fixed window factory
        let fw_limiter = PartitionedRateLimiter::new(
            create_per_key_fixed_window::<String>(10, Duration::from_secs(60), 5, QueueProcessingOrder::OldestFirst, false)
        );
        let lease = fw_limiter.attempt_acquire(&"test".to_string(), 1).unwrap();
        assert!(lease.is_acquired());

        // Test sliding window factory (requires tokio runtime)
        let sw_limiter = PartitionedRateLimiter::new(
            create_per_key_sliding_window::<String>(10, Duration::from_secs(60), 10, 5, QueueProcessingOrder::OldestFirst, false)
        );
        let lease = sw_limiter.attempt_acquire(&"test".to_string(), 1).unwrap();
        assert!(lease.is_acquired());
    }

    #[test]
    fn test_clear() {
        let limiter = PartitionedRateLimiter::new(|key: &i32| {
            let options = TokenBucketRateLimiterOptions::new(1, 1, Duration::from_secs(60), 0, QueueProcessingOrder::OldestFirst, false)
                .expect("Failed to create options");
            (
                *key,
                Arc::new(TokenBucketRateLimiter::new(options).expect("Failed to create limiter")) as Arc<dyn RateLimiter>,
            )
        });

        // Create multiple partitions
        let _lease1 = limiter.attempt_acquire(&1, 1);
        let _lease2 = limiter.attempt_acquire(&2, 1);
        let _lease3 = limiter.attempt_acquire(&3, 1);
        assert_eq!(limiter.partition_count(), 3);

        // Clear all partitions
        limiter.clear();
        assert_eq!(limiter.partition_count(), 0);

        // Should create new limiters after clear
        let lease4 = limiter.attempt_acquire(&1, 1).unwrap();
        assert!(lease4.is_acquired()); // New limiter for key 1
        assert_eq!(limiter.partition_count(), 1);
    }

    #[tokio::test]
    async fn test_async_acquire() {
        let limiter = PartitionedRateLimiter::new(|key: &String| {
            let options = TokenBucketRateLimiterOptions::new(1, 1, Duration::from_secs(60), 0, QueueProcessingOrder::OldestFirst, false)
                .expect("Failed to create options");
            (
                key.clone(),
                Arc::new(TokenBucketRateLimiter::new(options).expect("Failed to create limiter")) as Arc<dyn RateLimiter>,
            )
        });

        // Acquire the only permit for user1
        let lease1 = limiter.acquire_async(&"user1".to_string(), 1, None).await.unwrap();
        assert!(lease1.is_acquired());

        // User2 should still have their permit
        let lease2 = limiter.acquire_async(&"user2".to_string(), 1, None).await.unwrap();
        assert!(lease2.is_acquired());
    }
}