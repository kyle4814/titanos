# Dissent

Source: `firewall/dissent.py`.

## The core rule

When sources disagree, the status is `DISPUTED`. Not `FALSE`, not
`RESOLVED`, not an average. Resolution requires evidence, never a vote
count — `resolve()` raises `ValueError` if `SUPPORTED`/`REFUTED` is
requested without `evidence_refs`. **VERIFIED PROPERTY**
(`firewall/tests/test_quarantine_dissent.py::TestDissentIsNotContamination::test_majority_cannot_resolve_without_evidence`).

## Shared ancestry cannot adjudicate itself

`_distinct_origins()` counts positions by `root_origin`, not by count.
Nine agents restating one spec collapse to one origin and cannot resolve a
dispute on their own agreement. **VERIFIED PROPERTY**
(`test_shared_ancestry_cannot_adjudicate_itself`).

## Minority positions survive

`resolve()` never removes a `Position` from `rec.positions`. A resolved
dispute still shows who disagreed and why, even after the majority won.
**VERIFIED PROPERTY** (`test_resolution_preserves_the_losing_position`,
`test_minority_positions_survive_resolution`).

## No delete surface

Same property as `QuarantineStore`, same test pattern
(`test_register_exposes_no_delete_surface`).

## The property that makes this a firewall component, not just a data
structure

`firewall/tests/test_firewall.py::TestNotAnIdeologicalFilter` proves a
governance rule *critical of TitanOS itself* is `AUTHORIZED` on the same
terms as any other rule. Criticism of the system is not routed through
`dissent.py` as if it were contamination — it never reaches dissent at
all unless someone actually disagrees with it. **VERIFIED PROPERTY, and
the one most worth re-checking after any future change to this module.**
