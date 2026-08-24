# Artifact YAML Schema

Source of truth: `schema/artifact_schema.py`. This document summarizes it;
the module is authoritative if they ever disagree.

## Machine-verifiable vs. human-judgment fields

**SPECIFICATION**: a field is machine-verifiable only if a deterministic
check can prove it true or false from the artifact's own bytes plus fixed
rules — never from an opinion the artifact carries about itself.

| Group | Fields | Verifiable? |
|---|---|---|
| identity | artifact_id, artifact_type, schema_version, created_at, created_by | shape: yes |
| provenance | root_origin, parent_origins, source_identity, provenance_chain | structure: yes |
| integrity | content_hash, canonical_hash, signature, signature_status | shape: yes; cryptographic truth: NOT verified (see THREAT_MODEL.md) |
| status | contamination_state, validation_status, quarantine_status | enum membership: yes |
| classification | classification, memetic_profile | taxonomy membership: yes; the scores themselves are asserted, not measured |
| structure | dependencies, references, governance/doctrine/evidence_references | reference shape: yes |
| review | review_history, quarantine_metadata, reviewed_by | presence/shape: yes; the decision inside: no |
| **claims** | claims | **no — content, never provable by structure** |
| **trust_assertions** | trust_level, credibility_assessment, epistemic_confidence | **no — opinion, schema-valid presence != confirmed** |

## Required fields (`REQUIRED_FIELDS`)

`artifact_id`, `artifact_type`, `schema_version`, `created_at`,
`content_hash`, `contamination_state`, `classification`.

## Schema versioning

`SCHEMA_VERSION = "1.0.0"`. `schema_hash()` content-addresses the schema's
own field lists so a claimed `schema_version` string can be checked against
what's actually implemented, not merely string-matched. An artifact
declaring a version the validator doesn't implement is INVALID (rule R-9),
never assumed forward-compatible — **VERIFIED PROPERTY**
(`schema/tests/test_validator.py::TestSchemaVersionMismatch`).

## Unknown fields

Reported in `ValidationResult.unknown_fields`, never silently dropped and
never trusted. **VERIFIED PROPERTY**
(`schema/tests/test_validator.py::TestUnknownFieldsPreservedNotTrusted`).

## What this schema deliberately does not do

It does not define an "is trustworthy" field. `trust_level` and its
siblings are HUMAN_JUDGMENT fields precisely so that no future reader
mistakes their presence for a verified conclusion.
