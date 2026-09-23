"""Feedback-aware opportunity priority scheduling."""
from __future__ import annotations
from dataclasses import replace
from foundation.priority_scheduler import OpportunityPriority, prioritize, plan_prioritized
from foundation.opportunity_feedback import OpportunityFeedbackBook
from foundation.batch_planner import BatchPlan
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry

def recalibrate(items: tuple[OpportunityPriority, ...],
                feedback: OpportunityFeedbackBook) -> tuple[OpportunityPriority, ...]:
    adjusted=[]
    for x in items:
        adjusted.append(replace(x, expected_value=feedback.adjusted_value(x.opportunity_id,x.expected_value)))
    return prioritize(tuple(adjusted))

def plan_with_feedback(registry: WorkforceRegistry, health: WorkerHealthBook,
                       specialization: SpecializationBook,
                       opportunities: tuple[tuple[str,str,set[str]], ...],
                       priorities: tuple[OpportunityPriority, ...],
                       feedback: OpportunityFeedbackBook,
                       max_active: int) -> BatchPlan:
    return plan_prioritized(registry,health,specialization,opportunities,
                             recalibrate(priorities,feedback),max_active)

__all__=["recalibrate","plan_with_feedback"]
