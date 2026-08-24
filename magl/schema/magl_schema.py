"""
MAGL (Modular Architecture Generation Library unit) Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a MAGL YAML document may
declare — the magl/ package's counterpart to schema/artifact_schema.py and
kpm/schemas/blueprint_atom.py. Same discipline: this module is data (field
names, enum universes, required-path tables), never behaviour. All
behaviour lives in magl/validators/validate_magl.py.

WHY THIS FILE DOES NOT DEFINE ITS OWN EPISTEMIC OR LIFECYCLE VOCABULARY

Two of this schema's enum fields are NOT locally authored:

  - `classification.epistemic_status` must draw from the exact same
    15-member closed universe every other claim/artifact/blueprint in this
    codebase draws from — kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS.
    Redefining a parallel "MAGL epistemic status" list here would be the
    exact duplication this multi-schema exercise exists to eliminate, and
    would let a MAGL claim VERIFIED_FACT under a vocabulary the rest of the
    system doesn't recognise.

  - `lifecycle.status` / `promotion.current_gate` must draw from the same
    10-state promotion vocabulary as kpm.promotion.state_machine
    (RAW..SUPERSEDED). A MAGL's promotion status is not a MAGL-local
    concept — it is the SAME lifecycle every other promotable unit in this
    codebase goes through.

Both are imported, not copied, at the bottom of this file. If the
upstream frozensets change, this schema (and the validator built on it)
picks the change up automatically rather than silently drifting out of
sync.

WHAT A MAGL IS

A MAGL unit is a self-describing, independently-composable capability
declaration: what it claims to be able to do, under what epistemic
confidence, within what jurisdiction (the fields it is permitted to
read/write/execute/call/modify/publish), with what known risks and
controls, and where it sits in the shared promotion lifecycle. The
`classification.capability_type` / `jurisdiction.*` pairing carries the
schema's one structural security rule: a capability_type of EXECUTABLE or
EXTERNALLY_ACTING with an entirely empty jurisdiction is a structural
contradiction (claims to act, claims no scope to act within), and a
DESCRIPTIVE-only capability_type with any jurisdiction entries is the
mirror-image contradiction (claims to only describe, but also claims
execution/modification scope). Both are enforced by the validator, not
this module — this module only names the fields and enums involved.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Mapping

# ─────────────────────────────────────────────────────────────
# Cross-package import: reuse, never redefine, the shared closed
# vocabularies this schema depends on (epistemic classification,
# promotion lifecycle states).
# ─────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402
from kpm.promotion.state_machine import ALL_STATES as _PROMOTION_STATES  # noqa: E402

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "EPISTEMIC_CLASSIFICATIONS", "PROMOTION_STATES",
    "CAPABILITY_TYPES", "MATURITY_VALUES",
    "REQUIRED_TOP_FIELDS", "REQUIRED_NESTED_PATHS",
    "LIST_FIELDS", "STRING_FIELDS",
    "EXECUTION_JURISDICTION_FIELDS",
    "ACTING_CAPABILITY_TYPES",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

# Reused verbatim from kpm/schemas/epistemic_types.py — not redefined.
EPISTEMIC_CLASSIFICATIONS: FrozenSet[str] = ALL_CLASSIFICATIONS

# Reused verbatim from kpm/promotion/state_machine.py — not redefined.
PROMOTION_STATES: FrozenSet[str] = frozenset(_PROMOTION_STATES)

# capability_type universe — the risk-tier field from the governing
# directive's "Security Reality" section. Locally authored: this
# vocabulary is MAGL-specific and has no upstream twin elsewhere in the
# codebase.
CAPABILITY_TYPES: FrozenSet[str] = frozenset({
    "DESCRIPTIVE", "ANALYTICAL", "SIMULATIVE", "EXECUTABLE",
    "EXTERNALLY_ACTING",
})

# capability_types that require at least one non-empty jurisdiction
# grant. See EXECUTION_JURISDICTION_FIELDS below.
ACTING_CAPABILITY_TYPES: FrozenSet[str] = frozenset({
    "EXECUTABLE", "EXTERNALLY_ACTING",
})

MATURITY_VALUES: FrozenSet[str] = frozenset({
    "EXPERIMENTAL", "PROVISIONAL", "STABLE", "DEPRECATED",
})

# jurisdiction sub-fields that count as "claims a scope to act within".
# may_read is deliberately excluded — reading is not acting, and a purely
# DESCRIPTIVE capability_type is allowed to declare may_read (it can read
# things to describe them) without tripping the DESCRIPTIVE-with-
# jurisdiction contradiction.
EXECUTION_JURISDICTION_FIELDS: tuple[str, ...] = (
    "may_write", "may_execute", "may_call", "may_modify", "may_publish",
)

# ─────────────────────────────────────────────────────────────
# Field groups (top-level `magl.*` keys)
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({
    "id", "name", "version", "title", "description",
}))
CLASSIFICATION = FieldGroup("classification", frozenset({"classification"}))
PROVENANCE = FieldGroup("provenance", frozenset({"provenance"}))
PURPOSE = FieldGroup("purpose", frozenset({"purpose"}))
JURISDICTION = FieldGroup("jurisdiction", frozenset({"jurisdiction"}))
INPUTS = FieldGroup("inputs", frozenset({"inputs"}))
OUTPUTS = FieldGroup("outputs", frozenset({"outputs"}))
DEPENDENCIES = FieldGroup("dependencies", frozenset({"dependencies"}))
FRAMING = FieldGroup("framing", frozenset({"assumptions", "unknowns"}))
RISKS = FieldGroup("risks", frozenset({"risks"}))
CONTROLS = FieldGroup("controls", frozenset({"controls"}))
VERIFICATION = FieldGroup("verification", frozenset({"verification"}))
COMPOSITION = FieldGroup("composition", frozenset({"composition"}))
LIFECYCLE = FieldGroup("lifecycle", frozenset({"lifecycle"}))
AUDIT = FieldGroup("audit", frozenset({"audit"}))
DOCUMENTATION = FieldGroup("documentation", frozenset({"documentation"}))
PROMOTION = FieldGroup("promotion", frozenset({"promotion"}))

ALL_GROUPS = (
    IDENTITY, CLASSIFICATION, PROVENANCE, PURPOSE, JURISDICTION, INPUTS,
    OUTPUTS, DEPENDENCIES, FRAMING, RISKS, CONTROLS, VERIFICATION,
    COMPOSITION, LIFECYCLE, AUDIT, DOCUMENTATION, PROMOTION,
)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS for f in g.fields
)

# Top-level keys required directly under `magl:`.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "name", "version", "title", "description",
    "classification", "provenance", "purpose", "jurisdiction",
    "documentation", "lifecycle", "promotion",
})

# Dotted paths required within nested sections (checked once the parent
# section itself is confirmed present and is a mapping).
REQUIRED_NESTED_PATHS: Mapping[str, FrozenSet[str]] = {
    "classification": frozenset({
        "domain", "capability_type", "epistemic_status", "maturity",
    }),
    "provenance": frozenset({"license"}),
    "purpose": frozenset({"problem", "intended_benefit"}),
    "lifecycle": frozenset({"status", "created_at"}),
    "documentation": frozenset({"summary", "limitations"}),
    "promotion": frozenset({"current_gate"}),
}

# Fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "name", "version", "title", "description",
})

# Fields whose value, if present, must be a list.
LIST_FIELDS: FrozenSet[str] = frozenset({
    "assumptions", "unknowns",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    artifact_schema.schema_hash / blueprint_atom.schema_hash): a claimed
    MAGL schema version should be checkable against what this validator
    actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_nested_paths": {
            k: sorted(v) for k, v in sorted(REQUIRED_NESTED_PATHS.items())
        },
        "epistemic_classifications": sorted(EPISTEMIC_CLASSIFICATIONS),
        "promotion_states": sorted(PROMOTION_STATES),
        "capability_types": sorted(CAPABILITY_TYPES),
        "maturity_values": sorted(MATURITY_VALUES),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"magl-schema-v{SCHEMA_VERSION}"
