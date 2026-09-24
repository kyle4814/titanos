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

    def test_router_uses_unified_specialization_then_health_tiebreak(self):
        from foundation.worker_health import WorkerHealthBook
        from foundation.specialization import SpecializationBook
        from foundation.worker_router import route

        registry = WorkforceRegistry().register(
            WorkerSpec("expert-slow", "security", ("security",))
        ).register(
            WorkerSpec("expert-fast", "security", ("security",))
        )
        specialization = SpecializationBook()
        specialization.record("expert-slow", "security", completed=True, evidence_count=20)
        specialization.record("expert-fast", "security", completed=True, evidence_count=20)
        health = WorkerHealthBook()
        health.record("expert-slow", status="COMPLETED", latency_ms=2000)
        health.record("expert-fast", status="COMPLETED", latency_ms=500)
        self.assertEqual(
            route(registry, health, specialization, ("expert-slow", "expert-fast"), "security"),
            ("expert-fast", "expert-slow"),
        )

    def test_router_combines_domain_capability_specialization_and_health(self):
        from foundation.worker_health import WorkerHealthBook
        from foundation.specialization import SpecializationBook
        from foundation.worker_router import route

        registry = WorkforceRegistry().register(
            WorkerSpec("specialist", "security", ("security",))
        ).register(
            WorkerSpec("generalist", "security", ("security",))
        ).register(
            WorkerSpec("wrong-domain", "research", ("research",))
        )
        specialization = SpecializationBook()
        specialization.record("specialist", "security", completed=True, evidence_count=10)
        health = WorkerHealthBook()
        health.record("specialist", status="COMPLETED", latency_ms=500)
        health.record("generalist", status="COMPLETED", latency_ms=2000)
        routed = route(registry, health, specialization,
                       ("specialist", "generalist", "wrong-domain"), "security")
        self.assertEqual(routed, ("specialist", "generalist"))

    def test_specialization_ranking_prefers_domain_experience(self):
        from foundation.specialization import SpecializationBook

        book = SpecializationBook()
        book.record("generalist", "security", completed=True, evidence_count=1)
        book.record("specialist", "security", completed=True, evidence_count=10)
        book.record("specialist", "security", completed=True, evidence_count=10)
        self.assertEqual(book.rank(("generalist", "specialist"), "security"), ("specialist", "generalist"))

    def test_health_ranking_prefers_successful_fast_worker(self):
        from foundation.worker_health import WorkerHealthBook

        health = WorkerHealthBook()
        health.record("slow", status="COMPLETED", latency_ms=2000)
        health.record("fast", status="COMPLETED", latency_ms=500)
        health.record("unreliable", status="FAILED", latency_ms=500)
        self.assertEqual(health.rank(("slow", "fast", "unreliable")), ("fast", "slow", "unreliable"))

    def test_dispatch_fills_available_capacity_fairly_before_queueing(self):
        from foundation.workforce_dispatcher import DispatchBudget, dispatch

        registry = WorkforceRegistry().register(
            WorkerSpec("worker-a", "research", ("research",))
        ).register(
            WorkerSpec("worker-b", "research", ("research",))
        ).register(
            WorkerSpec("worker-c", "research", ("research",))
        )
        plan = plan_swarm(registry, (
            WorkRequirement("a", ("research",), "research"),
            WorkRequirement("b", ("research",), "research"),
            WorkRequirement("c", ("research",), "research"),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=2, max_per_worker=1))
        self.assertEqual(len(batch.items), 2)
        self.assertEqual(len(batch.queued), 1)
        self.assertEqual([item.slot for item in batch.items], [0, 1])
        self.assertEqual([item.worker_id for item in batch.items], ["worker-a", "worker-b"])

    def test_dispatch_applies_queue_backpressure_without_touching_active(self):
        from foundation.workforce_dispatcher import DispatchBudget, dispatch

        registry = WorkforceRegistry()
        for worker_id in ("a", "b", "c", "d"):
            registry = registry.register(WorkerSpec(worker_id, "research", ("research",)))
        plan = plan_swarm(registry, tuple(
            WorkRequirement(name, ("research",), "research")
            for name in ("r1", "r2", "r3", "r4")
        ))
        batch = dispatch(plan, DispatchBudget(max_active=1, max_per_worker=1, max_queue=1))
        self.assertEqual(len(batch.items), 1)
        self.assertEqual(len(batch.queued), 1)
        self.assertEqual(len(batch.dropped), 2)
        self.assertEqual(batch.items[0].worker_id, "a")

    def test_dispatch_never_duplicates_active_worker(self):
        from foundation.workforce_dispatcher import DispatchBudget, dispatch

        registry = WorkforceRegistry().register(
            WorkerSpec("worker-1", "research", ("research",))
        )
        plan = plan_swarm(registry, (
            WorkRequirement("research-a", ("research",), "research"),
            WorkRequirement("research-b", ("research",), "research"),
        ))
        batch = dispatch(plan, DispatchBudget(max_active=8, max_per_worker=1))
        self.assertEqual([item.worker_id for item in batch.items], ["worker-1"])
        self.assertEqual(len(batch.queued), 1)

    def test_swarm_plan_assigns_specialists(self):
        registry = WorkforceRegistry().register(
            WorkerSpec("researcher", "commercial", ("research", "evidence"))
        )
        plan = plan_swarm(registry, (
            WorkRequirement("research", ("research",), "commercial"),
        ))
        self.assertEqual(plan.assignments[0].worker_ids, ("researcher",))

    def test_router_prefers_specialization_then_health(self):
        from foundation.specialization import SpecializationBook
        from foundation.worker_health import WorkerHealthBook
        from foundation.worker_router import route

        registry = WorkforceRegistry().register(
            WorkerSpec("general", "research", ("research",))
        ).register(
            WorkerSpec("specialist", "research", ("research", "security"))
        )
        health = WorkerHealthBook()
        health.record("general", status="COMPLETED", latency_ms=100)
        health.record("specialist", status="COMPLETED", latency_ms=200)
        specialization = SpecializationBook()
        specialization.learn("specialist", "security", success=True)
        ordered = route(registry, health, specialization, ("general", "specialist"), "security")
        self.assertEqual(ordered[0], "specialist")

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
