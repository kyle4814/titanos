"""Worker heartbeat/lease renewal for long-running bounded workers."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from dataclasses import replace
from foundation.next_kernel import Opportunity, OpportunityStore

def renew(store: OpportunityStore, opportunity_id: str, worker_id: str, *, ttl_seconds: int = 900,
          now: datetime | None = None) -> Opportunity:
    if ttl_seconds <= 0: raise ValueError("ttl_seconds must be positive")
    now = now or datetime.now(timezone.utc)
    with store._mutation_lock:
        items=store.load()
        if opportunity_id not in items: raise KeyError(opportunity_id)
        current=items[opportunity_id]
        if current.lease_owner != worker_id:
            raise PermissionError("only the lease owner can renew the lease")
        if not current.lease_until: raise RuntimeError("lease has no expiry")
        expiry=datetime.fromisoformat(current.lease_until)
        if expiry <= now: raise RuntimeError("cannot renew an expired lease")
        updated=replace(current, lease_until=(now+timedelta(seconds=ttl_seconds)).isoformat())
        items[opportunity_id]=updated
        store.save(items)
        return updated

__all__=["renew"]
