"""Deterministic swarm planning with optional learned specialization."""

from __future__ import annotations

from dataclasses import dataclass

from foundation.specialization import SpecializationBook
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


def plan_swarm(
    registry: WorkforceRegistry,
    requirements: tuple[WorkRequirement, ...],
    *,
    specialization: SpecializationBook | None = None,
) -> SwarmPlan:
    assignments = []
    for req in requirements:
        matches = registry.match(set(req.capabilities), domain=req.domain)
        if specialization is not None and req.domain is not None:
            ordered = specialization.rank(tuple(w.worker_id for w in matches), req.domain)
            by_id = {w.worker_id: w for w in matches}
            matches = tuple(by_id[worker_id] for worker_id in ordered)
        selected = matches[:max(1, req.preferred_workers)]
        if not selected:
            raise LookupError(f"no worker satisfies requirement: {req.name}")
        assignments.append(SwarmAssignment(req.name, tuple(w.worker_id for w in selected)))
    return SwarmPlan(tuple(assignments))


__all__ = ["WorkRequirement", "SwarmAssignment", "SwarmPlan", "plan_swarm"]
