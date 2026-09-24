"""Conservative retry policy for bounded TitanOS worker execution."""

from __future__ import annotations

from dataclasses import dataclass

_TRANSIENT_MARKERS = (
    "timeout",
    "timed out",
    "rate limit",
    "rate_limit",
    "temporarily unavailable",
    "connection reset",
    "connection refused",
    "service unavailable",
)

@dataclass(frozen=True)
class RetryDecision:
    retry: bool
    reason: str
    next_attempt: int

def classify_failure(error: str | None) -> str:
    if not error:
        return "UNKNOWN"
    message = error.strip().lower()
    return "TRANSIENT" if any(marker in message for marker in _TRANSIENT_MARKERS) else "PERMANENT"

def decide_retry(status: str, error: str | None, attempt: int, max_attempts: int) -> RetryDecision:
    if attempt < 1 or max_attempts < 1:
        raise ValueError("attempts must be positive")
    if attempt > max_attempts:
        raise ValueError("attempt cannot exceed max_attempts")

    if status != "FAILED":
        return RetryDecision(False, "non-failed result is not retryable", attempt)
    if attempt >= max_attempts:
        return RetryDecision(False, "retry budget exhausted", attempt)
    if classify_failure(error) != "TRANSIENT":
        return RetryDecision(False, "failure is not classified as transient", attempt)
    return RetryDecision(True, "transient failure within retry budget", attempt + 1)

__all__ = ["RetryDecision", "classify_failure", "decide_retry"]
