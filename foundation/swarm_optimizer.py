"""Health-aware swarm planning.

Uses observed worker health only as a scheduling signal; capability and
authority constraints remain mandatory.
"""
from __future__ import annotations
from dataclasses import replace
from foundation.swarm_plan import SwarmPlan, SwarmAssignment
from foundation.worker_health import WorkerHealthBook
from foundation.workforce_registry import WorkforceRegistry

def optimize_plan(plan: SwarmPlan, registry: WorkforceRegistry,
                  health: WorkerHealthBook) -> SwarmPlan:
    assignments=[]
    for a in plan.assignments:
        ranked=health.rank(a.worker_ids)
        assignments.append(SwarmAssignment(a.requirement, ranked))
    return SwarmPlan(tuple(assignments))

__all__=["optimize_plan"]
