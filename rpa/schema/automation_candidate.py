"""
Automation Candidate Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields an
`automation_candidate:` YAML document may declare — rpa/'s counterpart to
magl/schema/magl_schema.py, kpm/schemas/blueprint_atom.py, and
rpa/schema/institutional_bottleneck.py. Same discipline: this module is
data (field names, enum universes, required-path tables), never
behaviour. All behaviour lives in
rpa/validators/validate_automation_candidate.py.

WHAT AN AUTOMATION CANDIDATE IS

A PROPOSAL to automate one bounded piece of an organisation's workflow,
discovered from a bottleneck (`bottleneck_ref` points at an
institutional_bottleneck id — a plain string reference, not a
cross-file-validated foreign key; see "WHAT THIS SCHEMA DELIBERATELY DOES
NOT DO" below, same boundary institutional_bottleneck.py draws around
`system_map_ref`/`involved_node_ids`). This is where
AUTOMATION_OPPORTUNITY_DETECTOR output lands.

It declares an explicit `proposed_jurisdiction` — deliberately the SAME
field names as magl_schema.py's jurisdiction section
(may_read/may_write/may_execute/may_call/may_modify/prohibited_actions),
because an automation candidate that eventually gets built literally
becomes a MAGL: this schema is the proposal stage that precedes that, and
using a different vocabulary here would force a lossy translation step
between "what we proposed to touch" and "what the MAGL is actually
authorized to touch".

WHAT THIS SCHEMA DELIBERATELY DOES NOT DO

`bottleneck_ref` and `system_map_ref` are plain string references to
other schemas' ids. This module does NOT import
institutional_bottleneck.py or legacy_system_map.py, and the validator
built on this schema does NOT check referential integrity against them —
same deliberately separate concern institutional_bottleneck.py documents
for its own cross-references, for the same reason (no build-order
dependency forced between sibling schemas).

WHY SCOPE MUST CORRESPOND TO JURISDICTION BREADTH

`automation_scope` is a risk-tier declaration (OBSERVATION_ONLY through
FULL_WORKFLOW_AUTOMATION). A candidate that claims OBSERVATION_ONLY but
also declares may_write/may_execute/may_call/may_modify entries is lying
about its own risk tier — the mirror-image of magl_schema.py's
DESCRIPTIVE-with-jurisdiction contradiction (see that file's
ACTING_CAPABILITY_TYPES / EXECUTION_JURISDICTION_FIELDS docstring). A
candidate that claims FULL_WORKFLOW_AUTOMATION but declares zero acting
jurisdiction is the mirror-image again — claims to act while claiming no
scope to act within. The validator enforces both directions under rule
AC-R-8, in the same shape as magl's MG-R-11.

WHY requires_human_approval IS CONSTRAINED, NOT FREE

A candidate proposing real write/execute/modify jurisdiction
(SMALL_BOUNDED_AUTOMATION or FULL_WORKFLOW_AUTOMATION) cannot declare
`requires_human_approval: false` — that would let a proposal assert its
own way past the human gate this whole component exists to enforce
(rpa/gates/human_jurisdiction.py). The validator rejects that combination
structurally, before any gate logic ever runs.

WHY known_risks MUST BE NON-EMPTY

A candidate with zero acknowledged risks is exactly the "beautiful
proposal, no evidence of self-scrutiny" pattern this codebase's doctrine
warns against elsewhere (mirrors magl_schema's non-empty
documentation.limitations rule, and blueprint_atom's non-empty
acceptance_criteria rule). Rejected structurally, not stylistically.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "EPISTEMIC_CLASSIFICATIONS", "AUTOMATION_SCOPES",
    "OBSERVATION_ONLY_SCOPE", "ACTING_SCOPES",
    "REQUIRED_TOP_FIELDS", "REQUIRED_NESTED_PATHS",
    "STRING_FIELDS", "LIST_FIELDS", "BOOL_FIELDS",
    "JURISDICTION_LIST_FIELDS", "ACTING_JURISDICTION_FIELDS",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# Reused verbatim from kpm/schemas/epistemic_types.py — not redefined.
EPISTEMIC_CLASSIFICATIONS: FrozenSet[str] = ALL_CLASSIFICATIONS

# automation_scope universe — locally authored, no upstream twin. Ordered
# loosely by increasing jurisdiction breadth (not enforced as an ordering
# by this module; the validator only checks the two named extremes).
AUTOMATION_SCOPES: FrozenSet[str] = frozenset({
    "OBSERVATION_ONLY",
    "DATA_NORMALIZATION",
    "PARALLEL_VALIDATION",
    "SMALL_BOUNDED_AUTOMATION",
    "FULL_WORKFLOW_AUTOMATION",
})

# The one scope that must carry an ENTIRELY read-only jurisdiction (only
# may_read permitted; may_write/may_execute/may_call/may_modify must all
# be empty).
OBSERVATION_ONLY_SCOPE = "OBSERVATION_ONLY"

# Scopes that require requires_human_approval: true and, for
# FULL_WORKFLOW_AUTOMATION, at least one non-empty acting jurisdiction
# field.
ACTING_SCOPES: FrozenSet[str] = frozenset({
    "SMALL_BOUNDED_AUTOMATION", "FULL_WORKFLOW_AUTOMATION",
})

# jurisdiction sub-fields, mirroring magl_schema.py's jurisdiction field
# names exactly (minus may_publish, which has no equivalent at the
# proposal stage — a candidate does not publish anything).
JURISDICTION_LIST_FIELDS: tuple[str, ...] = (
    "may_read", "may_write", "may_execute", "may_call", "may_modify",
    "prohibited_actions",
)

# jurisdiction sub-fields that count as "claims a scope to act within".
# may_read and prohibited_actions are excluded — reading is not acting,
# and declaring a prohibition is a constraint, not a grant. Mirrors
# magl_schema.py's EXECUTION_JURISDICTION_FIELDS exactly (minus
# may_publish, absent from this schema).
ACTING_JURISDICTION_FIELDS: tuple[str, ...] = (
    "may_write", "may_execute", "may_call", "may_modify",
)


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({
    "id", "bottleneck_ref", "system_map_ref", "title", "description",
}))
JURISDICTION = FieldGroup("jurisdiction", frozenset({"proposed_jurisdiction"}))
SCOPE = FieldGroup("scope", frozenset({"automation_scope"}))
APPROVAL = FieldGroup("approval", frozenset({"requires_human_approval"}))
REVERSIBILITY = FieldGroup("reversibility", frozenset({
    "reversible", "rollback_plan", "irreversibility_acknowledged",
}))
CLASSIFICATION = FieldGroup("classification", frozenset({"epistemic_status"}))
RISK = FieldGroup("risk", frozenset({"known_risks"}))
PILOT = FieldGroup("pilot", frozenset({"pilot_size"}))

ALL_GROUPS = (
    IDENTITY, JURISDICTION, SCOPE, APPROVAL, REVERSIBILITY, CLASSIFICATION,
    RISK, PILOT,
)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(f for g in ALL_GROUPS for f in g.fields)

# Top-level keys required directly under `automation_candidate:`.
# `rollback_plan` and `irreversibility_acknowledged` are NOT
# unconditionally required — their requiredness is conditional on
# `reversible` and is checked by the validator (mirrors
# kpm/validators/validate_blueprint.py's rollback.reversible pattern),
# not declared as an always-required field here.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "bottleneck_ref", "system_map_ref", "title", "description",
    "proposed_jurisdiction", "automation_scope", "requires_human_approval",
    "reversible", "epistemic_status", "known_risks", "pilot_size",
})

# Dotted paths required within the nested proposed_jurisdiction section.
# Empty here deliberately — proposed_jurisdiction's sub-fields are all
# optional lists (an OBSERVATION_ONLY candidate legitimately has an empty
# jurisdiction other than may_read); presence-of-parent-section is what
# REQUIRED_TOP_FIELDS already enforces.
REQUIRED_NESTED_PATHS: Mapping[str, FrozenSet[str]] = {}

# Fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "bottleneck_ref", "system_map_ref", "title", "description",
    "automation_scope", "epistemic_status", "pilot_size",
})

# Fields whose value, if present, must be a non-empty list.
LIST_FIELDS: FrozenSet[str] = frozenset({"known_risks"})

# Fields whose value, if present, must be a boolean.
BOOL_FIELDS: FrozenSet[str] = frozenset({
    "requires_human_approval", "reversible", "irreversibility_acknowledged",
})


def schema_hash() -> str:
    """Integrity-address the schema itself, same rationale as
    magl_schema.schema_hash / institutional_bottleneck.schema_hash."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_nested_paths": {
            k: sorted(v) for k, v in sorted(REQUIRED_NESTED_PATHS.items())
        },
        "automation_scopes": sorted(AUTOMATION_SCOPES),
        "acting_scopes": sorted(ACTING_SCOPES),
        "jurisdiction_list_fields": sorted(JURISDICTION_LIST_FIELDS),
        "acting_jurisdiction_fields": sorted(ACTING_JURISDICTION_FIELDS),
        "epistemic_classifications": sorted(EPISTEMIC_CLASSIFICATIONS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"automation-candidate-schema-v{SCHEMA_VERSION}"
