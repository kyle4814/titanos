import unittest

from foundation.specialization import SpecializationBook
from foundation.swarm_plan import WorkRequirement, plan_swarm
from foundation.workforce_registry import WorkerSpec, WorkforceRegistry


class SwarmSpecializationTests(unittest.TestCase):
    def test_learned_specialization_orders_matching_workers(self):
        registry = WorkforceRegistry().register(
            WorkerSpec("w1", "security", capabilities=("audit",))
        ).register(
            WorkerSpec("w2", "security", capabilities=("audit",))
        )
        specialization = SpecializationBook()
        for _ in range(3):
            specialization.record("w2", "security", completed=True, evidence_count=2)
        specialization.record("w1", "security", completed=False)
        plan = plan_swarm(
            registry,
            (WorkRequirement("audit", ("audit",), domain="security", preferred_workers=2),),
            specialization=specialization,
        )
        self.assertEqual(plan.assignments[0].worker_ids, ("w2", "w1"))

    def test_without_specialization_existing_order_is_preserved(self):
        registry = WorkforceRegistry().register(
            WorkerSpec("w1", "security", capabilities=("audit",))
        ).register(
            WorkerSpec("w2", "security", capabilities=("audit",))
        )
        plan = plan_swarm(
            registry,
            (WorkRequirement("audit", ("audit",), domain="security", preferred_workers=2),),
        )
        self.assertEqual(plan.assignments[0].worker_ids, ("w1", "w2"))


if __name__ == "__main__":
    unittest.main()
