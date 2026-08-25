# cosmic-library — TitanOS Epistemic Architecture

@TITANOS_GO_CYCLE_DOCTRINE.md
@TITANOS_NEXT_LEVER_SEQUENCER.md
@TITANOS_REALITY_YIELD_PROFIT_ARCHITECTURE.md
@TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md
@TITANOS_HELLS_GATE.md

These five files are stateless configuration — plain files in this
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
the pending real-world action, not a hypothetical one.

**Hell's Gate** is the general admission boundary
(`foundation/hells_gate.py`): every artifact seeking to enter the
canonical core produces exactly one of ADMIT / QUARANTINE / REJECT /
HUMAN_REVIEW_REQUIRED, default QUARANTINE, never "TRUSTED." It routes
actual containment through the real `firewall.quarantine.QuarantineStore`
rather than a second store, and does not replace the more specific gates
already behind it (`publication_gate.py`, `taal/gate/root_gate.py`,
`magl/composition/engine.py`) — it's the front door those still sit
behind.

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
`taal/`, `foundation/`) has its own `BUILD_REPORT.md` with an honest
limitations/human-decisions/next-work-cell section — read those before
assuming a capability is missing. As of the last full-repo regression
run (2026-08-25), all suites pass; run them again rather than trusting
that count, since it will go stale the moment this file does not.
