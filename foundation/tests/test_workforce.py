from __future__ import annotations

import unittest

from foundation.swarm_plan import WorkRequirement, plan_swarm
from foundation.worker_execution_contract import WorkerExecutionContract
from foundation.workforce_registry import WorkerSpec, WorkforceRegistry


class TestWorkforce(unittest.TestCase):
    def test_registry_matches_capabilities(self):
        registry = WorkforceRegistry().register(
            WorkerSpec("osint-1", "osint", ("research", "evidence"), "sonnet")
        ).register(
            WorkerSpec("cheap-1", "osint", ("research",), "haiku")
        )
        matches = registry.match({"research", "evidence"}, domain="osint")
        self.assertEqual([w.worker_id for w in matches], ["osint-1"])


    def test_duplicate_worker_ids_are_rejected(self):
        registry = WorkforceRegistry().register(WorkerSpec("worker-1", "research"))
        with self.assertRaises(ValueError):
            registry.register(WorkerSpec("worker-1", "research"))

    def test_dispatch_budget_bounds_active_workers(self):
        from foundation.workforce_dispatcher import DispatchBudget, dispatch

        registry = WorkforceRegistry().register(
            WorkerSpec("worker-1", "research", ("research",))
        ).register(
            WorkerSpec("worker-2", "research", ("research",))
        )
        plan = plan_swarm(registry, (
            WorkRequirement("research", ("research",), "research"),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=1, max_per_worker=1))
        self.assertEqual(len(batch.items), 1)
        self.assertLessEqual(len(batch.items), 1)
        self.assertEqual(batch.items[0].slot, 0)

    def test_swarm_plan_assigns_specialists(self):
        registry = WorkforceRegistry().register(
            WorkerSpec("researcher", "commercial", ("research", "evidence"))
        )
        plan = plan_swarm(registry, (
            WorkRequirement("research", ("research",), "commercial"),
        ))
        self.assertEqual(plan.assignments[0].worker_ids, ("researcher",))

    def test_execution_contract_is_bounded(self):
        contract = WorkerExecutionContract(
            "worker-1", "opp-1", "qualify opportunity",
            allowed_tools=("browser",),
            allowed_actions=("research", "draft"),
            forbidden_actions=("submit", "sign"),
            required_evidence=("source_url",),
            authority_ceiling="O1",
        )
        self.assertEqual(contract.authority_ceiling, "O1")
        self.assertIn("submit", contract.forbidden_actions)


if __name__ == "__main__":
    unittest.main()
