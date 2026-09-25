import unittest
from foundation.priority_scheduler import OpportunityPriority
from foundation.regime_shift import RegimeShift
from foundation.regime_scheduler import apply_regime_state
class TestRegimeScheduler(unittest.TestCase):
    def test_shifted_opportunity_is_downgraded(self):
        items=(OpportunityPriority("shifted",expected_value=20),OpportunityPriority("stable",expected_value=10))
        shifts=(RegimeShift("shifted",5,-5,-10,True),)
        out=apply_regime_state(items,shifts,(),penalty=15)
        self.assertEqual(tuple(x.opportunity_id for x in out),("stable","shifted"))
    def test_unflagged_is_unchanged(self):
        item=OpportunityPriority("o",expected_value=20)
        out=apply_regime_state((item,),(),(),10)
        self.assertEqual(out[0],item)
if __name__=="__main__": unittest.main()
