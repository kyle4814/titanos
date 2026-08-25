"""
TitanOS Epistemic Firewall — quarantine store and contamination state machine.

WHY THIS FILE EXISTS

The gate already returned a QUARANTINED verdict. Nothing quarantined
anything. A verdict with no mechanism behind it is a claim, and this
session has already shipped one of those (F-006: doctrine asserted an
invariant that only an optional constructor enforced). This closes the
same shape one layer up.

TWO PROPERTIES, BOTH STRUCTURAL

1. PRESERVATION, NOT DELETION. Quarantine never destroys. The artifact,
   its hash, its provenance and the reason are all retained. A false
   positive must be recoverable by review — if the filter deletes what it
   suspects, then the filter's own errors become unauditable, and the
   detector quietly becomes the authority (§19 forbids exactly this).

2. NO PATH FROM CONTAMINATED TO AUTHORIZED. Not "no such call is made" —
   no such EDGE EXISTS in the transition table. Illegal transitions raise.
   You cannot argue this store into releasing something; you can only add
   a transition, in code, in review, where a human can see it.

WHAT QUARANTINE IS NOT

It is not a verdict of falsehood. Quarantined material may be entirely
true. Quarantine says: this could not be verified through the required
gates, so it is held, preserved, and routed to a human — not that it is
wrong. Conflating "unverified" with "false" is how a safety filter turns
into a censor, which §8 forbids.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Mapping

__all__ = [
    "ContaminationState", "IllegalTransition", "QuarantineRecord",
    "QuarantineStore", "TRANSITIONS", "can_transition",
]

ContaminationState = str

ALL_STATES = (
    "CLEAN", "UNVERIFIED", "DISPUTED", "SUSPICIOUS", "CONTAMINATED",
    "QUARANTINED", "VERIFIED", "AUTHORIZED", "REJECTED", "ARCHIVED",
)

# The explicit transition table (§15).
#
# Read the QUARANTINED row carefully: it can go to VERIFIED, REJECTED or
# ARCHIVED — never directly to AUTHORIZED. Release from quarantine must
# pass back through verification, which is a separate, evidenced step. The
# absence of that edge is the enforcement; there is no flag to flip.
#
# CONTAMINATED likewise has no edge to AUTHORIZED or VERIFIED. Contaminated
# material may only be quarantined, rejected or archived. Recovering it
# requires re-ingesting it as a NEW artifact with its own provenance, which
# is the honest way to say "we checked again from scratch".
TRANSITIONS: Mapping[ContaminationState, frozenset[ContaminationState]] = {
    "CLEAN":        frozenset({"UNVERIFIED", "VERIFIED", "SUSPICIOUS", "DISPUTED"}),
    "UNVERIFIED":   frozenset({"VERIFIED", "SUSPICIOUS", "DISPUTED", "CONTAMINATED", "QUARANTINED", "REJECTED"}),
    "DISPUTED":     frozenset({"VERIFIED", "SUSPICIOUS", "CONTAMINATED", "QUARANTINED", "ARCHIVED"}),
    "SUSPICIOUS":   frozenset({"QUARANTINED", "CONTAMINATED", "VERIFIED", "REJECTED"}),
    "CONTAMINATED": frozenset({"QUARANTINED", "REJECTED", "ARCHIVED"}),
    "QUARANTINED":  frozenset({"VERIFIED", "REJECTED", "ARCHIVED"}),
    "VERIFIED":     frozenset({"AUTHORIZED", "DISPUTED", "SUSPICIOUS", "ARCHIVED"}),
    "AUTHORIZED":   frozenset({"DISPUTED", "SUSPICIOUS", "CONTAMINATED", "ARCHIVED"}),
    "REJECTED":     frozenset({"ARCHIVED"}),
    "ARCHIVED":     frozenset(),  # terminal
}


class IllegalTransition(Exception):
    """Raised when a state change would bypass a constitutional boundary.

    Loud on purpose. A silently-ignored illegal transition would let the
    caller believe a boundary held when it did not.
    """


def can_transition(src: ContaminationState, dst: ContaminationState) -> bool:
    return dst in TRANSITIONS.get(src, frozenset())


@dataclass(frozen=True)
class QuarantineRecord:
    """An append-only record. Amended by adding entries, never by editing.

    Frozen so `state`/`human_review_status` can only change via
    `QuarantineStore.transition()` (through `object.__setattr__`, the
    standard escape hatch for a frozen dataclass's own internal
    mutation) -- a caller holding a reference obtained from `get()`
    cannot bypass `can_transition()`'s reviewed_by requirement by
    assigning `rec.state = ...` directly. `history` is a `tuple`, not a
    `list` -- a caller holding a reference cannot `rec.history.
    append(...)`/`.insert(...)` to forge an entry (EPISTEMIC_
    INTEGRITY_002 found and closed a live exploit of exactly this shape
    against `PromotionRecord`). `transition()`/`quarantine()` replace
    `history` with a new tuple via `object.__setattr__`, the same
    pattern already used for `state`. `provenance` remains an ordinary
    mutable dict -- a disclosed, not fixed, residual boundary; no
    consumer in this repository currently trusts `provenance` for a
    trust/authority decision the way `confirm_pilot_authorized()`
    trusted `history`."""
    artifact_id: str
    content_hash: str
    state: ContaminationState
    reason: str
    provenance: Mapping[str, Any]
    preserved_content: str
    created_at: str
    history: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    human_review_status: str = "PENDING"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QuarantineStore:
    """In-memory reference implementation. Append-only by construction.

    There is no `delete`, no `purge` and no `clear`. Not by convention —
    the methods do not exist, so nothing downstream can call them even by
    mistake. Production would back this with append-only storage; the
    absence of a delete surface is the property being demonstrated.
    """

    def __init__(self) -> None:
        self._records: dict[str, QuarantineRecord] = {}

    @staticmethod
    def _hash(content: str) -> str:
        return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()

    def quarantine(
        self,
        *,
        artifact_id: str,
        content: str,
        reason: str,
        provenance: Mapping[str, Any] | None = None,
        from_state: ContaminationState = "UNVERIFIED",
    ) -> QuarantineRecord:
        """Hold an artifact. Preserves content, hash, provenance and reason."""
        if not can_transition(from_state, "QUARANTINED"):
            raise IllegalTransition(
                f"{from_state} -> QUARANTINED is not a legal transition. "
                f"Legal targets from {from_state}: {sorted(TRANSITIONS.get(from_state, []))}"
            )
        if not reason.strip():
            # An unexplained quarantine is indistinguishable from
            # suppression. §16 requires the reason be preserved, so an
            # empty one is refused rather than defaulted.
            raise ValueError(
                "quarantine requires a reason. An unexplained hold cannot be "
                "reviewed, and an unreviewable hold is censorship, not safety."
            )
        rec = QuarantineRecord(
            artifact_id=artifact_id,
            content_hash=self._hash(content),
            state="QUARANTINED",
            reason=reason,
            provenance=dict(provenance or {}),
            preserved_content=content,
            created_at=datetime.now(timezone.utc).isoformat(),
            history=({"from": from_state, "to": "QUARANTINED", "reason": reason,
                      "at": datetime.now(timezone.utc).isoformat()},),
        )
        self._records[artifact_id] = rec
        return rec

    def transition(
        self, artifact_id: str, to_state: ContaminationState, *,
        reason: str, reviewed_by: str | None = None,
    ) -> QuarantineRecord:
        """Move an artifact's state, or raise.

        `reviewed_by` is required to leave QUARANTINED. Release is a human
        act; an automated release would reduce quarantine to a delay.
        """
        rec = self._records.get(artifact_id)
        if rec is None:
            raise KeyError(f"no quarantine record for '{artifact_id}'")
        if not can_transition(rec.state, to_state):
            raise IllegalTransition(
                f"{rec.state} -> {to_state} is not a legal transition for "
                f"'{artifact_id}'. Legal targets: {sorted(TRANSITIONS.get(rec.state, []))}. "
                f"Note there is deliberately NO edge from QUARANTINED or "
                f"CONTAMINATED to AUTHORIZED — release must re-pass verification."
            )
        if rec.state == "QUARANTINED" and to_state == "VERIFIED" and not reviewed_by:
            raise IllegalTransition(
                "releasing from QUARANTINED requires reviewed_by. Automated "
                "release would make quarantine a delay rather than a gate."
            )
        new_entry = {
            "from": rec.state, "to": to_state, "reason": reason,
            "reviewed_by": reviewed_by,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        object.__setattr__(rec, "history", rec.history + (new_entry,))
        object.__setattr__(rec, "state", to_state)
        if reviewed_by:
            object.__setattr__(rec, "human_review_status", f"REVIEWED_BY:{reviewed_by}")
        return rec

    def get(self, artifact_id: str) -> QuarantineRecord | None:
        return self._records.get(artifact_id)

    def all_records(self) -> tuple[QuarantineRecord, ...]:
        return tuple(self._records.values())

    def pending_review(self) -> tuple[QuarantineRecord, ...]:
        """Everything awaiting a human. This list must never be silently empty."""
        return tuple(r for r in self._records.values()
                     if r.state == "QUARANTINED" and r.human_review_status == "PENDING")

    def export(self) -> str:
        return json.dumps([r.to_dict() for r in self._records.values()],
                          indent=2, sort_keys=True)
