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

### FRONTIER-016 — SETTLED 2026-08-28: the Consumer-Reality Contract
- **CURRENT:** the Consumer-Reality Contract below is now this
  repository's standard for the term "real consumer". Six functions
  (`read_pulse_continuity`, `read_cron_stderr`,
  `read_dependency_pressure_log`, `read_recorded_sigil`, `classify_hold`,
  `evaluate_continuation`) are consumed by `.claude/commands/boot.md`
  steps and qualify under it.
- **GAP:** closed as a doctrine question; the remaining gap is
  mechanical, not doctrinal — nothing yet checks the five clauses. That
  residue is FRONTIER-017, not this entry.
- **STATUS:** RESOLVED. Decided by direct human order, *not* by its own
  objective reopen trigger (neither (i) a new NO-BUILD citing the phrase
  nor (ii) a proposed 7th boot.md-only function had fired). Recorded so
  the closure is not later mistaken for the trigger having fired.
- **QUESTION:** does a documented, verified session protocol step count
  as a real consumer?
- **DECISION: YES — but only under the contract below.** All five clauses
  are required; failing any one makes the reference a mention, not a
  consumer.

  **CONSUMER-REALITY CONTRACT.** A documented protocol step is a real
  consumer of a callable when: (1) the document sits on a protocol path a
  session actually reaches; (2) the step names the exact callable and
  that callable exists; (3) the documented invocation executes against
  real state — signature matches and every documented outcome is
  reproducible; (4) the step states what the reader does with each
  outcome; and (5) the step states its own authority ceiling.

- **WHY (the property actually being protected):** "real consumer" exists
  to stop capability being claimed for code nothing exercises — dead
  weight that rots undetected and inflates the repo's stated ability. A
  protocol step satisfying all five clauses does exercise the callable,
  against live repository state, which is a *stronger* reality signal
  than a test fixture, not a weaker one. What it does not provide is
  *enforcement*. Those are two different properties, and this repository
  had been conflating them.
- **BOUNDARY — what does NOT count:** a mention, a "see also", a comment,
  a docstring, an index or lexicon entry, a document no protocol path
  reaches, a step naming a callable that does not exist, or a step naming
  a call but no handling of its outcomes. **And absolutely:** a
  protocol-step consumer NEVER satisfies a claim requiring
  machine-enforced invocation. It consumes the output; it is not a
  call-graph edge.
- **COUNTEREXAMPLE (verified against source, not hypothetical):**
  `COMMAND_LEXICON.md` documents a full execution chain
  (recon→delta→proof→regression→doc→commit→handoff) and reads exactly
  like a documented consumer. It fails clause 1 (referenced only as an
  index in `CLAUDE.md` prose; no protocol step invokes it), clause 2 (its
  one callable, `discover()`, is unittest's, not this repository's), and
  clause 4. `CLAUDE.md` already says of it: "a specification only, no
  runtime resolver exists or is claimed." It is a mention, not a
  consumer.
- **DOWNSTREAM EFFECT on future "no real consumer" claims:** such a claim
  must now name *which* kind of consumer is absent. "No code caller" and
  "no consumer at all" are different findings with different weight. A
  NO-BUILD may cite the absence of any consumer; it may not cite the
  absence of a code caller alone while this repository ships six
  functions consumed exactly that way. The Rejected section above was
  amended accordingly.
- **SIGIL (the drift-preventing law):** `SIGIL.DOOR` — *a governed
  callable has a real consumer iff a reachable protocol step names it,
  its target resolves, its documented outcomes reproduce, its outcome
  handling is stated, and its ceiling is stated. Consumption is not
  enforcement; a protocol consumer never proves invocation.*
- **CEILING, stated not papered over:** clauses 1, 2 and 4 are
  mechanically checkable. Clauses 3 and 5 are checkable only by a session
  executing them, as this one did. Nothing in this repository currently
  checks any of the five — see FRONTIER-017.

### FRONTIER-017 — BUILT 2026-08-28: clause-2 protocol target check
- **CURRENT:** `foundation/sentinel.py::check_protocol_document_targets()`
  is built and wired into `_LEVEL1_CHECKS`, so the hourly cron sweep now
  runs it. It resolves every fully-qualified callable named in
  `.claude/commands/*.md` against real source, in both forms in use
  (`foundation.mod.name(` and `foundation/mod.py::name(`). 10 tests.
- **GAP:** clause 2 only, and only for qualified references. Four
  residues are recorded below rather than silently absorbed.
- **PROOF EXECUTED:** four mutation classes each produced exactly one
  HIGH finding — typo'd dotted name (the original demonblade_010
  defect), typo'd path::symbol name, typo'd module, and deletion of a
  real `def` in source. Restoring the file returned zero findings. The
  9 real references in this repo resolve clean. `Finding.key()` stable
  across 3 sweeps. Replayed through live `pulse_sweep()`, not only the
  check in isolation. Full regression 1740/1740 green, 8/8 subsystems.
- **UNLOCK:** a protocol document can no longer point at a function that
  does not exist without the sweep saying so.
- **REUSE:** existing `Finding`/`_LEVEL1_CHECKS`/`_run_check_safely`
  machinery; no new module, no new authority, no scheduler change.

**Conserved residues from this build — none are lost, none are built:**
- **BLOCKED — unqualified references are out of scope by design.**
  `boot.md` contains `reconcile_sigil(REPO_ROOT, previous=recorded)` with
  no module prefix. Matching bare `name()` would require guessing which
  module to resolve against, which manufactures false positives. Asserted
  as a scope limit by `test_bare_unqualified_call_is_not_guessed_at` so a
  future edit cannot widen it silently. Reopen only if a bare reference
  is ever the ONLY form used for some callable.
- **DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION — clause 1 (reachability) and
  clause 4 (outcome handling) checks.** Both are mechanically checkable;
  neither has a reproduced defect, so building them now would be
  speculative infrastructure. Reopen when a protocol document is added
  that no path reaches, or a step is added naming a call with no outcome
  handling.
- **BLOCKED — clauses 3 and 5 are outside machine jurisdiction.** Whether
  a documented invocation executes, and whether its stated ceiling is
  honest, are only checkable by a session performing them. Named, not
  faked.
- **DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION — archive move.** This entry
  belongs in the Archive table, which requires a real commit hash. No
  commit exists (committing is not authorized). Reopen when this work is
  committed.

### FRONTIER-018 — CLOSED 2026-08-28: 7 Archive rows backfilled
- **CURRENT:** `check_frontier_hash_placeholders()` returns CLEAN. All
  seven rows now carry real, `git show`-verified commit hashes
  (`c7cb154`, `265531a`, `8c6e18f`, `dd9a7fd`×4). Closed in cycle
  demonblade_013; this entry's status field was left stale until
  2026-08-28 — the state-divergence that revealed it is recorded in
  FRONTIER-019. Formerly: seven Archive rows (FRONTIER-RPA-VALIDATION-
  BINDING, FIRST-PING, FRONTIER-KPM-E2E, FRONTIER-SITUATION-ANALYSIS-
  SLICE, FRONTIER-WORLD-PING-SLICE, FRONTIER-TECTONIC-TENSION-SLICE,
  FRONTIER-GIT-DURABILITY-AND-FIRST-SEED) still read `(this commit)`.
- **GAP:** the string is only legitimately true mid-edit, before a commit
  exists to name. These rows are committed (present in HEAD `cdce3df`),
  so each tag is false — the Archive claims a provenance it does not
  carry. Ironically FRONTIER-GIT-DURABILITY-AND-FIRST-SEED's own text
  says the prior rows' `(this commit)` tags "were false" while carrying
  the same false tag itself.
- **LEVER:** the Archive is the provenance path a future operator uses to
  find what shipped and when. Seven unresolvable pointers degrade the
  reconstruction test this repository explicitly builds toward.
- **FIRST STEP:** attribute each row to its real commit via `git log`,
  then replace the placeholder.
- **PROOF:** `check_frontier_hash_placeholders()` returns clean.
- **UNLOCK:** the Archive becomes navigable provenance rather than prose.
- **REUSE:** the check already exists and already fires; nothing new is
  needed to detect it.
- **SWEPT — closed in cycle demonblade_013**, verified by
  `check_frontier_hash_placeholders()` returning clean and by a mutation
  replay (reintroduce a placeholder → 1 finding; restore → 0).

### FRONTIER-019 — frontier status fields can go stale without detection
- **CURRENT:** class re-measured 2026-08-28 (cycle status_reality_001),
  correcting this entry's own prior "n=1" claim, which had itself gone
  stale — a small, ironic instance of exactly the failure this entry
  describes. Two distinct claim shapes actually exist among the 8
  entries in this file carrying a `PROOF` bullet:
  (a) entries naming an actual `check_*()`/`pulse_sweep()` function —
  FRONTIER-018 (`check_frontier_hash_placeholders()`) and FRONTIER-025
  (`pulse_sweep()` CLEAN) — **N=2**, not 1;
  (b) entries citing named unittest tests, mutation counts, or full
  regression numbers without naming a pulse_sweep-wired function —
  FRONTIER-020, 021/022, 023, 024 — **N=4** (5 counting sub-bullets).
- **GAP:** the two shapes have opposite risk profiles, proven by direct
  mutation, not assumed:
  **Shape (a) is SAFE** — `check_frontier_hash_placeholders()` and
  `check_ci_matrix_coverage()` (this session's own two additions) are
  stateless: they re-scan real filesystem state on every call, ignoring
  what any entry's prose claims. REPRODUCED: reintroduced a placeholder
  into a real Archive row while FRONTIER-018's own "CLOSED" prose was
  left untouched — `pulse_sweep()` fired immediately (1 finding), and
  `foundation/cron_pulse.py` already runs `pulse_sweep()` hourly
  (confirmed: `from foundation.sentinel import pulse_sweep` at its
  import line, wired into `main()`). Worst case is a ~1hr lag until the
  next tick, not silent, permanent divergence. Mutation restored;
  `pulse_sweep()` re-confirmed clean.
  **Shape (b) is UNSAFE — REPRODUCED LIVE:** reverted
  `_claims_doctrine_identity()` (the exact fix FRONTIER-024 claims
  CLOSED) back to `all()`. `pulse_sweep()` stayed at **zero findings**.
  Ground truth: `python3 -m unittest discover -s compiler` genuinely
  **FAILED** (1 failure, the exact regression test built to catch this).
  FRONTIER-024's own prose still read "CLOSED" throughout. Nothing
  local or scheduled would have caught this divergence — `pulse_sweep()`
  contains no subprocess/test-execution checks by design (only
  `foundation/sigil.py::compute_sigil()`'s PROOF dimension actually runs
  subsystem test suites, and it is not wired into cron_pulse.py; it only
  runs when manually invoked). Compounding this: `git status -sb` shows
  this branch **3 commits ahead of `origin/master`**, so even a real
  GitHub Actions CI run would not currently see this session's fixes —
  CI is a real mechanism only once pushed, and nothing pushes
  automatically. Mutation restored; compiler suite re-confirmed 16/16 OK.
- **LEVER:** shape (a) needs nothing further — already covered by an
  existing, already-scheduled primitive. Shape (b)'s only existing
  primitive that could close the gap is `compute_sigil()`'s PROOF
  dimension, which already runs every subsystem's suite — the gap is
  purely that nothing schedules it. Scheduling it (or an equivalent) is
  a real recurring-compute/cron-schedule change (~40-60s of subprocess
  work per prior measurement), which this session's own standing
  authority constraints reserve for a human decision ("do not... arm
  dormant workers... without contention"), not something to add
  unilaterally inside a bounded attack cycle.
- **FIRST STEP (shape b, if authorized):** wire `compute_sigil()` (or a
  lighter-weight targeted re-run of just the tests named in `PROOF`
  bullets) into `cron_pulse.py`'s hourly tick.
- **PROOF:** shape (a) — `check_frontier_hash_placeholders()` mutation
  matrix above. Shape (b) — `_claims_doctrine_identity()` regression
  mutation above.
- **UNLOCK:** shape (b) fixed would make ALL frontier PROOF claims,
  not just filesystem-predicate ones, self-correcting within an hour.
- **REUSE:** shape (a) needs none — already reused. Shape (b)'s fix, if
  authorized, reuses `compute_sigil()` entirely; no new test runner.
- **DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION — re-measured 2026-08-28
  (cycle status_reality_001).** Shape (a): closed by evidence, no
  action needed. Shape (b): real, reproduced, N=4-5, currently
  unbounded silent-divergence window — correctly NOT built this cycle;
  wake condition is an explicit human decision to schedule
  `compute_sigil()` (or equivalent) into cron, given its real recurring
  compute cost.

## How to use this file

1. Check here before proposing new work — an entry may already exist
   with its trade-offs worked out.
2. A candidate must pass the Frontier Gate (all 7 questions answered)
   before it's added under Active.
3. When built, move the entry's one-line summary to the Archive table
   and note the commit — don't leave stale full-prose entries active.
4. Re-verify a long-untouched entry against real repository state
   before trusting it.
