from __future__ import annotations
import unittest
from foundation.swarm_plan import SwarmAssignment, SwarmPlan
from foundation.workforce_dispatcher import DispatchBudget, dispatch
from foundation.worker_result import WorkerResult

class TestDispatcher(unittest.TestCase):
    def test_budget_bounds_active_workers(self):
        plan = SwarmPlan((SwarmAssignment("research", ("a","b","c")),))
        batch = dispatch(plan, DispatchBudget(max_active=2))
        self.assertEqual([x.worker_id for x in batch.items], ["a","b"])
        self.assertEqual([x.worker_id for x in batch.queued], ["c"])

    def test_per_worker_limit_prevents_duplicate_slots(self):
        plan = SwarmPlan((
            SwarmAssignment("a", ("worker-1",)),
            SwarmAssignment("b", ("worker-1",)),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=4, max_per_worker=1))
        self.assertEqual(len(batch.items), 1)
        self.assertEqual(len(batch.queued), 1)

    def test_completed_result_requires_evidence(self):
        with self.assertRaises(ValueError):
            WorkerResult("w","o","COMPLETED","done")

if __name__ == "__main__":
    unittest.main()
