from __future__ import annotations

import unittest

from unittest.mock import patch

from foundation.execution_approval import approval_request_for_intent, request_intent_approval
from foundation.execution_intent import ExecutionIntent


class TestExecutionApproval(unittest.TestCase):
    def intent(self, **overrides):
        values = {
            "intent_id": "EI-42",
            "target": "stripe:customer_123",
            "action": "CREATE_PAYMENT_LINK",
            "parameters": {"amount": 1000, "currency": "AUD"},
            "evidence_refs": ("OPP-42",),
            "expected_effect": "create one payment link",
            "authority_required": "A3",
            "reversible": True,
            "expires_at": "2026-10-01T00:00:00+00:00",
            "policy_version": "mothership-1",
        }
        values.update(overrides)
        return ExecutionIntent(**values)

    def test_card_contains_exact_fingerprint_and_target(self):
        intent = self.intent()
        req = approval_request_for_intent(intent)
        self.assertIn(intent.fingerprint(), req.action)
        self.assertIn(intent.target, req.action)
        self.assertIn(intent.expected_effect, req.why)

    def test_request_id_defaults_to_exact_intent_fingerprint(self):
        intent = self.intent()
        with patch("foundation.execution_approval.request_approval", return_value="APPROVED") as mocked:
            result = request_intent_approval(intent)
        self.assertEqual(result, "APPROVED")
        request = mocked.call_args.kwargs["request_id"]
        self.assertEqual(request, f"intent:{intent.fingerprint()}")

    def test_changed_parameters_change_approval_binding(self):
        first = approval_request_for_intent(self.intent())
        second = approval_request_for_intent(self.intent(parameters={"amount": 2000, "currency": "AUD"}))
        self.assertNotEqual(first.action, second.action)


if __name__ == "__main__":
    unittest.main()
