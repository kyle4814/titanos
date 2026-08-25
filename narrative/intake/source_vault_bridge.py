"""
Source Vault -> Narrative Atom bridge (`REALITY_INTAKE_MEMBRANE_001`).

WHAT WAS FOUND, NOT BUILT

The "reality intake membrane" this directive asked for already exists:
`kpm/source-vault/registry.py::SourceRegistry`. It already does exactly
what was requested — hash the original bytes, archive them
content-addressed and idempotently, record provenance (`provenance_
status` defaults to `"UNVERIFIED"` — ingested is never automatically
believed), and reject an out-of-vocabulary `source_type` with a
structured, catchable exception rather than silently substituting a
default. Building a second membrane would have duplicated it.

THE ACTUAL GAP

`SourceRegistry` (intake) and `narrative/schema/narrative_atom.py` +
`narrative/store/narrative_atom_store.py` (digestion) had never been
connected — zero references either direction, confirmed by grep before
writing this file. This module is the thin bridge, mirroring this
session's own established adapter pattern (`foundation/
queue_worker_adapter.py`, `taal/gate/permission_request_adapter.py`):
neither source module is modified.

WHY source_type CANNOT BE MECHANICALLY DERIVED

`SourceRegistry.SOURCE_TYPES` classifies by MEDIUM (`"yaml"`,
`"markdown"`, `"image"`, ...). `narrative_atom.SOURCE_TYPES` classifies
by DOMAIN (`"SCIENCE"`, `"MYTHOLOGY"`, `"TECHNICAL_KNOWLEDGE"`, ...) —
a genuinely different axis, not a synonym mapping. Same for
`epistemic_layer`/`evidence_status`/`confidence`: these are judgment
calls this codebase has never allowed a schema or adapter to infer
automatically (`narrative_atom.py`'s own `NA-R-12` rule exists
specifically to stop a document asserting its own epistemic status
unchecked). The bridge therefore takes these as required, explicit
caller-supplied arguments — it maps only what `SourceRecord` actually,
mechanically, honestly provides: `content_hash` -> `provenance_hash`
(already the exact `"sha256:<64 hex>"` format `narrative_atom.py`'s
NA-R-9 rule requires — verified by test, not assumed), `ingestion_
timestamp` -> `timestamp`, `source_location` -> `source_reference`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

# kpm/source-vault/ is a hyphenated directory name -- not a legal Python
# package identifier, so `registry.SourceRecord` cannot be reached via a
# dotted `kpm.source_vault...` import (same fact `kpm/source-vault/
# tests/test_registry.py` already documents). This module only needs
# SourceRecord for a type hint -- `from __future__ import annotations`
# makes annotations lazy strings, never evaluated at runtime, so no
# sys.path workaround is needed here; only a real caller/test that
# constructs a SourceRecord needs that workaround, exactly as `kpm/
# source-vault/tests/test_registry.py` already does.
if TYPE_CHECKING:
    from kpm.source_vault.registry import SourceRecord  # type: ignore

__all__ = ["source_record_to_narrative_atom_yaml"]


def source_record_to_narrative_atom_yaml(
    record: SourceRecord,
    *,
    atom_id: str,
    raw_fragment: str,
    domain: str,
    narrative_source_type: str,
    epistemic_layer: str,
    evidence_status: str,
    confidence: str,
    uncertainty: str = "",
    harm_risk: str = "NONE",
) -> str:
    """Build a `narrative_atom:` YAML document from an already-ingested
    `SourceRecord` plus the caller's explicit epistemic judgment.

    Does not itself validate the result — callers run it through
    `narrative.validators.validate_narrative_atom.validate_narrative_
    atom()` exactly as every other narrative atom in this repository is
    validated, the same two-step discipline (build, then validate)
    already established for every schema in this codebase.
    """
    return f"""
narrative_atom:
  id: "{atom_id}"
  timestamp: "{record.ingestion_timestamp}"
  source_reference: "{record.source_location} (SourceRegistry artifact {record.artifact_id})"
  source_type: {narrative_source_type}
  raw_fragment: "{raw_fragment}"
  domain: "{domain}"
  epistemic_layer: {epistemic_layer}
  evidence_status: {evidence_status}
  confidence: {confidence}
  uncertainty: "{uncertainty}"
  harm_risk: {harm_risk}
  provenance_hash: "{record.content_hash}"
  promotion_status: RAW
"""
