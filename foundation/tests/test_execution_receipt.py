from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from foundation.execution_executor import approved_dry_run
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import receipt_from_result


class TestExecutionReceipt(unittest.TestCase):
    def intent(self):
        return ExecutionIntent(
            intent_id="EI-RECEIPT-1",
            target="stripe:customer_123",
            action="CREATE_PAYMENT_LINK",
            parameters={"amount": 1000, "currency": "AUD"},
            evidence_refs=("OPP-42",),
            expected_effect="create one payment link",
            authority_required="A3",
            reversible=True,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            policy_version="mothership-1",
        )

    def test_receipt_binds_result_to_exact_intent(self):
        intent = self.intent()
        result = approved_dry_run(intent, intent.fingerprint())
        receipt = receipt_from_result(result)
        self.assertEqual(receipt.fingerprint, intent.fingerprint())
        self.assertEqual(receipt.intent_id, intent.intent_id)
        self.assertEqual(receipt.target, intent.target)
        self.assertEqual(receipt.action, intent.action)
        self.assertEqual(receipt.status, "APPROVED_DRY_RUN")
        self.assertFalse(receipt.executed)

    def test_receipt_is_immutable_and_machine_readable(self):
        intent = self.intent()
        receipt = receipt_from_result(approved_dry_run(intent, intent.fingerprint()))
        data = receipt.to_dict()
        self.assertEqual(data["receipt_id"], f"exec:{intent.fingerprint()}")
        self.assertIn("recorded_at", data)
        self.assertIn("evidence", data)
        with self.assertRaises(Exception):
            receipt.status = "EXECUTED"


if __name__ == "__main__":
    unittest.main()
