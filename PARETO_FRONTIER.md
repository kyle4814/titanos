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

### FRONTIER-026 — Operator digest delivered; the "upgrade massively" asks are sequenced, not built
- **CURRENT:** the money-printer digest is built and delivered
  (`foundation/ops_digest.py` roster + renderers, `foundation/telegram_notify.py`
  gated sender, phone Artifact + `SendUserFile`, wired into `next.md`'s
  end-of-run, 27 tests). This was the single highest-lever piece of Kyle's
  2026-09-04 message: he can now run everything from his phone.
- **GAP:** the same message named four larger asks, deliberately NOT built
  this cycle (CT_141 / one-bottleneck-per-cycle):
  1. **Telegram lead-contact discovery** — "start getting and searching for
     telegram contacts for leads." This is outbound-adjacent and touches
     real people; it must run through the partner-network evidence discipline
     (`foundation/partner_network.py`: a contact is never a partner, no
     scraping private data, no unsolicited contact) and the discovery gate.
     Public channel/group discovery for security-bounty and procurement
     signals is the lawful slice; scraping member lists is not.
  2. **More search loops** — additional real sources into the existing mouth
     pipeline (not a new one). Candidates already named on the board:
     Denmark `udbud.dk`, Netherlands TenderNed (Dutch-only — language is the
     open question), more EU national boards. Each is INSUFFICIENT_DATA until
     documents are read; value is real but marginal per cycle.
  3. **More agents / more loops** — `next.md` already authorizes a parallel
     swarm; the missing piece is a scheduled cadence, which is blocked on the
     same fact as the autonomy loop (a human decision on standing scheduling
     authority — see `HUMAN_DECISIONS.md`), not on code.
  4. **Auto-refresh the roster from cycle findings** — today `ops_digest.py`'s
     roster is hand-updated when an opportunity opens/closes. A cycle that
     discovers a QUALIFIED signal should append it to the roster as part of
     the same motion, so the digest can never lag the board.
- **LEVER:** #4 is the highest of the four — it closes the one honesty gap in
  the digest (roster drift), reuses the existing outcome-ledger/signal spine,
  needs no new external access, and makes every future cycle's digest
  self-maintaining. #1 has the highest ceiling but the most gates.
- **FIRST STEP:** a `roster_from_signals()` adapter that maps a QUALIFIED
  `CanonicalSignal` / entry-gate PASS into an `Opportunity`, with provenance,
  behind a test that a DISQUALIFIED/INSUFFICIENT_DATA signal never becomes a
  card.
- **PROOF:** a synthetic QUALIFIED signal produces exactly one new card;
  a synthetic INSUFFICIENT_DATA signal produces none.
- **UNLOCK:** the digest becomes a live view of the pipeline, not a
  transcription — and #2's new sources then flow to Kyle's phone automatically.
- **REUSE:** `signal_spine.py`, `opportunity.py`, `entry_gate.py`,
  `ops_digest.Opportunity`.

### FRONTIER-024 — Identity-threshold and repo-wide-discovery had zero regression protection [CLOSED same cycle]
- **CURRENT:** cycle `regression_probe_001` (2026-08-28) attacked
  whether the two fixes from `identity_classifier_001` (the `>=2`
  marker threshold, the repo-wide schema-based `applicable_doctrines()`)
  were regression-*guaranteed* or only *closed today*.
- **GAP:** both were closed-today-only. MUTATION A (threshold `>=2` ->
  `all()`): every one of the 14 committed compiler tests stayed green,
  because every real file in `doctrine/` carries all 3 markers, so the
  two implementations are behaviorally identical against the real
  directory — nothing in the committed suite could ever discriminate
  them. MUTATION B (`REPO_ROOT.rglob` -> `DOCTRINE_DIR.glob`, dropping
  `magl/constitution/OBELISK_INVARIANTS.yaml` from discovery): also
  stayed green — no committed test named that file, so nothing noticed
  it silently left the validated set. Both reproduced directly with
  `python3 -m unittest discover -s compiler` before any fix.
- **LEVER:** a receipt saying "mutation was manually demonstrated" is
  not evidence of a regression guarantee — only a committed test that
  fails on the mutation is. This gap would have let either fix silently
  erode on the next unrelated edit.
- **FIRST STEP / FIX:** two smallest discriminating tests added to
  `compiler/tests/test_workspace_root.py`:
  `test_threshold_flags_a_two_marker_fixture_without_invariants`
  (synthetic 2-marker fixture, the only assertion that can discriminate
  `>=2` from `all()` since no real file does) and
  `test_discovery_finds_obelisk_invariants_outside_doctrine_dir` (names
  the real out-of-directory file explicitly). The threshold's inline
  logic was also extracted to `_claims_doctrine_identity()` so both the
  real-directory sweep and the fixture test share one implementation.
- **PROOF:** re-ran both mutations against the fixed file —
  MUTATION A now fails
  (`test_threshold_flags_a_two_marker_fixture_without_invariants`,
  `AssertionError: False is not true`); MUTATION B now fails
  (`test_discovery_finds_obelisk_invariants_outside_doctrine_dir`,
  `'OBELISK_INVARIANTS.yaml' not found in {...}`). Control (unmutated,
  post-fix) run: OK, 16/16. Full 10-subsystem regression: 1,764
  executed tests, all OK; static `def test_*` count 1,800 (README
  corrected from 1,798). `pulse_sweep()` CLEAN.
- **UNLOCK:** the two escapes this session already closed
  (`identity_classifier_001`) now cannot silently regress on a future
  unrelated edit to `compiler/tests/test_workspace_root.py`.
- **REUSE:** no new registry/manifest/framework — two assertions added
  to the existing test file, reusing its own classmethod pattern
  (`_load`, `_supersession_is_corroborated`).

### FRONTIER-025 — CI subsystem matrix already missed a real, tested subsystem [CLOSED, cycle ci_escape_001]
- **CURRENT:** `.github/workflows/tests.yml`'s `strategy.matrix.subsystem`
  is a hand-maintained explicit list — confirmed by direct read.
- **GAP:** class-level measurement (2026-08-28, cycle ci_escape_001) of
  the full repository, not just the known instance.
  `A = TEST_BEARING_UNITS` = every `test_*.py` under the repo (`find . -name
  "test_*.py"`, excluding `.git`/`__pycache__`) = 94 files across 11
  top-level directories. `B = CI_EXECUTED_UNITS` = the then-10 matrix
  entries. `ESCAPE_SET = A - B` = exactly one file:
  `gems/claim_ledger/test_claim_ledger.py` (14 real tests). Every other
  test file nests under one of the 10 existing entries. **Verdict:
  `gems/claim_ledger` is N=1, not a general class** — no second escaped
  unit exists, and `gems/` has no doctrine establishing it as a growing
  category (checked `CLAUDE.md`, `HUMAN_DECISIONS.md`, `INTUITION.md`:
  zero prior mentions outside this session's own frontier entries).
- **END-TO-END REPRODUCTION:** simulated the exact 10-entry CI matrix
  verbatim (`python3 -m unittest discover -s <d> -p "test_*.py" -v` per
  entry) and grepped the combined verbose output for `claim_ledger` —
  zero matches, while running it directly gives `Ran 14 tests ... OK`.
  Confirmed non-execution by trace, not by absence-from-YAML alone.
- **SELF-CORRECTION:** the prior receipt's claim that fixing this
  "requires more than a one-line matrix addition (an `__init__.py`...)"
  was WRONG, falsified by direct test: `python3 -m unittest discover -s
  gems/claim_ledger -p "test_*.py"` already succeeds with **zero**
  `__init__.py` anywhere in `gems/` (Python's PEP 420 namespace-package
  support covers the leaf-directory case; only `-s gems` — the
  non-test-bearing *parent* — ever failed to import). The fix needed no
  source change at all, only a matrix line naming the leaf directory.
- **FIX (Option B won; A/C/D attacked and rejected):** added
  `- gems/claim_ledger` to the matrix (exact leaf path, zero source
  change). Option A (add `__init__.py`) was unnecessary — proven above.
  Option C (structural discovery, e.g. matrix generated from a
  filesystem scan) was REJECTED: the measured class is N=1 with no
  evidence of recurrence, so a discovery mechanism would be more
  mechanism than the measured escape justifies — same restraint already
  established by `foundation/sentinel.py`'s own
  `SUBSYSTEMS_REQUIRING_BUILD_REPORT` comment ("a directory becomes a
  subsystem by human decision, not by having a tests/ folder"). Option D
  (preserve an exclusion) was N/A — no exclusion authority for
  `gems/claim_ledger` exists anywhere; it was an unintentional escape,
  not a documented one.
- **REGRESSION GUARANTEE BUILT (reuse, not a new registry):**
  `foundation/sentinel.py::check_ci_matrix_coverage()` — a pure
  path-containment check (every `test_*.py` file's path must be
  contained under some matrix entry's directory), wired into
  `pulse_sweep()`. Deliberately does NOT decide what counts as a
  "subsystem" — only checks reachability against the matrix as declared,
  so it cannot become a second competing subsystem registry. Runs inside
  `foundation`'s own test suite, which is itself a CI matrix entry — a
  real, push-triggered CI consumer, not just a local assertion.
- **MUTATION PROOF:** reverted the real `.github/workflows/tests.yml`
  fix (removed the `gems/claim_ledger` line) and re-ran
  `TestCheckCiMatrixCoverage.test_real_repository_is_currently_clean`
  against the live repo — FAILED, correctly re-reproducing the escape.
  Restored; diff against backup confirmed byte-identical; re-ran — OK.
  6 new fixture-based tests in
  `foundation/tests/test_sentinel.py::TestCheckCiMatrixCoverage` also
  cover: real-repo-clean, escape-shape reproduction, leaf-entry
  reachability, parent-vs-sibling containment (proves real path
  containment, not string-prefix matching), missing-workflow-file
  handling, and `pulse_sweep()` wiring.
- **PROOF:** full regression re-run under the corrected 11-entry set:
  schema 67, firewall 36, kpm 106, magl 80, rpa 213, taal 203,
  foundation 950, narrative 92, legacy 7, compiler 16, `gems/claim_ledger`
  14 — all OK, TOTAL 1,784. `pulse_sweep()` CLEAN. Static `def test_*`
  count 1,806 (README corrected from 1,800; subsystem count corrected
  10→11).
- **UNLOCK:** the CI-matrix escape class (same shape as the
  doctrine-discovery escape closed earlier this session) is now
  mechanically caught for any future test file, not just retroactively
  fixed for `gems/claim_ledger`.
- **REUSE:** the exact `- <name>` matrix-list pattern already used for
  `compiler`; the exact isolated-Level-1-check pattern (`Finding`,
  `_run_check_safely`, `_LEVEL1_CHECKS`) every other sentinel check
  already uses; the fixture-based test style already established by
  `TestCheckProtocolDocumentTargets`.

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

### FRONTIER-020 — CLOSED 2026-08-28: doctrine workspace-root declarations
- **CURRENT:** all three doctrine files now declare `workspace_root`.
  `compiler/coverage.py::resolve_workspace_root()` reads it. `compiler` is
  in the CI matrix with 9 tests. doctrine-002 and POLE_REVERSAL return
  ACCEPTED; doctrine-001 correctly returns REFUSED (see below).
- **GAP:** closed. Originated as a CHAT-RECOVERED candidate (the
  "`titanos_launch/` probe") that existed only in a conversational receipt
  and was never persisted — recorded here with that provenance rather than
  silently treated as authoritative, per the case-authority rule.
- **WHAT WAS FOUND (N=3, same failure shape):** three doctrine files used
  three different implicit path prefixes (`titanos-obelisk/`,
  `titanos_launch/`, `cosmic-library/`), all resolving against the same
  parent root, none of it recorded. Running the compiler with the
  obvious-but-wrong root produced false STALE_CLAIMs that read exactly
  like doctrine drift. A false REFUSAL trains readers to ignore the tool.
- **ALSO FOUND:** doctrine-001 declared `status: ACTIVE` /
  `superseded_by: null` while doctrine-002 declared
  `supersedes: DOCTRINE-001`. Two-file contradiction, undetected because
  nothing had ever run the compiler against doctrine-001. Metadata
  corrected; its one genuine STALE_CLAIM (I-06) deliberately preserved —
  it is the historical defect doctrine-002 exists to fix.
- **PROOF:** 9 compiler tests incl. discriminating mutations (strip the
  declaration → REFUSED returns; wrong declaration → still REFUSED; CLI
  override still wins). Full sweep CLEAN, all suites green.
- **REUSE:** no new mechanism. Three per-file declarations read by the
  one existing resolver.

### FRONTIER-021 — CLOSED 2026-08-28: doctrine coverage escape
- **CURRENT:** `compiler/tests/` now discovers applicable doctrines by
  glob + the compiler's own applicability contract (a top-level
  `invariants:` key), runs every one through the compiler, and fails the
  build on any ACTIVE doctrine the compiler REFUSES. 12 tests.
- **GAP:** closed. REPRODUCED first: CI runs `unittest discover -s
  compiler`, and every prior test named its doctrine file explicitly, so
  discovery was EXPLICIT ENUMERATION INSIDE TEST CODE. A fourth file
  declaring `status: ENFORCED` against a nonexistent path was dropped
  into `doctrine/`; pointed at directly the compiler REFUSED it (exit 1),
  but the full suite stayed GREEN. It escaped validation while sitting in
  the repository. "Three known files pass" was never "a fourth cannot
  silently exist outside the boundary."
- **APPLICABILITY FILTER:** `invariants:` key present. Reuses
  `check_doctrine`'s own iteration contract rather than inventing a
  registry, manifest, or marker — a non-doctrine YAML beside them is not
  forced through and cannot false-fail (mutation-tested).
- **SUPERSEDED CARVE-OUT:** a REFUSED doctrine passes the gate only if it
  declares `status: SUPERSEDED`. doctrine-001 is exactly that — its I-06
  stale claim is the historical defect doctrine-002 exists to fix and
  must not be edited to make coverage green.
- **PROOF:** 4 discriminating mutations. escape (no root, bad path) → 2
  failures; wrong root → 1 failure; non-doctrine YAML → still OK (no
  false positive); clean tree → OK.
- **REUSE:** no new mechanism, no new state, no registry. Glob + existing
  compiler CLI + existing applicability contract.

### FRONTIER-022 — CLOSED 2026-08-28: doctrine identity + self-exemption escapes
- **CURRENT:** the coverage gate now (a) refuses to let a file claiming
  doctrine identity omit `invariants:` and thereby demote itself to
  "unrelated YAML", and (b) honours a `status: SUPERSEDED` exemption only
  when BOTH halves of the bidirectional supersession metadata agree in
  two separate files. 14 tests.
- **GAP:** closed. Two escapes REPRODUCED first.
  **B (self-exemption) was live:** a file declaring `SUPERSEDED`,
  `superseded_by: null`, a valid `workspace_root`, and `status: ENFORCED`
  against `nonexistent/nope.py` was REFUSED by the compiler (exit 1)
  while the CI gate reported OK. A lifecycle exemption the exempted file
  writes for itself is not an exemption, it is an escape hatch.
  **A (self-identification) was caught only incidentally** — by tests that
  happen to name `doctrine-002.yaml` literally. Rename or add a file and
  that accident does not repeat, so it was closed properly.
- **CORROBORATION SOURCE:** no new field. doctrine-001 declares
  `superseded_by: DOCTRINE-002`; doctrine-002 independently declares
  `supersedes: DOCTRINE-001`. Both must agree. Orphan SUPERSEDED (no
  successor) and non-reciprocal SUPERSEDED (successor never claimed it)
  are both rejected.
- **IDENTITY MARKERS:** `id` + `status` + `effective_from` — verified
  present in all three real doctrines and absent from ordinary YAML, so
  the boundary is measured, not guessed.
- **PROOF (5 discriminating mutations):** real doctrine stripped of
  `invariants` → 7 failures; new file with identity markers but no
  invariants → 1 failure; unrelated YAML → **OK, no false positive**;
  forged orphan SUPERSEDED → 1 failure; forged SUPERSEDED naming a
  successor that does not point back → 1 failure. Clean restore verified.
- **REUSE:** existing bidirectional schema metadata + existing glob
  discovery. No registry, no manifest, no lifecycle framework, no new
  field.

### FRONTIER-023 — CLOSED 2026-08-28: identity-classifier and out-of-dir escapes
- **CURRENT:** applicability discovery is now repo-wide and schema-based
  (a YAML whose `invariants:` list carries `enforced_at` is compiler-
  applicable, wherever it lives). The identity classifier uses a 2-of-3
  marker threshold instead of `all()`. Applicable set grew 3 → 4.
- **GAP:** two independent escapes, both reproduced before any change:
  a classifier that only caught the complete marker set, and a
  compiler-schema file living outside the scanned directory.
- **GAP 1 — CLASSIFIER (reproduced):** `all(m in doc for m in
  DOCTRINE_MARKERS)` meant only the COMPLETE marker set was caught.
  Enumerating all 8 subsets: **7 of 8 escaped silently.** A file with
  `{id, status}` and no `invariants:` was neither applicable nor
  malformed and fell through both boundaries. Fixed by threshold; all 4
  two-plus subsets now caught, single markers correctly still ignored.
- **GAP 2 — OUT-OF-DIR (reproduced, and it was real):**
  `magl/constitution/OBELISK_INVARIANTS.yaml` carries the exact compiler
  schema (11 invariants with `enforced_at`/`status`/`test`), lived
  outside `doctrine/`, and had **never once been validated**. Recorded as
  N=0 in the previous receipt; actually N=1 applicable (plus
  `kpm/constitution/CONSTITUTION.yaml`, which is doctrine-shaped but a
  different schema with no `invariants`). At the correct root it is
  **11/11 CONSISTENT** — never stale, just unchecked. Now declares
  `workspace_root: "../../.."` and is in the gated set.
- **FALSE-POSITIVE CONTROL:** `kpm/constitution/CONSTITUTION.yaml` has
  all three identity markers and no `invariants:` — it is a legitimately
  different artifact, not a malformed doctrine. The identity boundary
  stays scoped to `doctrine/` (where the convention holds) while
  applicability discovery is schema-based repo-wide. Verified it does not
  fail the suite.
- **PROOF:** 8-subset enumeration before (7 escapes) and after (0
  escapes); wrong-root mutation on the newly-discovered OBELISK file →
  caught; clean restore verified.
- **REUSE:** no registry, no manifest, no new field. Existing compiler
  schema + existing `workspace_root` + `rglob`.

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
| FRONTIER-RPA-VALIDATION-BINDING | Multi-turn adversarial recon (semantic equivalence-fraud hunt) found and closed a real gap: `rpa/gates/human_jurisdiction.py::authorize_pilot()` could queue any `candidate_id` for pilot review with zero connection to real, structurally validated content. Closed via 2 new `SourceRegistry` accessors (`get_by_hash`, `get_content`) + fresh recomputed validation at authorization time (never a durable "was validated" witness -- the validator is pure, so recomputation is strictly stronger). Same recon separately proved `foundation/switch_hardener.py` does NOT share this bug (no consequential consumer exists there) -- a genuine negative control, not assumed symmetry. Found and fixed one real regression during implementation: a `sys.path` insert of the hyphenated `kpm/source-vault/` dir collided with unittest's "tests" package resolution across subsystems; fixed via `importlib` file-based loading instead. 1308/1308 full regression. | `c7cb154` |
| FRONTIER-EPISTEMIC-FREEZE | Closed a real, reproduced epistemic-state collapse: froze 5 append-only record types (Claim, AtomRecord, PromotionRecord, QuarantineRecord, FlowSwitchRecord) that were bypassable via direct attribute assignment | `3dcb258` |
| FRONTIER-HISTORY-FREEZE | Closed a real, LIVE exploit: the same 5 types' `history` field was still a mutable list under freezing -- converted to tuple, closing a forged-entry bypass of `rpa/gates/human_jurisdiction.py`'s pilot-authorization gate | `8e0e12d` |
| FRONTIER-003 | CI workflow real and green (`kyle4814/titanos` created public, pushed, `.github/workflows/tests.yml` fired for the first time and passed, 8/8 subsystems) | `6fb29fa` (workflow) + live push 2026-08-25 |
| FIRST-PING | First proven `WORLD -> TITANOS -> WORLD` exchange: real GitHub Actions run ingested + classified through the existing (pre-built) digestion pipeline, self-sourced not human-supplied. See `FIRST_PING.md`. No new code. | `265531a` |
| FRONTIER-008 | Per-subsystem external packaging docs (`ADOPT.md`) for all 8 subsystems -- every quickstart independently re-run and matched, caught 3 real doc bugs before shipping | `82862e4`,`8b9d906`,`2b1fb4c`,`8c299e0`,`cb8bd84`,`3c5c87c`,`e8afcae`,`1b7793c` |
| FRONTIER-SIGIL-T7 | T7 rung implemented (`foundation/sigil.py::_dimension_external_integration()`) -- a documented-but-never-built ceiling, closed once real evidence (public repo + recorded CI success) actually existed to check against. Local-evidence-only by design, no live network call. 7 new tests, 32/32 targeted, 1212/1212 full regression. | `23373c3` |
| FRONTIER-4AGENT-FOUNDATION | 4 parallel agents built the 4 remaining feasible `foundation/MAPPING.md` items (`defusal_router.py`, `low_regret_engine.py`, `regression_engine.py`, `state_space_mapper.py`); independent adversarial review agent found and this session fixed: `ContradictionRecord` (kpm/contradictions/registry.py) was the ONE record type `EPISTEMIC_INTEGRITY_002`'s sweep missed -- same live forgeable-status/history exploit, now frozen+tupled like the other 5. Also fixed: `low_regret_engine.py` duplicate-name ambiguity + float-equality tie-detection trap, `MAPPING.md` test-count arithmetic. 1294/1294 full regression. | `522a6eb`,`6ee1a32` |
| FRONTIER-KPM-E2E | `kpm/BUILD_REPORT.md`'s own named-but-never-built next step: `kpm/tests/test_end_to_end.py` proves ingest->classify->blueprint->validate->promote genuinely connects, matching the proof `magl/rpa/taal` each already had for their own subsystem. Also found and fixed: `kpm/tests/` had no `__init__.py`, so `unittest discover` was silently never running anything placed there. Also found and fixed: `rpa/BUILD_REPORT.md` and `narrative/BUILD_REPORT.md`'s own "next smallest work cell" sections were stale, describing already-completed work (`rpa/composition/checker.py`, `narrative/store/narrative_atom_store.py`) as still pending. 1295/1295 full regression. | `8c6e18f` |
| FRONTIER-SITUATION-ANALYSIS-SLICE | 5-parallel-agent recon (cartographer/data-model/Monk-Demonblade/MAGL-bridge/red-team) then one narrow vertical slice built: `foundation/situation_analysis.py` (`monk_pass`/`demonblade_pass` pure functions, `build_magl_candidate`, `record_situation_crystal`) proves a full cycle — situation -> structure -> adversarial attack -> SURVIVED/KILLED -> MAGL candidate -> real `register_checked()`/`authorize_pilot()`/`confirm_pilot_authorized()` gates -> one durable `Crystal` a future reader can retrieve with zero conversation history. Reused every existing primitive unchanged (Crystal, ContradictionRegistry vocabulary, PromotionStore, SourceRegistry, MAGL catalogue/composition, RPA gate) — no new store, no new gate, no Monk.py/Demonblade.py class. Real finding from the recon: MAGL's `catalogue.py`/`validate_magl.py` stack and `ContradictionRegistry.record()` had **zero real non-test callers anywhere in the repo** before this slice — this is their first real caller. `build_magl_candidate()` structurally refuses a non-SURVIVED analysis (`AnalysisNotSurvived`); a negative test proves a composition conflict is still refused even for a SURVIVED candidate. 18 new tests, 1326/1326 full regression. | `dd9a7fd` |
| FRONTIER-WORLD-PING-SLICE | Second 5-parallel-agent recon (external-system cartographer/bottleneck engineer/red-team/corpus architect/integration engineer) extended the situation-analysis slice OUTWARD to a real external system (Acme Manufacturing's invoicing bottleneck, `rpa/fixtures/legacy_map.yaml`+`bottleneck.yaml`+`automation_candidate.yaml` — no synthetic fixture invented). Cartographer found `SituationAnalysis` needed **zero new fields** for external subjects. Added exactly two things: `find_bottleneck_hypotheses()` in `foundation/situation_analysis.py` (a `Claim`-based, never-a-bare-float bottleneck contract returning INSUFFICIENT_EVIDENCE/HOLD/SINGLE_CANDIDATE/AMBIGUOUS_MULTIPLE — never forces a fake single winner) and `CrystalStore.is_current()` in `foundation/crystal.py` (closed a real red-team finding: `supersedes` was validated on write but never consulted on read — zero real callers ever checked staleness). Full world-ping chain proven end-to-end on the real fixture through unmodified MAGL/RPA/Crystal gates. 33 new tests (52 total across the situation-analysis test files), 1341/1341 full regression. | `dd9a7fd` |
| FRONTIER-TECTONIC-TENSION-SLICE | Third 5-parallel-agent recon (tectonic cartographer/power-topology engineer/off-ramp engineer/red-team/integration engineer) extended the world-ping slice to STRUCTURAL TENSION between two actors — deliberately distinct from a single-actor bottleneck. Added `find_tension_hypotheses()` (two-sided, `Claim`-backed, states INSUFFICIENT_EVIDENCE/NO_TENSION_IDENTIFIED/STRUCTURAL_TENSION/CONTINGENT_TENSION/AMBIGUOUS_MULTIPLE — `STRUCTURAL_TENSION` explicitly never means "inevitable"; `ACTIVE_CLASH` was deliberately NOT implemented since distinguishing "already manifested" from "merely unresolved" would require causal/temporal understanding the keyword-overlap heuristic honestly can't provide) and `evaluate_off_ramp_candidates()` (vets caller-proposed stabilisation options against real evidence — never generates one, avoiding the "recommendation engine" trap; `NO_CREDIBLE_OFF_RAMP_IDENTIFIED`/`PRECONDITIONS_UNMET` are first-class honest outputs; `affected_relationships` mandatory-non-empty and `interim_cost_if_reversible` required-unless-irreversible close the "local stability ≠ global stability" and "reversible ≠ free" traps). Real fixture: the same Acme corpus's own `jurisdictions` block (clerk's informal $5000 approval authority vs. the formally-authority-less approval workflow) — a genuine two-sided tension already latent in existing evidence, not invented. Red team's sharpest finding (K15, dead-capability risk) was resolved by wiring the new layer into the SAME real end-to-end gate chain as the existing test, not a standalone unit test alone. 24 new tests, 1362/1362 full regression. | `dd9a7fd` |
| FRONTIER-CONTRADICTION-REGISTRY-WRITER | Fourth 5-parallel-agent recon: `ContradictionRegistry.record()` still had zero real non-test callers after three prior slices. Three independent agents (cartographer/semantics engineer/red team) converged on the same finding: `demonblade_pass()`'s `contradiction_candidates` are single-sided "unsupported dependency" findings, NOT the two-claims-that-cannot-both-be-true collision `ContradictionRegistry`'s own docstring defines — wiring them in directly would be semantic laundering, rejected as a build blocker (K3/K7). The corpus-loop engineer identified the one real subject that DOES fit: this session's own already-fixed RPA validation-transfer finding (real commit, real regression test `test_arbitrary_magl_id_with_no_validated_source_is_refused`). Built `foundation/historical_findings.py::record_rpa_validation_bypass_finding()` — one explicit, one-time, caller-invoked function recording+resolving this real historical contradiction with real evidence_refs (file paths, test name, ADOPT.md), never touching `demonblade_pass()` or `PromotionStore` directly. Proven to reach `regression_engine.check_for_regression()` as a real reader (proposes `STABLE→DEPRECATED`, never auto-executes — blueprint state confirmed unchanged after the call). Classified honestly as WRITER_TO_READER_ONLY, not a closed loop — no real external trigger outside test code exists yet. 7 new tests, 1369/1369 full regression. | `dd9a7fd` |
| FRONTIER-GIT-DURABILITY-AND-FIRST-SEED | Fifth 5-agent cycle closed the actual durability gap: all four prior cycles above were uncommitted in the working tree (their `(this commit)` tags were false). Git cartographer confirmed a clean 14-file commit set with zero unrelated changes; Osiris auditor confirmed full fresh-clone reconstructability (all 9 test questions resolved IMPLEMENTED, reasoning for every "why not X" decision — e.g. why `demonblade_pass()`'s candidates aren't wired to `ContradictionRegistry` — lives in code docstrings, not just this conversation); red team found no commit blockers. Committed as `dd9a7fd`. Then ran ONE real internal subject (the MAGL-Ω duplication-avoidance decision — `magl/BUILD_REPORT.md`'s real finding that 9/11 required invariants already existed, verified `ACCEPTED` by `compiler/coverage.py`) through the unmodified pipeline in a scratch script: `find_bottleneck_hypotheses` → `SINGLE_CANDIDATE`; `find_tension_hypotheses` → honestly `NO_TENSION_IDENTIFIED` (the `_mentions()` heuristic found no actor-name overlap in the evidence text — refused to manufacture a tension rather than force one); `demonblade_pass` → `SURVIVED`. **Correction (same cycle, caught by a second 5-agent pass before this row was committed):** the scratch script called `record_situation_crystal()` against a `CrystalStore()` instantiated in that same process — `CrystalStore` is pure in-memory with no disk backend, so that Crystal was never durable and no longer exists; the original wording here claimed it as "recorded," which overclaimed. No `Crystal` for this seed currently exists anywhere in the repository. The pipeline run itself (bottleneck/tension/demonblade results above) is real and reproducible from `magl/BUILD_REPORT.md`'s real content; only the "recorded to Crystal" step was never actually durable. Deliberately stopped before `build_magl_candidate`/MAGL/authorization either way — a historical governance decision has nothing for those gates to validate. Zero new architecture required for the pipeline itself. | `dd9a7fd` |

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
  YAML), and no protocol step or other consumer would
  invoke it — it would be a fourth function exercised only by its own
  test. (Phrasing amended 2026-08-28 by the FRONTIER-016 settlement: the
  disqualifier is the ABSENCE OF ANY CONSUMER, not the absence of a
  code-level caller specifically. This candidate had no consumer of
  either kind. Its two other objections below stand independently.) Crystal retrieval fails independently and more sharply: no
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

- **Second `autonomy_loop.py` actuator (Omega Continuity Prosecution,
  cycle demonblade_014, 2026-08-29)** — measured real recurrence across
  `foundation/pulse_log.jsonl`'s full 62-entry hourly history (the real
  unattended `cron_pulse.py` record, not a synthetic sample) rather than
  reasoning from the check list alone. Result: exactly two observation
  classes have ever fired in production — `check_readme_test_count`
  (already the one authorized actuator) and
  `check_frontier_hash_placeholders` (5 occurrences in this log, plus
  "recurred at least four times before that" per its own docstring
  referencing commit `5a9ca9f` — see FRONTIER-018). **Every other of the
  11 Level-1 checks has fired zero times in 62 real hourly cycles** —
  strictly stronger evidence than the prior "N=1, insufficient
  recurrence" kill this session had been carrying forward; re-verify
  against a longer `pulse_log.jsonl` before reopening any of them, not
  against reasoning alone.
  `check_frontier_hash_placeholders` was prosecuted seriously as the one
  candidate with real, repeated, evidenced recurrence, and **killed on a
  different axis than recurrence**: the repair is not self-verifying.
  The README actuator's post-fix `pulse_sweep()` clean state is
  *definitionally* correct — the fix recomputes the same ground truth
  the check itself reads, so "check clears" and "fix is correct" are the
  same fact. A placeholder-hash fix would have to guess the right commit
  via `git blame` on the affected line — this repo's own history
  (FRONTIER-018's manual backfill, FRONTIER-019's shape-(a)/shape-(b)
  divergence findings) already proves row text and shipping commit can
  diverge (rows edited after their describing commit, wording tweaked
  without re-attributing). An automated wrong-hash write would make
  `pulse_sweep()` report CLEAN while asserting **false provenance** into
  the Archive — silently worse than the honest placeholder it replaced,
  and per this file's own FRONTIER-018/019 entries a false archive
  citation is treated as a real, serious defect class, not a cosmetic
  one. Cheap post-fix verification cannot distinguish a correct hash
  from a plausible wrong one, which breaks the actuator design's own
  fail-closed contract (`autonomy_loop.py`'s pattern requires the
  re-run-`pulse_sweep()`-after-fix step to be *proof*, not merely
  *absence of the old symptom*). **Re-entry condition:** a mechanism
  that can independently confirm a candidate hash actually shipped the
  described capability (not merely last-touched the line) — e.g. cross-
  checking the row's own prose against that commit's diff/message — not
  yet built and not proposed as a build target this cycle; reopen only
  if that verification gap is closed first, not by trusting `git blame`
  alone.

- **New external mouth/sensor (Omega Food-Source Prosecution, cycle
  demonblade_015, 2026-08-29)** — before researching anything new, found
  `docs/SENSOR_ATLAS.yaml` already exists (commit `2172692`, one day
  prior) and already answers this exact question: 5 external candidates
  were live-fetched (`candidate_cisa_kev`, `candidate_usgs_earthquakes`,
  `candidate_noaa_nws_alerts`, `candidate_nasa_apod`,
  `candidate_arxiv_cs_cr` — all `confidence: REPRODUCED`, real WebFetch
  evidence, not training-data recall) plus the 2 existing production
  mouths (`mouth_pypi`, `mouth_github_releases`) documented for
  contrast. **Every single one of the 5 candidates carries the same
  disqualifying finding: no real consumer.** Checked directly rather
  than trusting the atlas's own prose: `foundation/dependency_pressure.py`
  — the one real consumer of the two existing mouths — explicitly
  states "No vulnerability database, no CVE lookup, no risk scoring" as
  a deliberate non-goal, which independently confirms
  `candidate_cisa_kev`'s atlas verdict (its only plausible in-repo
  consumer already refuses the job) rather than merely repeating it.
  This repository's real dependency surface remains PyYAML alone. This
  entry exists because the atlas itself was **orphaned** — nothing in
  `PARETO_FRONTIER.md`/`NEXT_MOVE.md`/`HUMAN_DECISIONS.md` referenced
  it, so a fresh cycle asking "what food source should the Demon chomp
  next" had no way to discover the live research already answered it,
  and would otherwise re-spend a live-fetch pass reproducing the same
  five verdicts. **Re-entry condition:** a real in-repository consumer
  need emerges for one of the five candidate domains (software supply
  chain beyond PyYAML, cybersecurity advisories, space/astronomy,
  weather/disaster, or academic research feeds) — not "the domain looks
  interesting," a named function or workflow that would actually act on
  the observation. Also open per the atlas's own `research_unknowns`:
  the mouth contract's 4-state enum (FIRST_SEEN/UNCHANGED/CHANGED/
  UNAVAILABLE) has no first-class EXPIRED state, found via the NWS
  alerts candidate — a real, still-unclosed contract gap, but not
  worth fixing speculatively ahead of a sensor that would need it.

- **CLOSED 2026-08-29 — `sigil.py`'s guard-ordering claim is now
  enforced.** `TestGuardRejectsBeforeAnySubprocessSpawns` in
  `foundation/tests/test_sigil.py`. Verified first that the property
  HELD (0 spawn calls under blocked ancestry) — an unenforced claim
  converted to a gate, not a reproduced defect. Two independent lenses:
  (A) trajectory — under blocked ancestry `subprocess.run` is never
  called, plus a positive control proving the unblocked path still
  spawns; (B) structure — the guard's early-return precedes every
  `subprocess.run` in the AST, catching a spawn on a branch no runtime
  case exercises. Mutation-proved: moving the guard below the loop fails
  BOTH lenses; ignoring the verdict fails lens A only — different
  reasons, so the second lens earns its place. While attacking the test
  I found my own lens A caught the bypass only as an AttributeError
  crash (the mock returned None); hardened to return a realistic fake so
  the gate fires as a clean assertion rather than by accident.
  Original entry follows for provenance.

- **OPEN SURFACE — `check_protocol_document_targets()` is blind to
  METHOD references in protocol documents.** Reproduced 2026-08-29:
  renaming `format_reliability_line` in source left the checker at 0
  findings and `pulse_sweep()` at 0 findings while `boot.md` still named
  the dead callable. Its two patterns
  (`_PROTOCOL_DOTTED_REF`, `_PROTOCOL_PATH_REF`) both require a
  `foundation.<module>.<name>(` or `foundation/<path>.py::<name>(`
  prefix; a method reference like `AutonomyReceipts.<name>()` matches
  neither. Every other callable `boot.md` routes to is a module-level
  function in the dotted form, so this was the only unprotected
  reference. **Closed locally** by a scoped test
  (`test_every_method_boot_md_names_on_this_class_actually_resolves`),
  NOT by extending the checker. **Why not extend it:** the dotted
  pattern would capture `autonomy_loop.AutonomyReceipts.` as the module
  prefix and try to resolve
  `foundation/autonomy_loop/AutonomyReceipts.py`, which does not exist —
  emitting a FALSE "module file does not exist" finding on the live
  hourly sweep. **Minimum brick if taken:** teach the resolver to fall
  back to attribute lookup on a class when the module path misses, with
  a negative test proving no false positive on the real repository.
  **Re-entry:** a second protocol document adds a method reference, or
  any method reference appears outside `AutonomyReceipts`.

- **CLOSED 2026-08-29 — `boot.md` reported the failure count without its
  bound.** Fixed structurally in `bb33be6`:
  `AutonomyReceipts.format_reliability_line()` emits observation, sample
  size, 95% bound, and sufficiency verdict as one inseparable string,
  and `boot.md` routes to it. Original entry follows for provenance.

- **(superseded, kept for provenance) `boot.md` reports the failure
  count without its bound.** Found 2026-08-29 while prosecuting the prior receipt.
  `HUMAN_DECISIONS.md` item 14 carries `failure_rate_upper_bound_95` and
  `evidence_is_sufficient_for()` (2 references), but
  `.claude/commands/boot.md` step 4b instructs the operator to report
  `attempted_and_recovered` with **0** references to either — so the
  documented operator path still surfaces a bare zero, which is exactly
  the false-confidence shape closed at the decision layer in `29ab61a`.
  The decision itself IS protected (item 14 carries the full qualifier),
  which is why this ranked second under `select_one_admitted()` rather
  than first. **Minimum brick:** add the bound and the sufficiency
  predicate to that step's reported fields. **Re-entry:** next cycle.

- **(superseded, kept for provenance) `sigil.py` guard-ordering claim
  unenforced.** Mapped 2026-08-29 rather than pattern-copying
  `autonomy_loop`'s git-verb confinement test, because the capability is
  different: sigil's risk is PROCESS SPAWNING, not git verbs. What was
  actually measured: its one `subprocess.run` has a fully constant argv
  shape (`sys.executable -m unittest discover -s <name> -p test_*.py`),
  `<name>` comes from the fixed `SUBSYSTEMS_REQUIRING_BUILD_REPORT`
  tuple, with no `shell=True`, `cwd` pinned to `repo_root`, and
  `timeout=120`. So arguments are already bounded — **no gap there.**
  The real gap is one specific claim in `_dimension_proof`'s docstring:
  "`guard_check()` is called FIRST, before any subprocess is created …
  **no subprocess is spawned at all for the repeat entry**". Nothing
  asserts that ordering. `test_recursion_guard.py` proves the guard
  function returns `BLOCKED_REPEAT` in isolation; `test_sigil.py` uses
  `guard_check` only to skip ITSELF. Neither asserts that
  `_dimension_proof` spawns ZERO subprocesses when blocked — so moving
  the guard call below the loop, or ignoring its result, would keep every
  test green. This is the F-013 class (claim with no enforcement) on a
  different capability, and the failure it prevents is not hypothetical:
  this repository's own history records 50+ forked `unittest` processes
  in under three minutes when the guard was absent.
  **Minimum brick when taken:** patch `foundation.sigil.subprocess.run`
  with a counter, force a blocked ancestry via
  `recursion_guard.child_env()`, assert zero spawns AND a guard-blocked
  result; plus the real case (unblocked → spawns occur) so the test can
  tell the two apart. **Re-entry:** next cycle, or sooner if `sigil.py`
  gains another shell-out path. Not built this cycle under the one-brick
  law; `select_one_admitted()` returned the item-14 candidate.

## How to use this file

1. Check here before proposing new work — an entry may already exist
   with its trade-offs worked out.
2. A candidate must pass the Frontier Gate (all 7 questions answered)
   before it's added under Active.
3. When built, move the entry's one-line summary to the Archive table
   and note the commit — don't leave stale full-prose entries active.
4. Re-verify a long-untouched entry against real repository state
   before trusting it.

---

## Deferred from EXP-001 (2026-09-01) — logged, not built

EXP-001's write scope forbade subsystem changes, so these are recorded
rather than acted on. Each is a candidate, not a commitment.

**FRONTIER-EXP001-A — require evidence for `Artifact.authorization_valid`.**
CURRENT: a bare unverified boolean is sufficient for `AUTHORIZED` +
`may_influence_runtime`, and disables the prompt-injection gate with it
(`failures/FAILURE_ARCHIVE.md` EXP-001-F1). GAP: no re-derivation, unlike
`publication_gate.authorize_publish()`. LEVER: the firewall is the module
most likely to be wired to untrusted input next, and this must be fixed
*before* that, not after. FIRST STEP: replace the boolean with an
authorization reference the gate re-derives. PROOF: the F1 reproduction
must return `REQUIRES_HUMAN_REVIEW` for both branches. REUSE:
`publication_gate.py`'s two-point pattern. UNLOCK: the firewall becomes
safe to wire.

**FRONTIER-EXP001-B — close the `classify_claim` evidence asymmetry.**
`_REQUIRES_EVIDENCE_TO_ENTER` is enforced on `reclassify` and not on
`classify_claim` (EXP-001-F2). Latent; both current callers are
well-behaved. FIRST STEP: apply the same check at creation. RISK: may
break callers that legitimately create pre-evidenced claims — needs a
survey first, which is why this is logged rather than done.

**FRONTIER-EXP001-C — delete the duplicated block in
`discovery_authorization.py`.** Lines 260–331 are dead code shadowed by
358–429, including an unread `_BUDGET_LEDGER` (EXP-001-F3). Pure
compaction; behaviour must not change. PROOF: budget enforcement test
still passes and the AST duplicate count drops to zero.

**FRONTIER-EXP001-D — measure `memetic_profile`, or delete it.**
Eight rhetorical dimensions are consumed by `_memetic_flags()` and carried
by the schema, and nothing in the repository produces one. On real input
the flags cannot fire. Either build the sensor or remove the consumer;
carrying an unfed capability is the "documented is not implemented" case
this repository exists to catch. Deletion is the cheaper honest option and
should be costed first.

**FRONTIER-EXP001-E — an adversarial corpus.** EXP-001 used public
READMEs, which are not trying to defeat anything, so it says nothing about
hostile input (see `experiments/EXP-001/LIMITATIONS.md`). A corpus that
actually attacks — provenance forgery, schema confusion, homoglyphs,
authority spoofing — is the natural successor and is a much larger piece
of work than one cycle.
