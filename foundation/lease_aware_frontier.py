"""Lease-aware frontier scheduling over the canonical NEXT store."""

from __future__ import annotations

from datetime import datetime, timezone
from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import recover_expired


SCHEDULABLE = frozenset({
    "DISCOVERED", "QUALIFIED", "PREPARED", "READY",
})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _live(opportunity: Opportunity, now: datetime) -> bool:
    if not opportunity.lease_owner or not opportunity.lease_until:
        return False
    try:
        return datetime.fromisoformat(opportunity.lease_until) > now
    except ValueError:
        return False


def available_frontier(
    store: OpportunityStore,
    *,
    limit: int = 1,
    recover: bool = True,
) -> tuple[Opportunity, ...]:
    """Return highest-value unleased actionable work.

    Expired leases are reclaimed first. Selection is deterministic and does
    not advance lifecycle state or claim work; callers must claim atomically.
    """
    if limit < 0:
        raise ValueError("limit must be non-negative")
    if recover:
        recover_expired(store)
    now = _now()
    candidates = [
        item for item in store.actionable()
        if item.status in SCHEDULABLE and not _live(item, now)
    ]
    candidates.sort(key=lambda x: (x.deadline is None, x.deadline or "", -(x.value or 0.0), x.id))
    return tuple(candidates[:limit])


__all__ = ["available_frontier", "SCHEDULABLE"]
