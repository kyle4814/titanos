"""Transactional worker transition facade.

Coordinates canonical NEXT lease transitions with persistent swarm state.
The canonical opportunity record remains authoritative; swarm state is a
derived execution view.
"""
from __future__ import annotations
from dataclasses import replace
from foundation.coordination_journal import CrashRecoverableCoordinator
from foundation.next_kernel import OpportunityStore
from foundation.next_leases import claim, release
from foundation.swarm_state import SwarmState
from foundation.worker_result import WorkerResult
from foundation.authority_result import apply_worker_result

def start_worker(store: OpportunityStore, coordinator: CrashRecoverableCoordinator,
                 state: SwarmState, opportunity_id: str, worker_id: str) -> SwarmState:
    claim(store, opportunity_id, worker_id)
    active = tuple(dict.fromkeys((*state.active, opportunity_id)))
    queued = tuple(x for x in state.queued if x != opportunity_id)
    new_state = replace(state, active=active, queued=queued)
    coordinator.commit(f"start:{opportunity_id}:{worker_id}", new_state)
    return new_state

def finish_worker(store: OpportunityStore, coordinator: CrashRecoverableCoordinator,
                  state: SwarmState, result: WorkerResult) -> SwarmState:
    item = store.load()[result.opportunity_id]
    if item.lease_owner != result.worker_id:
        raise PermissionError("worker does not own lease")
    if result.status == "COMPLETED" and not result.evidence_refs:
        raise ValueError("completed work requires evidence")
    apply_worker_result(store, result)
    release(store, result.opportunity_id, result.worker_id)
    active = tuple(x for x in state.active if x != result.opportunity_id)
    completed = tuple(dict.fromkeys((*state.completed, result.opportunity_id))) if result.status == "COMPLETED" else state.completed
    failed = tuple(dict.fromkeys((*state.failed, result.opportunity_id))) if result.status == "FAILED" else state.failed
    new_state = replace(state, active=active, completed=completed, failed=failed)
    coordinator.commit(f"finish:{result.opportunity_id}:{result.worker_id}", new_state)
    return new_state

__all__ = ["start_worker", "finish_worker"]
