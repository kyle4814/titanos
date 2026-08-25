"""
Narrative Atom Store — append-only promotion driver for
`narrative/schema/narrative_atom.py` (`PARETO_FRONTIER.md` FRONTIER-004).

WHAT THIS FILE IS, AND WHAT IT REUSES

`narrative_atom.py`'s `PROMOTION_STATES`/`PROMOTION_TRANSITIONS`/
`can_promote()` already exist and are tested — nothing here redefines
them. This module mirrors `kpm/promotion/state_machine.py::
PromotionStore` exactly, same shape, new domain: `register()` +
`promote()`, an append-only `AtomRecord` (amended by adding history
entries, never by editing), and the same two-property discipline
(illegal transitions absent from the table rather than checked ad hoc;
self-promotion forbidden at the one protected edge).

WHY `SUPPORTED -> CANONICAL_ABSTRACTION` IS THE ONE PROTECTED EDGE

Every other transition in `PROMOTION_TRANSITIONS` is a normal
evidentiary step (an atom moving through observation, classification,
connection, challenge, testing). Only canonization claims something is
"currently the most robust reusable abstraction under present
evidence" (narrative_atom.py's own doctrine) — the one claim serious
enough to require an independent second party, mirroring
`kpm.promotion.state_machine`'s STABLE gate exactly. `reviewed_by` must
differ from `created_by` by VALUE, not merely by presence — passing
your own name as reviewer does not satisfy it.

NO DELETE SURFACE

Same as `PromotionStore`/`QuarantineStore`/`RealityYieldLedger`/
`CrystalStore`: no `delete`, `purge`, `clear`, or `remove` method exists
on `NarrativeAtomStore` — not by convention, the methods do not exist,
so nothing downstream can call them even by mistake.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from narrative.schema.narrative_atom import PROMOTION_TRANSITIONS, can_promote

__all__ = [
    "AtomRecord", "NarrativeAtomStore",
    "IllegalAtomTransition", "SelfCanonizationForbidden",
]


class IllegalAtomTransition(Exception):
    """Raised when a promotion would use an edge absent from
    PROMOTION_TRANSITIONS. Loud on purpose — a silently-ignored illegal
    transition would let a caller believe a boundary held when it did
    not, the same reasoning as kpm.promotion.state_machine's identical
    exception."""


class SelfCanonizationForbidden(IllegalAtomTransition):
    """Raised when an atom's own creator attempts to canonize it
    (SUPPORTED -> CANONICAL_ABSTRACTION). Distinct from a missing
    reviewed_by (a plain IllegalAtomTransition below): here a reviewer
    name IS present, it is just the same name as the creator's."""


@dataclass(frozen=True)
class AtomRecord:
    """An append-only record. Amended by adding history entries, never
    by editing an existing one.

    Frozen so `state` can only change via `NarrativeAtomStore.promote()`
    (through `object.__setattr__`, the standard escape hatch for a
    frozen dataclass's own internal mutation) -- a caller holding a
    reference obtained from `get()` cannot bypass `can_promote()`/
    `SelfCanonizationForbidden` by assigning `rec.state = ...` directly.
    `history` is a `tuple`, not a `list` -- a caller holding a
    reference cannot `rec.history.append(...)`/`.insert(...)` to forge
    an entry (EPISTEMIC_INTEGRITY_002 found and closed a live exploit
    of exactly this shape against `PromotionRecord`, consumed by
    `rpa/gates/human_jurisdiction.py::confirm_pilot_authorized()` --
    see that module's own updated docstring). `promote()`/`register()`
    replace `history` with a new tuple via `object.__setattr__`, the
    same pattern already used for `state`."""
    atom_id: str
    state: str
    created_by: str
    history: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id, "state": self.state,
            "created_by": self.created_by, "history": list(self.history),
        }


class NarrativeAtomStore:
    """In-memory reference implementation. Append-only by construction —
    there is no delete/purge/clear/remove method, mirroring every other
    store of this shape in this repository."""

    def __init__(self) -> None:
        self._records: dict[str, AtomRecord] = {}

    def register(self, atom_id: str, *, created_by: str, state: str = "RAW") -> AtomRecord:
        if atom_id in self._records:
            raise ValueError(f"atom '{atom_id}' is already registered")
        if not created_by:
            raise ValueError("register() requires a non-empty created_by")
        rec = AtomRecord(
            atom_id=atom_id, state=state, created_by=created_by,
            history=({"from": None, "to": state, "reason": "registered",
                      "reviewed_by": None,
                      "at": datetime.now(timezone.utc).isoformat()},),
        )
        self._records[atom_id] = rec
        return rec

    def promote(
        self, atom_id: str, to_state: str, *,
        reason: str, reviewed_by: str | None = None,
    ) -> AtomRecord:
        """Move an atom's state, or raise.

        Transitioning INTO CANONICAL_ABSTRACTION requires `reviewed_by`,
        and `reviewed_by` must differ from the atom's `created_by` —
        checked by value, not by presence.
        """
        rec = self._records.get(atom_id)
        if rec is None:
            raise KeyError(f"no atom record for '{atom_id}'; register() it first.")

        if not can_promote(rec.state, to_state):
            raise IllegalAtomTransition(
                f"{rec.state} -> {to_state} is not a legal transition for "
                f"'{atom_id}'. Legal targets: "
                f"{sorted(PROMOTION_TRANSITIONS.get(rec.state, []))}."
            )

        if to_state == "CANONICAL_ABSTRACTION":
            if not reason.strip():
                raise ValueError("promotion to CANONICAL_ABSTRACTION requires a non-empty reason")
            if not reviewed_by:
                raise IllegalAtomTransition(
                    "promotion to CANONICAL_ABSTRACTION requires reviewed_by "
                    "(fail-closed: unknown review identity is not independent review)"
                )
            if reviewed_by == rec.created_by:
                raise SelfCanonizationForbidden(
                    f"atom '{atom_id}' was created_by='{rec.created_by}'; "
                    f"cannot be canonized by the same identity as reviewer."
                )

        new_entry = {
            "from": rec.state, "to": to_state, "reason": reason,
            "reviewed_by": reviewed_by,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        object.__setattr__(rec, "history", rec.history + (new_entry,))
        object.__setattr__(rec, "state", to_state)
        return rec

    def get(self, atom_id: str) -> AtomRecord | None:
        return self._records.get(atom_id)
