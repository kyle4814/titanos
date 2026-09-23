import unittest
from foundation.workforce_dispatcher import DispatchBudget, DispatchBatch, DispatchItem
from foundation.workforce_refill import refill
class TestRefill(unittest.TestCase):
    def test_refills_freed_slots(self):
        b=DispatchBatch((DispatchItem("a","r",0),),(DispatchItem("b","r",-1),DispatchItem("c","r",-1)))
        p=refill(b,DispatchBudget(max_active=2))
        self.assertEqual([x.worker_id for x in p.active],["a","b"])
        self.assertEqual([x.worker_id for x in p.queued],["c"])
        self.assertEqual(p.available_slots,0)
if __name__=="__main__": unittest.main()
