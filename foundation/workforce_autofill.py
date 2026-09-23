"""Automatic bounded dispatcher refill after worker completion."""
from __future__ import annotations
from dataclasses import dataclass
from foundation.workforce_dispatcher import DispatchBatch, DispatchBudget, DispatchItem
from foundation.workforce_refill import refill
from foundation.swarm_state import SwarmState

@dataclass(frozen=True)
class RefillEvent:
    completed_worker: str
    completed_opportunity: str
    promoted: tuple[DispatchItem, ...]
    remaining_queue: tuple[DispatchItem, ...]

def on_worker_finished(batch: DispatchBatch, budget: DispatchBudget,
                       completed_worker: str, completed_opportunity: str) -> tuple[DispatchBatch, RefillEvent]:
    next_plan = refill(batch, budget)
    new_batch = DispatchBatch(next_plan.active, next_plan.queued)
    promoted = tuple(x for x in next_plan.active if x not in batch.items)
    return new_batch, RefillEvent(completed_worker, completed_opportunity, promoted, next_plan.queued)

__all__ = ["RefillEvent", "on_worker_finished"]
