"""Router-driven swarm planning for TitanOS."""
from __future__ import annotations
from dataclasses import dataclass
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.worker_router import route
from foundation.workforce_registry import WorkforceRegistry

@dataclass(frozen=True)
class PlannedAssignment:
    opportunity_id: str
    domain: str
    workers: tuple[str, ...]

def plan_assignment(registry: WorkforceRegistry, health: WorkerHealthBook,
                     specialization: SpecializationBook, opportunity_id: str,
                     domain: str, required_capabilities: set[str]) -> PlannedAssignment:
    eligible = tuple(w.worker_id for w in registry.match(required_capabilities, domain=domain))
    ranked = route(registry, health, specialization, eligible, domain)
    if not ranked:
        raise LookupError("no eligible worker for opportunity")
    return PlannedAssignment(opportunity_id, domain, ranked)

__all__=["PlannedAssignment","plan_assignment"]
