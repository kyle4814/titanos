"""
Institutional Bottleneck Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields an
`institutional_bottleneck:` YAML document may declare — rpa/'s
counterpart to magl/schema/magl_schema.py and kpm/schemas/blueprint_atom.py.
Same discipline: this module is data (field names, enum universes,
required-path tables), never behaviour. All behaviour lives in
rpa/validators/validate_bottleneck.py.

WHAT AN INSTITUTIONAL BOTTLENECK RECORD IS

A CLAIM — not an automatically-true fact — that a specific point in an
organisation's architecture (referenced by node id strings from a
`legacy_system_map` this schema does not import or validate against) is
disproportionately responsible for delay, risk, or failure propagation.
This is the governing directive's "critical 20% of flows responsible for
80% of X" framing applied to a single named point.

Because it is a claim, it MUST carry an epistemic status, drawn from the
exact same 15-member closed universe every other claim in this codebase
draws from (kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS — imported,
never redefined here, for the same reason magl_schema.py imports it: a
bottleneck claim VERIFIED_FACT under a locally-invented vocabulary the
rest of the system doesn't recognise would be exactly the kind of
epistemic collapse that vocabulary exists to prevent).

WHAT THIS SCHEMA DELIBERATELY DOES NOT DO

`system_map_ref` and `involved_node_ids` are plain string references to
another schema's ids (rpa/schema/legacy_system_map.py's `nodes[].id`).
This module does NOT import that schema and this validator does NOT check
referential integrity against it — that is a deliberately separate
concern, owned by whatever cross-schema linking layer eventually joins
the two artefacts. Treating a node id here as anything other than an
opaque string would create a build-order dependency this task explicitly
forbids (the map schema may not exist yet when this module loads).

`recommended_next_step` is deliberately constrained to be an
INVESTIGATION/MEASUREMENT instruction, never an automation instruction —
see ACTION_VERB_BLOCKLIST below and BN-R-9 in the validator. Prescribing
a FIX for a bottleneck is a different artefact's job (an
automation-candidate record owned by a different component); this
schema's job is only to name the problem and propose how to learn more
about it.
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
    "EPISTEMIC_CLASSIFICATIONS", "BOTTLENECK_TYPES",
    "EVIDENCE_REQUIRED_CLASSIFICATIONS",
    "REQUIRED_TOP_FIELDS", "REQUIRED_NESTED_PATHS",
    "STRING_FIELDS", "LIST_FIELDS",
    "ACTION_VERB_BLOCKLIST",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# Reused verbatim from kpm/schemas/epistemic_types.py — not redefined.
EPISTEMIC_CLASSIFICATIONS: FrozenSet[str] = ALL_CLASSIFICATIONS

# bottleneck_type universe — locally authored, no upstream twin.
BOTTLENECK_TYPES: FrozenSet[str] = frozenset({
    "SINGLE_POINT_OF_FAILURE",
    "MANUAL_HANDOFF_DELAY",
    "INFORMATION_SILO",
    "KEY_PERSON_DEPENDENCY",
    "VENDOR_CONCENTRATION",
    "STALE_DECISION_LOOP",
    "CONTEXT_LOSS",
    "UNMEASURED_EXTRACTION",
})

# Mirrors kpm.schemas.epistemic_types._REQUIRES_EVIDENCE_TO_ENTER: the
# classifications that represent a strong evidentiary claim require
# non-empty evidence to be entered/held. VERIFIED_FACT and
# EVIDENCE_SUPPORTED_MODEL are the two of that upstream set that make
# sense as steady-state classifications for a bottleneck record (a
# bottleneck is never itself an IMPLEMENTED_SYSTEM).
EVIDENCE_REQUIRED_CLASSIFICATIONS: FrozenSet[str] = frozenset({
    "VERIFIED_FACT",
    "EVIDENCE_SUPPORTED_MODEL",
})

# Classifications for which evidence may legitimately be empty — a
# bottleneck record is allowed to exist as an unevidenced hypothesis.
EVIDENCE_OPTIONAL_CLASSIFICATIONS: FrozenSet[str] = frozenset({
    "SPECULATIVE_HYPOTHESIS",
    "UNKNOWN",
})

# Verbs whose presence in recommended_next_step signals a direct
# automation/fix instruction rather than an investigation/measurement
# step. Deliberately small and literal — see BN-R-9.
ACTION_VERB_BLOCKLIST: FrozenSet[str] = frozenset({
    "automate", "deploy", "replace", "delete", "execute",
})


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({"id", "system_map_ref"}))
INVOLVEMENT = FieldGroup("involvement", frozenset({"involved_node_ids"}))
CLASSIFICATION = FieldGroup("classification", frozenset({
    "bottleneck_type", "epistemic_status", "evidence",
}))
IMPACT = FieldGroup("impact", frozenset({"estimated_impact"}))
FRAMING = FieldGroup("framing", frozenset({"assumptions", "unknowns"}))
NEXT_STEP = FieldGroup("next_step", frozenset({"recommended_next_step"}))

ALL_GROUPS = (IDENTITY, INVOLVEMENT, CLASSIFICATION, IMPACT, FRAMING, NEXT_STEP)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(f for g in ALL_GROUPS for f in g.fields)

REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "system_map_ref", "involved_node_ids", "bottleneck_type",
    "epistemic_status", "estimated_impact", "assumptions", "unknowns",
    "recommended_next_step",
})

# Dotted paths required within the nested estimated_impact section.
REQUIRED_NESTED_PATHS: Mapping[str, FrozenSet[str]] = {
    "estimated_impact": frozenset({
        "value_at_risk", "delay_contribution", "failure_propagation_scope",
    }),
}

STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "system_map_ref", "bottleneck_type", "epistemic_status",
    "recommended_next_step",
})

LIST_FIELDS: FrozenSet[str] = frozenset({
    "involved_node_ids", "evidence", "assumptions", "unknowns",
})


def schema_hash() -> str:
    """Integrity-address the schema itself, same rationale as
    magl_schema.schema_hash."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_nested_paths": {
            k: sorted(v) for k, v in sorted(REQUIRED_NESTED_PATHS.items())
        },
        "bottleneck_types": sorted(BOTTLENECK_TYPES),
        "epistemic_classifications": sorted(EPISTEMIC_CLASSIFICATIONS),
        "evidence_required_classifications": sorted(EVIDENCE_REQUIRED_CLASSIFICATIONS),
        "action_verb_blocklist": sorted(ACTION_VERB_BLOCKLIST),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"institutional-bottleneck-schema-v{SCHEMA_VERSION}"
