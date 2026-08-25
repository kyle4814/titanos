"""
Reality Yield Ledger (governing directive §XI, made real).

WHAT THIS FILE ANSWERS, AND ONLY THIS

Before any "lesson" or "pathway" is hardened into permanent system
behaviour, it must show a positive REALITY_YIELD:

  REALITY_YIELD = VERIFIED_BENEFIT + ERROR_REDUCTION + REUSABILITY +
                  INFORMATION_GAIN - COMPUTE_COST - HUMAN_REVIEW_COST -
                  SYSTEMIC_RISK - REVERSIBILITY_COST

"Do not use projected outcomes as evidence of present value. Simulation
is not revenue. Confidence is not profit." This module does not compute
that equation from thin air — it forces every term to be a CLAIM WITH
EVIDENCE, recorded once, never edited, and it makes the resulting
three-way decision (CONTINUE_CAUTIOUSLY / HOLD_AND_REVIEW /
THROTTLE_OR_TERMINATE) a literal function of the recorded numbers, not a
vibe.

WHY EVIDENCE IS REQUIRED ON EVERY COMPONENT, NOT JUST THE ENTRY

A ledger that only requires "some evidence somewhere" on an entry lets an
impressive VERIFIED_BENEFIT ride in on the coattails of a well-evidenced
REUSABILITY line. Each YieldComponent is checked independently: a large,
confident-sounding number attached to forward-looking evidence is
rejected on ITS OWN terms, regardless of how solid its siblings are.

THE FORWARD-LOOKING-WORD BLOCKLIST IS DELIBERATELY NARROW AND IMPERFECT

"This will pay off" is trivially rewritten as "this pays off" by anyone
determined to get past a keyword filter — the blocklist below does not
detect intent, and it does not verify that the evidence text actually
describes an observation rather than merely omitting a banned word. It
exists as a structural nudge, the same spirit as the conclusory-word
blocklist in rpa/schema/institutional_bottleneck.py: cheap, catches the
common honest mistake of writing a forecast where a fact belongs, and
makes zero claim to being a semantic guarantee that evidence is real.
Actual evidentiary weight is a human-review judgment this file cannot
make.

WHY supersedes IS A NEW ENTRY, NEVER AN EDIT

Mirrors kpm/contradictions/registry.py and firewall/dissent.py: a
reassessment does not overwrite the record of what was believed before.
A subject's yield can be reassessed downward later (new evidence, a
production incident, a cost that was invisible until it recurred) and
the earlier, more optimistic assessment must still be retrievable via
history_for() — not because the old assessment was "right", but because
being able to see that it was wrong, and by how much, is the whole point
of keeping a ledger instead of a single mutable field.

NO DELETE SURFACE

RealityYieldLedger has no delete/purge/clear/remove method. A yield
assessment, once recorded — good or bad, positive or deeply negative —
stays recorded. The ledger's job is to tell the truth about what was
measured, not to curate a good-news feed.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Sequence

__all__ = [
    "YieldComponent",
    "LedgerEntry",
    "RealityYieldLedger",
    "net_reality_yield",
    "YIELD_NAMES",
    "COST_NAMES",
    "FORWARD_LOOKING_PHRASES",
]

# The four yield-side terms and the four cost-side terms of the
# REALITY_YIELD equation. Fixed sets — a component's `name` must belong
# to exactly one side; there is no third bucket and no free-text name.
YIELD_NAMES: frozenset[str] = frozenset({
    "VERIFIED_BENEFIT",
    "ERROR_REDUCTION",
    "REUSABILITY",
    "INFORMATION_GAIN",
})

COST_NAMES: frozenset[str] = frozenset({
    "COMPUTE_COST",
    "HUMAN_REVIEW_COST",
    "SYSTEMIC_RISK",
    "REVERSIBILITY_COST",
})

# Deliberately narrow, imperfect nudge against forecasts-as-evidence.
# See module docstring: this is a keyword blocklist, not a semantic
# check. It catches the common honest mistake, not a determined evader.
FORWARD_LOOKING_PHRASES: frozenset[str] = frozenset({
    "will",
    "projected",
    "expected to",
    "forecast",
    "eventually",
    "is going to",
    "should result in",
    "anticipated",
    "once deployed",
    "once scaled",
})


def _contains_forward_looking_language(evidence: str) -> str | None:
    """Return the offending phrase if `evidence` reads as a forecast, else None."""
    lowered = evidence.lower()
    for phrase in FORWARD_LOOKING_PHRASES:
        if phrase in lowered:
            return phrase
    return None


@dataclass
class YieldComponent:
    """One term of the REALITY_YIELD equation, as a claim with evidence.

    `value` is always entered as a non-negative magnitude. Which side of
    the equation it lands on (added or subtracted) is determined by
    `name` — VERIFIED_BENEFIT/ERROR_REDUCTION/REUSABILITY/
    INFORMATION_GAIN are yield-side, COMPUTE_COST/HUMAN_REVIEW_COST/
    SYSTEMIC_RISK/REVERSIBILITY_COST are cost-side — never by the caller
    passing a negative number for a cost.
    """

    name: str
    value: float
    evidence: str

    def __post_init__(self) -> None:
        if self.name not in YIELD_NAMES and self.name not in COST_NAMES:
            raise ValueError(
                f"'{self.name}' is not a recognised yield or cost component. "
                f"Yield-side: {sorted(YIELD_NAMES)}. "
                f"Cost-side: {sorted(COST_NAMES)}."
            )
        if self.value < 0:
            raise ValueError(
                f"component '{self.name}' has value {self.value!r}; component "
                f"values are entered as non-negative magnitudes — sign is "
                f"determined by which side of the equation the name belongs "
                f"to, not by the caller passing a negative number."
            )
        if not self.evidence or not self.evidence.strip():
            raise ValueError(
                f"component '{self.name}' requires non-empty evidence. A "
                f"value with no evidence is a bare number pulled from "
                f"nowhere, not a claim."
            )
        offender = _contains_forward_looking_language(self.evidence)
        if offender is not None:
            raise ValueError(
                f"component '{self.name}' evidence contains the "
                f"forward-looking phrase '{offender}': {self.evidence!r}. "
                f"Projected outcomes are not evidence of present value — "
                f"evidence must describe something already observed. "
                f"Simulation is not revenue; confidence is not profit."
            )

    def is_yield(self) -> bool:
        return self.name in YIELD_NAMES

    def is_cost(self) -> bool:
        return self.name in COST_NAMES

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LedgerEntry:
    """One recorded reality-yield assessment of a subject. Append-only.

    A reassessment is a NEW LedgerEntry with `supersedes` pointing at the
    old entry_id — never an edit to the existing entry. See module
    docstring for why.
    """

    entry_id: str
    subject: str
    yield_components: tuple[YieldComponent, ...]
    cost_components: tuple[YieldComponent, ...]
    assessed_by: str
    computed_at: str = ""
    supersedes: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["yield_components"] = [c.to_dict() for c in self.yield_components]
        d["cost_components"] = [c.to_dict() for c in self.cost_components]
        return d


def net_reality_yield(entry: LedgerEntry) -> float:
    """Pure function: sum(yield values) - sum(cost values). No side effects."""
    total_yield = sum(c.value for c in entry.yield_components)
    total_cost = sum(c.value for c in entry.cost_components)
    return total_yield - total_cost


class RealityYieldLedger:
    """Append-only ledger of reality-yield assessments.

    No delete surface — no `delete`, `purge`, `clear`, or `remove` method
    exists on this class. An assessment, once recorded, stays recorded
    — including assessments with a negative net yield. The ledger's job
    is to record the truth, not to only accept good news.
    """

    def __init__(self) -> None:
        self._entries: dict[str, LedgerEntry] = {}
        # Recording order per subject, preserved even across supersession.
        self._by_subject: dict[str, list[str]] = {}

    def record(
        self,
        entry_id: str,
        subject: str,
        yield_components: Sequence[YieldComponent],
        cost_components: Sequence[YieldComponent],
        assessed_by: str,
        supersedes: str | None = None,
    ) -> LedgerEntry:
        if entry_id in self._entries:
            raise ValueError(f"entry '{entry_id}' already recorded")
        if not subject or not subject.strip():
            raise ValueError("a ledger entry requires a non-empty subject")
        if not assessed_by:
            raise ValueError("a ledger entry requires assessed_by")
        if not yield_components and not cost_components:
            raise ValueError(
                "an assessment with nothing recorded on either the yield "
                "side or the cost side is not an assessment."
            )
        for component in yield_components:
            if not component.is_yield():
                raise ValueError(
                    f"component '{component.name}' was passed as a yield "
                    f"component but is a cost-side name."
                )
        for component in cost_components:
            if not component.is_cost():
                raise ValueError(
                    f"component '{component.name}' was passed as a cost "
                    f"component but is a yield-side name."
                )
        if supersedes is not None and supersedes not in self._entries:
            raise KeyError(
                f"cannot supersede '{supersedes}': no such entry recorded"
            )

        now = datetime.now(timezone.utc).isoformat()
        entry = LedgerEntry(
            entry_id=entry_id,
            subject=subject,
            yield_components=tuple(yield_components),
            cost_components=tuple(cost_components),
            assessed_by=assessed_by,
            computed_at=now,
            supersedes=supersedes,
        )
        entry.history.append({
            "event": "RECORDED",
            "at": now,
            "assessed_by": assessed_by,
            "supersedes": supersedes,
            "net_reality_yield": net_reality_yield(entry),
        })
        self._entries[entry_id] = entry
        self._by_subject.setdefault(subject, []).append(entry_id)
        return entry

    def get(self, entry_id: str) -> LedgerEntry | None:
        return self._entries.get(entry_id)

    def recommendation(self, entry_id: str) -> str:
        """The literal three-way branch from governing directive §XI.

        Raises KeyError if entry_id isn't found — never silently defaults
        to any of the three outcomes.
        """
        entry = self._entries.get(entry_id)
        if entry is None:
            raise KeyError(f"no ledger entry '{entry_id}'")
        net = net_reality_yield(entry)
        if net > 0:
            return "CONTINUE_CAUTIOUSLY"
        if net == 0:
            return "HOLD_AND_REVIEW"
        return "THROTTLE_OR_TERMINATE"

    def history_for(self, subject: str) -> tuple[LedgerEntry, ...]:
        """Every entry ever recorded for `subject`, in recording order.

        Includes superseded entries — a subject's yield can be reassessed
        downward later and the earlier, more optimistic assessment must
        still be visible, not silently replaced.
        """
        ids = self._by_subject.get(subject, ())
        return tuple(self._entries[i] for i in ids)
