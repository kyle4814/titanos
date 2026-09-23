"""Deterministic worker router combining capability, health and specialization."""
from __future__ import annotations
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry

def route(registry: WorkforceRegistry, health: WorkerHealthBook,
          specialization: SpecializationBook, worker_ids: tuple[str,...],
          domain: str)->tuple[str,...]:
    eligible=[]
    for wid in worker_ids:
        worker=registry.get(wid)
        if worker is None: continue
        if domain not in worker.capabilities and "*" not in worker.capabilities: continue
        eligible.append(wid)
    specialized=specialization.rank(tuple(eligible),domain)
    return health.rank(specialized)

__all__=["route"]
