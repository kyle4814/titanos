"""Conflict-aware batch swarm planner.

Plans a bounded set of opportunities without assigning one worker to multiple
simultaneous jobs. Ordering is deterministic; eligibility remains mandatory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from foundation.swarm_planner import PlannedAssignment, plan_assignment
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry

@dataclass(frozen=True)
class BatchPlan:
    assignments: tuple[PlannedAssignment, ...]
    deferred: tuple[str, ...]

@dataclass
class ActiveBatch:
    """In-memory capacity lease for a planned batch; completion releases slots."""
    plan: BatchPlan
    active: dict[str, str] = field(default_factory=dict)

    def start(self, opportunity_id: str) -> str:
        for a in self.plan.assignments:
            if a.opportunity_id == opportunity_id:
                if opportunity_id in self.active:
                    raise ValueError("opportunity already active")
                worker = a.workers[0]
                if worker in self.active.values():
                    raise ValueError("worker already active")
                self.active[opportunity_id] = worker
                return worker
        raise KeyError(opportunity_id)

    def complete(self, opportunity_id: str) -> str:
        try:
            return self.active.pop(opportunity_id)
        except KeyError as exc:
            raise KeyError(f"opportunity is not active: {opportunity_id}") from exc


    def heartbeat(self, opportunity_id: str, worker_id: str) -> bool:
        if self.active.get(opportunity_id) != worker_id:
            raise ValueError("heartbeat does not match active worker")
        return True

    def timeout(self, opportunity_id: str, health: WorkerHealthBook, *, retry: bool = True) -> str:
        worker = self.complete(opportunity_id)
        if retry:
            health.record_retry_failure(worker)
        else:
            health.record(worker, status="FAILED")
        return worker

    @property
    def capacity_used(self) -> int:
        return len(self.active)


def plan_batch(registry: WorkforceRegistry, health: WorkerHealthBook,
               specialization: SpecializationBook,
               opportunities: tuple[tuple[str,str,set[str]], ...],
               max_active: int) -> BatchPlan:
    if max_active < 0: raise ValueError("max_active must be non-negative")
    used: set[str] = set()
    planned: list[PlannedAssignment] = []
    deferred: list[str] = []
    for oid, domain, caps in opportunities:
        try:
            assignment=plan_assignment(registry,health,specialization,oid,domain,caps)
        except LookupError:
            deferred.append(oid); continue
        available=tuple(w for w in assignment.workers if w not in used)
        if not available or len(planned) >= max_active:
            deferred.append(oid); continue
        selected=PlannedAssignment(oid,domain,available)
        planned.append(selected)
        used.add(available[0])
    return BatchPlan(tuple(planned),tuple(deferred))

__all__=["BatchPlan","plan_batch"]
