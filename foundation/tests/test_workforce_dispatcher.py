import unittest

from foundation.swarm_plan import SwarmAssignment, SwarmPlan
from foundation.workforce_dispatcher import DispatchBudget, dispatch


class DispatcherBackpressureTests(unittest.TestCase):
    def test_active_capacity_and_per_worker_limit(self):
        plan = SwarmPlan((
            SwarmAssignment("a", ("w1", "w2")),
            SwarmAssignment("b", ("w1", "w3")),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=2, max_per_worker=1, max_queue=8))
        self.assertEqual(tuple(x.worker_id for x in batch.items), ("w1", "w2"))
        self.assertEqual(tuple(x.worker_id for x in batch.queued), ("w1", "w3"))

    def test_queue_capacity_is_hard_bounded(self):
        plan = SwarmPlan((
            SwarmAssignment("a", ("w1", "w2")),
            SwarmAssignment("b", ("w3", "w4")),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=1, max_per_worker=1, max_queue=1))
        self.assertEqual(len(batch.items), 1)
        self.assertEqual(len(batch.queued), 1)
        self.assertEqual(tuple(x.worker_id for x in batch.dropped), ("w4",))

if __name__ == "__main__":
    unittest.main()
