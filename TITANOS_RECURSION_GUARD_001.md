# TITANOS_RECURSION_GUARD_001

## INVARIANT

Protected execution ancestry must survive the process boundary where
recursive spawning can occur.

## PROOF

- `foundation/recursion_guard.py` — `check()`, `child_env()`, `GuardDecision`.
- `foundation/sigil.py::_dimension_proof()` — the real caller: checks
  the guard before spawning any subprocess, and stamps ancestry via
  `child_env()` on every subprocess it does spawn.
- `foundation/tests/test_recursion_guard.py` — 13 focused tests, all
  passing.
- `foundation/tests/test_sigil.py::TestComputeSigilOnRealRepo` — the
  real-repo integration path that actually exercises the guard against
  the causal bug it was built to prevent.
- Targeted run: 37/37 passing (`foundation.tests.test_sigil` +
  `foundation.tests.test_recursion_guard`).
- Full 8-subsystem regression: 8/8 passing.
- Process residue check after both runs: no persistent orphaned
  `unittest` process found.

Passing these tests proves exactly the property stated above for the
one boundary they exercise — not a general claim about all possible
recursive code in this repository.

## APPLICABILITY

Recursive or nested execution paths where a child process (or
equivalent descendant) must inherit enough execution ancestry to detect
prohibited active self-reentry *before* spawning multiplies. Currently
wired for exactly one real boundary: `compute_sigil()`'s PROOF dimension
shelling out to run subsystem test suites via `subprocess`.

This does **not** claim universal process control, does not claim all
recursion anywhere in this repository is protected, and does not claim
semantic progress detection beyond exact-operation-name repetition in
ancestry.

## LIMITATION

The guard protects the currently wired execution boundary (environment-
variable ancestry, inherited automatically by `subprocess.run()`) but
does not itself provide universal descendant tracking or
platform-independent termination of arbitrary, independently spawned
processes outside that one wiring — a process spawned through a
different mechanism (not inheriting the stamped environment) would not
be seen by this guard at all.
