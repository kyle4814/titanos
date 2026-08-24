# Provenance

## What lives where

Cryptographic provenance (content-addressed identity, manifest signing,
lineage cycle detection) is implemented in the separate `titanos-provenance`
repository (`STATE_RANK`, `combine()`, `verify_lineage()`), not in this
one. `provenance/seal.py` in this repository is a *consumer* of that
package — it seals this library's own artifacts, it is not a
reimplementation of provenance verification. **SPECIFICATION.**

## What this repository's schema checks about provenance (and what it doesn't)

`schema/artifact_schema.py`'s `PROVENANCE` field group and
`validator.py`'s R-8 rule check *shape and self-consistency*: an artifact
cannot declare itself as its own parent or root origin. This is a
structural sanity check, not a provenance verification — **VERIFIED
PROPERTY for the narrow claim** (`schema/tests/test_validator.py::TestImpossibleProvenance`),
**explicitly NOT a claim that a declared `root_origin` string is real**
(`schema/tests/test_false_negatives.py::TestProvenanceAndSourceSubstitution::test_syntactically_valid_but_unverifiable_root_origin_passes_schema`
documents this boundary directly — passing schema validation with a
fabricated-but-well-formed origin is the CORRECT, intended behaviour of
this layer, proving where its authority ends).

## Ancestry collapse

`firewall/gate.py::collapse_ancestry()` counts distinct `root_origin`
values among corroborating artifacts, not artifact count — five artifacts
from one origin collapse to one, and the gate routes that to
`REQUIRES_HUMAN_REVIEW` rather than treating repetition as confirmation.
**VERIFIED PROPERTY** (`firewall/tests/test_firewall.py::TestIndependence`).

## UNRESOLVED

Whether/how this repository should call into `titanos-provenance` to
actually verify a claimed lineage chain, versus continuing to check shape
only. No decision made; the two packages remain independently useful and
independently testable in the meantime.
