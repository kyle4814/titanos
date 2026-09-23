from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.execution_reconciliation import ReconciliationResult, ReconciliationStatus
from foundation.reconciliation_receipt import reconciliation_receipt_from_result
from foundation.reconciliation_receipt_store import ReconciliationReceiptStore


class TestReconciliationReceiptStore(unittest.TestCase):
    def test_reconciliation_result_becomes_durable_receipt(self):
        result = ReconciliationResult(
            ReconciliationStatus.RESOLVED_EXECUTED,
            ("provider:confirmed",),
            "payment_123",
        )
        receipt = reconciliation_receipt_from_result(
            "exec:abc", "abc", result
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = ReconciliationReceiptStore(Path(tmp) / "reconciliation.json")
            self.assertEqual(store.record(receipt), "RECORDED")
            loaded = store.get(receipt.receipt_id)
            self.assertEqual(loaded, receipt)

    def test_same_reconciliation_is_idempotent(self):
        result = ReconciliationResult(ReconciliationStatus.STILL_UNKNOWN)
        receipt = reconciliation_receipt_from_result("exec:abc", "abc", result)
        with tempfile.TemporaryDirectory() as tmp:
            store = ReconciliationReceiptStore(Path(tmp) / "reconciliation.json")
            self.assertEqual(store.record(receipt), "RECORDED")
            self.assertEqual(store.record(receipt), "DUPLICATE")

    def test_conflicting_reconciliation_cannot_rewrite_history(self):
        first = reconciliation_receipt_from_result(
            "exec:abc", "abc",
            ReconciliationResult(
                ReconciliationStatus.RESOLVED_NOT_EXECUTED,
                ("provider:absent",),
            ),
        )
        second = type(first)(
            receipt_id=first.receipt_id,
            execution_receipt_id=first.execution_receipt_id,
            fingerprint=first.fingerprint,
            status=ReconciliationStatus.RESOLVED_EXECUTED,
            recorded_at=first.recorded_at,
            evidence=("provider:confirmed",),
            external_reference="payment_123",
        )
        with tempfile.TemporaryDirectory() as tmp:
            store = ReconciliationReceiptStore(Path(tmp) / "reconciliation.json")
            store.record(first)
            with self.assertRaisesRegex(ValueError, "collision"):
                store.record(second)


if __name__ == "__main__":
    unittest.main()
