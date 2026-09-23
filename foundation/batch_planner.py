"""Conflict-aware batch swarm planner.

Plans a bounded set of opportunities without assigning one worker to multiple
simultaneous jobs. Ordering is deterministic; eligibility remains mandatory.
"""
from __future__ import annotations
from dataclasses import dataclass
from foundation.swarm_planner import PlannedAssignment, plan_assignment
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry

@dataclass(frozen=True)
class BatchPlan:
    assignments: tuple[PlannedAssignment, ...]
    deferred: tuple[str, ...]

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
