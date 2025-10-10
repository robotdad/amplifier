//! Token bucket rate limiter implementation.
//!
//! This module provides a rate limiter that uses the token bucket algorithm.
//! Tokens are added to the bucket at a fixed rate and consumed when permits
//! are acquired. Unlike concurrency limiters, tokens are not returned when
//! leases are dropped.

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

/// Options for configuring a `TokenBucketRateLimiter`.
#[derive(Clone, Debug)]
pub struct TokenBucketRateLimiterOptions {
    /// Maximum number of tokens that can be stored in the bucket.
    pub token_limit: u32,

    /// Number of tokens added to the bucket each replenishment period.
    pub tokens_per_period: u32,

    /// How frequently tokens are added to the bucket.
    pub replenishment_period: Duration,

    /// Maximum number of tokens that can be queued.
    pub queue_limit: u32,

    /// Order in which queued requests are processed.
    pub queue_processing_order: QueueProcessingOrder,

    /// If true, tokens are automatically replenished on a timer.
    /// If false, `try_replenish()` must be called manually.
    pub auto_replenishment: bool,
}

impl TokenBucketRateLimiterOptions {
    /// Create new token bucket limiter options with validation.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - `token_limit` is 0
    /// - `tokens_per_period` is 0
    /// - `replenishment_period` is zero
    pub fn new(
        token_limit: u32,
        tokens_per_period: u32,
        replenishment_period: Duration,
        queue_limit: u32,
        queue_processing_order: QueueProcessingOrder,
        auto_replenishment: bool,
    ) -> Result<Self, RateLimitError> {
        if token_limit == 0 {
            return Err(RateLimitError::InvalidParameter(
                "token_limit must be greater than 0".to_string(),
            ));
        }

        if tokens_per_period == 0 {
            return Err(RateLimitError::InvalidParameter(
                "tokens_per_period must be greater than 0".to_string(),
            ));
        }

        if replenishment_period.is_zero() {
            return Err(RateLimitError::InvalidParameter(
                "replenishment_period must be greater than zero".to_string(),
            ));
        }

        Ok(Self {
            token_limit,
            tokens_per_period,
            replenishment_period,
            queue_limit,
            queue_processing_order,
            auto_replenishment,
        })
    }
}

/// Internal state for the token bucket limiter.
struct State {
    /// Number of tokens currently available (fractional for fill rate).
    available_tokens: f64,

    /// Queue of pending requests waiting for tokens.
    queue: VecDeque<QueuedRequest>,

    /// Total number of tokens currently in the queue.
    queue_count: u32,

    /// Last time tokens were replenished.
    last_replenishment: Instant,

    /// Time when the bucket became full (all tokens available).
    idle_since: Option<Instant>,

    /// Whether the limiter has been disposed.
    disposed: bool,
}

/// A queued request waiting for tokens.
struct QueuedRequest {
    /// Number of tokens requested.
    token_count: u32,

    /// Channel to send the result when tokens become available.
    response: oneshot::Sender<Result<RateLimitLease, RateLimitError>>,
}

/// A rate limiter that uses the token bucket algorithm.
///
/// The `TokenBucketRateLimiter` maintains a bucket of tokens that are
/// replenished at a fixed rate. Tokens are consumed when permits are
/// acquired and are not returned when leases are dropped.
pub struct TokenBucketRateLimiter {
    /// Shared mutable state.
    state: Arc<Mutex<State>>,

    /// Configuration options.
    config: TokenBucketRateLimiterOptions,

    /// Counter for successful lease acquisitions.
    successful_leases: Arc<AtomicU64>,

    /// Counter for failed lease acquisitions.
    failed_leases: Arc<AtomicU64>,

    /// Cancellation token for stopping the replenishment timer.
    replenishment_cancel: CancellationToken,
}

impl TokenBucketRateLimiter {
    /// Create a new token bucket limiter with the specified options.
    ///
    /// # Errors
    ///
    /// Returns an error if the options are invalid.
    pub fn new(options: TokenBucketRateLimiterOptions) -> Result<Self, RateLimitError> {
        // Validate options
        if options.token_limit == 0 {
            return Err(RateLimitError::InvalidParameter(
                "token_limit must be greater than 0".to_string(),
            ));
        }

        if options.tokens_per_period == 0 {
            return Err(RateLimitError::InvalidParameter(
                "tokens_per_period must be greater than 0".to_string(),
            ));
        }

        if options.replenishment_period.is_zero() {
            return Err(RateLimitError::InvalidParameter(
                "replenishment_period must be greater than zero".to_string(),
            ));
        }

        let now = Instant::now();
        let state = State {
            available_tokens: options.token_limit as f64,
            queue: VecDeque::new(),
            queue_count: 0,
            last_replenishment: now,
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
    /// is enabled. It periodically adds tokens to the bucket.
    pub async fn run_replenishment_timer(&self) {
        let mut interval = tokio::time::interval(self.config.replenishment_period);
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

    /// Replenish tokens in the bucket.
    fn replenish(&self) {
        let mut state = self.state.lock();

        if state.disposed {
            return;
        }

        let now = Instant::now();
        let tokens_to_add = if self.config.auto_replenishment {
            // Auto-replenishment: Calculate based on elapsed time
            let elapsed = now.duration_since(state.last_replenishment);
            let periods = elapsed.as_secs_f64() / self.config.replenishment_period.as_secs_f64();
            periods * self.config.tokens_per_period as f64
        } else {
            // Manual replenishment: Always add fixed tokens_per_period
            self.config.tokens_per_period as f64
        };

        if tokens_to_add > 0.0 {
            // Add tokens (up to limit)
            state.available_tokens = (state.available_tokens + tokens_to_add)
                .min(self.config.token_limit as f64);
            state.last_replenishment = now;

            // Update idle tracking
            if state.available_tokens >= self.config.token_limit as f64 - 0.001
                && state.idle_since.is_none()
            {
                state.idle_since = Some(now);
            }

            // Process queue
            self.process_queue_internal(&mut state);
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
                    state.queue_count -= req.token_count;
                }
                continue;
            }

            // Check if we have enough tokens
            if state.available_tokens >= next_req.token_count as f64 {
                let req = match self.config.queue_processing_order {
                    QueueProcessingOrder::OldestFirst => state.queue.pop_front(),
                    QueueProcessingOrder::NewestFirst => state.queue.pop_back(),
                }.unwrap();

                state.available_tokens -= req.token_count as f64;
                state.queue_count -= req.token_count;
                state.idle_since = None;

                // Send lease (no cleanup needed - tokens don't return)
                let lease = self.create_lease(req.token_count);
                let _ = req.response.send(Ok(lease));
                self.successful_leases.fetch_add(1, Ordering::Relaxed);
            } else {
                // Not enough tokens for next request
                break;
            }
        }
    }

    /// Create a lease (no cleanup needed for token bucket).
    fn create_lease(&self, token_count: u32) -> RateLimitLease {
        if token_count == 0 {
            RateLimitLease::success()
        } else {
            // Tokens are not returned, so no cleanup callback
            RateLimitLease::success()
        }
    }

    /// Calculate retry-after duration for failed requests.
    fn calculate_retry_after(&self, state: &State, token_count: u32) -> Duration {
        // Calculate how many tokens we need beyond what's available
        let tokens_needed = (token_count as f64 - state.available_tokens).max(0.0);

        // Account for queued tokens
        let total_tokens_needed = tokens_needed + state.queue_count as f64;

        // Calculate how many periods we need to wait
        let periods_needed = (total_tokens_needed / self.config.tokens_per_period as f64).ceil() as u32;
        let periods = periods_needed.max(1);

        self.config.replenishment_period * periods
    }

    /// Try to acquire tokens immediately.
    fn try_acquire_immediate(&self, state: &mut State, token_count: u32) -> Option<RateLimitLease> {
        if state.disposed {
            return None;
        }

        // Special case: token_count == 0 for state checking
        if token_count == 0 && state.available_tokens > 0.0 {
            self.successful_leases.fetch_add(1, Ordering::Relaxed);
            return Some(RateLimitLease::success());
        }

        // Check if we have enough tokens and can acquire immediately
        if state.available_tokens >= token_count as f64 && token_count > 0 {
            // Can acquire if no queue or if we process newest first
            if state.queue.is_empty()
                || self.config.queue_processing_order == QueueProcessingOrder::NewestFirst
            {
                state.available_tokens -= token_count as f64;
                state.idle_since = None;
                self.successful_leases.fetch_add(1, Ordering::Relaxed);

                // Create lease (no cleanup needed)
                return Some(self.create_lease(token_count));
            }
        }

        None
    }
}

#[async_trait]
impl RateLimiter for TokenBucketRateLimiter {
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError> {
        // Tokens are called permits in the trait interface
        let token_count = permit_count;

        // Check if request exceeds capacity
        if token_count > self.config.token_limit {
            return Err(RateLimitError::PermitCountExceeded(
                token_count,
                self.config.token_limit,
            ));
        }

        let mut state = self.state.lock();

        if state.disposed {
            return Err(RateLimitError::Disposed);
        }

        // Special case: token_count == 0 for checking limiter state
        if token_count == 0 {
            if state.available_tokens > 0.0 {
                self.successful_leases.fetch_add(1, Ordering::Relaxed);
                return Ok(RateLimitLease::success());
            } else {
                self.failed_leases.fetch_add(1, Ordering::Relaxed);
                let retry_after = self.calculate_retry_after(&state, 1);
                return Ok(RateLimitLease::failed(Some(retry_after)));
            }
        }

        // Try to acquire tokens immediately
        if let Some(lease) = self.try_acquire_immediate(&mut state, token_count) {
            return Ok(lease);
        }

        // Cannot acquire immediately - return failed with retry-after
        self.failed_leases.fetch_add(1, Ordering::Relaxed);
        let retry_after = self.calculate_retry_after(&state, token_count);
        Ok(RateLimitLease::failed(Some(retry_after)))
    }

    async fn acquire_async(
        &self,
        permit_count: u32,
        cancel_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError> {
        // Tokens are called permits in the trait interface
        let token_count = permit_count;

        // Check if request exceeds capacity
        if token_count > self.config.token_limit {
            return Err(RateLimitError::PermitCountExceeded(
                token_count,
                self.config.token_limit,
            ));
        }

        // Try immediate acquisition first
        let rx = {
            let mut state = self.state.lock();

            if state.disposed {
                return Err(RateLimitError::Disposed);
            }

            // Try to acquire immediately
            if let Some(lease) = self.try_acquire_immediate(&mut state, token_count) {
                return Ok(lease);
            }

            // Check queue limit
            if state.queue_count + token_count > self.config.queue_limit {
                // Handle NewestFirst eviction
                if self.config.queue_processing_order == QueueProcessingOrder::NewestFirst
                    && token_count <= self.config.queue_limit
                {
                    // Evict oldest requests to make room
                    while state.queue_count + token_count > self.config.queue_limit {
                        if let Some(oldest) = state.queue.pop_front() {
                            state.queue_count -= oldest.token_count;

                            // Notify the evicted request that it failed
                            let retry_after = self.calculate_retry_after(&state, oldest.token_count);
                            let _ = oldest.response.send(Ok(RateLimitLease::failed(Some(retry_after))));
                            self.failed_leases.fetch_add(1, Ordering::Relaxed);
                        } else {
                            break;
                        }
                    }
                } else {
                    // Queue is full and we can't evict - return a failed lease
                    self.failed_leases.fetch_add(1, Ordering::Relaxed);
                    let retry_after = self.calculate_retry_after(&state, token_count);
                    return Ok(RateLimitLease::failed(Some(retry_after)));
                }
            }

            // Create queued request
            let (tx, rx) = oneshot::channel();
            let request = QueuedRequest {
                token_count,
                response: tx,
            };

            state.queue.push_back(request);
            state.queue_count += token_count;

            rx
        };

        // Wait for tokens or cancellation (outside the lock)
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
                            state.queue_count -= req.token_count;
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
            current_available_permits: state.available_tokens as i64,
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

impl ReplenishingRateLimiter for TokenBucketRateLimiter {
    fn is_auto_replenishing(&self) -> bool {
        self.config.auto_replenishment
    }

    fn replenishment_period(&self) -> Duration {
        self.config.replenishment_period
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

impl Drop for TokenBucketRateLimiter {
    fn drop(&mut self) {
        // Cancel the replenishment timer
        self.replenishment_cancel.cancel();

        let mut state = self.state.lock();
        state.disposed = true;

        // Fail all queued requests
        while let Some(request) = state.queue.pop_front() {
            state.queue_count -= request.token_count;
            let retry_after = self.calculate_retry_after(&state, request.token_count);
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
    async fn test_token_bucket_basic() {
        // Create limiter with 10 tokens, adding 5 every 100ms
        let options = TokenBucketRateLimiterOptions::new(
            10,  // token_limit
            5,   // tokens_per_period
            Duration::from_millis(100),  // replenishment_period
            20,  // queue_limit
            QueueProcessingOrder::OldestFirst,
            true,  // auto_replenishment
        )
        .unwrap();

        let limiter = Arc::new(TokenBucketRateLimiter::new(options).unwrap());

        // Spawn replenishment timer
        let limiter_clone = Arc::clone(&limiter);
        tokio::spawn(async move {
            limiter_clone.run_replenishment_timer().await;
        });

        // Should succeed - we start with 10 tokens
        let lease1 = limiter.attempt_acquire(5).unwrap();
        assert!(lease1.is_acquired());

        // Should succeed - we have 5 tokens left
        let lease2 = limiter.attempt_acquire(5).unwrap();
        assert!(lease2.is_acquired());

        // Should fail - no tokens left
        let lease3 = limiter.attempt_acquire(1).unwrap();
        assert!(!lease3.is_acquired());

        // Check retry-after metadata
        let retry_after = lease3.try_get_metadata::<Duration>("RetryAfter");
        assert!(retry_after.is_some());

        // Wait for replenishment
        sleep(Duration::from_millis(150)).await;

        // Should succeed after replenishment
        let lease4 = limiter.attempt_acquire(5).unwrap();
        assert!(lease4.is_acquired());
    }

    #[tokio::test]
    async fn test_manual_replenishment() {
        // Create limiter with manual replenishment
        let options = TokenBucketRateLimiterOptions::new(
            10,  // token_limit
            5,   // tokens_per_period
            Duration::from_millis(100),  // replenishment_period
            20,  // queue_limit
            QueueProcessingOrder::OldestFirst,
            false,  // auto_replenishment - MANUAL mode
        )
        .unwrap();

        let limiter = TokenBucketRateLimiter::new(options).unwrap();

        // Use all tokens
        let lease1 = limiter.attempt_acquire(10).unwrap();
        assert!(lease1.is_acquired());

        // Should fail - no tokens
        let lease2 = limiter.attempt_acquire(1).unwrap();
        assert!(!lease2.is_acquired());

        // Wait a bit to accumulate replenishment time
        sleep(Duration::from_millis(110)).await;

        // Manually replenish
        assert!(limiter.try_replenish());

        // Should succeed after manual replenishment
        let lease3 = limiter.attempt_acquire(5).unwrap();
        assert!(lease3.is_acquired());
    }

    #[test]
    fn test_auto_replenishment_prevents_manual() {
        let options = TokenBucketRateLimiterOptions::new(
            10,  // token_limit
            5,   // tokens_per_period
            Duration::from_millis(100),  // replenishment_period
            20,  // queue_limit
            QueueProcessingOrder::OldestFirst,
            true,  // auto_replenishment - AUTO mode
        )
        .unwrap();

        let limiter = TokenBucketRateLimiter::new(options).unwrap();

        // Should return false when auto-replenishment is enabled
        assert!(!limiter.try_replenish());
    }
}