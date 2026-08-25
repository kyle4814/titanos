"""
Defusal Router — CT_141's response sequence, routed (MAGL_CT141_002_
DEFUSAL_ROUTER, named as deferred in `foundation/MAPPING.md`).

WHAT THIS FILE IS, AND IS NOT

`foundation/flow_switch.py` already implements CT_141's *axiom*
(PANIC = information velocity > verification velocity) and the *tempo*
half of the response (NORMAL/HIGH_COMPLEXITY -> SIGNAL_COLLAPSE ->
RECOVERY -> ...). What it does not implement is the *response
checklist* — the ordered list of concrete things a system should do
once panic is detected, independent of which mode label it ends up in.
This module is that checklist, expressed as an inspectable, orderable
sequence rather than doctrine prose scattered across four files.

This module is a ROUTER, not an EXECUTOR. `route_defusal()` returns a
`DefusalSequence` describing what should happen and in what order; it
never performs an action, transitions a mode, writes a log entry, or
touches `FlowSwitchStore`. That boundary is deliberate and mirrors
`foundation/hells_gate.py` and `foundation/sentinel.py`: neither of
those modules executes their own findings either, and this module's own
test suite checks — the same way `TestSentinelCannotExecute` does for
`sentinel.py` — that no public callable here is named as an imperative
action verb.

WHAT THIS FILE REUSES, NOT DUPLICATES

- Panic detection: imports `PanicSample`/`detect_panic` from
  `foundation.flow_switch` rather than re-deriving the axiom. This
  module answers "given that panic is already detected, what ordered
  response does doctrine actually describe" — it does not decide
  whether panic is occurring.
- Tempo state: does not touch `MODE_TRANSITIONS` or `FlowSwitchStore`.
  A caller that wants both the tempo transition AND the response
  checklist calls `flow_switch.recommend_transition()` and
  `route_defusal()` separately, on the same `PanicSample` — this module
  is downstream of, not a replacement for, flow_switch's state machine.

HONESTY ABOUT THE STEP COUNT

`foundation/MAPPING.md`'s existing entry for this module describes the
response as "reduce velocity -> preserve raw input -> freeze belief ->
... -> log the event -> resume only on exit condition" and, in an
earlier session's transcript no longer available to this one, apparently
named an "11-step" checklist. That source text is gone — no file in this
repository currently contains 11 distinct, individually-nameable steps
for the CT_141 response, and inventing 11 to match a remembered number
that cannot be re-derived would be exactly the "manufacture certainty"
failure `TITANOS_GO_CYCLE_DOCTRINE.md` §XV prohibits.

What actually exists, checked with `grep -l CT_141 *.md` against this
repository's root, is the response text in four files:

- `TITANOS_GO_CYCLE_DOCTRINE.md` §IV — "throttle, preserve raw input,
  freeze belief, separate observation from interpretation, reduce the
  active problem, verify the next claim, take the lowest-regret action,
  recurse only after the signal is stable" plus "recovery passes through
  observation -> classification -> verification -> stabilization ->
  limited action -> reassessment."
- `TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md` §X — "freeze belief,
  preserve raw input, reduce output/broadcast, quarantine the claim,
  separate fact from interpretation, seek independent external signal,
  prefer reversible action, return to the smallest test" plus "loose
  lips sink ships -> minimize unnecessary broadcast, need-to-know data
  flow, preserve auditability, never hide critical risk from authorized
  human oversight."
- `TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md` §8 (The Fail-Safe Default)
  — "observe -> preserve -> classify -> verify -> simulate -> request
  review if required -> select lowest-regret move."
- `TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md` — restates the axiom
  and the no-panic-based-exit rule only; contributes no additional
  response step beyond the three files above.

Merging these three overlapping lists (the fourth contributes nothing
new) and collapsing exact restatements of the same operational idea
(e.g. "freeze belief" appears in two files; "verify the next claim" /
"seek independent external signal" / "verify" are the same act of
checking a claim against something outside itself) produces exactly
**nine** distinct, individually-testable steps — `DEFUSAL_STEPS` below.
Nine, not eleven. If a future session recovers the original 11-step
text, extending `DEFUSAL_STEPS` is a one-line change; this module does
not pad itself to a remembered number it cannot currently justify from
source.

FAIL-CLOSED SHAPE

`route_defusal()` only ever returns a populated `DefusalSequence` when
`detect_panic(sample)` is True. When it is not, the function returns a
`DefusalSequence` with `panic_detected=False` and an EMPTY step tuple —
never a sequence with the ordinary steps marked "not needed," and never
`None` (a `None` return would push interpretation of "no defusal
required" onto every caller separately, exactly the kind of ambiguous
contract `foundation/hells_gate.py`'s ADMIT/QUARANTINE/REJECT/
HUMAN_REVIEW_REQUIRED shape exists to avoid). A caller that checks
`sequence.panic_detected` before iterating `sequence.steps` can never
observe a non-empty response to a non-panicking sample.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from foundation.flow_switch import PanicSample, detect_panic  # noqa: E402

__all__ = [
    "DefusalStep", "DefusalSequence", "DEFUSAL_STEPS", "route_defusal",
]


@dataclass(frozen=True)
class DefusalStep:
    """One named step in the CT_141 response checklist.

    `complete` is always `False` on every step this module returns —
    this module never marks a step complete because it never performs
    one. A downstream executor that actually carries out a step is
    responsible for recording completion in its own state (a
    `Crystal`, a `FlowSwitchRecord` transition reason, a log entry);
    re-deriving completion here would require this module to either
    execute the step (forbidden) or trust a caller-supplied claim of
    completion (which `foundation/hells_gate.py`'s "capability vs
    claim" gate already treats as unverified by default). The field
    exists on the dataclass, frozen at `False`, so a future executor
    can produce a *new*, updated `DefusalStep` (via `dataclasses.
    replace`) rather than this module inventing a mutable in-place
    flag that would blur the router/executor boundary.
    """
    name: str
    description: str
    source: str
    complete: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "complete": self.complete,
        }


@dataclass(frozen=True)
class DefusalSequence:
    """The ordered response plan for one `PanicSample`, or the empty,
    not-needed result.

    `steps` is a tuple, not a list — the same append-only-shape
    discipline used throughout this codebase (`FlowSwitchRecord.
    history`, `HellsGateDecision.findings`) so a caller holding a
    reference cannot mutate the plan this function returned.
    """
    panic_detected: bool
    sample: PanicSample
    steps: tuple[DefusalStep, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "panic_detected": self.panic_detected,
            "sample": {
                "information_velocity": self.sample.information_velocity,
                "verification_velocity": self.sample.verification_velocity,
                "timestamp": self.sample.timestamp,
            },
            "steps": [s.to_dict() for s in self.steps],
        }


# ─────────────────────────────────────────────────────────────
# The nine-step CT_141 response checklist, derived from doctrine
# ─────────────────────────────────────────────────────────────
#
# Order matches the sequence every source file states it in: throttle
# first (stop making the problem worse before doing anything else),
# preserve/freeze/classify next (protect the evidence and stop drawing
# conclusions from it before verifying), verify and act only after that,
# log throughout, and only resume once an explicit exit condition is
# met — the same "no panic-based exit" shape `flow_switch.py`'s
# SIGNAL_COLLAPSE -> RECOVERY transition already enforces in code.

DEFUSAL_STEPS: tuple[DefusalStep, ...] = (
    DefusalStep(
        name="THROTTLE",
        description=(
            "Stop increasing output/action rate. Do not generate more "
            "noise, broadcast urgency, or accelerate because pressure "
            "demands it — the velocity mismatch is the failure, so the "
            "first move reduces velocity rather than trying to out-run "
            "it."
        ),
        source="GO_CYCLE_DOCTRINE §IV 'throttle'; REALITY_YIELD §X "
               "'reduce output/broadcast'",
    ),
    DefusalStep(
        name="PRESERVE_RAW_INPUT",
        description=(
            "Capture and retain the original, unmodified input that "
            "triggered the panic reading before any further processing "
            "touches it — later steps reason about this preserved copy, "
            "not a summary or a re-interpretation of it."
        ),
        source="GO_CYCLE_DOCTRINE §IV and REALITY_YIELD §X, both "
               "'preserve raw input'",
    ),
    DefusalStep(
        name="FREEZE_BELIEF",
        description=(
            "Stop updating confident conclusions and quarantine the "
            "specific claim(s) in flight when the panic reading "
            "occurred. This is not 'ignore the input' — it is 'do not "
            "let more of it become belief until it can be checked.'"
        ),
        source="GO_CYCLE_DOCTRINE §IV 'freeze belief'; REALITY_YIELD "
               "§X 'freeze belief... quarantine the claim'",
    ),
    DefusalStep(
        name="SEPARATE_OBSERVATION_FROM_INTERPRETATION",
        description=(
            "Classify what was actually observed apart from what was "
            "inferred, assumed, or predicted about it — the same "
            "fact/interpretation split the Three-Rail Doctrine's "
            "'Clear Mind' rail requires generally, applied specifically "
            "to the input that triggered this panic reading."
        ),
        source="GO_CYCLE_DOCTRINE §IV 'separate observation from "
               "interpretation'; REALITY_YIELD §X 'separate fact from "
               "interpretation'; SWITCH_GATE §8 'classify'",
    ),
    DefusalStep(
        name="REDUCE_SCOPE_AND_BROADCAST",
        description=(
            "Narrow the active problem to the smallest piece actually "
            "under review, and minimize unnecessary broadcast of the "
            "still-unverified claim on a need-to-know basis — 'loose "
            "lips sink ships,' without concealing the risk from "
            "authorized human oversight."
        ),
        source="GO_CYCLE_DOCTRINE §IV 'reduce the active problem'; "
               "REALITY_YIELD §X 'minimize unnecessary broadcast, "
               "need-to-know data flow'",
    ),
    DefusalStep(
        name="VERIFY",
        description=(
            "Check the next claim against something outside itself — "
            "an independent signal, a test, a re-derivation — rather "
            "than accepting confidence as a substitute for "
            "verification. This is the step that is allowed to change "
            "FREEZE_BELIEF's quarantine, and only this step."
        ),
        source="GO_CYCLE_DOCTRINE §IV 'verify the next claim'; "
               "REALITY_YIELD §X 'seek independent external signal'; "
               "SWITCH_GATE §8 'verify'",
    ),
    DefusalStep(
        name="TAKE_LOWEST_REGRET_ACTION",
        description=(
            "Where an action must still be taken, prefer the smallest, "
            "most reversible option and the smallest available test "
            "over a large or irreversible commitment — simulate before "
            "committing where simulation is possible."
        ),
        source="GO_CYCLE_DOCTRINE §IV 'take the lowest-regret action'; "
               "REALITY_YIELD §X 'prefer reversible action, return to "
               "the smallest test'; SWITCH_GATE §8 'simulate... select "
               "lowest-regret move'",
    ),
    DefusalStep(
        name="LOG_AND_PRESERVE_AUDITABILITY",
        description=(
            "Record what happened, what was frozen, what was verified, "
            "and what action was taken — preserving auditability and "
            "escalating to human review where required, rather than "
            "letting the episode disappear from the record once it "
            "feels resolved."
        ),
        source="REALITY_YIELD §X 'preserve auditability, never hide "
               "critical risk from authorized human oversight'; "
               "SWITCH_GATE §8 'request review if required'",
    ),
    DefusalStep(
        name="RESUME_ONLY_ON_EXIT_CONDITION",
        description=(
            "Do not resume normal tempo merely because time has passed "
            "or pressure has eased — resume only once an explicit exit "
            "condition is met and stable. This is the same rule "
            "`flow_switch.py` enforces in code: SIGNAL_COLLAPSE has no "
            "panic-based exit and no direct edge back to NORMAL or "
            "HIGH_COMPLEXITY; RECOVERY is the only legal next step, and "
            "even RECOVERY's own recommend_transition() will not "
            "re-enter NORMAL while a fresh panic reading persists."
        ),
        source="GO_CYCLE_DOCTRINE §IV 'recurse only after the signal is "
               "stable'... 'recovery passes through observation -> "
               "classification -> verification -> stabilization -> "
               "limited action -> reassessment'; foundation/"
               "MAPPING.md's own phrasing 'resume only on exit "
               "condition'",
    ),
)


def route_defusal(sample: PanicSample) -> DefusalSequence:
    """Return the CT_141 response plan for `sample`, or the empty,
    not-needed plan.

    Fail-closed in the direction that matters for this module: a
    non-panicking sample NEVER produces the nine-step plan (there is
    nothing here to defuse), and a panicking sample ALWAYS produces the
    full plan — this function does not selectively omit steps based on
    any heuristic about "how bad" the panic reading is. Doctrine does
    not describe a partial-severity response, and inventing one here
    would be exactly the kind of unverified elaboration this module's
    own docstring warns against.

    Pure function: no I/O, no mode transition, no store write. A caller
    that also wants the tempo-state recommendation calls
    `foundation.flow_switch.recommend_transition()` separately on the
    same `sample`.
    """
    if not detect_panic(sample):
        return DefusalSequence(panic_detected=False, sample=sample, steps=())
    return DefusalSequence(panic_detected=True, sample=sample, steps=DEFUSAL_STEPS)
