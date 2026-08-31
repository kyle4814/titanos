# Capability Sigil

Historical compression of verified architectural maturity — distinct
from `PARETO_FRONTIER.md` (directional: where capability can go next).
The sigil changes only through verified reality, never through
documentation, renaming, or file-count inflation. Computed by
`foundation/sigil.py::compute_sigil()` — this file is a snapshot of that
function's output, not an independent source of truth. Re-run it rather
than trusting this file if it looks stale.

```
TIER:T3 | IRON:10 | LATTICE:7 | PROOF:10 | SIGHT:10 | FRONTIER:10 | ORCH:10 | MEMORY:10 | REALITY:6
```

**Computed:** 2026-09-01, on a clean tree with all suites green.
Previously 2026-08-27 (after `foundation/mouth_pypi.py` was added), at
which point LATTICE read 6. It is now 7: a seventh module with an
explicit transition table exists. Both this file and `CLAUDE.md` carried
the stale 6 and AGREED with each other, so
`sentinel.check_sigil_snapshot_agreement()` -- which compares snapshots
to each other and says outright that neither is ground truth -- stayed
silent. Two equally stale caches agree. See `INTUITION.md` for why the
obvious fix (a freshness check plus an auto-recompute) was built,
measured, and reverted.

## Tier justification

**T3 — an honest, evidenced drop from T7, not a bug.** This repository
was T7 as of 2026-08-26 (see git history for that snapshot). On
2026-08-27, `foundation/mouth_pypi.py` added this repository's
first-ever real network call (one GET request to PyPI's public RSS feed
for the `PyYAML` package — this repo's one real dependency), wired into
the existing hourly cron pulse. This was explicitly authorized, not
accidental. `compute_tier()`'s own rung
(`if not zero_network: return "T3", ...`) is doing exactly its job:
`_dimension_reality()` greps every `.py` file for network imports and
correctly finds one now. All test suites remain green — the drop is
specifically and only the zero-network property, not a regression in
anything else. If the network mouth is ever removed, this repository
should recompute back to T7 without needing this file or any test
changed by hand.

## Per-dimension evidence

| Dimension | Score | Evidence |
|---|---|---|
| IRON | 10 | 8/8 subsystems have `BUILD_REPORT.md` |
| LATTICE | 7 | 7 modules with an explicit transition table (`kpm/promotion/state_machine.py`, `kpm/schemas/epistemic_types.py`, `foundation/task_queue.py`, `foundation/flow_switch.py`, `narrative/schema/narrative_atom.py`, `firewall/quarantine.py`, `foundation/admission.py`) |
| PROOF | 10 | 1212 tests, all green (real subprocess run, not a file count) — crossed the 1200-test threshold in `min(10, 2 + total // 150)` |
| SIGHT | 10 | Sentinel present and clean, secret scanner present and wired to `publication_gate.py` |
| FRONTIER | 10 | `PARETO_FRONTIER.md` has the Frontier Gate schema and Archive table; `NEXT_MOVE.md` and `INTUITION.md` both present |
| ORCH | 10 | Queue, worker, adapter all present, and a real worker proven end to end (not just a test double) |
| MEMORY | 10 | `Crystal`, `MEMORY_MAP.md`, `recovery_handoff()` all present |
| REALITY | 6 | Reality-yield ledger, Hell's Gate, publication gate all present; zero-network-dependency no longer holds (`foundation/mouth_pypi.py` imports `urllib.request`), so the +4 zero-network bonus is no longer earned |

## T7's evidence, specifically (historical — true as of 2026-08-26, superseded by the network tradeoff above, not deleted)

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
