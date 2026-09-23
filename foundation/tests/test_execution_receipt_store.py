from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from foundation.execution_executor import approved_dry_run
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import receipt_from_result
from foundation.execution_receipt_store import ExecutionReceiptStore


class TestExecutionReceiptStore(unittest.TestCase):
    def make_receipt(self):
        intent = ExecutionIntent(
            intent_id="EI-STORE-1",
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
        return receipt_from_result(approved_dry_run(intent, intent.fingerprint()))

    def test_record_survives_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "execution_receipts.json"
            receipt = self.make_receipt()
            store = ExecutionReceiptStore(path)
            self.assertEqual(store.record(receipt), "RECORDED")
            reloaded = ExecutionReceiptStore(path).get(receipt.receipt_id)
            self.assertEqual(reloaded, receipt)

    def test_same_receipt_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            receipt = self.make_receipt()
            self.assertEqual(store.record(receipt), "RECORDED")
            self.assertEqual(store.record(receipt), "DUPLICATE")

    def test_conflicting_receipt_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            receipt = self.make_receipt()
            store.record(receipt)
            conflicting = type(receipt)(
                receipt_id=receipt.receipt_id,
                intent_id=receipt.intent_id,
                fingerprint=receipt.fingerprint,
                target="different-target",
                action=receipt.action,
                status=receipt.status,
                executed=receipt.executed,
                recorded_at=receipt.recorded_at,
                evidence=receipt.evidence,
            )
            with self.assertRaisesRegex(ValueError, "identity collision"):
                store.record(conflicting)

    def test_malformed_persistence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.json"
            path.write_text("{not-json", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid persisted"):
                ExecutionReceiptStore(path).load()


if __name__ == "__main__":
    unittest.main()
