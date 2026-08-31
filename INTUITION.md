# Intuition

Low-commitment discovery surface. Per
`TITANOS_ADDENDUM_FRONTIER_AS_CAPABILITY_MAP.md`: promising
observations, repeated patterns, suspected high-leverage opportunities,
candidate connections, questions worth preserving. **Nothing here is
authorized work.** Nothing becomes implementation merely because it's
written here.

Promotion path: `INTUITION` → evidence → passes the Frontier Gate
(`PARETO_FRONTIER.md`) → repository inspection → bounded task → verified
capability. An entry moves to `PARETO_FRONTIER.md` only once it can
answer all seven Frontier Gate questions; until then it stays here,
however promising it looks.

---

## Open observations

- **`reconcile_in_progress()` is never called automatically.**
  `foundation/task_queue.py` requires a caller to explicitly invoke it
  on a task found `IN_PROGRESS` at load time — there's no hook wiring it
  into `TaskQueue.load()` or `run()`'s startup. Might be fine (explicit
  is safer than implicit for something this consequential) or might be
  a real gap once this queue has an actual cross-session persistence
  layer to recover from. Not enough evidence yet that this matters in
  practice — no persistence layer exists, so there has never been a
  real interrupted-and-reloaded queue to test it against.

- **`SentinelSweepWorker` only wraps a read-only operation.** Every
  worker proven through the queue↔worker seam so far
  (`foundation/sentinel_worker.py`) does nothing but observe. A worker
  wrapping a genuinely *mutating* operation (writing a file, promoting a
  state) hasn't been proven through the loop. FRONTIER-004 (Narrative
  Atom Store) would be a natural first real mutating worker if built
  that way — worth considering when FRONTIER-004 is picked up, not a
  separate frontier item on its own yet.

- **Correction, verified 2026-08-26, updated 2026-08-28: this claim
  was wrong for now two stores, not one.** `QuarantineStore`,
  `PromotionStore`, `RealityYieldLedger`, `CrystalStore`, `TaskQueue`
  genuinely are in-memory only. But
  `kpm/source_vault/registry.py::SourceRegistry` is NOT — by default it
  persists real, content-addressed data to
  `kpm/source-vault/registry.jsonl` + `archive/*.blob`, reloading on
  construction, and this session's own `FIRST_PING.md` work exercised
  that for real (found when the ingestion calls left real files in the
  tracked repo, not a temp dir). `foundation/authority_sigil.py::
  ReleaseLedger` (2026-08-28) is the second real exception, and
  deliberately so this time -- its own module docstring names durability
  as a load-bearing requirement (a persistent tick's budget consumption
  must survive a restart), not an incidental side effect the way
  `SourceRegistry`'s always was. Directly proven, not assumed: a
  simulated crash mid-write (a truncated trailing ledger line) is
  skipped on replay rather than crashing the whole ledger, and budget
  consumption correctly survives a fresh `ReleaseLedger` object reading
  the same file. So cross-session persistence DOES exist for two
  specific stores, just not the task-queue/promotion/ledger family this
  observation was actually worried about. `RecoveryHandoff`
  (`foundation/task_queue.py`) still can only recover within a single
  process's lifetime — that specific concern stands unchanged. Whether
  it matters for `TaskQueue` specifically depends entirely on whether
  this repository ever needs to survive a real process restart
  mid-queue — still no evidence that it does.

- **`foundation/secret_scanner.py`'s email/path-leakage patterns are
  LOW confidence and currently unused by anything.** Only
  `secret_scan_evidence` (fed by the whole `ScanReport`) is wired to
  `publication_gate.py`. Whether LOW-confidence findings should block
  `PublicationSwitch.secret_scan_passed` or just get logged is a real,
  unresolved design question — not decided.
  **Update 2026-08-26:** publication has now actually happened
  (`kyle4814/titanos` is public). The real scan (6,346 findings: 8 HIGH
  + 1 MEDIUM, both confirmed benign test fixtures; 6,337 LOW "path
  leakage", confirmed benign) was judged by a human decision at the
  time — a `PublicationSwitch` object was never actually constructed in
  code with that evidence (`grep` confirms `PublicationSwitch(` only
  appears in test files, never in a real call site). The gate exists
  and is tested; it was not the mechanism actually used for the real
  push. Still not urgent — no second real publication decision has
  needed it yet — but the gap between "gate exists" and "gate was
  actually used for the one real decision that needed it" is now a
  concrete, evidenced observation, not a hypothetical.

- **The `TITANOS_*.md` doctrine stack has grown to twelve files.**
  `MEMORY_MAP.md` measured this as a real boot-context problem
  (FRONTIER-009) but the fix isn't obviously safe (see that entry's own
  "silent failure mode" concern). Worth watching whether the doctrine
  stack keeps growing — at some size the calculus might tip even with
  the platform limitation, or a different mitigation might become
  obvious that isn't visible yet.

- **RESIDUE → DISCOVERY OBJECTIVE bridge — parked, not built.**
  2026-08-27 recon (following the discovery-authorization cycle) asked
  whether a mechanism should exist to derive a concrete
  `DiscoveryObjective` from real repository residue (so a future
  `INPUT_STARVED_HOLD`, per `foundation/sentinel.py::classify_hold()`,
  could call `foundation/discovery_authorization.py::authorize_discovery()`
  automatically instead of a human hand-typing an objective each time).
  **Finding: every currently-tracked residue in this repository is
  internally resolvable** — `PARETO_FRONTIER.md`'s two open entries
  (FRONTIER-009: needs build effort or stays correctly unbuilt;
  FRONTIER-005: needs more real internal ingestion cycles, not an
  external fact), `HUMAN_DECISIONS.md`'s open items (all human policy
  calls, not missing external facts), and every observation above —
  none of them is shaped "we don't know a fact about the outside world
  and an external artifact would resolve it." Building a
  `DiscoveryObjective` extractor now would have zero real residue to
  bind to — exactly the "dormant abstraction with no consumer" this
  session has killed every prior time it appeared (worker swarms,
  Chronos, a search engine). **Parked spec, if a real case ever
  appears:** `DiscoveryObjective(objective_id, residue_ref,
  hold_classification, exact_gap, question, expected_evidence_type,
  authorized_scope, stop_condition)` — `residue_ref` mandatory, pointing
  at an existing `PARETO_FRONTIER.md` entry's `GAP` field (the correct
  existing structured-residue surface — reuse, do not duplicate);
  reject on generic gap/question, unnamed expected evidence, scope
  outside `READ_URL`/`READ_API`, or an ineligible `HOLD_CLASS`. Do not
  build this speculatively — wait for a real `PARETO_FRONTIER.md` GAP
  that is genuinely external-fact-shaped, then build the extractor
  against that one real case, the same way `mouth_common.py` was only
  extracted after two real duplicated mouths existed to compare.

- **"ZEUS MEKANIKZ" — a possible future public-facing layer, named,
  not built.** 2026-08-27: a brand name with zero prior occurrence
  anywhere in this repository was proposed as a higher-level
  pressure/bottleneck/cooperation-resolution expression sitting on top
  of TitanOS's existing epistemic substrate (evidence, provenance,
  admission, authority, receipts). Evaluated against real repo state,
  not branding enthusiasm:
  - **Rename TitanOS → ZEUS MEKANIKZ: rejected.** ~20 `TITANOS_*.md`
    doctrine files, `README.md`, `LICENSE`, `SIGIL.md`,
    `HUMAN_DECISIONS.md`, and the live public repo `kyle4814/titanos`
    (real CI history attached to that name, per `FIRST_PING.md`) all
    carry the existing identity. A rename destroys real, load-bearing
    continuity for zero functional gain, and a public identity change
    with no new capability behind it reads as identity laundering to
    an external observer, not growth.
  - **Separate ZEUS MEKANIKZ codebase: rejected.** Would duplicate
    `hells_gate.py`, `communication_gate.py`, `SourceRegistry`,
    `sentinel.py`, `crystal.py` — real, tested infrastructure — against
    zero current evidence of a second audience needing separate
    plumbing. Exactly the "empty theater" this session has killed every
    prior time a swarm/engine/second-store was proposed with no real
    consumer.
  - **TitanOS stays the verified substrate; "ZEUS MEKANIKZ" is a named,
    unbuilt architectural hypothesis for a future public-facing layer:
    survives, as a label only.** This repository has no product, no
    customer, no revenue surface, and no external ping — same standing
    fact `TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md` already
    establishes — so a "resolution/cooperation layer" has no real
    consumer *yet* either. Recorded here, not promoted to
    `PARETO_FRONTIER.md`, because it cannot answer the Frontier Gate's
    FIRST STEP/PROOF questions honestly — there is nothing to build
    against. **No code, no new file, no rename executed.** Promotion
    path if a real consumer ever appears (a genuine external actor
    asking "what does this do and can I help"): a single new
    documentation surface reusing `PARETO_FRONTIER.md`'s Frontier Gate
    shape and `HUMAN_DECISIONS.md`'s resolved-entry convention, not a
    parallel identity.

- **Command language / sigil→IR compiler / issue-comment bot — parked,
  not built.** 2026-08-27: a directive proposed a layered command
  architecture (personality → alias resolution → canonical IR →
  authority check → primitive → execution → receipt) and a
  `/titanos <command> CASE-N` GitHub-issue-comment bot surface.
  **Real recon, not assumed:** no command/alias/IR mechanism exists
  anywhere in this repository (`grep` for `Command`/`alias_resolution`/
  `canonical_command` across all `.py` files: zero matches); no
  issue-comment-triggered GitHub Action exists; zero cases have ever
  been filed (the "Bring a bottleneck" issue template built the same
  cycle is the very first case-intake surface this repo has had).
  **Killed for now, correctly:** an issue-comment bot means parsing
  attacker-controlled input from the public internet and mapping it to
  execution — a real, consequential security surface — with zero
  evidence yet that any case volume exists to justify it. A sigil→IR
  compiler with no command ever issued is exactly the "architecturally
  beautiful, no current consumer" pattern this session kills every time
  it appears. Building either now would be "pre-building a mall" the
  same directive that proposed them explicitly forbids in the same
  breath. **Correct next trigger:** a real filed case (via the new
  issue template) that a human actually wants to process through a
  repeatable, inspectable step sequence — build the case object and
  the one primitive that case needs, the same way `mouth_common.py` was
  only extracted after two real duplicated mouths existed to compare.
  Do not build the general architecture first and wait for cases to
  arrive to justify it.

## Questions worth preserving, not yet answered

- Does `taal/gate/root_gate.py::GateInput` actually need every field
  `permission_request.py` provides, or does FRONTIER-002's adapter
  reveal an intentional narrowing? Won't know until it's built.
- ~~Is `CrystalStore.reusable_abstractions()` actually queried by
  anything yet~~ — **Answered 2026-08-26:** no. `grep` confirms its
  only callers are its own tests. Confirmed unused convenience method,
  not a hidden dependency — do not add surface area to `crystal.py`'s
  query API without a real caller motivating it first.

## The sigil measures the sentinel that would audit it (2026-09-01)

**Status:** built, measured, reverted. Not a proposal — a recorded
negative result, so the same build is not attempted a third time.

`check_sigil_snapshot_agreement()` compares SIGIL.md and CLAUDE.md to
each other and states plainly that "neither document is ground truth."
That leaves a blind spot it cannot close by construction: when every
cached snapshot is equally stale they agree, and the sweep is silent.
This was not hypothetical — both files carried `LATTICE:6` against a
real `compute_sigil()` value of `LATTICE:7` for several cycles.

The obvious fix is a freshness check plus an auto-recompute in
`autonomy_loop.py`. It was built. Running it once found three defects,
two mine and one structural:

1. **Date granularity made the check unsatisfiable.** SIGIL.md records
   `**Computed:** <date>`, and the check compared file mtimes against
   midnight of that date, so any file touched the same day looked newer
   than a same-day recompute. The condition could never clear.
2. **The fix wrote one snapshot, not both.** CLAUDE.md's sigil line is
   wrapped across lines inside prose; SIGIL.md's sits in a fenced block.
   One regex matched one of them, so the "fix" created the disagreement
   the other check then reported. The manual correction had to handle
   both formats too — that is a property of the files, not a bug in the
   attempt.
3. **The sigil and the sentinel are circularly dependent.** This is the
   one that kills the approach. `_dimension_sight()` scores partly on
   `clean=yes/no` — whether the pulse currently reports findings. So ANY
   new sentinel check that fires lowers SIGHT, which changes the sigil,
   which makes every snapshot stale, which fires the check again. An
   auto-fixer in that loop oscillates: the value it writes depends on
   whether it currently has anything to say.

Observed directly: adding the freshness check dropped SIGHT 10 -> 7 and
the tier T3 -> T2, and failed two `test_sigil` assertions that pin SIGHT
at 10 — before the fixer had written anything.

**What this means for the standing question of scheduling
`autonomy_loop.py`** (see `HUMAN_DECISIONS.md`): the recommendation to
leave it manual now rests on measurement rather than caution. The loop's
second finding class was attempted and is not safely automatable. Of the
sentinel's twelve checks, README test-count drift remains the only one
with a mechanically determinable, non-fabricating fix — the others
require judgement (a missing BUILD_REPORT.md cannot be auto-written
without inventing its contents; a broken `@`-import cannot be repaired
without knowing what the file should have said).

**What would change this.** A sigil whose dimensions do not include the
sentinel's own output would break the cycle and make the freshness fix
viable. That is a real change to `sigil.py`'s definition of SIGHT, not a
patch to the check, and it should not be made merely to enable an
auto-fixer — SIGHT scoring on pulse cleanliness is defensible on its own
terms.
