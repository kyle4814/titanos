"""Atomic frontier acquisition for the canonical NEXT store.

Selection and lease assignment happen under the same store mutation lock, so
two workers cannot both successfully acquire the same live opportunity.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from foundation.next_kernel import Opportunity, OpportunityStore
from foundation.next_leases import LEASE_STATES, recover_expired


def _now() -> datetime:
    return datetime.now(timezone.utc)


def acquire_next(
    store: OpportunityStore,
    worker_id: str,
    *,
    ttl_seconds: int = 900,
) -> Opportunity | None:
    if not worker_id.strip():
        raise ValueError("worker_id is required")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")

    with store._mutation_lock:
        recover_expired(store, now=_now())
        items = store.load()
        now = _now()

        candidates = []
        for item in items.values():
            if item.status not in LEASE_STATES:
                continue
            if item.lease_owner and item.lease_until:
                try:
                    if datetime.fromisoformat(item.lease_until) > now:
                        continue
                except ValueError:
                    pass
            candidates.append(item)

        candidates.sort(
            key=lambda x: (
                x.deadline is None,
                x.deadline or "",
                -(x.value or 0.0),
                x.id,
            )
        )
        if not candidates:
            return None

        selected = candidates[0]
        claimed = Opportunity(
            **{
                **selected.__dict__,
                "lease_owner": worker_id,
                "lease_until": (now + timedelta(seconds=ttl_seconds)).isoformat(),
            }
        )
        items[selected.id] = claimed
        store.save(items)
        return claimed


__all__ = ["acquire_next"]
