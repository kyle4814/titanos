"""
KPM — blueprint promotion state machine (§VII).

WHY THIS FILE EXISTS

A blueprint that only ever passes through its author's own hands before
being marked STABLE has not been reviewed — it has been rubber-stamped by
the one person structurally incapable of catching their own blind spots.
§VII of the governing directive states this as a rule. This module is
what makes the rule true of the running system rather than true of the
prose describing it: the same F-006 shape the firewall closes for
quarantine (a stated invariant with no mechanism behind it) recurs here
for promotion, and gets closed the same way.

TWO PROPERTIES, MIRRORING firewall/quarantine.py EXACTLY

1. NO PATH TO STABLE EXCEPT THROUGH A GATE THAT CAN REFUSE. The transition
   table has exactly two edges into STABLE: TESTED -> STABLE and
   HUMAN_REVIEW -> STABLE. RAW, DISTILLED, PROVISIONAL, CONTESTED and
   QUARANTINED have no such edge — not "callers are expected not to", but
   the edge is absent from the table, so `can_transition` returns False
   and `promote()` raises before anything else happens. You cannot argue
   this store into skipping a step; you can only add an edge, in code, in
   review, where a human can see it.

2. THE PRODUCER IS NOT THE PROMOTER. Even where an edge to STABLE exists,
   crossing it requires `reviewed_by`, and `reviewed_by` must differ from
   `created_by`. This is not merely "review happened" (the quarantine
   store's bar) — it is "review happened, and it was not the author
   reviewing themselves". A blueprint's own creator can move it through
   RAW -> DISTILLED -> PROVISIONAL -> TESTED alone; the moment TESTED (or
   HUMAN_REVIEW) targets STABLE, `SelfPromotionForbidden` fires if the
   reviewer and the creator are the same name. Nothing about the shape of
   the call — passing `reviewed_by=created_by` — gets around this, because
   the check compares values, not presence.

WHAT PROMOTION IS NOT

STABLE is not a claim of permanent correctness. STABLE can still move to
DEPRECATED (superseded by newer understanding) or SUPERSEDED (replaced by
a specific successor blueprint) — both terminal, because "deprecated" and
"superseded" are historical facts about a blueprint's lifecycle, not
states you revive by editing the record. CONTESTED and QUARANTINED are
likewise not verdicts of falsehood; they are holds, and the only way out
of either is HUMAN_REVIEW — mirroring quarantine.py's refusal to let a
disputed or suspicious artifact talk its way back to AUTHORIZED without
a human in the loop.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Mapping

__all__ = [
    "PromotionState", "IllegalTransition", "SelfPromotionForbidden",
    "PromotionRecord", "PromotionStore", "TRANSITIONS", "can_transition",
]

PromotionState = str

ALL_STATES = (
    "RAW", "DISTILLED", "PROVISIONAL", "TESTED", "CONTESTED",
    "QUARANTINED", "HUMAN_REVIEW", "STABLE", "DEPRECATED", "SUPERSEDED",
)

# The explicit transition table (§VII / §15).
#
# Read the STABLE edges carefully: exactly two transitions target STABLE
# — TESTED -> STABLE and HUMAN_REVIEW -> STABLE. RAW, DISTILLED,
# PROVISIONAL, CONTESTED and QUARANTINED have no edge to STABLE at all.
# That absence is the enforcement; `can_transition()` consults nothing
# else, and there is no runtime flag that routes around it.
#
# CONTESTED and QUARANTINED both funnel to HUMAN_REVIEW only. Neither can
# resolve itself back onto the forward path — a human must look at it and
# decide TESTED (cleared), STABLE (cleared and ready), QUARANTINED (still
# held) or DEPRECATED (abandoned).
TRANSITIONS: Mapping[PromotionState, frozenset[PromotionState]] = {
    "RAW":          frozenset({"DISTILLED", "QUARANTINED"}),
    "DISTILLED":    frozenset({"PROVISIONAL", "CONTESTED", "QUARANTINED"}),
    "PROVISIONAL":  frozenset({"TESTED", "CONTESTED", "QUARANTINED"}),
    "TESTED":       frozenset({"STABLE", "CONTESTED", "QUARANTINED"}),
    "CONTESTED":    frozenset({"HUMAN_REVIEW"}),
    "QUARANTINED":  frozenset({"HUMAN_REVIEW"}),
    "HUMAN_REVIEW": frozenset({"TESTED", "STABLE", "QUARANTINED", "DEPRECATED"}),
    "STABLE":       frozenset({"DEPRECATED", "SUPERSEDED"}),
    "DEPRECATED":   frozenset(),  # terminal
    "SUPERSEDED":   frozenset(),  # terminal
}


class IllegalTransition(Exception):
    """Raised when a state change would use an edge absent from TRANSITIONS.

    Loud on purpose, matching firewall/quarantine.py — a silently-ignored
    illegal transition would let the caller believe a boundary held when
    it did not.
    """


class SelfPromotionForbidden(IllegalTransition):
    """Raised when a blueprint's own creator attempts to promote it to STABLE.

    This is distinct from a missing `reviewed_by` (which is simply an
    illegal transition per the missing-review rule below): here a review
    name IS present, it is just the same name as the creator's. §VII
    requires a second, independent human — not a second signature from
    the first one.
    """


def can_transition(src: PromotionState, dst: PromotionState) -> bool:
    return dst in TRANSITIONS.get(src, frozenset())


@dataclass(frozen=True)
class PromotionRecord:
    """An append-only record. Amended by adding history entries, never by editing.

    Frozen so `state` can only change via `PromotionStore.promote()`
    (through `object.__setattr__`, the standard escape hatch for a
    frozen dataclass's own internal mutation) -- a caller holding a
    reference obtained from `get()` cannot bypass `can_transition()`/
    `SelfPromotionForbidden` by assigning `rec.state = ...` directly.
    `history` remains an ordinary mutable list; appending to it does not
    reassign the attribute, so it stays legal under freezing."""
    blueprint_id: str
    state: PromotionState
    created_by: str
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PromotionStore:
    """In-memory reference implementation. Append-only by construction.

    There is no `delete`, no `purge`, no `clear` and no `remove` method.
    Not by convention — the methods do not exist, so nothing downstream
    can call them even by mistake, mirroring QuarantineStore.
    """

    def __init__(self) -> None:
        self._records: dict[str, PromotionRecord] = {}

    def register(self, blueprint_id: str, *, created_by: str,
                 state: PromotionState = "RAW") -> PromotionRecord:
        """Register a new blueprint at its initial state (default RAW)."""
        if blueprint_id in self._records:
            raise ValueError(f"blueprint '{blueprint_id}' is already registered")
        rec = PromotionRecord(
            blueprint_id=blueprint_id, state=state, created_by=created_by,
            history=[{"from": None, "to": state, "reason": "registered",
                      "reviewed_by": None,
                      "at": datetime.now(timezone.utc).isoformat()}],
        )
        self._records[blueprint_id] = rec
        return rec

    def promote(
        self, blueprint_id: str, to_state: PromotionState, *,
        reason: str, reviewed_by: str | None = None,
        created_by: str | None = None,
    ) -> PromotionRecord:
        """Move a blueprint's state, or raise.

        `created_by` may be omitted if the blueprint is already registered
        (it is then read from the record); passing a conflicting value is
        an error, since the creator of a blueprint is a fact, not a
        per-call parameter to be overridden.

        Transitioning INTO STABLE requires `reviewed_by`, and
        `reviewed_by` must differ from the blueprint's `created_by` — the
        producer must not be the final promoter (§VII). This is checked
        by value, not by presence: setting `reviewed_by` to your own name
        does not satisfy it.
        """
        rec = self._records.get(blueprint_id)
        if rec is None:
            if created_by is None:
                raise KeyError(
                    f"no promotion record for '{blueprint_id}'; register() it "
                    f"first or pass created_by to promote() to auto-register."
                )
            rec = self.register(blueprint_id, created_by=created_by, state="RAW")
        elif created_by is not None and created_by != rec.created_by:
            raise ValueError(
                f"'{blueprint_id}' was created_by='{rec.created_by}'; "
                f"cannot override to '{created_by}'."
            )

        if not can_transition(rec.state, to_state):
            raise IllegalTransition(
                f"{rec.state} -> {to_state} is not a legal transition for "
                f"'{blueprint_id}'. Legal targets: {sorted(TRANSITIONS.get(rec.state, []))}. "
                f"Note there is deliberately no edge from RAW, DISTILLED, "
                f"PROVISIONAL, CONTESTED or QUARANTINED to STABLE — only "
                f"TESTED -> STABLE and HUMAN_REVIEW -> STABLE exist."
            )

        if to_state == "STABLE":
            if not reason.strip():
                raise ValueError(
                    "promotion to STABLE requires a reason. An unexplained "
                    "promotion cannot be audited."
                )
            if not reviewed_by:
                raise IllegalTransition(
                    "promotion to STABLE requires reviewed_by. Automated "
                    "promotion would make review theatre rather than a gate."
                )
            if reviewed_by == rec.created_by:
                raise SelfPromotionForbidden(
                    f"'{blueprint_id}' cannot be self-promoted to STABLE: "
                    f"reviewed_by ('{reviewed_by}') is the same as created_by "
                    f"('{rec.created_by}'). §VII requires an independent reviewer."
                )

        rec.history.append({
            "from": rec.state, "to": to_state, "reason": reason,
            "reviewed_by": reviewed_by,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        object.__setattr__(rec, "state", to_state)
        return rec

    def get(self, blueprint_id: str) -> PromotionRecord | None:
        return self._records.get(blueprint_id)

    def all_records(self) -> tuple[PromotionRecord, ...]:
        return tuple(self._records.values())

    def in_state(self, state: PromotionState) -> tuple[PromotionRecord, ...]:
        return tuple(r for r in self._records.values() if r.state == state)

    def export(self) -> str:
        return json.dumps([r.to_dict() for r in self._records.values()],
                          indent=2, sort_keys=True)
