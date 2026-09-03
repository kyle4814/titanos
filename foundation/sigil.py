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

from foundation.sentinel import (
    SUBSYSTEMS_REQUIRING_BUILD_REPORT, has_substantive_build_report, pulse_sweep,
)
from foundation.recursion_guard import GuardDecision, check as guard_check, child_env as guard_child_env

__all__ = [
    "Sigil", "SigilReconciliation", "compute_sigil", "reconcile_sigil", "format_sigil",
    "RecordedSigil", "parse_sigil", "read_recorded_sigil", "RECORDED_SIGIL_PATTERN",
    "PROOF_OPERATION",
    "PROOF_SUBSYSTEM_TIMEOUT_SECONDS",
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
_EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", "tests",
                  "corpus", "build", "dist"}


def _iter_py_files(repo_root: Path):
    for path in repo_root.rglob("*.py"):
        if any(part in _EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def _defines(module_path: Path, *symbols: str) -> bool:
    """True only if `module_path` exists AND actually defines every named
    symbol at module level.

    WHY THIS EXISTS (reproduced defect, not a hypothetical)

    Every capability dimension below used to award its points on bare
    `Path.exists()`. That is not "derived from a concrete, inspectable
    fact" in the sense `TITANOS_SIGIL_CAPABILITY_INDEX.md` requires --
    file existence is effectively caller-suppliable. REPRODUCED
    2026-08-29: a scratch directory containing six EMPTY files with the
    right names, plus two trivial marker strings, scored
    `ORCH:10 | MEMORY:10` -- byte-identical to the real repository's own
    score for those dimensions.

    This does not attempt to prove the symbol WORKS -- that is PROOF's
    job, and PROOF genuinely runs the test suites. It closes the far
    cheaper hole: a named capability scoring full marks while the module
    behind it is empty, gutted, or truncated (a partial checkout, a
    failed clone, or a refactor that emptied a module all produce this
    honestly, without anyone acting maliciously).

    Deliberately NOT applied to markdown documents (`MEMORY_MAP.md`,
    `PARETO_FRONTIER.md`, `BUILD_REPORT.md`): for those, existence
    genuinely IS the signal being scored -- there is no equivalent
    "defines a symbol" notion, and inventing a required-heading check
    would be a different claim than the one those dimensions make.
    """
    if not module_path.exists():
        return False
    try:
        text = module_path.read_text(errors="ignore")
    except OSError:
        return False
    # A symbol ending in "_" is a deliberate PREFIX match (e.g. "test_"
    # means "defines at least one test function"). A word boundary would
    # never fire there -- "_" is itself a word character, so `test_\b`
    # cannot match `def test_foo`.
    # Leading indentation is allowed: a test function is a method inside
    # a TestCase class, so anchoring hard at column 0 would have reported
    # a fully-populated test file as empty. Caught 2026-08-29 by running
    # this helper against the real repository and seeing ORCH drop 10->8
    # -- the two-sided check (real repo must NOT change, fake must
    # collapse) is what surfaced it.
    return all(
        re.search(
            rf"^[ \t]*(?:async +)?(?:def|class) +{re.escape(s)}"
            + ("" if s.endswith("_") else r"\b"),
            text, re.MULTILINE,
        )
        for s in symbols
    )


def _dimension_iron(repo_root: Path) -> tuple[int, str]:
    """Durable code foundation: subsystems with a real BUILD_REPORT.md
    audit trail (`sentinel.py`'s own fixed list, not re-derived here)."""
    # Reuses sentinel's own predicate rather than a second copy of the
    # rule -- these two surfaces scoring the same claim by different
    # standards is exactly how the hollow-BUILD_REPORT.md gap survived.
    present = sum(
        1 for name in SUBSYSTEMS_REQUIRING_BUILD_REPORT
        if has_substantive_build_report(repo_root / name)
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


# HOW LONG A SUBSYSTEM'S SUITE MAY TAKE BEFORE THIS GIVES UP ON IT.
#
# This was 120 seconds, and on 2026-09-04 the `foundation` child suite
# measured 128.8 SECONDS -- seven percent over the limit. The suite had
# grown past it during the session that measured it.
#
# The consequence was not a clean failure. A TimeoutExpired sets
# all_green=False, which caps PROOF at `min(4, total // 200)` instead of
# the green formula, which fails `run_all_tests.sh`'s foundation suite.
# So the whole-repository gate passed or failed according to how loaded
# the machine happened to be. It failed twice and passed four times in
# one evening on identical code, which reads as flakiness rather than as
# the deterministic cliff it actually is.
#
# 600 is not a guess at a safe margin: it is roughly 4.5x the measured
# duration, chosen so ordinary growth does not silently re-cross the
# line. Raising it is safe because the timeout is the SECOND safety net
# here, not the first -- `recursion_guard.check()` structurally prevents
# the unbounded forking this timeout was originally added to backstop
# (see TITANOS_RECURSION_GUARD_001.md). A timeout is a blunt instrument
# against a bug that now has a precise control.
PROOF_SUBSYSTEM_TIMEOUT_SECONDS = 600

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

    # Reuses _dimension_iron()'s constant instead of a second hardcoded
    # copy. `legacy` is deliberately NOT in this list — that's an
    # already-considered, not-yet-earned policy call (does it count as
    # a formal subsystem for IRON/PROOF scoring), not an oversight. Add
    # it to SUBSYSTEMS_REQUIRING_BUILD_REPORT only if that call changes.
    subsystems = SUBSYSTEMS_REQUIRING_BUILD_REPORT
    total = 0
    all_green = True
    timed_out: list[str] = []
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
                env=spawn_env, timeout=PROOF_SUBSYSTEM_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            # A TIMEOUT IS NOT A TEST FAILURE, and collapsing the two
            # was the deeper defect. Both produced all_green=False and
            # an identically degraded score, so a suite that was merely
            # slow reported as a suite that was broken -- a confident
            # verdict computed over a machine-load artefact. Recorded
            # separately so the justification can say which happened.
            timed_out.append(name)
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
    if all_green:
        state = "all green"
    elif timed_out:
        # Names the timed-out subsystems explicitly. "FAILURES PRESENT"
        # on a suite that merely ran long sends the next reader hunting
        # for a broken test that does not exist.
        state = (f"TIMED OUT after {PROOF_SUBSYSTEM_TIMEOUT_SECONDS}s: "
                 f"{', '.join(timed_out)} (not a test failure)")
    else:
        state = "FAILURES PRESENT"
    justification = f"{total} tests, {state}"
    return score, justification, all_green, total


def _dimension_sight(repo_root: Path) -> tuple[int, str, bool]:
    """Observability: Sentinel exists and its own pulse_sweep is clean,
    plus the secret scanner exists and is wired to publication_gate."""
    sentinel_exists = _defines(
        repo_root / "foundation" / "sentinel.py", "pulse_sweep", "Finding")
    scanner_exists = _defines(
        repo_root / "foundation" / "secret_scanner.py", "scan", "ScanReport")
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
        "queue": (repo_root / "foundation" / "task_queue.py", ("TaskQueue", "Task")),
        "worker": (repo_root / "foundation" / "layer0_worker.py", ("should_halt", "CycleRecord")),
        "adapter": (repo_root / "foundation" / "queue_worker_adapter.py",
                    ("make_worker_perform", "make_worker_verify")),
        "real_worker": (repo_root / "foundation" / "sentinel_worker.py", ("SentinelSweepWorker",)),
        # A test file's capability claim is that it defines real test
        # functions -- an empty file named test_closed_loop_reality.py
        # proves nothing, which is exactly the hole this closes.
        "closed_loop_proof": (repo_root / "foundation" / "tests" / "test_closed_loop_reality.py",
                              ("test_",)),
    }
    present = {k: _defines(p, *syms) for k, (p, syms) in files.items()}
    score = sum(2 for v in present.values() if v)
    proven_end_to_end = present["real_worker"] and present["closed_loop_proof"]
    justification = f"{sum(present.values())}/5 components present, end_to_end_proven={proven_end_to_end}"
    return score, justification, proven_end_to_end


def _dimension_memory(repo_root: Path) -> tuple[int, str]:
    """Durable handoff/compaction: Crystal (epistemic provenance),
    MEMORY_MAP.md (boot-load tier audit), recovery_handoff (queue
    interruption recovery)."""
    crystal = _defines(
        repo_root / "foundation" / "crystal.py", "Crystal", "CrystalStore")
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
    ledger = _defines(
        repo_root / "foundation" / "reality_yield_ledger.py",
        "YieldComponent", "LedgerEntry")
    hells_gate = _defines(
        repo_root / "foundation" / "hells_gate.py",
        "HellsGateArtifact", "HellsGateDecision")
    pub_gate = _defines(
        repo_root / "foundation" / "publication_gate.py",
        "PublicationSwitch", "PublicationDecision")

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


def _dimension_external_integration(repo_root: Path) -> tuple[bool, str]:
    """T7's one new fact: has a real external integration boundary
    actually been demonstrated (not just built)?

    LOCAL EVIDENCE ONLY -- DELIBERATELY NO LIVE NETWORK CALL.

    Checking this by actually calling the GitHub API would contradict
    the very zero-network-dependency property `_dimension_reality()`
    exists to certify -- a sigil computation that itself makes a
    network call could never honestly claim the Obelisk Test still
    passes. Instead this checks two purely local, offline facts:

      1. `.git/config` has a `[remote "origin"]` section with a
         non-empty URL -- real local git state, not a network probe.
      2. A durable, committed record in the repository itself
         (`FIRST_PING.md`) documents an actual observed external
         result -- a GitHub Actions run reference alongside a recorded
         success/conclusion, not merely the workflow file's existence
         (which only proves CI was configured, not that it ever ran).

    Both together distinguish "a remote is wired and CI might work"
    from "a real external system was actually exercised and a human or
    session recorded what it returned" -- the same evidence-over-claim
    discipline `foundation/publication_gate.py` already holds.
    """
    git_config = repo_root / ".git" / "config"
    remote_configured = False
    if git_config.exists():
        try:
            text = git_config.read_text(errors="ignore")
        except OSError:
            text = ""
        if re.search(r'\[remote "origin"\]\s*\n\s*url\s*=\s*\S+', text):
            remote_configured = True

    first_ping = repo_root / "FIRST_PING.md"
    real_run_recorded = False
    if first_ping.exists():
        try:
            text = first_ping.read_text(errors="ignore")
        except OSError:
            text = ""
        has_run_ref = re.search(r"github\.com/\S+/actions/runs/\d+", text) is not None
        has_success = re.search(r"conclusion\s*[=:]\s*[`\"']?success", text) is not None
        real_run_recorded = has_run_ref and has_success

    proven = remote_configured and real_run_recorded
    justification = (
        f"remote_configured={'yes' if remote_configured else 'no'}, "
        f"real_run_recorded_locally={'yes' if real_run_recorded else 'no'}"
    )
    return proven, justification


def compute_tier(*, all_tests_green: bool, sight_clean: bool, orchestration_proven: bool,
                  zero_network: bool, iron_score: int,
                  external_integration_proven: bool = False) -> tuple[str, str]:
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
    if not external_integration_proven:
        return "T6", "all suites green, zero-network holds, orchestration proven end to end, Sentinel clean, every subsystem documented — no external integration boundary (CI, publication) has been demonstrated, so T7 is not claimed"
    return "T7", "everything T6 requires, plus a real external integration boundary actually demonstrated (remote configured, and a real recorded external run result — not just the workflow file's existence)"


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
    external_integration_proven, external_j = _dimension_external_integration(repo_root)

    tier, tier_reason = compute_tier(
        all_tests_green=all_green, sight_clean=sight_clean,
        orchestration_proven=orch_proven, zero_network=zero_network, iron_score=iron,
        external_integration_proven=external_integration_proven,
    )

    return Sigil(
        tier=tier, tier_reason=tier_reason,
        iron=iron, lattice=lattice, proof=proof, sight=sight, frontier=frontier,
        orchestration=orchestration, memory=memory, reality=reality,
        justification={
            "iron": iron_j, "lattice": lattice_j, "proof": proof_j, "sight": sight_j,
            "frontier": frontier_j, "orchestration": orch_j, "memory": memory_j,
            "reality": reality_j, "external_integration": external_j,
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


# --------------------------------------------------------------------------
# READING BACK THE RECORDED SIGIL
#
# THE EXACT OPEN EDGE THIS CLOSES (traced and reproduced 2026-08-28):
# `format_sigil()` writes the canonical one-line snapshot, and `SIGIL.md`
# durably stores it. `reconcile_sigil(repo_root, previous)` is the
# designated consumer of that snapshot -- and three separate real
# documents instruct a session to use it:
#
#   SIGIL.md              "Run reconcile_sigil(repo_root, previous) after
#                          any cycle that changes capability"
#   .claude/commands/boot.md  "re-run compute_sigil() rather than trusting
#                          a stale snapshot if it's been a while"
#   CLAUDE.md             "two layers of caching one real value -- do not
#                          trust either without re-running compute_sigil()"
#
# But nothing could turn the stored line back into an object, so
# `previous` was obtainable only by a human hand-retyping nine values.
# A `format_*` with no matching parser and a real designated reader is
# the same open-retrieval shape already found and closed twice on the
# pulse/dependency-pressure circuits.
#
# THE CONSEQUENCE IS NOT HYPOTHETICAL -- it has already happened twice in
# this repository, both caught by a human eyeballing prose rather than by
# the reconciliation mechanism that exists for exactly this:
#   * CLAUDE.md carried "TIER:T7 ... REALITY:10" long after the real value
#     had dropped to T3/REALITY:6 (the network mouth was added).
#   * SIGIL.md's own evidence table still claims "1212 tests" against a
#     real current count of ~1527.
#
# WHY THIS RETURNS A DIFFERENT TYPE THAN `Sigil`
#
# `compute_sigil()` is documented as "the only public way to produce a
# Sigil -- never accepts a caller-supplied score," and that invariant is
# load-bearing: a hand-edited markdown file must never become something a
# caller can mistake for measured capability. So parsing yields a
# `RecordedSigil`, not a `Sigil`. It carries exactly the nine fields
# `reconcile_sigil()` actually compares (the eight DIMENSION_NAMES plus
# `tier`), so it works as `previous` by structure, and it is impossible
# to pass off as a computed one -- `isinstance(parsed, Sigil)` is False,
# checked by test. Everything `format_sigil()` does not encode
# (tier_reason, per-dimension justification, all_tests_green,
# total_tests) is genuinely unrecoverable from the snapshot and is not
# invented here.
# --------------------------------------------------------------------------

RECORDED_SIGIL_PATTERN = re.compile(
    r"TIER:\s*(?P<tier>T\d+)\s*\|\s*IRON:\s*(?P<iron>\d+)\s*\|\s*"
    r"LATTICE:\s*(?P<lattice>\d+)\s*\|\s*PROOF:\s*(?P<proof>\d+)\s*\|\s*"
    r"SIGHT:\s*(?P<sight>\d+)\s*\|\s*FRONTIER:\s*(?P<frontier>\d+)\s*\|\s*"
    r"ORCH:\s*(?P<orchestration>\d+)\s*\|\s*MEMORY:\s*(?P<memory>\d+)\s*\|\s*"
    r"REALITY:\s*(?P<reality>\d+)"
)


@dataclass(frozen=True)
class RecordedSigil:
    """A previously-recorded sigil snapshot, parsed from text.

    Deliberately NOT a `Sigil`: a Sigil is measured evidence produced only
    by `compute_sigil()`, while this is whatever a markdown file happens
    to say. It exists to be passed as `reconcile_sigil()`'s `previous`
    argument -- the one place a historical, possibly-stale, possibly
    hand-edited value legitimately belongs, because reconcile always
    recomputes `current` itself and never trusts `previous` as truth.
    """

    tier: str
    iron: int
    lattice: int
    proof: int
    sight: int
    frontier: int
    orchestration: int
    memory: int
    reality: int
    source: str


def parse_sigil(text: str, source: str = "<string>") -> Optional[RecordedSigil]:
    """Recover a RecordedSigil from `format_sigil()` output embedded in
    arbitrary text. Returns None if no sigil line is present -- an absent
    snapshot is a valid state (nothing has ever been recorded), not an
    error. The first match wins, matching this repository's existing
    first-occurrence-wins convention (`consolidate()`)."""
    match = RECORDED_SIGIL_PATTERN.search(text)
    if match is None:
        return None
    fields = match.groupdict()
    return RecordedSigil(
        tier=fields["tier"],
        source=source,
        **{name: int(fields[name]) for name in DIMENSION_NAMES},
    )


def read_recorded_sigil(repo_root: Path) -> Optional[RecordedSigil]:
    """Read `SIGIL.md`'s recorded snapshot. Read-only, fails soft: a
    missing or unreadable file returns None (nothing recorded yet), never
    raises -- a boot sequence must not break because a snapshot is absent.

    Cheap by design: no subprocess, no test run. Getting the recorded
    value is now free; `reconcile_sigil()` remains the expensive step
    that actually measures reality, and stays a deliberate decision."""
    path = repo_root / "SIGIL.md"
    try:
        text = path.read_text()
    except OSError:
        return None
    return parse_sigil(text, source=str(path))
