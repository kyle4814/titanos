# TITANOS // GREENLIGHT & MEMETIC PROPAGATION DOCTRINE

Added 2026-08-25 per Kyle's explicit instruction. Loaded at session start
via this project's `CLAUDE.md` — stateless config, not session memory.
Tenth doctrine file — **compressed from four directives pasted in the
same session** (Semantic Crystalization Protocol, Greenlight Execution
Architecture / "Tuning Fork" + Constitutional Pivot "Clear River", Viral
Precision Propagation Doctrine, Core Payload Agency & Memetic Propagation
Doctrine v2.0.0). Per those directives' own Code Production Doctrine
("before creating code, search the corpus... do not duplicate because
duplication creates competing realities") and this session's Compression
principle: four directives that were ~90% restatement of the nine prior
doctrine files (same CT_141, same Hell's Gate, same Four-Agent shape,
same "never leave on problems", same reality-yield discipline) do not
each get a separate file. Only what was genuinely new is recorded below,
with a pointer to the existing implementation it extends rather than
replaces.

## WHAT WAS ALREADY FULLY COVERED (not restated as new doctrine)

CT_141, Hell's Gate, Black Ice reflection, Four-Agent Alpha/Beta/Gamma/
Delta, reality-yield accounting, "never leave on a problem", capability-
only language, one-degree-of-separation public/private boundary, `/boot`
and `/go` — all already governed by the first nine doctrine files and
implemented in `foundation/`. The "malware propagation is explicitly
forbidden, adoption must be voluntary and transparent" framing in the
Viral Precision and Core Payload directives is a restatement of
`TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md`'s existing public/
private boundary rule, not a new constraint — this repo has never had,
and does not now have, any self-installing or self-replicating code path.

## WHAT WAS GENUINELY NEW

### 1. The Greenlight state model (RED / AMBER / QUARANTINE / GREEN)

A four-state relabeling of the same admission concept
`foundation/hells_gate.py` already implements as REJECT / HUMAN_REVIEW_
REQUIRED / QUARANTINE / ADMIT. Audited field-by-field: the Greenlight
Contract's ten checklist items (intent explicit, scope bounded,
permissions present, safety constraints satisfied, no prohibited
objective, expected output defined, stop condition exists, rollback path
exists, cost within budget, success externally evaluable) map onto Hell's
Gate's existing ten gates with no gap on either side. **Not rebuilt** —
a second state-machine with the same four outcomes under different names
would be exactly the "competing realities" duplication these directives
themselves warn against.

### 2. The Reality Sensor's five-way epistemic split (Payload_03)

OBSERVED / REPORTED / INFERRED / HYPOTHESIZED / UNKNOWN, with "no agent
may upgrade a category without evidence." This is finer-grained than
`kpm/schemas/epistemic_types.py`'s 15-value `ALL_CLASSIFICATIONS` in one
specific way (it separates "directly observed" from "reported by another
party" — the existing vocabulary does not distinguish those two source
positions) but coarser in every other way. **Not built as a parallel
vocabulary** — flagged in `PARETO_FRONTIER.md` as a possible future
refinement to `epistemic_types.py` itself (add a `source_position` axis
orthogonal to the existing classification, not a new enum), not built
this cycle because no real workload has yet needed the distinction the
existing 15 values don't already make.

### 3. The Seed/Manifest packaging fields (Payload_10/11, §XII of Viral
   Precision doctrine)

For an artifact to "carry its own identity, context, boundaries, tests,
method of reproduction, method of removal" when published: thesis,
quickstart, examples, failure cases, threat model, limitations,
changelog, fork guide, integration interfaces, machine-readable manifest,
provenance record, contribution path. **Genuinely absent** from this
repository — `README.md` covers the whole repo, but no per-subsystem
packaging exists (each of `schema/`, `firewall/`, `kpm/`, `magl/`,
`rpa/`, `taal/`, `foundation/`, `narrative/` has a `BUILD_REPORT.md`,
close but framed as an internal audit trail, not an external "here is
how to adopt/fork/remove this" document). **Not built this cycle** —
blocked on the same fact `TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md`'s
opening note already established: there is no GitHub remote, so there is
nowhere for a fork guide or contribution path to point. Building the
full 12-field packaging template now would be the "empty theater" every
one of these directives independently warns against. Recorded as
`PARETO_FRONTIER.md` FRONTIER-008, blocked on the same GitHub-remote
decision as FRONTIER-003.

### 4. Crystalline Memory (Payload_09) — **built this cycle**

The one genuinely missing, genuinely buildable link in the doctrine's own
stated chain: `REALITY -> LEVER -> ACTION -> TEST -> YIELD -> MEMORY ->
PACKAGE -> ADOPTION -> FEEDBACK`. REALITY/LEVER/ACTION/TEST/YIELD all
already have real implementations (`foundation/reality_yield_ledger.py`
and the GO-cycle machinery); PACKAGE is blocked (see #3 above); ADOPTION
and FEEDBACK are blocked (no external ping surface, same standing
finding as `TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md`'s opening
note). MEMORY was the first unblocked, genuinely unbuilt link: every
cycle's conclusion has lived only in `BUILD_REPORT.md` prose, never as a
structured, queryable record forcing "what would have disproven this" to
be answered explicitly.

Built `foundation/crystal.py` — `Crystal` (problem/context/hypothesis/
action/evidence/result/failure_mode/limitation/provenance/
reusable_abstraction/regression_test_ref/epistemic_status, the last
field reusing `kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS` rather
than a parallel vocabulary) + `CrystalStore` (append-only, no delete
surface, `supersedes` for reassessment — same pattern as
`RealityYieldLedger`/`QuarantineStore`/`PromotionStore`). Deliberately
**not** a duplicate of `RealityYieldLedger`: that module answers "was
this worth it" in cost/benefit terms; `Crystal` answers "what was
believed, on what evidence, and what would change that belief" —
epistemic provenance, not cost accounting. A crystal's `evidence`/
`result` fields may cite a `LedgerEntry.entry_id` but this module does
not compute yield. 19 tests, all passing.

## /BOOT AND /GO — NOT RE-SPECIFIED

Both `/boot` and `/go` already exist as real slash commands
(`.claude/commands/boot.md`, `.claude/commands/go.md`) matching the
"load state, identify highest lever, do not execute yet" / "one bounded
cycle, then stop" contract these four directives independently re-ask
for in nearly identical words. Not modified this cycle — no gap found
between what they already do and what these directives request.

## FINAL NOTE ON DIRECTIVE VOLUME

Four large constitutional-style directives arrived in rapid succession
mid-cycle, three of them stacking on top of each other before the first
was finished being processed. Per this session's own Anti-Overthinking
Lock ("does this analysis change the next action? If no, do not generate
it") and CT_141 (panic = information velocity exceeding verification
velocity): the correct response to directive-volume pressure is not to
generate four separate multi-thousand-word doctrine files matching the
input volume — it is to compress to what actually changed the next
action, which was: build `foundation/crystal.py`. Everything else in
this file exists so the audit trail is honest about what was read and
declined, not to pad the corpus.