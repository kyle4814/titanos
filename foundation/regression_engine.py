"""
Foundation Regression Engine — MAGL_FOUNDATION_003_REGRESSION_ENGINE
(`foundation/MAPPING.md`).

WHY THIS FILE EXISTS

`kpm/contradictions/registry.py` already RECORDS that a contradiction
exists between two or more claims. `kpm/promotion/state_machine.py`
already provides a real, enforced, append-only lifecycle with an
explicit `TRANSITIONS` table. Neither module talks to the other. §XIV
step 14 of the governing directive ("if contradicted, downgrade,
quarantine, or deprecate") names the missing link: nothing currently
re-tests a hardened switch against new evidence and connects the two
existing stores. This module is that connective tissue — and nothing
more. It does not add a third store, a new evidence format, or a second
notion of "sufficient evidence."

WHY THIS DOES NOT INVENT A NEW EVIDENCE THRESHOLD

`ContradictionRegistry.resolve()` already draws the one evidence-
sufficiency line this codebase has decided on: a contradiction may only
be closed as `RESOLVED` — a factual finding that at least one involved
claim is wrong — if `evidence_refs` is non-empty. `WONT_FIX` requires a
reason but asserts no finding; `OPEN` asserts nothing has been checked
yet. This module reuses exactly that distinction rather than adding a
second, competing bar: it only proposes a regression for contradictions
already closed `RESOLVED` in the registry, because `RESOLVED` is the one
status in that module's own vocabulary that both (a) names a specific
record as party to a verified contradiction and (b) was gated on
non-empty evidence to get there. An `OPEN` contradiction is a flagged
possibility, not (yet) a verified collision; propagating it into an
automatic downgrade proposal would be exactly the "caller-declared fact
treated as verified fact" pattern this codebase's Black Ice doctrine
forbids elsewhere.

WHY THIS DOES NOT CALL `.promote()`

`foundation/sentinel.py`'s `FourPaths`/`Finding` model draws a hard line
between observing and acting: "FINDING DOES NOT EQUAL AUTHORIZATION."
`check_for_regression()` follows the identical discipline. It answers
"is there a verified contradiction against this record, and if so what
is the one already-legal transition that would downgrade it" — and
returns that as a `RegressionDecision` the caller can inspect, log,
surface to a human, or act on. It never calls `PromotionStore.promote()`
itself. This is not a missing feature; it is the point. Automatically
executing a state transition off the back of code that also decides
whether the transition is warranted would collapse the same
observe/propose/execute boundary this codebase already enforces in
`sentinel.py` and in `foundation/hells_gate.py` (which likewise never
outputs "TRUSTED" — only a challengeable admission decision). The
caller — a human, or a higher-level workflow a human has already
authorized — makes the actual `promote()` call, with the proposal in
hand, through the ordinary `PromotionStore` API, subject to every rule
that API already enforces (including `SelfPromotionForbidden`, where
relevant, on the way back out of a downgraded state).

WHY THE TARGET IS CHOSEN THE WAY IT IS

This module does not invent a "downgrade" edge. It walks the real
`kpm.promotion.state_machine.TRANSITIONS` table, already legal, already
tested, unchanged, and picks the first target from a fixed preference
order that is actually reachable from the record's current state:

    QUARANTINED > CONTESTED > HUMAN_REVIEW > DEPRECATED

This order is not arbitrary. `QUARANTINED` and `CONTESTED` are the
table's two designated "something is wrong, stop advancing" holds, and
either is reachable directly from every one of RAW / DISTILLED /
PROVISIONAL / TESTED / HUMAN_REVIEW. Neither is reachable directly from
`CONTESTED` or `QUARANTINED` themselves (a contradiction against a
record already mid-hold routes to `HUMAN_REVIEW`, the table's own only
way out of either state — see `state_machine.py`'s own docstring: "the
only way out of either is HUMAN_REVIEW"). `DEPRECATED` is last because
it is the table's terminal "abandoned" state, only reachable from
`STABLE` or `HUMAN_REVIEW` — the correct answer specifically for a
contradiction found against something already `STABLE`, where neither
`QUARANTINED` nor `CONTESTED` nor even `HUMAN_REVIEW` is a legal direct
target (`TRANSITIONS["STABLE"] == {"DEPRECATED", "SUPERSEDED"}`).

Some states have NO legal target in this preference order at all —
`DEPRECATED` and `SUPERSEDED` are both terminal (`TRANSITIONS[...] ==
frozenset()`). A contradiction found against a record already in either
state cannot be automatically routed anywhere by this table, and this
module reports that honestly (`proposed_target=None`,
`regression_proposed=False`, `no_legal_target=True`) rather than
inventing a delete/overwrite mechanism to route around it — per this
repository's standing `SIGIL.NO_DELETE_SURFACE` rule, that absence is
itself the correct, real finding to surface to a human, not a gap to
silently paper over.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.contradictions.registry import ContradictionRegistry  # noqa: E402
from kpm.promotion.state_machine import PromotionStore, TRANSITIONS  # noqa: E402

__all__ = ["RegressionDecision", "check_for_regression", "DOWNGRADE_PREFERENCE_ORDER"]

# Fixed preference order for the one already-legal downgrade edge to
# select, walked in this order against the record's current state's
# real entry in TRANSITIONS. See the module docstring for why this
# specific order, not a config knob — changing it changes what
# "downgrade" means for every caller, so it is a code review decision,
# not a runtime parameter.
DOWNGRADE_PREFERENCE_ORDER: tuple[str, ...] = (
    "QUARANTINED", "CONTESTED", "HUMAN_REVIEW", "DEPRECATED",
)


@dataclass(frozen=True)
class RegressionDecision:
    """A proposal, never an executed action. See module docstring.

    `regression_proposed=False` covers two very different situations,
    distinguished by `no_legal_target` — do not conflate them:
      * no verified contradiction was found at all (nothing to act on)
      * a verified contradiction WAS found, but the record's current
        state has no legal downgrade edge in TRANSITIONS (a real,
        reportable gap, not a null result)
    """

    record_id: str
    regression_proposed: bool
    current_state: str | None
    triggering_contradiction_id: str | None
    proposed_target: str | None
    no_legal_target: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "regression_proposed": self.regression_proposed,
            "current_state": self.current_state,
            "triggering_contradiction_id": self.triggering_contradiction_id,
            "proposed_target": self.proposed_target,
            "no_legal_target": self.no_legal_target,
            "reason": self.reason,
        }


def check_for_regression(
    promotion_store: PromotionStore,
    contradiction_registry: ContradictionRegistry,
    record_id: str,
    *,
    contradiction_id: str,
) -> RegressionDecision:
    """Propose — never execute — a downgrade for `record_id` in response
    to a verified (RESOLVED, evidence-gated) contradiction.

    `contradiction_id` names the specific contradiction to check, rather
    than this function silently scanning the whole registry for
    anything that might apply. This mirrors `ContradictionRegistry`'s
    own real public surface: it exposes `.get(contradiction_id)` and
    `.open_contradictions()` (OPEN-only), not a reverse index from
    "involved_id -> every contradiction naming it." A caller who already
    knows which contradiction to re-test (the ordinary case — regression
    checks are triggered BY a specific contradiction being resolved, not
    by blind polling) passes it explicitly; this function then verifies,
    from the registry's own record, that:
      1. the contradiction exists,
      2. `record_id` is actually one of its `involved_ids` (a caller
         cannot get a downgrade proposal for a record a contradiction
         never named),
      3. its status is `RESOLVED` — the one status `ContradictionRegistry`
         itself only reaches with non-empty `evidence_refs` (see
         `resolve()`), i.e. "sufficient evidence" is defined exactly as
         the registry already defines it, not by a second threshold
         invented here.

    If all three hold, this function reads `record_id`'s CURRENT state
    from `promotion_store` (never trusts a caller-supplied state) and
    selects the first entry of `DOWNGRADE_PREFERENCE_ORDER` that is a
    real legal target per `kpm.promotion.state_machine.TRANSITIONS`.

    Returns a `RegressionDecision` describing what SHOULD happen and
    why. Does not call `promotion_store.promote()`. The caller executes
    the proposal, if it chooses to, with a separate explicit call.
    """
    contradiction = contradiction_registry.get(contradiction_id)
    if contradiction is None:
        return RegressionDecision(
            record_id=record_id, regression_proposed=False, current_state=None,
            triggering_contradiction_id=contradiction_id, proposed_target=None,
            no_legal_target=False,
            reason=f"no contradiction '{contradiction_id}' exists in the registry — "
                   f"nothing to act on.",
        )

    if record_id not in contradiction.involved_ids:
        return RegressionDecision(
            record_id=record_id, regression_proposed=False, current_state=None,
            triggering_contradiction_id=contradiction_id, proposed_target=None,
            no_legal_target=False,
            reason=f"contradiction '{contradiction_id}' does not name '{record_id}' "
                   f"among its involved_ids ({contradiction.involved_ids}) — "
                   f"nothing to act on for this record.",
        )

    if contradiction.status != "RESOLVED":
        # OPEN: not yet evidence-verified. WONT_FIX: explicitly not a
        # factual finding (see registry.py's own docstring). Neither
        # passes the registry's own evidence-sufficiency bar for
        # asserting the contradiction is real.
        return RegressionDecision(
            record_id=record_id, regression_proposed=False, current_state=None,
            triggering_contradiction_id=contradiction_id, proposed_target=None,
            no_legal_target=False,
            reason=f"contradiction '{contradiction_id}' is status "
                   f"'{contradiction.status}', not RESOLVED — the registry only "
                   f"requires evidence_refs to reach RESOLVED, so a non-RESOLVED "
                   f"contradiction is not (yet) sufficient evidence to propose "
                   f"a downgrade.",
        )

    record = promotion_store.get(record_id)
    if record is None:
        return RegressionDecision(
            record_id=record_id, regression_proposed=False, current_state=None,
            triggering_contradiction_id=contradiction_id, proposed_target=None,
            no_legal_target=False,
            reason=f"'{record_id}' has no promotion record in the given "
                   f"PromotionStore — nothing to downgrade.",
        )

    current_state = record.state
    legal_targets = TRANSITIONS.get(current_state, frozenset())
    proposed_target = next(
        (t for t in DOWNGRADE_PREFERENCE_ORDER if t in legal_targets), None
    )

    if proposed_target is None:
        return RegressionDecision(
            record_id=record_id, regression_proposed=False, current_state=current_state,
            triggering_contradiction_id=contradiction_id, proposed_target=None,
            no_legal_target=True,
            reason=f"'{record_id}' has a RESOLVED, evidence-backed contradiction "
                   f"('{contradiction_id}'), but its current state "
                   f"'{current_state}' has no legal edge to any of "
                   f"{DOWNGRADE_PREFERENCE_ORDER} in TRANSITIONS (legal targets "
                   f"from here: {sorted(legal_targets) or 'none — terminal state'}). "
                   f"This is a real gap, not a null result: a human must decide "
                   f"how to handle a verified contradiction against a record in "
                   f"a state the promotion lifecycle treats as having no further "
                   f"downward move.",
        )

    return RegressionDecision(
        record_id=record_id, regression_proposed=True, current_state=current_state,
        triggering_contradiction_id=contradiction_id, proposed_target=proposed_target,
        no_legal_target=False,
        reason=f"'{record_id}' has a RESOLVED, evidence-backed contradiction "
               f"('{contradiction_id}'); {current_state} -> {proposed_target} is "
               f"a legal transition per TRANSITIONS. Proposing this downgrade — "
               f"NOT executing it. The caller must separately call "
               f"promotion_store.promote('{record_id}', '{proposed_target}', "
               f"reason=...) to actually apply it.",
    )
