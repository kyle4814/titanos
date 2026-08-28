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
now genuinely returns True for an authorized `DiscoveryPolicy` — but
this repository still makes zero network connections and still passes
the Obelisk Test unchanged: no fetcher/adapter consumes that True, and
none should be built until a concrete discovery objective is actually
open in `PARETO_FRONTIER.md` (none is, as of this entry). See also
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
action verb). Real finding from its first run: `schema/`, `firewall/`,
`narrative/` have no `BUILD_REPORT.md`.

**Frontier-as-Capability-Map addendum** governs `PARETO_FRONTIER.md`'s
own maintenance discipline (Frontier Gate: CURRENT/GAP/LEVER/FIRST
STEP/PROOF/UNLOCK/REUSE per entry; built items archived to a one-line
table, not left in the active scan path) and introduces `INTUITION.md`
— a low-commitment discovery surface for observations that aren't yet
evidence-backed enough to become frontier commitments.

**Obelisk Zero-Dependency Doctrine** — H0 (proven now, zero external
dependency) / H1 (resource-conditional, never claimed as implemented) /
H2 (civilisational vista, a strategic map only). Audited same day: zero
network imports anywhere in this repository, `yaml` the sole third-party
dependency across all eight subsystems — the Obelisk Test already
passes. See `TITANOS_OBELISK_ZERO_DEPENDENCY_DOCTRINE.md`.

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
LATTICE:6 | PROOF:10 | SIGHT:10 | FRONTIER:10 | ORCH:10 | MEMORY:10 |
REALITY:6`. **Caution if extending `foundation/sigil.py`:**
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

## Standing facts about this repository

Real, running Python (unittest), no runtime dependency beyond PyYAML.
Every subsystem (`schema/`, `firewall/`, `kpm/`, `magl/`, `rpa/`,
`taal/`, `foundation/`, `narrative/`) has its own `BUILD_REPORT.md` with
an honest limitations/human-decisions/next-work-cell section — read
those before assuming a capability is missing. As of the last full-repo
regression run (2026-08-25, post-Crystal), all 8 suites pass, 915 tests
total; run them again rather than trusting that count, since it will go
stale the moment this file does not.
