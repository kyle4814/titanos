import unittest
from datetime import datetime, timezone, timedelta
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook

class TestFeedbackDecay(unittest.TestCase):
    def test_old_evidence_has_less_weight(self):
        now=datetime.now(timezone.utc)
        fresh=OutcomeFeedback("o",10,30,True,1.0,(now-timedelta(days=1)).isoformat())
        old=OutcomeFeedback("o",10,30,True,1.0,(now-timedelta(days=30)).isoformat())
        self.assertGreater(fresh.decayed_weight(now),old.decayed_weight(now))

    def test_decay_changes_calibration(self):
        now=datetime.now(timezone.utc)
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("o",10,30,True,1.0,(now-timedelta(days=60)).isoformat()))
        b.record(OutcomeFeedback("o",10,0,True,1.0,now.isoformat()))
        self.assertLess(b.calibration("o",now=now,half_life_days=30),0.0)

if __name__=="__main__":
    unittest.main()
