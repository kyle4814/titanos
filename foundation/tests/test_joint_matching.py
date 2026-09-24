import unittest
from foundation.priority_scheduler import OpportunityPriority
from foundation.opportunity_feedback import OpportunityFeedbackBook, OutcomeFeedback
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.worker_assignment import match_opportunity_workers

class JointMatchTests(unittest.TestCase):
    def test_learned_priority_and_specialization_jointly_match(self):
        f=OpportunityFeedbackBook()
        f.record(OutcomeFeedback("high",10,30,True,1.0,"2026-09-24T00:00:00+00:00"))
        s=SpecializationBook()
        s.record("expert","security",completed=True,evidence_count=10)
        s.record("novice","security",completed=True,evidence_count=1)
        out=match_opportunity_workers(
            (OpportunityPriority("low"),OpportunityPriority("high")),
            ("novice","expert"),"security",s,WorkerHealthBook(),f)
        self.assertEqual(out[0],("high","expert"))

if __name__=="__main__": unittest.main()
