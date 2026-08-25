"""
CT_141 Low-Regret Engine — minimax-regret selection over declared options.

THE AXIOM

    REGRET(option) = BEST ACHIEVABLE WORST CASE - THIS OPTION'S WORST CASE

`TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md` §IX (ARE — Auto
Recommendation Engine) names four option archetypes a recommendation
must generate: **A** highest lever, **B** fastest reality test, **C**
lowest regret, **D** do nothing / preserve optionality. Every other
archetype in that list already has a home elsewhere in this codebase
(lever ranking, reality-yield accounting, the switch/quarantine
machinery that lets "do nothing" be a first-class, inspectable choice).
"Lowest regret" did not — `foundation/MAPPING.md`'s
`MAGL_CT141_004_LOW_REGRET_ENGINE` entry named it and deferred it,
because picking a "lowest-regret action" is not a schema question, it
is a decision-theory question. This module is the answer: an honest,
textbook implementation of **minimax regret**, not an invented
heuristic that merely sounds like it.

WHY MINIMAX REGRET AND NOT EXPECTED VALUE

Expected-value maximisation is the correct choice rule when you trust
your probability estimates over the option space. This doctrine set
repeatedly does not extend that trust — see `flow_switch.py`'s axiom
that confidence and speed are not the same signal, and the CT_141
defusal override's refusal to let urgency stand in for verification.
Minimax regret is the standard decision rule for exactly that
condition: when you do not have (or do not trust) a probability
distribution over which future actually arrives, and you would rather
bound how bad your worst mistake can be than maximise a number you are
not confident you calculated honestly. It is a real, well-known
concept from decision theory under uncertainty (Savage, 1951) — not a
project-specific invention.

THE REGRET FORMULA, EXACTLY

For a set of candidate options, each with a caller-declared
`worst_case_value` (the outcome if this option is chosen and things go
as badly as the caller believes is plausible):

    best_worst_case = max(c.worst_case_value for c in candidates)
    regret(c)        = best_worst_case - c.worst_case_value

This is the standard minimax-regret construction applied to the
worst-case column of the payoff table (rather than to a full
state-by-state payoff matrix, which this module does not have — the
caller declares one worst case per option, not a worst case per
possible future state). `regret(c) >= 0` always, because
`best_worst_case` is itself one of the `worst_case_value`s in the set.
The selected option is the one with the smallest regret — equivalently,
the option whose own worst case is closest to the best worst case
achievable across all options on the table. This is the "least bad if
I'm wrong" reading of lowest-regret from §IX, made computable.

WHAT THIS MODULE DOES NOT DO

It does not compute `expected_value` or `worst_case_value` — those are
caller-declared inputs, exactly like `PanicSample.information_velocity`
and `verification_velocity` in `flow_switch.py`: this module reasons
about declared numbers, it does not measure or estimate anything
itself. It does not touch cost/yield accounting —
`foundation/reality_yield_ledger.py` already owns that, and duplicating
it here would create two competing places to ask "what did this cost."
This module answers one question only: given already-summarised
options, which one minimises worst-case regret.

TIE-BREAK: REVERSIBILITY, NEVER EXPECTED VALUE

When two or more candidates tie on regret, the tie is broken by
preferring the more reversible option — matching this doctrine set's
repeated preference for reversible action under uncertainty (CT_141
defusal override: "prefer reversible action"; §IX's own archetype D,
"do nothing / preserve optionality"). It is deliberately NOT broken by
preferring the higher `expected_value`: that would silently reintroduce
expected-value maximisation as the real tie-break rule, defeating the
entire reason a caller chose minimax regret over EV maximisation in the
first place. If reversibility also ties, the tie is left visible in
the result (`tied_with`) rather than resolved by an arbitrary rule the
caller did not ask for — fail-closed means surfacing an unresolved tie,
not quietly picking one.

FAIL-CLOSED ON EMPTY INPUT

An empty candidate list cannot produce a `best_worst_case`, so there is
no regret to compute and no honest answer to "which is lowest regret."
`select_lowest_regret` raises `ValueError` rather than returning `None`
or crashing on an unguarded `max()` — a bare `ValueError: max() arg is
an empty sequence` would tell a caller nothing about which invariant
they violated.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Sequence

__all__ = [
    "Confidence",
    "Candidate",
    "CandidateRegret",
    "LowRegretDecision",
    "select_lowest_regret",
]

# Ordered low -> high only for display/validation purposes; regret
# selection itself never uses this ordering as a tie-break signal.
Confidence = str
ALL_CONFIDENCE_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH"})

# Regret is a subtraction of two caller-declared floats; exact equality
# on subtracted floats is a known correctness trap (e.g. worst_case
# values of 0.1+0.2 vs 0.3 produce regrets 0.0 and 5.55e-17 -- a real
# tie that exact `==` would miss). Found by adversarial review
# (2026-08-26). This tolerance is deliberately tiny -- it exists only
# to absorb floating-point representation error, not to treat genuinely
# different regret values (e.g. differing by 0.01) as tied.
REGRET_TIE_EPSILON = 1e-9


@dataclass(frozen=True)
class Candidate:
    """One caller-declared option on the decision table.

    This module does not derive `expected_value` or `worst_case_value`
    from anything — both are supplied by the caller, matching
    `PanicSample`'s "caller declares, module reasons" boundary. Neither
    is validated for plausibility (this module has no independent way
    to check a caller's belief about what could go wrong); it is
    validated only for internal consistency (see `__post_init__`).

    `reversibility`: True if choosing this option and later discovering
    it was wrong can be undone without unrecoverable loss. This is the
    tie-break signal, not a component of the regret calculation itself
    — two options can have identical regret while differing sharply in
    how expensive it is to walk away from a bad outcome, and that
    difference should decide the tie.
    """
    name: str
    expected_value: float
    worst_case_value: float
    reversibility: bool
    confidence: Confidence

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Candidate.name must be non-empty.")
        if self.confidence not in ALL_CONFIDENCE_LEVELS:
            raise ValueError(
                f"Candidate '{self.name}' has unrecognised confidence "
                f"'{self.confidence}'; must be one of "
                f"{sorted(ALL_CONFIDENCE_LEVELS)}."
            )
        if self.worst_case_value > self.expected_value:
            # Fail-closed on an internally inconsistent declaration: a
            # "worst case" that is better than the "expected" outcome
            # is not a worst case by definition, and letting it through
            # would silently corrupt the regret computation with a
            # caller-side labelling error this module has no way to
            # detect later.
            raise ValueError(
                f"Candidate '{self.name}' declares worst_case_value "
                f"({self.worst_case_value}) greater than expected_value "
                f"({self.expected_value}); worst case cannot exceed "
                f"expected case."
            )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateRegret:
    """One candidate's full regret computation, kept for inspection.

    `LowRegretDecision.all_regrets` carries one of these per candidate
    so the decision is auditable — a caller can see every option's
    regret score, not just the winner's, which is the entire point of
    making this a structured result instead of returning a bare name.
    """
    name: str
    worst_case_value: float
    regret: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LowRegretDecision:
    """The full, inspectable outcome of a minimax-regret selection.

    `tied_with` is non-empty only when the minimum-regret candidate
    could not be uniquely resolved even after the reversibility
    tie-break — it lists the names of the other candidates still tied
    with `selected.name` at that point, so the caller (a human, per
    this doctrine's tie-break-visibility rule) can make the final call
    rather than have it made silently.
    """
    selected: CandidateRegret
    best_worst_case: float
    all_regrets: list[CandidateRegret] = field(default_factory=list)
    tied_with: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected": self.selected.to_dict(),
            "best_worst_case": self.best_worst_case,
            "all_regrets": [r.to_dict() for r in self.all_regrets],
            "tied_with": list(self.tied_with),
        }


def select_lowest_regret(
    candidates: Sequence[Candidate],
) -> LowRegretDecision:
    """Select the candidate minimising minimax regret.

    regret(c) = max(worst_case_value across all candidates) -
                c.worst_case_value

    The candidate with the smallest regret is selected. Ties on regret
    are broken by preferring `reversibility=True` over `False` — never
    by preferring higher `expected_value`, which would silently swap in
    expected-value maximisation as the real decision rule (see module
    docstring). If a tie survives the reversibility tie-break, the
    first candidate (by input order) among the tied set is returned as
    `selected`, and every other name still tied with it is listed in
    `tied_with` so the ambiguity is visible rather than hidden.

    Raises `ValueError` on an empty `candidates` sequence — there is no
    `best_worst_case` to compute and therefore no honest selection to
    make. Also raises `ValueError` on duplicate `Candidate.name` values
    — `CandidateRegret`/`tied_with` identify candidates by name only
    (found by adversarial review, 2026-08-26: with duplicate names a
    caller cannot tell which physical candidate won, and a genuine tie
    between two same-named candidates would render `tied_with`
    self-referential).
    """
    if not candidates:
        raise ValueError(
            "select_lowest_regret requires at least one candidate; an "
            "empty option set has no best-worst-case to compute regret "
            "against."
        )

    names = [c.name for c in candidates]
    if len(names) != len(set(names)):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(
            f"select_lowest_regret requires unique Candidate.name values "
            f"-- duplicated: {dupes}. Results are identified by name; "
            f"duplicates make the winner and any tie ambiguous."
        )

    best_worst_case = max(c.worst_case_value for c in candidates)

    all_regrets = [
        CandidateRegret(
            name=c.name,
            worst_case_value=c.worst_case_value,
            regret=best_worst_case - c.worst_case_value,
        )
        for c in candidates
    ]

    min_regret = min(r.regret for r in all_regrets)
    tied_idx = [
        i for i, r in enumerate(all_regrets)
        if abs(r.regret - min_regret) <= REGRET_TIE_EPSILON
    ]

    if len(tied_idx) == 1:
        winner_idx = tied_idx[0]
        tied_with: list[str] = []
    else:
        reversible_idx = [i for i in tied_idx if candidates[i].reversibility]
        pool_idx = reversible_idx if reversible_idx else tied_idx
        winner_idx = pool_idx[0]
        tied_with = [candidates[i].name for i in pool_idx if i != winner_idx]

    return LowRegretDecision(
        selected=all_regrets[winner_idx],
        best_worst_case=best_worst_case,
        all_regrets=all_regrets,
        tied_with=tied_with,
    )
