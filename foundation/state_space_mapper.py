"""
State-Space Mapper — bounded multi-dimensional decision-coordinate model
implementing `TITANOS_GO_CYCLE_DOCTRINE.md` §XI, "THE 999 STATE-SPACE
PRINCIPLE" (`foundation/MAPPING.md`'s `MAGL_005_999_STATE_SPACE_MAPPER`,
previously named but deferred: "No existing multi-dimensional
decision-coordinate model.").

WHAT §XI ACTUALLY ASKS FOR, AND ONLY THAT

    "Non-literal expandable possibility map. For significant decisions,
    consider as needed: time, scale, domain, actor, incentive, threat,
    uncertainty, evidence, consequence, intervention, recovery. Do not
    force every decision through every dimension — use the minimum
    required to reduce uncertainty. The purpose is navigation, not
    complexity for its own sake."

That sentence is the whole contract. It asks for a coordinate system a
caller can partially fill in, not a device that fills itself in, ranks
outcomes, or predicts anything. This module is deliberately just a
validated bag of named fields plus a comparison — nothing that reasons
about what the values *mean*.

WHY THIS IS NOT MAGL_004 (THE ORACLE SCENARIO ENGINE)

`foundation/MAPPING.md` separately names `MAGL_004_ORACLE_SCENARIO_
ENGINE` as still genuinely unbuilt: "multi-future generation with A/B/
C/D option branching." That module's job would be to *generate*
possibilities — given a state space, propose what could happen next.
This module's job stops one step earlier: it only lets a caller
*record* the coordinates of a decision they already have in mind. A
`StateSpaceMap` never produces a new value, never predicts a
consequence, never scores or ranks one map against another as "better."
Building prediction here — even something as small as "given these
dimensions, here is a likely next state" — would be exactly the scope
inflation §XI's own closing sentence warns against ("navigation, not
complexity for its own sake") and would silently duplicate work that
belongs to MAGL_004 once that module is actually built. If a future
change to this file starts producing new values rather than validating
caller-supplied ones, that change belongs in a different module.

WHY NO REQUIRED DIMENSIONS AND NO SCORE

§XI's own governing rule is "use the minimum required" — an empty
`StateSpaceMap` (zero dimensions declared) is therefore a legal, fully
formed instance, not an error: sometimes the minimum required to
navigate a decision is genuinely zero of these eleven axes. Similarly,
this module never assigns a similarity score, distance metric, or
ranking between two maps — doctrine explicitly distrusts collapsing a
multi-dimensional situation into one number for exactly this kind of
non-literal possibility map (see the sibling caution in
`TITANOS_PARETO_FRONTIER_RECURSION_ENGINE.md`: "never collapse verified
and projected value into one number"). `diff_state_spaces()` instead
returns the three literal, inspectable sets involved (shared-and-equal,
shared-but-different, present-in-only-one), so the caller decides what
the difference means — the module does not decide for them.

WHY UNKNOWN DIMENSION NAMES FAIL LOUDLY, NOT SILENTLY

A caller who types "tiem" instead of "time" has made a mistake, not
declared a twelfth dimension. Silently accepting it (as a new key) would
quietly expand the model per caller typo, which defeats the entire
point of a *fixed, closed* vocabulary; silently dropping it would hide
the mistake from the caller entirely. Both are worse than a loud
`ValueError` naming exactly which key was unrecognised — same fail-
closed-on-unknown discipline as `foundation/hells_gate.py`'s Prime Axiom
and `foundation/flow_switch.py`'s illegal-transition rejection.

WHY A DECLARED-BUT-EMPTY VALUE IS ALSO REJECTED

`build_state_space(scale="")` is not "I have nothing to say about
scale" — that case is already expressed correctly by simply omitting
`scale` entirely. A present key with an empty value is an ambiguous,
malformed declaration (did the caller mean to redact it? forget to fill
it in? pass through an empty template field?) and this module has no
way to distinguish those cases, so — same discipline as
`foundation/crystal.py`'s `_REQUIRED_NON_EMPTY` check on its own
required fields — it is rejected rather than guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

__all__ = [
    "DIMENSIONS",
    "StateSpaceMap",
    "UnknownDimensionError",
    "build_state_space",
    "StateSpaceDiff",
    "diff_state_spaces",
]

# ─────────────────────────────────────────────────────────────
# The fixed, closed vocabulary — TITANOS_GO_CYCLE_DOCTRINE.md §XI
# ─────────────────────────────────────────────────────────────

DIMENSIONS = frozenset({
    "time", "scale", "domain", "actor", "incentive", "threat",
    "uncertainty", "evidence", "consequence", "intervention", "recovery",
})


class UnknownDimensionError(ValueError):
    """Raised when a caller declares a dimension name outside the fixed
    eleven-name vocabulary. Carries the offending names so the caller
    (or a test) can inspect exactly what was rejected, not just that
    something was."""

    def __init__(self, unknown_keys: frozenset[str]) -> None:
        self.unknown_keys = unknown_keys
        super().__init__(
            f"unrecognised state-space dimension(s) {sorted(unknown_keys)} "
            f"— the fixed vocabulary is {sorted(DIMENSIONS)}. This is not "
            f"an extensible key set; a misspelled or novel dimension name "
            f"is rejected rather than silently accepted or dropped."
        )


@dataclass(frozen=True)
class StateSpaceMap:
    """An immutable, partial set of decision coordinates.

    `dimensions` holds only the axes the caller actually declared —
    never all eleven, never a required subset. Construct via
    `build_state_space()`, not directly, so the closed-vocabulary and
    non-empty-value invariants are enforced in exactly one place.
    """

    dimensions: Mapping[str, str]

    def to_dict(self) -> dict[str, str]:
        return dict(self.dimensions)

    def declared(self) -> frozenset[str]:
        """Which of the eleven dimension names this map actually declares."""
        return frozenset(self.dimensions.keys())


def build_state_space(**declared_dimensions: str) -> StateSpaceMap:
    """Validate and construct a `StateSpaceMap` from caller-supplied
    keyword dimensions.

    An empty call (`build_state_space()`) is legal and returns a map
    with zero declared dimensions — §XI's own "use the minimum
    required" rule means the minimum can legitimately be zero. Every
    supplied key must be one of the eleven fixed dimension names
    (`DIMENSIONS`); every supplied value must be a non-empty string
    after stripping whitespace.
    """
    unknown = frozenset(declared_dimensions) - DIMENSIONS
    if unknown:
        raise UnknownDimensionError(unknown)

    for key, value in declared_dimensions.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"state-space dimension '{key}' was declared but given an "
                f"empty value — omit the key entirely if there is nothing "
                f"to say about it; a declared-but-empty dimension is a "
                f"malformed declaration, not a legitimate 'no comment'."
            )

    return StateSpaceMap(dimensions=MappingProxyType(dict(declared_dimensions)))


@dataclass(frozen=True)
class StateSpaceDiff:
    """A literal, bounded comparison between two `StateSpaceMap`s.

    Deliberately not a similarity score or a ranking — see this module's
    module-level docstring for why. Each field is a plain set of
    dimension names; the caller decides what to make of them.
    """

    shared_equal: frozenset[str]
    shared_different: frozenset[str]
    only_in_first: frozenset[str]
    only_in_second: frozenset[str]

    def differs(self) -> bool:
        """True if the two maps disagree on any dimension — either by
        declaring a different value for the same dimension, or by one
        map declaring a dimension the other omits entirely."""
        return bool(self.shared_different or self.only_in_first or self.only_in_second)


def diff_state_spaces(first: StateSpaceMap, second: StateSpaceMap) -> StateSpaceDiff:
    """Compare two `StateSpaceMap`s dimension by dimension.

    Answers "does this decision differ from that one in a way that
    matters" honestly rather than with a synthetic similarity number:
    a dimension declared identically in both is `shared_equal`; declared
    in both with different values is `shared_different`; declared in
    only one map is `only_in_first` / `only_in_second`. A dimension
    neither map declares does not appear anywhere in the result — silence
    on a dimension is not a disagreement about it.
    """
    first_keys = first.declared()
    second_keys = second.declared()
    shared = first_keys & second_keys

    shared_equal = frozenset(
        key for key in shared if first.dimensions[key] == second.dimensions[key]
    )
    shared_different = shared - shared_equal

    return StateSpaceDiff(
        shared_equal=shared_equal,
        shared_different=shared_different,
        only_in_first=first_keys - second_keys,
        only_in_second=second_keys - first_keys,
    )
