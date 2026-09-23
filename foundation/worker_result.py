"""Structured result envelope returned by TitanOS workers."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class WorkerResult:
    worker_id: str
    opportunity_id: str
    status: str
    summary: str
    evidence_refs: tuple[str, ...] = ()
    receipt_ref: str | None = None
    escalation: str | None = None
    error: str | None = None
    def __post_init__(self) -> None:
        if self.status not in {"COMPLETED", "BLOCKED", "FAILED", "ESCALATED"}:
            raise ValueError("invalid worker result status")
        if not self.worker_id.strip() or not self.opportunity_id.strip():
            raise ValueError("worker_id and opportunity_id are required")
        if self.status == "COMPLETED" and not self.evidence_refs:
            raise ValueError("completed work requires evidence_refs")

__all__ = ["WorkerResult"]
