"""Bridge coverage work items into TitanOS's existing Opportunity/Receipt model.

No second opportunity lifecycle is introduced. This module translates the
coverage queue's work state into the repository's established queue semantics
and requires receipts before an engineering outcome can be recorded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from foundation.coverage_work_queue import CoverageWorkItem
from foundation.opportunity import QUEUE_STATES
from foundation.receipt import Receipt


WORK_TO_OPPORTUNITY_STATE: Final[dict[str, str]] = {
    "DISCOVERED": "DISCOVERED",
    "PREPARED": "ROUTED",
    "READY": "READY_FOR_INVESTIGATION",
    "COMMITTED": "INVESTIGATING",
    "OUTCOME": "QUALIFIED",
    "RETIRED": "RETIRED",
}


@dataclass(frozen=True)
class CoverageOutcome:
    work_id: str
    opportunity_state: str
    receipt_refs: tuple[str, ...]
    outcome_recorded: bool = False

    def __post_init__(self) -> None:
        if self.opportunity_state not in QUEUE_STATES:
            raise ValueError(f"invalid opportunity state: {self.opportunity_state}")

    def to_dict(self) -> dict[str, object]:
        return {
            "work_id": self.work_id,
            "opportunity_state": self.opportunity_state,
            "receipt_refs": self.receipt_refs,
            "outcome_recorded": self.outcome_recorded,
        }


def project_state(work: CoverageWorkItem) -> str:
    return WORK_TO_OPPORTUNITY_STATE[work.state]


def record_outcome(work: CoverageWorkItem, receipt: Receipt) -> CoverageOutcome:
    """Record an outcome only when a receipt exists.

    The receipt is the evidence artifact; this function never manufactures one.
    """
    if work.state != "OUTCOME":
        raise ValueError("work item must be in OUTCOME state")
    if not getattr(receipt, "receipt_id", None):
        raise ValueError("outcome requires a persisted receipt id")
    return CoverageOutcome(
        work_id=work.work_id,
        opportunity_state=project_state(work),
        receipt_refs=tuple(dict.fromkeys(work.receipt_refs + (receipt.receipt_id,))),
        outcome_recorded=True,
    )


__all__ = ["WORK_TO_OPPORTUNITY_STATE", "CoverageOutcome", "project_state", "record_outcome"]
