"""
Crystalline Memory (PAYLOAD_09 / TITANOS_LAYER0.../doctrine's "MEMORY" link
in REALITY -> LEVER -> ACTION -> TEST -> YIELD -> MEMORY -> PACKAGE ->
ADOPTION -> FEEDBACK).

WHAT THIS FILE ANSWERS, AND ONLY THIS

Every GO/build cycle in this repository already produces a conclusion
("18 tests passing", "declined as duplicate") but that conclusion has
lived only in prose — a BUILD_REPORT.md paragraph or a commit message.
Prose is not queryable and does not force the *why*: it is easy to write
"this worked" and never write down what would have falsified it. A
Crystal is the structured alternative: one record per completed cycle,
with a fixed field set, so "why did we believe this" and "what would
have proven it wrong" are first-class, not reconstructed later from
memory.

WHY THIS IS NOT A SECOND REALITY-YIELD LEDGER

`reality_yield_ledger.py` already answers "was this worth it, in cost vs
benefit terms" and this file does not re-answer that question — a
Crystal's `evidence`/`result` fields may *cite* a LedgerEntry `entry_id`
but the store here does not compute net yield. A Crystal answers a
different question: "what was believed, on what basis, and what would
change that belief" — epistemic provenance, not cost accounting.

WHY EVIDENCE-FREE FIELDS ARE STILL ALLOWED TO BE EMPTY

`failure_mode` and `limitation` may legitimately be empty ("no failure
mode discovered yet" is different from a lie). What is NOT allowed to be
empty is `problem`, `hypothesis`, `action`, `result`, and
`reusable_abstraction` — a crystal that cannot state what it believed,
what it did, and what came of it is not a completed cycle, it is a
diary entry, and does not belong in this store.

NO DELETE SURFACE, SAME PATTERN AS EVERY OTHER STORE IN THIS REPO

Mirrors `reality_yield_ledger.py` / `kpm/promotion/state_machine.py` /
`firewall/quarantine.py`: append-only, no delete/purge/clear/remove
method. A crystal later shown to be wrong is superseded, not erased —
`supersedes` points at the old id, both remain retrievable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS

__all__ = ["Crystal", "CrystalStore"]

_REQUIRED_NON_EMPTY = (
    "problem",
    "hypothesis",
    "action",
    "result",
    "reusable_abstraction",
)


@dataclass
class Crystal:
    """One completed cycle's structured memory. Immutable once constructed.

    `epistemic_status` reuses `kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS`
    rather than a parallel vocabulary — same discipline as
    `narrative/schema/narrative_atom.py`'s `EPISTEMIC_LAYERS`.
    """

    crystal_id: str
    problem: str
    context: str
    hypothesis: str
    action: str
    evidence: str
    result: str
    failure_mode: str
    limitation: str
    provenance: str
    reusable_abstraction: str
    regression_test_ref: str
    epistemic_status: str
    recorded_by: str
    recorded_at: str = ""
    supersedes: str | None = None

    def __post_init__(self) -> None:
        for field_name in _REQUIRED_NON_EMPTY:
            value = getattr(self, field_name)
            if not value or not value.strip():
                raise ValueError(
                    f"crystal '{self.crystal_id}' requires non-empty "
                    f"'{field_name}' — a crystal that cannot state this is "
                    f"not a completed cycle."
                )
        if self.epistemic_status not in ALL_CLASSIFICATIONS:
            raise ValueError(
                f"crystal '{self.crystal_id}' epistemic_status "
                f"{self.epistemic_status!r} is not one of "
                f"{sorted(ALL_CLASSIFICATIONS)}"
            )
        if not self.recorded_by:
            raise ValueError(
                f"crystal '{self.crystal_id}' requires recorded_by — no "
                f"crystal may claim to have no author."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CrystalStore:
    """Append-only store of Crystal records. No delete surface."""

    def __init__(self) -> None:
        self._crystals: dict[str, Crystal] = {}
        self._order: list[str] = []

    def record(
        self,
        crystal_id: str,
        *,
        problem: str,
        context: str,
        hypothesis: str,
        action: str,
        evidence: str,
        result: str,
        failure_mode: str = "",
        limitation: str = "",
        provenance: str,
        reusable_abstraction: str,
        regression_test_ref: str = "",
        epistemic_status: str,
        recorded_by: str,
        supersedes: str | None = None,
    ) -> Crystal:
        if crystal_id in self._crystals:
            raise ValueError(f"crystal '{crystal_id}' already recorded")
        if supersedes is not None and supersedes not in self._crystals:
            raise KeyError(f"cannot supersede '{supersedes}': no such crystal recorded")

        crystal = Crystal(
            crystal_id=crystal_id,
            problem=problem,
            context=context,
            hypothesis=hypothesis,
            action=action,
            evidence=evidence,
            result=result,
            failure_mode=failure_mode,
            limitation=limitation,
            provenance=provenance,
            reusable_abstraction=reusable_abstraction,
            regression_test_ref=regression_test_ref,
            epistemic_status=epistemic_status,
            recorded_by=recorded_by,
            recorded_at=datetime.now(timezone.utc).isoformat(),
            supersedes=supersedes,
        )
        self._crystals[crystal_id] = crystal
        self._order.append(crystal_id)
        return crystal

    def get(self, crystal_id: str) -> Crystal | None:
        return self._crystals.get(crystal_id)

    def all_crystals(self) -> tuple[Crystal, ...]:
        """Every crystal ever recorded, in recording order, superseded included."""
        return tuple(self._crystals[i] for i in self._order)

    def reusable_abstractions(self) -> tuple[str, ...]:
        """The distilled lesson text of every recorded crystal, in order.

        This is the one query this store exists to make cheap: "what have
        we learned that generalises" without re-reading every
        BUILD_REPORT.md prose paragraph ever written in this repository.
        """
        return tuple(c.reusable_abstraction for c in self.all_crystals())
