"""Evidence-backed opportunity-to-worker routing.

This module composes existing opportunity handoff, specialization learning,
and worker health. It owns no parallel opportunity lifecycle.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from foundation.opportunity import OpportunityReceipt, InvestigationMission, handoff
from foundation.specialization import SpecializationBook
from foundation.worker_health import WorkerHealthBook
from foundation.opportunity_feedback import OutcomeFeedback
from foundation.priority_scheduler import OpportunityPriority, prioritize
from foundation.batch_planner import BatchPlan, plan_batch
from foundation.workforce_registry import WorkforceRegistry
from foundation.learning_receipt import LearningReceipt
from foundation.institutional_memory import InstitutionalMemory, InstitutionalMemoryStore


@dataclass(frozen=True)
class WorkerAssignment:
    opportunity_id: str
    worker_id: str
    domain: str
    mission: InvestigationMission


@dataclass(frozen=True)
class AssignmentOutcome:
    opportunity_id: str
    worker_id: str
    domain: str
    outcome: str
    evidence_count: int = 0


def record_assignment_outcome(
    assignment: "WorkerAssignment",
    outcome: str,
    health: WorkerHealthBook,
    specialization: SpecializationBook,
    *,
    evidence_count: int = 0,
) -> AssignmentOutcome:
    """Apply one execution result to live worker health and specialization."""
    if outcome not in {"SUCCESS", "FAILURE"}:
        raise AssignmentRefused("outcome must be SUCCESS or FAILURE")
    if evidence_count < 0:
        raise AssignmentRefused("evidence_count cannot be negative")
    if outcome == "SUCCESS":
        health.record_success(assignment.worker_id)
    else:
        health.record(assignment.worker_id, status="FAILED")
    specialization.record_outcome(
        assignment.worker_id, assignment.domain,
        outcome=outcome, evidence_count=evidence_count)
    return AssignmentOutcome(
        assignment.opportunity_id, assignment.worker_id,
        assignment.domain, outcome, evidence_count)


class AssignmentRefused(ValueError):
    pass


def route_opportunity(
    opportunity: OpportunityReceipt,
    worker_ids: tuple[str, ...],
    domain: str,
    specialization: SpecializationBook,
    health: WorkerHealthBook,
    *,
    next_cheapest_experiment: str,
    what_would_disprove_value: str,
    now: Optional[datetime] = None,
) -> WorkerAssignment:
    """Create one bounded assignment after the existing opportunity gate passes."""
    if not worker_ids:
        raise AssignmentRefused("no workers supplied")
    if not domain.strip():
        raise AssignmentRefused("domain is required")

    mission = handoff(
        opportunity,
        next_cheapest_experiment=next_cheapest_experiment,
        what_would_disprove_value=what_would_disprove_value,
        now=now,
    )
    ranked = specialization.rank_with_health(worker_ids, domain, health)
    if not ranked:
        raise AssignmentRefused("no eligible workers")
    return WorkerAssignment(opportunity.opportunity_id, ranked[0], domain.strip(), mission)


def route_with_learning(
    opportunity: OpportunityReceipt,
    worker_ids: tuple[str, ...],
    domain: str,
    specialization: SpecializationBook,
    health: WorkerHealthBook,
    feedback,
    *,
    expected_value: float,
    next_cheapest_experiment: str,
    what_would_disprove_value: str,
    now: Optional[datetime] = None,
) -> tuple[WorkerAssignment, float]:
    """Rank an opportunity using observed value calibration, then apply the normal evidence gate."""
    adjusted = feedback.adjusted_value(
        opportunity.opportunity_id, expected_value, now=now)
    assignment = route_opportunity(
        opportunity, worker_ids, domain, specialization, health,
        next_cheapest_experiment=next_cheapest_experiment,
        what_would_disprove_value=what_would_disprove_value, now=now)
    return assignment, adjusted


def prioritize_with_learning(
    priorities: tuple[OpportunityPriority, ...],
    feedback,
    *,
    now: Optional[datetime] = None,
) -> tuple[OpportunityPriority, ...]:
    """Re-score known opportunities with observed value calibration before scheduling."""
    adjusted = tuple(
        __import__("dataclasses").replace(
            item,
            expected_value=feedback.adjusted_value(
                item.opportunity_id, item.expected_value, now=now),
        )
        for item in priorities
    )
    return prioritize(adjusted)


def match_opportunity_workers(
    priorities: tuple[OpportunityPriority, ...],
    worker_ids: tuple[str, ...],
    domain: str,
    specialization: SpecializationBook,
    health: WorkerHealthBook,
    feedback,
    *,
    now: Optional[datetime] = None,
) -> tuple[tuple[str, str], ...]:
    """Return deterministic opportunity→worker matches from learned value and skill."""
    ordered = prioritize_with_learning(priorities, feedback, now=now)
    ranked = specialization.rank_with_health(worker_ids, domain, health)
    if not ranked:
        return ()
    return tuple((item.opportunity_id, ranked[i % len(ranked)]) for i, item in enumerate(ordered))


def dispatch_learned_batch(
    registry: WorkforceRegistry,
    health: WorkerHealthBook,
    specialization: SpecializationBook,
    opportunities: tuple[tuple[str, str, set[str]], ...],
    priorities: tuple[OpportunityPriority, ...],
    feedback,
    max_active: int,
    *,
    now: Optional[datetime] = None,
) -> BatchPlan:
    """Plan a bounded batch using learned opportunity ordering and existing swarm controls."""
    ordered = prioritize_with_learning(priorities, feedback, now=now)
    order = {item.opportunity_id: i for i, item in enumerate(ordered)}
    ranked = tuple(sorted(opportunities, key=lambda item: (order.get(item[0], len(order)), item[0])))
    return plan_batch(registry, health, specialization, ranked, max_active)


__all__ = ["WorkerAssignment", "AssignmentOutcome", "AssignmentRefused",
           "route_opportunity", "record_assignment_outcome", "persist_assignment_outcome", "route_with_learning", "prioritize_with_learning", "match_opportunity_workers", "dispatch_learned_batch"]
