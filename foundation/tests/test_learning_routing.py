import unittest
from datetime import datetime, timezone
from foundation.opportunity import OpportunityReceipt, SignalEvidence
from foundation.opportunity_feedback import OpportunityFeedbackBook, OutcomeFeedback
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.worker_assignment import route_with_learning

class LearningRoutingTests(unittest.TestCase):
    def test_routing_exposes_calibrated_value(self):
        oid="OPP-cal"
        f=OpportunityFeedbackBook()
        f.record(OutcomeFeedback(oid,10,20,True,1.0,"2026-09-24T00:00:00+00:00"))
        o=OpportunityReceipt(oid,"target","2026-09-24T00:00:00+00:00",(
            SignalEvidence("DEMAND","demand","PRIMARY","src"),
            SignalEvidence("CODE_PRESSURE","pressure","PRIMARY","src"),
        ),activity_class="ACTIVE",locally_reproducible="YES")
        a,v=route_with_learning(o,("w",),"security",SpecializationBook(),WorkerHealthBook(),f,
            expected_value=10,next_cheapest_experiment="test",what_would_disprove_value="fail",
            now=datetime(2026,9,24,1,tzinfo=timezone.utc))
        self.assertEqual(a.worker_id,"w")
        self.assertGreater(v,10)

if __name__=="__main__": unittest.main()
