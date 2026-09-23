"""Ingest and finalize a bounded worker execution against NEXT.

Result ingestion is deliberately conservative: it verifies lease ownership,
merges evidence, releases the lease, and leaves lifecycle advancement to the
existing authority-controlled kernel.
"""
from __future__ import annotations
from dataclasses import asdict
from foundation.next_kernel import OpportunityStore
from foundation.next_leases import release
from foundation.worker_result import WorkerResult

def ingest_worker_result(store: OpportunityStore, result: WorkerResult):
    with store._mutation_lock:
        items = store.load()
        if result.opportunity_id not in items:
            raise KeyError(result.opportunity_id)
        current = items[result.opportunity_id]
        if current.lease_owner != result.worker_id:
            raise PermissionError("worker does not own opportunity lease")
        refs = tuple(sorted(set(current.evidence_refs) | set(result.evidence_refs)))
        updated = type(current)(**{**asdict(current), "evidence_refs": refs})
        items[result.opportunity_id] = updated
        store.save(items)
    released = release(store, result.opportunity_id, result.worker_id)
    return released

__all__ = ["ingest_worker_result"]
