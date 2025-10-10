//! Fixed window rate limiter implementation.
//!
//! This module provides a rate limiter that uses the fixed window algorithm.
//! Each window has a fixed duration and permit count. When the window expires,
//! permits are reset to the full limit.

use crate::core::traits::{RateLimiter, ReplenishingRateLimiter};
use crate::core::{QueueProcessingOrder, RateLimitError, RateLimitLease, RateLimiterStatistics};
use async_trait::async_trait;
use parking_lot::Mutex;
use std::collections::VecDeque;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::oneshot;
use tokio_util::sync::CancellationToken;

/// Options for configuring a `FixedWindowRateLimiter`.
#[derive(Clone, Debug)]
pub struct FixedWindowRateLimiterOptions {
    /// Maximum number of permits available per window.
    pub permit_limit: u32,

    /// Duration of each window.
    pub window: Duration,

    /// Maximum number of permits that can be queued.
    pub queue_limit: u32,

    /// Order in which queued requests are processed.
    pub queue_processing_order: QueueProcessingOrder,

    /// If true, windows automatically advance on a timer.
    /// If false, `try_replenish()` must be called manually to advance windows.
    pub auto_replenishment: bool,
}

impl FixedWindowRateLimiterOptions {
    /// Create new fixed window limiter options with validation.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - `permit_limit` is 0
    /// - `window` is zero
    pub fn new(
        permit_limit: u32,
        window: Duration,
        queue_limit: u32,
        queue_processing_order: QueueProcessingOrder,
        auto_replenishment: bool,
    ) -> Result<Self, RateLimitError> {
        if permit_limit == 0 {
            return Err(RateLimitError::InvalidParameter(
                "permit_limit must be greater than 0".to_string(),
            ));
        }

        if window.is_zero() {
            return Err(RateLimitError::InvalidParameter(
                "window must be greater than zero".to_string(),
            ));
        }

        Ok(Self {
            permit_limit,
            window,
            queue_limit,
            queue_processing_order,
            auto_replenishment,
        })
    }
}

/// Internal state for the fixed window limiter.
struct State {
    /// Number of permits currently available in this window.
    available_permits: u32,

    /// Start time of the current window.
    window_start: Instant,

    /// Queue of pending requests waiting for permits.
    queue: VecDeque<QueuedRequest>,

    /// Total number of permits currently in the queue.
    queue_count: u32,

    /// Time when the window became full (all permits available).
    idle_since: Option<Instant>,

    /// Whether the limiter has been disposed.
    disposed: bool,
}

/// A queued request waiting for permits.
struct QueuedRequest {
    /// Number of permits requested.
    permit_count: u32,

    /// Channel to send the result when permits become available.
    response: oneshot::Sender<Result<RateLimitLease, RateLimitError>>,
}

/// A rate limiter that uses the fixed window algorithm.
///
/// The `FixedWindowRateLimiter` divides time into fixed windows. Each window
/// has a maximum number of permits that can be acquired. When a window expires,
/// the permit count resets to the full limit.
pub struct FixedWindowRateLimiter {
    /// Shared mutable state.
    state: Arc<Mutex<State>>,

    /// Configuration options.
    config: FixedWindowRateLimiterOptions,

    /// Counter for successful lease acquisitions.
    successful_leases: Arc<AtomicU64>,

    /// Counter for failed lease acquisitions.
    failed_leases: Arc<AtomicU64>,

    /// Cancellation token for stopping the replenishment timer.
    replenishment_cancel: CancellationToken,
}

impl FixedWindowRateLimiter {
    /// Create a new fixed window limiter with the specified options.
    ///
    /// # Errors
    ///
    /// Returns an error if the options are invalid.
    pub fn new(options: FixedWindowRateLimiterOptions) -> Result<Self, RateLimitError> {
        // Validate options
        if options.permit_limit == 0 {
            return Err(RateLimitError::InvalidParameter(
                "permit_limit must be greater than 0".to_string(),
            ));
        }

        if options.window.is_zero() {
            return Err(RateLimitError::InvalidParameter(
                "window must be greater than zero".to_string(),
            ));
        }

        let now = Instant::now();
        let state = State {
            available_permits: options.permit_limit,
            window_start: now,
            queue: VecDeque::new(),
            queue_count: 0,
            idle_since: Some(now),
            disposed: false,
        };

        Ok(Self {
            state: Arc::new(Mutex::new(state)),
            config: options,
            successful_leases: Arc::new(AtomicU64::new(0)),
            failed_leases: Arc::new(AtomicU64::new(0)),
            replenishment_cancel: CancellationToken::new(),
        })
    }

    /// Run the automatic replenishment timer.
    ///
    /// This method should be spawned as a background task when auto-replenishment
    /// is enabled. It periodically advances to the next window.
    pub async fn run_replenishment_timer(&self) {
        let mut interval = tokio::time::interval(self.config.window);
        let cancel = self.replenishment_cancel.clone();

        loop {
            tokio::select! {
                _ = interval.tick() => {
                    self.replenish();
                }
                _ = cancel.cancelled() => {
                    break;
                }
            }
        }
    }

    /// Replenish permits by advancing to a new window.
    fn replenish(&self) {
        let mut state = self.state.lock();

        if state.disposed {
            return;
        }

        // Reset to full permits for the new window
        state.available_permits = self.config.permit_limit;
        state.window_start = Instant::now();

        // Update idle tracking
        if state.available_permits == self.config.permit_limit && state.idle_since.is_none() {
            state.idle_since = Some(state.window_start);
        }

        // Process queue with the new permits
        self.process_queue_internal(&mut state);
    }

    /// Check if the current window has expired (for manual mode).
    fn check_window_expiration(&self, state: &mut State) {
        if !self.config.auto_replenishment {
            let elapsed = Instant::now().duration_since(state.window_start);
            if elapsed >= self.config.window {
                // Window expired, reset
                state.available_permits = self.config.permit_limit;
                state.window_start = Instant::now();

                // Update idle tracking
                if state.available_permits == self.config.permit_limit && state.idle_since.is_none() {
                    state.idle_since = Some(state.window_start);
                }
            }
        }
    }

    /// Process queued requests (single location for all queue logic).
    fn process_queue_internal(&self, state: &mut State) {
        while !state.queue.is_empty() {
            // Check next request based on processing order
            let next = match self.config.queue_processing_order {
                QueueProcessingOrder::OldestFirst => state.queue.front(),
                QueueProcessingOrder::NewestFirst => state.queue.back(),
            };

            let Some(next_req) = next else {
                break;
            };

            // Skip closed/cancelled requests
            if next_req.response.is_closed() {
                let req = match self.config.queue_processing_order {
                    QueueProcessingOrder::OldestFirst => state.queue.pop_front(),
                    QueueProcessingOrder::NewestFirst => state.queue.pop_back(),
                };

                if let Some(req) = req {
                    state.queue_count -= req.permit_count;
                }
                continue;
            }

            // Check if we have enough permits
            if state.available_permits >= next_req.permit_count {
                let req = match self.config.queue_processing_order {
                    QueueProcessingOrder::OldestFirst => state.queue.pop_front(),
                    QueueProcessingOrder::NewestFirst => state.queue.pop_back(),
                }.unwrap();

                state.available_permits -= req.permit_count;
                state.queue_count -= req.permit_count;
                state.idle_since = None;

                // Send lease (no cleanup needed - permits don't return)
                let lease = self.create_lease(req.permit_count);
                let _ = req.response.send(Ok(lease));
                self.successful_leases.fetch_add(1, Ordering::Relaxed);
            } else {
                // Not enough permits for next request
                break;
            }
        }
    }

    /// Create a lease (no cleanup needed for fixed window).
    fn create_lease(&self, permit_count: u32) -> RateLimitLease {
        if permit_count == 0 {
            RateLimitLease::success()
        } else {
            // Permits are consumed for this window, no cleanup callback needed
            RateLimitLease::success()
        }
    }

    /// Calculate retry-after duration for failed requests.
    fn calculate_retry_after(&self, state: &State, permit_count: u32) -> Duration {
        // Calculate time remaining in current window
        let elapsed = Instant::now().duration_since(state.window_start);
        let remaining_in_window = self.config.window.saturating_sub(elapsed);

        // If we have enough permits in this window, retry immediately
        if state.available_permits >= permit_count {
            return Duration::ZERO;
        }

        // If the request fits in a fresh window, wait for next window
        if permit_count <= self.config.permit_limit {
            return remaining_in_window;
        }

        // Request exceeds window capacity, cannot be satisfied
        // Return the window duration as a reasonable retry time
        self.config.window
    }

    /// Try to acquire permits immediately.
    fn try_acquire_immediate(&self, state: &mut State, permit_count: u32) -> Option<RateLimitLease> {
        if state.disposed {
            return None;
        }

        // Check window expiration in manual mode
        self.check_window_expiration(state);

        // Special case: permit_count == 0 for state checking
        if permit_count == 0 && state.available_permits > 0 {
            self.successful_leases.fetch_add(1, Ordering::Relaxed);
            return Some(RateLimitLease::success());
        }

        // Check if we have enough permits and can acquire immediately
        if state.available_permits >= permit_count && permit_count > 0 {
            // Can acquire if no queue or if we process newest first
            if state.queue.is_empty()
                || self.config.queue_processing_order == QueueProcessingOrder::NewestFirst
            {
                state.available_permits -= permit_count;
                state.idle_since = None;
                self.successful_leases.fetch_add(1, Ordering::Relaxed);

                // Create lease (no cleanup needed)
                return Some(self.create_lease(permit_count));
            }
        }

        None
    }
}

#[async_trait]
impl RateLimiter for FixedWindowRateLimiter {
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError> {
        // Check if request exceeds capacity
        if permit_count > self.config.permit_limit {
            return Err(RateLimitError::PermitCountExceeded(
                permit_count,
                self.config.permit_limit,
            ));
        }

        let mut state = self.state.lock();

        if state.disposed {
            return Err(RateLimitError::Disposed);
        }

        // Special case: permit_count == 0 for checking limiter state
        if permit_count == 0 {
            // Check window expiration in manual mode
            self.check_window_expiration(&mut state);

            if state.available_permits > 0 {
                self.successful_leases.fetch_add(1, Ordering::Relaxed);
                return Ok(RateLimitLease::success());
            } else {
                self.failed_leases.fetch_add(1, Ordering::Relaxed);
                let retry_after = self.calculate_retry_after(&state, 1);
                return Ok(RateLimitLease::failed(Some(retry_after)));
            }
        }

        // Try to acquire permits immediately
        if let Some(lease) = self.try_acquire_immediate(&mut state, permit_count) {
            return Ok(lease);
        }

        // Cannot acquire immediately - return failed with retry-after
        self.failed_leases.fetch_add(1, Ordering::Relaxed);
        let retry_after = self.calculate_retry_after(&state, permit_count);
        Ok(RateLimitLease::failed(Some(retry_after)))
    }

    async fn acquire_async(
        &self,
        permit_count: u32,
        cancel_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError> {
        // Check if request exceeds capacity
        if permit_count > self.config.permit_limit {
            return Err(RateLimitError::PermitCountExceeded(
                permit_count,
                self.config.permit_limit,
            ));
        }

        // Try immediate acquisition first
        let rx = {
            let mut state = self.state.lock();

            if state.disposed {
                return Err(RateLimitError::Disposed);
            }

            // Try to acquire immediately
            if let Some(lease) = self.try_acquire_immediate(&mut state, permit_count) {
                return Ok(lease);
            }

            // Check queue limit
            if state.queue_count + permit_count > self.config.queue_limit {
                // Handle NewestFirst eviction
                if self.config.queue_processing_order == QueueProcessingOrder::NewestFirst
                    && permit_count <= self.config.queue_limit
                {
                    // Evict oldest requests to make room
                    while state.queue_count + permit_count > self.config.queue_limit {
                        if let Some(oldest) = state.queue.pop_front() {
                            state.queue_count -= oldest.permit_count;

                            // Notify the evicted request that it failed
                            let retry_after = self.calculate_retry_after(&state, oldest.permit_count);
                            let _ = oldest.response.send(Ok(RateLimitLease::failed(Some(retry_after))));
                            self.failed_leases.fetch_add(1, Ordering::Relaxed);
                        } else {
                            break;
                        }
                    }
                } else {
                    // Queue is full and we can't evict - return a failed lease
                    self.failed_leases.fetch_add(1, Ordering::Relaxed);
                    let retry_after = self.calculate_retry_after(&state, permit_count);
                    return Ok(RateLimitLease::failed(Some(retry_after)));
                }
            }

            // Create queued request
            let (tx, rx) = oneshot::channel();
            let request = QueuedRequest {
                permit_count,
                response: tx,
            };

            state.queue.push_back(request);
            state.queue_count += permit_count;

            rx
        };

        // Wait for permits or cancellation (outside the lock)
        if let Some(token) = cancel_token {
            tokio::select! {
                result = rx => {
                    match result {
                        Ok(lease_result) => lease_result,
                        Err(_) => Err(RateLimitError::Cancelled),
                    }
                }
                _ = token.cancelled() => {
                    // Handle cancellation - try to remove from queue
                    let mut state = self.state.lock();

                    // Find and remove the cancelled request
                    let mut found_index = None;
                    for (i, req) in state.queue.iter().enumerate() {
                        if req.response.is_closed() {
                            found_index = Some(i);
                            break;
                        }
                    }

                    if let Some(idx) = found_index {
                        if let Some(req) = state.queue.remove(idx) {
                            state.queue_count -= req.permit_count;
                        }
                    }

                    Err(RateLimitError::Cancelled)
                }
            }
        } else {
            // No cancellation token, just wait
            match rx.await {
                Ok(lease_result) => lease_result,
                Err(_) => Err(RateLimitError::Cancelled),
            }
        }
    }

    fn get_statistics(&self) -> RateLimiterStatistics {
        let state = self.state.lock();

        RateLimiterStatistics {
            current_available_permits: state.available_permits as i64,
            current_queued_count: state.queue_count,
            total_successful_leases: self.successful_leases.load(Ordering::Relaxed),
            total_failed_leases: self.failed_leases.load(Ordering::Relaxed),
        }
    }

    fn idle_duration(&self) -> Option<Duration> {
        let state = self.state.lock();
        state.idle_since.map(|since| since.elapsed())
    }
}

impl ReplenishingRateLimiter for FixedWindowRateLimiter {
    fn is_auto_replenishing(&self) -> bool {
        self.config.auto_replenishment
    }

    fn replenishment_period(&self) -> Duration {
        self.config.window
    }

    fn try_replenish(&self) -> bool {
        if self.config.auto_replenishment {
            // Cannot manually replenish when auto-replenishment is enabled
            false
        } else {
            self.replenish();
            true
        }
    }
}

impl Drop for FixedWindowRateLimiter {
    fn drop(&mut self) {
        // Cancel the replenishment timer
        self.replenishment_cancel.cancel();

        let mut state = self.state.lock();
        state.disposed = true;

        // Fail all queued requests
        while let Some(request) = state.queue.pop_front() {
            state.queue_count -= request.permit_count;
            let retry_after = self.calculate_retry_after(&state, request.permit_count);
            let _ = request.response.send(Ok(RateLimitLease::failed(Some(retry_after))));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::QueueProcessingOrder;
    use std::sync::Arc;
    use std::time::Duration;
    use tokio::time::sleep;

    #[tokio::test]
    async fn test_fixed_window_basic() {
        // Create limiter with 10 permits per 100ms window
        let options = FixedWindowRateLimiterOptions::new(
            10,  // permit_limit
            Duration::from_millis(100),  // window
            20,  // queue_limit
            QueueProcessingOrder::OldestFirst,
            true,  // auto_replenishment
        )
        .unwrap();

        let limiter = Arc::new(FixedWindowRateLimiter::new(options).unwrap());

        // Spawn replenishment timer
        let limiter_clone = Arc::clone(&limiter);
        tokio::spawn(async move {
            limiter_clone.run_replenishment_timer().await;
        });

        // Should succeed - we start with 10 permits
        let lease1 = limiter.attempt_acquire(5).unwrap();
        assert!(lease1.is_acquired());

        // Should succeed - we have 5 permits left
        let lease2 = limiter.attempt_acquire(5).unwrap();
        assert!(lease2.is_acquired());

        // Should fail - no permits left
        let lease3 = limiter.attempt_acquire(1).unwrap();
        assert!(!lease3.is_acquired());

        // Check retry-after metadata
        let retry_after = lease3.try_get_metadata::<Duration>("RetryAfter");
        assert!(retry_after.is_some());

        // Wait for next window
        sleep(Duration::from_millis(150)).await;

        // Should succeed after window reset
        let lease4 = limiter.attempt_acquire(10).unwrap();
        assert!(lease4.is_acquired());
    }

    #[tokio::test]
    async fn test_manual_replenishment() {
        // Create limiter with manual replenishment
        let options = FixedWindowRateLimiterOptions::new(
            10,  // permit_limit
            Duration::from_millis(100),  // window
            20,  // queue_limit
            QueueProcessingOrder::OldestFirst,
            false,  // auto_replenishment - MANUAL mode
        )
        .unwrap();

        let limiter = FixedWindowRateLimiter::new(options).unwrap();

        // Use all permits
        let lease1 = limiter.attempt_acquire(10).unwrap();
        assert!(lease1.is_acquired());

        // Should fail - no permits
        let lease2 = limiter.attempt_acquire(1).unwrap();
        assert!(!lease2.is_acquired());

        // Wait for window to expire
        sleep(Duration::from_millis(110)).await;

        // Manually replenish
        assert!(limiter.try_replenish());

        // Should succeed after manual replenishment
        let lease3 = limiter.attempt_acquire(10).unwrap();
        assert!(lease3.is_acquired());
    }

    #[test]
    fn test_auto_replenishment_prevents_manual() {
        let options = FixedWindowRateLimiterOptions::new(
            10,  // permit_limit
            Duration::from_millis(100),  // window
            20,  // queue_limit
            QueueProcessingOrder::OldestFirst,
            true,  // auto_replenishment - AUTO mode
        )
        .unwrap();

        let limiter = FixedWindowRateLimiter::new(options).unwrap();

        // Should return false when auto-replenishment is enabled
        assert!(!limiter.try_replenish());
    }

    #[tokio::test]
    async fn test_window_expiration_in_manual_mode() {
        // Create limiter with manual mode
        let options = FixedWindowRateLimiterOptions::new(
            10,  // permit_limit
            Duration::from_millis(100),  // window
            20,  // queue_limit
            QueueProcessingOrder::OldestFirst,
            false,  // auto_replenishment - MANUAL mode
        )
        .unwrap();

        let limiter = FixedWindowRateLimiter::new(options).unwrap();

        // Use all permits
        let lease1 = limiter.attempt_acquire(10).unwrap();
        assert!(lease1.is_acquired());

        // Should fail - no permits
        let lease2 = limiter.attempt_acquire(1).unwrap();
        assert!(!lease2.is_acquired());

        // Wait for window to expire
        sleep(Duration::from_millis(110)).await;

        // Should succeed - window auto-expired on attempt
        let lease3 = limiter.attempt_acquire(10).unwrap();
        assert!(lease3.is_acquired());
    }
}