"""
Discovery Authorization — the canonical, machine-readable object that
arms `foundation/communication_gate.py`'s `CommunicationSwitch` for
bounded, read-only external discovery, per Kyle's explicit standing
authorization (2026-08-27, recorded verbatim below and in
`HUMAN_DECISIONS.md`).

WHY THIS FILE EXISTS RIGHT NOW, NOT HYPOTHETICALLY

The prior HOLD→DISCOVER recon (this same day) found the real blocker
was never "discovery is technically impossible" — `communication_gate.py`
already had a complete, fail-closed switch model, `SourceRegistry.
ingest_source()` already had a complete provenance/admission path, and
`mouth_common.py` already had a proven fetch→parse→hash→observe shape.
The actual gap was narrower: human intent had never been turned into a
`CommunicationSwitch` instance the gate could evaluate — an English
paragraph is not "evidence" in the sense `evaluate()` checks for.

THIS FILE DOES NOT PERFORM ANY NETWORK I/O AND DOES NOT BUILD A FETCHER.
It does exactly two things: (1) represents Kyle's standing authorization
as real `CommunicationSwitch` objects so `authorize_communication()` can
actually evaluate them instead of a caller re-typing the same claim by
hand each time, and (2) bounds *how* discovery may run once armed
(`DiscoveryPolicy` — objective, budget, stop conditions) — a concern
`CommunicationSwitch` deliberately does not cover, since "who authorized
what scope" and "how much of it may one discovery attempt consume" are
independent questions.

STATUS CORRECTION 2026-09-01. The paragraph here previously read
"Nothing in this repository calls a real fetcher based on either — the
door is armed, but no fetcher/adapter exists yet." That became false
once the mouths were built, and it stayed in the file for several
cycles while `mouth_common.fetch_feed()` opened real sockets beside a
gate that nothing consulted. The claim was load-bearing in the worst
way: it is the reason the gap went unnoticed, because the file
documenting the door insisted there was no door.

Now accurate: `mouth_common.fetch_feed()` calls `authorize_discovery()`
before every request and refuses outright without a policy. This module
still performs no network I/O itself -- that separation is the point,
and it is enforced by a test that reads this module's real imports.

SCOPE OF THE STANDING AUTHORIZATION (verbatim from Kyle, 2026-08-27)

READ_URL and READ_API only, publicly accessible sources only (GitHub
repos, documentation, package registries, public APIs), no
login-required systems, no private data, no credential acquisition, no
privilege escalation, no financial transactions, no paid API usage
without separate explicit authorization, no autonomous code execution
from fetched content, no autonomous dependency installation from
discovery results, no autonomous scope expansion beyond the active
verified question. RECEIVE_WEBHOOK was never authorized and is not
represented here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from foundation.communication_gate import (
    CommunicationDenied,
    CommunicationSwitch,
    authorize_communication,
)

__all__ = [
    "STANDING_AUTHORIZED_BY", "STANDING_AUTHORIZATION_NOTE",
    "STANDING_AUTHORIZED_SCOPES", "FORBIDDEN_OBJECTIVE_PHRASES",
    "DEFAULT_MAX_QUERIES", "DEFAULT_MAX_WALL_CLOCK_SECONDS",
    "DEFAULT_MAX_RESULTS",
    "DiscoveryPolicy", "UnboundedDiscoveryObjective",
    "standing_switch_for", "authorize_discovery",
]

STANDING_AUTHORIZED_BY = "Kyle Graham"
STANDING_AUTHORIZATION_NOTE = (
    "bounded, read-only external discovery for the purpose of resolving "
    "verified INPUT_STARVED holds and verified repository capability "
    "gaps; publicly accessible sources only; no login-required systems, "
    "private data, credentials, privilege escalation, financial "
    "transactions, or paid API usage without separate explicit "
    "authorization; no autonomous code execution or dependency "
    "installation from discovery results; no autonomous scope expansion "
    "beyond the active verified question (2026-08-27)"
)

# RECEIVE_WEBHOOK deliberately excluded — never authorized.
STANDING_AUTHORIZED_SCOPES = frozenset({"READ_URL", "READ_API"})

# A discovery objective must name a concrete question, not a mandate to
# wander. These are the literal anti-patterns Kyle's own authorization
# named as never valid — checked as a substring match against a
# lowercased objective, same "narrow and imperfect, better than nothing"
# discipline as reality_yield_ledger.py's forward-looking-word blocklist.
FORBIDDEN_OBJECTIVE_PHRASES = (
    "anything interesting",
    "keep searching",
    "make the bot smarter",
    "make the system smarter",
)

# The phrase list above is exact-match and can only ever catch what
# somebody already thought of. Found by attacking this module after
# wiring it to a real socket: the objective "find everything" passed
# validation and reached `urlopen`, failing only on DNS. That is the
# blocklist's structural weakness, not a missing entry -- adding
# "find everything" to the tuple would leave "search the web",
# "explore", "look around" and every future phrasing open.
#
# This is the complementary STRUCTURAL check. An objective whose object
# is an unbounded universal quantifier is unbounded by construction,
# whatever words surround it, and that is a property of the string
# rather than a guess about its meaning.
#
# It is deliberately conservative. A network gate's correct failure
# direction is refusal, and an objective wrongly refused costs one
# rewording, while one wrongly allowed costs an unbounded fetch. This
# still does not make the check complete -- no string test can confirm
# an objective is concrete, only that it is not obviously not.
_UNBOUNDED_QUANTIFIER = re.compile(
    r"\b(everything|anything|all the things|whatever|as much as (you |i )?can|"
    r"any and all|the (whole|entire) (web|internet)|the web|the internet)\b",
    re.I)

DEFAULT_MAX_QUERIES = 5
DEFAULT_MAX_WALL_CLOCK_SECONDS = 60
DEFAULT_MAX_RESULTS = 10


class UnboundedDiscoveryObjective(ValueError):
    """Raised when a DiscoveryPolicy's objective is empty or matches a
    known-generic anti-pattern — 'search for anything interesting' is
    not an authorizable discovery objective, per Kyle's own standing
    authorization text."""


@dataclass(frozen=True)
class DiscoveryPolicy:
    """Bounds one discovery attempt. Independent of `CommunicationSwitch`
    — WHO authorized WHAT SCOPE (the switch) is a different question
    from HOW MUCH one attempt may consume (this). Both are required
    before `authorize_discovery()` succeeds."""

    objective: str                                    # required, concrete — see UnboundedDiscoveryObjective
    requested_scope: str                               # must be in STANDING_AUTHORIZED_SCOPES
    max_queries: int = DEFAULT_MAX_QUERIES
    max_wall_clock_seconds: int = DEFAULT_MAX_WALL_CLOCK_SECONDS
    max_results: int = DEFAULT_MAX_RESULTS
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective, "requested_scope": self.requested_scope,
            "max_queries": self.max_queries,
            "max_wall_clock_seconds": self.max_wall_clock_seconds,
            "max_results": self.max_results, "created_at": self.created_at,
        }


def _validate_objective(objective: str) -> None:
    text = objective.strip()
    if not text:
        raise UnboundedDiscoveryObjective(
            "DiscoveryPolicy.objective is empty — 'search for anything' "
            "is not an authorizable discovery objective"
        )
    lowered = text.lower()
    for phrase in FORBIDDEN_OBJECTIVE_PHRASES:
        if phrase in lowered:
            raise UnboundedDiscoveryObjective(
                f"objective {text!r} matches forbidden generic pattern "
                f"{phrase!r} — a discovery objective must name a "
                f"concrete question, not a mandate to wander"
            )
    quantifier = _UNBOUNDED_QUANTIFIER.search(text)
    if quantifier:
        raise UnboundedDiscoveryObjective(
            f"objective {text!r} contains the unbounded quantifier "
            f"{quantifier.group(0)!r} — an objective whose object is "
            f"'everything' is unbounded by construction, however it is "
            f"phrased. Name the specific subject to be observed."
        )


def standing_switch_for(requested_scope: str) -> CommunicationSwitch:
    """Build the CommunicationSwitch representing Kyle's standing
    authorization for one scope. Does not evaluate or authorize
    anything by itself — `authorize_discovery()` still runs it through
    the real `communication_gate.py` two-point enforcement."""
    return CommunicationSwitch(
        requested_scope=requested_scope,
        human_authorized_by=STANDING_AUTHORIZED_BY,
        human_authorization_note=STANDING_AUTHORIZATION_NOTE,
        reversibility_acknowledged=True,
    )


def authorize_discovery(policy: DiscoveryPolicy) -> bool:
    """The one real entry point a future discovery adapter must call
    before doing anything. Validates the objective is concrete (raises
    UnboundedDiscoveryObjective otherwise), confirms the requested scope
    is within Kyle's standing authorization (raises CommunicationDenied
    otherwise — RECEIVE_WEBHOOK or any unlisted scope is refused here,
    before it would even reach communication_gate.py), then re-derives
    authorization from the real switch via `authorize_communication()`
    — never trusts a cached flag. Performs no I/O itself.

    A fetcher DOES now consume this: `mouth_common.fetch_feed()` calls
    this function immediately before `urlopen`, and refuses to open a
    socket at all when no policy is supplied. This docstring previously
    said the opposite; see the module docstring's status correction."""
    _validate_objective(policy.objective)
    if policy.requested_scope not in STANDING_AUTHORIZED_SCOPES:
        raise CommunicationDenied(
            f"requested_scope {policy.requested_scope!r} is not within "
            f"Kyle's standing authorization {sorted(STANDING_AUTHORIZED_SCOPES)} "
            f"— RECEIVE_WEBHOOK and any other scope require a separate, "
            f"explicit authorization"
        )
    switch = standing_switch_for(policy.requested_scope)
    return authorize_communication(switch)
