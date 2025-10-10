use crate::core::{
    QueueProcessingOrder, RateLimitError, RateLimitLease, RateLimiter, RateLimiterStatistics,
    ReplenishingRateLimiter,
};
use async_trait::async_trait;
use std::{
    collections::VecDeque,
    sync::{
        atomic::{AtomicBool, AtomicU32, Ordering},
        Arc, Mutex,
    },
    time::{Duration, Instant},
};
use tokio::sync::{mpsc, oneshot};
use tokio_util::sync::CancellationToken;

/// Rate limiter using a sliding time window divided into segments
pub struct SlidingWindowRateLimiter {
    config: SlidingWindowRateLimiterOptions,
    state: Arc<Mutex<State>>,
    requests_tx: mpsc::UnboundedSender<Request>,
    total_successful_leases: Arc<AtomicU32>,
    total_failed_leases: Arc<AtomicU32>,
    processing_scheduled: Arc<AtomicBool>,
}

impl SlidingWindowRateLimiter {
    /// Creates a new sliding window rate limiter
    pub fn new(options: SlidingWindowRateLimiterOptions) -> Self {
        let (tx, mut rx) = mpsc::unbounded_channel::<Request>();

        let state = Arc::new(Mutex::new(State {
            segments: VecDeque::new(),
            queue: VecDeque::new(),
            queue_count: 0,
            idle_since: Some(Instant::now()),
            auto_replenish_timer: None,
            disposed: false,
        }));

        let total_successful_leases = Arc::new(AtomicU32::new(0));
        let total_failed_leases = Arc::new(AtomicU32::new(0));
        let processing_scheduled = Arc::new(AtomicBool::new(false));

        let limiter = Self {
            config: options.clone(),
            state: state.clone(),
            requests_tx: tx,
            total_successful_leases: total_successful_leases.clone(),
            total_failed_leases: total_failed_leases.clone(),
            processing_scheduled: processing_scheduled.clone(),
        };

        // Start background request processor
        {
            let state = state.clone();
            let config = options.clone();
            let total_successful_leases = total_successful_leases.clone();
            let total_failed_leases = total_failed_leases.clone();
            let processing_scheduled = processing_scheduled.clone();

            tokio::spawn(async move {
                while let Some(request) = rx.recv().await {
                    Self::process_request(
                        request,
                        &state,
                        &config,
                        &total_successful_leases,
                        &total_failed_leases,
                        &processing_scheduled,
                    );
                }
            });
        }

        // Start auto-replenishment timer if enabled
        if options.auto_replenishment {
            let replenish_limiter = limiter.clone();
            let handle = tokio::spawn(async move {
                replenish_limiter.run_replenishment_timer().await;
            });

            {
                let mut s = state.lock().unwrap();
                s.auto_replenish_timer = Some(handle);
            }
        }

        limiter
    }

    fn process_request(
        request: Request,
        state: &Arc<Mutex<State>>,
        config: &SlidingWindowRateLimiterOptions,
        successful_leases: &Arc<AtomicU32>,
        failed_leases: &Arc<AtomicU32>,
        processing_scheduled: &Arc<AtomicBool>,
    ) {
        match request {
            Request::AcquireAsync {
                permit_count,
                response,
                _cancel_token,
            } => {
                // Try immediate acquisition
                let result = Self::try_acquire_or_queue(permit_count, state, config);
                match result {
                    AcquireResult::Immediate(lease) => {
                        if lease.is_acquired() {
                            successful_leases.fetch_add(permit_count, Ordering::Relaxed);
                        } else {
                            failed_leases.fetch_add(permit_count, Ordering::Relaxed);
                        }
                        let _ = response.send(Ok(lease));
                    }
                    AcquireResult::Queued(rx) => {
                        // Spawn task to wait for result
                        let successful_leases = successful_leases.clone();
                        let failed_leases = failed_leases.clone();
                        tokio::spawn(async move {
                            match rx.await {
                                Ok(Ok(lease)) => {
                                    if lease.is_acquired() {
                                        successful_leases.fetch_add(permit_count, Ordering::Relaxed);
                                    } else {
                                        failed_leases.fetch_add(permit_count, Ordering::Relaxed);
                                    }
                                    let _ = response.send(Ok(lease));
                                }
                                Ok(Err(e)) => {
                                    failed_leases.fetch_add(permit_count, Ordering::Relaxed);
                                    let _ = response.send(Err(e));
                                }
                                Err(_) => {
                                    failed_leases.fetch_add(permit_count, Ordering::Relaxed);
                                    let _ = response.send(Err(RateLimitError::Disposed));
                                }
                            }
                        });
                    }
                }
            }
            Request::TryReplenish { response } => {
                let result = Self::replenish_core(state, config, processing_scheduled);
                let _ = response.send(result);
            }
        }
    }

    fn try_acquire_or_queue(
        permit_count: u32,
        state: &Arc<Mutex<State>>,
        config: &SlidingWindowRateLimiterOptions,
    ) -> AcquireResult {
        if permit_count > config.permit_limit {
            return AcquireResult::Immediate(RateLimitLease::failed(None));
        }

        let mut s = state.lock().unwrap();
        if s.disposed {
            return AcquireResult::Immediate(RateLimitLease::failed(None));
        }

        // Remove expired segments
        Self::remove_expired_segments(&mut s, config);

        // Calculate available permits
        let available = Self::available_permits(&s, config);

        if available >= permit_count {
            // Acquire permits immediately
            Self::record_acquisition(&mut s, permit_count, config);
            s.idle_since = None;
            return AcquireResult::Immediate(RateLimitLease::success());
        }

        // Try to queue if space available
        if s.queue_count + permit_count <= config.queue_limit {
            let (tx, rx) = oneshot::channel();
            s.queue.push_back(QueuedRequest {
                permits_requested: permit_count,
                response: tx,
                queued_at: Instant::now(),
            });
            s.queue_count += permit_count;
            s.idle_since = None;
            AcquireResult::Queued(rx)
        } else {
            let retry_after = Self::calculate_retry_after(&s);
            AcquireResult::Immediate(RateLimitLease::failed(Some(retry_after)))
        }
    }

    fn remove_expired_segments(state: &mut State, _config: &SlidingWindowRateLimiterOptions) {
        let now = Instant::now();
        while let Some(segment) = state.segments.front() {
            if segment.expires_at <= now {
                state.segments.pop_front();
            } else {
                break;
            }
        }
    }

    fn available_permits(state: &State, config: &SlidingWindowRateLimiterOptions) -> u32 {
        let used_in_window: u32 = state.segments.iter().map(|s| s.count).sum();
        config.permit_limit.saturating_sub(used_in_window)
    }

    fn record_acquisition(
        state: &mut State,
        count: u32,
        config: &SlidingWindowRateLimiterOptions,
    ) {
        let now = Instant::now();

        // Add to most recent segment if it exists and was created recently
        if let Some(last) = state.segments.back_mut() {
            // Check if the last segment was created within the current segment duration
            let segment_age = now.duration_since(last.expires_at - config.window);
            let segment_duration = config.window / config.segments_per_window;

            if segment_age < segment_duration {
                last.count += count;
                return;
            }
        }

        // Create new segment
        state.segments.push_back(Segment {
            expires_at: now + config.window,
            count,
        });
    }

    fn replenish_core(
        state: &Arc<Mutex<State>>,
        config: &SlidingWindowRateLimiterOptions,
        processing_scheduled: &Arc<AtomicBool>,
    ) -> bool {
        let mut s = state.lock().unwrap();
        if s.disposed {
            processing_scheduled.store(false, Ordering::Relaxed);
            return false;
        }

        // Remove expired segments
        Self::remove_expired_segments(&mut s, config);

        // Process queued requests
        let processed = Self::process_queue(&mut s, config);

        // Update idle time if queue is empty
        if s.queue.is_empty() && s.idle_since.is_none() {
            s.idle_since = Some(Instant::now());
        }

        processing_scheduled.store(false, Ordering::Relaxed);
        processed > 0
    }

    fn process_queue(state: &mut State, config: &SlidingWindowRateLimiterOptions) -> u32 {
        let mut permits_granted = 0;
        let mut granted_requests = Vec::new();

        // Process queue based on configured order
        let indices: Vec<usize> = match config.queue_processing_order {
            QueueProcessingOrder::OldestFirst => (0..state.queue.len()).collect(),
            QueueProcessingOrder::NewestFirst => (0..state.queue.len()).rev().collect(),
        };

        // First pass: determine which requests can be granted
        for idx in indices {
            let permits_requested = if let Some(request) = state.queue.get(idx) {
                let available = Self::available_permits(state, config);
                if available >= request.permits_requested {
                    request.permits_requested
                } else {
                    continue;
                }
            } else {
                continue;
            };

            // Now we can mutate state
            granted_requests.push((idx, permits_requested));
            Self::record_acquisition(state, permits_requested, config);
            permits_granted += permits_requested;

            // Can't continue granting if we've exhausted permits
            if Self::available_permits(state, config) == 0 {
                break;
            }
        }

        // Second pass: remove granted requests and send permits
        granted_requests.sort_unstable_by(|a, b| b.0.cmp(&a.0)); // Sort descending for removal
        for (idx, _) in granted_requests {
            if let Some(request) = state.queue.remove(idx) {
                state.queue_count = state.queue_count.saturating_sub(request.permits_requested);
                let _ = request.response.send(Ok(RateLimitLease::success()));
            }
        }

        permits_granted
    }

    async fn run_replenishment_timer(&self) {
        let segment_duration = self.config.window / self.config.segments_per_window;
        let mut interval = tokio::time::interval(segment_duration);
        interval.set_missed_tick_behavior(tokio::time::MissedTickBehavior::Skip);

        loop {
            interval.tick().await;

            // Check if already processing or disposed
            if self.processing_scheduled.load(Ordering::Relaxed) {
                continue;
            }

            {
                let s = self.state.lock().unwrap();
                if s.disposed {
                    break;
                }
                // Skip if no queue to process
                if s.queue.is_empty() {
                    continue;
                }
            }

            // Schedule processing
            if self
                .processing_scheduled
                .compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed)
                .is_err()
            {
                continue;
            }

            // Send replenish request
            let (tx, rx) = oneshot::channel();
            if self
                .requests_tx
                .send(Request::TryReplenish { response: tx })
                .is_err()
            {
                break;
            }

            // Wait for completion (non-blocking)
            tokio::spawn(async move {
                let _ = rx.await;
            });
        }
    }

    fn calculate_retry_after(state: &State) -> Duration {
        // Time until the oldest segment expires
        if let Some(oldest) = state.segments.front() {
            let now = Instant::now();
            if oldest.expires_at > now {
                oldest.expires_at - now
            } else {
                Duration::ZERO
            }
        } else {
            // No segments, permits available immediately
            Duration::ZERO
        }
    }
}

impl Clone for SlidingWindowRateLimiter {
    fn clone(&self) -> Self {
        Self {
            config: self.config.clone(),
            state: self.state.clone(),
            requests_tx: self.requests_tx.clone(),
            total_successful_leases: self.total_successful_leases.clone(),
            total_failed_leases: self.total_failed_leases.clone(),
            processing_scheduled: self.processing_scheduled.clone(),
        }
    }
}

#[async_trait]
impl RateLimiter for SlidingWindowRateLimiter {
    fn attempt_acquire(&self, permit_count: u32) -> Result<RateLimitLease, RateLimitError> {
        // For synchronous attempt, check directly without channel
        if permit_count > self.config.permit_limit {
            return Ok(RateLimitLease::failed(None));
        }

        let mut s = self.state.lock().unwrap();
        if s.disposed {
            return Err(RateLimitError::Disposed);
        }

        // Remove expired segments
        Self::remove_expired_segments(&mut s, &self.config);

        // Calculate available permits
        let available = Self::available_permits(&s, &self.config);

        if available >= permit_count {
            // Acquire permits
            Self::record_acquisition(&mut s, permit_count, &self.config);
            s.idle_since = None;
            self.total_successful_leases
                .fetch_add(permit_count, Ordering::Relaxed);
            Ok(RateLimitLease::success())
        } else {
            // Calculate retry-after duration
            let retry_after = Self::calculate_retry_after(&s);
            self.total_failed_leases
                .fetch_add(permit_count, Ordering::Relaxed);
            Ok(RateLimitLease::failed(Some(retry_after)))
        }
    }

    async fn acquire_async(
        &self,
        permit_count: u32,
        cancel_token: Option<CancellationToken>,
    ) -> Result<RateLimitLease, RateLimitError> {
        let (tx, rx) = oneshot::channel();
        self.requests_tx
            .send(Request::AcquireAsync {
                permit_count,
                response: tx,
                _cancel_token: cancel_token.clone(),
            })
            .map_err(|_| RateLimitError::Disposed)?;

        // Handle cancellation
        if let Some(token) = cancel_token {
            tokio::select! {
                result = rx => {
                    result.map_err(|_| RateLimitError::Disposed)?
                }
                _ = token.cancelled() => {
                    Err(RateLimitError::Cancelled)
                }
            }
        } else {
            rx.await.map_err(|_| RateLimitError::Disposed)?
        }
    }

    fn get_statistics(&self) -> RateLimiterStatistics {
        let mut s = self.state.lock().unwrap();
        Self::remove_expired_segments(&mut s, &self.config);

        RateLimiterStatistics {
            current_available_permits: Self::available_permits(&s, &self.config) as i64,
            current_queued_count: s.queue_count,
            total_successful_leases: self.total_successful_leases.load(Ordering::Relaxed) as u64,
            total_failed_leases: self.total_failed_leases.load(Ordering::Relaxed) as u64,
        }
    }

    fn idle_duration(&self) -> Option<Duration> {
        let s = self.state.lock().unwrap();
        s.idle_since.map(|since| since.elapsed())
    }
}

#[async_trait]
impl ReplenishingRateLimiter for SlidingWindowRateLimiter {
    fn is_auto_replenishing(&self) -> bool {
        self.config.auto_replenishment
    }

    fn replenishment_period(&self) -> Duration {
        self.config.window / self.config.segments_per_window
    }

    fn try_replenish(&self) -> bool {
        // Don't replenish if auto-replenishment is enabled
        if self.config.auto_replenishment {
            return false;
        }

        // Check if already processing
        if self.processing_scheduled.load(Ordering::Relaxed) {
            return false;
        }

        // Set processing flag
        if self
            .processing_scheduled
            .compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_err()
        {
            return false;
        }

        // Do replenishment directly without channel
        Self::replenish_core(&self.state, &self.config, &self.processing_scheduled)
    }
}

/// Configuration options for the sliding window rate limiter
#[derive(Debug, Clone)]
pub struct SlidingWindowRateLimiterOptions {
    /// Maximum number of permits that can be leased in a window
    pub permit_limit: u32,

    /// Duration of the sliding window
    pub window: Duration,

    /// Number of segments to divide the window into
    pub segments_per_window: u32,

    /// Maximum number of permits that can be queued
    pub queue_limit: u32,

    /// Order in which queued requests are processed
    pub queue_processing_order: QueueProcessingOrder,

    /// Whether to automatically replenish permits
    pub auto_replenishment: bool,
}

impl Default for SlidingWindowRateLimiterOptions {
    fn default() -> Self {
        Self {
            permit_limit: 100,
            window: Duration::from_secs(60),
            segments_per_window: 10,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
            auto_replenishment: true,
        }
    }
}

struct State {
    segments: VecDeque<Segment>,
    queue: VecDeque<QueuedRequest>,
    queue_count: u32,
    idle_since: Option<Instant>,
    auto_replenish_timer: Option<tokio::task::JoinHandle<()>>,
    disposed: bool,
}

struct Segment {
    expires_at: Instant,
    count: u32,
}

struct QueuedRequest {
    permits_requested: u32,
    response: oneshot::Sender<Result<RateLimitLease, RateLimitError>>,
    #[allow(dead_code)]
    queued_at: Instant,
}

enum Request {
    AcquireAsync {
        permit_count: u32,
        response: oneshot::Sender<Result<RateLimitLease, RateLimitError>>,
        _cancel_token: Option<CancellationToken>,
    },
    TryReplenish {
        response: oneshot::Sender<bool>,
    },
}

enum AcquireResult {
    Immediate(RateLimitLease),
    Queued(oneshot::Receiver<Result<RateLimitLease, RateLimitError>>),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_basic_sliding_window() {
        let options = SlidingWindowRateLimiterOptions {
            permit_limit: 10,
            window: Duration::from_millis(100),
            segments_per_window: 5,
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
            auto_replenishment: false,
        };

        let limiter = SlidingWindowRateLimiter::new(options);

        // Should allow initial permits
        let lease1 = limiter.attempt_acquire(5).unwrap();
        assert!(lease1.is_acquired());

        // Should allow more up to limit
        let lease2 = limiter.attempt_acquire(5).unwrap();
        assert!(lease2.is_acquired());

        // Should reject over limit
        let lease3 = limiter.attempt_acquire(1).unwrap();
        assert!(!lease3.is_acquired());

        // Wait for first segment to expire (segments expire after window duration)
        tokio::time::sleep(Duration::from_millis(105)).await;

        // Some permits should be available as segments expire
        let stats = limiter.get_statistics();
        assert!(
            stats.current_available_permits > 0,
            "Should have some permits after segment expiry"
        );
    }

    #[tokio::test]
    async fn test_segments_expire_individually() {
        let options = SlidingWindowRateLimiterOptions {
            permit_limit: 10,
            window: Duration::from_millis(100),
            segments_per_window: 4, // 25ms per segment
            queue_limit: 0,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
            auto_replenishment: false,
        };

        let limiter = SlidingWindowRateLimiter::new(options);

        // Acquire permits at different times
        assert!(limiter.attempt_acquire(3).unwrap().is_acquired());
        tokio::time::sleep(Duration::from_millis(30)).await; // Into second segment
        assert!(limiter.attempt_acquire(3).unwrap().is_acquired());
        tokio::time::sleep(Duration::from_millis(30)).await; // Into third segment
        assert!(limiter.attempt_acquire(4).unwrap().is_acquired());

        let stats = limiter.get_statistics();
        assert_eq!(stats.current_available_permits, 0);

        // Wait for first acquisition to expire
        tokio::time::sleep(Duration::from_millis(45)).await;
        limiter.try_replenish();

        // First 3 permits should be available
        let stats = limiter.get_statistics();
        assert!(stats.current_available_permits >= 3);
    }

    #[tokio::test]
    async fn test_auto_replenishment() {
        let options = SlidingWindowRateLimiterOptions {
            permit_limit: 5,
            window: Duration::from_millis(100),
            segments_per_window: 2,
            queue_limit: 10,
            queue_processing_order: QueueProcessingOrder::OldestFirst,
            auto_replenishment: true,
        };

        let limiter = SlidingWindowRateLimiter::new(options);

        // Use all permits
        assert!(limiter.attempt_acquire(5).unwrap().is_acquired());

        // Queue a request
        let acquire_task = tokio::spawn({
            let limiter = limiter.clone();
            async move { limiter.acquire_async(2, None).await }
        });

        // Give the request time to be queued
        tokio::time::sleep(Duration::from_millis(10)).await;

        // Should be queued
        let stats = limiter.get_statistics();
        assert_eq!(stats.current_queued_count, 2);

        // Wait for auto-replenishment to process queue
        tokio::time::sleep(Duration::from_millis(150)).await;

        // Request should complete
        let result = acquire_task.await.unwrap();
        assert!(result.is_ok());
        assert!(result.unwrap().is_acquired());

        let stats = limiter.get_statistics();
        assert_eq!(stats.current_queued_count, 0);
    }
}