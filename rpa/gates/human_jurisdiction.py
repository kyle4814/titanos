"""
Human Jurisdiction Gate.

WHAT THIS FILE IS

The "HUMAN_APPROVAL_GATE" the governing directive requires for automation
candidates — built as a THIN, HONEST WRAPPER around
kpm.promotion.state_machine, not a new parallel promotion mechanism.

WHY THIS IS A WRAPPER AND NOT A NEW STATE MACHINE

This codebase has a documented history of catching exactly this kind of
duplication in code review (see magl/BUILD_REPORT.md's reconnaissance
section for the pattern named explicitly). kpm.promotion.state_machine
already owns:

  - the explicit TRANSITIONS table (absence of an edge is the
    enforcement, not a runtime if-check an argument could talk around —
    see that module's docstring),
  - PromotionStore.promote() and its STABLE-entry guard (reviewed_by
    required, reason required, SelfPromotionForbidden if reviewed_by ==
    created_by),
  - the append-only PromotionRecord.history audit trail.

Building a second promotion mechanism here — even a "simpler" one scoped
to automation candidates — would duplicate all of that, and duplicated
enforcement logic is exactly the kind of drift this codebase's anti-
duplication discipline exists to prevent (two mechanisms means two places
a fix has to land, and two places for them to silently disagree). So this
module imports PromotionStore / can_transition / SelfPromotionForbidden
directly and adds nothing to the transition table — it only sequences two
calls into it and re-derives one answer defensively from history.

A REAL FINDING THAT SHAPED THIS IMPLEMENTATION: TESTED HAS NO DIRECT EDGE
TO HUMAN_REVIEW

The original design brief for this gate assumed a candidate could move
straight from TESTED to HUMAN_REVIEW. Reading kpm/promotion/
state_machine.py's real `TRANSITIONS` table shows that edge does not
exist: `TRANSITIONS["TESTED"]` is `{STABLE, CONTESTED, QUARANTINED}` —
TESTED goes to STABLE directly (subject to the reviewed_by/
SelfPromotionForbidden guard), or to CONTESTED/QUARANTINED, and only
CONTESTED and QUARANTINED have an edge into HUMAN_REVIEW at all. There is
no way to reach HUMAN_REVIEW from TESTED in one hop, and this module does
not add one — adding an edge to TRANSITIONS to make this gate's job
easier would be precisely the "argue the store into skipping a step"
move that module's docstring says is impossible by design.

So `authorize_pilot` takes the real two-hop path: TESTED -> QUARANTINED
-> HUMAN_REVIEW. QUARANTINED is the closer semantic fit of the two
available intermediate states — its own docstring describes it as a
hold that "funnels to HUMAN_REVIEW only" and that "a human must look at
it" to clear it, which is exactly "ready for a human to look at, pending
their sign-off to pilot". (CONTESTED reads as "someone disputes this",
which is not what a fresh, untested-for-humans candidate is.) Neither hop
requires `reviewed_by` — TRANSITIONS enforces the STABLE-entry review
guard, not entry into QUARANTINED or HUMAN_REVIEW — but this function
still threads `reviewed_by` through both calls' `reason`/audit fields
purely for traceability of who queued the candidate.

WHY authorize_pilot DOES NOT REACH STABLE BY ITSELF

`authorize_pilot` moves a candidate TESTED -> QUARANTINED -> HUMAN_REVIEW
only. Reaching HUMAN_REVIEW means "ready for a human to look at", not
"authorized". A caller who wants a candidate actually authorized to pilot
must make a SEPARATE call — typically `store.promote(candidate_id,
"STABLE", reviewed_by=..., created_by=..., reason=...)` — after a human
has in fact reviewed it. Collapsing "queue for review" and "grant
approval" into one function call would let a single line of calling code
silently skip the human in the loop; keeping them as two calls means the
second call is the literal place in the codebase where a human's
decision must be recorded.

WHY confirm_pilot_authorized RE-DERIVES ITS ANSWER FROM HISTORY

`confirm_pilot_authorized` does not trust `record.state == "STABLE"` at
face value. It walks `record.history` and checks that the transition
which produced the current STABLE state actually originated at
HUMAN_REVIEW (this gate's intended path) and was reviewed by someone
other than the record's `created_by`. This mirrors this codebase's
"verify from the actual record, not the claimed status" discipline (see
e.g. compiler/coverage.py) — a record whose `state` field says STABLE but
whose history does not actually show a legitimate, independently-reviewed
promotion must not be trusted merely because the label says so.

Per the real TRANSITIONS table (kpm/promotion/state_machine.py), STABLE
is reachable from exactly two sources: TESTED -> STABLE and
HUMAN_REVIEW -> STABLE. `confirm_pilot_authorized` only accepts the
HUMAN_REVIEW -> STABLE path, matching this gate's design (`authorize_pilot`
always routes through HUMAN_REVIEW first) — a record that reached STABLE
directly via TESTED -> STABLE, bypassing this gate's queueing step
entirely, is deliberately NOT considered pilot-authorized by this
function, even though PromotionStore itself permits that edge for
promotable units in general. See rpa/gates/tests/test_human_jurisdiction.py
for a test proving TESTED -> STABLE is real-but-not-this-gate's-path, and
that `authorize_pilot` cannot be bypassed to fabricate a HUMAN_REVIEW
entry without an actual independent reviewer.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.promotion.state_machine import (  # noqa: E402
    IllegalTransition,
    PromotionRecord,
    PromotionStore,
    SelfPromotionForbidden,
    can_transition,
)

__all__ = ["authorize_pilot", "confirm_pilot_authorized"]


def authorize_pilot(
    store: PromotionStore, candidate_id: str, *, reviewed_by: str,
    created_by: str, reason: str,
) -> PromotionRecord:
    """Move an automation candidate from TESTED to HUMAN_REVIEW.

    THIS IS INTENTIONALLY A THIN WRAPPER. It reuses
    kpm.promotion.state_machine's existing PromotionStore/TRANSITIONS/
    SelfPromotionForbidden machinery rather than building a second
    promotion system for automation candidates specifically — see this
    module's docstring for why a second mechanism would be exactly the
    kind of duplication this codebase's review discipline exists to
    catch.

    Requires the record to currently be in TESTED state. Per the real
    TRANSITIONS table there is no direct TESTED -> HUMAN_REVIEW edge
    (see module docstring), so this makes the real two-hop trip
    TESTED -> QUARANTINED -> HUMAN_REVIEW, using two ordinary
    `store.promote()` calls and no new transition logic of its own —
    `can_transition` (via `store.promote()`) is what actually permits or
    refuses each hop; if the record is not in TESTED, the first hop
    raises IllegalTransition exactly as `store.promote()` normally would,
    and this function does not catch or reinterpret that.

    Reaching HUMAN_REVIEW here is NOT authorization. It means "ready for
    a human to look at". Actually authorizing the pilot (HUMAN_REVIEW ->
    STABLE) requires a SEPARATE, later call to `store.promote(...,
    "STABLE", ...)` — deliberately not made here, so that a single call
    to this function can never be mistaken for a human having actually
    approved anything.

    `reviewed_by` is accepted and threaded through to both
    `store.promote()` calls' `reason`/audit trail even though neither
    QUARANTINED nor HUMAN_REVIEW entry has a reviewed_by requirement in
    TRANSITIONS (only entry into STABLE does) — recording who queued the
    candidate for review is still useful audit context, and self-queueing
    (reviewed_by == created_by) is legitimate at this stage (raising a
    candidate's own hand for review is not the same act as approving it).
    SelfPromotionForbidden is only ever raised by PromotionStore.promote()
    itself, and only for a transition INTO STABLE — that exception is
    never suppressed or caught here; it propagates unchanged so a caller
    who feeds the wrong names into the later STABLE call receives the
    real state machine's real, well-understood error, not something this
    wrapper reinterpreted.
    """
    store.promote(
        candidate_id, "QUARANTINED",
        reason=reason, reviewed_by=reviewed_by, created_by=created_by,
    )
    return store.promote(
        candidate_id, "HUMAN_REVIEW",
        reason=reason, reviewed_by=reviewed_by,
    )


def confirm_pilot_authorized(store: PromotionStore, candidate_id: str) -> bool:
    """Return True only if `candidate_id` is genuinely authorized to
    pilot: currently STABLE, AND its history shows that STABLE was
    reached via a HUMAN_REVIEW -> STABLE transition reviewed by someone
    other than the record's created_by.

    This DOES NOT simply trust `record.state == "STABLE"`. It re-derives
    the authorization guarantee by walking `record.history` and finding
    the transition entry that actually produced the current STABLE
    state, checking:

      1. that entry's `from` is "HUMAN_REVIEW" (this gate's designed
         path — see module docstring for why the also-legal
         TESTED -> STABLE edge is deliberately NOT accepted here), and
      2. that entry's `reviewed_by` is present and differs from
         `record.created_by` (independent review actually happened;
         PromotionStore.promote() already refuses to create a
         HUMAN_REVIEW -> STABLE entry where reviewed_by == created_by
         via SelfPromotionForbidden, so this is a defence-in-depth
         re-check against the record's own data, not a check that could
         ever legitimately fail against data that came only through
         `authorize_pilot` + `store.promote()`).

    Returns False — never raises — for any record that is missing,
    not currently STABLE, or whose history does not show a HUMAN_REVIEW
    -> STABLE transition satisfying both conditions above. A caller
    cannot be fooled by a record whose `state` field merely says STABLE.
    """
    rec = store.get(candidate_id)
    if rec is None:
        return False
    if rec.state != "STABLE":
        return False

    # Find the most recent transition INTO STABLE in the append-only
    # history — that is the transition that produced the current state.
    stable_entries = [h for h in rec.history if h.get("to") == "STABLE"]
    if not stable_entries:
        return False
    last_stable_entry = stable_entries[-1]

    if last_stable_entry.get("from") != "HUMAN_REVIEW":
        return False

    reviewer = last_stable_entry.get("reviewed_by")
    if not reviewer:
        return False
    if reviewer == rec.created_by:
        return False

    return True
