from __future__ import annotations

import unittest

from foundation.execution_reconciliation import (
    ReconciliationResult,
    ReconciliationStatus,
)


class TestExecutionReconciliation(unittest.TestCase):
    def test_resolved_executed_preserves_external_reference(self):
        result = ReconciliationResult(
            ReconciliationStatus.RESOLVED_EXECUTED,
            ("stripe:payment:confirmed",),
            "payment_123",
        )
        self.assertEqual(result.status, ReconciliationStatus.RESOLVED_EXECUTED)
        self.assertEqual(result.external_reference, "payment_123")

    def test_still_unknown_remains_explicit(self):
        result = ReconciliationResult(
            ReconciliationStatus.STILL_UNKNOWN,
            ("provider unavailable",),
        )
        self.assertEqual(result.status, ReconciliationStatus.STILL_UNKNOWN)
        self.assertEqual(result.to_dict()["status"], "STILL_UNKNOWN")

    def test_resolved_not_executed_is_distinct(self):
        result = ReconciliationResult(ReconciliationStatus.RESOLVED_NOT_EXECUTED)
        self.assertNotEqual(
            result.status, ReconciliationStatus.RESOLVED_EXECUTED
        )


if __name__ == "__main__":
    unittest.main()
