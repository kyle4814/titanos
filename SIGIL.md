# Capability Sigil

Historical compression of verified architectural maturity — distinct
from `PARETO_FRONTIER.md` (directional: where capability can go next).
The sigil changes only through verified reality, never through
documentation, renaming, or file-count inflation. Computed by
`foundation/sigil.py::compute_sigil()` — this file is a snapshot of that
function's output, not an independent source of truth. Re-run it rather
than trusting this file if it looks stale.

```
TIER:T7 | IRON:10 | LATTICE:6 | PROOF:10 | SIGHT:10 | FRONTIER:10 | ORCH:10 | MEMORY:10 | REALITY:10
```

**Computed:** 2026-08-26, commit range ending `b71982c`.

## Tier justification

**T7, earned, not aspirational.** All suites green, zero-network
dependency holds, orchestration proven end to end, Sentinel reports zero
open findings, every subsystem has a `BUILD_REPORT.md` — plus the one
new T7 fact: a real external integration boundary has actually been
demonstrated, not just built. `kyle4814/titanos` is a real, public
GitHub repository (`.git/config` has a real `origin` remote), and
`.github/workflows/tests.yml` has actually run and returned a real
success (`FIRST_PING.md` records the specific run URL and
`conclusion=success`, not just the workflow file's existence).
`compute_tier()`'s new rung (`foundation/sigil.py::
_dimension_external_integration()`) checks this with local evidence
only — no live network call, so the sigil computation itself never
breaks the zero-network property it's certifying.

## Per-dimension evidence

| Dimension | Score | Evidence |
|---|---|---|
| IRON | 10 | 8/8 subsystems have `BUILD_REPORT.md` |
| LATTICE | 6 | 6 modules with an explicit transition table (`kpm/promotion/state_machine.py`, `kpm/schemas/epistemic_types.py`, `foundation/task_queue.py`, `foundation/flow_switch.py`, `narrative/schema/narrative_atom.py`, `firewall/quarantine.py`) |
| PROOF | 10 | 1212 tests, all green (real subprocess run, not a file count) — crossed the 1200-test threshold in `min(10, 2 + total // 150)` |
| SIGHT | 10 | Sentinel present and clean, secret scanner present and wired to `publication_gate.py` |
| FRONTIER | 10 | `PARETO_FRONTIER.md` has the Frontier Gate schema and Archive table; `NEXT_MOVE.md` and `INTUITION.md` both present |
| ORCH | 10 | Queue, worker, adapter all present, and a real worker proven end to end (not just a test double) |
| MEMORY | 10 | `Crystal`, `MEMORY_MAP.md`, `recovery_handoff()` all present |
| REALITY | 10 | Reality-yield ledger, Hell's Gate, publication gate all present, zero network-dependency imports found anywhere |

## T7's evidence, specifically

| Fact | Status | Evidence |
|---|---|---|
| Remote configured | yes | `.git/config` has a real `[remote "origin"]` with a non-empty URL |
| Real external run recorded | yes | `FIRST_PING.md` documents `https://github.com/kyle4814/titanos/actions/runs/32852929273` with `conclusion=success`, an actual observed result, not a claim |

## What this deliberately does not measure

Model intelligence, consciousness, autonomous agency, adoption, funding,
user count, or global impact. It measures only what this repository's
code and tests can currently prove about itself.

## Reconciliation

Run `foundation/sigil.py::reconcile_sigil(repo_root, previous)` after
any cycle that changes capability (a component is built, verified,
invalidated, or a critical contract is added/removed). It recomputes
from scratch and reports exactly which dimensions changed and why — if
nothing crossed a threshold, it reports `changed=False` and this file
should not be rewritten.
