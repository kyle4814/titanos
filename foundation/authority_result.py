"""Authority-aware worker result application to NEXT lifecycle."""
from __future__ import annotations

from foundation.next_kernel import OpportunityStore
from foundation.worker_result import WorkerResult

STATUS_MAP = {
    "BLOCKED": "BLOCKED",
    "FAILED": "FAILED",
    "ESCALATED": "HUMAN-GATED",
}

def apply_worker_result(store: OpportunityStore, result: WorkerResult):
    item = store.load()[result.opportunity_id]
    if result.status == "COMPLETED":
        if not result.evidence_refs:
            raise ValueError("completed work requires evidence")
        # A worker may prepare evidence, but cannot self-promote past the
        # authority envelope enforced by OpportunityStore.advance().
        target = "PREPARED" if item.status in {"DISCOVERED", "QUALIFIED"} else item.status
    else:
        target = STATUS_MAP[result.status]

    if target != item.status:
        item = store.advance(result.opportunity_id, target)
    return item

__all__ = ["apply_worker_result"]
