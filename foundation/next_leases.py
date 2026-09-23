"""Crash-safe worker leases for the canonical NEXT OpportunityStore.

A lease prevents concurrent agents from claiming the same actionable record.
Leases are coordination metadata, not authority: claiming work never advances
lifecycle state and never authorizes consequential actions.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone, timedelta
from typing import Final

from foundation.next_kernel import Opportunity, OpportunityStore

LEASE_STATES: Final[frozenset[str]] = frozenset({
    "DISCOVERED", "QUALIFIED", "PREPARED", "READY", "HUMAN-GATED", "AWAITING-OUTCOME",
})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def claim(store: OpportunityStore, opportunity_id: str, worker_id: str, *, ttl_seconds: int = 900) -> Opportunity:
    if not worker_id.strip():
        raise ValueError("worker_id is required")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    with store._mutation_lock:
        items = store.load()
        if opportunity_id not in items:
            raise KeyError(opportunity_id)
        current = items[opportunity_id]
        if current.status not in LEASE_STATES:
            raise ValueError(f"state {current.status} is not claimable")
        now = _now()
        if current.lease_owner and current.lease_owner != worker_id:
            expiry = _parse(current.lease_until)
            if expiry and expiry > now:
                raise RuntimeError(f"opportunity already leased by {current.lease_owner}")
        updated = replace(
            current,
            lease_owner=worker_id,
            lease_until=(now + timedelta(seconds=ttl_seconds)).isoformat(),
        )
        items[opportunity_id] = updated
        store.save(items)
        return updated


def release(store: OpportunityStore, opportunity_id: str, worker_id: str) -> Opportunity:
    with store._mutation_lock:
        items = store.load()
        if opportunity_id not in items:
            raise KeyError(opportunity_id)
        current = items[opportunity_id]
        if current.lease_owner != worker_id:
            raise PermissionError("only the lease owner can release the lease")
        updated = replace(current, lease_owner="", lease_until="")
        items[opportunity_id] = updated
        store.save(items)
        return updated


def recover_expired(store: OpportunityStore, *, now: datetime | None = None) -> tuple[Opportunity, ...]:
    now = now or _now()
    with store._mutation_lock:
        items = store.load()
        recovered: list[Opportunity] = []
        changed = False
        for key, current in items.items():
            if not current.lease_owner or not current.lease_until:
                continue
            expiry = _parse(current.lease_until)
            if expiry and expiry <= now:
                updated = replace(current, lease_owner="", lease_until="")
                items[key] = updated
                recovered.append(updated)
                changed = True
        if changed:
            store.save(items)
        return tuple(recovered)


__all__ = ["claim", "release", "recover_expired"]
