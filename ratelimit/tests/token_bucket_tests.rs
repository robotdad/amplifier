//! Tests for TokenBucketRateLimiter
//!
//! Ported from: System.Threading.RateLimiting.Test.TokenBucketRateLimiterTests

use ratelimit::{
    QueueProcessingOrder, RateLimitError, RateLimiter, ReplenishingRateLimiter,
    TokenBucketRateLimiter, TokenBucketRateLimiterOptions,
};
use std::sync::Arc;
use std::time::Duration;

mod common;

// Helper to create a limiter with processors for async tests
async fn create_limiter_with_processors(
    options: TokenBucketRateLimiterOptions,
) -> Arc<TokenBucketRateLimiter> {
    let limiter = Arc::new(TokenBucketRateLimiter::new(options).unwrap());

    // Spawn replenishment timer if auto-replenishment is enabled
    if limiter.is_auto_replenishing() {
        let timer_clone = Arc::clone(&limiter);
        tokio::spawn(async move { timer_clone.run_replenishment_timer().await });
    }
    // Note: TokenBucket doesn't need queue processor since tokens don't return

    // Give processors time to start
    tokio::time::sleep(Duration::from_millis(1)).await;
    limiter
}

// ============================================================================
// VALIDATION TESTS
// ============================================================================

#[test]
fn invalid_options_throws() {
    // Token limit <= 0
    let result = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 0,
        tokens_per_period: 1,
        replenishment_period: Duration::from_millis(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        auto_replenishment: false,
    });
    assert!(matches!(result, Err(RateLimitError::InvalidParameter(_))));

    // Tokens per period <= 0
    let result = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 0,
        replenishment_period: Duration::from_millis(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        auto_replenishment: false,
    });
    assert!(matches!(result, Err(RateLimitError::InvalidParameter(_))));

    // Replenishment period = 0
    let result = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 1,
        replenishment_period: Duration::ZERO,
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        auto_replenishment: false,
    });
    assert!(matches!(result, Err(RateLimitError::InvalidParameter(_))));
}

// ============================================================================
// BASIC ACQUIRE/RELEASE TESTS
// ============================================================================

#[test]
fn can_acquire_resource() {
    let limiter = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 1,
        replenishment_period: Duration::from_millis(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        auto_replenishment: false,
    })
    .unwrap();

    // First acquire succeeds
    let lease = limiter.attempt_acquire(1).unwrap();
    assert!(lease.is_acquired());

    // Second acquire fails (no tokens available)
    let lease2 = limiter.attempt_acquire(1).unwrap();
    assert!(!lease2.is_acquired());

    // Drop doesn't change token count (tokens don't return)
    drop(lease);
    let lease3 = limiter.attempt_acquire(1).unwrap();
    assert!(!lease3.is_acquired());

    // Manual replenish
    assert!(limiter.try_replenish());

    // Now can acquire
    let lease4 = limiter.attempt_acquire(1).unwrap();
    assert!(lease4.is_acquired());
}

#[tokio::test]
async fn can_acquire_resource_async() {
    let limiter = create_limiter_with_processors(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 1,
        replenishment_period: Duration::from_millis(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        auto_replenishment: false,
    })
    .await;

    let lease = limiter.acquire_async(1, None).await.unwrap();
    assert!(lease.is_acquired());

    // Second acquire should queue
    let limiter_clone = Arc::clone(&limiter);
    let wait_task = tokio::spawn(async move { limiter_clone.acquire_async(1, None).await });

    tokio::time::sleep(Duration::from_millis(10)).await;
    assert!(!wait_task.is_finished());

    // Manual replenish
    assert!(limiter.try_replenish());

    // Queued request should complete
    let lease2 = wait_task.await.unwrap().unwrap();
    assert!(lease2.is_acquired());
}

// ============================================================================
// REPLENISHMENT TESTS
// ============================================================================

#[test]
fn replenish_honors_tokens_per_period() {
    let limiter = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 7,
        tokens_per_period: 3,
        replenishment_period: Duration::from_millis(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: false,
    })
    .unwrap();

    // Use 5 tokens
    assert!(limiter.attempt_acquire(5).unwrap().is_acquired());
    assert!(!limiter.attempt_acquire(3).unwrap().is_acquired());

    // Should have 2 tokens left
    assert_eq!(limiter.get_statistics().current_available_permits, 2);

    // Replenish adds 3
    limiter.try_replenish();
    assert_eq!(limiter.get_statistics().current_available_permits, 5);

    // Replenish again (caps at 7)
    limiter.try_replenish();
    assert_eq!(limiter.get_statistics().current_available_permits, 7);
}

#[test]
fn try_replenish_with_auto_replenish_returns_false() {
    let limiter = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 2,
        tokens_per_period: 1,
        replenishment_period: Duration::from_secs(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: true,  // Auto-replenishment enabled
    })
    .unwrap();

    assert_eq!(limiter.get_statistics().current_available_permits, 2);

    // Can't manually replenish when auto is enabled
    assert!(!limiter.try_replenish());
    assert_eq!(limiter.get_statistics().current_available_permits, 2);
}

#[tokio::test]
async fn try_replenish_with_all_tokens_available_noops() {
    let limiter = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 2,
        tokens_per_period: 1,
        replenishment_period: Duration::from_millis(30),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: false,
    })
    .unwrap();

    assert_eq!(limiter.get_statistics().current_available_permits, 2);

    tokio::time::sleep(Duration::from_millis(100)).await;

    limiter.try_replenish();
    assert_eq!(limiter.get_statistics().current_available_permits, 2);
}

// ============================================================================
// ERROR HANDLING TESTS
// ============================================================================

#[test]
fn throws_when_acquiring_more_than_limit() {
    let limiter = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 1,
        replenishment_period: Duration::from_millis(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        auto_replenishment: false,
    })
    .unwrap();

    let result = limiter.attempt_acquire(2);
    assert!(matches!(
        result,
        Err(RateLimitError::PermitCountExceeded(2, 1))
    ));
}

#[tokio::test]
async fn throws_when_waiting_for_more_than_limit() {
    let limiter = create_limiter_with_processors(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 1,
        replenishment_period: Duration::from_millis(1),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        auto_replenishment: false,
    })
    .await;

    let result = limiter.acquire_async(2, None).await;
    assert!(matches!(
        result,
        Err(RateLimitError::PermitCountExceeded(2, 1))
    ));
}

// ============================================================================
// METADATA TESTS
// ============================================================================

#[tokio::test]
async fn retry_metadata_on_failed_wait_async() {
    let options = TokenBucketRateLimiterOptions {
        token_limit: 2,
        tokens_per_period: 1,
        replenishment_period: Duration::from_secs(20),
        queue_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: false,
    };

    let limiter = create_limiter_with_processors(options.clone()).await;

    // Use all tokens
    let _lease = limiter.attempt_acquire(2).unwrap();

    // Try to acquire more than available - should fail with retry hint
    let failed_lease = limiter.acquire_async(2, None).await.unwrap();
    assert!(!failed_lease.is_acquired());

    // Check RetryAfter metadata
    let retry_after = failed_lease
        .try_get_metadata::<Duration>("RetryAfter")
        .copied();
    assert!(retry_after.is_some());

    // Should be 2 periods (need to wait for 2 replenishments)
    let expected = options.replenishment_period * 2;
    assert_eq!(retry_after.unwrap(), expected);
}

#[test]
fn replenishing_rate_limiter_properties_have_correct_values() {
    let replenish_period = Duration::from_secs(60); // 1 minute

    let limiter = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 1,
        replenishment_period: replenish_period,
        queue_limit: 2,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: true,
    })
    .unwrap();

    assert!(limiter.is_auto_replenishing());
    assert_eq!(limiter.replenishment_period(), replenish_period);

    let replenish_period2 = Duration::from_secs(2);
    let limiter2 = TokenBucketRateLimiter::new(TokenBucketRateLimiterOptions {
        token_limit: 1,
        tokens_per_period: 1,
        replenishment_period: replenish_period2,
        queue_limit: 2,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        auto_replenishment: false,
    })
    .unwrap();

    assert!(!limiter2.is_auto_replenishing());
    assert_eq!(limiter2.replenishment_period(), replenish_period2);
}

// ============================================================================
// NOTE: Additional tests to be added
// ============================================================================

// Total tests to port: ~50 from TokenBucketRateLimiterTests.cs
// Current progress: 10 / 50 tests implemented
//
// Remaining test categories:
// - Queue ordering (OldestFirst/NewestFirst)
// - Cancellation handling
// - Statistics tracking
// - Zero token edge cases
// - Integer overflow edge cases
// - Auto-replenishment timing
// - Multiple token dequeuing
