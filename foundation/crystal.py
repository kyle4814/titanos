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

DURABILITY -- WHAT WAS FALSE BEFORE AND WHAT CHANGED

`CrystalStore`'s docstring used to claim "Append-only store of Crystal
records. No delete surface" while holding nothing but a plain in-memory
dict. That claim was false: "append-only" describes an ordering
discipline, not a durability guarantee, and a Python dict has none —
every crystal recorded by a real GO cycle was lost the moment the
process exited, not merely on a crash. For a module whose entire reason
to exist is being the MEMORY link in this repository's own
REALITY -> LEVER -> ACTION -> TEST -> YIELD -> MEMORY chain
(`TITANOS_GREENLIGHT_AND_MEMETIC_DOCTRINE.md`), that is not a minor gap.

This module now follows the JSONL append/replay pattern proven in
`foundation/outcome_ledger.py::OutcomeLedger`: an optional `crystal_path`
is appended to on every `record()` and replayed on construction, with
`fsync` after every write (a guarantee `OutcomeLedger` itself does not
make — a store that reports success before its bytes are durable is
reporting something it does not actually know) and a truncated trailing
line skipped rather than raised on reload.

THE DEFAULT IS DELIBERATELY *NOT* A REPOSITORY PATH

`OutcomeLedger` defaults `ledger_path` to a module-relative file, but
every one of its own tests explicitly overrides that default with a
tempdir path — none of them ever construct `OutcomeLedger()` bare. This
module's existing test suite is the opposite: dozens of cases already
call `CrystalStore()` with no arguments, and per this fix's own
requirement they must keep passing unchanged. Defaulting `crystal_path`
to a real `foundation/crystal_store.jsonl` path would make every one of
those calls silently start writing to the repository on every test run
— test pollution, and the exact durability-vs-isolation trap
`outcome_ledger.py` and `admission.py` have already been caught in once
each. The correct call here is therefore the opposite of
`OutcomeLedger`'s default: `crystal_path` defaults to `None` (in-memory
only, byte-for-byte the previous behaviour). Durability is opt-in —
callers that want a crystal to survive process exit must pass an
explicit path, e.g. `CrystalStore(crystal_path=Path(__file__).resolve().parent / "crystal_store.jsonl")`.
This is the safer default because silent non-durability is a known,
already-documented limitation (see this repo's `CLAUDE.md`), while
silent repository writes during `unittest` runs are a new defect this
fix must not introduce.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
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
    """Append-only store of Crystal records. No delete surface.

    DURABILITY: see the module docstring's "DURABILITY" section for the
    full history of the defect this fixes. Short version: `crystal_path`
    is optional and defaults to `None` (in-memory only, matching the
    store's previous, entirely non-durable behaviour) precisely so the
    existing bare `CrystalStore()` test suite keeps its isolation. Pass
    an explicit path to get real durability — every `record()` is then
    appended to that file and fsync'd before the call returns, and the
    same records are replayed back on the next construction against that
    path.
    """

    def __init__(self, crystal_path: "str | Path | None" = None) -> None:
        self._crystal_path = Path(crystal_path) if crystal_path else None
        self._crystals: dict[str, Crystal] = {}
        self._order: list[str] = []
        if self._crystal_path is not None and self._crystal_path.exists():
            self._replay()

    # -- durability ----------------------------------------------------
    def _replay(self) -> None:
        """Reload every previously appended crystal from disk.

        Mirrors `OutcomeLedger._replay()`: a line that fails to parse as
        JSON is assumed to be a truncated trailing write from a process
        that died mid-append, and is skipped rather than raised — losing
        at most the single unflushed record, never the whole store. A
        line that parses but fails `Crystal`'s own field validation (or
        is missing a required key) is likewise skipped rather than
        aborting the whole reload, on the same "one bad record must not
        take down the rest of memory" principle.
        """
        with open(self._crystal_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue        # truncated trailing write; see docstring
                try:
                    crystal = Crystal(**obj)
                except (KeyError, TypeError, ValueError):
                    continue
                self._crystals[crystal.crystal_id] = crystal
                self._order.append(crystal.crystal_id)

    def _append(self, crystal: Crystal) -> None:
        if self._crystal_path is None:
            return
        self._crystal_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._crystal_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(crystal.to_dict(), sort_keys=True, default=str) + "\n")
            fh.flush()
            os.fsync(fh.fileno())  # durable before record() returns, not
                                    # merely "handed to the OS eventually"

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
        self._append(crystal)
        return crystal

    def get(self, crystal_id: str) -> Crystal | None:
        return self._crystals.get(crystal_id)

    def all_crystals(self) -> tuple[Crystal, ...]:
        """Every crystal ever recorded, in recording order, superseded included."""
        return tuple(self._crystals[i] for i in self._order)

    def is_current(self, crystal_id: str) -> bool:
        """True iff `crystal_id` exists and no other recorded crystal
        declares `supersedes=crystal_id`.

        `supersedes` (see `Crystal.supersedes`, checked at write-time in
        `record()`) was, before this method existed, validated on write
        but never consulted on read — `get()`/`all_crystals()` return a
        superseded crystal exactly as readily as a current one, with no
        signal attached. A future reader trusting a `Crystal` as current
        world-state without calling this first is exactly the "historical
        lesson treated as current truth" failure mode this repository's
        Monk/Demonblade doctrine forbids — this method exists so that
        check is one call, not a manual scan every caller has to
        reinvent (or forget to).

        A crystal with no superseding entry is current by definition,
        including one that was never in question — this never returns
        True for an id that was never recorded.
        """
        if crystal_id not in self._crystals:
            return False
        return not any(
            c.supersedes == crystal_id for c in self._crystals.values()
        )

    def reusable_abstractions(self) -> tuple[str, ...]:
        """The distilled lesson text of every recorded crystal, in order.

        This is the one query this store exists to make cheap: "what have
        we learned that generalises" without re-reading every
        BUILD_REPORT.md prose paragraph ever written in this repository.
        """
        return tuple(c.reusable_abstraction for c in self.all_crystals())
