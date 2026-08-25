"""
Foundation Switch Hardener — §IV/§V of the governing directive.

WHY THIS IS A THIN WRAPPER, NOT A NEW LIFECYCLE

§V's ten-gate hardening check ("has this lesson earned permanence?") and
kpm/promotion/state_machine.py's RAW -> ... -> STABLE lifecycle
("has this blueprint earned permanence?") are the same question asked
about two different kinds of artifact. This codebase has a documented,
repeated discipline of noticing that and reusing rather than duplicating
(see magl/BUILD_REPORT.md's reconnaissance section, and
rpa/gates/human_jurisdiction.py's identical wrapper pattern around the
same store). A lesson becomes a hardened switch by passing through
exactly the same RAW -> DISTILLED -> PROVISIONAL -> TESTED -> HUMAN_REVIEW
-> STABLE path, with the same non-self-promotion guarantee, as any other
promoted artifact in this repository.

WHAT IS GENUINELY NEW HERE

1. `run_hardening_gates()` — the ten specific questions from §V, which
   have no existing analog anywhere in this codebase (the closest,
   compiler/coverage.py, checks DOCTRINE CONSISTENCY against code that
   already exists; this checks whether a NEW candidate rule should exist
   at all).
2. `classify_hardened_switch()` — once a lesson reaches STABLE, which of
   the nine §IV categories (INVARIANT / GATE / CIRCUIT_BREAKER / ROUTER /
   DEFAULT / LEDGER_ENTRY / OPEN_QUESTION / DEPRECATED_PATH / MAGL) it
   becomes. "NOT EVERYTHING LEARNED IS A LAW" — this function forces an
   explicit choice rather than letting every hardened lesson default to
   the same category.

WHAT THIS FILE DOES NOT DO

It does not re-implement TRANSITIONS, SelfPromotionForbidden, or any
transition logic. All of that is imported from kpm.promotion.state_machine
unchanged. If that table's rules change, this file's behaviour changes
with it automatically — that's the point of reuse over duplication.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.promotion.state_machine import (  # noqa: E402
    PromotionRecord, PromotionStore, SelfPromotionForbidden, can_transition,
)

__all__ = [
    "GateFinding", "HardeningGateReport", "run_hardening_gates",
    "SWITCH_CATEGORIES", "classify_hardened_switch",
    "advance_to_tested", "harden",
]

# ── §V — the ten hardening gates ────────────────────────────────────────

GATE_NAMES = (
    "PROVENANCE", "EVIDENCE", "FALSIFIABILITY", "SCOPE", "FAILURE_MODE",
    "REVERSIBILITY", "RED_TEAM", "REALITY_YIELD", "DUPLICATION_CHECK",
    "HUMAN_AGENCY",
)


@dataclass
class GateFinding:
    gate: str
    passed: bool
    detail: str


@dataclass
class HardeningGateReport:
    subject: str
    findings: list[GateFinding] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(f.passed for f in self.findings)

    @property
    def failed_gates(self) -> tuple[str, ...]:
        return tuple(f.gate for f in self.findings if not f.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "all_passed": self.all_passed,
            "failed_gates": list(self.failed_gates),
            "findings": [{"gate": f.gate, "passed": f.passed, "detail": f.detail}
                        for f in self.findings],
        }


def run_hardening_gates(
    subject: str, *,
    provenance: str, evidence: tuple[str, ...],
    falsifiability_condition: str, scope: tuple[str, ...],
    failure_mode: str, reversible: bool,
    red_team_argument: str, reality_yield_positive: bool,
    duplicate_of: str | None, reduces_human_agency: bool,
) -> HardeningGateReport:
    """Run the ten §V gates as explicit, individually-named checks.

    Every gate answer is supplied by the caller as declared fact — this
    function does not go looking for evidence or run a red-team pass
    itself, the same boundary every validator in this codebase holds
    (a schema checks shape/consistency of DECLARED fields; it does not
    manufacture the fields it checks). A caller who fabricates a "PASS"
    answer defeats this the same way a caller can fabricate any declared
    field anywhere else in this codebase — the honesty of the inputs is
    outside this function's power to enforce, and it does not pretend
    otherwise.
    """
    findings = [
        GateFinding("PROVENANCE", bool(provenance),
                   provenance or "no provenance declared"),
        GateFinding("EVIDENCE", len(evidence) > 0,
                   f"{len(evidence)} evidence item(s)"),
        GateFinding("FALSIFIABILITY", bool(falsifiability_condition),
                   falsifiability_condition or "no falsification condition declared"),
        GateFinding("SCOPE", len(scope) > 0,
                   f"{len(scope)} scope entries" if scope else "no scope declared — "
                   "an unscoped rule is a global rule, which is a much larger "
                   "claim than most lessons earn"),
        GateFinding("FAILURE_MODE", bool(failure_mode),
                   failure_mode or "no over-application failure mode declared"),
        GateFinding("REVERSIBILITY", True, "reversible" if reversible
                   else "IRREVERSIBLE — passes this gate but the fact is carried "
                        "forward, not hidden; irreversibility raises the bar on "
                        "every other gate rather than blocking on its own"),
        GateFinding("RED_TEAM", bool(red_team_argument),
                   red_team_argument or "no red-team argument against installation "
                                        "was generated"),
        GateFinding("REALITY_YIELD", reality_yield_positive,
                   "positive reality yield" if reality_yield_positive
                   else "reality yield not positive — see foundation/"
                        "reality_yield_ledger.py for the actual computation"),
        GateFinding("DUPLICATION_CHECK", duplicate_of is None,
                   "no duplicate found" if duplicate_of is None
                   else f"duplicates existing rule: {duplicate_of}"),
        GateFinding("HUMAN_AGENCY", not reduces_human_agency,
                   "does not reduce human agency" if not reduces_human_agency
                   else "reduces unnecessary human choice or creates forced "
                        "dependence"),
    ]
    return HardeningGateReport(subject=subject, findings=findings)


# ── §IV — the nine switch categories ────────────────────────────────────

SWITCH_CATEGORIES = frozenset({
    "INVARIANT", "GATE", "CIRCUIT_BREAKER", "ROUTER", "DEFAULT",
    "LEDGER_ENTRY", "OPEN_QUESTION", "DEPRECATED_PATH", "MAGL",
})


class UnrecognisedSwitchCategory(Exception):
    pass


def classify_hardened_switch(store: PromotionStore, subject_id: str,
                             category: str) -> str:
    """Assign one of the nine §IV categories to a subject that has
    reached STABLE. Refuses to classify anything not yet STABLE — a
    category assigned before hardening completed would be exactly the
    self-certification pattern this codebase's history exists to catch.

    Returns the category on success. Does not mutate the PromotionStore
    (category assignment is a caller-side concern; this function's only
    job is to gate the assignment on the subject's REAL state, re-read
    from the store rather than trusted from a caller's claim).
    """
    if category not in SWITCH_CATEGORIES:
        raise UnrecognisedSwitchCategory(
            f"'{category}' is not one of {sorted(SWITCH_CATEGORIES)} — "
            f"NOT EVERYTHING LEARNED IS A LAW; an unrecognised category is "
            f"refused, never defaulted to the nearest-sounding one."
        )
    record = store.get(subject_id)
    if record is None or record.state != "STABLE":
        raise ValueError(
            f"'{subject_id}' has not reached STABLE "
            f"(current: {record.state if record else 'not registered'}) — "
            f"a switch cannot be categorised before it has been hardened."
        )
    return category


# ── Convenience: drive a lesson through the real lifecycle ─────────────

def advance_to_tested(store: PromotionStore, subject_id: str, *,
                      created_by: str) -> PromotionRecord:
    """RAW -> DISTILLED -> PROVISIONAL -> TESTED, the ordinary forward
    path, unchanged from kpm/promotion/state_machine.py's own rules."""
    store.promote(subject_id, "DISTILLED", reason="abstraction identified",
                 created_by=created_by)
    store.promote(subject_id, "PROVISIONAL", reason="scoped and evidenced")
    return store.promote(subject_id, "TESTED", reason="hardening gates run")


def harden(store: PromotionStore, subject_id: str, *,
          gate_report: HardeningGateReport, reviewed_by: str,
          created_by: str) -> PromotionRecord:
    """TESTED -> STABLE, but ONLY if every §V gate passed. This is the
    actual enforcement point: `run_hardening_gates()` can be called by
    anyone and produce any report, but this function is what a caller
    must go through to actually harden something, and it refuses outright
    if `gate_report.all_passed` is False — a caller cannot promote past a
    failed gate by simply not checking the report first.

    self_promotion (reviewed_by == created_by) is refused by the
    underlying store exactly as for any other promotion — that guarantee
    is inherited, not re-implemented.
    """
    if not gate_report.all_passed:
        raise ValueError(
            f"cannot harden '{subject_id}': failed gates "
            f"{gate_report.failed_gates} — per §V, return this lesson to "
            f"QUARANTINE, HYPOTHESIS, EXPERIMENT, or OPEN_QUESTION instead."
        )
    return store.promote(subject_id, "STABLE", reason="all ten hardening gates passed",
                         reviewed_by=reviewed_by)
