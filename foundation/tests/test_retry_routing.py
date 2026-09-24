import unittest
from foundation.worker_assignment import select_retry_worker, AssignmentRefused
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook

class RetryRoutingTests(unittest.TestCase):
    def test_retry_selects_best_healthy_alternative(self):
        s=SpecializationBook()
        s.record("failed","security",completed=False)
        s.record("backup","security",completed=True,evidence_count=5)
        s.record("other","security",completed=True,evidence_count=1)
        h=WorkerHealthBook()
        self.assertEqual(select_retry_worker("failed",("failed","backup","other"),"security",s,h),"backup")
    def test_quarantined_alternative_is_skipped(self):
        s=SpecializationBook()
        s.record("backup","security",completed=True,evidence_count=5)
        s.record("other","security",completed=True,evidence_count=1)
        h=WorkerHealthBook(); h.quarantine("backup")
        self.assertEqual(select_retry_worker("failed",("failed","backup","other"),"security",s,h),"other")
    def test_no_healthy_alternative_rejected(self):
        h=WorkerHealthBook(); h.quarantine("backup")
        with self.assertRaises(AssignmentRefused):
            select_retry_worker("failed",("failed","backup"),"security",SpecializationBook(),h)

if __name__=="__main__": unittest.main()
