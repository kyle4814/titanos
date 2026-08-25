# TITANOS // CAPABILITY SIGIL & CIVILISATION INDEX

Added 2026-08-25 per Kyle's explicit instruction. Loaded at session start
via this project's `CLAUDE.md` — stateless config, not session memory.
Fifteenth doctrine file.

## THE CORE CLAIM

The Pareto frontier is directional (where capability can go next); the
sigil is historical compression (what capability has already been
earned). The sigil must never be manually incremented — it is computed
from repository evidence, and produces the same result every time
against the same repository state. Eight dimensions (IRON/LATTICE/
PROOF/SIGHT/FRONTIER/ORCHESTRATION/MEMORY/REALITY), each 0-10, each
derived from a concrete, inspectable fact — never a caller-supplied
number. A bounded tier ladder (T0-T7) is a conjunction of specific
proven properties per rung, not an averaged score — a high average with
one weak dimension cannot buy a tier it hasn't earned. The sigil
describes capability; it never grants authority, and must never bypass
gates, tests, or human authorization.

## BUILT SAME DAY

`foundation/sigil.py`: `compute_sigil()` (the only public way to produce
a `Sigil` — always recomputes, never accepts a caller score),
`compute_tier()` (pure function, the conjunction ladder), `format_sigil()`,
`reconcile_sigil()` (compares two computations, reports exactly which
dimensions changed and why, or that nothing crossed a threshold). Reuses
`foundation/sentinel.py`'s existing `SUBSYSTEMS_REQUIRING_BUILD_REPORT`
list and `pulse_sweep()` rather than re-deriving them. PROOF genuinely
runs every subsystem's test suite via subprocess (the exact invocation
this repository's commit history has always used), not a file count.

**Real repository result, computed same day:** `TIER:T6 | IRON:10 |
LATTICE:6 | PROOF:8 | SIGHT:10 | FRONTIER:10 | ORCH:10 | MEMORY:10 |
REALITY:10` — recorded in `SIGIL.md`.

## A REAL BUG FOUND AND FIXED DURING THIS BUILD

`_dimension_proof()` shells out to `python3 -m unittest discover -s
foundation` as part of computing PROOF — but `foundation/tests/`
contains this very module's own real-repository integration tests,
which call `compute_sigil()`. Without a guard, this recurses without
bound: every nested `compute_sigil()` call spawns eight subprocesses,
one of which is `foundation` again, discovering the same tests again.
This was not caught by review — it was caught by actually running the
code and watching process count climb past 50 forked `unittest`
processes in under three minutes. Fixed with `RECURSION_GUARD_ENV`: every
child subprocess `_dimension_proof` spawns carries this environment
variable set; `foundation/tests/test_sigil.py`'s real-repo test class
checks for it in `setUpClass` and skips itself when present, capping
recursion at exactly one guarded level. A `subprocess.run(..., timeout=120)`
was also added as a second, independent safety net. 25 tests, all
passing, confirmed against the real repository with zero leftover
processes after the run — checked with `ps aux`, not assumed.

## NOT BUILT

No autonomous scheduling of sigil recomputation, no dashboard, no
switch-integration policy (the directive's own "IF orchestration
maturity is below threshold, manual workflow remains required" example
is a future policy layer, not built this cycle — no current workflow in
this repository actually branches on sigil state, so building the
branch logic now would have nothing real to gate).
