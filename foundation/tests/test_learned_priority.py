import unittest
from foundation.priority_scheduler import OpportunityPriority
from foundation.opportunity_feedback import OpportunityFeedbackBook, OutcomeFeedback
from foundation.worker_assignment import prioritize_with_learning

class LearnedPriorityTests(unittest.TestCase):
    def test_observed_value_changes_priority_input(self):
        f=OpportunityFeedbackBook()
        f.record(OutcomeFeedback("low",10,5,True,1.0,"2026-09-24T00:00:00+00:00"))
        f.record(OutcomeFeedback("high",10,25,True,1.0,"2026-09-24T00:00:00+00:00"))
        rows=prioritize_with_learning((
            OpportunityPriority("low",priority=0),
            OpportunityPriority("high",priority=0),
        ),f)
        self.assertEqual(rows[0].opportunity_id,"high")
        self.assertGreater(rows[0].expected_value,10)

if __name__=="__main__": unittest.main()
