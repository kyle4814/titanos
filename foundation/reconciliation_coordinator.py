"""Closed-loop reconciliation coordinator.

Turns an uncertain execution receipt into durable reconciliation evidence and a
retry classification. Reconciliation is observational only; this module never
executes the original side effect.
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_retry import RetryDecision, classify_retry
from foundation.reconciliation_dispatcher import ReconciliationDispatcher
from foundation.reconciliation_receipt import (
    ReconciliationReceipt,
    reconciliation_receipt_from_result,
)
from foundation.reconciliation_receipt_store import ReconciliationReceiptStore

__all__ = ["ReconciliationCycle", "ReconciliationCoordinator"]


@dataclass(frozen=True)
class ReconciliationCycle:
    execution_receipt: ExecutionReceipt
    reconciliation_receipt: ReconciliationReceipt
    retry_decision: RetryDecision


class ReconciliationCoordinator:
    def __init__(
        self,
        dispatcher: ReconciliationDispatcher,
        receipt_store: ReconciliationReceiptStore,
    ) -> None:
        self.dispatcher = dispatcher
        self.receipt_store = receipt_store

    def run(
        self, intent: ExecutionIntent, execution_receipt: ExecutionReceipt
    ) -> ReconciliationCycle:
        result = self.dispatcher.reconcile(intent, execution_receipt)
        receipt = reconciliation_receipt_from_result(
            execution_receipt.receipt_id,
            execution_receipt.fingerprint,
            result,
        )
        self.receipt_store.record(receipt)

        if result.status.value == "RESOLVED_EXECUTED":
            decision = RetryDecision.TERMINAL
        elif result.status.value == "RESOLVED_NOT_EXECUTED":
            decision = RetryDecision.RECONCILE_REQUIRED
        else:
            decision = RetryDecision.RECONCILE_REQUIRED

        return ReconciliationCycle(
            execution_receipt=execution_receipt,
            reconciliation_receipt=receipt,
            retry_decision=decision,
        )
