from __future__ import annotations

import unittest

from foundation.execution_receipt import ExecutionReceipt
from foundation.execution_retry import RetryDecision, classify_retry


def receipt(status: str, executed: bool) -> ExecutionReceipt:
    return ExecutionReceipt(
        receipt_id="exec:EI-test",
        intent_id="EI-test",
        fingerprint="EI-test",
        target="stripe:customer",
        action="CREATE_PAYMENT_LINK",
        status=status,
        executed=executed,
        recorded_at="2026-09-23T00:00:00+00:00",
        evidence="adapter evidence",
    )


class TestExecutionRetry(unittest.TestCase):
    def test_confirmed_execution_is_terminal(self):
        self.assertEqual(
            classify_retry(receipt("EXECUTED", True)),
            RetryDecision.TERMINAL,
        )

    def test_uncertain_outcomes_require_reconciliation(self):
        for status in ("FAILED", "TIMEOUT", "UNKNOWN", "PARTIAL"):
            with self.subTest(status=status):
                self.assertEqual(
                    classify_retry(receipt(status, False)),
                    RetryDecision.RECONCILE_REQUIRED,
                )

    def test_execution_flag_alone_cannot_make_unknown_retryable(self):
        self.assertEqual(
            classify_retry(receipt("UNKNOWN", False)),
            RetryDecision.RECONCILE_REQUIRED,
        )


if __name__ == "__main__":
    unittest.main()
