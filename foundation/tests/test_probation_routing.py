import unittest
from foundation.worker_health import WorkerHealthBook

class ProbationRoutingTests(unittest.TestCase):
    def test_healthy_worker_precedes_probationary_worker(self):
        # A worker part-way through probation is still quarantined
        # (record_success: quarantined == probation_remaining > 0, pinned by
        # test_worker_probation) and rank() excludes quarantined workers
        # (test_worker_quarantine). Once probation completes the worker is
        # eligible and ranks after the healthy worker with real throughput.
        # The former fixture (one of two successes, expected to rank last)
        # failed at its birth commit 98ad4187; delegated decision,
        # HUMAN_DECISIONS.md item 22, 2026-09-26.
        h=WorkerHealthBook()
        h.record("healthy", status="COMPLETED", latency_ms=100)
        h.quarantine("probation", probation_successes=2)
        h.record_success("probation", probation_successes=2)
        self.assertEqual(h.rank(("probation", "healthy")), ("healthy",))
        h.record_success("probation", probation_successes=2)
        self.assertEqual(h.rank(("probation", "healthy")), ("healthy", "probation"))

    def test_probationary_worker_still_remains_eligible(self):
        h=WorkerHealthBook()
        h.quarantine("w1", probation_successes=1)
        h.record_success("w1", probation_successes=1)
        self.assertEqual(h.rank(("w1",)), ("w1",))

if __name__=="__main__": unittest.main()
