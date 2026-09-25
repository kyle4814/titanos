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
from foundation.institutional_memory import (
    InstitutionalMemory, InstitutionalMemoryStore, StaleMemoryTransition,
)


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


class LearningConflict(RuntimeError):
    """A learning transition kept losing to concurrent writers for
    MAX_LEARNING_ATTEMPTS reloads. Nothing was applied. The caller decides
    whether to try again later; the store's stale-write refusal stands."""


# Bounded, like ConsumedIds.MAX_ATTEMPTS: a conflict is a domain result to
# resolve by reloading, not a reason to spin forever.
MAX_LEARNING_ATTEMPTS = 8


def _persist_learning(store, mutate, actor, mutation, input_evidence, observed_at):
    """load -> mutate -> save, reloading and reapplying on a stale transition.

    `InstitutionalMemoryStore.save()` refuses a receipt whose `before` is no
    longer the persisted state, and does so before any durable write, so a
    refused attempt applied nothing and can be rebuilt from the latest
    state. Each attempt mints a fresh receipt bound to the state it actually
    saw; a concurrent learner's outcome is therefore never overwritten and
    ours is never lost or applied twice. Any other store error propagates
    unchanged on the first attempt."""
    last: Optional[StaleMemoryTransition] = None
    for _ in range(MAX_LEARNING_ATTEMPTS):
        memory = store.load()
        before = store._payload(memory)
        result = mutate(memory)
        after = store._payload(memory)
        receipt = LearningReceipt.create(actor, mutation, input_evidence, before, after,
                                         observed_at=observed_at)
        try:
            store.save(memory, receipt)
        except StaleMemoryTransition as exc:
            last = exc
            continue
        return result
    raise LearningConflict(
        f"{mutation} for {actor} lost to concurrent writers {MAX_LEARNING_ATTEMPTS} times; "
        "nothing was applied") from last


def persist_assignment_outcome(
    store: InstitutionalMemoryStore,
    assignment: WorkerAssignment,
    outcome: str,
    *,
    evidence_count: int = 0,
    observed_at: Optional[str] = None,
) -> AssignmentOutcome:
    """Apply an assignment outcome and persist the transition with a learning receipt."""
    return _persist_learning(
        store,
        lambda memory: record_assignment_outcome(
            assignment, outcome, memory.worker_health, memory.specialization,
            evidence_count=evidence_count,
        ),
        assignment.worker_id,
        "assignment_outcome",
        (assignment.opportunity_id, assignment.domain, outcome),
        observed_at,
    )


def persist_opportunity_outcome(
    store: InstitutionalMemoryStore,
    opportunity_id: str,
    expected_value: float,
    realized_value: float,
    completed: bool,
    evidence_strength: float = 0.0,
    *,
    observed_at: Optional[str] = None,
) -> OutcomeFeedback:
    """Persist outcome feedback as a receipt-bound institutional-memory transition."""
    feedback = OutcomeFeedback(
        opportunity_id, expected_value, realized_value, completed,
        evidence_strength, observed_at,
    )

    def mutate(memory):
        memory.opportunity_learning.record(feedback)
        return feedback

    return _persist_learning(
        store, mutate,
        "opportunity:" + opportunity_id,
        "opportunity_outcome",
        (opportunity_id, str(expected_value), str(realized_value), str(completed)),
        observed_at,
    )


def plan_from_persisted_learning(
    store: InstitutionalMemoryStore,
    registry: WorkforceRegistry,
    health: WorkerHealthBook,
    specialization: SpecializationBook,
    opportunities: tuple[tuple[str, str, set[str]], ...],
    priorities: tuple[OpportunityPriority, ...],
    max_active: int,
    *,
    now: Optional[datetime] = None,
) -> BatchPlan:
    """Reload institutional memory, recalibrate priorities, and build the next bounded batch."""
    memory = store.load()
    learned = prioritize_with_learning(priorities, memory.opportunity_learning, now=now)
    order = {item.opportunity_id: i for i, item in enumerate(learned)}
    ranked = tuple(sorted(
        opportunities,
        key=lambda item: (order.get(item[0], len(order)), item[0]),
    ))
    return plan_batch(registry, health, specialization, ranked, max_active)


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


def select_retry_worker(
    failed_worker_id: str,
    worker_ids: tuple[str, ...],
    domain: str,
    specialization: SpecializationBook,
    health: WorkerHealthBook,
) -> str:
    """Select the best healthy alternative specialist for a retry."""
    alternatives = tuple(w for w in worker_ids if w != failed_worker_id)
    ranked = specialization.rank_with_health(alternatives, domain, health)
    if not ranked:
        raise AssignmentRefused("no healthy alternative worker")
    return ranked[0]


__all__ = ["WorkerAssignment", "AssignmentOutcome", "AssignmentRefused",
           "LearningConflict", "MAX_LEARNING_ATTEMPTS",
           "route_opportunity", "record_assignment_outcome", "persist_assignment_outcome", "persist_opportunity_outcome", "plan_from_persisted_learning", "route_with_learning", "prioritize_with_learning", "match_opportunity_workers", "dispatch_learned_batch", "select_retry_worker"]
