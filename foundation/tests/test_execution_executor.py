from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from foundation.execution_executor import (
    approved_dry_run,
    approved_dry_run_with_receipt,
    dry_run,
)
from foundation.execution_intent import ExecutionIntent, ExecutionIntentError
from foundation.execution_receipt_store import ExecutionReceiptStore


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

    def test_approved_dry_run_requires_exact_fingerprint(self):
        intent = self.intent()
        result = approved_dry_run(intent, intent.fingerprint())
        self.assertEqual(result.status, "APPROVED_DRY_RUN")
        self.assertEqual(result.fingerprint, intent.fingerprint())
        self.assertFalse(result.executed)

    def test_approved_dry_run_rejects_different_intent(self):
        intent = self.intent()
        with self.assertRaisesRegex(ExecutionIntentError, "does not match"):
            approved_dry_run(intent, "EI-not-the-approved-intent")

    def test_approved_dry_run_with_receipt_persists_receipt(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            receipt = approved_dry_run_with_receipt(
                intent, intent.fingerprint(), store
            )
            self.assertEqual(receipt.status, "APPROVED_DRY_RUN")
            self.assertFalse(receipt.executed)
            self.assertEqual(store.get(receipt.receipt_id), receipt)

    def test_approved_dry_run_with_receipt_rejects_before_persistence(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            with self.assertRaisesRegex(ExecutionIntentError, "does not match"):
                approved_dry_run_with_receipt(intent, "WRONG", store)
            self.assertFalse(Path(tmp, "receipts.json").exists())

    def test_approval_cannot_replay_against_changed_target(self):
        original = self.intent()
        changed = self.intent(target="stripe:customer_999")
        with self.assertRaisesRegex(ExecutionIntentError, "does not match"):
            approved_dry_run(changed, original.fingerprint())

    def test_approval_cannot_replay_against_changed_parameters(self):
        original = self.intent()
        changed = self.intent(parameters={"amount": 2000, "currency": "AUD"})
        with self.assertRaisesRegex(ExecutionIntentError, "does not match"):
            approved_dry_run(changed, original.fingerprint())

    def test_approval_cannot_replay_against_changed_policy(self):
        original = self.intent()
        changed = self.intent(policy_version="mothership-2")
        with self.assertRaisesRegex(ExecutionIntentError, "does not match"):
            approved_dry_run(changed, original.fingerprint())

    def test_duplicate_receipt_is_idempotent(self):
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            first = approved_dry_run_with_receipt(intent, intent.fingerprint(), store)
            second = approved_dry_run_with_receipt(intent, intent.fingerprint(), store)
            self.assertEqual(first, second)
            self.assertEqual(len(store.load()), 1)

    def test_expired_intent_is_rejected(self):
        intent = self.intent(
            expires_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        )
        with self.assertRaisesRegex(ExecutionIntentError, "expired"):
            dry_run(intent)


if __name__ == "__main__":
    unittest.main()
