"""Concrete bridge from coverage work to the canonical NEXT OpportunityStore.

The store lives in foundation.next_kernel and is the persistence authority.
Coverage work is projected into that existing durable record; no parallel JSON
state is introduced. This adapter only ingests/resumes work. It never grants
authority or commits an action.
"""

from __future__ import annotations

from foundation.coverage_work_queue import CoverageWorkItem
from foundation.next_kernel import Opportunity, OpportunityStore

STATE_MAP = {
    "DISCOVERED": "DISCOVERED",
    "PREPARED": "PREPARED",
    "READY": "READY",
    "COMMITTED": "COMMITTED",
    "OUTCOME": "OUTCOME",
    "RETIRED": "SUCCEEDED",
}


def opportunity_from_work(item: CoverageWorkItem) -> Opportunity:
    return Opportunity(
        id=item.work_id,
        source="coverage_frontier",
        title=(
            f"Coverage gap: {item.gap.opportunity_type} / "
            f"{item.gap.region} / {item.gap.jurisdiction} / "
            f"{item.gap.source_class}"
        ),
        status=STATE_MAP[item.state],
        value=float(item.score),
        evidence_refs=tuple(dict.fromkeys(item.evidence_refs + item.receipt_refs)),
        authority=item.required_authority,
        next_action=item.next_action,
    )


def persist_work(store: OpportunityStore, item: CoverageWorkItem) -> str:
    """Persist a coverage item through the canonical NEXT store."""
    return store.upsert(opportunity_from_work(item))


def recover_actionable(store: OpportunityStore) -> tuple[Opportunity, ...]:
    """Return durable actionable records for swarm resumption."""
    return tuple(store.actionable())


__all__ = ["STATE_MAP", "opportunity_from_work", "persist_work", "recover_actionable"]
