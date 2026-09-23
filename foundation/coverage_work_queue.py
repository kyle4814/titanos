"""Persistent-shaped engineering queue for closing opportunity coverage gaps.

This is intentionally a small contract layer over GapPlan. It does not
execute work or grant authority. Agents may prepare/verify queue items;
commit/production actions remain explicitly human-controlled.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final

from foundation.opportunity_coverage_gaps import CoverageGap
from foundation.opportunity_gap_planner import GapPlan

WORK_STATES: Final[tuple[str, ...]] = (
    "DISCOVERED", "PREPARED", "READY", "COMMITTED", "OUTCOME", "RETIRED",
)

STATE_AUTHORITY: Final[dict[str, str]] = {
    "DISCOVERED": "O0",
    "PREPARED": "O1",
    "READY": "O2",
    "COMMITTED": "O3",
    "OUTCOME": "O3",
    "RETIRED": "O2",
}


@dataclass(frozen=True)
class CoverageWorkItem:
    work_id: str
    gap: CoverageGap
    score: int
    state: str = "DISCOVERED"
    owner: str = "unassigned"
    next_action: str = "triage"
    evidence_refs: tuple[str, ...] = ()
    receipt_refs: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    controlling_party: str = "system"

    def __post_init__(self) -> None:
        if self.state not in WORK_STATES:
            raise ValueError(f"invalid work state: {self.state}")
        if not self.work_id.strip():
            raise ValueError("work_id is required")

    @property
    def required_authority(self) -> str:
        return STATE_AUTHORITY[self.state]

    def transition(self, state: str, *, controlling_party: str) -> "CoverageWorkItem":
        if state not in WORK_STATES:
            raise ValueError(f"invalid work state: {state}")
        if state in {"COMMITTED", "OUTCOME"} and controlling_party != "human":
            raise PermissionError(
                f"{state} requires explicit human controlling party")
        return replace(self, state=state, controlling_party=controlling_party)

    def add_evidence(self, *refs: str) -> "CoverageWorkItem":
        return replace(self, evidence_refs=tuple(dict.fromkeys(
            self.evidence_refs + tuple(r for r in refs if r)
        )))

    def add_receipt(self, *refs: str) -> "CoverageWorkItem":
        return replace(self, receipt_refs=tuple(dict.fromkeys(
            self.receipt_refs + tuple(r for r in refs if r)
        )))


def work_item_from_plan(plan: GapPlan, *, work_id: str) -> CoverageWorkItem:
    return CoverageWorkItem(
        work_id=work_id,
        gap=plan.gap,
        score=plan.score,
        next_action="reuse existing adapter" if plan.reusable_adapters else "discover adapter",
        blockers=plan.blockers,
    )


__all__ = ["WORK_STATES", "STATE_AUTHORITY", "CoverageWorkItem", "work_item_from_plan"]
