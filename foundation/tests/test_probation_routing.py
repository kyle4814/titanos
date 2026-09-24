import unittest
from foundation.worker_health import WorkerHealthBook

class ProbationRoutingTests(unittest.TestCase):
    def test_healthy_worker_precedes_probationary_worker(self):
        h=WorkerHealthBook()
        h.record("healthy", status="COMPLETED", latency_ms=100)
        h.quarantine("probation", probation_successes=2)
        h.record_success("probation", probation_successes=2)
        self.assertEqual(h.rank(("probation", "healthy")), ("healthy", "probation"))

    def test_probationary_worker_still_remains_eligible(self):
        h=WorkerHealthBook()
        h.quarantine("w1", probation_successes=1)
        h.record_success("w1", probation_successes=1)
        self.assertEqual(h.rank(("w1",)), ("w1",))

if __name__=="__main__": unittest.main()
