"""Closed-loop worker outcome feedback for TitanOS workforce learning."""

from __future__ import annotations

from dataclasses import dataclass

from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.worker_result import WorkerResult


@dataclass(frozen=True)
class WorkerFeedback:
    worker_id: str
    domain: str
    status: str
    evidence_count: int


def apply_worker_feedback(
    result: WorkerResult,
    domain: str,
    health: WorkerHealthBook,
    specialization: SpecializationBook,
    *,
    latency_ms: float = 0.0,
    retry: bool = False,
) -> WorkerFeedback:
    if not domain.strip():
        raise ValueError("domain is required")
    health.record(
        result.worker_id,
        status=result.status,
        latency_ms=latency_ms,
        retry=retry,
    )
    specialization.record(
        result.worker_id,
        domain,
        completed=result.status == "COMPLETED",
        evidence_count=len(result.evidence_refs),
    )
    return WorkerFeedback(
        result.worker_id,
        domain,
        result.status,
        len(result.evidence_refs),
    )


__all__ = ["WorkerFeedback", "apply_worker_feedback"]
