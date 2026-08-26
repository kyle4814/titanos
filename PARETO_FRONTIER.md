# Pareto Frontier — Capability Map

Not a backlog. Per `TITANOS_ADDENDUM_FRONTIER_AS_CAPABILITY_MAP.md`
(loaded via `CLAUDE.md`), this file is the navigation surface between
what this repository can demonstrably do (code + tests) and what it can
next become (the smallest credible delta). `/boot` loads it. Distinct
from `HUMAN_DECISIONS.md` (judgment calls only a human can resolve) and
from `INTUITION.md` (low-commitment discovery — nothing there is
authorized work until it passes the Frontier Gate below and moves here).

**Staleness is a real risk, named not hidden.** An entry not touched in
a long time should be re-verified against real repository state before
being trusted, not assumed still accurate.

---

## Frontier Gate

No candidate enters "Active" without answering all seven. If it can't
answer these yet, it stays in `INTUITION.md`, not here.

1. **CURRENT** — what the repository can demonstrably do right now.
2. **GAP** — the specific missing capability.
3. **LEVER** — why closing this gap is disproportionately valuable.
4. **FIRST STEP** — the smallest implementation or proof.
5. **PROOF** — how the new capability becomes verified.
6. **UNLOCK** — what becomes reachable afterward.
7. **REUSE** — what existing work this builds on rather than duplicates.

## Active

### FRONTIER-009 — Boot Context Selector for `CLAUDE.md` doctrine imports
- **CURRENT:** `MEMORY_MAP.md` (built) measured 1,700+ lines across
  doctrine files loading unconditionally at every session boot — now
  16 `@`-imports (grown from 12 at measurement time), count re-verified
  2026-08-25 via `FRONTIER_009_RECON_001`. Tier-3 content paying Tier-0 cost.
- **GAP:** no mechanism loads only the doctrine relevant to the active
  task.
- **CAUSAL GAP RE-EXAMINED (`FRONTIER_009_RECON_001`):** no session has
  ever failed to reliably do anything *because* of this — the current
  system correctly loads all doctrine, every time. The cost is verbosity,
  not a correctness failure. The chain "without X, the system cannot
  reliably do Y, because Z" cannot honestly be written: X's absence
  produces no observed Y failure. This entry's own `effort`/`risk`
  fields already concluded the fix trades a loud cost (verbose boot) for
  a silent one (a session missing doctrine it needed) — net negative.
  **Verdict: D — UNNECESSARY. Stays OPEN, not built, not reordered.**
- **LEVER:** reduces boot context size with no functional change.
- **FIRST STEP:** genuinely uncertain — see below.
- **PROOF:** would need a regression test proving a session can still
  discover a doctrine file it needs despite not auto-loading it.
- **UNLOCK:** cheaper, faster session boots as the doctrine stack grows
  further.
- **REUSE:** `MEMORY_MAP.md`'s tier classification.
- **effort:** MEDIUM-HIGH — no native lazy-`@`-import capability exists
  in Claude Code; the only implementation path is removing `@`-imports
  entirely and replacing them with plain-text pointers a session reads
  selectively, which trades automatic loading for manual discipline and
  risks a session silently missing doctrine it needed (a silent failure
  mode, worse than a loud one). **risk:** LOW-MEDIUM for this reason —
  not yet clearly a net win, which is why this remains OPEN rather than
  promoted to "smallest first move now."

## Archive addition — FRONTIER-008 COMPLETE

All 8 subsystems now have a verified `ADOPT.md` (`firewall/`, `schema/`,
`kpm/`, `magl/`, `rpa/`, `taal/`, `foundation/`, `narrative/`,
2026-08-25/26) — every quickstart's *code*, not just its test command,
independently re-run and matched against real output. Verification was
load-bearing, not ceremonial: caught and fixed three real inaccuracies
before they shipped (`kpm/ADOPT.md`: `reclassify()`'s true positional
signature + `PromotionStore` has no RAW→TESTED shortcut edge;
`taal/ADOPT.md`: a wrong claimed verdict, missing `supporting_evidence`).
Depth was scoped proportionately, not uniformly — `rpa/`, `taal/`,
`foundation/` (largest, 17 modules) each gave full quickstart depth only
to their security-critical or highest-value pieces, indexing the rest by
pointer, matching the Blueprint Production Law's "smaller than the
original domain" test. Moved to Archive table below.

## Blocked

### FRONTIER-005 — Five-Record query views, Gold Ledger, Isomorphism contract
- **CURRENT:** FRONTIER-004 (`NarrativeAtomStore`) is now built. Two
  real narrative atoms exist (`NA-INGEST-001`/`NA-INGEST-002`,
  `narrative/tests/test_real_ingestion_recursion_guard.py`, commit
  `5c73498`) — real, not synthetic, but thin.
- **GAP:** views/ledger/contract over content that barely exists yet.
- **blocked_by:** partially resolved — FRONTIER-004 dependency is
  satisfied; the "real ingestion source" dependency is technically
  non-zero but not yet substantial enough to build query views/a Gold
  Ledger against without the result being speculative. Not force-
  unblocked; stays Blocked until more real content exists.
- Items (B)/(C)/(F) of `TITANOS_AKASHIC_NARRATIVE_ENGINE.md` §XVIII,
  deliberately deferred — "do not build everything at once."

## Archive (built)

One line each — full reasoning lives in the commit that built it. Kept
here, not deleted, per this file's own Archivist principle; removed
from the active scan path per this addendum's compaction rule.

| ID | Capability | Commit |
|---|---|---|
| FRONTIER-RG | Bounded recursive execution ancestry (recursion guard) | `93b3e89` |
| FRONTIER-004 | Narrative Atom Store (`narrative/store/narrative_atom_store.py`) | `d5537c1` |
| FRONTIER-MEMBRANE | Source Vault -> Narrative Atom bridge (`narrative/intake/source_vault_bridge.py`) | `4ac4ef6` |
| FRONTIER-000 | Narrative Atom schema + validator | `d14e128` |
| FRONTIER-006 | Layer 0 Worker Contract (ABC-enforced) | `f416cd0` |
| FRONTIER-007 | Crystalline Memory (`foundation/crystal.py`) | `7ecf615` |
| FRONTIER-MAP | Memory Map / boot-load tier audit | `f5c2f34` |
| FRONTIER-010 | Sentinel_141 Level 1 Pulse Sweep | `b25b680` |
| FRONTIER-012 | Bounded Task Queue Workflow | `f5de342` |
| FRONTIER-013 | Queue ↔ Layer0Worker execution seam | `0b1efba` |
| FRONTIER-014 | Closed-loop reality proof (real worker) | `190b119` |
| FRONTIER-015 | Explicit run deferral + recovery handoff | `44c9b18` |
| FRONTIER-011 | `BUILD_REPORT.md` for schema/firewall/narrative | `e816905` |
| FRONTIER-001 | Reusable secret/credential scanner | `1b03480` |
| FRONTIER-002 | `permission_request` → `GateInput` adapter | `632e774` |
| SIGIL | Capability Sigil (`foundation/sigil.py`, `SIGIL.md`) | `e3ce475` |
| FRONTIER-FSCHEMA | `PARETO_FRONTIER.md` structural schema validator (`foundation/sentinel.py::check_frontier_schema`) | `cbcb73f` |
| FRONTIER-REFCHECK | RPA cross-file referential integrity checker (`rpa/composition/checker.py`) | `9a63205`, extended `d8afa32`, `3741094`, `b5cad9a` |
| FRONTIER-CONCLUDE | Coded Conclusion Gate (`foundation/conclusion_gate.py`) | `c53411f` |
| FRONTIER-CONCLUDE-ENFORCE | Conclusion Gate enforced at `Layer0Worker.run()` (mandatory, not optional) | `8c91b81` |
| FRONTIER-MANIFEST | Runtime dependency manifest (`requirements.txt`, PyYAML pinned) | `b2ce4b1` |
| FRONTIER-COMM-SWITCH | External Communication switch, prerequisite only (`foundation/communication_gate.py`) — no retrieval capability implemented | `ff7af45` |
| FRONTIER-NARRATIVE-REFCHECK | Narrative atom cross-atom referential integrity checker (`narrative/composition/checker.py`) | `67c3507` |
| FRONTIER-INVARIANT-SPECIMEN | First proven invariant durably registered in `SIGIL_LEXICON.md` (`SIGIL.REF_INTEGRITY`, transferred rpa->narrative) | `5fd5dc7` |
| FRONTIER-NO-DELETE-INVARIANT | Second registered invariant (`SIGIL.NO_DELETE_SURFACE`), proven across 8 independent stores, stronger than the control specimen | `e560129` |
| FRONTIER-ABSENT-EDGE-INVARIANT | Third registered invariant (`SIGIL.ABSENT_ILLEGAL_EDGE`), proven across 6 independent state machines, independence verified by import-check test | `e8e1cf2` |
| FRONTIER-NO-CACHED-DECISION | Fourth registered invariant (`SIGIL.NO_CACHED_DECISION`), correctly scoped to 2 domains after recon disproved a false 3-domain claim; also fixed an audit gap in an existing test | `95906bb` |
| FRONTIER-NO-EXECUTION-AUTHORITY | Fifth registered invariant (`SIGIL.NO_EXECUTION_AUTHORITY`): 4 independent modules (`sentinel.py`, `hells_gate.py`, `regression_engine.py`, `defusal_router.py`) share "proposes/observes, structurally forbidden from executing" -- proof re-derived directly against all 4 real modules in one test file, not just citing each module's own existing test | `82f08ea` |
| FRONTIER-RPA-VALIDATION-BINDING | Multi-turn adversarial recon (semantic equivalence-fraud hunt) found and closed a real gap: `rpa/gates/human_jurisdiction.py::authorize_pilot()` could queue any `candidate_id` for pilot review with zero connection to real, structurally validated content. Closed via 2 new `SourceRegistry` accessors (`get_by_hash`, `get_content`) + fresh recomputed validation at authorization time (never a durable "was validated" witness -- the validator is pure, so recomputation is strictly stronger). Same recon separately proved `foundation/switch_hardener.py` does NOT share this bug (no consequential consumer exists there) -- a genuine negative control, not assumed symmetry. Found and fixed one real regression during implementation: a `sys.path` insert of the hyphenated `kpm/source-vault/` dir collided with unittest's "tests" package resolution across subsystems; fixed via `importlib` file-based loading instead. 1308/1308 full regression. | (this commit) |
| FRONTIER-EPISTEMIC-FREEZE | Closed a real, reproduced epistemic-state collapse: froze 5 append-only record types (Claim, AtomRecord, PromotionRecord, QuarantineRecord, FlowSwitchRecord) that were bypassable via direct attribute assignment | `3dcb258` |
| FRONTIER-HISTORY-FREEZE | Closed a real, LIVE exploit: the same 5 types' `history` field was still a mutable list under freezing -- converted to tuple, closing a forged-entry bypass of `rpa/gates/human_jurisdiction.py`'s pilot-authorization gate | `8e0e12d` |
| FRONTIER-003 | CI workflow real and green (`kyle4814/titanos` created public, pushed, `.github/workflows/tests.yml` fired for the first time and passed, 8/8 subsystems) | `6fb29fa` (workflow) + live push 2026-08-25 |
| FIRST-PING | First proven `WORLD -> TITANOS -> WORLD` exchange: real GitHub Actions run ingested + classified through the existing (pre-built) digestion pipeline, self-sourced not human-supplied. See `FIRST_PING.md`. No new code. | (this commit) |
| FRONTIER-008 | Per-subsystem external packaging docs (`ADOPT.md`) for all 8 subsystems -- every quickstart independently re-run and matched, caught 3 real doc bugs before shipping | `82862e4`,`8b9d906`,`2b1fb4c`,`8c299e0`,`cb8bd84`,`3c5c87c`,`e8afcae`,`1b7793c` |
| FRONTIER-SIGIL-T7 | T7 rung implemented (`foundation/sigil.py::_dimension_external_integration()`) -- a documented-but-never-built ceiling, closed once real evidence (public repo + recorded CI success) actually existed to check against. Local-evidence-only by design, no live network call. 7 new tests, 32/32 targeted, 1212/1212 full regression. | `23373c3` |
| FRONTIER-4AGENT-FOUNDATION | 4 parallel agents built the 4 remaining feasible `foundation/MAPPING.md` items (`defusal_router.py`, `low_regret_engine.py`, `regression_engine.py`, `state_space_mapper.py`); independent adversarial review agent found and this session fixed: `ContradictionRecord` (kpm/contradictions/registry.py) was the ONE record type `EPISTEMIC_INTEGRITY_002`'s sweep missed -- same live forgeable-status/history exploit, now frozen+tupled like the other 5. Also fixed: `low_regret_engine.py` duplicate-name ambiguity + float-equality tie-detection trap, `MAPPING.md` test-count arithmetic. 1294/1294 full regression. | `522a6eb`,`6ee1a32` |
| FRONTIER-KPM-E2E | `kpm/BUILD_REPORT.md`'s own named-but-never-built next step: `kpm/tests/test_end_to_end.py` proves ingest->classify->blueprint->validate->promote genuinely connects, matching the proof `magl/rpa/taal` each already had for their own subsystem. Also found and fixed: `kpm/tests/` had no `__init__.py`, so `unittest discover` was silently never running anything placed there. Also found and fixed: `rpa/BUILD_REPORT.md` and `narrative/BUILD_REPORT.md`'s own "next smallest work cell" sections were stale, describing already-completed work (`rpa/composition/checker.py`, `narrative/store/narrative_atom_store.py`) as still pending. 1295/1295 full regression. | (this commit) |
| FRONTIER-SITUATION-ANALYSIS-SLICE | 5-parallel-agent recon (cartographer/data-model/Monk-Demonblade/MAGL-bridge/red-team) then one narrow vertical slice built: `foundation/situation_analysis.py` (`monk_pass`/`demonblade_pass` pure functions, `build_magl_candidate`, `record_situation_crystal`) proves a full cycle — situation -> structure -> adversarial attack -> SURVIVED/KILLED -> MAGL candidate -> real `register_checked()`/`authorize_pilot()`/`confirm_pilot_authorized()` gates -> one durable `Crystal` a future reader can retrieve with zero conversation history. Reused every existing primitive unchanged (Crystal, ContradictionRegistry vocabulary, PromotionStore, SourceRegistry, MAGL catalogue/composition, RPA gate) — no new store, no new gate, no Monk.py/Demonblade.py class. Real finding from the recon: MAGL's `catalogue.py`/`validate_magl.py` stack and `ContradictionRegistry.record()` had **zero real non-test callers anywhere in the repo** before this slice — this is their first real caller. `build_magl_candidate()` structurally refuses a non-SURVIVED analysis (`AnalysisNotSurvived`); a negative test proves a composition conflict is still refused even for a SURVIVED candidate. 18 new tests, 1326/1326 full regression. | (this commit) |
| FRONTIER-WORLD-PING-SLICE | Second 5-parallel-agent recon (external-system cartographer/bottleneck engineer/red-team/corpus architect/integration engineer) extended the situation-analysis slice OUTWARD to a real external system (Acme Manufacturing's invoicing bottleneck, `rpa/fixtures/legacy_map.yaml`+`bottleneck.yaml`+`automation_candidate.yaml` — no synthetic fixture invented). Cartographer found `SituationAnalysis` needed **zero new fields** for external subjects. Added exactly two things: `find_bottleneck_hypotheses()` in `foundation/situation_analysis.py` (a `Claim`-based, never-a-bare-float bottleneck contract returning INSUFFICIENT_EVIDENCE/HOLD/SINGLE_CANDIDATE/AMBIGUOUS_MULTIPLE — never forces a fake single winner) and `CrystalStore.is_current()` in `foundation/crystal.py` (closed a real red-team finding: `supersedes` was validated on write but never consulted on read — zero real callers ever checked staleness). Full world-ping chain proven end-to-end on the real fixture through unmodified MAGL/RPA/Crystal gates. 33 new tests (52 total across the situation-analysis test files), 1341/1341 full regression. | (this commit) |
| FRONTIER-TECTONIC-TENSION-SLICE | Third 5-parallel-agent recon (tectonic cartographer/power-topology engineer/off-ramp engineer/red-team/integration engineer) extended the world-ping slice to STRUCTURAL TENSION between two actors — deliberately distinct from a single-actor bottleneck. Added `find_tension_hypotheses()` (two-sided, `Claim`-backed, states INSUFFICIENT_EVIDENCE/NO_TENSION_IDENTIFIED/STRUCTURAL_TENSION/CONTINGENT_TENSION/AMBIGUOUS_MULTIPLE — `STRUCTURAL_TENSION` explicitly never means "inevitable"; `ACTIVE_CLASH` was deliberately NOT implemented since distinguishing "already manifested" from "merely unresolved" would require causal/temporal understanding the keyword-overlap heuristic honestly can't provide) and `evaluate_off_ramp_candidates()` (vets caller-proposed stabilisation options against real evidence — never generates one, avoiding the "recommendation engine" trap; `NO_CREDIBLE_OFF_RAMP_IDENTIFIED`/`PRECONDITIONS_UNMET` are first-class honest outputs; `affected_relationships` mandatory-non-empty and `interim_cost_if_reversible` required-unless-irreversible close the "local stability ≠ global stability" and "reversible ≠ free" traps). Real fixture: the same Acme corpus's own `jurisdictions` block (clerk's informal $5000 approval authority vs. the formally-authority-less approval workflow) — a genuine two-sided tension already latent in existing evidence, not invented. Red team's sharpest finding (K15, dead-capability risk) was resolved by wiring the new layer into the SAME real end-to-end gate chain as the existing test, not a standalone unit test alone. 24 new tests, 1362/1362 full regression. | (this commit) |
| FRONTIER-CONTRADICTION-REGISTRY-WRITER | Fourth 5-parallel-agent recon: `ContradictionRegistry.record()` still had zero real non-test callers after three prior slices. Three independent agents (cartographer/semantics engineer/red team) converged on the same finding: `demonblade_pass()`'s `contradiction_candidates` are single-sided "unsupported dependency" findings, NOT the two-claims-that-cannot-both-be-true collision `ContradictionRegistry`'s own docstring defines — wiring them in directly would be semantic laundering, rejected as a build blocker (K3/K7). The corpus-loop engineer identified the one real subject that DOES fit: this session's own already-fixed RPA validation-transfer finding (real commit, real regression test `test_arbitrary_magl_id_with_no_validated_source_is_refused`). Built `foundation/historical_findings.py::record_rpa_validation_bypass_finding()` — one explicit, one-time, caller-invoked function recording+resolving this real historical contradiction with real evidence_refs (file paths, test name, ADOPT.md), never touching `demonblade_pass()` or `PromotionStore` directly. Proven to reach `regression_engine.check_for_regression()` as a real reader (proposes `STABLE→DEPRECATED`, never auto-executes — blueprint state confirmed unchanged after the call). Classified honestly as WRITER_TO_READER_ONLY, not a closed loop — no real external trigger outside test code exists yet. 7 new tests, 1369/1369 full regression. | `dd9a7fd` |
| FRONTIER-GIT-DURABILITY-AND-FIRST-SEED | Fifth 5-agent cycle closed the actual durability gap: all four prior cycles above were uncommitted in the working tree (their `(this commit)` tags were false). Git cartographer confirmed a clean 14-file commit set with zero unrelated changes; Osiris auditor confirmed full fresh-clone reconstructability (all 9 test questions resolved IMPLEMENTED, reasoning for every "why not X" decision — e.g. why `demonblade_pass()`'s candidates aren't wired to `ContradictionRegistry` — lives in code docstrings, not just this conversation); red team found no commit blockers. Committed as `dd9a7fd`. Then ran ONE real internal subject (the MAGL-Ω duplication-avoidance decision — `magl/BUILD_REPORT.md`'s real finding that 9/11 required invariants already existed, verified `ACCEPTED` by `compiler/coverage.py`) through the unmodified pipeline in a scratch script: `find_bottleneck_hypotheses` → `SINGLE_CANDIDATE`; `find_tension_hypotheses` → honestly `NO_TENSION_IDENTIFIED` (the `_mentions()` heuristic found no actor-name overlap in the evidence text — refused to manufacture a tension rather than force one); `demonblade_pass` → `SURVIVED`. **Correction (same cycle, caught by a second 5-agent pass before this row was committed):** the scratch script called `record_situation_crystal()` against a `CrystalStore()` instantiated in that same process — `CrystalStore` is pure in-memory with no disk backend, so that Crystal was never durable and no longer exists; the original wording here claimed it as "recorded," which overclaimed. No `Crystal` for this seed currently exists anywhere in the repository. The pipeline run itself (bottleneck/tension/demonblade results above) is real and reproducible from `magl/BUILD_REPORT.md`'s real content; only the "recorded to Crystal" step was never actually durable. Deliberately stopped before `build_magl_candidate`/MAGL/authorization either way — a historical governance decision has nothing for those gates to validate. Zero new architecture required for the pipeline itself. | (this commit) |

## Rejected / not on the frontier

- **Full `core/`/`workers/`/`ledgers/` directory restructure** — would
  duplicate existing structure (`foundation/`/`magl/`/`rpa/`/`taal/`
  already are the shapes proposed) or be empty theater (typed worker
  directories with no code). Rejected as the *next move*, not as a
  future possibility — if a genuine need for typed worker processes
  emerges, build that need directly, don't pre-build scaffolding.

- **"Universal decision layer" / input-topology router, and Crystal
  cross-subject similarity retrieval** — 5-agent recon (cartographer/
  ontology-minimalist/corpus-reuse/red-team/integration engineer),
  2026-08-26, both candidates NO-BUILD against the same 10-point
  checklist `FRONTIER-SITUATION-ANALYSIS-SLICE` and its two extensions
  already used to justify prior cycles. Router fails decisively:
  `test_situation_analysis_external_system.py` already calls
  `find_bottleneck_hypotheses()`/`find_tension_hypotheses()` directly on
  the same `SituationAnalysis`, back to back — "doing nothing plus
  better composition" already dominates a dispatcher. No real
  unstructured-input fixture exists (every fixture is already-structured
  YAML), and it would be a fourth function whose only real caller is its
  own test. Crystal retrieval fails independently and more sharply: no
  mechanism anywhere judges relevance between two different Crystals
  (confirmed zero non-test readers of `.get()`/`.all_crystals()`/
  `.reusable_abstractions()` beyond this session's own test fixtures),
  and stretching `_mentions()`'s same-document keyword-overlap heuristic
  across unrelated historical subjects would silently launder a weak
  same-session heuristic into a cross-document applicability claim it
  was never evidenced for — "a previous solution worked there, therefore
  it works here." The separately-attacked 9-category problem taxonomy
  (bottleneck/tension/contradiction/coordination/resource-constraint/
  information-deficit/risk-reversibility/dependency/opportunity-frontier)
  was killed outright: only 2 of 9 categories have any real analysis
  function behind them. Nothing built. If either candidate is revisited,
  it needs a real non-test caller and a real unstructured-input fixture
  first — not built speculatively ahead of either.

## How to use this file

1. Check here before proposing new work — an entry may already exist
   with its trade-offs worked out.
2. A candidate must pass the Frontier Gate (all 7 questions answered)
   before it's added under Active.
3. When built, move the entry's one-line summary to the Archive table
   and note the commit — don't leave stale full-prose entries active.
4. Re-verify a long-untouched entry against real repository state
   before trusting it.
