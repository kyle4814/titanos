"""Closed-loop reconciliation workflow.

This module observes and records reconciliation and, when justified by
external evidence, prepares a new retry proposal. It never authorizes or
performs a follow-up external side effect.
"""

from __future__ import annotations

from dataclasses import dataclass

from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_retry import RetryDecision, classify_reconciled_retry
from foundation.reconciliation_dispatcher import ReconciliationDispatcher
from foundation.reconciliation_receipt import (
    ReconciliationReceipt,
    reconciliation_receipt_from_result,
)
from foundation.reconciliation_receipt_store import ReconciliationReceiptStore
from foundation.retry_proposal import RetryProposal, build_retry_proposal

__all__ = ["ReconciliationWorkflow", "ReconciliationWorkflowResult"]


@dataclass(frozen=True)
class ReconciliationWorkflowResult:
    reconciliation_receipt: ReconciliationReceipt
    retry_decision: RetryDecision
    persistence: str
    retry_proposal: RetryProposal | None = None


class ReconciliationWorkflow:
    def __init__(
        self,
        dispatcher: ReconciliationDispatcher,
        receipt_store: ReconciliationReceiptStore,
    ) -> None:
        self.dispatcher = dispatcher
        self.receipt_store = receipt_store

    def reconcile(
        self, intent: ExecutionIntent, execution_receipt: ExecutionReceipt
    ) -> ReconciliationWorkflowResult:
        result = self.dispatcher.reconcile(intent, execution_receipt)
        receipt = reconciliation_receipt_from_result(
            execution_receipt.receipt_id,
            execution_receipt.fingerprint,
            result,
        )
        persistence = self.receipt_store.record(receipt)
        decision = classify_reconciled_retry(result)
        proposal = (
            build_retry_proposal(intent, receipt)
            if decision is RetryDecision.RETRY_POLICY_REQUIRED
            else None
        )
        return ReconciliationWorkflowResult(
            reconciliation_receipt=receipt,
            retry_decision=decision,
            persistence=persistence,
            retry_proposal=proposal,
        )
