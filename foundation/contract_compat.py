"""Contract compatibility check — the one real primitive this repo was
missing for "can capability A's output satisfy capability B's input,"
per the Demonblade Genome directive (2026-08-27).

WHAT THIS IS

A `Contract` names what a capability structurally produces (a set of
top-level field/key names) and what a downstream capability structurally
requires. `check_compatible()` answers exactly one question: does the
producer's field set cover the consumer's required set? Nothing about
types, semantics, or runtime values — a structural presence check, nothing
more.

WHAT THIS IS NOT

Not a capability registry. Not an auto-wiring engine. Not a discovery
service that searches a graph of capabilities for compatible pairs. Not
a sandbox/execution harness. All of those were the large, speculative
parts of the source directive — this repo has zero real consumer for any
of them (same verdict this session has reached every time a generic
capability graph / lever registry / YGGDRASIL-shaped subsystem was
proposed: dominated by nothing, because nothing calls it). What follows
is only the one small, real, testable predicate the directive's own
§XIII Pareto test asks for ("one real compatibility function over a
theoretical evolution platform"), demonstrated against a real historical
bug in this repository, not a synthetic example.

THE REAL BUG THIS REPRODUCES

Cycle 2 of this session's build history (see `PARETO_FRONTIER.md`
`FRONTIER-WORLD-PING-SLICE`) ingested `rpa/fixtures/bottleneck.yaml`
(top-level key `institutional_bottleneck`) as the content for
`rpa.gates.human_jurisdiction.authorize_pilot()`, which actually requires
content shaped like `rpa/fixtures/automation_candidate.yaml` (top-level
key `automation_candidate`, validated by
`rpa.validators.validate_automation_candidate`). The mismatch was only
caught by a human/model noticing the gate's real requirement — a
structural compatibility check run *before* attempting the call would
have caught it mechanically, for free. This module is that check.

CORRECTION (2026-08-27, same day this module was built): re-examined
whether `check_compatible()` should be wired live into
`authorize_pilot()` at that call site. It should not be —
`authorize_pilot()` already runs `validate_automation_candidate()` fresh
on every declared source hash and raises `NoValidatedSource` if none
validate (a guard this session added independently, per that function's
own docstring, closing this exact gap already). That check is strictly
stronger than this module's (full `REQUIRED_TOP_FIELDS` + nested
structure, not just top-level-key presence). Wiring `check_compatible()`
in there would duplicate enforcement, not add any. This module's real
historical demo remains correct and useful as a demonstration of the
compatibility-predicate concept; it is not a currently-needed live
guard, and stays available heredity — dormant, verified, reusable if a
real *unguarded* consumer ever needs exactly this shape of check.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

__all__ = [
    "Contract",
    "CompatibilityResult",
    "check_compatible",
    "contract_from_top_level_keys",
]


@dataclass(frozen=True)
class Contract:
    """What a capability structurally produces or requires.

    `produces` and `requires` are sets of top-level field/key names —
    this says nothing about types or values. A capability that only
    consumes (never produces) declares `produces=frozenset()`; one that
    only produces declares `requires=frozenset()`.
    """

    name: str
    produces: frozenset[str]
    requires: frozenset[str]


@dataclass(frozen=True)
class CompatibilityResult:
    """The receipt: whether a producer's declared output satisfies a
    consumer's declared input, and — if not — exactly what's missing."""

    compatible: bool
    missing: frozenset[str]
    reason: str


def check_compatible(producer: Contract, consumer: Contract) -> CompatibilityResult:
    """Does `producer` structurally satisfy `consumer`'s requirements?

    This finds a HYPOTHESIS, not an authorization — a COMPATIBLE result
    means "the declared shapes line up," never "safe to call," never
    "authorized." Nothing here checks preconditions, permissions, side
    effects, or semantics; those remain the caller's responsibility,
    same as every other structural-only check in this repository.
    """
    missing = consumer.requires - producer.produces
    if missing:
        return CompatibilityResult(
            compatible=False,
            missing=frozenset(missing),
            reason=(
                f"{producer.name!r} does not produce {sorted(missing)}, "
                f"required by {consumer.name!r}"
            ),
        )
    return CompatibilityResult(
        compatible=True,
        missing=frozenset(),
        reason=f"{producer.name!r} satisfies {consumer.name!r}'s declared requirements",
    )


def contract_from_top_level_keys(name: str, data: Mapping, *, requires: frozenset[str] = frozenset()) -> Contract:
    """Build a `Contract` from an already-parsed mapping's top-level keys
    (e.g. a YAML document loaded with `yaml.safe_load`). Read-only —
    never parses the file itself, so this stays independent of which
    YAML/JSON loader a caller uses."""
    produces = frozenset(data.keys()) if isinstance(data, Mapping) else frozenset()
    return Contract(name=name, produces=produces, requires=requires)
