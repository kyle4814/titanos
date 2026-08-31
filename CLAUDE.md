# cosmic-library — TitanOS Epistemic Architecture

@TITANOS_GO_CYCLE_DOCTRINE.md
@TITANOS_NEXT_LEVER_SEQUENCER.md
@TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md
@TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md
@TITANOS_HELLS_GATE.md
@TITANOS_PARETO_FRONTIER_RECURSION_ENGINE.md
@TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md
@TITANOS_AKASHIC_NARRATIVE_ENGINE.md
@TITANOS_LAYER0_RECURSIVE_PARETO_FRONTIER.md
@TITANOS_GREENLIGHT_AND_MEMETIC_DOCTRINE.md
@TITANOS_MEMORY_IRRELEVANCE_PROTOCOL.md
@TITANOS_SENTINEL_141.md
@TITANOS_ADDENDUM_FRONTIER_AS_CAPABILITY_MAP.md
@TITANOS_OBELISK_ZERO_DEPENDENCY_DOCTRINE.md
@TITANOS_SIGIL_CAPABILITY_INDEX.md
@TITANOS_RECURSION_GUARD_001.md
@TITANOS_LAUNCH_SEQUENCE_001.md
@TITANOS_MONK_DEMONBLADE_PRINCIPLE.md
@TITANOS_COMMUNICATION_SWITCH_001.md

Monk-Demonblade Principle (next doctrine file after Launch Sequence
001): names, but does not newly enforce, the capability/authority
separation this repo's code already has — Demonblade proposes/attacks,
Monk demands the real call graph and real consumer before accepting a
finding, Gate is whichever existing enforcement point (Hell's Gate,
publication_gate, a domain gate) would actually apply. Pure vocabulary
and formal-notation compression of the RPA fix + switch-hardener/TAAL/
MAGL negative-control recon already completed this session — no new
code.

Recursion Guard (16th doctrine file): protected execution ancestry
must survive the process boundary where recursive spawning can occur
— `foundation/recursion_guard.py`, wired into `foundation/sigil.py`'s
subprocess-spawning PROOF dimension. Proof: 37/37 targeted, 8/8
regression, zero process residue. Commit `93b3e89`.

These sixteen files are stateless configuration — plain files in this
repository, loaded at the start of every session that works here,
independent of any conversation memory or session recall. Added
2026-08-25 per Kyle's explicit instruction.

**Reality Yield & Profit Architecture Engine** governs `/go` (slash
command, distinct from the bare word `GO`): a profit/exchange-scoped
specialization of the same cycle, adding the Micro-P&L Invariant and the
"send the smallest external ping" discipline. **Read its file's opening
note before invoking `/go`** — this repository currently has no external
ping surface (no product, no customer, no revenue), so `/go`'s own §XIII
Step 4 rule ("if no external ping exists, do not build a large system —
build the interface required to create the first one") means it will
typically resolve to ordinary GO-Cycle work inside this repo, not literal
profit-architecture construction, until that changes.

**GO Cycle Doctrine** governs autonomous build behavior: when the
operator types `GO` alone, self-navigate reconnaissance → target
selection → build → test → cross-examination → preservation → the next
cycle, through the four Alpha/Beta/Gamma/Delta lenses, without asking
what to work on unless a genuine human-authority decision is required.

**Next-Lever Sequencer** governs WHICH target Phase 3 of a GO cycle
selects: not the most interesting or most novel candidate, but the
single highest-leverage move given the leverage hierarchy (remove
blocker → verify critical assumption → use what exists → repair
load-bearing weakness → build smallest missing capability → create
reusable infrastructure → automate only after proof → scale only after
reality yield), with sequencing enforced — a lower-rung action is never
legitimate while a higher, unresolved rung is available.

## AIG compressed status packet

For a status update on a request that turned up **no repository delta**
(no new target, no new evidence, no new failure) — not for real build/recon
work, which still gets a full prose report — reply with the two-line
packet `T=<target or ∅>|Δ=0|V=P|μ=∅|S=Z` prefixed with `@R|`, followed by
`A{⏹:{no non-dominated delta}}` on its own line. (Not written as a literal
`@`-prefixed code line in this file — `foundation/sentinel.py`'s
`check_claude_md_imports` scans every line starting with `@` as a
doctrine-file import; a literal example broke that check on 2026-08-27,
caught by `foundation/tests/test_sentinel.py`. Fixed by rewording, not by
weakening the scanner.)

`T=∅` means no concrete object target (repo file, external artifact) —
it does not mean no valid work. A genuine question, a challenge to a
prior verdict, or a real proposed change to this convention itself
still gets answered even with `T=∅`; only a payload with no new
claim/command/constraint/evidence relative to the last one collapses
to the `Z` packet below. This file is `RUNTIME_LOADED` — read at every
session boot, same as this repo's other doctrine files — but following
it is `PROCESS_ONLY`, a judgment call each session makes, not something
any code here enforces.

Field meanings: `T`=target, `I`=intent, `Δ`=verified delta (0 if none),
`E`=evidence, `C`=real consumer, `V`=verify result (P/H/F), `μ`=mutation
candidate (∅ if none), `S`=state (`GO`/`HOLD`/`Q`/`X`/`Z`). Optional:
`K`=constraints, `N`=next action. `Z` = rest/stop; a valid, successful
result, not a failure — same meaning as `HOLD_NO_NON_DOMINATED_DELTA`
elsewhere in this repo's doctrine.

Stop rule: if `T=∅` and nothing new exists (no evidence/failure/lever/
consumer), the packet above is the whole reply — do not also produce an
essay, and do not spend a turn proposing changes to this packet format
itself without a concrete, evidenced gain. This is a reporting shorthand,
not a new subsystem — it governs output style only, not enforcement;
real gates remain `foundation/hells_gate.py` and friends as documented
below.

## `/boot`

Run `/boot` (a project-level slash command, `.claude/commands/boot.md`)
at the start of a session to execute the ten-step boot sequence and
produce a `BOOT STATUS` report before any GO cycle begins. This is the
literal "load on boot" step: it re-reads the actual current repository
state — every `BUILD_REPORT.md`/`MAPPING.md` under `schema/`, `firewall/`,
`kpm/`, `magl/`, `rpa/`, `taal/`, `foundation/` — rather than trusting a
prior conversation's summary of it, per the GO Cycle doctrine's own
Zero-Trust Reconnaissance principle (§V): a module list is not proof a
capability is missing or present; verified behavior is.

**Critical Function Switch-Gate Constitution** governs how doctrine
becomes enforcement: a reminder is not a guarantee, so every critical
function (publication, credential access, irreversible changes,
canonical promotion, deletion, deployment, ...) must be backed by real
code — a switch/gate/state machine the next stage cannot bypass — checked
at a minimum of two independent points, fail-closed on unknown. The
first function hard-gated under this rule: `foundation/publication_gate.py`
(publication / private-public boundary crossing), built because it was
the pending real-world action, not a hypothetical one. The second:
`foundation/communication_gate.py` (external communication) — see
`TITANOS_COMMUNICATION_SWITCH_001.md`. **The switch is now armed; the
door still does not exist.** 2026-08-27: Kyle gave a standing, bounded,
read-only discovery authorization (READ_URL/READ_API only, public
sources only, no credentials/privilege/spend/code-execution — see
`HUMAN_DECISIONS.md`), represented as real `CommunicationSwitch`
instances by `foundation/discovery_authorization.py` rather than a
prose claim a caller re-types each time. `authorize_communication()`
now genuinely returns True for an authorized `DiscoveryPolicy`.

**CORRECTED 2026-09-01.** This paragraph previously read "this
repository still makes zero network connections... no fetcher/adapter
consumes that True, and none should be built until a concrete discovery
objective is actually open." That became false when the mouths were
built and stayed in this file for several cycles. `foundation/
mouth_common.py::fetch_feed()` is the single socket in this repository
and it makes real network requests; five mouths and `target_mapping.py`
call it. For several of those cycles it did so WITHOUT consulting the
gate at all — the switch was armed and had no consumer, and this
sentence is precisely why nobody noticed, because the file documenting
the door insisted there was no door. Wired 2026-09-01: `fetch_feed()`
now calls `authorize_discovery()` before every request and refuses
outright without a `DiscoveryPolicy` naming a concrete objective and
budget. See `foundation/tests/test_network_control_plane.py`, which
attacks the gate from the positions a careless caller would occupy.
See also
`foundation/sentinel.py::classify_hold()` — the HOLD_CLASSES
(`TERMINAL_HOLD`/`BLOCKED_HOLD`/`INPUT_STARVED_HOLD`/`BUDGET_HOLD`/
`AUTHORITY_HOLD`) this authorization made worth naming, since only
`INPUT_STARVED_HOLD` is the state this switch is actually for.

**Hell's Gate** is the general admission boundary
(`foundation/hells_gate.py`): every artifact seeking to enter the
canonical core produces exactly one of ADMIT / QUARANTINE / REJECT /
HUMAN_REVIEW_REQUIRED, default QUARANTINE, never "TRUSTED." It routes
actual containment through the real `firewall.quarantine.QuarantineStore`
rather than a second store, and does not replace the more specific gates
already behind it (`publication_gate.py`, `taal/gate/root_gate.py`,
`magl/composition/engine.py`) — it's the front door those still sit
behind.

**Greenlight & Memetic Propagation Doctrine** compresses four directives
pasted in rapid succession into one file — audited against the existing
nine and found ~90% restatement (same CT_141/Hell's Gate/Four-Agent/
reality-yield shape under new names: Greenlight's RED/AMBER/QUARANTINE/
GREEN maps 1:1 onto `foundation/hells_gate.py`'s existing four outcomes,
not rebuilt). The one genuinely new, genuinely buildable gap — a
structured "why did we believe this, what would disprove it" record per
completed cycle, the doctrine's own MEMORY link in
`REALITY→LEVER→ACTION→TEST→YIELD→MEMORY→PACKAGE→ADOPTION→FEEDBACK` — is
built: `foundation/crystal.py` (`Crystal`/`CrystalStore`).

**Memory Irrelevance Protocol** audits this file's own loading discipline
against its own five-tier model (invariants / live state / executable
knowledge / indexed doctrine / provenance archive) and finds a real gap:
all eleven `@`-imported doctrine files (1,700+ lines) load unconditionally
at every boot, which is Tier 3 content paying Tier 0 cost — caused by a
named platform limitation (`@`-import has no lazy-load primitive), not
fixed this cycle. See `MEMORY_MAP.md` for the full tier classification
and `PARETO_FRONTIER.md` FRONTIER-009 for the deferred fix.

**Sentinel_141** is the repo's first read-only health sensor
(`foundation/sentinel.py::pulse_sweep()`) — deterministic checks only
(broken `@`-imports, missing `BUILD_REPORT.md`, Python syntax, duplicate
`PARETO_FRONTIER.md` ids), CT_141-compacted above 20 raw findings,
structurally forbidden from executing a finding (`FourPaths` cannot
recommend a path with no proposal; no public callable is named as an
action verb). Its first run found that `schema/`, `firewall/` and
`narrative/` had no `BUILD_REPORT.md` — since resolved; all eight
subsystems now have one, and this file contradicted itself about that
for several cycles (the "Standing facts" section below always stated it
correctly). The sentinel now runs twelve checks, not four.

**Frontier-as-Capability-Map addendum** governs `PARETO_FRONTIER.md`'s
own maintenance discipline (Frontier Gate: CURRENT/GAP/LEVER/FIRST
STEP/PROOF/UNLOCK/REUSE per entry; built items archived to a one-line
table, not left in the active scan path) and introduces `INTUITION.md`
— a low-commitment discovery surface for observations that aren't yet
evidence-backed enough to become frontier commitments.

**Obelisk Zero-Dependency Doctrine** — H0 (proven now, zero external
dependency) / H1 (resource-conditional, never claimed as implemented) /
H2 (civilisational vista, a strategic map only). Audited 2026-08-25:
zero network imports anywhere, `yaml` the sole third-party dependency —
the Obelisk Test passed as stated.

**That audit is superseded and its headline is now false.** The mouths
added `urllib.request` from 2026-08-27, which `SIGIL.md` itself records
as the cause of the T7 -> T3 tier drop and `REALITY:10 -> 6`. The repo
still has exactly one third-party dependency (`yaml`) and every suite
still runs with no network access, so the *dependency* half of the
Obelisk Test holds; the *zero network imports* half does not. Network
access is now bounded by `communication_gate.py` rather than by absence.
See `TITANOS_OBELISK_ZERO_DEPENDENCY_DOCTRINE.md`.

**Capability Sigil** (`SIGIL.md`, computed by `foundation/sigil.py::
compute_sigil()`) is historical compression — what capability has
already been earned — distinct from the frontier's directional "what's
next." Never manually incremented; recomputes from repository evidence
every time, same result for the same state. **This paragraph is a
snapshot of `SIGIL.md`'s own snapshot of `compute_sigil()`'s output --
two layers of caching one real value. Do not trust either without
re-running `compute_sigil()` if it matters to what you're about to
claim** (this exact staleness was found and corrected 2026-08-28: this
paragraph said `TIER:T7 | REALITY:10` after `SIGIL.md` itself had
already documented the real, evidenced drop to `TIER:T3 | REALITY:6`
following `mouth_pypi.py`'s network dependency two cycles earlier -- see
`SIGIL.md`'s own "CORRECTION" note). As of 2026-08-28, directly
recomputed rather than copied from either file: `TIER:T3 | IRON:10 |
LATTICE:7 | PROOF:10 | SIGHT:10 | FRONTIER:10 | ORCH:10 | MEMORY:10 |
REALITY:6`. (LATTICE corrected 6 -> 7 on 2026-09-01: `foundation/
admission.py` added a seventh explicit transition table. This file and
`SIGIL.md` both carried the stale 6 and AGREED, so the agreement check
stayed silent -- see `SIGIL.md`'s computation note.) **Caution if extending `foundation/sigil.py`:**
its PROOF dimension shells out to run every subsystem's test suite,
including `foundation`'s own — which contains this module's real-repo
tests. `foundation/recursion_guard.py::check()`/`child_env()` prevents
unbounded forking (see `TITANOS_RECURSION_GUARD_001.md`); do not remove
without understanding why it exists.

`SIGIL_LEXICON.md` indexes proven *concepts* as glyphs (execution
ancestry, bounded block, ...) — distinct from `SIGIL.md`'s maturity
tier. `COMMAND_LEXICON.md` indexes one proven *execution chain*
(recon→delta→proof→regression→process-check→doc→commit→handoff) —
a specification only, no runtime resolver exists or is claimed.

## `PARETO_FRONTIER.md`, `NEXT_MOVE.md`, and `INTUITION.md`

The persistent state layer `TITANOS_LIVING_PARETO_FRONTIER_ARCHITECTURE.md`'s
boot sequence assumed already existed — built 2026-08-25 as that
doctrine's own "highest-lever missing connection" for that cycle.
`PARETO_FRONTIER.md` is the ranked candidate-move registry (engineering
work items, not human judgment calls — see below); `NEXT_MOVE.md` is the
single standing recommendation; `INTUITION.md` is a low-commitment
discovery surface with no authority — nothing there is implementation
work until it passes the Frontier Gate and moves into
`PARETO_FRONTIER.md`. `/boot` loads all three. None replaces
`HUMAN_DECISIONS.md`.

## `HUMAN_DECISIONS.md`

**Read this before assuming something is blocked, broken, or needs to be
rebuilt.** Every judgment call this project has deliberately left to a
human, across every session, is consolidated there in one place instead
of scattered across eight `BUILD_REPORT.md` files. Kyle asked to be able
to go hands-off this machine — this file is how a future session (with
or without him present) finds out what's actually still waiting on a
decision, without re-deriving it from git history.

## The value radar (`foundation/`) — undocumented here until 2026-09-01

Thirteen modules totalling roughly 5,700 lines had no mention in this
file at all, including the largest single module in the repository. They
are the "does anyone outside care?" instrument, and every one of them
exists because a live run found the previous one lying.

- `signal_spine.py` — the canonical signal contract and the only fusion
  path. Keeps `observed_at` separate from `event_at`, preserves
  `evidence` verbatim, and collapses echoes via `source_lineage` so two
  feeds reporting one event cannot pass as two facts. Refuses to
  construct a signal claiming EXPLICIT_DEMAND with no pressure evidence
  — an independent second enforcement point, found by mutation.
- `tentacles.py` — thin adapters turning real feed items into canonical
  signals. Never fetches.
- `mouth_common.py` + `mouth_github_releases/pypi/npm/github_issues/
  github_commits.py` — the fetchers. `fetch_feed()` is the repository's
  only socket and is gated (see the communication-gate note above).
- `activity_shape.py` — human hands versus machines. `_is_bot` is the
  single bot classifier; nothing may grow a second one.
- `code_pressure.py` — share of recent commits that are repair work.
  Excludes bots entirely, after a target locked at 100% remediation
  where all ten commits were `github-actions[bot]` talking to itself.
- `demand_direction.py` — which side of the transaction the asker is on.
  A contributor-onboarding programme manufactures "help wanted" issues
  to hand to a cohort; those are labour supply wearing demand's clothes,
  and both prior gates passed them. Reads the maintainer's own declared
  labels, never intent.
- `target_mapping.py` — repo-to-registry identity, with
  `SOURCE_NATIVE`/`DECLARED_MATCH` distinguished from inference.
- `opportunity.py` — ranking and the handoff, plus `ceiling_analysis()`,
  which exists because INVESTIGATE was once structurally unreachable and
  the honest response was to make the ceiling legible rather than lower
  the threshold.
- `outcome_ledger.py` — the durable calibration spine. Content-addressed
  pre-action contexts, a witness requirement above transport, and
  `DISPROVEN` for a target a killing experiment excluded before any
  approach was made.
- `admission.py` — the work ledger and capacity report. In-memory only,
  despite "append-only" language; see the durability note below.
- `value_model.py` — value classes kept apart. UNKNOWN is never zero.
- `situation_analysis.py` — 977 lines, the largest module here, and
  entirely absent from this file until now.
- `corpus_triage.py` — decides in seconds whether a delivered corpus
  contains anything buildable. `structural_key()` collapses wording and
  keeps shape, which is what separates "twenty specifications" from "one
  specification written twenty times". Every corpus delivered to this
  repository so far has measured as scaffolding.
- `autonomy_loop.py` — the only thing authorised to repair README's test
  count, with verification, rollback and a receipt. Not scheduled; see
  `HUMAN_DECISIONS.md` for why that is a human decision.
- `secret_scanner.py`, `sentinel.py` (twelve checks), `readme` guards —
  the observation layer.

## Two honest caveats about this repository's own claims

**Durability.** Several stores describe themselves as "append-only
ledgers" and hold nothing but an in-memory dict: `crystal.py`,
`reality_yield_ledger.py`, `admission.py`, `firewall/quarantine.py`,
`kpm/promotion/state_machine.py`, `narrative/store/narrative_atom_store.py`.
"Append-only" is true of a Python list and means nothing across a
process boundary — every record in those six is lost on ordinary exit,
not merely on a crash. The genuinely durable stores are
`outcome_ledger.jsonl`, `autonomy_loop_log.jsonl`, `pulse_log.jsonl`,
`authority_ledger.jsonl` and `kpm/source-vault/registry.jsonl`. No
ledger anywhere hash-chains its records, so deleting a middle line is
undetectable; `LedgerTampered` catches in-place mutation of one record,
not deletion.

**Gates.** Twelve gate/switch modules exist, all with declarations,
implementations and tests. Exactly one is load-bearing on a real action:
`discovery_authorization`/`communication_gate`, reachable from
`fetch_feed()`. `publication_gate` is legitimately unwired — it guards
`git push`, a human action with no in-repo code path. The rest —
`hells_gate` (described above as the front door), `contribution_gate`,
`switch_hardener`, `taal/gate/root_gate`, `rpa/gates/human_jurisdiction`,
`firewall/gate` — have no production caller, and `flow_switch` and
`magl/composition/engine` are called only by callers that themselves
have none. Audited 2026-09-01. Do not read a gate's existence as
evidence that anything passes through it.

## Standing facts about this repository

Real, running Python (unittest), no runtime dependency beyond PyYAML.
Every subsystem (`schema/`, `firewall/`, `kpm/`, `magl/`, `rpa/`,
`taal/`, `foundation/`, `narrative/`) has its own `BUILD_REPORT.md` with
an honest limitations/human-decisions/next-work-cell section — read
those before assuming a capability is missing. As of the last full-repo
regression run (2026-09-01) all twelve suites pass — `schema`,
`firewall`, `kpm`, `magl`, `rpa`, `taal`, `foundation`, `narrative`,
`compiler`, `legacy`, `gems/claim_ledger`, `provenance`.

**Local green is not evidence. Check CI.** On 2026-09-01 GitHub Actions
was found to have been failing for at least eight consecutive commits
while every local run reported PASS. Nothing was flaky. Several tests
asserted on state that exists only on the machine this repository was
built on — gitignored runtime ledgers, and sibling repositories that
`doctrine/*.yaml` point at via `workspace_root: "../.."` — so "green"
meant "ran where the state happens to be". `run_all_tests.sh` was also
parsing the tail of merged stdout+stderr, so a compiler test's own JSON
output displaced the summary and 41 passing tests were reported as
`0 FAIL`. All three are fixed, and the suite is now verified in a fresh
clone with no siblings and no ledgers before being believed. Two lists
of suites (this runner and the CI matrix) had drifted in both
directions; `sentinel.check_local_runner_matches_ci` now fails when they
disagree. The count in `README.md` is the one kept current (by
`autonomy_loop.py`, the only thing authorised to write it); this file
deliberately no longer carries a second copy, because the previous one
sat at 915 for weeks while reality passed 2,400 — a hand-maintained
number in a second place is a staleness generator, not a fact.
