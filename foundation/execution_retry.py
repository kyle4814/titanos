"""Retry policy for externally meaningful execution.

The kernel never treats an uncertain external outcome as permission to retry.
A retry is only classified as safe when a future adapter-specific policy can
prove the original side effect is absent or the operation is idempotently
addressed. Until then, reconciliation is required.
"""

from __future__ import annotations

from enum import StrEnum

from foundation.execution_receipt import ExecutionReceipt

__all__ = ["RetryDecision", "classify_retry"]


class RetryDecision(StrEnum):
    TERMINAL = "TERMINAL"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"


def classify_retry(receipt: ExecutionReceipt) -> RetryDecision:
    """Classify a receipt without authorizing any retry."""
    if receipt.status == "EXECUTED" and receipt.executed:
        return RetryDecision.TERMINAL
    return RetryDecision.RECONCILE_REQUIRED
