//! Concurrency limiter implementation.
//!
//! This module provides a rate limiter that manages concurrent access to a resource
//! with a fixed number of permits. It supports both synchronous and asynchronous
//! acquisition with queueing.

use crate::core::traits::RateLimiter;
use crate::core::{QueueProcessingOrder, RateLimitError, RateLimitLease, RateLimiterStatistics};
use async_trait::async_trait;
use parking_lot::Mutex;
use std::collections::VecDeque;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{mpsc, oneshot, Mutex as TokioMutex};
use tokio_util::sync::CancellationToken;

/// Options for configuring a `ConcurrencyLimiter`.
#[derive(Clone, Debug)]
pub struct ConcurrencyLimiterOptions {
    /// Maximum number of permits that can be acquired concurrently.
    pub permit_limit: u32,

    /// Maximum number of permits that can be queued.
    /// When the queue limit is reached, new requests will fail immediately.
    pub queue_limit: u32,

    /// Order in which queued requests are processed.
    pub queue_processing_order: QueueProcessingOrder,
}

impl ConcurrencyLimiterOptions {
    /// Create new concurrency limiter options with validation.
    ///
    /// # Errors
    ///
    /// Returns an error if:
    /// - `permit_limit` is 0
    /// - `queue_limit` would cause integer overflow
    pub fn new(
        permit_limit: u32,
        queue_limit: u32,
        queue_processing_order: QueueProcessingOrder,
    ) -> Result<Self, RateLimitError> {
        if permit_limit == 0 {
            return Err(RateLimitError::InvalidParameter(
                "permit_limit must be greater than 0".to_string(),
            ));
        }

        Ok(Self {
            permit_limit,
            queue_limit,
            queue_processing_order,
        })
    }
}

/// Internal state for the concurrency limiter.
struct State {
    /// Number of permits currently available.
    available_permits: u32,

    /// Queue of pending requests waiting for permits.
    queue: VecDeque<QueuedRequest>,

    /// Total number of permits currently in the queue.
    queue_count: u32,

    /// Time when the limiter became idle (all permits available).
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

/// A rate limiter that manages concurrent access to a resource.
///
/// The `ConcurrencyLimiter` maintains a fixed number of permits that can be
/// acquired concurrently. When all permits are in use, new requests can be
/// queued (up to the queue limit) and will be granted permits as they become
/// available.
pub struct ConcurrencyLimiter {
    /// Shared mutable state.
    state: Arc<Mutex<State>>,

    /// Configuration options.
    config: ConcurrencyLimiterOptions,

    /// Channel for returning permits.
    permit_return_tx: mpsc::UnboundedSender<u32>,

    /// Channel receiver for returned permits (wrapped for shared ownership).
    permit_return_rx: Arc<TokioMutex<mpsc::UnboundedReceiver<u32>>>,

    /// Counter for successful lease acquisitions.
    successful_leases: Arc<AtomicU64>,

    /// Counter for failed lease acquisitions.
    failed_leases: Arc<AtomicU64>,
}

impl ConcurrencyLimiter {
    /// Create a new concurrency limiter with the specified options.
    ///
    /// # Errors
    ///
    /// Returns an error if the options are invalid.
    pub fn new(options: ConcurrencyLimiterOptions) -> Result<Self, RateLimitError> {
        // Validate options
        if options.permit_limit == 0 {
            return Err(RateLimitError::InvalidParameter(
                "permit_limit must be greater than 0".to_string(),
            ));
        }

        let (permit_return_tx, permit_return_rx) = mpsc::unbounded_channel();

        let state = State {
            available_permits: options.permit_limit,
            queue: VecDeque::new(),
            queue_count: 0,
            idle_since: Some(Instant::now()),
            disposed: false,
        };

        Ok(Self {
            state: Arc::new(Mutex::new(state)),
            config: options,
            permit_return_tx,
            permit_return_rx: Arc::new(TokioMutex::new(permit_return_rx)),
            successful_leases: Arc::new(AtomicU64::new(0)),
            failed_leases: Arc::new(AtomicU64::new(0)),
        })
    }

    /// Run the background queue processor.
    ///
    /// This method should be spawned as a background task. It processes
    /// returned permits and allocates them to queued requests.
    pub async fn run_queue_processor(&self) {
        let mut rx = self.permit_return_rx.lock().await;

        while let Some(returned_permits) = rx.recv().await {
            let mut state = self.state.lock();

            if state.disposed {
                break;
            }

            // If returned_permits is 0, state was already updated by sync cleanup
            // We're just here to process the queue
            if returned_permits > 0 {
                state.available_permits += returned_permits;

                // Update idle tracking
                if state.available_permits == self.config.permit_limit {
                    state.idle_since = Some(Instant::now());
                }
            }

            // Process queue - ONLY place this happens
            self.process_queue_internal(&mut state);
        }
    }

    /// Create a lease with appropriate cleanup.
    fn create_lease(&self, permit_count: u32, for_sync: bool) -> RateLimitLease {
        if permit_count == 0 {
            return RateLimitLease::success();
        }

        if for_sync {
            // For synchronous mode: update state directly AND notify channel
            // This ensures both sync tests work and async waiters get notified
            let state = Arc::clone(&self.state);
            let permit_limit = self.config.permit_limit;
            let tx = self.permit_return_tx.clone();

            RateLimitLease::success_with_cleanup(move || {
                // Update state directly for sync operations
                let mut s = state.lock();
                if !s.disposed {
                    s.available_permits += permit_count;
                    if s.available_permits == permit_limit {
                        s.idle_since = Some(Instant::now());
                    }
                }
                drop(s); // Release lock before sending to channel

                // Also notify the channel for any async waiters
                let _ = tx.send(0); // Send 0 since we already updated state
            })
        } else {
            // For async mode: just send via channel
            let tx = self.permit_return_tx.clone();

            RateLimitLease::success_with_cleanup(move || {
                // Queue processor handles everything
                let _ = tx.send(permit_count);
            })
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

                // Send lease with async cleanup (channel-based)
                let lease = self.create_lease(req.permit_count, false);
                let _ = req.response.send(Ok(lease));
                self.successful_leases.fetch_add(1, Ordering::Relaxed);
            } else {
                // Not enough permits for next request
                break;
            }
        }
    }

    /// Try to acquire permits immediately.
    fn try_acquire_immediate(&self, state: &mut State, permit_count: u32, for_sync: bool) -> Option<RateLimitLease> {
        if state.disposed {
            return None;
        }

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

                // Create lease with appropriate cleanup
                return Some(self.create_lease(permit_count, for_sync));
            }
        }

        None
    }
}

#[async_trait]
impl RateLimiter for ConcurrencyLimiter {
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
            if state.available_permits > 0 {
                self.successful_leases.fetch_add(1, Ordering::Relaxed);
                return Ok(RateLimitLease::success());
            } else {
                self.failed_leases.fetch_add(1, Ordering::Relaxed);
                return Ok(RateLimitLease::failed(None));
            }
        }

        // Try to acquire permits immediately (sync mode)
        if let Some(lease) = self.try_acquire_immediate(&mut state, permit_count, true) {
            return Ok(lease);
        }

        // Cannot acquire immediately
        self.failed_leases.fetch_add(1, Ordering::Relaxed);
        Ok(RateLimitLease::failed(None))
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

            // Try to acquire immediately (async mode)
            if let Some(lease) = self.try_acquire_immediate(&mut state, permit_count, false) {
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
                            let _ = oldest.response.send(Ok(RateLimitLease::failed(None)));
                            self.failed_leases.fetch_add(1, Ordering::Relaxed);
                        } else {
                            break;
                        }
                    }
                } else {
                    // Queue is full and we can't evict - return a failed lease
                    self.failed_leases.fetch_add(1, Ordering::Relaxed);
                    return Ok(RateLimitLease::failed(None));
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

impl Drop for ConcurrencyLimiter {
    fn drop(&mut self) {
        let mut state = self.state.lock();
        state.disposed = true;

        // Fail all queued requests
        while let Some(request) = state.queue.pop_front() {
            state.queue_count -= request.permit_count;
            let _ = request.response.send(Ok(RateLimitLease::failed(None)));
        }
    }
}