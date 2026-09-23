import unittest
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook
from foundation.regime_shift import detect_shift
class TestRegimeShift(unittest.TestCase):
    def test_detects_material_recent_divergence(self):
        b=OpportunityFeedbackBook()
        for i in range(5):
            b.record(OutcomeFeedback("o",100,100,True,1.0))
        b.record(OutcomeFeedback("o",100,0,True,1.0))
        r=detect_shift(b,"o",recent_window=1,threshold=10)
        self.assertTrue(r.detected)
        self.assertLess(r.delta,0)
if __name__=="__main__": unittest.main()
