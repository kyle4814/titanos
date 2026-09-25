from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.adapter_execution_gateway import AdapterExecutionGateway
from foundation.execution_adapter import AdapterResult
from foundation.execution_dispatcher import AdapterDispatcher
from foundation.execution_intent import ExecutionIntent, ExecutionIntentError
from foundation.execution_receipt_store import ExecutionReceiptStore


class Adapter:
    name = "stripe"

    def supports(self, intent):
        return intent.target.startswith("stripe:")

    def execute(self, intent):
        return AdapterResult(
            status="EXECUTED",
            effect="payment link created",
            executed=True,
            evidence=("stripe:receipt:123",),
        )


class TestAdapterExecutionGateway(unittest.TestCase):
    def intent(self):
        return ExecutionIntent(
            intent_id="EI-GATEWAY-1",
            target="stripe:customer_123",
            action="CREATE_PAYMENT_LINK",
            parameters={"amount": 1000, "currency": "AUD"},
            evidence_refs=("OPP-1",),
            expected_effect="create one payment link",
            authority_required="A3",
            reversible=True,
            expires_at="2099-01-01T00:00:00+00:00",
            policy_version="mothership-1",
        )

    def gateway(self, tmp):
        return AdapterExecutionGateway(
            AdapterDispatcher.from_adapters([Adapter()]),
            ExecutionReceiptStore(Path(tmp) / "receipts.json"),
        )

    def test_approved_execution_produces_persisted_adapter_receipt(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            receipt = self.gateway(tmp).execute_approved(intent, intent.fingerprint())
            self.assertTrue(receipt.executed)
            self.assertEqual(receipt.status, "EXECUTED")
            self.assertEqual(receipt.evidence, "stripe:receipt:123")
            stored = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            self.assertEqual(stored.get(receipt.receipt_id), receipt)

    def test_wrong_approval_blocks_adapter_before_side_effect(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ExecutionIntentError, "does not match"):
                self.gateway(tmp).execute_approved(intent, "WRONG")
            self.assertFalse(Path(tmp, "receipts.json").exists())

    def test_duplicate_execution_is_receipt_idempotent(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp)
            first = gateway.execute_approved(intent, intent.fingerprint())
            second = gateway.execute_approved(intent, intent.fingerprint())
            self.assertEqual(first.receipt_id, second.receipt_id)
            self.assertEqual(len(gateway.receipt_store.load()), 1)

    def test_duplicate_execution_never_reruns_the_adapter(self):
        # The adapter is the side effect (e.g. a payment link). A replayed
        # approval must return the recorded receipt, not act a second time.
        calls = []

        class CountingAdapter(Adapter):
            def execute(self, intent):
                calls.append(intent.intent_id)
                return super().execute(intent)

        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([CountingAdapter()]),
                ExecutionReceiptStore(Path(tmp) / "receipts.json"),
            )
            first = gateway.execute_approved(intent, intent.fingerprint())
            second = gateway.execute_approved(intent, intent.fingerprint())
            self.assertEqual(first, second)
            self.assertEqual(calls, ["EI-GATEWAY-1"])

    def test_duplicate_still_requires_the_exact_approval(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp)
            gateway.execute_approved(intent, intent.fingerprint())
            with self.assertRaisesRegex(ExecutionIntentError, "does not match"):
                gateway.execute_approved(intent, "WRONG")


if __name__ == "__main__":
    unittest.main()
