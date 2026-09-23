import unittest
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook
class TestOpportunityFeedback(unittest.TestCase):
    def test_calibration_uses_realized_outcomes(self):
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("o1",10,16,True,1))
        b.record(OutcomeFeedback("o1",10,8,True,1))
        self.assertEqual(b.calibration("o1"),2)
        self.assertEqual(b.adjusted_value("o1",10),12)
if __name__=="__main__": unittest.main()
