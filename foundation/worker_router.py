"""Deterministic worker router combining capability, health and specialization."""

from __future__ import annotations

from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry


def route(
    registry: WorkforceRegistry,
    health: WorkerHealthBook,
    specialization: SpecializationBook,
    worker_ids: tuple[str, ...],
    domain: str,
    min_authority: str = "O0",
) -> tuple[str, ...]:
    levels = {"O0": 0, "O1": 1, "O2": 2, "O3": 3, "O4": 4}
    if min_authority not in levels:
        raise ValueError("invalid minimum authority")
    eligible = []
    for wid in worker_ids:
        worker = registry.get(wid)
        if worker.domain != domain:
            continue
        if levels[worker.authority_ceiling] < levels[min_authority]:
            continue
        if domain not in worker.capabilities and "*" not in worker.capabilities:
            continue
        eligible.append(wid)

    def score(wid: str) -> tuple[float, float, float, float, str]:
        h = health.workers.get(wid)
        s = specialization.records.get((wid, domain))
        throughput = h.throughput if h else 0.0
        failure_rate = h.failure_rate if h else 0.0
        success_rate = s.success_rate if s else 0.0
        evidence = float(s.evidence_count if s else 0)
        return (-success_rate, -evidence, -throughput, failure_rate, wid)

    return tuple(sorted(eligible, key=score))


__all__ = ["route"]
