"""
Blueprint Atom Schema (§Phase 3 of the Knowledge Production Machine directive).

WHAT THIS FILE IS

The canonical, versioned definition of what fields a Blueprint Atom YAML may
declare — the structural counterpart to schema/artifact_schema.py, but for
"blueprint" documents rather than "artifact" documents. Same discipline:
MACHINE_VERIFIABLE_FIELDS vs HUMAN_JUDGMENT_FIELDS is the load-bearing split,
everything else is bookkeeping.

WHY THE SPLIT MATTERS (same reasoning as artifact_schema.py)

A required field being present, an enum value being one of the declared set,
a list being non-empty — these are provable. "This is the smallest next
step." "This purpose is well-framed." "This threat model is complete." —
those are human judgments the schema lets a blueprint CARRY but never lets
the validator manufacture a verdict about.

WHAT A BLUEPRINT ATOM IS

A blueprint atom is a single unit of "what we intend to build and why",
sitting between distilled knowledge (source artifacts) and implementation.
It carries its own epistemic classification (is this a verified fact we're
building on, or a speculative hypothesis we're testing?), its own promotion
state machine position, and an explicit falsifiability requirement
(acceptance_criteria) — a blueprint with no way to check it's done is a
structural defect, not a stylistic gap.

NESTED STRUCTURE

Unlike artifact_schema.py's flat field list, a blueprint atom is a nested
document (`blueprint:` at top level, with structured sub-sections such as
`classification:`, `implementation:`, `promotion:`, `rollback:`, `audit:`).
This module models that with NESTED_REQUIRED_FIELDS (dotted paths) alongside
the flat REQUIRED_FIELDS used for top-level presence checks, and dedicated
enum tables for the nested enum fields (`status`, `classification.primary`,
`classification.confidence`, `promotion.current_gate`).

SCHEMA VERSIONING

Same integrity-addressing pattern as artifact_schema.py: schema_hash() over
the canonical field list, so a blueprint's declared shape can be checked
against what this validator actually implements rather than assumed
compatible.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import FrozenSet, Mapping

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "MACHINE_VERIFIABLE_FIELDS", "HUMAN_JUDGMENT_FIELDS",
    "REQUIRED_TOP_FIELDS", "REQUIRED_NESTED_PATHS",
    "STATUS_VALUES", "EPISTEMIC_CLASSIFICATIONS", "CONFIDENCE_VALUES",
    "NON_STABLE_PROMOTABLE_CLASSIFICATIONS",
    "LIST_FIELDS", "STRING_FIELDS",
    "schema_hash", "FieldGroup",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

STATUS_VALUES: FrozenSet[str] = frozenset({
    "RAW", "DISTILLED", "PROVISIONAL", "TESTED", "CONTESTED",
    "QUARANTINED", "HUMAN_REVIEW", "STABLE", "DEPRECATED", "SUPERSEDED",
})

EPISTEMIC_CLASSIFICATIONS: FrozenSet[str] = frozenset({
    "VERIFIED_FACT",
    "EVIDENCE_SUPPORTED_MODEL",
    "IMPLEMENTED_SYSTEM",
    "TECHNICAL_DESIGN",
    "SOFTWARE_REQUIREMENT",
    "POLICY_REQUIREMENT",
    "ARCHITECTURAL_METAPHOR",
    "SYMBOLIC_DOCTRINE",
    "CREATIVE_CONCEPT",
    "SPECULATIVE_HYPOTHESIS",
    "SCIENTIFIC_CLAIM_REQUIRING_EVIDENCE",
    "HISTORICAL_CLAIM_REQUIRING_EVIDENCE",
    "UNVERIFIED_EXTERNAL_CLAIM",
    "PERSONAL_EXPERIENCE",
    "UNKNOWN",
})

CONFIDENCE_VALUES: FrozenSet[str] = frozenset({"LOW", "MEDIUM", "HIGH"})

# Epistemic classifications that are inherently interpretive/unfalsifiable —
# a directive-level rule (belt-and-suspenders alongside whatever promotion
# state machine another component enforces): these can never be promoted to
# STABLE. A "creative concept" or "speculative hypothesis" declared STABLE is
# a category error, not an achievement.
NON_STABLE_PROMOTABLE_CLASSIFICATIONS: FrozenSet[str] = frozenset({
    "CREATIVE_CONCEPT", "SPECULATIVE_HYPOTHESIS", "SYMBOLIC_DOCTRINE",
})

# ─────────────────────────────────────────────────────────────
# Field groups (top-level `blueprint.*` keys)
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]
    verifiable: bool  # True = machine-verifiable, False = human-judgment


IDENTITY = FieldGroup("identity", frozenset({
    "id", "title", "version", "status", "domain", "source_artifacts",
}), verifiable=True)  # existence/shape/enum-membership checkable

PROVENANCE = FieldGroup("provenance", frozenset({
    "provenance",
}), verifiable=True)  # structural shape (immutable_source_refs /
# interpretations are lists) is checkable; whether an interpretation is a
# FAIR reading of its source is not

CLASSIFICATION = FieldGroup("classification", frozenset({
    "classification",
}), verifiable=True)  # membership of classification.primary/confidence in
# their declared enums is checkable

FRAMING = FieldGroup("framing", frozenset({
    "purpose", "problem", "constraints", "assumptions", "unknowns",
    "non_goals",
}), verifiable=False)  # "is this purpose well-framed" is a human judgment;
# schema only checks non-emptiness of purpose/problem, not their quality

INTERFACE = FieldGroup("interface", frozenset({
    "inputs", "outputs", "invariants", "interfaces", "dependencies",
}), verifiable=True)  # presence/shape (lists) checkable

RISK = FieldGroup("risk", frozenset({
    "threat_model", "failure_modes", "controls",
}), verifiable=False)  # completeness of a threat model is a human judgment;
# schema only checks shape

IMPLEMENTATION = FieldGroup("implementation", frozenset({
    "implementation",
}), verifiable=True)  # smallest_next_step non-empty and
# acceptance_criteria non-empty are both provable structural facts

VERIFICATION = FieldGroup("verification", frozenset({
    "verification",
}), verifiable=True)  # shape (tests/evidence_required are lists) checkable;
# whether the tests are the RIGHT tests is not

DISSENT = FieldGroup("dissent", frozenset({
    "dissent",
}), verifiable=False)  # alternative models / unresolved objections are
# content, not structurally verifiable

PROMOTION = FieldGroup("promotion", frozenset({
    "promotion",
}), verifiable=True)  # current_gate enum membership AND its agreement with
# `status` are both provable structural facts

ROLLBACK = FieldGroup("rollback", frozenset({
    "rollback",
}), verifiable=True)  # reversible is boolean; recovery_procedure
# required-when-reversible is a provable conditional structural fact

AUDIT = FieldGroup("audit", frozenset({
    "audit",
}), verifiable=True)  # created_by non-empty, reviewed_by/timestamps/hashes
# shape checkable; whether the review was any GOOD is not

ALL_GROUPS = (
    IDENTITY, PROVENANCE, CLASSIFICATION, FRAMING, INTERFACE, RISK,
    IMPLEMENTATION, VERIFICATION, DISSENT, PROMOTION, ROLLBACK, AUDIT,
)

MACHINE_VERIFIABLE_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS if g.verifiable for f in g.fields
)
HUMAN_JUDGMENT_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS if not g.verifiable for f in g.fields
)

# Top-level keys required directly under `blueprint:`.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "title", "version", "status", "classification", "purpose",
    "problem", "implementation", "promotion", "rollback", "audit",
})

# Dotted paths required within nested sections (checked once the parent
# section itself is confirmed present and is a mapping).
REQUIRED_NESTED_PATHS: Mapping[str, FrozenSet[str]] = {
    "classification": frozenset({"primary", "confidence"}),
    "implementation": frozenset({"smallest_next_step", "acceptance_criteria"}),
    "promotion": frozenset({"current_gate"}),
    "rollback": frozenset({"reversible"}),
    "audit": frozenset({"created_by"}),
}

# Fields whose value, if present, must be a list.
LIST_FIELDS: FrozenSet[str] = frozenset({
    "domain", "source_artifacts", "constraints", "assumptions", "unknowns",
    "non_goals", "inputs", "outputs", "invariants", "threat_model",
    "failure_modes", "controls", "interfaces", "dependencies",
})

# Fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "title", "version", "purpose", "problem",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    artifact_schema.schema_hash): a claimed blueprint schema version should
    be checkable against what this validator actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_nested_paths": {
            k: sorted(v) for k, v in sorted(REQUIRED_NESTED_PATHS.items())
        },
        "machine_verifiable_fields": sorted(MACHINE_VERIFIABLE_FIELDS),
        "human_judgment_fields": sorted(HUMAN_JUDGMENT_FIELDS),
        "status_values": sorted(STATUS_VALUES),
        "epistemic_classifications": sorted(EPISTEMIC_CLASSIFICATIONS),
        "confidence_values": sorted(CONFIDENCE_VALUES),
        "non_stable_promotable_classifications": sorted(NON_STABLE_PROMOTABLE_CLASSIFICATIONS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"blueprint-atom-schema-v{SCHEMA_VERSION}"
