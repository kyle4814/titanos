# Adopting `narrative/`

External-facing packaging doc — FRONTIER-008's eighth and final
instance, same template as the seven before it. Distinct from
`narrative/BUILD_REPORT.md` (internal audit trail).

## Thesis

The Narrative Atom: the one primitive `TITANOS_AKASHIC_NARRATIVE_
ENGINE.md`'s Five Records, Gold Ledger, and Isomorphism Engine all
operate on. `EPISTEMIC_LAYERS` is imported directly from
`kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS` — not a parallel
vocabulary. Real, non-synthetic use: `FIRST_PING.md` (this repository's
first proven external-reality exchange) ran through this subsystem's
intake bridge before classification.

## Quickstart

```python
from narrative.store.narrative_atom_store import NarrativeAtomStore

store = NarrativeAtomStore()
atom = store.register("NA-1", created_by="you")   # starts RAW
for state in ("OBSERVED", "CLASSIFIED", "CONNECTED", "CHALLENGED",
              "TESTED", "SUPPORTED"):
    store.promote("NA-1", to_state=state, reason="advancing")

store.promote("NA-1", to_state="CANONICAL_ABSTRACTION",
               reason="evidence-supported, independently reviewed",
               reviewed_by="someone_else")
# reviewed_by must differ from created_by -- self-canonization is refused
```

```python
from narrative.intake.source_vault_bridge import source_record_to_narrative_atom_yaml
# bridges an already-ingested kpm.source_vault.registry.SourceRecord
# into a narrative_atom YAML document -- the real path FIRST_PING.md's
# successor would take to go beyond raw classification into a full atom
```

## Failure cases

- `store.promote()` raises `IllegalAtomTransition` for any edge not in
  `PROMOTION_TRANSITIONS` — there is no shortcut from `RAW` straight to
  `CANONICAL_ABSTRACTION`; the full chain above is the only legal path.
- Promoting to `CANONICAL_ABSTRACTION` without `reviewed_by` raises
  (fail-closed: unknown review identity is not independent review), and
  `reviewed_by == created_by` raises `SelfCanonizationForbidden` — checked
  by value, not presence.
- `CANONICAL_ABSTRACTION` is **not eternal** — `CANONICAL_ABSTRACTION →
  CHALLENGED` is a legal edge; new contradicting evidence can reopen a
  canonized atom, same discipline as `kpm`'s `STABLE → DISPUTED`... this
  module's equivalent path.
- `AtomRecord.history` is a frozen tuple — `.append()` raises
  `AttributeError` (same `EPISTEMIC_INTEGRITY_002` fix as every other
  append-only record type in this repository).

## Threat model

- **In scope:** forged promotion history (frozen tuple, closed),
  self-canonization (refused by value comparison), an atom smuggling an
  unverified external claim in as fact via subjective-experience framing
  (`narrative/validators/validate_narrative_atom.py`'s `NA-R-12` rule —
  a `PERSONAL_EXPERIENCE` atom's `evidence_status: VERIFIED_FACT` is
  rejected unless a separate `external_explanation_status` field is
  independently `VERIFIED_FACT` too), self-sealing rhetoric blocking
  canonization (`NA-R-14`), popularity/authority-weight fields
  structurally rejected if present (`NA-R-15`).
- **Out of scope:** cross-atom referential integrity is a separate
  module — see `narrative/composition/checker.py`.

## Limitations

No persistence layer — `NarrativeAtomStore` is in-memory per process
instance, same as every store in this repository. Only 2 real
non-synthetic atoms exist anywhere in this repository so far
(`NA-INGEST-001`/`NA-INGEST-002`) — `PARETO_FRONTIER.md` FRONTIER-005
(query views, Gold Ledger) stays deliberately Blocked until more real
content exists; building views over near-empty content would be
speculative.

## Changelog

- 2026-08-25: schema + validator built first (`FRONTIER-000`), store
  built later (`FRONTIER-004`), intake bridge (`FRONTIER-MEMBRANE`),
  cross-atom referential integrity checker
  (`FRONTIER-NARRATIVE-REFCHECK`).
- 2026-08-25: `AtomRecord.history` frozen — same
  `EPISTEMIC_INTEGRITY_002` fix as every other record type.
- 2026-08-26: first real (non-synthetic) use — `FIRST_PING.md` ran a
  genuine external artifact (a GitHub Actions CI result) through this
  subsystem's neighboring pipeline for the first time.
- `narrative/`'s own suite: 88 tests as of 2026-08-26.

## Fork guide

`narrative/schema/narrative_atom.py` imports `kpm.schemas.
epistemic_types` for its classification vocabulary — forking `narrative/`
alone requires `kpm/` alongside it. `narrative/intake/source_vault_
bridge.py` additionally references `kpm.source_vault.registry.
SourceRecord` (type hint only, lazy via `from __future__ import
annotations` — no runtime import needed unless actually constructing
one). Run `python3 -m unittest discover -s narrative -p "test_*.py"` to
confirm the fork is intact (88 tests as of 2026-08-26).

## Integration interfaces

`AtomRecord` is the public data shape (`to_dict()` provided).
`NarrativeAtomStore.register()`/`.promote()`/`.get()` are the only
public store methods — no delete surface exists, matching
`SIGIL_LEXICON.md`'s `SIGIL.NO_DELETE_SURFACE`.

## Contribution path

None yet — see `firewall/ADOPT.md`'s note; same repository-wide state.
`.github/workflows/tests.yml` runs this subsystem's suite on every push/
PR to `kyle4814/titanos`.

## Machine-readable manifest

```yaml
subsystem: narrative
public_modules:
  - narrative.schema.narrative_atom
  - narrative.validators.validate_narrative_atom
  - narrative.store.narrative_atom_store
  - narrative.intake.source_vault_bridge
  - narrative.composition.checker
runtime_dependencies: [PyYAML]
depends_on_subsystem: [kpm]
test_command: python3 -m unittest discover -s narrative -p "test_*.py"
test_count: 88
known_limitation: only 2 real non-synthetic atoms exist in this repository so far
provenance: narrative/BUILD_REPORT.md
```
