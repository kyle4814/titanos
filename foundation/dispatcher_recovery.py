"""Reconcile dispatcher execution state against canonical NEXT leases."""
from __future__ import annotations
from dataclasses import replace
from foundation.next_kernel import OpportunityStore
from foundation.dispatcher_state import DispatcherState, DispatcherStateStore

def reconcile_dispatcher(store: OpportunityStore, dispatcher_store: DispatcherStateStore,
                         state: DispatcherState) -> DispatcherState:
    """Drop stale active entries and prevent duplicate queued/active identities."""
    canonical_active = []
    for opportunity_id in state.active:
        try:
            item = store.load()[opportunity_id]
        except KeyError:
            continue
        if item.lease_owner:
            canonical_active.append(opportunity_id)

    active = tuple(dict.fromkeys(canonical_active))
    active_set = set(active)
    queued = tuple(dict.fromkeys(x for x in state.queued if x not in active_set))
    completed = tuple(dict.fromkeys(x for x in state.completed if x not in active_set))
    failed = tuple(dict.fromkeys(x for x in state.failed if x not in active_set))
    repaired = replace(state, active=active, queued=queued, completed=completed, failed=failed)
    dispatcher_store.save(repaired)
    return repaired

__all__=["reconcile_dispatcher"]
