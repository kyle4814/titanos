from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_retry import RetryDecision
from foundation.execution_reconciliation import ReconciliationResult, ReconciliationStatus
from foundation.reconciliation_coordinator import ReconciliationCoordinator
from foundation.reconciliation_dispatcher import ReconciliationDispatcher
from foundation.reconciliation_receipt_store import ReconciliationReceiptStore


class Adapter:
    name = "provider"

    def supports(self, intent):
        return True

    def reconcile(self, intent, receipt):
        return ReconciliationResult(
            ReconciliationStatus.RESOLVED_EXECUTED,
            ("provider:confirmed",),
            "external-123",
        )


class TestReconciliationCoordinator(unittest.TestCase):
    def test_reconciled_non_execution_requires_retry_policy(self):
        intent = ExecutionIntent(
            intent_id="EI-2",
            target="provider:item",
            action="CREATE",
            parameters={"x": 2},
            evidence_refs=("OPP-2",),
            expected_effect="create item",
            authority_required="A3",
            reversible=True,
            expires_at="2099-01-01T00:00:00+00:00",
            policy_version="test-1",
        )
        execution = ExecutionReceipt(
            receipt_id=f"exec:{intent.fingerprint()}",
            intent_id=intent.intent_id,
            fingerprint=intent.fingerprint(),
            target=intent.target,
            action=intent.action,
            status="UNKNOWN",
            executed=False,
            recorded_at="2026-09-23T00:00:00+00:00",
            evidence="timeout",
        )

        class AbsentAdapter(Adapter):
            def reconcile(self, intent, receipt):
                return ReconciliationResult(
                    ReconciliationStatus.RESOLVED_NOT_EXECUTED,
                    ("provider:absent",),
                )

        with tempfile.TemporaryDirectory() as tmp:
            store = ReconciliationReceiptStore(Path(tmp) / "reconciliation.json")
            cycle = ReconciliationCoordinator(
                ReconciliationDispatcher.from_adapters([AbsentAdapter()]), store
            ).run(intent, execution)
            self.assertEqual(
                cycle.retry_decision, RetryDecision.RETRY_POLICY_REQUIRED
            )

    def test_cycle_persists_evidence_and_stops_retry(self):
        intent = ExecutionIntent(
            intent_id="EI-1",
            target="provider:item",
            action="CREATE",
            parameters={"x": 1},
            evidence_refs=("OPP-1",),
            expected_effect="create item",
            authority_required="A3",
            reversible=True,
            expires_at="2099-01-01T00:00:00+00:00",
            policy_version="test-1",
        )
        execution = ExecutionReceipt(
            receipt_id=f"exec:{intent.fingerprint()}",
            intent_id=intent.intent_id,
            fingerprint=intent.fingerprint(),
            target=intent.target,
            action=intent.action,
            status="UNKNOWN",
            executed=False,
            recorded_at="2026-09-23T00:00:00+00:00",
            evidence="timeout",
        )

        with tempfile.TemporaryDirectory() as tmp:
            store = ReconciliationReceiptStore(Path(tmp) / "reconciliation.json")
            cycle = ReconciliationCoordinator(
                ReconciliationDispatcher.from_adapters([Adapter()]), store
            ).run(intent, execution)

            self.assertEqual(
                cycle.reconciliation_receipt.status,
                ReconciliationStatus.RESOLVED_EXECUTED,
            )
            self.assertEqual(cycle.retry_decision, RetryDecision.TERMINAL)
            self.assertIsNotNone(store.get(cycle.reconciliation_receipt.receipt_id))


if __name__ == "__main__":
    unittest.main()
