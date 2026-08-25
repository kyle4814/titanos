"""
Normalized Security Event Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a
`normalized_security_event` YAML document may declare — taal/'s
counterpart to magl/schema/magl_schema.py, rpa/schema/*.py, and
taal/schema/permission_request.py. Same discipline: this module is data
(field names, enum universes, required-field tables), never behaviour.
All behaviour lives in
taal/validators/validate_normalized_security_event.py.

WHAT A NORMALIZED SECURITY EVENT IS, AND WHAT IT IS NOT

Per the governing directive's §9, the Integrator (a different component,
built by a different agent) normalizes raw, heterogeneous signals —
application logs, access requests, AI tool calls, policy engine output,
anomaly detectors, audit logs, human reports, telemetry — into this one
canonical shape. This schema is that shape.

A normalized_security_event is an OBSERVATION record. It states what was
observed, factually, and nothing more. It is never a verdict, and it must
never contain a conclusion field. See FORBIDDEN_VERDICT_FIELDS below —
`verdict`, `threat_label`, `attack_confirmed`, `is_malicious`, and
`recommended_action` all belong to a separate VERDICT schema (owned by a
different agent, built on top of events like this one, never merged into
it). This is the load-bearing structural separation of this schema
(observation vs. conclusion) — mirroring rpa/schema/legacy_system_map.py's
FORBIDDEN_PRESCRIPTIVE_FIELDS pattern exactly: an explicit, named,
closed set of field names that the validator rejects outright if present,
regardless of what else is well-formed.

WHY raw_reference EXISTS INSTEAD OF EMBEDDING THE RAW SIGNAL

This schema normalizes; it does not duplicate or store raw payloads.
`raw_reference` is a pointer to the original raw signal (a log line id, a
request id, a ticket number — whatever the Integrator's source system
uses), never the raw signal itself embedded inline. Keeping raw payloads
out of the normalized record keeps this schema small, keeps it from
becoming a second copy of a system of record, and keeps sensitive raw
payload content (which may include credentials, PII, or other material
this schema has no business retaining) out of the normalized layer
entirely.

WHY related_permission_request_ref IS A FREE-TEXT POINTER, NOT A
VALIDATED LINK

Same boundary as every other `_ref` field in this codebase's history
(see rpa/schema/institutional_bottleneck.py's `system_map_ref`,
rpa/schema/value_flow.py, rpa/schema/before_after_measurement.py's
`pilot_simulation_ref`): a free-text reference to a
taal/schema/permission_request.py `id`, with no cross-file validation
performed here. This validator has no access to (and must not depend on)
whatever store holds permission_request documents; confirming the
reference resolves to a real permission_request is a different
component's job, if anyone's.

WHY `signals` IS A LIST OF FACTUAL STRINGS, NEVER AN INTERPRETATION

`signals` must record observable facts only — "3 failed auth attempts in
10s" is a fine signal; "looks like brute force" is not, because it is
already a conclusion wearing an observation's clothes. This distinction
cannot be enforced semantically (nothing can tell "the door was left
open" from "this looks like a break-in" by grammar alone), so the field
NAME and this docstring carry the weight of making the distinction
explicit for a human or automated author. See
CONCLUSORY_WORD_BLOCKLIST below and the judgment call documented in the
validator module docstring for the one narrow, literal check this schema
DOES perform.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "EPISTEMIC_CLASSIFICATIONS", "SOURCE_TYPES",
    "REQUIRED_TOP_FIELDS", "STRING_FIELDS",
    "FORBIDDEN_VERDICT_FIELDS", "CONCLUSORY_WORD_BLOCKLIST",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

# Reused verbatim from kpm/schemas/epistemic_types.py — not redefined.
# See magl_schema.py's identical rationale: redefining a parallel
# "security event epistemic status" list here would let a normalized
# event claim VERIFIED_FACT confidence under a vocabulary the rest of the
# system doesn't recognise.
EPISTEMIC_CLASSIFICATIONS: FrozenSet[str] = ALL_CLASSIFICATIONS

SOURCE_TYPES: FrozenSet[str] = frozenset({
    "APPLICATION_EVENT", "ACCESS_REQUEST", "AI_TOOL_REQUEST",
    "POLICY_VIOLATION", "ANOMALY", "AUDIT_LOG", "HUMAN_REPORT",
    "SECURITY_TELEMETRY",
})

# Fields that belong to a separate VERDICT schema (a different agent's
# component), never to this observation record. Presence of ANY of these
# is a structural rule violation — this is the load-bearing separation of
# this schema. Mirrors rpa/schema/legacy_system_map.py's
# FORBIDDEN_PRESCRIPTIVE_FIELDS pattern exactly.
FORBIDDEN_VERDICT_FIELDS: FrozenSet[str] = frozenset({
    "verdict", "threat_label", "attack_confirmed", "is_malicious",
    "recommended_action",
})

# JUDGMENT CALL (documented per task instructions): a small, literal
# blocklist of obviously-conclusory words rejected if found inside a
# `signals` entry. This is deliberately narrow — it cannot and does not
# attempt to catch every conclusory phrasing (that is not semantically
# enforceable), it only catches the small set of words that are almost
# never legitimate inside a FACTUAL observation string. Mirrors the
# action-verb blocklist pattern in
# rpa/schema/institutional_bottleneck.py's ACTION_VERB_BLOCKLIST
# (recommended_next_step field). Included because the cost of a false
# positive (a legitimate signal happens to contain one of these words) is
# low — the author simply rephrases factually — while the cost of leaving
# the field fully unconstrained is a schema that claims a
# fact/interpretation boundary in its docstring but enforces none of it.
CONCLUSORY_WORD_BLOCKLIST: FrozenSet[str] = frozenset({
    "malicious", "attack", "compromised", "confirmed",
})

# ─────────────────────────────────────────────────────────────
# Field groups (top-level `normalized_security_event.*` keys)
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({"id", "observed_at"}))
SOURCE = FieldGroup("source", frozenset({"source_type", "raw_reference"}))
SUBJECT = FieldGroup("subject", frozenset({
    "entity", "observed_action", "affected_resource",
}))
LINKAGE = FieldGroup("linkage", frozenset({"related_permission_request_ref"}))
OBSERVATION = FieldGroup("observation", frozenset({"signals", "confidence"}))

ALL_GROUPS = (IDENTITY, SOURCE, SUBJECT, LINKAGE, OBSERVATION)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS for f in g.fields
)

# related_permission_request_ref is optional — not listed as required.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "observed_at", "source_type", "raw_reference", "entity",
    "observed_action", "affected_resource", "signals", "confidence",
})

# Fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "observed_at", "raw_reference", "entity", "observed_action",
    "affected_resource", "related_permission_request_ref",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    magl_schema.schema_hash) — a claimed normalized_security_event schema
    version should be checkable against what this validator actually
    implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "source_types": sorted(SOURCE_TYPES),
        "epistemic_classifications": sorted(EPISTEMIC_CLASSIFICATIONS),
        "forbidden_verdict_fields": sorted(FORBIDDEN_VERDICT_FIELDS),
        "conclusory_word_blocklist": sorted(CONCLUSORY_WORD_BLOCKLIST),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"normalized-security-event-schema-v{SCHEMA_VERSION}"
