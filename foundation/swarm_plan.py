"""Deterministic swarm planning from bounded work requirements."""

from __future__ import annotations

from dataclasses import dataclass
from foundation.workforce_registry import WorkerSpec, WorkforceRegistry

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

def plan_swarm(registry: WorkforceRegistry, requirements: tuple[WorkRequirement, ...]) -> SwarmPlan:
    assignments = []
    for req in requirements:
        matches = registry.match(set(req.capabilities), domain=req.domain)
        selected = matches[:max(1, req.preferred_workers)]
        if not selected:
            raise LookupError(f"no worker satisfies requirement: {req.name}")
        assignments.append(SwarmAssignment(req.name, tuple(w.worker_id for w in selected)))
    return SwarmPlan(tuple(assignments))

__all__ = ["WorkRequirement", "SwarmAssignment", "SwarmPlan", "plan_swarm"]
