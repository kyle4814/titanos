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
        health = WorkerHealthBook()
        health.record_retry_failure("w1", quarantine_after=1)
        self.assertTrue(health.workers["w1"].quarantined)
        health.record_success("w1")
        self.assertFalse(health.workers["w1"].quarantined)
        self.assertIn("w1", health.rank(("w1",)))

if __name__ == "__main__":
    unittest.main()
