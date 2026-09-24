import unittest
from foundation.worker_health import WorkerHealthBook

class WorkerProbationTests(unittest.TestCase):
    def test_quarantined_worker_requires_probation_successes(self):
        h=WorkerHealthBook()
        h.record_retry_failure("w1", quarantine_after=1)
        h.record_success("w1", probation_successes=2)
        self.assertTrue(h.workers["w1"].quarantined)
        self.assertEqual(h.workers["w1"].probation_remaining, 1)
        h.record_success("w1", probation_successes=2)
        self.assertFalse(h.workers["w1"].quarantined)

    def test_recovery_does_not_bypass_probation(self):
        h=WorkerHealthBook()
        h.quarantine("w1", probation_successes=2)
        h.record_success("w1", probation_successes=3)
        self.assertTrue(h.workers["w1"].quarantined)
        self.assertEqual(h.workers["w1"].probation_remaining, 2)

if __name__=="__main__": unittest.main()
