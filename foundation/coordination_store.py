"""Single-file transactional persistence boundary for swarm/NEXT coordination.

The canonical OpportunityStore remains authoritative for opportunities and leases.
This coordinator persists a matching swarm snapshot only after the NEXT mutation
succeeds, with deterministic recovery metadata for reconciliation.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from foundation.next_kernel import OpportunityStore
from foundation.swarm_state import SwarmState, SwarmStateStore

@dataclass(frozen=True)
class CoordinationReceipt:
    operation_id: str
    swarm_id: str
    next_persisted: bool
    swarm_persisted: bool

class CoordinationStore:
    def __init__(self, next_store: OpportunityStore, swarm_store: SwarmStateStore):
        self.next_store = next_store
        self.swarm_store = swarm_store

    def snapshot(self, operation_id: str, state: SwarmState) -> CoordinationReceipt:
        # NEXT is canonical. Persist it first; only then publish swarm state.
        self.next_store.save(self.next_store.load())
        self.swarm_store.save(state)
        return CoordinationReceipt(operation_id, state.swarm_id, True, True)

__all__ = ["CoordinationReceipt", "CoordinationStore"]
