"""
Permission Request Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a `permission_request`
YAML document may declare — taal/'s counterpart to magl/schema/magl_schema.py
and rpa/schema/*.py. Same discipline: this module is data (field names,
enum universes, required-field tables), never behaviour. All behaviour
lives in taal/validators/validate_permission_request.py.

WHAT A PERMISSION REQUEST IS, AND WHAT IT IS NOT

This schema exists to answer exactly one question, precisely and
structurally:

    "WHAT EXACTLY IS THIS ENTITY ASKING THE SYSTEM TO ALLOW?"

A permission_request is the ASK. It is never, under any circumstance, an
authorization. Nothing in this schema grants anything, approves anything,
or confers any right to act. Whether a given ask is ever GRANTED is a
question this schema deliberately does not answer — that verdict belongs
to the root-gate (a different component, built by a different agent).
This module's entire job is to represent the request precisely enough
that a downstream authority can reason about it, and to structurally
reject the one class of document that would corrupt that separation: a
request that also declares itself pre-authorized (see `self_authorized`
below, and PR-R-9 in the validator — the load-bearing rule of this whole
schema).

WHY self_authorized EXISTS AND WHY IT ALWAYS FAILS

A permission_request can never carry a field claiming its own
authorization. `self_authorized: true` is not a shortcut, an override, or
a fast-path — it is the self-certification pattern this codebase's
history exists to catch (see schema/validator.py's R-10 rule for the
identical shape of defect in a different schema: an artifact declaring
`validation_status: VALID` about itself). The validator treats
`self_authorized: true` as an unconditional INVALID result, regardless of
how well-formed every other field is. This is deliberately NOT
"encouraged but ignored" — it is a hard rejection, because a system that
merely ignored the field would still be parsing and trusting a document
shaped like a self-authorization request, and a future refactor could
accidentally start honouring it. Rejecting the whole document forecloses
that path structurally.

WHY risk_hint IS NEVER AUTHORITATIVE

`risk_hint` is optional free text — a human or system-supplied risk note.
This schema only RECORDS it. Nothing in this module, or intended to be
built on top of it, may treat `risk_hint` as an input to any authorization
decision. A request carrying `risk_hint: "none, fully safe"` receives
exactly the same structural treatment as one carrying
`risk_hint: "extremely dangerous"` — the field is data, never instruction,
mirrored on every other free-text field in this codebase (see
magl_schema.py's discussion of fields read as DATA, never as control
flow).

WHY delegation_chain IS CONDITIONALLY REQUIRED

`delegation: true` without a non-empty `delegation_chain` is a structural
contradiction (claims to act on behalf of another, names no chain).
`delegation: false` with a non-empty `delegation_chain` is the
mirror-image contradiction (declares no delegation, but also declares a
chain of who delegated). Both are enforced by the validator (PR-R-6), not
this module — this module only names the fields.

WHY THE IRREVERSIBLE+INDEFINITE+HIGH-STAKES-ACTION COMBINATION IS FLAGGED
BUT NOT INVALIDATED

A request with `reversibility: IRREVERSIBLE`, `duration: "indefinite"`,
and `action` in {DELETE, CONFIGURATION_CHANGE, CREDENTIAL_ACCESS} is not
necessarily illegitimate — some real asks genuinely have that shape (e.g.
a legitimate indefinite credential rotation policy). This schema does not
decide authorization, so it cannot and does not mark the document
INVALID for this alone. But the combination is exactly the shape of ask
that must never pass silently through a pipeline unnoticed, so the
validator attaches a distinct WARNING-severity Issue (PR-R-8) to a
separate `warnings` list on ValidationResult, structurally impossible to
miss and structurally impossible to confuse with a fatal rejection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import FrozenSet

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "ACTIONS", "PROVENANCE_VALUES", "REVERSIBILITY_VALUES",
    "REQUIRED_TOP_FIELDS", "STRING_FIELDS", "BOOLEAN_FIELDS",
    "HIGH_STAKES_ACTIONS", "INDEFINITE_DURATION_VALUE",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations — all locally authored, no upstream twin for these.
# ─────────────────────────────────────────────────────────────

ACTIONS: FrozenSet[str] = frozenset({
    "READ", "WRITE", "EXECUTE", "DELETE", "MODIFY", "CREATE",
    "DELEGATE", "NETWORK_CALL", "PROCESS_SPAWN", "CREDENTIAL_ACCESS",
    "CONFIGURATION_CHANGE",
})

PROVENANCE_VALUES: FrozenSet[str] = frozenset({
    "VERIFIED", "CLAIMED", "UNKNOWN", "UNVERIFIABLE",
})

REVERSIBILITY_VALUES: FrozenSet[str] = frozenset({
    "FULLY_REVERSIBLE", "PARTIALLY_REVERSIBLE", "IRREVERSIBLE", "UNKNOWN",
})

# Actions that, combined with IRREVERSIBLE reversibility and an
# "indefinite" duration, trigger the PR-R-8 WARNING flag (never a fatal
# rejection by itself — see module docstring).
HIGH_STAKES_ACTIONS: FrozenSet[str] = frozenset({
    "DELETE", "CONFIGURATION_CHANGE", "CREDENTIAL_ACCESS",
})

# The exact literal duration value the PR-R-8 flag checks for. Duration
# is otherwise unconstrained free text ("15m", "1h", "until revoked",
# etc.) — only this one literal is structurally significant.
INDEFINITE_DURATION_VALUE = "indefinite"

# ─────────────────────────────────────────────────────────────
# Field groups (top-level `permission_request.*` keys)
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


ASK = FieldGroup("ask", frozenset({
    "id", "requester", "resource", "action", "scope", "duration",
}))
DELEGATION = FieldGroup("delegation", frozenset({
    "delegation", "delegation_chain",
}))
JUSTIFICATION = FieldGroup("justification", frozenset({
    "justification", "provenance", "risk_hint",
}))
RISK = FieldGroup("risk", frozenset({"reversibility"}))
SELF_CERT = FieldGroup("self_cert", frozenset({"self_authorized"}))

ALL_GROUPS = (ASK, DELEGATION, JUSTIFICATION, RISK, SELF_CERT)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS for f in g.fields
)

# Required directly under `permission_request:`. delegation_chain is
# conditionally required (only when delegation is true) — enforced by the
# validator (PR-R-6), not listed here as unconditionally required.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "requester", "resource", "action", "scope", "duration",
    "delegation", "justification", "provenance", "reversibility",
    "self_authorized",
})

# Fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "requester", "resource", "scope", "duration", "justification",
})

# Fields whose value must be a bool (not merely truthy).
BOOLEAN_FIELDS: FrozenSet[str] = frozenset({
    "delegation", "self_authorized",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    magl_schema.schema_hash) — a claimed permission_request schema version
    should be checkable against what this validator actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "actions": sorted(ACTIONS),
        "provenance_values": sorted(PROVENANCE_VALUES),
        "reversibility_values": sorted(REVERSIBILITY_VALUES),
        "high_stakes_actions": sorted(HIGH_STAKES_ACTIONS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"permission-request-schema-v{SCHEMA_VERSION}"
