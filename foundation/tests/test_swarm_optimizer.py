import unittest
from foundation.swarm_plan import SwarmAssignment, SwarmPlan
from foundation.worker_health import WorkerHealthBook
from foundation.workforce_registry import WorkforceRegistry
from foundation.swarm_optimizer import optimize_plan
class TestSwarmOptimizer(unittest.TestCase):
    def test_health_reorders_workers(self):
        p=SwarmPlan((SwarmAssignment("r",("slow","fast")),))
        h=WorkerHealthBook()
        h.record("slow",status="COMPLETED",latency_ms=2000)
        h.record("fast",status="COMPLETED",latency_ms=1000)
        out=optimize_plan(p,WorkforceRegistry(),h)
        self.assertEqual(out.assignments[0].worker_ids,("fast","slow"))
if __name__=="__main__": unittest.main()
