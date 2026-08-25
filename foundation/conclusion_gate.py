"""
Conclusion Gate — SUBZERO_MUTATION_001.

WHY THIS IS SMALLER THAN A WORKFLOW ENGINE

`foundation/layer0_worker.py::CycleRecord` already tracks a run's
`steps_completed`/`halted`/`halt_reason` for autonomous typed workers —
but `halted` is binary and nothing validates whether a caller's claim of
success is actually earned. `foundation/task_queue.py::RecoveryHandoff`
already IS the HANDOFF_REQUIRED durable-state concept, scoped to one
subsystem (the task queue) — reused here as an opaque payload a
`CycleConclusion` may carry, not duplicated. Neither existing type
rejects a caller's claim of completion when required evidence is
absent. That is the actual gap this module closes: a validating
boundary, not a new execution model, not a workflow engine, not a
second orchestration layer.

WHAT THIS DOES NOT DO

Does not run anything, re-derive proof, or measure yield — takes
`objective`/`changed`/`proof`/`limitation`/`next_move` as caller-declared
inputs, the same boundary `human_jurisdiction.py` and `hells_gate.py`
already hold (re-derive a *decision* from evidence the caller supplies;
never invent the evidence itself). `conclude_cycle()` is a pure
function over its input — it calls nothing, spawns nothing, and cannot
recurse into another cycle. It never emits a caller-declared status
directly (mirroring `hells_gate.py`'s own "never output TRUSTED"
discipline) — the status is always computed here, never trusted.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = ["TerminalStatus", "CycleConclusion", "conclude_cycle"]


class TerminalStatus(str, Enum):
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"
    LIMITED = "LIMITED"
    HANDOFF_REQUIRED = "HANDOFF_REQUIRED"


_NO_LIMITATION_MARKERS = frozenset({"", "none", "n/a", "na", "ø", "nil"})


@dataclass(frozen=True)
class CycleConclusion:
    status: TerminalStatus
    objective: str
    changed: str
    proof: str
    limitation: str
    next_move: str
    next_move_executed: bool
    reason: str
    handoff_state: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value, "objective": self.objective,
            "changed": self.changed, "proof": self.proof,
            "limitation": self.limitation, "next_move": self.next_move,
            "next_move_executed": self.next_move_executed,
            "reason": self.reason,
            "handoff_state": self.handoff_state,
        }


def conclude_cycle(
    *,
    objective: str,
    next_move: str,
    next_move_executed: bool,
    changed: str = "",
    proof: str = "",
    limitation: str = "",
    blocker: str = "",
    handoff: bool = False,
    handoff_state: Any = None,
) -> CycleConclusion:
    """Validating terminal boundary for one execution cycle. Fixed
    precedence, evaluated in this order — the same order every call
    resolves in, making a conclusion with multiple simultaneous signals
    deterministic rather than ambiguous:

    1. `next_move_executed=True` — the Next-Move Isolation Law: a
       declared NEXT must never be performed inside the cycle that
       declared it. Always BLOCKED, regardless of any other input.
    2. `blocker` non-empty — an explicit evidence-backed blocker.
       BLOCKED.
    3. `handoff=True` — durable state is sufficient but continuation
       requires a new execution context. HANDOFF_REQUIRED, carrying
       whatever `handoff_state` the caller supplied (opaque to this
       module — may be a `task_queue.RecoveryHandoff`, a plain string,
       or anything else the caller's domain needs to hand forward).
    4. Any of `objective`/`changed`/`proof`/`next_move` blank —
       COMPLETE requires all four declared. BLOCKED (the report itself
       is incomplete, not the underlying work).
    5. `limitation` non-empty (and not a "no limitation" marker like
       "none"/"n/a"/"Ø") — LIMITED.
    6. Otherwise — COMPLETE.

    Fails closed on false completion (any of 1-5 above prevents
    COMPLETE). Never fails closed on legitimate incompleteness —
    BLOCKED/LIMITED/HANDOFF_REQUIRED are all valid, fully inspectable
    terminal states, not errors raised by this function.
    """
    if next_move_executed:
        return CycleConclusion(
            status=TerminalStatus.BLOCKED,
            objective=objective, changed=changed, proof=proof,
            limitation=limitation, next_move=next_move,
            next_move_executed=next_move_executed,
            reason=(
                "next_move_executed=True violates the Next-Move Isolation "
                "Law — a declared NEXT move must never be performed "
                "inside the cycle that declared it; this cycle cannot be "
                "concluded COMPLETE while that boundary is broken"
            ),
        )

    if blocker:
        return CycleConclusion(
            status=TerminalStatus.BLOCKED,
            objective=objective, changed=changed, proof=proof,
            limitation=limitation, next_move=next_move,
            next_move_executed=next_move_executed,
            reason=blocker,
        )

    if handoff:
        return CycleConclusion(
            status=TerminalStatus.HANDOFF_REQUIRED,
            objective=objective, changed=changed, proof=proof,
            limitation=limitation, next_move=next_move,
            next_move_executed=next_move_executed,
            reason=(
                "durable state is sufficient but continuation requires a "
                "new execution context"
            ),
            handoff_state=handoff_state,
        )

    missing = [name for name, value in (
        ("objective", objective), ("changed", changed),
        ("proof", proof), ("next_move", next_move),
    ) if not value or not value.strip()]
    if missing:
        return CycleConclusion(
            status=TerminalStatus.BLOCKED,
            objective=objective, changed=changed, proof=proof,
            limitation=limitation, next_move=next_move,
            next_move_executed=next_move_executed,
            reason=(
                f"required field(s) missing or blank: {', '.join(missing)} "
                "— COMPLETE cannot be emitted without a declared "
                "objective, change, proof, and next move"
            ),
        )

    if limitation.strip().lower() not in _NO_LIMITATION_MARKERS:
        return CycleConclusion(
            status=TerminalStatus.LIMITED,
            objective=objective, changed=changed, proof=proof,
            limitation=limitation, next_move=next_move,
            next_move_executed=next_move_executed,
            reason=(
                "a known boundary prevents stronger completion; recorded "
                "honestly rather than hidden"
            ),
        )

    return CycleConclusion(
        status=TerminalStatus.COMPLETE,
        objective=objective, changed=changed, proof=proof,
        limitation=limitation, next_move=next_move,
        next_move_executed=next_move_executed,
        reason=(
            "objective, change, and proof are all declared; no blocker, "
            "no handoff signal, no hidden limitation, next move not yet "
            "executed"
        ),
    )
