import unittest
from foundation.worker_health import WorkerHealthBook

class ProbationFailureTests(unittest.TestCase):
    def test_failure_during_probation_resets_probation(self):
        h=WorkerHealthBook()
        h.quarantine("w1", probation_successes=3)
        h.record_success("w1", probation_successes=3)
        self.assertEqual(h.workers["w1"].probation_remaining, 2)
        h.record_retry_failure("w1", quarantine_after=9, probation_successes=3)
        self.assertTrue(h.workers["w1"].quarantined)
        self.assertEqual(h.workers["w1"].probation_remaining, 3)

if __name__=="__main__": unittest.main()
