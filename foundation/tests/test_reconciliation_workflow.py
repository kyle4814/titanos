from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_reconciliation import (
    ReconciliationResult,
    ReconciliationStatus,
)
from foundation.reconciliation_dispatcher import ReconciliationDispatcher
from foundation.reconciliation_receipt_store import ReconciliationReceiptStore
from foundation.reconciliation_workflow import ReconciliationWorkflow
from foundation.execution_retry import RetryDecision


class Adapter:
    name = "provider"

    def supports(self, intent):
        return intent.target.startswith("provider:")

    def reconcile(self, intent, receipt):
        return ReconciliationResult(
            ReconciliationStatus.RESOLVED_NOT_EXECUTED,
            ("provider:absent",),
        )


class TestReconciliationWorkflow(unittest.TestCase):
    def setUp(self):
        self.intent = ExecutionIntent(
            intent_id="EI-WORKFLOW-1",
            target="provider:thing",
            action="CREATE_THING",
            parameters={"value": 1},
            evidence_refs=("OPP-1",),
            expected_effect="create one thing",
            authority_required="A3",
            reversible=True,
            expires_at="2099-01-01T00:00:00+00:00",
            policy_version="mothership-1",
        )
        self.execution_receipt = ExecutionReceipt(
            receipt_id=f"exec:{self.intent.fingerprint()}",
            intent_id=self.intent.intent_id,
            fingerprint=self.intent.fingerprint(),
            target=self.intent.target,
            action=self.intent.action,
            status="TIMEOUT",
            executed=False,
            recorded_at="2026-09-23T00:00:00+00:00",
            evidence="gateway timeout",
        )

    def test_reconcile_persists_and_classifies_without_retrying(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ReconciliationReceiptStore(Path(tmp) / "reconciliation.json")
            workflow = ReconciliationWorkflow(
                ReconciliationDispatcher.from_adapters([Adapter()]),
                store,
            )
            outcome = workflow.reconcile(self.intent, self.execution_receipt)

            self.assertEqual(outcome.persistence, "RECORDED")
            self.assertEqual(
                outcome.reconciliation_receipt.status,
                ReconciliationStatus.RESOLVED_NOT_EXECUTED,
            )
            self.assertEqual(
                outcome.retry_decision,
                RetryDecision.RETRY_POLICY_REQUIRED,
            )
            self.assertIsNotNone(store.get(outcome.reconciliation_receipt.receipt_id))

    def test_reconciliation_does_not_authorize_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            workflow = ReconciliationWorkflow(
                ReconciliationDispatcher.from_adapters([Adapter()]),
                ReconciliationReceiptStore(Path(tmp) / "reconciliation.json"),
            )
            outcome = workflow.reconcile(self.intent, self.execution_receipt)
            self.assertNotEqual(
                outcome.retry_decision,
                RetryDecision.TERMINAL,
            )


if __name__ == "__main__":
    unittest.main()
