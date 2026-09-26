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

    def test_success_argument_does_not_raise_the_requirement(self):
        # Delegated contract decision (HUMAN_DECISIONS.md item 21,
        # 2026-09-26): the requirement is fixed when the worker is
        # quarantined; `probation_successes` on record_success is validated
        # and otherwise ignored (as since 53e6ef3c). Raising the requirement
        # on a later call would need the original requirement persisted,
        # which no field stores -- the former expectation here
        # (`probation_remaining == 2` after one success against a
        # requirement of 2) failed at its birth commit 7adeaef4 and had no
        # stateless formula consistent with the test above.
        h=WorkerHealthBook()
        h.quarantine("w1", probation_successes=2)
        h.record_success("w1", probation_successes=3)
        self.assertTrue(h.workers["w1"].quarantined)
        self.assertEqual(h.workers["w1"].probation_remaining, 1)
        with self.assertRaises(ValueError):
            h.record_success("w1", probation_successes=0)

if __name__=="__main__": unittest.main()
