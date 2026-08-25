# Sigil Lexicon

A compressed index into proven repository concepts — not a second
source of truth. **The sigil is not the architecture.** Canonical
resolution always runs: `Stable_ID → Glyph → Canonical Meaning →
Source → Proof → Status → Version`. Source precedence: `CODE > TESTS >
PROOF > DOCTRINE > SIGIL`.

Distinct from `SIGIL.md` (`foundation/sigil.py`'s computed capability
tier — `TIER:Tn | IRON:.. | ...`). This file indexes *concepts*; that
one indexes *maturity*.

## Uniqueness law

One Stable_ID → one canonical meaning. One glyph → one canonical
meaning. A meaning change requires a new version/supersession entry,
never a silent mutation. Ambiguity or collision → expand to canonical
text, never guess. Every glyph retains an ASCII Stable_ID fallback —
rendering failure must never make the architecture undecodable.

## Representation law (when is compression earned)

Before any structure becomes a compact form (integer, ordinal, glyph,
bitfield, hash), classify it first — **type determines representation,
representation determines valid operations, valid operations determine
whether compression is earned**:

- **Mutually exclusive states** → named enum (e.g. `taal/gate/
  root_gate.py::VERDICTS`), never a bitmask.
- **Ordered states where comparison is actually needed** → ordinal rank
  via canonical-order position (e.g. `root_gate.py::_PERMISSIVENESS_
  ORDER` + `_cap()` — already the one real instance of this in this
  repo), not a raw magic number.
- **Independent coexisting booleans** → bitfield, only if multiple
  properties genuinely coexist AND a real repeated operation benefits
  AND decode stays deterministic. No instance of this exists in this
  repository today.
- **Multi-dimensional measurement** → tuple/vector, never collapsed
  into one scalar if that destroys causal information (e.g.
  `foundation/sigil.py`'s eight dimensions stay eight fields, not one
  packed integer).

A compression is earned only when a real repeated operation benefits
from it and the original semantics remain deterministically
recoverable — never for elegance alone. (Established 2026-08-25,
`STRUCTURAL_COMPRESSION_GATE_001` — audited against `root_gate.py` and
`sigil.py`, the only two real instances of numeric/ordinal
representation in this repository at time of writing; no bitfield use
case has ever appeared.)

## Seeded entries (already-proven concepts only)

| ID | Glyph | Name | Meaning | Class | Status | Source | Proof | Version |
|---|---|---|---|---|---|---|---|---|
| SIGIL.EXECUTION_ANCESTRY | ⛓ | execution ancestry | protected execution lineage carried across a process boundary | L4 invariant | ACTIVE | `foundation/recursion_guard.py` | `foundation/tests/test_recursion_guard.py` (13 tests) | 1 |
| SIGIL.PROCESS_BOUNDARY | ↳ | process boundary | the point where a child/spawned execution begins | L4 invariant | ACTIVE | `foundation/recursion_guard.py::child_env()` | same as above | 1 |
| SIGIL.RECURSIVE_REENTRY | ⟳ | recursive re-entry | the same protected operation appearing again in active ancestry | L4 invariant | ACTIVE | `foundation/recursion_guard.py::check()` | same as above | 1 |
| SIGIL.BOUNDED_BLOCK | ⊘ | bounded block | prohibited repetition blocked before descendant multiplication | L4 invariant | ACTIVE | `foundation/recursion_guard.py::GuardDecision.BLOCKED_REPEAT/BLOCKED_DEPTH` | same as above | 1 |
| SIGIL.PROVEN | ✓ | proven | evidence-backed property (code + test, not claim) | L5 proof | ACTIVE | (cross-cutting) | this session's targeted/regression runs | 1 |
| SIGIL.LIMITATION | ⚠ | limitation | a known, honestly stated boundary of a proven property | L5 proof | ACTIVE | `TITANOS_RECURSION_GUARD_001.md` §LIMITATION | — | 1 |
| SIGIL.VERIFIED_CHANGE | Δ | verified change | a repository mutation confirmed by targeted + regression proof | L3 capability | ACTIVE | (cross-cutting) | commit `93b3e89` | 1 |
| SIGIL.DURABLE_STATE | ▣ | durable state | committed, reconciled repository state (not chat context) | L1 domain | ACTIVE | `PARETO_FRONTIER.md`, `SIGIL.md`, `NEXT_MOVE.md` | (repo-native, no single test) | 1 |
| SIGIL.MIN_CAUSAL_SEAM | ⌁ | minimum causal seam | the smallest single point requiring inspection to resolve an ambiguity | L2 component | ACTIVE | (methodological, this session's own recurring practice) | — | 1 |
| SIGIL.REF_INTEGRITY | 🔗 | referential integrity | a reference crossing document/record boundaries must resolve at the relevant composition boundary, or the composition is refused | L4 invariant | ACTIVE | proven `rpa/composition/checker.py::check_chain_integrity()`, independently transferred and reproven `narrative/composition/checker.py::check_atom_relations()` | `rpa/composition/tests/test_checker.py` (22 tests), `narrative/composition/tests/test_checker.py` (11 tests) | 1 |
| SIGIL.ABSENT_ILLEGAL_EDGE | ∉ | absent illegal edge | state-machine legality is enforced by an illegal transition never being listed in an explicit table, never by a runtime if-check that filters it out after the fact | L4 invariant | ACTIVE | independently implemented across 6 unrelated state machines, each with its own locally-defined lookup function: `kpm/promotion/state_machine.py::can_transition()`, `foundation/task_queue.py::can_transition()`, `foundation/flow_switch.py::can_transition()`, `firewall/quarantine.py::can_transition()`, `narrative/schema/narrative_atom.py::can_promote()`, `kpm/schemas/epistemic_types.py::can_reclassify()` | `kpm/promotion/tests/test_state_machine.py`, `foundation/tests/test_task_queue.py`, `foundation/tests/test_flow_switch.py`, `firewall/tests/test_quarantine_dissent.py`, `narrative/tests/test_narrative_atom_store.py`, `kpm/schemas/tests/test_epistemic_types.py` | 1 |
| SIGIL.NO_CACHED_DECISION | ⊨ | no cached decision | an authorizing function never accepts a pre-computed decision as its parameter, only raw declared evidence — so a caller cannot construct an "already approved" object and have it honoured; the decision is always re-derived from evidence at the call, proven by a Decision-shaped object raising AttributeError when passed where evidence is expected | L4 invariant | ACTIVE | `foundation/publication_gate.py::authorize_publish()`, independently `foundation/communication_gate.py::authorize_communication()` — no cross-import between the two | `foundation/tests/test_sigil_lexicon_no_cached_decision_specimen.py` (10 tests, includes behavioral proof, not docstring assertion) | 1 |
| SIGIL.NO_DELETE_SURFACE | ⌀ | no-delete surface | a durable store enforces irreversibility structurally, by never exposing a delete/purge/clear/remove method, not by a runtime policy check a caller could bypass | L4 invariant | ACTIVE | independently implemented across 8 unrelated stores: `foundation/task_queue.py::TaskQueue`, `kpm/promotion/state_machine.py::PromotionStore`, `kpm/contradictions/registry.py`, `narrative/store/narrative_atom_store.py::NarrativeAtomStore`, `magl/registry/catalogue.py`, `firewall/quarantine.py`, `foundation/crystal.py::CrystalStore`, `foundation/flow_switch.py::FlowSwitchStore` | `foundation/tests/test_task_queue.py`, `kpm/promotion/tests/test_state_machine.py`, `kpm/contradictions/tests/test_registry.py`, `narrative/tests/test_narrative_atom_store.py`, `magl/registry/tests/test_catalogue.py`, `firewall/tests/test_quarantine_dissent.py`, `foundation/tests/test_crystal.py`, `foundation/tests/test_flow_switch.py` — each asserts `assertFalse(hasattr(store, method))` over `("delete", "purge", "clear", "remove")` | 1 |
| SIGIL.NO_EXECUTION_AUTHORITY | ⛔ | no execution authority | a module that reasons about, observes, or proposes a consequential action is structurally forbidden from executing that action itself — proposal and execution are always two separate functions, only the latter callable by a separate, explicit caller decision | L4 invariant | ACTIVE | independently implemented across 4 unrelated modules, none importing or wrapping another for this property: `foundation/sentinel.py` (`FourPaths` — observes, never executes a finding), `foundation/hells_gate.py` (never outputs the literal string `"TRUSTED"`, no bare `TRUSTED` decision state exists), `foundation/regression_engine.py::check_for_regression()` (proposes a downgrade, never calls `PromotionStore.promote()`), `foundation/defusal_router.py::route_defusal()` (routes a CT_141 response sequence, never marks a step executed) | `foundation/tests/test_sigil_lexicon_no_execution_authority_specimen.py` (7 tests, re-derives the proof against all four real modules directly rather than only citing each module's own existing test file) | 1 |

## Evolution contract (future, not yet implemented)

On a future proven architectural change: extract the changed concept →
compare against existing Stable_IDs → if it matches an existing entry,
update its refs/proof/version; if it's genuinely new and proven, add an
entry; if unproven, do not promote it; if it supersedes an existing
entry, retain the old entry marked `SUPERSEDED` with an alias, never
delete; if ambiguous, escalate rather than guess. **This is a
reconciliation contract for a human/model to follow by hand** — no
automated scanning code exists yet. Claiming otherwise would be exactly
the "no glyph exceeds its evidence" violation this file exists to
prevent.

## Architecture levels (reference)

L0 SYSTEM · L1 DOMAIN · L2 COMPONENT · L3 CAPABILITY · L4 INVARIANT · L5 PROOF
