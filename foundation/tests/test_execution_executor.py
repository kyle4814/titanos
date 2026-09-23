from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from foundation.execution_executor import dry_run
from foundation.execution_intent import ExecutionIntent, ExecutionIntentError


class TestExecutionExecutor(unittest.TestCase):
    def intent(self, **overrides):
        values = {
            "intent_id": "EI-DRY-1",
            "target": "stripe:customer_123",
            "action": "CREATE_PAYMENT_LINK",
            "parameters": {"amount": 1000, "currency": "AUD"},
            "evidence_refs": ("OPP-42",),
            "expected_effect": "create one payment link",
            "authority_required": "A3",
            "reversible": True,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "policy_version": "mothership-1",
        }
        values.update(overrides)
        return ExecutionIntent(**values)

    def test_dry_run_never_executes(self):
        result = dry_run(self.intent())
        self.assertEqual(result.status, "DRY_RUN")
        self.assertFalse(result.executed)

    def test_result_binds_exact_intent(self):
        intent = self.intent()
        result = dry_run(intent)
        self.assertEqual(result.fingerprint, intent.fingerprint())
        self.assertEqual(result.intent_id, intent.intent_id)
        self.assertEqual(result.target, intent.target)
        self.assertEqual(result.action, intent.action)

    def test_expired_intent_is_rejected(self):
        intent = self.intent(
            expires_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        )
        with self.assertRaisesRegex(ExecutionIntentError, "expired"):
            dry_run(intent)


if __name__ == "__main__":
    unittest.main()
