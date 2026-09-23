"""Deterministic worker lease watchdog policy.

The watchdog only identifies leases needing attention; it never steals a live
lease. A healthy worker must renew through the canonical heartbeat path.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from foundation.next_kernel import OpportunityStore
from foundation.next_leases import recover_expired

@dataclass(frozen=True)
class WatchdogReport:
    expired: tuple[str, ...]
    healthy: tuple[str, ...]
    recovered: tuple[str, ...]

def inspect(store: OpportunityStore, *, now: datetime | None = None,
            recovery: bool = True) -> WatchdogReport:
    now = now or datetime.now(timezone.utc)
    expired_ids=[]
    healthy=[]
    for item in store.load().values():
        if not item.lease_owner or not item.lease_until:
            continue
        expiry=datetime.fromisoformat(item.lease_until)
        if expiry <= now: expired_ids.append(item.opportunity_id)
        else: healthy.append(item.opportunity_id)
    recovered=tuple(x.opportunity_id for x in recover_expired(store, now=now)) if recovery else ()
    return WatchdogReport(tuple(expired_ids),tuple(healthy),recovered)

__all__=["WatchdogReport","inspect"]
