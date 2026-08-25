"""
Capability Sigil (`TITANOS_SIGIL_CAPABILITY_INDEX.md` / MAGL_SIGIL_001).

WHAT THIS IS, AND WHAT IT IS NOT

The Pareto frontier (`PARETO_FRONTIER.md`) is directional — where
capability can go next. The sigil is historical compression — what
capability has already been earned, derived entirely from repository
evidence. It is not a model-intelligence score, not a consciousness
claim, not a measure of autonomous agency. It measures only what this
codebase can demonstrably support right now, computed the same way
every time from the same evidence — never hand-edited.

SOURCE-OF-TRUTH LAW, ENFORCED BY CONSTRUCTION

Every `_dimension_*` function below inspects real repository state
(file existence, grep-detectable patterns, actual test execution) and
returns an integer 0-10 plus a one-line justification string citing the
concrete evidence. There is no code path anywhere in this module that
accepts a caller-supplied score — `compute_sigil()` is the only public
way to produce a `Sigil`, and it always recomputes from scratch. Calling
it twice against an unchanged repository produces byte-identical output
(verified by test) — this is what "the frontier must not directly
mutate the sigil; verified reality must" means in code, not prose.

WHY RUNNING THE ACTUAL TEST SUITES BELONGS HERE, NOT JUST GREP

PROOF's score is not "does a tests/ directory exist" — it is the
literal pass/fail result of running every subsystem's suite via
`unittest`, exactly the same invocation this repository's own commit
history has run before every commit. A sigil that only checked for the
presence of test files could not detect a real regression; this one
would, because it runs them.

TIER LADDER, EACH RUNG A CONJUNCTION OF CONCRETE FACTS

Not score thresholds averaged together (which is easy to game by
padding one dimension) — an explicit conjunction of specific proven
properties per rung, checked in `compute_tier()`. A tier can only be
reached by satisfying every fact the rung requires; nothing here awards
a tier for a high average with one dimension carrying the rest.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from foundation.sentinel import SUBSYSTEMS_REQUIRING_BUILD_REPORT, pulse_sweep
from foundation.recursion_guard import GuardDecision, check as guard_check, child_env as guard_child_env

__all__ = [
    "Sigil", "SigilReconciliation", "compute_sigil", "reconcile_sigil", "format_sigil",
    "PROOF_OPERATION",
]

# `_dimension_proof` shells out to `python3 -m unittest discover -s
# foundation`, and `foundation/tests/` contains this module's own
# real-repo integration tests, which call `compute_sigil()`. Without a
# guard this recurses without bound: every nested compute_sigil() spawns
# its own eight subprocesses, one of which is "foundation" again — this
# was discovered by actually triggering the fork bomb during development,
# not reasoned out in advance. `foundation/recursion_guard.py` is the
# general fix (see its own docstring for the full causal chain and why
# a single ad hoc boolean env var was replaced with it): before spawning
# any subprocess, `_dimension_proof` calls `guard_check(PROOF_OPERATION)`
# — a repeat entry is blocked BEFORE a single subprocess is created, not
# after a recursive child has already started and must notice on its own.
PROOF_OPERATION = "sigil_proof_sweep"

DIMENSION_NAMES = (
    "iron", "lattice", "proof", "sight", "frontier", "orchestration", "memory", "reality",
)

_TRANSITIONS_PATTERN = re.compile(r"^[A-Z_]*TRANSITIONS\s*[:=]", re.MULTILINE)
_EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", "tests"}


def _iter_py_files(repo_root: Path):
    for path in repo_root.rglob("*.py"):
        if any(part in _EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def _dimension_iron(repo_root: Path) -> tuple[int, str]:
    """Durable code foundation: subsystems with a real BUILD_REPORT.md
    audit trail (`sentinel.py`'s own fixed list, not re-derived here)."""
    present = sum(
        1 for name in SUBSYSTEMS_REQUIRING_BUILD_REPORT
        if (repo_root / name / "BUILD_REPORT.md").exists()
    )
    total = len(SUBSYSTEMS_REQUIRING_BUILD_REPORT)
    score = round(10 * present / total) if total else 0
    return score, f"{present}/{total} subsystems have BUILD_REPORT.md"


def _dimension_lattice(repo_root: Path) -> tuple[int, str]:
    """Explicit constraints: modules declaring a real transition table
    (grep-detectable `..._TRANSITIONS = {...}` pattern), not a hardcoded
    list — stays accurate as new gates/state-machines are added."""
    files = []
    for path in _iter_py_files(repo_root):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        if _TRANSITIONS_PATTERN.search(text):
            files.append(path)
    score = min(10, len(files))
    return score, f"{len(files)} modules with an explicit transition table"


_TESTS_RUN_PATTERN = re.compile(r"Ran (\d+) tests?")


def _dimension_proof(repo_root: Path) -> tuple[int, str, bool, int]:
    """Test coverage: actually runs every subsystem's suite via a fresh
    subprocess per subsystem — the exact invocation this repository's
    own commit history has always used
    (`python3 -m unittest discover -s <subsystem> -p "test_*.py"`).

    Deliberately NOT a single in-process `unittest.TestLoader().discover()`
    loop over all eight subsystems: multiple subsystems declare a
    same-named `tests` subpackage (e.g. `magl/tests/`, `rpa/tests/`,
    `taal/tests/`, `foundation/tests/`), and Python's `sys.modules` cache
    collides across sequential in-process `discover()` calls, silently
    producing spurious import failures for every subsystem after the
    first. This was caught by actually running this function and
    comparing its count against known reality, not assumed correct
    because the code looked right.

    Guarded via `foundation/recursion_guard.py`: `guard_check()` is
    called FIRST, before any subprocess is created. If this call is
    itself running nested inside another `PROOF_OPERATION` (i.e. it was
    reached via the `foundation` child subprocess below, discovering and
    running this module's own real-repo tests), the check returns
    `BLOCKED_REPEAT` and this function returns immediately with a
    bounded, explicit "guard-blocked" result — no subprocess is spawned
    at all for the repeat entry, not merely a spawned child noticing
    later that it should stop.
    """
    guard = guard_check(PROOF_OPERATION)
    if not guard.is_safe():
        return 0, f"guard-blocked: {guard.reason}", False, 0

    subsystems = ("schema", "firewall", "kpm", "magl", "rpa", "taal", "foundation", "narrative")
    total = 0
    all_green = True
    spawn_env = guard_child_env(PROOF_OPERATION)
    for name in subsystems:
        subsystem_dir = repo_root / name
        if not subsystem_dir.is_dir():
            all_green = False
            continue
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", name, "-p", "test_*.py"],
                cwd=str(repo_root), capture_output=True, text=True,
                env=spawn_env, timeout=120,
            )
        except subprocess.TimeoutExpired:
            all_green = False
            continue
        match = _TESTS_RUN_PATTERN.search(proc.stderr)
        total += int(match.group(1)) if match else 0
        if proc.returncode != 0:
            all_green = False
    if total == 0:
        score = 0
    elif not all_green:
        score = min(4, total // 200)  # capped low: a failing suite is never high proof
    else:
        score = min(10, 2 + total // 150)
    justification = f"{total} tests, {'all green' if all_green else 'FAILURES PRESENT'}"
    return score, justification, all_green, total


def _dimension_sight(repo_root: Path) -> tuple[int, str, bool]:
    """Observability: Sentinel exists and its own pulse_sweep is clean,
    plus the secret scanner exists and is wired to publication_gate."""
    sentinel_exists = (repo_root / "foundation" / "sentinel.py").exists()
    scanner_exists = (repo_root / "foundation" / "secret_scanner.py").exists()
    clean = False
    if sentinel_exists:
        report = pulse_sweep(repo_root)
        clean = report.raw_finding_count == 0
    wired = False
    gate_path = repo_root / "foundation" / "publication_gate.py"
    scanner_path = repo_root / "foundation" / "secret_scanner.py"
    if gate_path.exists() and scanner_path.exists():
        gate_text = gate_path.read_text(errors="ignore")
        scanner_text = scanner_path.read_text(errors="ignore")
        wired = "secret_scan_evidence" in gate_text and "to_evidence_string" in scanner_text
    score = sum([3 if sentinel_exists else 0, 3 if clean else 0,
                 2 if scanner_exists else 0, 2 if wired else 0])
    justification = (
        f"sentinel={'present' if sentinel_exists else 'absent'}, "
        f"clean={'yes' if clean else 'no'}, scanner_wired={'yes' if wired else 'no'}"
    )
    return score, justification, clean


def _dimension_frontier(repo_root: Path) -> tuple[int, str]:
    """Capability-mapping quality: PARETO_FRONTIER.md's own structural
    completeness (Frontier Gate schema, Archive table), plus NEXT_MOVE.md
    and INTUITION.md as companion surfaces."""
    frontier_path = repo_root / "PARETO_FRONTIER.md"
    has_gate = has_archive = False
    if frontier_path.exists():
        text = frontier_path.read_text(errors="ignore")
        has_gate = "## Frontier Gate" in text
        has_archive = "## Archive (built)" in text
    next_move = (repo_root / "NEXT_MOVE.md").exists()
    intuition = (repo_root / "INTUITION.md").exists()
    score = sum([3 if frontier_path.exists() else 0, 2 if has_gate else 0,
                 2 if has_archive else 0, 2 if next_move else 0, 1 if intuition else 0])
    justification = (
        f"gate_schema={'yes' if has_gate else 'no'}, archive={'yes' if has_archive else 'no'}, "
        f"next_move={'yes' if next_move else 'no'}, intuition={'yes' if intuition else 'no'}"
    )
    return score, justification


def _dimension_orchestration(repo_root: Path) -> tuple[int, str, bool]:
    """Queue/worker/switch composition, including whether a REAL
    (non-test-double) worker has been proven through the loop end to
    end — that proof is what separates a wired seam from a demonstrated
    one."""
    files = {
        "queue": repo_root / "foundation" / "task_queue.py",
        "worker": repo_root / "foundation" / "layer0_worker.py",
        "adapter": repo_root / "foundation" / "queue_worker_adapter.py",
        "real_worker": repo_root / "foundation" / "sentinel_worker.py",
        "closed_loop_proof": repo_root / "foundation" / "tests" / "test_closed_loop_reality.py",
    }
    present = {k: p.exists() for k, p in files.items()}
    score = sum(2 for v in present.values() if v)
    proven_end_to_end = present["real_worker"] and present["closed_loop_proof"]
    justification = f"{sum(present.values())}/5 components present, end_to_end_proven={proven_end_to_end}"
    return score, justification, proven_end_to_end


def _dimension_memory(repo_root: Path) -> tuple[int, str]:
    """Durable handoff/compaction: Crystal (epistemic provenance),
    MEMORY_MAP.md (boot-load tier audit), recovery_handoff (queue
    interruption recovery)."""
    crystal = (repo_root / "foundation" / "crystal.py").exists()
    memory_map = (repo_root / "MEMORY_MAP.md").exists()
    task_queue_path = repo_root / "foundation" / "task_queue.py"
    recovery = task_queue_path.exists() and "recovery_handoff" in task_queue_path.read_text(errors="ignore")
    archive_table = False
    frontier_path = repo_root / "PARETO_FRONTIER.md"
    if frontier_path.exists():
        archive_table = "## Archive (built)" in frontier_path.read_text(errors="ignore")
    score = sum([3 if crystal else 0, 3 if memory_map else 0, 2 if recovery else 0,
                 2 if archive_table else 0])
    justification = (
        f"crystal={'yes' if crystal else 'no'}, memory_map={'yes' if memory_map else 'no'}, "
        f"recovery_handoff={'yes' if recovery else 'no'}"
    )
    return score, justification


def _dimension_reality(repo_root: Path) -> tuple[int, str, bool]:
    """Evidence <-> real-world validation: reality-yield ledger, Hell's
    Gate, publication gate, and a real zero-network-dependency check
    (the Obelisk Test), run fresh rather than cited from memory."""
    ledger = (repo_root / "foundation" / "reality_yield_ledger.py").exists()
    hells_gate = (repo_root / "foundation" / "hells_gate.py").exists()
    pub_gate = (repo_root / "foundation" / "publication_gate.py").exists()

    network_pattern = re.compile(
        r"^\s*(import requests|import boto3|import socket|from http\.client|import urllib\.request)",
        re.MULTILINE,
    )
    zero_network = True
    for path in _iter_py_files(repo_root):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        if network_pattern.search(text):
            zero_network = False
            break

    score = sum([2 if ledger else 0, 2 if hells_gate else 0, 2 if pub_gate else 0,
                 4 if zero_network else 0])
    justification = (
        f"ledger={'yes' if ledger else 'no'}, hells_gate={'yes' if hells_gate else 'no'}, "
        f"publication_gate={'yes' if pub_gate else 'no'}, zero_network_deps={'yes' if zero_network else 'no'}"
    )
    return score, justification, zero_network


def compute_tier(*, all_tests_green: bool, sight_clean: bool, orchestration_proven: bool,
                  zero_network: bool, iron_score: int) -> tuple[str, str]:
    """Explicit conjunction ladder, not an averaged score. Each rung
    requires every fact of the rungs below it plus its own new fact —
    a tier can never be reached by a high average carrying one weak
    dimension."""
    if not all_tests_green:
        return "T2", "core implementation exists but not all test suites are currently green"
    if not zero_network:
        return "T3", "all test suites green, but the zero-network-dependency property no longer holds"
    if not orchestration_proven:
        return "T3", "all suites green and zero-network holds, but no real worker has been proven through the queue<->worker loop end to end"
    if not sight_clean:
        return "T4", "orchestration proven end to end, but Sentinel currently reports open findings"
    if iron_score < 10:
        return "T5", "self-maintaining workflow proven (Sentinel clean, orchestration proven), but not every subsystem has a BUILD_REPORT.md"
    return "T6", "all suites green, zero-network holds, orchestration proven end to end, Sentinel clean, every subsystem documented — no external integration boundary (CI, publication) has been demonstrated, so T7 is not claimed"


@dataclass(frozen=True)
class Sigil:
    tier: str
    tier_reason: str
    iron: int
    lattice: int
    proof: int
    sight: int
    frontier: int
    orchestration: int
    memory: int
    reality: int
    justification: dict  # dimension name -> one-line evidence string
    all_tests_green: bool
    total_tests: int


def compute_sigil(repo_root: Path) -> Sigil:
    """The only public way to produce a Sigil. Always recomputes from
    real repository evidence — never accepts a caller-supplied score."""
    iron, iron_j = _dimension_iron(repo_root)
    lattice, lattice_j = _dimension_lattice(repo_root)
    proof, proof_j, all_green, total_tests = _dimension_proof(repo_root)
    sight, sight_j, sight_clean = _dimension_sight(repo_root)
    frontier, frontier_j = _dimension_frontier(repo_root)
    orchestration, orch_j, orch_proven = _dimension_orchestration(repo_root)
    memory, memory_j = _dimension_memory(repo_root)
    reality, reality_j, zero_network = _dimension_reality(repo_root)

    tier, tier_reason = compute_tier(
        all_tests_green=all_green, sight_clean=sight_clean,
        orchestration_proven=orch_proven, zero_network=zero_network, iron_score=iron,
    )

    return Sigil(
        tier=tier, tier_reason=tier_reason,
        iron=iron, lattice=lattice, proof=proof, sight=sight, frontier=frontier,
        orchestration=orchestration, memory=memory, reality=reality,
        justification={
            "iron": iron_j, "lattice": lattice_j, "proof": proof_j, "sight": sight_j,
            "frontier": frontier_j, "orchestration": orch_j, "memory": memory_j,
            "reality": reality_j,
        },
        all_tests_green=all_green, total_tests=total_tests,
    )


def format_sigil(sigil: Sigil) -> str:
    return (
        f"TIER:{sigil.tier} | IRON:{sigil.iron} | LATTICE:{sigil.lattice} | "
        f"PROOF:{sigil.proof} | SIGHT:{sigil.sight} | FRONTIER:{sigil.frontier} | "
        f"ORCH:{sigil.orchestration} | MEMORY:{sigil.memory} | REALITY:{sigil.reality}"
    )


@dataclass(frozen=True)
class SigilReconciliation:
    previous: Optional[Sigil]
    current: Sigil
    changed: bool
    changed_dimensions: tuple
    reason: str


def reconcile_sigil(repo_root: Path, previous: Optional[Sigil]) -> SigilReconciliation:
    """Recompute and compare against `previous` (pass None on first run).
    Never mutates anything — the caller decides whether/how to persist
    a changed sigil (e.g. rewriting SIGIL.md), matching every other
    read-only inspection module in this repository."""
    current = compute_sigil(repo_root)
    if previous is None:
        return SigilReconciliation(
            previous=None, current=current, changed=True,
            changed_dimensions=tuple(DIMENSION_NAMES) + ("tier",),
            reason="no previous sigil recorded",
        )
    changed_dims = tuple(
        name for name in DIMENSION_NAMES if getattr(previous, name) != getattr(current, name)
    )
    tier_changed = previous.tier != current.tier
    if tier_changed:
        changed_dims = changed_dims + ("tier",)
    changed = bool(changed_dims)
    reason = (
        "no threshold crossed — repository evidence unchanged" if not changed
        else f"changed dimensions: {', '.join(changed_dims)}"
    )
    return SigilReconciliation(
        previous=previous, current=current, changed=changed,
        changed_dimensions=changed_dims, reason=reason,
    )
