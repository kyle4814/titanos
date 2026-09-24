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


@dataclass(frozen=True)
class WorkerAssignment:
    opportunity_id: str
    worker_id: str
    domain: str
    mission: InvestigationMission


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


__all__ = ["WorkerAssignment", "AssignmentRefused", "route_opportunity"]
