import unittest
from foundation.priority_scheduler import OpportunityPriority, prioritize
class TestPriorityScheduler(unittest.TestCase):
    def test_deterministic_utility_order(self):
        items=(OpportunityPriority("b",priority=2),OpportunityPriority("a",priority=3))
        self.assertEqual(tuple(x.opportunity_id for x in prioritize(items)),("a","b"))
if __name__=="__main__": unittest.main()
