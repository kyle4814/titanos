"""
Rollback Contract Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a Rollback Contract
YAML document may declare — the rpa/ package's counterpart to
rpa/schema/pilot_simulation.py and rpa/schema/before_after_measurement.py.
Same discipline: this module is data (field names, enum universes,
required-path tables), never behaviour. All behaviour lives in
rpa/validators/validate_rollback_contract.py.

WHAT A ROLLBACK CONTRACT IS

The governing directive's §XV item 8 lists an explicit, separate
rollback plan as its own numbered deliverable — distinct from a generic
"reversible: true/false" flag elsewhere in this system. A rollback
contract states WHAT would trigger a rollback (trigger_conditions), the
ordered steps to actually perform it (rollback_steps), WHO is
authorized to invoke it (rollback_owner), how long it is expected to
take, how much data loss it risks, and whether it has actually been
TESTED (verified) as opposed to merely written down. verified and
verification_evidence are a deliberately paired boolean+evidence field:
claiming evidence for a rollback that was never verified is a
structural contradiction this schema's validator rejects outright — see
RB-R-8.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import FrozenSet

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "DATA_LOSS_RISK_VALUES",
    "REQUIRED_TOP_FIELDS",
    "STRING_FIELDS", "LIST_FIELDS",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

DATA_LOSS_RISK_VALUES: FrozenSet[str] = frozenset({
    "NONE", "LOW", "MEDIUM", "HIGH",
})

# ─────────────────────────────────────────────────────────────
# Field groups / required-field tables
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({
    "id", "applies_to_ref",
}))
PLAN = FieldGroup("plan", frozenset({
    "trigger_conditions", "rollback_steps", "rollback_owner",
    "estimated_rollback_time", "data_loss_risk",
}))
VERIFICATION = FieldGroup("verification", frozenset({
    "verified", "verification_evidence",
}))

ALL_GROUPS = (IDENTITY, PLAN, VERIFICATION)

# Top-level keys required directly under `rollback_contract:`.
# `verification_evidence` is deliberately excluded from the unconditional
# required set — it is conditionally required only when verified is true
# (see validator RB-R-8); requiring it unconditionally would force a
# non-empty string even for verified: false, which is exactly backwards.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "applies_to_ref", "trigger_conditions", "rollback_steps",
    "rollback_owner", "estimated_rollback_time", "data_loss_risk",
    "verified",
})

# Top-level fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "applies_to_ref", "rollback_owner", "estimated_rollback_time",
})

# Top-level fields whose value must be a non-empty list.
LIST_FIELDS: FrozenSet[str] = frozenset({
    "trigger_conditions", "rollback_steps",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    pilot_simulation.schema_hash / before_after_measurement.schema_hash):
    a claimed Rollback Contract schema version should be checkable
    against what this validator actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "data_loss_risk_values": sorted(DATA_LOSS_RISK_VALUES),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"rollback-contract-schema-v{SCHEMA_VERSION}"
