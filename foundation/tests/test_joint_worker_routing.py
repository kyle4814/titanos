import unittest
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.swarm_plan import WorkRequirement, plan_swarm
from foundation.workforce_registry import WorkerSpec, WorkforceRegistry

class JointRoutingTests(unittest.TestCase):
    def test_health_and_specialization_are_both_consumed(self):
        registry = WorkforceRegistry().register(WorkerSpec("w1","security",capabilities=("audit",))).register(WorkerSpec("w2","security",capabilities=("audit",)))
        specialization = SpecializationBook()
        specialization.record("w2","security",completed=True,evidence_count=5)
        health = WorkerHealthBook()
        health.record("w2",status="FAILED",latency_ms=1000)
        health.record("w1",status="COMPLETED",latency_ms=100)
        plan = plan_swarm(registry,(WorkRequirement("audit",("audit",),domain="security",preferred_workers=1),),specialization=specialization,health=health)
        self.assertEqual(plan.assignments[0].worker_ids,("w1",))

if __name__=="__main__":
    unittest.main()
