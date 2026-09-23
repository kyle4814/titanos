import unittest
from foundation.batch_planner import plan_batch
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry, WorkerSpec
class TestBatchPlanner(unittest.TestCase):
    def test_no_worker_is_double_booked(self):
        r=WorkforceRegistry().register(WorkerSpec("a","security",("audit",))).register(WorkerSpec("b","security",("audit",)))
        p=plan_batch(r,WorkerHealthBook(),SpecializationBook(),(("o1","security",{"audit"}),("o2","security",{"audit"})),2)
        self.assertEqual(len(p.assignments),2)
        self.assertNotEqual(p.assignments[0].workers[0],p.assignments[1].workers[0])
    def test_capacity_defers_excess(self):
        r=WorkforceRegistry().register(WorkerSpec("a","security",("audit",)))
        p=plan_batch(r,WorkerHealthBook(),SpecializationBook(),(("o1","security",{"audit"}),("o2","security",{"audit"})),1)
        self.assertEqual(len(p.assignments),1); self.assertEqual(p.deferred,("o2",))
if __name__=="__main__": unittest.main()
