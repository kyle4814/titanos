"""
TAAL (Threat Archetype Abstraction Layer) — threat_archetype Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a threat_archetype YAML
document may declare — taal/'s counterpart to magl/schema/magl_schema.py
and kpm/schemas/blueprint_atom.py. Same discipline: this module is data
(field names, enum universes, required-path tables), never behaviour. All
behaviour lives in taal/validators/validate_threat_archetype.py.

THE WHOLE POINT OF THIS COMPONENT

The governing directive requires that the "demonic archetype" symbolic
language (THE DECEIVER, THE PARASITE, THE IMPERSONATOR, ...) be preserved
as a human memory aid ONLY — never as something an enforcement or scoring
system reasons about. This schema enforces that split structurally, not
just by convention:

  - `symbolic_layer` holds the archetype name, the required literal
    `metaphor_status: SYMBOLIC_ONLY`, and a human-readable description.
    Nothing in `symbolic_layer` is read by any rule below except the
    presence/non-emptiness/literal-value of its own three fields. No rule
    number below ever branches on `symbolic_layer.human_description` or
    `symbolic_layer.archetype_name` content.

  - `technical_layer` (plus adversarial_goal / capability_request /
    boundary_analysis / evidence / behaviour / risk / controls / response
    / false_positive_controls / false_negative_controls / provenance) is
    the ONLY material any validator, gate, or scoring logic ever reasons
    about. Every enforcement-relevant TA-R-* rule below reads exclusively
    from these sections.

  - `metaphor_status` is required to be the exact literal string
    "SYMBOLIC_ONLY" — this is the structural guarantee, checked by the
    validator, that the symbolic layer can never silently claim to BE
    technical evidence. Any other value (including a plausible-sounding
    one like "VERIFIED" or "TECHNICAL") is rejected.

  taal/validators/tests/test_validate_threat_archetype.py::
  TestSymbolicTechnicalSeparation is the proof: two otherwise-identical
  documents differing ONLY in symbolic_layer content (one mundane, one
  maximally mythic) produce byte-identical technical findings.

WHY THIS FILE DOES NOT DEFINE ITS OWN CONFIDENCE VOCABULARY

`evidence.confidence` and `provenance.evidence_status` are NOT locally
authored enums. Both draw from the exact same closed vocabulary every
other claim in this codebase draws from —
kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS — imported, not copied,
at the bottom of this file. Inventing a parallel "threat confidence" scale
here would be the exact duplication this multi-schema exercise exists to
eliminate.
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
# vocabulary this schema depends on (epistemic classification).
# ─────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "EPISTEMIC_CLASSIFICATIONS",
    "METAPHOR_STATUS_REQUIRED_VALUE",
    "THREAT_CLASSES",
    "IMPACT_LEVELS",
    "REVERSIBILITY_VALUES",
    "RESPONSE_STATES",
    "REQUIRED_TOP_FIELDS", "REQUIRED_NESTED_PATHS",
    "BOUNDARY_CROSSED_FIELDS",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

# Reused verbatim from kpm/schemas/epistemic_types.py — not redefined.
EPISTEMIC_CLASSIFICATIONS: FrozenSet[str] = ALL_CLASSIFICATIONS

# The one legal value of symbolic_layer.metaphor_status. Any other string
# — including a missing field — is a structural rejection. This is the
# load-bearing literal that keeps the symbolic layer from ever claiming to
# be technical evidence.
METAPHOR_STATUS_REQUIRED_VALUE: str = "SYMBOLIC_ONLY"

THREAT_CLASSES: FrozenSet[str] = frozenset({
    "IDENTITY_DECEPTION",
    "AUTHORIZATION_ABUSE",
    "PRIVILEGE_ESCALATION_ATTEMPTS",
    "DATA_EXFILTRATION_PATTERNS",
    "INTEGRITY_MANIPULATION",
    "UNAUTHORIZED_EXECUTION",
    "PERSISTENCE_RISK",
    "RESOURCE_ABUSE",
    "DEPENDENCY_COMPROMISE",
    "SUPPLY_CHAIN_RISK",
    "SOCIAL_ENGINEERING_RISK",
    "AUTOMATION_ABUSE",
    "AGENT_PERMISSION_DRIFT",
    "CONTEXT_MANIPULATION",
    "PROMPT_INJECTION_RISK",
    "INSIDER_THREAT",
    "AVAILABILITY_DISRUPTION",
    "OBSERVABILITY_EVASION_RISK",
    "TRUST_BOUNDARY_CONFUSION",
    "THIRD_PARTY_DELEGATION_RISK",
})

IMPACT_LEVELS: FrozenSet[str] = frozenset({
    "NONE", "LOW", "MEDIUM", "HIGH", "SEVERE",
})

REVERSIBILITY_VALUES: FrozenSet[str] = frozenset({
    "FULLY_REVERSIBLE", "PARTIALLY_REVERSIBLE", "IRREVERSIBLE", "UNKNOWN",
})

RESPONSE_STATES: FrozenSet[str] = frozenset({
    "AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS", "REQUIRES_HUMAN_REVIEW",
    "QUARANTINED", "REFUSED", "UNKNOWN",
})

# boundary_analysis sub-fields whose non-emptiness (at least one of the
# four) is the structural definition of "this describes a threat, not
# normal operation".
BOUNDARY_CROSSED_FIELDS: tuple[str, ...] = (
    "trust_boundary_crossed", "privilege_boundary_crossed",
    "data_boundary_crossed", "execution_boundary_crossed",
)

# ─────────────────────────────────────────────────────────────
# Field groups (top-level `threat_archetype.*` keys)
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({"id", "version", "title"}))
SYMBOLIC = FieldGroup("symbolic_layer", frozenset({"symbolic_layer"}))
TECHNICAL = FieldGroup("technical_layer", frozenset({"technical_layer"}))
ADVERSARIAL_GOAL = FieldGroup("adversarial_goal", frozenset({"adversarial_goal"}))
CAPABILITY_REQUEST = FieldGroup("capability_request", frozenset({"capability_request"}))
BOUNDARY_ANALYSIS = FieldGroup("boundary_analysis", frozenset({"boundary_analysis"}))
EVIDENCE = FieldGroup("evidence", frozenset({"evidence"}))
BEHAVIOUR = FieldGroup("behaviour", frozenset({"behaviour"}))
RISK = FieldGroup("risk", frozenset({"risk"}))
CONTROLS = FieldGroup("controls", frozenset({"controls"}))
RESPONSE = FieldGroup("response", frozenset({"response"}))
FP_CONTROLS = FieldGroup("false_positive_controls", frozenset({"false_positive_controls"}))
FN_CONTROLS = FieldGroup("false_negative_controls", frozenset({"false_negative_controls"}))
PROVENANCE = FieldGroup("provenance", frozenset({"provenance"}))

ALL_GROUPS = (
    IDENTITY, SYMBOLIC, TECHNICAL, ADVERSARIAL_GOAL, CAPABILITY_REQUEST,
    BOUNDARY_ANALYSIS, EVIDENCE, BEHAVIOUR, RISK, CONTROLS, RESPONSE,
    FP_CONTROLS, FN_CONTROLS, PROVENANCE,
)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS for f in g.fields
)

# Top-level keys required directly under `threat_archetype:`.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "version", "title",
    "symbolic_layer", "technical_layer", "adversarial_goal",
    "capability_request", "boundary_analysis", "evidence", "behaviour",
    "risk", "controls", "response",
    "false_positive_controls", "false_negative_controls", "provenance",
})

# Dotted paths required within nested sections (checked once the parent
# section itself is confirmed present and is a mapping).
REQUIRED_NESTED_PATHS: Mapping[str, FrozenSet[str]] = {
    "symbolic_layer": frozenset({
        "archetype_name", "metaphor_status", "human_description",
    }),
    "technical_layer": frozenset({
        "threat_class", "behaviour_class", "target_classes", "asset_classes",
    }),
    "adversarial_goal": frozenset({"primary"}),
    "evidence": frozenset({"confidence", "unknowns"}),
    "behaviour": frozenset({"observable_indicators"}),
    "risk": frozenset({
        "confidentiality_impact", "integrity_impact", "availability_impact",
        "blast_radius", "reversibility",
    }),
    "controls": frozenset({"detection"}),
    "response": frozenset({"default_state"}),
    "provenance": frozenset({"evidence_status", "last_reviewed"}),
}


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    magl_schema.schema_hash / blueprint_atom.schema_hash): a claimed
    threat_archetype schema version should be checkable against what this
    validator actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_nested_paths": {
            k: sorted(v) for k, v in sorted(REQUIRED_NESTED_PATHS.items())
        },
        "threat_classes": sorted(THREAT_CLASSES),
        "impact_levels": sorted(IMPACT_LEVELS),
        "reversibility_values": sorted(REVERSIBILITY_VALUES),
        "response_states": sorted(RESPONSE_STATES),
        "metaphor_status_required_value": METAPHOR_STATUS_REQUIRED_VALUE,
        "epistemic_classifications": sorted(EPISTEMIC_CLASSIFICATIONS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"taal-threat-archetype-schema-v{SCHEMA_VERSION}"
