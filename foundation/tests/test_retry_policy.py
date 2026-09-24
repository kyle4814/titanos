import unittest
from foundation.retry_policy import classify_failure, decide_retry

class RetryPolicyTests(unittest.TestCase):
    def test_transient_failure_retries_within_budget(self):
        self.assertEqual(classify_failure("request timed out"), "TRANSIENT")
        d = decide_retry("FAILED", "request timed out", 1, 3)
        self.assertTrue(d.retry)
        self.assertEqual(d.next_attempt, 2)

    def test_permanent_failure_is_not_retried(self):
        d = decide_retry("FAILED", "invalid authorization", 1, 3)
        self.assertFalse(d.retry)

    def test_retry_budget_exhaustion_stops(self):
        d = decide_retry("FAILED", "connection reset", 3, 3)
        self.assertFalse(d.retry)
        self.assertEqual(d.next_attempt, 3)

if __name__ == "__main__":
    unittest.main()
