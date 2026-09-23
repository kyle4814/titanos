import unittest
from foundation.feedback_scheduler import recalibrate
from foundation.priority_scheduler import OpportunityPriority
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook
class TestFeedbackScheduler(unittest.TestCase):
    def test_realized_value_changes_order(self):
        b=OpportunityFeedbackBook()
        b.record(OutcomeFeedback("a",10,30,True))
        b.record(OutcomeFeedback("b",20,20,True))
        out=recalibrate((OpportunityPriority("a",expected_value=10),OpportunityPriority("b",expected_value=20)),b)
        self.assertEqual(tuple(x.opportunity_id for x in out),("a","b"))
if __name__=="__main__": unittest.main()
