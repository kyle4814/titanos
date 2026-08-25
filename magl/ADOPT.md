# Adopting `magl/`

External-facing packaging doc — FRONTIER-008's fourth instance, same
template as `firewall/`, `schema/`, `kpm/`'s `ADOPT.md`. Distinct from
`magl/BUILD_REPORT.md` (internal audit trail).

## Thesis

MAGL-Ω, "the Grand Exchange": a schema + validator + registry +
composition-checking engine for declaring, cataloguing, and safely
combining capability modules. Binds `classification.epistemic_status`
and `lifecycle.status` to `kpm`'s existing controlled vocabularies
rather than inventing new ones — this subsystem is a consumer of `kpm`'s
epistemic vocabulary and `firewall`'s append-only/no-delete house style,
not a parallel system. Zero runtime dependency beyond PyYAML.

## Quickstart

The exact minimum-viable loop this subsystem's own `test_end_to_end.py`
demonstrates — VALID MAGL → VALIDATED → CATALOGUED:

```python
import yaml
from pathlib import Path
from magl.validators.validate_magl import validate_magl
from magl.registry.catalogue import MAGLEntry, MAGLCatalogue

text = Path("magl/fixtures/valid_magl.yaml").read_text()
result = validate_magl(text)
assert result.status == "VALID", result.issues

doc = yaml.safe_load(text)["magl"]
entry = MAGLEntry(
    magl_id=doc["id"], version=doc["version"], name=doc["name"],
    domain=tuple(doc["classification"]["domain"]),
    capability_type=tuple(doc["classification"]["capability_type"]),
    epistemic_status=doc["classification"]["epistemic_status"],
    maturity=doc["classification"]["maturity"],
    dependencies_required=tuple(doc["dependencies"]["required"]),
    dependencies_incompatible=tuple(doc["dependencies"]["incompatible_with"]),
    lifecycle_status=doc["lifecycle"]["status"],
    license=doc["provenance"]["license"],
    content_hash=doc["audit"]["content_hash"] or "sha256:" + "0" * 64,
)
catalogue = MAGLCatalogue()
catalogue.register(entry)          # or register_checked() -- see below
found = catalogue.get(doc["id"], doc["version"])
```

```python
from magl.composition.engine import MAGLSummary, check_composition
# check_composition() runs 9 steps (schema/jurisdiction/dependencies/
# incompatibility/side-effects/circularity/privilege-escalation/
# invariants/provenance) and returns a CompositionReport whose
# .fatal_findings() is empty only if every step passed
```

## Failure cases

- `MAGLCatalogue.register()` (plain) performs **no composition check** —
  it will accept an entry that `check_composition()` would refuse.
  `register_checked()` is the guarded sibling: it raises
  `CompositionRefusedAtRegistration` if the composition report has any
  fatal finding. If your integration needs the safety guarantee, call
  `register_checked()`, not `register()` — this is a real, named,
  deliberately-left-open gap (`PARETO_FRONTIER.md`/`NEXT_MOVE.md`'s
  "one named watch item": `register()`'s only current caller anywhere in
  this repository is `register_checked()` itself, after the check
  already passed — no live bypass exists today, but a future caller
  using `register()` directly would reopen it).
- `validate_magl()` never raises on malformed input — same fail-closed
  wrapper and `_BoundedSafeLoader` hardening as `schema/validator.py`
  (duplicate-key detection, size/depth bounds, `RecursionError` caught
  at both compose and construct stages).
- `MAGLRelationshipGraph.detect_cycles()` — a real dependency graph
  cycle is returned as data (a list of cycles), never silently ignored
  or auto-broken.

## Threat model

- **In scope:** privilege escalation across composed capabilities
  (`_step7_privilege_escalation`) — narrower than general escalation
  analysis by design, named as an open human-judgment call in
  `HUMAN_DECISIONS.md` item 7, not a gap this module hides.
- **Out of scope:** the `register()`/`register_checked()` split above —
  documented, not silently unsafe, but a caller must choose correctly.

## Limitations

No persistence layer (in-memory per process instance, same as `kpm/`'s
stores). No cryptographic signing. No network calls.

## Changelog

- 2026-08-25: initial build, 3-agent parallel construction + direct
  integration pass. 9 of 11 "Obelisk Enforcement Contract" invariants
  found already implemented elsewhere in this repo (recorded in
  `magl/constitution/OBELISK_INVARIANTS.yaml`, not re-built).
- `magl/`'s own suite: 80 tests as of 2026-08-26 (BUILD_REPORT's 93-count
  included manual compiler-check items not run via `unittest`).

## Fork guide

`magl/schema/`, `magl/validators/`, `magl/registry/`, `magl/composition/`
import `kpm.schemas.epistemic_types` and `kpm.promotion.state_machine`'s
vocabulary — forking `magl/` alone requires `kpm/` alongside it, or
replacing those two imports with an equivalent vocabulary. Run
`python3 -m unittest discover -s magl -p "test_*.py"` to confirm the
fork is intact (80 tests as of 2026-08-26).

## Integration interfaces

`MAGLEntry`, `Issue`, `ValidationResult`, `MAGLSummary`, `Finding`,
`CompositionReport`, `Relationship` are the public data shapes —
dataclasses, `to_dict()` provided where serialization is expected.
`register()` vs `register_checked()` is the one interface decision a
caller must make deliberately (see Failure cases).

## Contribution path

None yet — see `firewall/ADOPT.md`'s note; same repository-wide state.
`.github/workflows/tests.yml` runs this subsystem's suite on every push/
PR to `kyle4814/titanos`.

## Machine-readable manifest

```yaml
subsystem: magl
public_modules:
  - magl.schema.magl_schema
  - magl.validators.validate_magl
  - magl.registry.catalogue
  - magl.composition.engine
runtime_dependencies: [PyYAML]
depends_on_subsystem: [kpm]
test_command: python3 -m unittest discover -s magl -p "test_*.py"
test_count: 80
known_limitation: register() has no composition check, register_checked() does -- caller must choose
provenance: magl/BUILD_REPORT.md, magl/constitution/OBELISK_INVARIANTS.yaml
```
