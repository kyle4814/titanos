import unittest
from foundation.swarm_planner import plan_assignment
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry, WorkerSpec
class TestSwarmPlanner(unittest.TestCase):
    def test_planner_routes_eligible_workers(self):
        r=WorkforceRegistry()
        r=r.register(WorkerSpec("a","security",("audit",)))
        r=r.register(WorkerSpec("b","security",("audit",)))
        h=WorkerHealthBook(); h.record("a",status="COMPLETED",latency_ms=1000)
        h.record("b",status="COMPLETED",latency_ms=2000)
        s=SpecializationBook()
        out=plan_assignment(r,h,s,"o1","security",{"audit"})
        self.assertEqual(out.workers,("a","b"))
    def test_unmatched_opportunity_is_explicit(self):
        with self.assertRaises(LookupError):
            plan_assignment(WorkforceRegistry(),WorkerHealthBook(),SpecializationBook(),"o1","security",{"audit"})
if __name__=="__main__": unittest.main()
