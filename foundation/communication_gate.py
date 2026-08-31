"""
Communication Gate — the prerequisite switch for the §2 critical
function "external communication," under
TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md.

WHY THIS FILE EXISTS RIGHT NOW, NOT HYPOTHETICALLY

Ø_FRONTIER_PROBE_001 found a real internal N=Ø and correctly declined to
build a live network fetcher to escape it — this repository's entire
proven Obelisk Test claim (zero network imports, runs with no external
dependency) would have been broken by that shortcut. But the switch
doctrine's own principle applies here too: "an instruction can be
ignored, diluted, overwritten, or lost in context" — a session's own
discipline in declining to fetch is a reminder, not a mechanism. This
file is the mechanism: if any future component ever proposes a real
network operation, it has something concrete to check against instead
of relying on a fresh session remembering the same discipline from
scratch.

THIS FILE MAKES NO NETWORK CONNECTION. IT NEVER WILL — that is not this
module's job. It answers exactly one question, mirroring
foundation/publication_gate.py's own scope note verbatim in spirit:
"is external communication currently authorized" — and nothing in this
repository calls a real network operation based on its answer, because
no real network operation exists anywhere in this repository yet. This
is the lock. The door has not been built.

THE SWITCH MODEL, LITERALLY (same shape as publication_gate.py's)

    {
        "armed": false,
        "trigger_verified": false,
        "scope_declared": false,
        "human_review_required": true,
        "action_permitted": false,
    }

Every field starts at the fail-closed value. `action_permitted` can only
become True if a human has explicitly named which scope is authorized
and why — never inferred, never defaulted from "the capability would be
useful," never granted merely because a caller (model, external content,
or future retrieval component) requests it.

TWO-POINT ENFORCEMENT (§5), SAME PATTERN AS publication_gate.py

Point one: `evaluate()` computes the decision from declared evidence.
Point two: `authorize_communication()` does NOT trust a cached
`action_permitted` flag from a `CommunicationSwitch` object a caller
hands it — it re-derives the answer from the switch's own recorded
evidence fields every time, the same "verify from the record, not the
label" discipline as `taal/gate/human_jurisdiction.py::
confirm_pilot_authorized()` and `publication_gate.py::authorize_publish()`.

SCOPE, DECLARED BUT NEVER ACTIVATED

`COMMUNICATION_SCOPES` names the specific future boundaries this switch
can eventually govern (READ_URL, READ_API, RECEIVE_WEBHOOK) — declaring
the vocabulary now makes the future integration contract legible without
building any of the three. None of them do anything; there is no code
anywhere that reads a URL, calls an API, or receives a webhook. A
`CommunicationSwitch.requested_scope` must name one of these values or
authorization is refused — an unscoped "just turn communication on"
request is not a real authorization request.

WHAT THIS FILE DOES NOT DO

It does not perform any I/O. It does not import `requests`, `urllib`,
`socket`, or `http.client`. It does not retrieve, send, or receive
anything. It does not grant a caller any capability that did not already
exist — no fetcher exists to grant capability to. `authorize_
communication()`'s True return value is not consumed by anything in this
repository; the future retrieval component this switch is meant to gate
does not exist yet, per this cycle's own explicit non-goal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, FrozenSet

__all__ = [
    "CAPABILITY_ID", "COMMUNICATION_SCOPES",
    "CommunicationSwitch", "CommunicationDecision",
    "evaluate", "authorize_communication", "CommunicationDenied",
]

CAPABILITY_ID = "EXTERNAL_COMMUNICATION"

# Declared future boundaries only — none active, none implemented.
# READ_URL / READ_API: a bounded, one-way, read-only retrieval (per
# Ø_FRONTIER_PROBE_001's own "future integration contract": external
# content becomes ◈ OBSERVED input via SourceRegistry.ingest_source(),
# never authority). RECEIVE_WEBHOOK: an inbound listener — named because
# the doctrine's own §2 list mentions "external communication" generally,
# not because any inbound mechanism is remotely close to justified.
COMMUNICATION_SCOPES: FrozenSet[str] = frozenset({
    "READ_URL", "READ_API", "RECEIVE_WEBHOOK",
})


class CommunicationDenied(Exception):
    """Raised by authorize_communication() when re-derivation from
    evidence disagrees with the switch's own action_permitted flag, or
    when required evidence is missing. Loud on purpose, same reasoning
    as publication_gate.py::PublicationRefused — a caller that ignores
    this exception has to do so explicitly, not by accident."""


@dataclass(frozen=True)
class CommunicationSwitch:
    """Declared evidence for one external-communication authorization
    decision. Every field here is a CLAIM the caller makes; this module
    does not go verify anything about a real retrieval mechanism — there
    isn't one to verify. Same boundary as PublicationSwitch: checks
    shape/consistency of DECLARED fields, does not manufacture them."""

    capability_id: str = CAPABILITY_ID
    requested_scope: str = ""                 # must be one of COMMUNICATION_SCOPES
    doctrine_reference: str = "TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md"
    human_authorized_by: str = ""              # required non-empty — a name, not a bool
    human_authorization_note: str = ""         # what exactly was authorized, and why
    reversibility_acknowledged: bool = False   # sent/received external data is not
                                               # fully reversible; must be explicit,
                                               # never assumed (same as publication_gate.py)
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CommunicationDecision:
    armed: bool = False
    trigger_verified: bool = False
    scope_declared: bool = False
    human_review_required: bool = True
    action_permitted: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "armed": self.armed, "trigger_verified": self.trigger_verified,
            "scope_declared": self.scope_declared,
            "human_review_required": self.human_review_required,
            "action_permitted": self.action_permitted,
            "reasons": list(self.reasons),
        }


def evaluate(switch: CommunicationSwitch) -> CommunicationDecision:
    """Point one of two-point enforcement (§5). Fail-closed throughout:
    every gate must be explicitly satisfied, never assumed from silence.

    IF ANY REQUIRED CONDITION IS UNKNOWN, action_permitted STAYS FALSE.
    This function never returns action_permitted=True by omission, and
    it does not perform, request, or simulate any network operation
    regardless of the result.
    """
    d = CommunicationDecision()

    # --- trigger: is this actually the governed capability? --------------
    if switch.capability_id != CAPABILITY_ID:
        d.reasons.append(
            f"capability_id '{switch.capability_id}' does not match "
            f"'{CAPABILITY_ID}' — this switch only governs external "
            f"communication, not an unrelated capability"
        )
        return d
    d.trigger_verified = True

    # --- scope: an unscoped request is not a real authorization request --
    if switch.requested_scope not in COMMUNICATION_SCOPES:
        d.reasons.append(
            f"requested_scope '{switch.requested_scope}' is not one of "
            f"the declared scopes {sorted(COMMUNICATION_SCOPES)} — "
            f"'just enable communication' is not an authorizable request"
        )
        return d
    d.scope_declared = True
    d.armed = True

    # --- human review: always required for this switch, no exception -----
    if not switch.human_authorized_by.strip():
        d.reasons.append(
            "human_review_required is unconditionally True for external "
            "communication — no human_authorized_by name recorded"
        )
        return d
    if not switch.human_authorization_note.strip():
        d.reasons.append(
            "human_authorized_by is present but human_authorization_note "
            "is empty — an unexplained authorization is not "
            "distinguishable from a forged one; the doctrine requires "
            "evidence, not a name alone"
        )
        return d
    if not switch.reversibility_acknowledged:
        d.reasons.append(
            "reversibility_acknowledged is False — external "
            "communication is not fully reversible (data sent or "
            "received cannot be un-sent or un-received) and this must "
            "be explicitly acknowledged, never assumed"
        )
        return d
    d.human_review_required = False  # satisfied, not skipped

    d.action_permitted = True
    d.reasons.append(
        f"scope '{switch.requested_scope}' authorized by "
        f"{switch.human_authorized_by}: {switch.human_authorization_note}"
    )
    return d


def authorize_communication(switch: CommunicationSwitch) -> bool:
    """Point two of two-point enforcement (§5).

    Does NOT accept a CommunicationDecision as input and does NOT trust
    any action_permitted flag a caller might have cached. Re-runs
    evaluate() against the switch's own declared evidence every time, so
    a caller cannot construct a decision object by hand claiming
    authorization and have this function believe it.

    Raises CommunicationDenied (never returns False silently) so a
    caller cannot mistake "didn't check" for "checked and it's fine" —
    the same reasoning as publication_gate.py::authorize_publish().

    CORRECTION 2026-09-01. This docstring previously said "no code in
    this repository consumes this return value to perform a network
    operation, because no such operation exists." That stopped being
    true when the mouths were built: `mouth_common.fetch_feed()` opens a
    real socket, and for several cycles it did so WITHOUT passing
    through this gate at all. The statement was not merely stale -- it
    was the reason nobody noticed the gap, because the gate's own
    documentation asserted the door it guarded did not exist.

    Now accurate: `fetch_feed()` is the single socket in this
    repository, and it calls `discovery_authorization.authorize_
    discovery()` -- which re-derives through this function -- before
    every request, refusing outright when no policy is supplied. This
    function still answers "is the switch open," not "did anything walk
    through it"; what changed is that something now walks through it.
    """
    decision = evaluate(switch)
    if not decision.action_permitted:
        raise CommunicationDenied(
            f"external communication (scope='{switch.requested_scope}') "
            f"is NOT authorized: {'; '.join(decision.reasons)}"
        )
    return True
