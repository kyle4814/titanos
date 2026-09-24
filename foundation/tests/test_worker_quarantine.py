import unittest
from foundation.worker_health import WorkerHealthBook

class WorkerQuarantineTests(unittest.TestCase):
    def test_quarantined_worker_is_excluded_from_rank(self):
        health = WorkerHealthBook()
        health.record("w1", status="FAILED", latency_ms=100)
        health.record("w2", status="COMPLETED", latency_ms=100)
        health.quarantine("w1")
        self.assertEqual(health.rank(("w1", "w2")), ("w2",))

    def test_recovered_worker_reenters_routing(self):
        health = WorkerHealthBook()
        health.quarantine("w1")
        self.assertEqual(health.rank(("w1", "w2")), ("w2",))
        health.recover("w1")
        self.assertEqual(set(health.rank(("w1", "w2"))), {"w1", "w2"})

if __name__ == "__main__":
    unittest.main()
