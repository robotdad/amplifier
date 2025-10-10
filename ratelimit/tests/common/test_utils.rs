//! Test utility functions.
//!
//! Rust equivalent of Utils.cs from the C# test suite.

use std::time::Duration;

/// Helper to create test durations.
#[allow(dead_code)]
pub fn millis(ms: u64) -> Duration {
    Duration::from_millis(ms)
}

/// Helper to create test durations in seconds.
#[allow(dead_code)]
pub fn secs(s: u64) -> Duration {
    Duration::from_secs(s)
}

// Additional test utilities will be added as needed during test conversion
