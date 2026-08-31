"""Which side of the transaction is the asker on?

WHY THIS EXISTS

The demand mouth found two targets that scored highly and were both
worthless, for a reason no existing instrument could see.

`Vynix-Labs/Soroban-state-lens`: 2 stars, 78 forks, ~60 issues all
written by one account in a single batch, every one labelled
`Stellar Wave`, every one assigned and closed within a week by a
different one-commit contributor. `promisszn/soroban-amm`: 0 stars, 154
forks, all 58 issues by one account, same `Stellar Wave` label. These
are contributor-onboarding programmes -- a maintainer manufacturing
beginner tasks to feed a cohort. The demand is created BY the supply
side, and eighty contributors are already queued for it.

WHAT THE EXISTING INSTRUMENTS COULD NOT SEE

`activity_shape` asks "human or bot?" and answered correctly: those are
humans. `mouth_github_issues` asks "assigned or open?" and answered
correctly: unassigned. Both were right. Neither could tell that the
humans were on the WRONG SIDE of the transaction -- offering to work,
not asking to have work done. That is a third axis, orthogonal to both,
and it is the one that decides whether a buyer can possibly exist.

THE EVIDENCE IS DECLARED, NOT INFERRED

This module does not guess intent. A maintainer who labels an issue
`difficulty:beginner` and `size:xs` is stating outright that the task is
small and suitable for a newcomer -- which is a statement that it is
teaching material, not a problem they need expert help with. The label
is the maintainer's own words about their own issue. Nothing here reads
tone, sentiment, or wording.

WHY ONE LABEL IS NOT ENOUGH, MEASURED NOT ASSUMED

A live sweep of 30 unassigned asks found 7 carrying some teaching label.
Four of those were `mlflow/mlflow`, `maplibre/martin`,
`open-telemetry/opentelemetry.io` and `UniversalPython` -- healthy
projects where a maintainer flagged one genuinely approachable real
task. Treating a lone `good first issue` as a farm marker would have
discarded four legitimate targets to catch one.

What separated the farm was GRADING DEPTH: `good first issue` AND
`difficulty:beginner` AND `size:xs` AND `phase:7` AND a cohort label.
One grading axis is triage. Several independent axes are a curriculum,
and a curriculum exists to be taught from, not to be solved.

WHAT THIS DELIBERATELY DOES NOT CONCLUDE

`NEED_NOT_EXCLUDED` is not "verified demand" and is named so it cannot
be misread as one. It means only that no recruitment evidence was found.
Absence of farm markers is not proof that a real need exists -- that
would be the missing-evidence-as-positive-signal substitution this whole
spine was built to refuse.

A FORK:STAR RATIO WAS CONSIDERED AND REJECTED

`Soroban-state-lens` has 39 forks per star and `soroban-amm` has 154
forks and no stars, so the ratio looked like a decisive tell. Measured
across the same 30-ask sweep it flagged 9 of 27 repositories, including
`open-telemetry/opentelemetry.io` and `OCA/hr` -- a docs repository and
an enterprise module collection, both of which legitimately take more
forks than stars because contribution happens through forks. The ratio
is recorded here as a REJECTED discriminator so it does not get
proposed again.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence

__all__ = [
    "DIRECTIONS",
    "DIRECTION_MODEL_VERSION",
    "MIN_GRADING_AXES",
    "SOLE_AUTHOR_SHARE",
    "TEACHING_LABELS",
    "RESERVATION_LABELS",
    "GRADING_PREFIXES",
    "REJECTED_DISCRIMINATORS",
    "DemandDirection",
    "classify_direction",
]

DIRECTION_MODEL_VERSION = "1"

DIRECTIONS = (
    # Positive evidence that the ask exists to be handed to a contributor.
    "WORK_OFFERED",
    # No recruitment evidence found. NOT a positive finding of real need.
    "NEED_NOT_EXCLUDED",
    # Nothing to read -- no labels at all.
    "UNKNOWN",
)

# A maintainer's own declaration that the task is approachable. Weak on
# its own: a healthy project flagging one genuinely easy real task looks
# exactly like this, and four of the seven live asks carrying such a
# label were mlflow, martin, opentelemetry.io and UniversalPython.
TEACHING_LABELS = frozenset({
    "good first issue", "good-first-issue", "goodfirstissue",
    "beginner", "beginners", "easy", "starter", "newcomer", "newbie",
    "up-for-grabs", "up for grabs",
})

# Stronger, and different in kind: these do not say "this is easy", they
# say "this is RESERVED for someone inexperienced" -- the maintainer is
# excluding experienced contributors on purpose, because the point of the
# issue is to teach. `first-timers-only` is a formal convention meaning
# exactly that.
#
# One of these alone is sufficient, and the reasoning is eligibility
# rather than judgement: an issue reserved for first-time contributors
# is one this system could not take even if the underlying problem were
# real and valuable. No threshold applies to a closed door.
RESERVATION_LABELS = frozenset({
    "first-timers-only", "first timers only", "first-timers",
    "mentorship", "mentored", "student", "onboarding",
    "reserved-for-newcomers", "newcomers-only",
})

# Namespaced labels that GRADE a task along an axis. Several independent
# axes on one issue is a curriculum, which is the actual signal -- see
# the module docstring for why one axis alone is not.
GRADING_PREFIXES = ("difficulty:", "size:", "level:", "phase:", "complexity:",
                    "effort:", "week:", "track:", "cohort:", "wave:")

# Below this many independent grading axes, graded labels are ordinary
# triage. A judgement, versioned with the model, not a discovery.
MIN_GRADING_AXES = 2

# Sole-authorship share at which a repository's asks stop reading as a
# community and start reading as one account running a programme. Only
# ever used to CORROBORATE a teaching or cohort label -- never on its
# own, because a single-maintainer project with real problems also
# writes all of its own issues.
SOLE_AUTHOR_SHARE = 0.9

# Discriminators measured and found to misclassify. Kept so they are not
# re-proposed. See the module docstring.
REJECTED_DISCRIMINATORS = (
    "fork:star ratio -- flagged 9/27 repositories including "
    "open-telemetry/opentelemetry.io and OCA/hr, both legitimate",
)

_COHORT = re.compile(r"\b(wave|cohort|bootcamp|hackathon|sprint\s*\d|"
                     r"season\s*\d|batch\s*\d)\b", re.I)


def _norm(label: str) -> str:
    return " ".join(str(label).strip().lower().split())


@dataclass(frozen=True)
class DemandDirection:
    """Which side of the transaction the asker is on, and why.

    `reasons` carries the maintainer's own labels back to the caller, so
    a verdict can always be argued with against the evidence that
    produced it rather than taken on trust.
    """

    direction: str
    grading_axes: tuple[str, ...] = ()
    teaching_labels: tuple[str, ...] = ()
    reservation_labels: tuple[str, ...] = ()
    cohort_label: Optional[str] = None
    sole_author_share: Optional[float] = None
    reasons: tuple[str, ...] = ()
    model_version: str = DIRECTION_MODEL_VERSION

    def is_recruitment(self) -> bool:
        return self.direction == "WORK_OFFERED"

    def counts_as_demand(self) -> bool:
        """Only an ask with no recruitment evidence may be read as demand.

        UNKNOWN does not qualify: with no labels there is nothing to
        stand on, and unknown is not true.
        """
        return self.direction == "NEED_NOT_EXCLUDED"

    def show_the_math(self) -> str:
        lines = [f"DEMAND DIRECTION {self.direction} "
                 f"(model v{self.model_version})"]
        if self.grading_axes:
            lines.append(f"  grading axes  {len(self.grading_axes)} "
                         f"{list(self.grading_axes)} "
                         f"(threshold {MIN_GRADING_AXES})")
        if self.teaching_labels:
            lines.append(f"  teaching      {list(self.teaching_labels)}")
        if self.reservation_labels:
            lines.append(f"  RESERVED FOR  {list(self.reservation_labels)}")
        if self.cohort_label:
            lines.append(f"  cohort label  {self.cohort_label!r}")
        if self.sole_author_share is not None:
            lines.append(f"  sole author   {self.sole_author_share:.0%} of "
                         f"the repository's recent asks")
        for r in self.reasons:
            lines.append(f"  reason: {r}")
        if self.direction == "NEED_NOT_EXCLUDED":
            lines.append("  NOTE: no recruitment evidence found. That is "
                         "NOT evidence that a real need exists.")
        return "\n".join(lines)


def classify_direction(labels: Sequence[str],
                       sole_author_share: Optional[float] = None
                       ) -> DemandDirection:
    """Classify one ask from its labels, and optionally from authorship.

    `sole_author_share` is the share of the repository's recent asks
    written by a single account, when the caller happens to know it. It
    is never required: the label evidence stands alone, and a caller
    that cannot afford the extra request still gets a verdict. When it
    IS supplied, near-total sole authorship corroborates a single
    teaching label that would otherwise be too weak to act on -- one
    account writing every ask in a repository is a programme, whereas
    many accounts asking is a community.
    """
    norm = [_norm(l) for l in labels if _norm(l)]
    if not norm:
        return DemandDirection(direction="UNKNOWN",
                               reasons=("no labels to read",))

    teaching = tuple(sorted({l for l in norm if l in TEACHING_LABELS}))
    reserved = tuple(sorted({l for l in norm if l in RESERVATION_LABELS}))
    axes = tuple(sorted({l.split(":", 1)[0] + ":"
                         for l in norm
                         if l.startswith(GRADING_PREFIXES)}))
    cohort = next((l for l in norm if _COHORT.search(l)), None)

    reasons: list[str] = []
    recruitment = False

    if reserved:
        recruitment = True
        reasons.append(
            f"reserved for inexperienced contributors by {list(reserved)}: "
            f"the maintainer is excluding experienced help on purpose, so "
            f"this ask is not available to answer whatever its merits")
    if len(axes) >= MIN_GRADING_AXES:
        recruitment = True
        reasons.append(
            f"{len(axes)} independent grading axes ({', '.join(axes)}) is a "
            f"graded curriculum, not triage")
    if cohort and teaching:
        recruitment = True
        reasons.append(
            f"cohort label {cohort!r} alongside a teaching label: the ask "
            f"belongs to a contributor programme")
    if ((teaching or cohort) and sole_author_share is not None
            and sole_author_share >= SOLE_AUTHOR_SHARE):
        recruitment = True
        marker = (f"labelled this one for beginners" if teaching
                  else f"labelled this one {cohort!r}")
        reasons.append(
            f"one account wrote {sole_author_share:.0%} of this "
            f"repository's recent asks and {marker}: a programme, not a "
            f"community")

    if not recruitment:
        if teaching:
            reasons.append(
                f"teaching label {list(teaching)} present but only "
                f"{len(axes)} grading axis/axes and no corroboration -- a "
                f"maintainer flagging one approachable real task looks "
                f"exactly like this")
        else:
            reasons.append("no teaching or grading taxonomy on this ask")

    return DemandDirection(
        direction="WORK_OFFERED" if recruitment else "NEED_NOT_EXCLUDED",
        grading_axes=axes, teaching_labels=teaching,
        reservation_labels=reserved, cohort_label=cohort,
        sole_author_share=sole_author_share, reasons=tuple(reasons))
