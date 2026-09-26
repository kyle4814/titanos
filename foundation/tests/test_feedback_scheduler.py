import unittest
from foundation.feedback_scheduler import recalibrate
from foundation.priority_scheduler import OpportunityPriority
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook
class TestFeedbackScheduler(unittest.TestCase):
    def test_realized_value_changes_order(self):
        # Passed at birth (a292816c) with an unweighted calibration; feedback
        # has been evidence-weighted since, and a record with the default
        # evidence_strength=0.0 carries no weight. Evidenced feedback keeps
        # this test's contract: a realised over-delivery re-orders.
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("a",10,30,True,evidence_strength=1.0))
        b.record(OutcomeFeedback("b",20,20,True,evidence_strength=1.0))
        out=recalibrate((OpportunityPriority("a",expected_value=10),OpportunityPriority("b",expected_value=20)),b)
        self.assertEqual(tuple(x.opportunity_id for x in out),("a","b"))
    def test_unevidenced_feedback_does_not_reorder(self):
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("a",10,30,True))
        out=recalibrate((OpportunityPriority("a",expected_value=10),OpportunityPriority("b",expected_value=20)),b)
        self.assertEqual(tuple(x.opportunity_id for x in out),("b","a"))
if __name__=="__main__": unittest.main()
