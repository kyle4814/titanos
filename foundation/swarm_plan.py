"""Deterministic swarm planning using learned specialization and worker health."""

from __future__ import annotations
from dataclasses import dataclass
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.workforce_registry import WorkforceRegistry

@dataclass(frozen=True)
class WorkRequirement:
    name: str
    capabilities: tuple[str, ...]
    domain: str | None = None
    required_evidence: tuple[str, ...] = ()
    preferred_workers: int = 1

@dataclass(frozen=True)
class SwarmAssignment:
    requirement: str
    worker_ids: tuple[str, ...]

@dataclass(frozen=True)
class SwarmPlan:
    assignments: tuple[SwarmAssignment, ...]

def plan_swarm(registry: WorkforceRegistry, requirements: tuple[WorkRequirement, ...], *,
               specialization: SpecializationBook | None = None,
               health: WorkerHealthBook | None = None) -> SwarmPlan:
    assignments = []
    for req in requirements:
        matches = registry.match(set(req.capabilities), domain=req.domain)
        ids = tuple(w.worker_id for w in matches)
        if specialization is not None and req.domain is not None:
            ids = specialization.rank(ids, req.domain)
        if health is not None:
            ranked = health.rank(ids)
            rank = {wid: i for i, wid in enumerate(ranked)}
            ids = tuple(sorted(ids, key=lambda wid: (rank.get(wid, len(rank)), wid)))
        selected = ids[:max(1, req.preferred_workers)]
        if not selected:
            raise LookupError(f"no worker satisfies requirement: {req.name}")
        assignments.append(SwarmAssignment(req.name, selected))
    return SwarmPlan(tuple(assignments))

__all__ = ["WorkRequirement", "SwarmAssignment", "SwarmPlan", "plan_swarm"]
