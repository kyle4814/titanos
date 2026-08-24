"""
TitanOS Artifact YAML Schema (§Phase 2).

WHAT THIS FILE IS

A canonical, versioned definition of what fields an Artifact YAML may
declare, and — critically — which of those fields are MACHINE-VERIFIABLE
and which are HUMAN-JUDGMENT. That split is the load-bearing property of
this file. Everything else is bookkeeping around it.

WHY THE SPLIT MATTERS

A hash either matches or it doesn't. A timestamp either parses or it
doesn't. Those are machine-verifiable: the validator can prove them true or
false and the proof is reproducible by anyone re-running it.

"This artifact is trustworthy." "This claim is correct." "This source is
credible." Those are human-judgment fields. The schema lets an artifact
CARRY a judgment (as a claim, with whoever asserted it), but the validator
must never treat the presence of a judgment field as if it were a proof.
Conflating the two is exactly how a cryptographic signature over a document
gets mistaken for a certificate of truth about the document's contents —
the signature proves who signed, never what they were right about.

SCHEMA VERSIONING

This module defines SCHEMA_VERSION. A schema version is itself
integrity-addressable (schema_hash() over its canonical field list) so an
artifact's declared schema_version can be checked against what the
validator actually implements, rather than assumed compatible. Schema
evolution is an explicit, versioned event — never an in-place edit.

UNKNOWN FIELDS

A field the validator doesn't recognise is neither an error nor a free
pass. It is preserved verbatim (§Phase 6 preservation invariant) and
reported as `unknown_fields`, and it categorically does NOT become trusted
just because it parsed. A future schema version might promote it; today's
validator must not guess.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, FrozenSet, Mapping

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "MACHINE_VERIFIABLE_FIELDS", "HUMAN_JUDGMENT_FIELDS",
    "REQUIRED_FIELDS", "ENUM_FIELDS",
    "schema_hash", "FieldGroup",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Field groups
# ─────────────────────────────────────────────────────────────
# Grouped by section per the directive. Each entry: field name -> group.
# Group is either "identity", "provenance", "integrity", "status",
# "classification", "structure", "epistemic", "review".


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]
    verifiable: bool  # True = machine-verifiable, False = human-judgment


IDENTITY = FieldGroup("identity", frozenset({
    "artifact_id", "artifact_type", "schema_version", "created_at",
    "created_by",
}), verifiable=True)  # existence/shape checkable; author identity is a claim, see note below

PROVENANCE = FieldGroup("provenance", frozenset({
    "root_origin", "parent_origins", "source_identity", "provenance_chain",
}), verifiable=True)  # structural — cycle/reference checks are provable

INTEGRITY = FieldGroup("integrity", frozenset({
    "content_hash", "canonical_hash", "signature", "signature_status",
}), verifiable=True)  # hash match / signature verification is provable

STATUS = FieldGroup("status", frozenset({
    "contamination_state", "validation_status", "quarantine_status",
}), verifiable=True)  # must be one of the enumerated states — checkable

CLASSIFICATION = FieldGroup("classification", frozenset({
    "classification", "memetic_profile",
}), verifiable=True)  # membership in the declared taxonomy is checkable;
# note: the memetic *scores themselves* are asserted by whatever computed
# them, not measured by this schema — the schema only checks their shape.

STRUCTURE = FieldGroup("structure", frozenset({
    "dependencies", "references", "governance_references",
    "doctrine_references", "evidence_references",
}), verifiable=True)  # reference existence / cycle-freedom is checkable

REVIEW = FieldGroup("review", frozenset({
    "review_history", "quarantine_metadata", "reviewed_by",
}), verifiable=True)  # presence/shape checkable; the review DECISION inside
# is a human judgment, not re-derivable by the validator

# ── The two fields the whole directive is actually about ──────────────
CLAIMS = FieldGroup("claims", frozenset({
    "claims",
}), verifiable=False)  # "what this artifact asserts is true" — content,
# not provable by structural validation, ever

TRUST_ASSERTIONS = FieldGroup("trust_assertions", frozenset({
    "trust_level", "credibility_assessment", "epistemic_confidence",
}), verifiable=False)  # a human or agent's OPINION about the artifact —
# schema-valid presence of this field must never be read as the validator
# having confirmed the opinion

ALL_GROUPS = (IDENTITY, PROVENANCE, INTEGRITY, STATUS, CLASSIFICATION,
              STRUCTURE, REVIEW, CLAIMS, TRUST_ASSERTIONS)

MACHINE_VERIFIABLE_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS if g.verifiable for f in g.fields
)
HUMAN_JUDGMENT_FIELDS: FrozenSet[str] = frozenset(
    f for g in ALL_GROUPS if not g.verifiable for f in g.fields
)

REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    "artifact_id", "artifact_type", "schema_version", "created_at",
    "content_hash", "contamination_state", "classification",
})

ENUM_FIELDS: Mapping[str, FrozenSet[str]] = {
    "contamination_state": frozenset({
        "CLEAN", "UNVERIFIED", "DISPUTED", "SUSPICIOUS", "CONTAMINATED",
        "QUARANTINED", "VERIFIED", "AUTHORIZED", "REJECTED", "ARCHIVED",
    }),
    "classification": frozenset({
        "FACTUAL_CLAIM", "EVIDENCE", "INFERENCE", "HYPOTHESIS", "SPECULATION",
        "PHILOSOPHY", "METAPHOR", "MYTH", "NARRATIVE", "VALUE_JUDGMENT",
        "GOVERNANCE_RULE", "CONSTITUTIONAL_RULE", "EXECUTABLE_POLICY",
        "UNKNOWN", "CONTAMINATED",
    }),
    "signature_status": frozenset({"UNSIGNED", "SIGNED", "INVALID", "UNKNOWN"}),
    "validation_status": frozenset({
        "VALID", "INVALID", "UNKNOWN", "QUARANTINED", "CONTAMINATED", "VERIFIED",
    }),
}


def schema_hash() -> str:
    """Integrity-address the schema itself, so a claimed schema_version is
    checkable against what this validator actually implements — not just
    trusted because the string matches.
    """
    payload = {
        "version": SCHEMA_VERSION,
        "required_fields": sorted(REQUIRED_FIELDS),
        "machine_verifiable_fields": sorted(MACHINE_VERIFIABLE_FIELDS),
        "human_judgment_fields": sorted(HUMAN_JUDGMENT_FIELDS),
        "enum_fields": {k: sorted(v) for k, v in sorted(ENUM_FIELDS.items())},
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"artifact-schema-v{SCHEMA_VERSION}"
