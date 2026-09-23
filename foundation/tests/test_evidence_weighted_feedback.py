import unittest
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook
class TestEvidenceWeightedFeedback(unittest.TestCase):
    def test_weak_evidence_has_less_influence(self):
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("o",10,30,True,1.0))
        b.record(OutcomeFeedback("o",10,0,True,0.1))
        self.assertAlmostEqual(b.calibration("o"), (20*1 + -10*.1)/1.1)
    def test_unverified_outcome_has_no_influence(self):
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("o",10,100,False,1.0))
        self.assertEqual(b.calibration("o"),0.0)
if __name__=="__main__": unittest.main()
