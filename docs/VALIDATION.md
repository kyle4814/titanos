# Validation

Source: `schema/validator.py::validate_artifact()`.

## The distinction this module exists to preserve

A parser answers "can this be structurally understood." A validator
answers "does it conform to the declared schema." Neither answers "is it
true." `validate_artifact()` returns `VALID` / `INVALID` / `UNKNOWN` — that
vocabulary is deliberately disjoint from `gate.py`'s
`AUTHORIZED`/`REFUSED`/`QUARANTINED`/`REQUIRES_HUMAN_REVIEW` and from
`dissent.py`'s `SUPPORTED`/`DISPUTED`/`REFUTED`. **VALID never means
true, safe, or authorized — SPECIFICATION, enforced by keeping these three
vocabularies in three separate modules that never share a status enum.**

## Rules (R-0 .. R-12)

| Rule | Checks |
|---|---|
| R-0 | internal validator error — caught, never propagated (fail-closed, not fail-open) |
| R-1 | YAML parses, within structural ceilings (size/nodes/depth), no duplicate keys |
| R-2 | required fields present |
| R-3 | enum fields hold only declared values |
| R-4 | field types match schema |
| R-5 | hash fields match `sha256:<64 hex>` shape |
| R-6 | signature field shape only — never cryptographically verified here |
| R-7 | timestamps are valid RFC3339 |
| R-8 | no self-referential provenance (artifact as its own parent/root) |
| R-9 | schema_version matches the implemented version |
| R-10 | artifact does not declare system-only output fields about itself |
| R-11 | artifact does not declare rule/transition-redefinition fields |
| R-12 | mapping keys are strings (a real bug found against the live 3,058-file corpus — see below) |

Every rejection carries `what`/`why`/`where`/`rule`/`evidence` — **VERIFIED
PROPERTY**, every issue is a structured `Issue` dataclass, never a bare
bool (`schema/tests/test_validator.py::TestValidArtifactPasses::test_result_never_a_bare_bool`).

## Structural ceilings

`MAX_DOCUMENT_BYTES = 2_000_000`, `MAX_NODES = 50_000`, `MAX_DEPTH = 64`.
Enforced before construction via `yaml.compose()` node counting, with a
`RecursionError` catch around both compose and construct — PyYAML's own
composer is recursive, so a sufficiently deep alias chain can blow the
Python call stack before the node-count ceiling gets a chance to run.
Found and fixed during adversarial testing, not assumed safe —
**VERIFIED PROPERTY**
(`schema/tests/test_false_negatives.py::TestYamlAliasAndAnchorTricks`).

## Never fail open

`validate_artifact()` wraps its entire body in a try/except; any unforeseen
exception becomes an `INVALID` result with rule `R-0`, never propagates.
This was not theoretical: running the validator against the real,
unmodified 3,058-file legacy corpus crashed on a file using a boolean YAML
key (`true: ...`) before R-12 and this wrapper existed. **VERIFIED
PROPERTY, found against real data**
(`schema/tests/test_real_corpus_regressions.py`).

## Never fail closed by accident either

A file that merely doesn't conform to this schema (2,952 of 3,058 real
legacy files) is `INVALID` under this schema — not `CONTAMINATED`,
not `UNSAFE`. `legacy/classify.py` and `legacy/DECISION_PACKET.md` are
explicit that non-conformance to a schema invented after a file was
written is not evidence of anything about that file.
