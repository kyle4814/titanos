"""Bounded, fair dispatcher for TitanOS swarm plans."""
from __future__ import annotations
from dataclasses import dataclass
from foundation.swarm_plan import SwarmPlan

@dataclass(frozen=True)
class DispatchBudget:
    max_active: int = 8
    max_per_worker: int = 1
    max_queue: int = 128
    fairness_offset: int = 0
    def __post_init__(self) -> None:
        if self.max_active <= 0 or self.max_per_worker <= 0 or self.max_queue < 0:
            raise ValueError("dispatch limits must be positive and max_queue non-negative")
        if self.fairness_offset < 0:
            raise ValueError("fairness_offset must be non-negative")

@dataclass(frozen=True)
class DispatchItem:
    worker_id: str
    requirement: str
    slot: int

@dataclass(frozen=True)
class DispatchBatch:
    items: tuple[DispatchItem, ...]
    queued: tuple[DispatchItem, ...]
    dropped: tuple[DispatchItem, ...] = ()

def _fair_candidates(plan: SwarmPlan, offset: int) -> list[tuple[str, str]]:
    lanes = [list((a.requirement, wid) for wid in a.worker_ids) for a in plan.assignments]
    out: list[tuple[str, str]] = []
    depth = 0
    while any(depth < len(lane) for lane in lanes):
        for lane in lanes:
            if depth < len(lane):
                out.append(lane[depth])
        depth += 1
    if not out:
        return out
    shift = offset % len(out)
    return out[shift:] + out[:shift]

def dispatch(plan: SwarmPlan, budget: DispatchBudget) -> DispatchBatch:
    items: list[DispatchItem] = []
    queued: list[DispatchItem] = []
    seen: dict[str, int] = {}
    for requirement, worker_id in _fair_candidates(plan, budget.fairness_offset):
        count = seen.get(worker_id, 0)
        seen[worker_id] = count + 1
        target = items if len(items) < budget.max_active and count < budget.max_per_worker else queued
        target.append(DispatchItem(worker_id, requirement, len(items) if target is items else -1))
    dropped = tuple(queued[budget.max_queue:])
    queued = queued[:budget.max_queue]
    active = tuple(DispatchItem(x.worker_id, x.requirement, i) for i, x in enumerate(items))
    return DispatchBatch(active, tuple(queued), dropped)

__all__ = ["DispatchBudget", "DispatchItem", "DispatchBatch", "dispatch"]
