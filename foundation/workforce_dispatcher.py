"""Bounded dispatcher for TitanOS swarm plans.

The dispatcher allocates logical work to a finite execution budget. It does
not invoke a model itself; an adapter such as Claude Code consumes the returned
dispatch batch and reports structured results.
"""
from __future__ import annotations

from dataclasses import dataclass
from foundation.swarm_plan import SwarmPlan
from foundation.worker_execution_contract import WorkerExecutionContract

@dataclass(frozen=True)
class DispatchBudget:
    max_active: int = 8
    max_per_worker: int = 1
    def __post_init__(self) -> None:
        if self.max_active <= 0 or self.max_per_worker <= 0:
            raise ValueError("dispatch limits must be positive")

@dataclass(frozen=True)
class DispatchItem:
    worker_id: str
    requirement: str
    slot: int

@dataclass(frozen=True)
class DispatchBatch:
    items: tuple[DispatchItem, ...]
    queued: tuple[DispatchItem, ...]

def dispatch(plan: SwarmPlan, budget: DispatchBudget) -> DispatchBatch:
    items: list[DispatchItem] = []
    queued: list[DispatchItem] = []
    seen: dict[str, int] = {}
    for assignment in plan.assignments:
        for worker_id in assignment.worker_ids:
            count = seen.get(worker_id, 0)
            seen[worker_id] = count + 1
            target = items if len(items) < budget.max_active and count < budget.max_per_worker else queued
            target.append(DispatchItem(worker_id, assignment.requirement, len(items) if target is items else -1))
    # Re-number active slots deterministically.
    active = tuple(DispatchItem(x.worker_id, x.requirement, i) for i, x in enumerate(items))
    return DispatchBatch(active, tuple(queued))

__all__ = ["DispatchBudget", "DispatchItem", "DispatchBatch", "dispatch"]
