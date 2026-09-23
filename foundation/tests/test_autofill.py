import unittest
from foundation.workforce_dispatcher import DispatchBatch, DispatchBudget, DispatchItem
from foundation.workforce_autofill import on_worker_finished
class TestAutoFill(unittest.TestCase):
    def test_completion_promotes_queued_work(self):
        batch=DispatchBatch((DispatchItem("a","r",0),),(DispatchItem("b","r",-1),DispatchItem("c","r",-1)))
        out,event=on_worker_finished(batch,DispatchBudget(max_active=2),"a","o-a")
        self.assertEqual([x.worker_id for x in out.items],["a","b"])
        self.assertEqual([x.worker_id for x in out.queued],["c"])
        self.assertEqual([x.worker_id for x in event.promoted],["b"])
if __name__=="__main__": unittest.main()
