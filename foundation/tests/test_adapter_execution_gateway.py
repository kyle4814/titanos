from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.adapter_execution_gateway import AdapterExecutionGateway
from foundation.approval_envelope import ApprovalEnvelope, ConsumedIds
from foundation.authorization_gate import AuthorizationGate
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


KEY = b"k" * 32  # test-only approval key

def _ledger():
    """A fresh on-disk replay ledger (ConsumedIds refuses process-local state)."""
    import tempfile as _t
    from pathlib import Path as _P
    return ConsumedIds(_P(_t.mkdtemp()) / "consumed.db")



class TestAdapterExecutionGateway(unittest.TestCase):
    def setUp(self):
        self.consumed = _ledger()
        self._n = 0

    def run_(self, gateway, intent, permit=None):
        if permit is None:
            self._n += 1
            env = ApprovalEnvelope.decide(proposal_id="p", intent=intent, decision="APPROVE",
                                          authority="A3", reviewer="kyle", nonce=f"n{self._n}").signed(KEY)
            permit = AuthorizationGate.issue(intent, env, key=KEY, consumed=self.consumed)
        return gateway.execute_permitted(intent, permit)

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
            KEY,
            self.consumed,
        )

    def test_approved_execution_produces_persisted_adapter_receipt(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            receipt = self.run_(self.gateway(tmp), intent)
            self.assertTrue(receipt.executed)
            self.assertEqual(receipt.status, "EXECUTED")
            self.assertEqual(receipt.evidence, "stripe:receipt:123")
            stored = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            self.assertEqual(stored.get(receipt.receipt_id), receipt)

    def test_wrong_approval_blocks_adapter_before_side_effect(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ExecutionIntentError, "ExecutionPermit is required"):
                self.run_(self.gateway(tmp), intent, "WRONG")
            self.assertFalse(Path(tmp, "receipts.json").exists())

    def test_duplicate_execution_is_receipt_idempotent(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp)
            first = self.run_(gateway, intent)
            second = self.run_(gateway, intent)
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
                KEY,
                self.consumed,
            )
            first = self.run_(gateway, intent)
            second = self.run_(gateway, intent)
            self.assertEqual(first, second)
            self.assertEqual(calls, ["EI-GATEWAY-1"])

    def test_duplicate_still_requires_the_exact_approval(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            gateway = self.gateway(tmp)
            self.run_(gateway, intent)
            with self.assertRaisesRegex(ExecutionIntentError, "ExecutionPermit is required"):
                self.run_(gateway, intent, "WRONG")


if __name__ == "__main__":
    unittest.main()
