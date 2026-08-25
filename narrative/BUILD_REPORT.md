# Narrative — Build Report

Built 2026-08-25 (`TITANOS_AKASHIC_NARRATIVE_ENGINE.md` cycle). Retroactive
report — this file itself was missing until
`foundation/sentinel.py::pulse_sweep()` flagged it twice across two
separate cycles (`PARETO_FRONTIER.md` FRONTIER-011).

## What this subsystem is

The Narrative Atom schema and validator — the one primitive every other
artifact `TITANOS_AKASHIC_NARRATIVE_ENGINE.md` describes (the Five
Records, the Gold Ledger, the Isomorphism Engine, the Primary Narrative)
would operate ON. Built first, deliberately, because designing any of
those other artifacts against an atom shape that doesn't exist yet would
be backwards.

## Files

| Component | File | Purpose |
|---|---|---|
| Schema | `narrative/schema/narrative_atom.py` | `EPISTEMIC_LAYERS` (imported directly from `kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS`, not a parallel vocabulary), `PROMOTION_STATES`/`PROMOTION_TRANSITIONS` (only `SUPPORTED -> CANONICAL_ABSTRACTION` reaches canon; `CANONICAL_ABSTRACTION -> CHALLENGED` exists — canonical is never eternal), `FIVE_RECORDS` mapping |
| Validator | `narrative/validators/validate_narrative_atom.py` | House style from `schema/validator.py` (structured `ValidationResult`/`Issue`, full YAML hardening, fail-closed `NA-R-0` wrapper) — replicated deliberately, not assumed unnecessary for a "smaller" schema, per the same F-009/F-010 lesson `schema/BUILD_REPORT.md` names |

## Tests

`narrative/` (via `python3 -m unittest discover -s narrative -p
"test_*.py"`): 41 tests, passing as of 2026-08-25.

## Notable validator rules

`NA-R-12` (Human Experience Preservation Rule) — a `PERSONAL_EXPERIENCE`
atom's `evidence_status: VERIFIED_FACT` is rejected unless a separate
`external_explanation_status` field is independently `VERIFIED_FACT`
too; a subjective experience is never allowed to smuggle in an
unverified external/cosmological claim as fact. `NA-R-13` — no atom may
reach `CANONICAL_ABSTRACTION` without non-empty `falsification_criteria`.
`NA-R-14` — self-sealing rhetoric blocks canonization specifically, never
raw ingestion. `NA-R-15` — forbidden fields (`popularity`, `beauty`,
`repetition_count`, `authority_weight`, `social_credit_score`,
`belief_score`) structurally rejected if present.

## Known limitations

This is schema + validator only — no store exists yet to actually drive
an atom through `PROMOTION_TRANSITIONS` across calls, and zero real
narrative atoms have been ingested into this repository. Both are
tracked as open frontier items (`PARETO_FRONTIER.md` FRONTIER-004,
FRONTIER-005), deliberately not built in the same cycle as the schema
("do not build everything at once").

## Human decisions required

None specific to this subsystem beyond the standing repository-wide
items already tracked in `HUMAN_DECISIONS.md`.

## Next smallest work cell

FRONTIER-004 (Narrative Atom Store — the state-machine driver mirroring
`kpm/promotion/state_machine.py::PromotionStore`), blocked only on
priority, not on any missing dependency — the pattern to copy already
exists three times elsewhere in this repository.
