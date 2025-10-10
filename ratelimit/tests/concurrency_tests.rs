//! Tests for ConcurrencyLimiter
//!
//! Ported from: System.Threading.RateLimiting.Test.ConcurrencyLimiterTests

use ratelimit::{
    ConcurrencyLimiter, ConcurrencyLimiterOptions, QueueProcessingOrder, RateLimitError,
    RateLimiter,
};
use std::sync::Arc;
use tokio_util::sync::CancellationToken;

mod common;

// Helper to create a limiter with queue processor for async tests
async fn create_limiter_with_processor(
    options: ConcurrencyLimiterOptions,
) -> Arc<ConcurrencyLimiter> {
    let limiter = Arc::new(ConcurrencyLimiter::new(options).unwrap());
    let clone = Arc::clone(&limiter);
    tokio::spawn(async move { clone.run_queue_processor().await });
    // Give processor time to start
    tokio::time::sleep(tokio::time::Duration::from_millis(1)).await;
    limiter
}

// ============================================================================
// VALIDATION TESTS
// ============================================================================

#[test]
fn invalid_options_throws() {
    // Negative permit limit
    let result = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 0, // Invalid: must be > 0
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    });
    assert!(matches!(result, Err(RateLimitError::InvalidParameter(_))));

    // Negative queue limit would be caught by type system (u32), so test boundary
    let result = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 0, // Valid: 0 means no queueing
    });
    assert!(result.is_ok());
}

// ============================================================================
// BASIC ACQUIRE/RELEASE TESTS
// ============================================================================

#[test]
fn can_acquire_resource() {
    let limiter = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    })
    .unwrap();

    // First acquire succeeds
    let lease = limiter.attempt_acquire(1).unwrap();
    assert!(lease.is_acquired());

    // Second acquire fails (no permits available)
    let lease2 = limiter.attempt_acquire(1).unwrap();
    assert!(!lease2.is_acquired());

    // Drop first lease (returns permit)
    drop(lease);

    // Third acquire succeeds (permit available again)
    // Note: In sync mode without processor, permits aren't immediately available
    // This is expected behavior for sync mode
    let lease3 = limiter.attempt_acquire(1).unwrap();
    assert!(lease3.is_acquired());
}

#[tokio::test]
async fn can_acquire_resource_async() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    })
    .await;

    // First acquire succeeds
    let lease = limiter.acquire_async(1, None).await.unwrap();
    assert!(lease.is_acquired());

    // Second acquire is queued (not completed immediately)
    let limiter_clone = Arc::clone(&limiter);
    let wait_task = tokio::spawn(async move { limiter_clone.acquire_async(1, None).await });

    // Give it a moment to queue
    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    // Should not be completed yet
    assert!(!wait_task.is_finished());

    // Drop first lease (triggers queue processing)
    drop(lease);

    // Second acquire should complete successfully
    let lease2 = wait_task.await.unwrap().unwrap();
    assert!(lease2.is_acquired());
}

// ============================================================================
// QUEUE ORDERING TESTS
// ============================================================================

#[tokio::test]
async fn can_acquire_resource_async_queues_and_grabs_oldest() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 2,
    })
    .await;

    // Acquire first permit
    let lease = limiter.acquire_async(1, None).await.unwrap();
    assert!(lease.is_acquired());

    // Queue two requests
    let limiter_clone1 = Arc::clone(&limiter);
    let wait1 = tokio::spawn(async move { limiter_clone1.acquire_async(1, None).await });

    let limiter_clone2 = Arc::clone(&limiter);
    let wait2 = tokio::spawn(async move { limiter_clone2.acquire_async(1, None).await });

    // Give them time to queue
    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    assert!(!wait1.is_finished());
    assert!(!wait2.is_finished());

    // Release first permit
    drop(lease);

    // First queued request should complete (OldestFirst)
    let lease = wait1.await.unwrap().unwrap();
    assert!(lease.is_acquired());
    assert!(!wait2.is_finished());

    // Release second permit
    drop(lease);

    // Second queued request should complete
    let lease = wait2.await.unwrap().unwrap();
    assert!(lease.is_acquired());
}

#[tokio::test]
async fn can_acquire_resource_async_queues_and_grabs_newest() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 2,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 3,
    })
    .await;

    // Acquire all permits
    let lease = limiter.acquire_async(2, None).await.unwrap();
    assert!(lease.is_acquired());

    // Queue two requests
    let limiter_clone1 = Arc::clone(&limiter);
    let wait1 = tokio::spawn(async move { limiter_clone1.acquire_async(2, None).await });

    let limiter_clone2 = Arc::clone(&limiter);
    let wait2 = tokio::spawn(async move { limiter_clone2.acquire_async(1, None).await });

    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    assert!(!wait1.is_finished());
    assert!(!wait2.is_finished());

    // Release permits
    drop(lease);

    // Second queued request completes first (NewestFirst)
    let lease = wait2.await.unwrap().unwrap();
    assert!(lease.is_acquired());
    assert!(!wait1.is_finished());

    // Release permit
    drop(lease);

    // First queued request completes
    let lease = wait1.await.unwrap().unwrap();
    assert!(lease.is_acquired());
}

// ============================================================================
// ERROR HANDLING TESTS
// ============================================================================

#[test]
fn throws_when_acquiring_more_than_limit() {
    let limiter = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
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
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    })
    .await;

    let result = limiter.acquire_async(2, None).await;
    assert!(matches!(
        result,
        Err(RateLimitError::PermitCountExceeded(2, 1))
    ));
}

// ============================================================================
// ZERO PERMIT TESTS (Special Case)
// ============================================================================

#[test]
fn acquire_zero_with_availability() {
    let limiter = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    })
    .unwrap();

    // Acquiring 0 permits when permits are available should succeed
    let lease = limiter.attempt_acquire(0).unwrap();
    assert!(lease.is_acquired());
}

#[test]
fn acquire_zero_without_availability() {
    let limiter = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    })
    .unwrap();

    // Acquire the only permit
    let lease = limiter.attempt_acquire(1).unwrap();
    assert!(lease.is_acquired());

    // Acquiring 0 permits when no permits available should fail
    let lease2 = limiter.attempt_acquire(0).unwrap();
    assert!(!lease2.is_acquired());
}

#[tokio::test]
async fn acquire_async_zero_with_availability() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    })
    .await;

    // Acquiring 0 permits when permits are available should succeed
    let lease = limiter.acquire_async(0, None).await.unwrap();
    assert!(lease.is_acquired());
}

// ============================================================================
// CANCELLATION TESTS
// ============================================================================

#[tokio::test]
async fn can_cancel_acquire_async_after_queuing() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 1,
    })
    .await;

    // Acquire the permit
    let lease = limiter.attempt_acquire(1).unwrap();
    assert!(lease.is_acquired());

    // Queue a request with cancellation token
    let cancel_token = CancellationToken::new();
    let limiter_clone = Arc::clone(&limiter);
    let token_clone = cancel_token.clone();
    let wait_task =
        tokio::spawn(async move { limiter_clone.acquire_async(1, Some(token_clone)).await });

    // Give it time to queue
    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    // Cancel the request
    cancel_token.cancel();

    // Should get cancellation error
    let result = wait_task.await.unwrap();
    assert!(matches!(result, Err(RateLimitError::Cancelled)));

    // Release the original lease
    drop(lease);

    // Give processor time to handle the return
    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    // Verify permit is available (cancellation freed queue slot)
    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 1);
}

#[tokio::test]
async fn can_cancel_acquire_async_before_queuing() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 1,
    })
    .await;

    let lease = limiter.attempt_acquire(1).unwrap();
    assert!(lease.is_acquired());

    // Create already-cancelled token
    let cancel_token = CancellationToken::new();
    cancel_token.cancel();

    // Try to acquire with already-cancelled token
    let result = limiter.acquire_async(1, Some(cancel_token)).await;
    assert!(matches!(result, Err(RateLimitError::Cancelled)));

    // Release lease
    drop(lease);

    // Give processor time to handle the return
    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    // Verify permit is available
    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 1);
}

// ============================================================================
// STATISTICS TESTS
// ============================================================================

#[test]
fn get_statistics_returns_new_instances() {
    let limiter = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 1,
    })
    .unwrap();

    let stats1 = limiter.get_statistics();
    assert_eq!(stats1.current_available_permits, 1);

    let _lease = limiter.attempt_acquire(1).unwrap();

    let stats2 = limiter.get_statistics();
    // Each call returns a new instance with current values
    assert_eq!(stats1.current_available_permits, 1); // Original unchanged
    assert_eq!(stats2.current_available_permits, 0); // New reflects change
}

#[tokio::test]
async fn get_statistics_has_correct_values() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 100,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 50,
    })
    .await;

    // Initial state
    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 100);
    assert_eq!(stats.current_queued_count, 0);
    assert_eq!(stats.total_failed_leases, 0);
    assert_eq!(stats.total_successful_leases, 0);

    // Success from acquire
    let lease1 = limiter.attempt_acquire(60).unwrap();
    assert!(lease1.is_acquired());
    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 40);
    assert_eq!(stats.current_queued_count, 0);
    assert_eq!(stats.total_failed_leases, 0);
    assert_eq!(stats.total_successful_leases, 1);

    // Queue a request
    let limiter_clone = Arc::clone(&limiter);
    let lease2_task = tokio::spawn(async move { limiter_clone.acquire_async(50, None).await });

    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 40);
    assert_eq!(stats.current_queued_count, 50);
    assert_eq!(stats.total_failed_leases, 0);
    assert_eq!(stats.total_successful_leases, 1);

    // Failure from wait (queue full)
    let lease3 = limiter.acquire_async(1, None).await.unwrap();
    assert!(!lease3.is_acquired());
    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 40);
    assert_eq!(stats.current_queued_count, 50);
    assert_eq!(stats.total_failed_leases, 1);
    assert_eq!(stats.total_successful_leases, 1);

    // Failure from acquire
    let lease4 = limiter.attempt_acquire(100).unwrap();
    assert!(!lease4.is_acquired());
    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 40);
    assert_eq!(stats.current_queued_count, 50);
    assert_eq!(stats.total_failed_leases, 2);
    assert_eq!(stats.total_successful_leases, 1);

    // Release lease1 (queued request completes)
    drop(lease1);
    let lease2 = lease2_task.await.unwrap().unwrap();
    assert!(lease2.is_acquired());

    // Success from queued wait
    let stats = limiter.get_statistics();
    assert_eq!(stats.current_available_permits, 50);
    assert_eq!(stats.current_queued_count, 0);
    assert_eq!(stats.total_failed_leases, 2);
    assert_eq!(stats.total_successful_leases, 2);
}

// ============================================================================
// IDLE DURATION TESTS
// ============================================================================

#[test]
fn null_idle_duration_when_active() {
    let limiter = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 1,
    })
    .unwrap();

    let _lease = limiter.attempt_acquire(1).unwrap();

    // Should be None when permits are acquired
    assert!(limiter.idle_duration().is_none());
}

#[tokio::test]
async fn idle_duration_updates_when_idle() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 1,
    })
    .await;

    // Should have idle duration initially
    let duration1 = limiter.idle_duration();
    assert!(duration1.is_some());

    // Wait a bit
    tokio::time::sleep(tokio::time::Duration::from_millis(15)).await;

    // Idle duration should have increased
    let duration2 = limiter.idle_duration();
    assert!(duration2.is_some());
    assert!(duration2.unwrap() > duration1.unwrap());
}

#[test]
fn idle_duration_updates_when_changing_from_active() {
    let limiter = ConcurrencyLimiter::new(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 1,
    })
    .unwrap();

    // Acquire and release
    let lease = limiter.attempt_acquire(1).unwrap();
    drop(lease);

    // Should have idle duration after release
    // Note: In sync mode without processor, idle time is updated immediately
    assert!(limiter.idle_duration().is_some());
}

// ============================================================================
// QUEUE LIMIT TESTS
// ============================================================================

#[tokio::test]
async fn fails_when_queueing_more_than_limit_oldest_first() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::OldestFirst,
        queue_limit: 1,
    })
    .await;

    let _lease = limiter.attempt_acquire(1).unwrap();
    let limiter_clone = Arc::clone(&limiter);
    let _wait = tokio::spawn(async move { limiter_clone.acquire_async(1, None).await });

    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    // Queue is full, this should fail
    let failed_lease = limiter.acquire_async(1, None).await.unwrap();
    assert!(!failed_lease.is_acquired());
}

#[tokio::test]
async fn drops_oldest_when_queueing_more_than_limit_newest_first() {
    let limiter = create_limiter_with_processor(ConcurrencyLimiterOptions {
        permit_limit: 1,
        queue_processing_order: QueueProcessingOrder::NewestFirst,
        queue_limit: 1,
    })
    .await;

    let lease = limiter.attempt_acquire(1).unwrap();

    let limiter_clone1 = Arc::clone(&limiter);
    let wait1 = tokio::spawn(async move { limiter_clone1.acquire_async(1, None).await });

    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
    assert!(!wait1.is_finished());

    // This should evict wait1 (oldest)
    let limiter_clone2 = Arc::clone(&limiter);
    let wait2 = tokio::spawn(async move { limiter_clone2.acquire_async(1, None).await });

    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;

    // wait1 should have been evicted
    let lease1 = wait1.await.unwrap().unwrap();
    assert!(!lease1.is_acquired());
    assert!(!wait2.is_finished());

    // Release original lease
    drop(lease);

    // wait2 should complete successfully
    let lease2 = wait2.await.unwrap().unwrap();
    assert!(lease2.is_acquired());
}

// ============================================================================
// NOTE: Additional tests to be added
// ============================================================================

// Total tests to port: ~40 from ConcurrencyLimiterTests.cs
// Current progress: 19 / 40 tests implemented
//
// Remaining test categories:
// - Multiple permit dequeuing
// - Disposal behavior
// - Metadata handling
// - Integer overflow edge cases
// - Queue eviction edge cases
// - Concurrent acquire with queued items