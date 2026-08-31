# TITANOS — Case Study

**How a repository learned to catch itself lying.**

Revision `4cb313c` · 2,549 tests · 10 suites · 0 failures

---

## The one-sentence version

Nine engineering cycles produced nine defects. **Every single one was found
by running the system, never by reading it** — and in seven of the nine, the
thing that had been lying was an instrument built one or two cycles earlier
to stop exactly that kind of lie.

That pattern is the case study. Not the code.

---

## What was actually built

A defensive-security and epistemic-integrity toolkit: small, independently
tested Python libraries whose shared job is to refuse to let confidence,
repetition, or persuasive language substitute for evidence.

The domain that stress-tested it was commercial: scan public open-source
activity, decide which projects have a real problem worth solving, and refuse
to call anything an opportunity without evidence. That domain was chosen
because it punishes self-deception immediately — a radar that lies to you
produces a list of targets that waste your week.

---

## The nine defects, in order

Each row is a real failure with a real reproduction. None was found by review.

| # | Instrument | What it claimed | What was actually true |
|---|---|---|---|
| 1 | Demand mouth | counted open requests for help | five were already assigned to someone; it had discarded the `assignees` field |
| 2 | Code pressure | 100% repair pressure, target LOCKED | all ten commits were `github-actions[bot]` filing `fix: resolve issue #N` against itself |
| 3 | Demand direction | measured demand | measured a contributor-onboarding programme — the asks were manufactured by the *supply* side, and ~80 contributors were already queued for them |
| 4 | Communication gate | "no fetcher exists in this repository" | five fetchers existed and had been opening sockets ungated for cycles. **The sentence was the reason nobody noticed.** |
| 5 | Objective validator | unbounded objectives caught "however phrased" | `download every release across every repository on github` passed |
| 6 | Discovery budget | "a policy names a concrete objective and budget" | `max_queries` was read by no code anywhere |
| 7 | Source vault | append-only, durable, immutable | one crash-truncated line made it unconstructable, and three intact records became unreachable |
| 8 | Six "append-only ledgers" | durable | in-memory dicts. Every record lost on ordinary process exit, not just on a crash |
| 9 | Power scoring | independent corroboration across sources | one party's self-report through three channels — ~5,600 points manufacturable from a repo you own |

## The five principles that came out of it

**1 — A document that asserts an absence becomes camouflage for the thing it denies.**

Defect #4 is the sharpest lesson in the whole project. The gate was built,
tested, armed, and correct. Its own docstring said no fetcher existed. Five
fetchers existed. The gate went unwired for cycles *because* the file
guarding the door insisted there was no door. Stale documentation is not
untidiness; it is an active security control failure.

**2 — Absence of evidence gets a name of its own, or it becomes evidence of absence.**

`NEED_NOT_EXCLUDED`, `CHAIN_UNVERIFIED_LEGACY`, `NOT_CLAIMABLE`, `UNKNOWN`,
`DISPROVEN`. Each exists because the alternative — a silent zero, a default
pass, a missing record read as a clean one — had already caused a specific
error. `UNKNOWN` is never `0`.

**3 — Two things that agree can both be wrong.**

`SIGIL.md` and `CLAUDE.md` both recorded `LATTICE:6` against a real value of
7, and the check that compares them stayed silent because *they agreed with
each other*. A detector that measures consensus is not measuring truth.

**4 — Source multiplicity is not independence, and the principle applies at
every level.**

The system learned this once for *feeds* (two feeds reporting one release are
one fact) and then failed to apply it to *controlling parties* (three signals
from a repo you own are one party talking three times). Diversity of endpoint
is not diversity of witness.

**5 — Measure before encoding, and let the measurement kill your hypothesis.**

A `forks:stars` ratio looked like a decisive tell for manufactured demand —
39:1 on one target, 154:0 on another. Measured across a real sweep it flagged
9 of 27 repositories including `open-telemetry/opentelemetry.io` and `OCA/hr`,
both entirely legitimate. It is recorded in `REJECTED_DISCRIMINATORS` so it is
not proposed again. **A negative result that is written down is a permanent
asset.**

## The method

```
LOOK → VERIFY → BUILD → PROVE → RECEIPT → LEARN → MUTATE → REPEAT
```

Concretely, what this meant in practice:

- **Search before build.** Violated once — `readme_sync.py` was written to fix
  a recurring problem that `autonomy_loop.py` had already been fixing
  correctly for days. The duplicate was deleted and a guard added that
  convicts it by name. The deeper finding was worse than the duplication: the
  fixer existed and *was never being invoked*, and an unreached capability
  reads exactly like an absent one.
- **Mutation testing on every gate.** A gate is only proven by breaking it.
  One mutation revealed a *second* enforcement point nobody had documented —
  the signal spine independently refuses a demand claim with no evidence, so
  removing the direct check produced no signal at all rather than a false one.
- **Cleanroom reconstruction.** An engineer with zero context was given only
  the repository and asked whether they could continue the work. They answered
  12 of 13 questions from disk. Their four named gaps were then closed.
- **Refusal as a first-class result.** A cycle that concludes *do not build
  this* is a successful cycle. A sigil auto-fixer was built, measured, found
  to sit in a circular dependency with the value it audited, and reverted —
  with the negative result recorded so it is not attempted a third time.

## What this system does not do

Stated here because a case study that omits it is marketing.

- **No revenue. No customer. No contract.** Pipeline 0, cash 0, at every point
  in its history.
- The radar's `mouth → tentacle → signal` chain had **no in-repo caller** for
  most of this project's life; sweeps were run by hand.
- **11 of 12 gate modules have no production caller**, including the one this
  repository's own documentation calls the front door. Wiring it was evaluated
  and honestly declined: no current caller can supply the evidence its ten
  gates require, and a gate that always returns QUARANTINE is worse than none.
- 816 duplicated lines across 15 validators are recorded and deliberately not
  merged — those validators are independent by design, and a blind merge at
  the end of a session breaks six suites at once.
- **The autonomy claim is not met.** Exactly one scheduled entrypoint exists
  and it is read-only. See `foundation/autonomy_metric.py` for the honest
  measurement rather than an assertion.

## The standard

> A system that cannot detect its own false claims will eventually sell you one.

The measure of this project is not how autonomous it looks. It is whether the
next false claim it makes about itself gets caught — and by what.
