# Capability Sigil

Historical compression of verified architectural maturity — distinct
from `PARETO_FRONTIER.md` (directional: where capability can go next).
The sigil changes only through verified reality, never through
documentation, renaming, or file-count inflation. Computed by
`foundation/sigil.py::compute_sigil()` — this file is a snapshot of that
function's output, not an independent source of truth. Re-run it rather
than trusting this file if it looks stale.

```
TIER:T6 | IRON:10 | LATTICE:6 | PROOF:8 | SIGHT:10 | FRONTIER:10 | ORCH:10 | MEMORY:10 | REALITY:10
```

**Computed:** 2026-08-25, commit range ending `632e774`.

## Tier justification

All suites green, zero-network dependency holds, orchestration proven
end to end (a real, non-test-double `Layer0Worker` driven through the
queue via `foundation/sentinel_worker.py`), Sentinel reports zero open
findings, every subsystem has a `BUILD_REPORT.md` — **T6**, not T7: no
external integration boundary (CI, publication) has been demonstrated
yet, so scale-readiness is not claimed.

## Per-dimension evidence

| Dimension | Score | Evidence |
|---|---|---|
| IRON | 10 | 8/8 subsystems have `BUILD_REPORT.md` |
| LATTICE | 6 | 6 modules with an explicit transition table (`kpm/promotion/state_machine.py`, `kpm/schemas/epistemic_types.py`, `foundation/task_queue.py`, `foundation/flow_switch.py`, `narrative/schema/narrative_atom.py`, `firewall/quarantine.py`) |
| PROOF | 8 | 1018 tests, all green (real subprocess run, not a file count) |
| SIGHT | 10 | Sentinel present and clean, secret scanner present and wired to `publication_gate.py` |
| FRONTIER | 10 | `PARETO_FRONTIER.md` has the Frontier Gate schema and Archive table; `NEXT_MOVE.md` and `INTUITION.md` both present |
| ORCH | 10 | Queue, worker, adapter all present, and a real worker proven end to end (not just a test double) |
| MEMORY | 10 | `Crystal`, `MEMORY_MAP.md`, `recovery_handoff()` all present |
| REALITY | 10 | Reality-yield ledger, Hell's Gate, publication gate all present, zero network-dependency imports found anywhere |

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
