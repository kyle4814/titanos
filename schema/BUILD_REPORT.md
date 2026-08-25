# Schema — Build Report

The earliest subsystem in this repository. Retroactive report — written
2026-08-25 in response to `foundation/sentinel.py::pulse_sweep()`
repeatedly flagging this subsystem as missing the audit-trail document
every sibling subsystem carries (`PARETO_FRONTIER.md` FRONTIER-011).

## What this subsystem is

The canonical Artifact YAML schema and its validator — the load-bearing
split every later validator in this repository copies: which fields are
MACHINE_VERIFIABLE (a schema/validator can prove a violation) vs.
HUMAN_JUDGMENT (a human decides, the schema only carries the field).

## Files

| Component | File | Purpose |
|---|---|---|
| Schema | `schema/artifact_schema.py` | Canonical field list, machine-verifiable/human-judgment split, `schema_hash()` for declared-vs-implemented drift detection |
| Validator | `schema/validator.py` | "Does this artifact conform to the declared schema, structurally, deterministically, without executing anything it contains?" — nothing about truth, safety, or provenance (those are `firewall/`'s job) |

## Tests

`schema/` + `schema/validators/tests` (via `python3 -m unittest discover
-s schema -p "test_*.py"`): 67 tests, passing as of 2026-08-25.

## Design pattern this subsystem originated

The fail-closed outer wrapper (a top-level try/except converting any
unforeseen exception into a structured rejection, "rule R-0") and the
YAML hardening pattern (`_BoundedSafeLoader`, duplicate-key detection,
size/node/depth ceilings checked before construction, `RecursionError`
caught at both compose and construct stages) were both born here after
two real bugs were found running this validator against the real
3,058-file legacy YAML corpus (`failures/FAILURE_ARCHIVE.md` F-009/F-010)
— every later validator in this repository (`kpm/`, `magl/`, `rpa/`,
`taal/`, `narrative/`) replicates this pattern deliberately, not by
coincidence.

## Known limitations

Does not answer truth ("is this artifact true?" — `firewall/dissent.py`
+ human review), safety ("is this safe to run?" — `firewall/gate.py` +
`firewall/quarantine.py`), or provenance (not implemented at this layer)
— by design, not omission; those are separate, later subsystems'
responsibility.

## Human decisions required

None specific to this subsystem beyond the standing repository-wide
items already tracked in `HUMAN_DECISIONS.md`.

## Next smallest work cell

None currently identified — this subsystem is stable, fully tested, and
has had no open frontier item against it in any cycle to date.
