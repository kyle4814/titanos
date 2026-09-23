"""Retry classification for externally meaningful execution.

A reconciliation result can establish that the original side effect did not
occur, but that fact alone does not authorize a retry. Authorization remains
an adapter/policy/authority concern.
"""

from __future__ import annotations

from enum import StrEnum

from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_reconciliation import ReconciliationResult, ReconciliationStatus

__all__ = ["RetryDecision", "classify_retry", "classify_reconciled_retry"]


class RetryDecision(StrEnum):
    TERMINAL = "TERMINAL"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    RETRY_POLICY_REQUIRED = "RETRY_POLICY_REQUIRED"


def classify_retry(receipt: ExecutionReceipt) -> RetryDecision:
    """Classify an execution receipt without authorizing any retry."""
    if receipt.status == "EXECUTED" and receipt.executed:
        return RetryDecision.TERMINAL
    return RetryDecision.RECONCILE_REQUIRED


def classify_reconciled_retry(result: ReconciliationResult) -> RetryDecision:
    """Classify a reconciled outcome without authorizing a new side effect."""
    if result.status is ReconciliationStatus.RESOLVED_EXECUTED:
        return RetryDecision.TERMINAL
    if result.status is ReconciliationStatus.RESOLVED_NOT_EXECUTED:
        return RetryDecision.RETRY_POLICY_REQUIRED
    return RetryDecision.RECONCILE_REQUIRED
