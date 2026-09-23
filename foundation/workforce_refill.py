"""Deterministic refill planner for bounded TitanOS worker pools."""
from __future__ import annotations
from dataclasses import dataclass
from foundation.workforce_dispatcher import DispatchBudget, DispatchBatch, DispatchItem

@dataclass(frozen=True)
class RefillPlan:
    active: tuple[DispatchItem, ...]
    queued: tuple[DispatchItem, ...]
    available_slots: int

def refill(batch: DispatchBatch, budget: DispatchBudget) -> RefillPlan:
    slots = max(0, budget.max_active - len(batch.items))
    promoted = batch.queued[:slots]
    remaining = batch.queued[slots:]
    active = tuple(DispatchItem(x.worker_id, x.requirement, i) for i, x in enumerate((*batch.items, *promoted)))
    return RefillPlan(active, remaining, max(0, budget.max_active - len(active)))

__all__ = ["RefillPlan", "refill"]
