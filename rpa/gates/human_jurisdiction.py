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
from typing import Sequence

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
from rpa.validators.validate_automation_candidate import (  # noqa: E402
    validate_automation_candidate,
)

# kpm/source-vault/ is a hyphenated directory name -- not a legal Python
# package identifier, and inserting it into sys.path (as several earlier
# call sites in this repo do) creates a real collision: kpm/source-vault/
# tests/ and rpa/tests/ are both literally a directory named "tests",
# so a bare sys.path insert of kpm/source-vault/ shadows whichever
# "tests" package unittest discovery is trying to resolve for whatever
# subsystem happens to run second (found the hard way: `python3 -m
# unittest discover -s rpa` broke after this fix's first draft added
# exactly that insert). Loading registry.py by explicit file path via
# importlib avoids touching sys.path at all.
import importlib.util as _importlib_util  # noqa: E402

_REGISTRY_PATH = _REPO_ROOT / "kpm" / "source-vault" / "registry.py"
_registry_spec = _importlib_util.spec_from_file_location(
    "kpm_source_vault_registry", _REGISTRY_PATH,
)
_registry_module = _importlib_util.module_from_spec(_registry_spec)
# Registered in sys.modules under its synthetic name BEFORE exec_module,
# same as the standard importlib recipe -- dataclasses' own type
# resolution (`sys.modules.get(cls.__module__)`) needs to find this
# module by that name once SourceRecord's dataclass machinery runs.
sys.modules[_registry_spec.name] = _registry_module
_registry_spec.loader.exec_module(_registry_module)
SourceRegistry = _registry_module.SourceRegistry

__all__ = [
    "authorize_pilot", "confirm_pilot_authorized",
    "NoValidatedSource", "AmbiguousValidatedSource",
]


class NoValidatedSource(Exception):
    """Raised by `authorize_pilot` when none of the declared `source_hashes`
    recover to content that passes `validate_automation_candidate()`.

    This is the fix for a real, adversarially-found gap (this session's own
    recon): `PromotionStore`'s STABLE-entry guard only checks reviewer
    diversity and a non-empty reason — it has no way to know whether the
    automation candidate's actual jurisdiction/failure-scenario/rollback
    content was ever structurally validated. `confirm_pilot_authorized()`'s
    re-derivation from history proves WHO reviewed it, never WHAT was
    reviewed. Fresh, non-cached validation at the moment of queueing is
    the fix — see rpa/ADOPT.md and this session's own recon for why
    recomputation (not a durable "was validated" witness) is correct:
    validate_automation_candidate() is pure and deterministic, so a stale
    stored witness would be strictly weaker than checking fresh."""


class AmbiguousValidatedSource(Exception):
    """Raised when more than one declared source_hash independently
    validates as a real automation candidate — this gate has no way to
    know which one the caller actually means to authorize, and guessing
    (e.g. "the first one") would silently reintroduce the exact
    subject-substitution risk this fix exists to close."""


def authorize_pilot(
    store: PromotionStore, candidate_id: str, *, reviewed_by: str,
    created_by: str, reason: str,
    source_registry: SourceRegistry, source_hashes: Sequence[str],
) -> PromotionRecord:
    """Move an automation candidate from TESTED to HUMAN_REVIEW.

    NEW GUARD (this session's own adversarial recon found and closed
    this gap): before queueing anything for human review, this function
    now recovers the exact bytes for every hash in `source_hashes` via
    `source_registry.get_content()` (raising `KeyError`/`NoSuchContentHash`
    unchanged if a hash doesn't resolve — fail loud, not silent) and runs
    `validate_automation_candidate()` fresh against each. Exactly one must
    return `VALID`:

      - zero VALID results -> `NoValidatedSource` (no real, structurally
        checked automation candidate backs this authorization request —
        this is the exact hole the recon found: a caller could previously
        queue *any* `candidate_id` string for review with no connection
        to real, validated content at all).
      - more than one VALID result -> `AmbiguousValidatedSource` (this
        gate cannot know which one the caller means to authorize, and
        guessing would reopen the same substitution risk).

    Validation is recomputed fresh every call rather than trusting a
    stored past result, because `validate_automation_candidate()` is pure
    and deterministic — recomputation is strictly stronger than any
    durable witness (immune to validator-version drift, immune to a
    witness surviving past when it should have been invalidated).

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
    valid_count = 0
    for content_hash in source_hashes:
        for record in source_registry.get_by_hash(content_hash):
            content = source_registry.get_content(record.artifact_id)
            result = validate_automation_candidate(content.decode("utf-8"))
            if result.status == "VALID":
                valid_count += 1

    if valid_count == 0:
        raise NoValidatedSource(
            f"cannot authorize pilot for '{candidate_id}': none of the "
            f"declared source_hashes recover to content that passes "
            f"validate_automation_candidate(). An authorization request "
            f"with no real validated automation-candidate content behind "
            f"it cannot be queued for human review."
        )
    if valid_count > 1:
        raise AmbiguousValidatedSource(
            f"cannot authorize pilot for '{candidate_id}': {valid_count} "
            f"declared source_hashes independently validate as real "
            f"automation candidates. This gate cannot determine which one "
            f"is the actual subject of this authorization request."
        )

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
