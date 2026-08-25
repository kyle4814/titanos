# Pareto Frontier Registry

Persistent, git-tracked candidate-move registry per
`TITANOS_PARETO_FRONTIER_RECURSION_ENGINE.md` §XII. This is the "living"
half of the architecture's decision state — before this file existed, a
LEVER phase's Option A/B/C analysis lived only in a chat transcript and
had to be re-derived from scratch (or from memory) by the next session.
`/boot` now loads this file as one of its ten steps.

**Not the same thing as `HUMAN_DECISIONS.md`.** That file holds judgment
calls only a human can resolve (policy, legal, personal choices — "should
X be true"). This file holds ranked engineering candidate moves ("what
should get built next") — some entries here exist *because* an item in
`HUMAN_DECISIONS.md` unblocks them once resolved; each entry says so
where relevant.

**Staleness is a real risk with this kind of file — named, not hidden.**
A frontier registry nobody updates becomes exactly the kind of stale
assumption `TITANOS_PARETO_FRONTIER_RECURSION_ENGINE.md`'s Boot Zero
step is supposed to catch. Convention: every entry carries `added`
(date) and `status`; an entry not touched in a long time should be
re-verified, not trusted, the next time it's picked up.

---

## Built

### FRONTIER-013 — Queue <-> Layer0Worker execution seam (`foundation/queue_worker_adapter.py`)
- **status:** BUILT — `make_worker_perform`/`make_worker_verify`, 10 seam
  tests (T1-T10 matrix) + 1 regression test, both existing modules
  (`task_queue.py`, `layer0_worker.py`) unmodified except one real bug
  fix (below).
- Explicit adapter, not a redesign: `task_queue.run()`'s `perform:
  Callable[[Task], str]` / `verify: Callable[[Task, str], bool]`
  contract is genuinely incompatible with `Layer0Worker.run()`'s
  zero-arg/`CycleRecord`-return shape — bridged via a `dict[str,
  CycleRecord]` the two returned closures share, not by changing either
  contract. Success is detected via `"UPDATE_STATE" in record.
  steps_completed` (the one step only reached after execute+verify both
  succeed), not `record.halted` (which is also `True` on a *successful*
  cycle that recommends stopping future recursion — checking it alone
  would misclassify that as failure).
- **real bug found and fixed by writing the seam tests:**
  `TaskQueue.eligible_tasks()` silently skipped dependencies on unknown
  task_ids (`if d in self._tasks` filtered them out of the `all(...)`
  check instead of failing it), making a task with only unrecognised
  dependencies vacuously eligible — fail-open instead of fail-closed.
  Fixed; regression test added to `test_task_queue.py`. Discovered via
  T8 ("ineligible task never reaches worker execution"), not introduced
  by this cycle.
- **reality pass:** `foundation/sentinel.py::pulse_sweep()` run against
  the actual current repo post-change — 3 findings, identical to the
  pre-existing FRONTIER-011 finding (missing `BUILD_REPORT.md` for
  three subsystems), zero new findings, not compacted.
- The arbitrary-callable path (no worker involved) is preserved and
  still tested unchanged (T7) — `Layer0Worker` integration is an
  explicit canonical option, not the only way to run a task.

### FRONTIER-012 — Bounded Task Queue Workflow (`foundation/task_queue.py`)
- **status:** BUILT — `Task`/`TaskQueue`/`RunBudget`/`run()`/
  `reconcile_in_progress()`, 32 tests.
- Requested as a "reconciliation" of a previously-interrupted task-queue
  session. **Verified first, per this repo's own Zero-Trust
  Reconnaissance rule: `git status` was clean and no queue/runner code
  existed anywhere in the repository before this cycle.** There was
  nothing to reconcile — the premise was false, named honestly rather
  than silently played along with. Built fresh instead: load -> validate
  -> select eligible -> perform bounded unit -> verify -> save -> repeat
  within budget -> stop. Same state-machine discipline as `kpm/promotion/
  state_machine.py`/`foundation/flow_switch.py` (explicit transition
  table, illegal edges simply absent). `reconcile_in_progress()` directly
  implements the directive's own rule that an IN_PROGRESS task is never
  assumed complete without independent evidence.

### FRONTIER-010 — Sentinel_141 Level 1 Pulse Sweep (`foundation/sentinel.py`)
- **status:** BUILT — `Finding`/`HealthReport`/`pulse_sweep()`/
  `FourPaths`, 24 tests.
- First read-only health sensor in this repo. Real finding from its own
  first run against this repository: `schema/`, `firewall/`,
  `narrative/` have no `BUILD_REPORT.md` — recorded, not auto-fixed
  (Sentinel may not silently route a finding into execution).
- **explicitly declined this cycle:** Level 2 Deep Sweep, Level 3
  Strategic Compaction Review, external scheduling — no production
  history of Level 1 running yet to justify them; no GitHub remote to
  attach a scheduler to (same block as FRONTIER-003).

### FRONTIER-MAP — Memory Map (`MEMORY_MAP.md`)
- **status:** BUILT
- Priority item 1 of `TITANOS_MEMORY_IRRELEVANCE_PROTOCOL.md`'s own
  build order. Classifies this repo's real content into the doctrine's
  five tiers; finds a measured, real problem (1,700+ lines of Tier-3
  doctrine loading as Tier-0 cost every boot via `CLAUDE.md`'s
  `@`-imports) and names its cause honestly as a platform limitation,
  not something this cycle papered over with a fake selector.

### FRONTIER-007 — Crystalline Memory (`foundation/crystal.py`)
- **status:** BUILT — `Crystal`/`CrystalStore`, 19 tests.
- Answer to the "MEMORY" link in the chain named by
  `TITANOS_GREENLIGHT_AND_MEMETIC_DOCTRINE.md`:
  `REALITY→LEVER→ACTION→TEST→YIELD→MEMORY→PACKAGE→ADOPTION→FEEDBACK`.
  REALITY/LEVER/ACTION/TEST/YIELD already existed; PACKAGE (FRONTIER-008)
  and ADOPTION/FEEDBACK are blocked (no GitHub remote / no external ping
  surface); MEMORY was the first unblocked genuinely-missing link — every
  prior cycle's conclusion lived only in `BUILD_REPORT.md` prose, never
  as a structured record forcing "what would disprove this" to be
  answered explicitly. Not a duplicate of `reality_yield_ledger.py`
  (that answers cost/benefit; `Crystal` answers epistemic provenance).

### FRONTIER-006 — Layer 0 Worker Contract
- **status:** BUILT — `foundation/layer0_worker.py`, 18 tests.
- Third consecutive directive to request typed worker infrastructure;
  first two correctly deferred as empty theater (nine worker directories,
  no code). This ask was narrower — one contract — and Python's ABC
  mechanism enforces the four mandatory hooks (`check_existing`,
  `verify`, `preserve_provenance`, `update_state`) at instantiation time,
  stronger than the doctrine even required.
- **explicitly declined this cycle:** `foundation/PARETO_FRONTIER.md`,
  `foundation/PARETO_LEDGER.json`, `foundation/NEXT_LEVER.md` — all three
  requested by `TITANOS_LAYER0_RECURSIVE_PARETO_FRONTIER.md`, all three
  functionally duplicate this very file and `NEXT_MOVE.md`, already
  living at repo root. Not built.

### FRONTIER-000 — Narrative Atom schema + validator
- **status:** BUILT — commit pending this cycle, `narrative/schema/
  narrative_atom.py` + `narrative/validators/validate_narrative_atom.py`,
  67 tests.
- Item (A) from `TITANOS_AKASHIC_NARRATIVE_ENGINE.md`'s §XVIII list — the
  primitive every other item in that doctrine (Five-Record model, Gold
  Ledger, Isomorphism contract, Primary Narrative format) would operate
  on. Reuses `kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS` for
  `epistemic_layer` rather than a parallel vocabulary.

## Active candidates

### FRONTIER-001 — Reusable secret/credential scanner
- **status:** OPEN
- **added:** 2026-08-25
- **value:** HIGH — needed for (a) actual GitHub publication, (b) Hell's
  Gate Gate 2 (harm screen) once it evaluates real external
  contributions, (c) MAGL's own named Open-Source Release Gate checklist
  (`magl/BUILD_REPORT.md` human-decision #3).
- **effort:** LOW-MEDIUM — the pattern set is already proven (used ad hoc
  during the publication-readiness pass: API-key shapes, PEM headers,
  generic secret assignments, email addresses, filesystem-path leakage).
  Wrapping it in a tested `scan(paths) -> ScanReport` module is
  mechanical, not exploratory.
- **risk:** LOW — read-only, no privilege, fully reversible.
- **reversibility:** HIGH.
- **evidence:** the ad hoc scan already ran once for real and found one
  genuine issue (`legacy/manifests/*.json` path leakage) — proof the
  pattern set catches real things, not just theoretical ones.
- **information_gain:** MEDIUM — mostly converts known-working manual
  steps into a tested artifact, doesn't discover new unknowns.
- **dependencies:** none.
- **reality_yield:** would become the `secret_scan_evidence` input to
  `foundation/publication_gate.py::PublicationSwitch` — directly wired to
  an existing gate, not a standalone artifact nobody calls.
- **duplication_risk:** none found — no scanner module exists anywhere in
  this repo today (verified 2026-08-25).

### FRONTIER-002 — `permission_request` → `GateInput` adapter
- **status:** OPEN
- **added:** 2026-08-25
- **value:** MEDIUM — closes the third instance of this session's
  recurring "proven seam, not yet a pipeline" pattern
  (`taal/BUILD_REPORT.md` next-work-cell).
- **effort:** LOW — both shapes are already fully specified and tested
  independently; this is a pure mapping function.
- **risk:** LOW — internal only, no external-facing change, no privilege
  implications.
- **reversibility:** HIGH.
- **evidence:** none yet — untested hypothesis that closing this seam
  matters in practice; no real workload has hit it yet.
- **information_gain:** LOW-MEDIUM — would confirm or disconfirm whether
  the two shapes actually compose cleanly, which is currently assumed,
  not verified.
- **dependencies:** `taal/schema/permission_request.py`,
  `taal/gate/root_gate.py::GateInput` (both exist and are tested).
- **reality_yield:** unmeasured until built.
- **duplication_risk:** none — this exact gap is named in
  `taal/BUILD_REPORT.md` and nowhere else attempts it.

### FRONTIER-003 — CI workflow (`.github/workflows/`)
- **status:** BLOCKED
- **added:** 2026-08-25
- **value:** HIGH once a GitHub remote exists — "CI is the heartbeat"
  (`TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md` §XIV).
- **effort:** LOW — the test command is already simple and uniform
  (`python3 -m unittest discover` per subsystem), no build step, no
  secrets required to run tests.
- **risk:** LOW.
- **reversibility:** HIGH.
- **blocked_by:** `HUMAN_DECISIONS.md` item 1 — no GitHub repo exists yet
  to attach a workflow to. Writing the YAML file is cheap and could be
  done speculatively, but doctrine explicitly warns against "empty
  theater" — a workflow file with nothing to trigger it is exactly that,
  so this stays BLOCKED rather than OPEN until the repo target is named.

### FRONTIER-008 — Per-subsystem seed/manifest packaging
- **status:** BLOCKED
- **added:** 2026-08-25
- **value:** MEDIUM-HIGH once publication is real — makes each subsystem
  self-describing to an external adopter (thesis, quickstart, examples,
  failure cases, threat model, limitations, changelog, fork guide,
  manifest, provenance, contribution path — `TITANOS_GREENLIGHT_AND_
  MEMETIC_DOCTRINE.md` §3).
- **blocked_by:** same as FRONTIER-003 — no GitHub remote exists yet, so
  a fork guide / contribution path has nowhere to point. Building the
  template now would be empty theater per this repo's own standing rule.
- **dependencies:** `HUMAN_DECISIONS.md` item 1 (GitHub target).

### FRONTIER-009 — Boot Context Selector for `CLAUDE.md` doctrine imports
- **status:** OPEN
- **added:** 2026-08-25
- **value:** MEDIUM — reduces boot context size (currently 1,700+ lines
  of Tier-3 doctrine loaded unconditionally every session, per
  `MEMORY_MAP.md`), no functional/safety change.
- **effort:** MEDIUM-HIGH — requires either a platform capability that
  does not currently exist (conditional `@`-import), or removing the
  `@`-imports and replacing them with plain-text pointers `/boot` reads
  selectively — a real behavior change with a real regression risk (a
  session could simply never read a doctrine file it needed).
- **risk:** LOW-MEDIUM — the failure mode (missed doctrine) is silent,
  not loud, which is worse than a build failure.
- **dependencies:** `MEMORY_MAP.md` (built — this entry's own audit).
- **duplication_risk:** none — no selector mechanism exists today.

### FRONTIER-011 — Missing BUILD_REPORT.md for schema/, firewall/, narrative/
- **status:** OPEN
- **added:** 2026-08-25
- **source:** Sentinel_141's own first `pulse_sweep()` run against this
  repository (`foundation/sentinel.py::check_subsystem_build_reports`).
- **value:** LOW-MEDIUM — audit-trail consistency with the five sibling
  subsystems that already have one; no functional impact.
- **effort:** LOW.
- **risk:** none — pure documentation addition.

### FRONTIER-004 — Narrative Atom Store (state machine driver)
- **status:** OPEN
- **added:** 2026-08-25
- **value:** MEDIUM — `narrative/schema/narrative_atom.py`'s
  `PROMOTION_TRANSITIONS` table exists and is tested, but nothing
  actually drives an atom through it across calls (no store, no
  `reviewed_by`-gated promotion to `CANONICAL_ABSTRACTION`, mirroring
  `kpm/promotion/state_machine.py::PromotionStore`).
- **effort:** LOW — the pattern to copy already exists three times in
  this repo (`kpm/promotion/state_machine.py`,
  `foundation/flow_switch.py::FlowSwitchStore`, `firewall/quarantine.py`).
- **risk:** LOW.
- **evidence:** none yet — no real narrative atom has been promoted
  through any state.
- **dependencies:** `narrative/schema/narrative_atom.py` (built).

### FRONTIER-005 — Five-Record query views, Gold Ledger, Isomorphism contract
- **status:** OPEN
- **added:** 2026-08-25
- **value:** MEDIUM-HIGH once real atoms exist to query — currently
  zero real narrative atoms have been ingested, so building these would
  be speculative infrastructure with nothing to operate on.
- **effort:** MEDIUM.
- **dependencies:** FRONTIER-004, and a real ingestion source (no
  narrative content has been ingested into this repository yet).
- Items (B), (C), (F) from `TITANOS_AKASHIC_NARRATIVE_ENGINE.md`'s
  §XVIII list, deliberately not built this cycle — "do not build
  everything at once."

## Rejected / not on the frontier

- **Full `core/`/`workers/`/`ledgers/` directory restructure** proposed
  by `TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md` §IV — rejected as
  the *next move* (not as a future possibility) specifically because
  every one of those directories would either duplicate something that
  already exists under this repo's current structure (`foundation/` ⊃
  the doctrine's `core/obelisk`+`core/ct141`+`core/hells_gate`;
  `magl/`+`rpa/`+`taal/` already ARE the MAGL-shaped subsystems the
  doctrine's `magls/active/` etc. describes) or would be empty theater
  (`workers/scout/`, `workers/historian/` etc. have no code behind them
  yet — the four-agent pattern is currently doctrine + ad hoc execution
  in each session, not typed worker processes). Renaming working,
  tested code into a new directory tree to match a prescribed shape,
  with no functional change, is pure churn — explicitly against this
  same doctrine's own "do not rebuild existing modules under new names"
  rule (§XVI). If a genuine need for typed worker processes emerges,
  build that need directly; don't pre-build the scaffolding.

## How to use this file

1. Before proposing new work, check here first — an entry may already
   exist with its trade-offs worked out.
2. When a candidate is selected and built, update its `status` to
   `BUILT` (not deleted — provenance survives, per this doctrine's own
   Archivist principle) and note the commit.
3. When a new candidate is discovered during recon, add it here with all
   fields filled honestly — `UNKNOWN` is a legitimate value for any
   field, an empty field is not.
