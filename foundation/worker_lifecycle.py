"""Worker result ingestion and lease lifecycle helpers."""
from __future__ import annotations
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import release

def complete_worker(store: OpportunityStore, opportunity_id: str, worker_id: str, result) -> Opportunity:
    item = store.load()[opportunity_id]
    if item.lease_owner != worker_id:
        raise PermissionError("worker does not own opportunity lease")
    if result.opportunity_id != opportunity_id or result.worker_id != worker_id:
        raise ValueError("result identity mismatch")
    if result.status == "COMPLETED" and not result.evidence_refs:
        raise ValueError("completed work requires evidence")
    updated = Opportunity(**{
        **item.__dict__,
        "evidence_refs": tuple(dict.fromkeys((*item.evidence_refs, *result.evidence_refs))),
        "next_action": result.summary,
    })
    store.upsert(updated)
    release(store, opportunity_id, worker_id)
    return store.load()[opportunity_id]

__all__ = ["complete_worker"]
