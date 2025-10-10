//! Rate limit lease types.

use std::any::Any;
use std::collections::HashMap;
use std::time::Duration;

/// Represents the result of a rate limit acquisition attempt.
///
/// A lease indicates whether permits were successfully acquired and may
/// contain metadata such as retry-after hints for failed acquisitions.
pub struct RateLimitLease {
    is_acquired: bool,
    metadata: HashMap<String, Box<dyn Any + Send + Sync>>,
    on_drop: Option<Box<dyn FnOnce() + Send>>,
}

impl RateLimitLease {
    /// Create a successful lease.
    pub fn success() -> Self {
        Self {
            is_acquired: true,
            metadata: HashMap::new(),
            on_drop: None,
        }
    }

    /// Create a successful lease with a cleanup callback.
    ///
    /// The callback is invoked when the lease is dropped (for returning permits).
    pub fn success_with_cleanup<F>(cleanup: F) -> Self
    where
        F: FnOnce() + Send + 'static,
    {
        Self {
            is_acquired: true,
            metadata: HashMap::new(),
            on_drop: Some(Box::new(cleanup)),
        }
    }

    /// Create a failed lease with optional retry-after metadata.
    pub fn failed(retry_after: Option<Duration>) -> Self {
        let mut metadata = HashMap::new();
        if let Some(duration) = retry_after {
            metadata.insert(
                "RetryAfter".to_string(),
                Box::new(duration) as Box<dyn Any + Send + Sync>,
            );
        }

        Self {
            is_acquired: false,
            metadata,
            on_drop: None,
        }
    }

    /// Returns `true` if permits were successfully acquired.
    pub fn is_acquired(&self) -> bool {
        self.is_acquired
    }

    /// Attempt to get metadata by name.
    pub fn try_get_metadata<T: 'static>(&self, name: &str) -> Option<&T> {
        self.metadata
            .get(name)
            .and_then(|boxed| boxed.downcast_ref::<T>())
    }

    /// Get all metadata names available on this lease.
    pub fn metadata_names(&self) -> impl Iterator<Item = &String> {
        self.metadata.keys()
    }

    /// Add metadata to the lease.
    pub fn with_metadata<T: Any + Send + Sync + 'static>(
        mut self,
        name: impl Into<String>,
        value: T,
    ) -> Self {
        self.metadata.insert(name.into(), Box::new(value));
        self
    }
}

impl Drop for RateLimitLease {
    fn drop(&mut self) {
        if let Some(cleanup) = self.on_drop.take() {
            cleanup();
        }
    }
}

// Implement Debug manually to avoid "doesn't implement Debug" errors
impl std::fmt::Debug for RateLimitLease {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("RateLimitLease")
            .field("is_acquired", &self.is_acquired)
            .field("metadata_count", &self.metadata.len())
            .finish()
    }
}
