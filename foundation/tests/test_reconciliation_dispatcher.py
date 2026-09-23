from __future__ import annotations

import unittest

from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_reconciliation import (
    ReconciliationResult,
    ReconciliationStatus,
)
from foundation.execution_intent import ExecutionIntent
from foundation.reconciliation_dispatcher import (
    ReconciliationDispatchError,
    ReconciliationDispatcher,
)


class Adapter:
    def __init__(self, name="stripe"):
        self.name = name

    def supports(self, intent):
        return intent.target.startswith("stripe:")

    def reconcile(self, intent, receipt):
        return ReconciliationResult(
            ReconciliationStatus.RESOLVED_EXECUTED,
            ("provider:confirmed",),
            "payment_123",
        )


class TestReconciliationDispatcher(unittest.TestCase):
    def intent(self, target="stripe:customer_123"):
        return ExecutionIntent(
            intent_id="EI-RECON-1",
            target=target,
            action="CREATE_PAYMENT_LINK",
            parameters={"amount": 1000, "currency": "AUD"},
            evidence_refs=("OPP-1",),
            expected_effect="create one payment link",
            authority_required="A3",
            reversible=True,
            expires_at="2099-01-01T00:00:00+00:00",
            policy_version="mothership-1",
        )

    def receipt(self, intent, status="UNKNOWN", executed=False):
        return ExecutionReceipt(
            receipt_id=f"exec:{intent.fingerprint()}",
            intent_id=intent.intent_id,
            fingerprint=intent.fingerprint(),
            target=intent.target,
            action=intent.action,
            status=status,
            executed=executed,
            recorded_at="2026-09-23T00:00:00+00:00",
            evidence="gateway timeout",
        )

    def test_reconciles_one_matching_adapter(self):
        intent = self.intent()
        result = ReconciliationDispatcher.from_adapters([Adapter()]).reconcile(
            intent, self.receipt(intent)
        )
        self.assertEqual(result.status, ReconciliationStatus.RESOLVED_EXECUTED)
        self.assertEqual(result.external_reference, "payment_123")

    def test_rejects_ambiguous_reconciliation(self):
        intent = self.intent()
        dispatcher = ReconciliationDispatcher.from_adapters(
            [Adapter("a"), Adapter("b")]
        )
        with self.assertRaisesRegex(ReconciliationDispatchError, "ambiguous"):
            dispatcher.reconcile(intent, self.receipt(intent))

    def test_rejects_fingerprint_mismatch(self):
        intent = self.intent()
        other = self.intent("stripe:other")
        with self.assertRaisesRegex(ReconciliationDispatchError, "fingerprint"):
            ReconciliationDispatcher.from_adapters([Adapter()]).reconcile(
                intent, self.receipt(other)
            )

    def test_refuses_reconciliation_of_confirmed_execution(self):
        intent = self.intent()
        with self.assertRaisesRegex(ReconciliationDispatchError, "does not require"):
            ReconciliationDispatcher.from_adapters([Adapter()]).reconcile(
                intent, self.receipt(intent, "EXECUTED", True)
            )


if __name__ == "__main__":
    unittest.main()
