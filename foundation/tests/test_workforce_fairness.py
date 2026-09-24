import unittest
from foundation.swarm_plan import SwarmAssignment, SwarmPlan
from foundation.workforce_dispatcher import DispatchBudget, dispatch

class DispatcherFairnessTests(unittest.TestCase):
    def test_round_robin_lanes_prevent_first_requirement_starvation(self):
        plan = SwarmPlan((
            SwarmAssignment("a", ("w1", "w2", "w3")),
            SwarmAssignment("b", ("w4",)),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=2, max_per_worker=1, max_queue=8))
        self.assertEqual(tuple((x.requirement, x.worker_id) for x in batch.items), (("a","w1"),("b","w4")))

    def test_fairness_offset_rotates_admission(self):
        plan = SwarmPlan((
            SwarmAssignment("a", ("w1",)),
            SwarmAssignment("b", ("w2",)),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=1, fairness_offset=1))
        self.assertEqual(batch.items[0].worker_id, "w2")

if __name__ == "__main__":
    unittest.main()
