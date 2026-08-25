"""
CT_141 Flow Switch — system-wide operating tempo state machine and panic
detector.

THE AXIOM

    PANIC = INFORMATION VELOCITY > VERIFICATION VELOCITY

When a system produces or consumes claims, actions or tokens faster than
it can independently check them, the correct response is to throttle, not
accelerate. Confidence and speed are not the same signal, and treating
them as the same signal is the failure mode this module exists to catch.

FOUR MODES, NOT A DIAL

    NORMAL           Explore -> Test -> Execute -> Learn
    HIGH_COMPLEXITY  Narrow -> Verify -> Reversible Action -> Measure
    SIGNAL_COLLAPSE  Freeze Belief -> Preserve Evidence -> Reduce Output
                      -> Await Validation
    RECOVERY         Reconstruct Context -> Identify Stable Invariants
                      -> Resume Minimal Flow

Tempo is discrete, not a continuous throttle knob, for the same reason
`firewall/quarantine.py` uses a state machine rather than a score: a
discrete machine has an inspectable transition table, and a table can be
red-teamed by a human. A dial can only be argued with.

WHY SIGNAL_COLLAPSE HAS NO DIRECT EDGE BACK

`firewall/quarantine.py` will not let QUARANTINED jump straight to
AUTHORIZED — release has to re-pass verification. The identical shape
applies here. Once belief has been frozen because verification could not
keep up with information, the system that recorded that failure is not
in a position to also self-certify its own recovery: whatever caused the
collapse is still, by construction, unverified. RECOVERY is a
mandatory, separate step — reconstruct context, identify what invariants
actually held — before tempo may increase again. SIGNAL_COLLAPSE ->
NORMAL and SIGNAL_COLLAPSE -> HIGH_COMPLEXITY are both absent from
MODE_TRANSITIONS on purpose; the absence is the enforcement, not a
runtime if-check that something could bypass.

RECOVERY -> SIGNAL_COLLAPSE is also absent. Re-entering collapse from
inside recovery would not be a new collapse, it would be the same
collapse never having actually ended — RECOVERY exits either forward
(to NORMAL or HIGH_COMPLEXITY, once invariants are confirmed) or it is
still in collapse and should not have claimed to be RECOVERY at all.

NO SILENT TRANSITIONS

Every transition is recorded with a caller-supplied `reason` (why the
move happened) and `evidence_for_exit` (what would justify leaving the
mode being entered). Both are mandatory; an empty `evidence_for_exit` is
rejected the same way `firewall/quarantine.py` rejects an empty
quarantine reason — an unexplained exit criterion is indistinguishable
from "we will decide later, informally", which is exactly the drift this
module exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Mapping

__all__ = [
    "OperatingMode", "MODE_TRANSITIONS", "can_transition",
    "IllegalModeTransition", "PanicSample", "detect_panic",
    "FlowSwitchRecord", "FlowSwitchStore", "recommend_transition",
]

# ─────────────────────────────────────────────────────────────
# Vocabulary
# ─────────────────────────────────────────────────────────────

OperatingMode = str

ALL_MODES = frozenset({
    "NORMAL", "HIGH_COMPLEXITY", "SIGNAL_COLLAPSE", "RECOVERY",
})

# The explicit transition table, same pattern as firewall/quarantine.py's
# TRANSITIONS: legality is the presence of an edge, not a runtime check.
#
# SIGNAL_COLLAPSE -> {RECOVERY} only. No edge to NORMAL or HIGH_COMPLEXITY.
# This is the load-bearing safety property of this module — see module
# docstring "WHY SIGNAL_COLLAPSE HAS NO DIRECT EDGE BACK".
MODE_TRANSITIONS: Mapping[OperatingMode, frozenset[OperatingMode]] = {
    "NORMAL":           frozenset({"HIGH_COMPLEXITY", "SIGNAL_COLLAPSE"}),
    "HIGH_COMPLEXITY":  frozenset({"NORMAL", "SIGNAL_COLLAPSE"}),
    "SIGNAL_COLLAPSE":  frozenset({"RECOVERY"}),
    "RECOVERY":         frozenset({"NORMAL", "HIGH_COMPLEXITY"}),
}


class IllegalModeTransition(Exception):
    """Raised when a mode change would bypass the recovery boundary.

    Loud on purpose — a silently-clamped illegal transition would let a
    caller believe tempo dropped through SIGNAL_COLLAPSE's proper exit
    when it did not.
    """


def can_transition(src: OperatingMode, dst: OperatingMode) -> bool:
    return dst in MODE_TRANSITIONS.get(src, frozenset())


# ─────────────────────────────────────────────────────────────
# Panic detection
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PanicSample:
    """A caller-declared reading of the two velocities.

    This module does not measure anything. `information_velocity` and
    `verification_velocity` are supplied by the caller (new claims /
    actions / tokens per unit time, and independently-checked claims /
    actions per the same unit time, respectively); this module only
    reasons about the two numbers.
    """
    information_velocity: float
    verification_velocity: float
    timestamp: str


def detect_panic(sample: PanicSample) -> bool:
    """PANIC = INFORMATION VELOCITY > VERIFICATION VELOCITY.

    Edge cases handled explicitly rather than falling out of the
    comparison by luck:

    - verification_velocity == 0 and information_velocity > 0: panic.
      Nothing is being checked while things are being produced — this is
      exactly the failure mode the axiom names.
    - verification_velocity == 0 and information_velocity == 0: NOT
      panic. Nothing is happening at all, which is not the same failure
      as producing unchecked output; a quiescent system is not panicking.
    """
    if sample.information_velocity == 0 and sample.verification_velocity == 0:
        return False
    return sample.information_velocity > sample.verification_velocity


# ─────────────────────────────────────────────────────────────
# Append-only history store
# ─────────────────────────────────────────────────────────────

@dataclass
class FlowSwitchRecord:
    """An append-only record of one session's tempo history.

    Mirrors QuarantineRecord's shape: current state plus a growing
    history list, amended only by appending new entries.
    """
    session_id: str
    mode: OperatingMode
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FlowSwitchStore:
    """In-memory reference implementation. Append-only by construction.

    There is no `delete`, no `purge`, no `clear` and no `remove`. Not by
    convention — the methods do not exist, so nothing downstream can call
    them even by mistake, mirroring firewall/quarantine.py's
    QuarantineStore.
    """

    def __init__(self) -> None:
        self._records: dict[str, FlowSwitchRecord] = {}

    def start_session(
        self, session_id: str, initial_mode: OperatingMode = "NORMAL",
    ) -> FlowSwitchRecord:
        if initial_mode not in ALL_MODES:
            raise ValueError(
                f"unrecognised initial_mode '{initial_mode}'. Must be one "
                f"of {sorted(ALL_MODES)}."
            )
        rec = FlowSwitchRecord(
            session_id=session_id,
            mode=initial_mode,
            history=[{
                "from": None, "to": initial_mode,
                "reason": "session start",
                "evidence_for_exit": "n/a — initial mode",
                "at": datetime.now(timezone.utc).isoformat(),
            }],
        )
        self._records[session_id] = rec
        return rec

    def transition(
        self, session_id: str, to_mode: OperatingMode, *,
        reason: str, evidence_for_exit: str,
    ) -> FlowSwitchRecord:
        """Move a session's mode, or raise.

        No transition may occur silently: `reason` explains why the move
        happened, `evidence_for_exit` states what would justify leaving
        the mode being entered. Both are mandatory.
        """
        rec = self._records.get(session_id)
        if rec is None:
            raise KeyError(f"no flow-switch session for '{session_id}'")
        if not evidence_for_exit.strip():
            raise ValueError(
                "transition requires a non-empty evidence_for_exit. A mode "
                "change with no stated exit criterion cannot be validated "
                "later and is indistinguishable from drift."
            )
        if not reason.strip():
            raise ValueError(
                "transition requires a non-empty reason. An unexplained "
                "tempo change cannot be audited."
            )
        if not can_transition(rec.mode, to_mode):
            raise IllegalModeTransition(
                f"{rec.mode} -> {to_mode} is not a legal transition for "
                f"session '{session_id}'. Legal targets from {rec.mode}: "
                f"{sorted(MODE_TRANSITIONS.get(rec.mode, []))}. Note there is "
                f"deliberately no edge from SIGNAL_COLLAPSE to NORMAL or "
                f"HIGH_COMPLEXITY — recovery must pass through RECOVERY."
            )
        rec.history.append({
            "from": rec.mode, "to": to_mode, "reason": reason,
            "evidence_for_exit": evidence_for_exit,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        rec.mode = to_mode
        return rec

    def get(self, session_id: str) -> FlowSwitchRecord | None:
        return self._records.get(session_id)

    def all_records(self) -> tuple[FlowSwitchRecord, ...]:
        return tuple(self._records.values())


# ─────────────────────────────────────────────────────────────
# Pure decision function
# ─────────────────────────────────────────────────────────────

def recommend_transition(sample: PanicSample, current_mode: OperatingMode) -> OperatingMode | None:
    """Recommend a target mode, or None to stay put. No side effects.

    This function never recommends a target that MODE_TRANSITIONS would
    reject — in particular it never recommends NORMAL or HIGH_COMPLEXITY
    out of SIGNAL_COLLAPSE, panicking or not, because RECOVERY is the
    only legal next step from collapse and a caller could otherwise use
    this function to talk itself past the store's enforcement by never
    calling .transition() at all.
    """
    if current_mode not in ALL_MODES:
        raise ValueError(f"unrecognised current_mode '{current_mode}'.")

    panicking = detect_panic(sample)

    if current_mode == "SIGNAL_COLLAPSE":
        # Collapse must be actively investigated, not waited out — there
        # is no panic-based exit at all, regardless of whether panic is
        # currently detected. RECOVERY is the only legal target.
        return "RECOVERY"

    if current_mode == "RECOVERY":
        # Recovery resumes minimal flow once stable. It never recommends
        # re-entering SIGNAL_COLLAPSE (that edge does not exist) even if
        # the sample still reads as panicking — a fresh panic signal
        # inside RECOVERY is evidence recovery isn't finished, not a
        # license to loop back into collapse; recommend staying put.
        if panicking:
            return None
        return "NORMAL"

    if current_mode in ("NORMAL", "HIGH_COMPLEXITY"):
        if panicking:
            return "SIGNAL_COLLAPSE"
        return None

    return None
