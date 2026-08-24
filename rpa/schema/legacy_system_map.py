"""
Legacy System Map Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a Legacy System Map
YAML document may declare — the rpa/ package's counterpart to
magl/schema/magl_schema.py and kpm/schemas/blueprint_atom.py. Same
discipline: this module is data (field names, enum universes,
required-path tables), never behaviour. All behaviour lives in
rpa/validators/validate_legacy_system_map.py.

WHAT A LEGACY SYSTEM MAP IS

A Legacy System Map is the read-only "digital twin" of an existing
organisation's architecture that the governing directive requires be
built BEFORE any transformation, automation, or process change is
proposed. It is strictly DESCRIPTIVE: nodes (people, roles, systems,
data stores, vendors, cost centres, workflows, decision points,
physical infrastructure), edges between them (dependency, reporting,
data flow, manual handoff, approval, vendor relationship, backup),
security/authority/organisational boundaries, jurisdiction claims (who
has authority over what, and on what stated basis), observed single
points of failure, and explicitly preserved unknowns.

WHY THIS FILE DOES NOT DEFINE ITS OWN EPISTEMIC VOCABULARY

`epistemic_status` is NOT locally authored. It must draw from the exact
same 15-member closed universe every other claim/artifact/blueprint/MAGL
in this codebase draws from — kpm.schemas.epistemic_types.
ALL_CLASSIFICATIONS. A system map assembled from one rushed interview is
not entitled to claim VERIFIED_FACT just because this schema didn't stop
it — this module only enforces that the declared value is a LEGAL member
of the shared vocabulary; which specific value is earned is a human
judgment call made by whoever classified the map, not something this
schema decides.

WHY THIS SCHEMA IS DELIBERATELY CLOSED TO PRESCRIPTIVE FIELDS

This map is an observation instrument, never a recommendation engine. It
has no field for "automation_recommendation", "proposed_change",
"suggested_fix", or anything of that shape, and never will — see
rpa/validators/validate_legacy_system_map.py's unknown-field handling and
its test_no_automation_recommendation_field test. Mixing "what we found"
with "what we should do about it" inside the same descriptive record is
exactly the collapse the governing directive's read-first-then-decide
sequencing exists to prevent.
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
# epistemic-confidence vocabulary.
# ─────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "EPISTEMIC_CLASSIFICATIONS",
    "SCAN_METHODS", "NODE_TYPES", "CRITICALITY_LEVELS",
    "EDGE_RELATIONSHIPS",
    "REQUIRED_TOP_FIELDS", "REQUIRED_NODE_FIELDS",
    "REQUIRED_EDGE_FIELDS", "REQUIRED_BOUNDARY_FIELDS",
    "REQUIRED_JURISDICTION_FIELDS",
    "LIST_FIELDS_TOP",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

# Reused verbatim from kpm/schemas/epistemic_types.py — not redefined.
EPISTEMIC_CLASSIFICATIONS: FrozenSet[str] = ALL_CLASSIFICATIONS

SCAN_METHODS: FrozenSet[str] = frozenset({
    "INTERVIEW", "DOCUMENT_REVIEW", "SYSTEM_LOG_ANALYSIS", "WORKSHOP",
    "MIXED",
})

NODE_TYPES: FrozenSet[str] = frozenset({
    "PERSON", "ROLE", "SOFTWARE_SYSTEM", "DATA_STORE", "VENDOR",
    "COST_CENTRE", "WORKFLOW", "DECISION_POINT",
    "PHYSICAL_INFRASTRUCTURE",
})

CRITICALITY_LEVELS: FrozenSet[str] = frozenset({
    "LOW", "MEDIUM", "HIGH", "MUST_NEVER_STOP",
})

EDGE_RELATIONSHIPS: FrozenSet[str] = frozenset({
    "DEPENDS_ON", "REPORTS_TO", "FEEDS_DATA_TO", "MANUAL_HANDOFF_TO",
    "APPROVES_FOR", "VENDOR_OF", "BACKS_UP",
})

# ─────────────────────────────────────────────────────────────
# Field groups / required-field tables
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({
    "id", "organisation_name", "version", "scanned_at", "scan_method",
    "epistemic_status",
}))
STRUCTURE = FieldGroup("structure", frozenset({
    "nodes", "edges", "boundaries", "jurisdictions",
    "single_points_of_failure", "unknowns",
}))

ALL_GROUPS = (IDENTITY, STRUCTURE)

# Top-level keys required directly under `legacy_system_map:`.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "organisation_name", "version", "scanned_at", "scan_method",
    "epistemic_status", "nodes", "edges", "boundaries", "jurisdictions",
    "single_points_of_failure", "unknowns",
})

# Required per-node fields (nodes[] entries).
REQUIRED_NODE_FIELDS: FrozenSet[str] = frozenset({
    "id", "type", "name", "authority", "known_failure_history",
    "criticality",
})

# Required per-edge fields (edges[] entries).
REQUIRED_EDGE_FIELDS: FrozenSet[str] = frozenset({
    "from_node", "to_node", "relationship", "is_manual",
})

# Required per-boundary fields (boundaries[] entries).
REQUIRED_BOUNDARY_FIELDS: FrozenSet[str] = frozenset({
    "id", "description", "contains_node_ids",
})

# Required per-jurisdiction-claim fields (jurisdictions[] entries).
REQUIRED_JURISDICTION_FIELDS: FrozenSet[str] = frozenset({
    "authority_node_id", "scope_node_ids", "basis",
})

# Top-level fields whose value must be a list.
LIST_FIELDS_TOP: FrozenSet[str] = frozenset({
    "nodes", "edges", "boundaries", "jurisdictions",
    "single_points_of_failure", "unknowns",
})

# Fields this schema deliberately, permanently excludes. Never add to
# REQUIRED_TOP_FIELDS or treat as a recognised optional field — a map is
# descriptive-only and must never carry a prescriptive instruction. Kept
# here as a documented denylist (belt) in addition to the validator's
# unknown-field surfacing (braces) — see
# rpa/validators/validate_legacy_system_map.py LM-R-11.
FORBIDDEN_PRESCRIPTIVE_FIELDS: FrozenSet[str] = frozenset({
    "automation_recommendation", "proposed_change", "suggested_fix",
    "recommended_action", "transformation_plan",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    magl_schema.schema_hash / artifact_schema.schema_hash): a claimed
    Legacy System Map schema version should be checkable against what
    this validator actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_node_fields": sorted(REQUIRED_NODE_FIELDS),
        "required_edge_fields": sorted(REQUIRED_EDGE_FIELDS),
        "required_boundary_fields": sorted(REQUIRED_BOUNDARY_FIELDS),
        "required_jurisdiction_fields": sorted(REQUIRED_JURISDICTION_FIELDS),
        "epistemic_classifications": sorted(EPISTEMIC_CLASSIFICATIONS),
        "scan_methods": sorted(SCAN_METHODS),
        "node_types": sorted(NODE_TYPES),
        "criticality_levels": sorted(CRITICALITY_LEVELS),
        "edge_relationships": sorted(EDGE_RELATIONSHIPS),
        "forbidden_prescriptive_fields": sorted(FORBIDDEN_PRESCRIPTIVE_FIELDS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"legacy-system-map-schema-v{SCHEMA_VERSION}"
