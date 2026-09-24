import unittest
from datetime import datetime, timezone, timedelta
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook

class LearningInvariantsTests(unittest.TestCase):
    def test_completed_feedback_is_bounded_by_evidence_strength(self):
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("x",10,20,True,2.0))
        b.record(OutcomeFeedback("x",10,0,True,-1.0))
        self.assertEqual(b.records["x"][0].weight,1.0)
        self.assertEqual(b.records["x"][1].weight,0.0)
    def test_incomplete_outcome_has_zero_learning_weight(self):
        self.assertEqual(OutcomeFeedback("x",10,100,False,1.0).weight,0.0)
    def test_time_decay_never_increases_weight(self):
        observed=datetime.now(timezone.utc)-timedelta(days=30)
        f=OutcomeFeedback("x",10,20,True,1.0,observed.isoformat())
        self.assertLessEqual(f.decayed_weight(datetime.now(timezone.utc)),f.weight)
    def test_empty_history_is_neutral(self):
        self.assertEqual(OpportunityFeedbackBook().calibration("missing"),0.0)

if __name__=="__main__": unittest.main()
