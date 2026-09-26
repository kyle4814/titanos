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
        # A shift is recent calibration versus the whole history
        # (regime_shift.detect_shift, pinned by test_regime_shift), so a
        # history that is entirely the recent window can never register one;
        # the former fixture failed at its birth commit 6db050ac. Three
        # on-target outcomes followed by three +20 over-deliveries move the
        # recent window 10 away from the historical mean, at the threshold.
        b=OpportunityFeedbackBook()
        for _ in range(3):
            b.record(OutcomeFeedback("o",10,10,True,1.0))
        for _ in range(3):
            b.record(OutcomeFeedback("o",10,30,True,1.0))
        r=assess_recovery(b,"o",recent_window=3,recovery_window=3,threshold=10)
        self.assertTrue(r.shift.detected)
        self.assertFalse(r.recovered)
        self.assertEqual(r.fresh_evidence_count,3)
if __name__=="__main__": unittest.main()
