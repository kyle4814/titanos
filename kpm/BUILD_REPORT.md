# KPM-Ω — First Execution Report (§XVII)

Built 2026-08-25, at `/home/tech2/cosmic-library/kpm/` (not `/titanos` — see
`constitution/CONSTITUTION.yaml` header for why). 4 parallel Sonnet agents,
each given a tight, non-overlapping file contract and told to read the
existing `schema/`/`firewall/` code first and replicate its house style
(structured never-bare-bool results, append-only no-delete stores,
absence-of-edge transition tables, fail-closed exception handling,
evidence-gated resolution, minority/dissent preservation) rather than
invent a new one.

## WHAT EXISTS

Before this session: the epistemic firewall (`schema/`, `firewall/`,
`doctrine/`, `legacy/`, `compiler/`) — 110 tests, all passing, documented
in `docs/`. This work builds a second, related but distinct system beside
it: a bounded recursive **production** pipeline for turning source
material into small versioned blueprint atoms, as opposed to the
firewall's job of gating artifacts already in that shape.

## WHAT WAS BUILT (Phases 1–6, 8–11 of the directive's 15-phase order)

| Component | File | Phase |
|---|---|---|
| Repo skeleton | `kpm/` (21 directories per §XV, adapted) | 1 |
| Immutable source registry | `kpm/source-vault/registry.py` | 2 |
| Epistemic type system + classifier | `kpm/schemas/epistemic_types.py` | 4 |
| Blueprint atom schema | `kpm/schemas/blueprint_atom.py` | 3 |
| Blueprint validator | `kpm/validators/validate_blueprint.py` | 5, 6 |
| Promotion state machine | `kpm/promotion/state_machine.py` | 10 |
| Contradiction registry | `kpm/contradictions/registry.py` | 8 |
| Constitution (doctrine) | `kpm/constitution/CONSTITUTION.yaml` | — |

**Not built this session, by design** (§XVI: "do not build everything"):
acceptance-criteria validator as a distinct component (folded into the
blueprint validator's BP-R-8 check instead — judged sufficient for now,
a separate module would be premature), quarantine mechanism specific to
blueprints (the promotion state machine's QUARANTINED state exists but
has no dedicated store the way `firewall/quarantine.py` does — it reuses
`PromotionRecord.history` for now), four/five-agent work-cell *contracts*
as executable code (the roles are defined in `CONSTITUTION.yaml` as
doctrine; nothing enforces them at runtime yet — the four agents that
built this session's code manually followed the "producer isn't the
promoter" rule, but no code checks that a human orchestrating future work
cells does too, beyond the self-promotion check in the state machine),
recursive queue with budgets, simulation harness, release pipeline,
cross-domain library graph (Phases 12–15 — genuinely not started).

## WHAT PASSED

**228 tests, 228 passing, 0 failing**, run independently by suite and
verified again together in this integration pass:

| Suite | Count |
|---|---|
| `kpm/source-vault/tests/` | 16 |
| `kpm/schemas/tests/test_epistemic_types.py` | 40 |
| `kpm/validators/tests/test_validate_blueprint.py` | 29 |
| `kpm/promotion/tests/` | 17 |
| `kpm/contradictions/tests/` | 16 |
| `schema/tests/` (pre-existing, regression-checked) | 67 |
| `firewall/tests/` (pre-existing, regression-checked) | 36 |
| `legacy/tests/` (pre-existing, regression-checked) | 7 |
| **Total** | **228** |

`CONSTITUTION.yaml`'s two machine-checkable claims were cross-verified
against the actual code by direct inspection (not just trusted from the
agents' self-reports): `forbidden_promotion_transitions` matches
`kpm/promotion/state_machine.py::TRANSITIONS` exactly (RAW, DISTILLED,
PROVISIONAL, CONTESTED, QUARANTINED all lack a STABLE edge; only TESTED
and HUMAN_REVIEW have one) — **VERIFIED PROPERTY**.

## WHAT FAILED

Nothing, on the current test suites. That is a claim about test coverage,
not about the absence of bugs — see WHAT IS UNKNOWN.

One naming friction, not a failure: `kpm/source-vault/` uses a hyphen, so
it isn't a valid Python package path (`kpm.source_vault` doesn't import).
The registry's own tests work around this with a direct `sys.path`
insert. Left as-is rather than renamed, because §XV's own skeleton names
it `source-vault` with a hyphen — renaming would be correcting the
directive against itself without being asked to.

## WHAT IS UNKNOWN

- Whether the four components actually compose end-to-end. Each was built
  and tested in isolation by an agent that couldn't see the others' code
  while working. This integration pass ran their test suites together and
  confirmed no import collisions or naming clashes, but **no test yet
  ingests a real source, classifies a claim from it, builds a blueprint
  atom, validates it, and promotes it through the state machine as one
  pipeline** — that's the first genuinely open question, not assumed
  answered.
- Whether `kpm/schemas/epistemic_types.py`'s `reclassify()` mutating in
  place (an agent's judgment call, not something I specified) will cause
  surprising aliasing bugs once claims are held by multiple blueprint
  atoms simultaneously — untested, because no multi-holder scenario exists
  yet to test it against.
- Whether the four/five-agent work-cell separation (Distiller/Architect/
  Adversary/Verifier) needs to become executable code or can remain
  doctrine enforced by process discipline. `CONSTITUTION.yaml` states
  the rule; only the promotion state machine's self-promotion check
  enforces any part of it in code.

## WHAT WAS QUARANTINED

Nothing — no real source material was ingested yet in this session, so
there was nothing for the promotion/contradiction/quarantine machinery to
act on. The machinery exists and is tested against synthetic cases only.

## WHAT REQUIRES HUMAN JURISDICTION

1. Whether to proceed to Phase 7 (acceptance criteria as a standalone
   validator) and Phase 9 (dedicated blueprint quarantine store) before
   or after building the end-to-end pipeline test — order not decided.
2. Whether `reclassify()`'s mutate-in-place design should be revisited
   before any real multi-blueprint usage, given the aliasing question
   above.
3. Whether work-cell role separation should be enforced in code (a
   `WorkCellRegistry` that tracks who-produced/who-verified per blueprint
   and refuses self-certification structurally, matching the promotion
   state machine's `SelfPromotionForbidden` pattern) rather than left as
   doctrine + manual discipline.
4. The standing decisions from the epistemic firewall work are still
   open and unrelated to this build: F-007 (titan repo git history),
   the 3,058-file legacy corpus review question, and four-eyes review
   for quarantine release.

## WHAT THE NEXT SMALLEST WORK CELL SHOULD DO

Ingest ONE real source file through `SourceRegistry.ingest_source()`,
extract ONE claim from it via `classify_claim()`, build ONE
`blueprint_atom` YAML referencing that claim, run it through
`validate_blueprint()`, and promote it through `PromotionStore` from RAW
to at least TESTED — as a single integration test, not new production
code. This is the cheapest way to find out whether the four independently
built, independently green components actually fit together, before
building anything further on top of an unverified assumption that they do.
