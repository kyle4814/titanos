"""
Value Flow Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a `value_flow:` YAML
document may declare — rpa/'s implementation of the governing directive's
"zero-extraction" accounting model. Same discipline as
rpa/schema/institutional_bottleneck.py and magl/schema/magl_schema.py:
this module is data (field names, enum universes, required-path tables),
never behaviour. All behaviour lives in
rpa/validators/validate_value_flow.py.

WHAT ZERO-EXTRACTION MEANS HERE

The model draws one hard structural line: EXPLICITLY BUDGETED NECESSARY
CONSUMPTION (`necessary_consumption[]` — operations, maintenance,
security, staff, etc, each with a stated category and a stated basis for
why it is necessary) versus every other outflow of value
(`extractions[]`). Nothing is allowed to leave the system silently or
unaccounted-for: every `extractions[]` entry must answer, structurally,
the six questions the governing directive names — WHO receives it, WHY,
UNDER WHAT AUTHORITY, WHAT DID THEY CONTRIBUTE, WHAT IS THE LIMIT, HOW IS
IT AUDITED. An extraction record missing any one of those six answers is
not "incomplete data" — it is exactly the "uninspectable rent-seeking"
shape the zero-extraction model exists to make impossible to produce
without being caught.

A `value_flow` document with zero declared `necessary_consumption` is
itself treated as suspicious and rejected (VF-R-2) — nothing real runs on
zero cost, so a document claiming that is either wrong or hiding
consumption inside `extractions[]` where it does not belong.

WHAT THIS SCHEMA DELIBERATELY DOES NOT DO

This is a structural accounting schema, not a currency/arithmetic engine.
All amount fields are free text (`amount_description`) — no unit
conversion, no sum-to-total reconciliation, no currency math is performed
here or in the validator. `system_map_ref` is a plain opaque string
reference to a `legacy_system_map` id; this module does not import that
schema and the validator does not check referential integrity against it
(same boundary as institutional_bottleneck.py's `system_map_ref` /
`involved_node_ids`).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import FrozenSet, Mapping

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "NECESSARY_CONSUMPTION_CATEGORIES",
    "REQUIRED_TOP_FIELDS",
    "REQUIRED_NECESSARY_CONSUMPTION_FIELDS",
    "REQUIRED_EXTRACTION_FIELDS",
    "REQUIRED_VALUE_CREATED_FIELDS",
    "REQUIRED_REINVESTMENT_FIELDS",
    "REQUIRED_RESERVED_FIELDS",
    "REQUIRED_RETURNED_FIELDS",
    "STRING_FIELDS", "LIST_FIELDS",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# necessary_consumption[].category universe — locally authored.
NECESSARY_CONSUMPTION_CATEGORIES: FrozenSet[str] = frozenset({
    "OPERATIONS", "MAINTENANCE", "SECURITY", "STAFF", "INFRASTRUCTURE",
    "RESERVES", "LEGAL", "TAX", "SAFETY", "RESEARCH", "CONTINGENCY",
})


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({"id", "system_map_ref", "period"}))
ACCOUNTING = FieldGroup("accounting", frozenset({
    "value_created", "necessary_consumption", "extractions",
    "reinvestment", "reserved", "returned",
}))
LEAKAGE = FieldGroup("leakage", frozenset({
    "undeclared_leakage_flag", "leakage_description",
}))

ALL_GROUPS = (IDENTITY, ACCOUNTING, LEAKAGE)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(f for g in ALL_GROUPS for f in g.fields)

# Top-level keys required directly under `value_flow:`. leakage_description
# is intentionally NOT in this set — it is conditionally required, enforced
# by VF-R-6 in the validator, not by unconditional top-level presence.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "system_map_ref", "period", "value_created",
    "necessary_consumption", "extractions", "reinvestment", "reserved",
    "returned", "undeclared_leakage_flag",
})

REQUIRED_VALUE_CREATED_FIELDS: FrozenSet[str] = frozenset({
    "source", "amount_description",
})

REQUIRED_NECESSARY_CONSUMPTION_FIELDS: FrozenSet[str] = frozenset({
    "category", "amount_description", "basis",
})

# The literal enforcement of the directive's "every extraction must
# answer these six questions" rule (VF-R-1, the single most important
# rule in this schema).
REQUIRED_EXTRACTION_FIELDS: FrozenSet[str] = frozenset({
    "id", "recipient", "reason", "authority", "contribution", "limit",
    "audit_mechanism", "reviewable",
})

REQUIRED_REINVESTMENT_FIELDS: FrozenSet[str] = frozenset({
    "target", "amount_description", "rationale",
})

REQUIRED_RESERVED_FIELDS: FrozenSet[str] = frozenset({
    "purpose", "amount_description",
})

REQUIRED_RETURNED_FIELDS: FrozenSet[str] = frozenset({
    "recipient", "amount_description", "basis",
})

STRING_FIELDS: FrozenSet[str] = frozenset({"id", "system_map_ref", "period"})

LIST_FIELDS: FrozenSet[str] = frozenset({
    "value_created", "necessary_consumption", "extractions",
    "reinvestment", "reserved", "returned",
})


def schema_hash() -> str:
    """Integrity-address the schema itself, same rationale as
    magl_schema.schema_hash / institutional_bottleneck.schema_hash."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "necessary_consumption_categories": sorted(NECESSARY_CONSUMPTION_CATEGORIES),
        "required_extraction_fields": sorted(REQUIRED_EXTRACTION_FIELDS),
        "required_necessary_consumption_fields": sorted(REQUIRED_NECESSARY_CONSUMPTION_FIELDS),
        "required_value_created_fields": sorted(REQUIRED_VALUE_CREATED_FIELDS),
        "required_reinvestment_fields": sorted(REQUIRED_REINVESTMENT_FIELDS),
        "required_reserved_fields": sorted(REQUIRED_RESERVED_FIELDS),
        "required_returned_fields": sorted(REQUIRED_RETURNED_FIELDS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"value-flow-schema-v{SCHEMA_VERSION}"
