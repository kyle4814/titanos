import unittest
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook
from foundation.regime_recovery import assess_recovery
class TestRegimeRecovery(unittest.TestCase):
    def test_stable_fresh_evidence_recovers(self):
        b=OpportunityFeedbackBook()
        for _ in range(3):
            b.record(OutcomeFeedback("o",10,10,True,1.0))
        r=assess_recovery(b,"o",recent_window=3,recovery_window=3,threshold=10)
        self.assertTrue(r.recovered)
        self.assertEqual(r.fresh_evidence_count,3)
    def test_shift_blocks_recovery(self):
        b=OpportunityFeedbackBook()
        for _ in range(3):
            b.record(OutcomeFeedback("o",10,30,True,1.0))
        r=assess_recovery(b,"o",recent_window=3,recovery_window=3,threshold=10)
        self.assertFalse(r.recovered)
if __name__=="__main__": unittest.main()
