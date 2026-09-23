"""Restart/crash reconciliation for persistent TitanOS swarms."""
from __future__ import annotations

from dataclasses import replace
from foundation.next_kernel import OpportunityStore
from foundation.next_leases import recover_expired
from foundation.swarm_state import SwarmState, SwarmStateStore

def reconcile_swarm(store: OpportunityStore, swarm_store: SwarmStateStore,
                    state: SwarmState, *, now=None) -> SwarmState:
    """Return expired active work to the queue and persist the repaired state."""
    recover_expired(store, now=now)
    recovered_ids = {o.opportunity_id for o in recover_expired(store, now=now)}
    if not recovered_ids:
        return state
    active = tuple(x for x in state.active if x not in recovered_ids)
    queued = tuple(dict.fromkeys((*state.queued, *recovered_ids)))
    repaired = replace(state, active=active, queued=queued)
    swarm_store.save(repaired)
    return repaired

__all__ = ["reconcile_swarm"]
