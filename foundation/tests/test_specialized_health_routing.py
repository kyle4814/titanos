import unittest
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook

class SpecializedHealthRoutingTests(unittest.TestCase):
    def test_domain_fit_then_health(self):
        s=SpecializationBook(); h=WorkerHealthBook()
        s.record("expert","security",completed=True,evidence_count=4)
        s.record("generalist","security",completed=True,evidence_count=1)
        h.record("expert",status="FAILED",latency_ms=100)
        h.record("generalist",status="COMPLETED",latency_ms=100)
        self.assertEqual(s.rank_with_health(("generalist","expert"),"security",h),
                         ("expert","generalist"))

    def test_quarantine_excludes_specialist(self):
        s=SpecializationBook(); h=WorkerHealthBook()
        s.record("expert","security",completed=True,evidence_count=9)
        h.quarantine("expert")
        self.assertEqual(s.rank_with_health(("expert","other"),"security",h),
                         ("other",))

if __name__=="__main__": unittest.main()
