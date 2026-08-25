"""
Recursion Guard (`TITANOS_RECURSION_GUARD_001.md`).

THE CAUSAL BUG THIS EXISTS TO PREVENT

`foundation/sigil.py::compute_sigil()`'s PROOF dimension shells out to
run every subsystem's test suite via a fresh `subprocess`, including
`foundation`'s own — which contains `compute_sigil()`'s own real-repo
integration tests. The first time this ran for real: `compute_sigil()`
→ spawns 8 subprocesses → one of them (`foundation`) discovers
`test_sigil.py` → that test calls `compute_sigil()` again → spawns 8
more subprocesses → one of them is `foundation` again → repeat, without
bound. Caught by watching process count climb past 50 forked
`unittest` processes in under three minutes, not by review.

The first fix (a single boolean environment variable, checked only in
the test file) worked but was the wrong layer: it let the recursive
child fully spawn and start importing before discovering it should stop,
and it wasn't reusable by anything else in this repository that might
someday shell out recursively. This module replaces it with a small,
general, two-fact guard: **what operation is currently active in my
ancestry, and how deep am I** — checked at the actual spawn point,
before a single subprocess is created for a repeat entry.

WHY ENVIRONMENT VARIABLES, NOT AN IN-MEMORY OBJECT

The failure crosses a subprocess boundary. A plain Python object held
in the parent process's memory is invisible to a child spawned via
`subprocess.run()` — it does not share memory with its parent.
Environment variables are the one thing that actually survives that
boundary automatically (every child inherits its parent's environment
unless a caller explicitly strips it), so they are the ancestry
carrier here, not a stylistic choice.

WHAT THIS DELIBERATELY DOES NOT DO

No global run-id registry, no persisted execution history, no generic
distributed-worker orchestration, no semantic "progress fingerprint"
diffing engine. For the one recursive path that exists in this
repository today, "no progress" is definitionally true the moment the
same named operation reappears in its own active ancestry — the
`ANCESTRY_LAW` case, not a case requiring state-diffing to detect. If a
genuinely different recursive shape appears later that needs more (a
real progress fingerprint, fan-out limits across sibling branches),
extend this module then, against real evidence — not now, speculatively.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

__all__ = ["GuardDecision", "GuardCheck", "check", "child_env", "DEFAULT_MAX_DEPTH"]

_OPERATION_ENV = "TITANOS_GUARD_OPERATION"
_DEPTH_ENV = "TITANOS_GUARD_DEPTH"

# Small and explicit, not an arbitrary large number — this repository's
# only known recursive shape needs depth 1 (parent -> one guarded child)
# to work at all; 3 gives headroom for one legitimate extra nesting
# level without opening the door to runaway growth.
DEFAULT_MAX_DEPTH = 3


class GuardDecision(str, Enum):
    SAFE = "SAFE"
    BLOCKED_REPEAT = "BLOCKED_REPEAT"
    BLOCKED_DEPTH = "BLOCKED_DEPTH"


@dataclass(frozen=True)
class GuardCheck:
    decision: GuardDecision
    operation: str
    depth: int
    reason: str

    def is_safe(self) -> bool:
        return self.decision is GuardDecision.SAFE


def check(operation: str, *, max_depth: int = DEFAULT_MAX_DEPTH,
          environ: Optional[dict] = None) -> GuardCheck:
    """Call BEFORE spawning nested/recursive work for `operation`.

    Reads ancestry from `environ` (defaults to the real process
    environment) — the same environment a parent stamped via
    `child_env()` for this same operation, if this process is itself a
    guarded child. Fail-closed: an ancestry that cannot be determined
    (missing/malformed depth value) is treated as depth 0, never as
    "unrelated" — see module docstring's FAIL-CLOSED LAW.
    """
    env = environ if environ is not None else os.environ
    current_operation = env.get(_OPERATION_ENV)
    try:
        depth = int(env.get(_DEPTH_ENV, "0"))
    except ValueError:
        depth = 0

    if current_operation == operation:
        return GuardCheck(
            GuardDecision.BLOCKED_REPEAT, operation, depth,
            f"operation '{operation}' is already active in ancestry at depth {depth} "
            f"— re-entry blocked before any subprocess would have been spawned",
        )
    if depth >= max_depth:
        return GuardCheck(
            GuardDecision.BLOCKED_DEPTH, operation, depth,
            f"ancestry depth {depth} >= max_depth {max_depth}",
        )
    return GuardCheck(GuardDecision.SAFE, operation, depth, "no active ancestry conflict")


def child_env(operation: str, *, base: Optional[dict] = None) -> dict:
    """Build the environment for a subprocess about to perform
    `operation`. Stamps ancestry (operation name + incremented depth) so
    a nested `check()` call — in that child, or any of its own
    descendants — can detect repeat entry before spawning further.

    `base` defaults to a copy of the real process environment (so the
    child still gets everything else it needs, e.g. PATH); pass an
    explicit `base` in tests to avoid depending on the real environment.
    """
    env = dict(base if base is not None else os.environ)
    current_depth = 0
    try:
        current_depth = int(env.get(_DEPTH_ENV, "0"))
    except ValueError:
        current_depth = 0
    env[_OPERATION_ENV] = operation
    env[_DEPTH_ENV] = str(current_depth + 1)
    return env
