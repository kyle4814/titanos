# Adopting `schema/`

External-facing packaging doc — FRONTIER-008's second instance, same
template as `firewall/ADOPT.md`. Distinct from `BUILD_REPORT.md` (this
subsystem's internal audit trail).

## Thesis

The canonical Artifact YAML schema and its validator — the earliest
subsystem in this repository, and the split every later validator here
copies: MACHINE_VERIFIABLE (a schema/validator can prove a violation) vs.
HUMAN_JUDGMENT (a human decides; the schema only carries the field).
Answers "does this conform, structurally, deterministically" — not truth,
safety, or provenance. Zero runtime dependency beyond PyYAML; no
network, no external service.

## Quickstart

```python
from schema.artifact_schema import FieldGroup, schema_hash

schema_hash()   # declared-vs-implemented drift detector — compare
                # this value across versions to catch silent field drift
```

```python
from schema.validator import validate_artifact

result = validate_artifact(yaml_text)   # a plain str, never executed
if result.issues:
    for issue in result.issues:
        print(issue.to_dict())          # structured, not a raw exception
```

## Failure cases

- `validate_artifact()` never raises on malformed input — a fail-closed
  outer wrapper (rule R-0) converts any unforeseen exception into a
  structured `Issue` instead. If your integration expects a Python
  exception on bad YAML, it will not get one; check `result.issues`.
- The YAML loader is deliberately hardened (`_BoundedSafeLoader`):
  duplicate keys are rejected, and size/node/depth are bounded *before*
  construction, `RecursionError` caught at both compose and construct
  stages. A very large or deeply nested document will be rejected as an
  `Issue`, not hang the process — this was born from two real bugs found
  running this validator against a real 3,058-file legacy corpus
  (`failures/FAILURE_ARCHIVE.md` F-009/F-010), not theoretical hardening.
- `validate_artifact()` answers structural conformance only — a
  structurally valid artifact can still be false, unsafe, or
  unprovenanced. Do not treat a clean `ValidationResult` as a safety or
  truth verdict; that's `firewall/`'s job, not this module's.

## Threat model

- **In scope:** YAML bombs (billion-laughs / deeply nested / duplicate-
  key attacks) — the entire reason `_BoundedSafeLoader` exists.
- **Out of scope, by design:** truth, safety, provenance — this module
  never claims to answer those; conflating "passed schema validation"
  with "safe to trust" is a caller error, not a gap in this module.

## Limitations

No cryptographic signing, no network calls, no execution of the parsed
content under any circumstance (`yaml.SafeLoader`-derived only).

## Changelog

- Pre-existing, stable since early in this repository's history: no
  open frontier item has ever been raised against this subsystem
  specifically — every later subsystem needing YAML validation reused
  this pattern rather than finding a gap in it.

## Fork guide

`schema/artifact_schema.py` and `schema/validator.py` have no dependency
on any other subsystem in this repository — both import standalone.
To fork just this piece: copy `schema/` and its `tests/`, run
`python3 -m unittest discover -s schema -p "test_*.py"` to confirm the
fork is intact (67 tests as of 2026-08-25).

## Integration interfaces

`FieldGroup`, `Issue`, `ValidationResult` are the public data shapes —
plain dataclasses, `to_dict()` provided for serialization.
`validate_artifact(text: str) -> ValidationResult` is the sole public
entry point; `_validate_artifact_inner` and the loader internals are
private, not part of the contract.

## Contribution path

None yet — see `firewall/ADOPT.md`'s note; same repository-wide state.
`.github/workflows/tests.yml` runs this subsystem's suite on every push/
PR to `kyle4814/titanos`.

## Machine-readable manifest

```yaml
subsystem: schema
public_modules: [schema.artifact_schema, schema.validator]
runtime_dependencies: [PyYAML]
test_command: python3 -m unittest discover -s schema -p "test_*.py"
test_count: 67
known_limitation: answers structural conformance only, not truth/safety/provenance
provenance: schema/BUILD_REPORT.md
```
