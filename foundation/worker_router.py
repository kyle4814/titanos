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
) -> tuple[str, ...]:
    eligible = []
    for wid in worker_ids:
        worker = registry.get(wid)
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
