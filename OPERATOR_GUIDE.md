# Operator Guide

For a fresh human operator — with or without Kyle present — picking this
repository up. Written because `TITANOS_LAYER0_RECURSIVE_PARETO_
FRONTIER.md` asked directly for it: nothing before this file explained
the actual `/boot` → `/go` workflow end to end.

## 1. `/boot`

Run the `/boot` slash command (`.claude/commands/boot.md`). It re-verifies
real state rather than trusting a prior conversation: runs the CT_141 and
Black-Ice-gate test suites, reads every subsystem's `BUILD_REPORT.md`,
reads `HUMAN_DECISIONS.md` and `PARETO_FRONTIER.md`/`NEXT_MOVE.md`, runs
`git log`, runs the full test suite, and reports:

```
BOOT STATUS: / CORE: / STATE: / OBJECTIVE: / BOTTLENECK: /
HIGHEST LEVER: / NEXT MOVE: / GO / HOLD / HUMAN DECISION:
```

`/boot` never starts building anything. It stops at the report.

## 2. Review the frontier

Read `PARETO_FRONTIER.md` (ranked candidate engineering moves, each with
value/effort/risk/reversibility/evidence) and `NEXT_MOVE.md` (the single
standing recommendation). Also check `HUMAN_DECISIONS.md` — a different
kind of list: judgment calls only a human can resolve, not engineering
work items.

## 3. Issue `/go`

`.claude/commands/go.md` runs one bounded cycle: re-verifies state,
applies the Alpha/Beta/Gamma/Delta lenses to the recommended move,
checks it against CT_141 and Hell's Gate, builds the smallest safe
increment if it survives, tests it, records reality yield, updates the
frontier, and halts. It does not chain into a second cycle automatically.

## 4. Observe the cycle

Every `/go` cycle ends with a report in this shape (exact fields vary
slightly by which doctrine file is currently framing the cycle, but the
substance is constant):

```
[CURRENT STATE] [WHAT CHANGED] [BUILT] [TESTED] [REALITY YIELD]
[UNCERTAINTY] [NEXT MOVE] [STOP CONDITION]
```

Read the STOP CONDITION line specifically — it says why the cycle ended,
not just that it did.

## 5. Inspect the ledger

`foundation/reality_yield_ledger.py`'s `RealityYieldLedger` records every
yield assessment ever made, append-only — including negative ones and
superseded ones (a later downgrade never erases an earlier optimistic
entry). There is no CLI for this yet; inspect it via a short Python
session (`from foundation.reality_yield_ledger import RealityYieldLedger`)
or read the relevant `BUILD_REPORT.md`'s "Real findings" sections, which
narrate the same information in prose.

## 6. Reject a recommendation

`NEXT_MOVE.md`'s recommendation is exactly that — a recommendation, not
an instruction. Nothing in this repository executes it without a human
(or a `/go` invocation) actively choosing to. To reject it: just don't
run `/go` on it, and optionally note why in `PARETO_FRONTIER.md`'s entry
for that candidate (mark `status: REJECTED`, keep the entry — this
codebase's standing rule is that rejected work is recorded, never
deleted, so the reasoning survives for the next person who might
otherwise re-propose the same thing).

## 7. Recover from failure

If a `/go` cycle's build step fails or a test regresses: the relevant
`BUILD_REPORT.md`'s "Self-repair" pattern applies (see
`TITANOS_GO_CYCLE_DOCTRINE.md` §XII) — observe the failure, reproduce it,
identify the mechanism and blast radius, contain it, apply the minimum
patch, add a regression test, record the root cause, re-run the affected
suite. `failures/FAILURE_ARCHIVE.md` has real, worked examples of this
exact process from earlier in this repository's history — read one
before improvising a recovery approach from scratch.

## What this guide is not

It is not a replacement for the nine `TITANOS_*.md` doctrine files —
those are the actual governing rules, `@`-imported by `CLAUDE.md` every
session. This is the short version: how the pieces fit together in
practice, for someone who doesn't want to read nine doctrine files before
their first `/boot`.
