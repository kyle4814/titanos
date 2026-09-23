from __future__ import annotations

import unittest

from foundation.execution_adapter import AdapterResult, ExecutionAdapter
from foundation.execution_intent import ExecutionIntent


class FakeStripeAdapter:
    name = "stripe"

    def supports(self, intent: ExecutionIntent) -> bool:
        return intent.target.startswith("stripe:")

    def execute(self, intent: ExecutionIntent) -> AdapterResult:
        return AdapterResult(
            status="EXECUTED",
            effect=f"executed {intent.action}",
            executed=True,
            evidence=("stripe:receipt:123",),
        )


class TestExecutionAdapter(unittest.TestCase):
    def intent(self, target="stripe:customer_123"):
        return ExecutionIntent(
            intent_id="EI-ADAPTER-1",
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

    def test_adapter_contract_is_runtime_checkable(self):
        adapter = FakeStripeAdapter()
        self.assertIsInstance(adapter, ExecutionAdapter)

    def test_adapter_can_decline_unsupported_intent(self):
        adapter = FakeStripeAdapter()
        self.assertFalse(adapter.supports(self.intent("github:repo")))

    def test_adapter_result_is_machine_readable(self):
        result = FakeStripeAdapter().execute(self.intent())
        self.assertEqual(result.status, "EXECUTED")
        self.assertTrue(result.executed)
        self.assertEqual(result.evidence, ("stripe:receipt:123",))
        self.assertEqual(result.to_dict()["evidence"], ["stripe:receipt:123"])


if __name__ == "__main__":
    unittest.main()
