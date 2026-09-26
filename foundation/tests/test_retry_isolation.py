import unittest
from foundation.worker_health import WorkerHealthBook

class RetryIsolationTests(unittest.TestCase):
    def test_retry_failures_quarantine_at_threshold(self):
        health = WorkerHealthBook()
        health.record_retry_failure("w1", quarantine_after=3)
        health.record_retry_failure("w1", quarantine_after=3)
        self.assertFalse(health.workers["w1"].quarantined)
        health.record_retry_failure("w1", quarantine_after=3)
        self.assertTrue(health.workers["w1"].quarantined)

    def test_success_releases_quarantine(self):
        # Written (e7bec52a) before probation existed (53e6ef3c): release
        # now needs `probation_successes` successes, default 2. A
        # single-success probation keeps this test's contract -- one
        # success releases -- under the current one (delegated decision,
        # HUMAN_DECISIONS.md item 22, 2026-09-26).
        health = WorkerHealthBook()
        health.record_retry_failure("w1", quarantine_after=1, probation_successes=1)
        self.assertTrue(health.workers["w1"].quarantined)
        health.record_success("w1")
        self.assertFalse(health.workers["w1"].quarantined)
        self.assertIn("w1", health.rank(("w1",)))

    def test_default_probation_needs_two_successes(self):
        health = WorkerHealthBook()
        health.record_retry_failure("w1", quarantine_after=1)
        health.record_success("w1")
        self.assertTrue(health.workers["w1"].quarantined)
        self.assertNotIn("w1", health.rank(("w1",)))

if __name__ == "__main__":
    unittest.main()
