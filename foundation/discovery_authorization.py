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

import hashlib
import json
import re
import time
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
    "DiscoveryBudgetExhausted", "spend_query", "budget_spent",
    "reset_budgets",
    "DiscoveryBudgetExhausted", "spend_query", "budget_spent",
    "reset_budgets",
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

# The regex above matches bare quantifier PRONOUNS only, and the comment
# above it claimed an objective containing an unbounded quantifier was
# caught "however it is phrased". That was false, and an independent
# adversarial review broke it with five strings that all passed:
#
#   "download every release across every repository on github"
#   "collect all public github repos matching *"
#   "mirror the full github issue tracker"
#   "monitor every repo in this github org"
#   "crawl each page under this domain"
#
# Each is "search everything" in substance. A quantifier applied to a
# NOUN is invisible to a pronoun-only pattern, which is the whole class
# the first version missed.
#
# This second pattern catches a quantifier ranging over a CLASS of
# things rather than a named instance. It is deliberately conservative:
# a network gate's correct failure direction is refusal, and a wrongly
# refused objective costs one rewording while a wrongly allowed one
# costs an unbounded crawl.
#
# It still cannot be complete. "every release of numpy" is bounded by
# numpy and would be refused here; that is an accepted false positive,
# not a claim of precision. No string test can confirm an objective is
# bounded -- only that it is not obviously unbounded.
_QUANTIFIED_CLASS = re.compile(
    r"\b(every|each|all|any|the\s+(full|entire|whole|complete))\s+"
    r"(?:\w+\s+){0,3}?"
    r"(repo|repos|repositor(?:y|ies)|packages?|projects?|pages?|sites?|"
    r"domains?|orgs?|organi[sz]ations?|users?|accounts?|issues?|"
    r"releases?|files?|endpoints?|records?|feeds?)\b",
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
            f"'everything' is unbounded by construction. Name the "
            f"specific subject to be observed."
        )
    quantified = _QUANTIFIED_CLASS.search(text)
    if quantified:
        raise UnboundedDiscoveryObjective(
            f"objective {text!r} quantifies over a class of things "
            f"({quantified.group(0)!r}) rather than naming an instance. "
            f"'every repository', 'all packages' and 'the full issue "
            f"tracker' are unbounded however they are worded. Name the "
            f"specific subject to be observed."
        )



# ─────────────────────────────────────────────────────────────
# BUDGET ENFORCEMENT
#
# `max_queries`, `max_wall_clock_seconds` and `max_results` were
# declared on DiscoveryPolicy, serialised by to_dict(), and read by
# NOTHING. An independent adversarial review grepped the whole
# repository and found zero consumers. Meanwhile `fetch_feed()`'s own
# docstring told callers a policy "names a concrete objective and
# budget" -- so the gate advertised a limit it did not have, which is
# the switch-that-does-nothing defect this repository's own doctrine
# calls out by name.
#
# THE SCOPE IS PER-PROCESS, AND THAT IS STATED RATHER THAN IMPLIED.
# The ledger below lives in module memory, so the budget covers one
# Python process. That genuinely matches how this repository fetches:
# `cron_pulse.py` is a cron entry, so every tick is a fresh process
# with a fresh budget, and the limit constrains a runaway loop inside
# one run -- which is the failure this is for. It does NOT constrain
# total requests per hour across many cron ticks; that is what
# GitHub's own rate limit does, and pretending otherwise would be a
# second false claim in the same place as the first.
# ─────────────────────────────────────────────────────────────

class DiscoveryBudgetExhausted(CommunicationDenied):
    """A policy's declared budget was spent. Subclasses CommunicationDenied
    so a caller that already handles refusal handles this too, and so no
    existing caller can accidentally treat exhaustion as success."""


def _policy_key(policy: "DiscoveryPolicy") -> str:
    """Identity by declared content, not by object id.

    Two policies naming the same objective and budget are the same
    authorization however many times they are constructed -- otherwise a
    caller could reset its own budget just by building a fresh instance
    in a loop, which is the exact bypass this is meant to close.
    """
    return hashlib.sha256(json.dumps({
        "objective": policy.objective.strip().lower(),
        "requested_scope": policy.requested_scope,
        "max_queries": policy.max_queries,
        "max_wall_clock_seconds": policy.max_wall_clock_seconds,
    }, sort_keys=True).encode()).hexdigest()[:16]


# key -> [queries_spent, first_spend_monotonic]
_BUDGET_LEDGER: dict[str, list] = {}


def spend_query(policy: "DiscoveryPolicy", now: "float | None" = None) -> int:
    """Charge one request against a policy. Raises when the budget is out.

    Called by `mouth_common.fetch_feed()` immediately after
    authorization and BEFORE the socket opens, so an exhausted budget
    costs no request. Returns the number spent including this one.

    `now` is injectable for tests; production uses a monotonic clock so
    a system clock adjustment cannot extend or collapse a window.
    """
    key = _policy_key(policy)
    current = time.monotonic() if now is None else now
    entry = _BUDGET_LEDGER.setdefault(key, [0, current])
    spent, started = entry

    elapsed = current - started
    if elapsed > policy.max_wall_clock_seconds:
        # The window is over. A fresh window is the honest reading of
        # "max_wall_clock_seconds" -- it bounds one burst, and refusing
        # forever would make a long-lived process permanently mute.
        entry[0], entry[1] = 0, current
        spent = 0

    if spent >= policy.max_queries:
        raise DiscoveryBudgetExhausted(
            f"discovery budget exhausted for objective "
            f"{policy.objective!r}: {spent} of {policy.max_queries} "
            f"queries already spent within {policy.max_wall_clock_seconds}s "
            f"(this process). Refusing before the request is made, so the "
            f"budget costs nothing to enforce."
        )
    entry[0] = spent + 1
    return entry[0]


def budget_spent(policy: "DiscoveryPolicy") -> int:
    """How many queries this policy has spent in this process. Read-only;
    exists so the budget is observable rather than only enforceable."""
    return _BUDGET_LEDGER.get(_policy_key(policy), [0, 0.0])[0]


def reset_budgets() -> None:
    """Clear the ledger. For tests and for a caller that genuinely starts
    a new run inside one process -- deliberately NOT called anywhere in
    the fetch path, or the budget would reset itself."""
    _BUDGET_LEDGER.clear()


# ─────────────────────────────────────────────────────────────
# BUDGET ENFORCEMENT
#
# `max_queries`, `max_wall_clock_seconds` and `max_results` were
# declared on DiscoveryPolicy, serialised by to_dict(), and read by
# NOTHING. An independent adversarial review grepped the whole
# repository and found zero consumers. Meanwhile `fetch_feed()`'s own
# docstring told callers a policy "names a concrete objective and
# budget" -- so the gate advertised a limit it did not have, which is
# exactly the switch-that-does-nothing defect this repository's own
# doctrine calls out by name.
#
# THE SCOPE IS PER-PROCESS, AND THAT IS STATED RATHER THAN IMPLIED.
# The ledger below lives in module memory, so the budget covers one
# Python process. That matches how this repository actually fetches:
# `cron_pulse.py` is a cron entry, so every tick is a fresh process
# with a fresh budget, and the limit constrains a runaway loop inside
# one run -- which is the failure this is for. It does NOT constrain
# total requests per hour across many ticks; GitHub's own rate limit
# does that, and pretending otherwise would put a second false claim
# in the same place as the first.
# ─────────────────────────────────────────────────────────────


class DiscoveryBudgetExhausted(CommunicationDenied):
    """A policy's declared budget was spent.

    Subclasses CommunicationDenied so a caller that already handles
    refusal handles this too, and so no existing caller can mistake
    exhaustion for success."""


def _policy_key(policy: "DiscoveryPolicy") -> str:
    """Identity by declared content, not by object id.

    Two policies naming the same objective and budget are the same
    authorization however many times they are constructed -- otherwise a
    caller resets its own budget just by building a fresh instance in a
    loop, which is the exact bypass this closes.
    """
    return hashlib.sha256(json.dumps({
        "objective": policy.objective.strip().lower(),
        "requested_scope": policy.requested_scope,
        "max_queries": policy.max_queries,
        "max_wall_clock_seconds": policy.max_wall_clock_seconds,
    }, sort_keys=True).encode()).hexdigest()[:16]


_BUDGET_LEDGER: dict = {}


def spend_query(policy: "DiscoveryPolicy", now=None) -> int:
    """Charge one request against a policy. Raises when the budget is out.

    Called by `mouth_common.fetch_feed()` after authorization and BEFORE
    the socket opens, so an exhausted budget costs no request. Returns
    the number spent including this one.

    `now` is injectable for tests; production uses a monotonic clock so
    a system clock adjustment cannot extend or collapse a window.
    """
    key = _policy_key(policy)
    current = time.monotonic() if now is None else now
    entry = _BUDGET_LEDGER.setdefault(key, [0, current])
    spent, started = entry

    if current - started > policy.max_wall_clock_seconds:
        # The window is over. A fresh window is the honest reading of
        # max_wall_clock_seconds -- it bounds one burst, and refusing
        # forever would make a long-lived process permanently mute.
        entry[0], entry[1] = 0, current
        spent = 0

    if spent >= policy.max_queries:
        raise DiscoveryBudgetExhausted(
            f"discovery budget exhausted for objective {policy.objective!r}: "
            f"{spent} of {policy.max_queries} queries already spent within "
            f"{policy.max_wall_clock_seconds}s (this process). Refusing "
            f"before the request is made, so the budget costs nothing to "
            f"enforce."
        )
    entry[0] = spent + 1
    return entry[0]


def budget_spent(policy: "DiscoveryPolicy") -> int:
    """How many queries this policy has spent in this process. Read-only;
    exists so the budget is observable, not only enforceable."""
    return _BUDGET_LEDGER.get(_policy_key(policy), [0, 0.0])[0]


def reset_budgets() -> None:
    """Clear the ledger. For tests, and for a caller that genuinely
    starts a new run inside one process -- deliberately NOT called
    anywhere in the fetch path, or the budget would reset itself."""
    _BUDGET_LEDGER.clear()


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
