"""
Minimum viable local autonomy envelope. Built 2026-08-29 per Kyle's
explicit authorization (ALIEN4814/Omega Autonomy Prosecution cycle):
real, running, local-commit-capable, no fixed time budget, stop = a
kill-switch file + fail-closed on anything unexpected. Confirmed via
AskUserQuestion before any code was written, not inferred from prompt
styling alone.

SCOPE, DELIBERATELY NARROW

This is not a general autonomous engineer. It has exactly ONE
authorized action: fix `README.md`'s test-count/subsystem-count drift
-- the one finding class in this repository that is deterministic,
mechanically verifiable, and already proven correct by
`check_readme_test_count()` itself (see that function's own docstring:
this exact drift has already been hand-corrected at least twice in
this repository's real history). Any other finding, or any finding
alongside this one, halts the loop for human review rather than
attempting a fix outside the authorized envelope.

Reuses `pulse_sweep()`/`check_readme_test_count()`/`count_real_tests()`
for sensing and plain `git` for materialization. No new sensor, no new
candidate-selection framework, no ATP/gem vocabulary, no wiring into
`HuntSurface`/`evaluate_continuation()` -- the candidate universe here
is a singleton (one authorized action or none), so the governor's
evidence-gated multi-candidate machinery would be ceremony, not
function; using it would not change this loop's actual behaviour.

FAIL-CLOSED LAW

If the working tree is not clean at cycle start, if more than one
class of finding exists, if the fix does not verifiably clear the
finding it targeted, or if the exact expected README text pattern is
not found verbatim -- the loop stops entirely and requires a human. It
never guesses, never retries blindly, and never widens its own
authorized-action set.

KILL SWITCH

`<repo_root>/.autonomy_stop` -- checked before every cycle and during
every sleep interval, in short slices, so dropping the file stops the
loop within one slice even while backgrounded.

NEVER: push, network access, credential use, deletion of durable
history, self-expansion of this file's own authorized-action set.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from foundation.sentinel import pulse_sweep, count_real_tests

__all__ = [
    "AUTONOMY_STOP_FILENAME", "RECEIPT_LOG_NAME", "README_DRIFT_OBSERVATION",
    "CycleResult", "run_one_cycle", "run_loop",
]

AUTONOMY_STOP_FILENAME = ".autonomy_stop"
RECEIPT_LOG_NAME = "autonomy_loop_log.jsonl"

# Must match check_readme_test_count()'s own stable observation text
# exactly -- this is how the loop recognizes "the one authorized
# finding" without re-parsing prose or duplicating sentinel.py's
# private regex.
README_DRIFT_OBSERVATION = (
    "README.md's declared test count disagrees with a real count of `def test_`"
)

_README_COUNT_PATTERN = re.compile(r"\*\*([\d,]+) tests across (\d+) subsystems")

_ACTIONS = frozenset({
    "CLEAN_IDLE",
    "FIXED_README_DRIFT",
    "STOPPED_KILL_SWITCH",
    "STOPPED_DIRTY_TREE",
    "STOPPED_UNEXPECTED_FINDINGS",
    "STOPPED_PATTERN_NOT_FOUND",
    "STOPPED_FIX_VERIFICATION_FAILED",
})


@dataclass(frozen=True)
class CycleResult:
    """One cycle's outcome. Every field is receipted verbatim to
    `autonomy_loop_log.jsonl` -- this dataclass IS the receipt shape."""

    action: str
    detail: str
    occurred_at: str

    def __post_init__(self) -> None:
        if self.action not in _ACTIONS:
            raise ValueError(f"unknown CycleResult action {self.action!r}")

    def is_stop(self) -> bool:
        return self.action.startswith("STOPPED_")


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True,
    )


def _is_clean(repo_root: Path) -> bool:
    result = _git(repo_root, "status", "--porcelain")
    return result.returncode == 0 and result.stdout.strip() == ""


def _subsystem_count(repo_root: Path) -> Optional[int]:
    """Read the CI matrix's declared subsystem count -- same source of
    truth `check_ci_matrix_coverage()` already reads. Returns None if
    unreadable; the caller fails closed on that."""
    workflow = repo_root / ".github" / "workflows" / "tests.yml"
    if not workflow.exists():
        return None
    try:
        doc = yaml.safe_load(workflow.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    matrix = (
        doc.get("jobs", {}).get("test", {}).get("strategy", {})
        .get("matrix", {}).get("subsystem", [])
    )
    return len(matrix) if isinstance(matrix, list) else None


def _attempt_readme_fix(repo_root: Path) -> tuple[bool, str]:
    """Narrow, verbatim string-replace only -- never a general rewrite.
    Returns (applied, detail). Refuses (applied=False) rather than
    guessing if the exact expected pattern isn't present, or if the
    computed replacement can't be determined."""
    readme = repo_root / "README.md"
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"could not read README.md: {exc}"

    match = _README_COUNT_PATTERN.search(text)
    if match is None:
        return False, "expected README pattern not found verbatim"

    new_count = count_real_tests(repo_root)
    new_subsystems = _subsystem_count(repo_root)
    if new_subsystems is None:
        return False, "could not determine subsystem count from tests.yml"

    old_snippet = match.group(0)
    new_snippet = f"**{new_count:,} tests across {new_subsystems} subsystems"
    if old_snippet == new_snippet:
        return False, "computed replacement identical to current text -- nothing to fix"

    new_text = text.replace(old_snippet, new_snippet, 1)
    try:
        readme.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        return False, f"could not write README.md: {exc}"
    return True, f"{old_snippet!r} -> {new_snippet!r}"


def run_one_cycle(repo_root: Path) -> CycleResult:
    """One bounded unit of work. Never raises on ordinary drift/absence
    conditions -- every real failure mode is a `CycleResult`, not an
    exception, so `run_loop()` never needs its own except-clause around
    this call to stay receipted."""
    now = datetime.now(timezone.utc).isoformat()
    stop_file = repo_root / AUTONOMY_STOP_FILENAME

    if stop_file.exists():
        return CycleResult("STOPPED_KILL_SWITCH", f"{stop_file} present", now)

    if not _is_clean(repo_root):
        return CycleResult(
            "STOPPED_DIRTY_TREE",
            "working tree not clean at cycle start -- ambiguous state, "
            "human must intervene before this loop will act again",
            now,
        )

    report = pulse_sweep(repo_root)
    findings = report.findings

    if not findings:
        return CycleResult("CLEAN_IDLE", "pulse_sweep() clean, nothing to do", now)

    if len(findings) == 1 and findings[0].observation == README_DRIFT_OBSERVATION:
        applied, detail = _attempt_readme_fix(repo_root)
        if not applied:
            return CycleResult("STOPPED_PATTERN_NOT_FOUND", detail, now)

        post = pulse_sweep(repo_root)
        if post.findings:
            return CycleResult(
                "STOPPED_FIX_VERIFICATION_FAILED",
                f"fix applied but pulse_sweep() still reports "
                f"{len(post.findings)} finding(s) -- the fix did not "
                f"actually clear the condition it targeted",
                now,
            )

        add = _git(repo_root, "add", "README.md")
        if add.returncode != 0:
            return CycleResult(
                "STOPPED_FIX_VERIFICATION_FAILED", f"git add failed: {add.stderr}", now,
            )
        commit_msg = (
            "[autonomy-loop] README.md: correct test-count drift\n\n"
            f"{detail}\n\n"
            "Applied and verified by foundation/autonomy_loop.py -- "
            "local commit only, never pushed by this loop."
        )
        commit = _git(repo_root, "commit", "-m", commit_msg)
        if commit.returncode != 0:
            return CycleResult(
                "STOPPED_FIX_VERIFICATION_FAILED",
                f"git commit failed: {commit.stderr}", now,
            )
        return CycleResult("FIXED_README_DRIFT", detail, now)

    return CycleResult(
        "STOPPED_UNEXPECTED_FINDINGS",
        f"{len(findings)} finding(s) outside the authorized envelope: "
        + "; ".join(f.observation for f in findings),
        now,
    )


def _append_receipt(log_path: Path, result: CycleResult) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "action": result.action,
                "detail": result.detail,
                "occurred_at": result.occurred_at,
            }) + "\n")
    except OSError:
        pass  # a logging failure must never crash or silently continue the loop wrong


def run_loop(
    repo_root: Path,
    *,
    sleep_seconds: int = 300,
    sleep_slice_seconds: int = 5,
    max_cycles: Optional[int] = None,
) -> list[CycleResult]:
    """Runs cycles until a STOPPED_* result, the kill switch fires
    (including mid-sleep), or `max_cycles` is reached. `max_cycles` is a
    TEST HOOK ONLY -- omit it for a real run; the architect-authorized
    contract is "runs until manually stopped," not a fixed budget.

    Every CLEAN_IDLE / FIXED_README_DRIFT cycle sleeps in short slices
    (checking the kill switch each slice) before the next cycle -- this
    is what makes the loop responsive to a dropped `.autonomy_stop` file
    even while backgrounded, and prevents busy-looping.
    """
    stop_file = repo_root / AUTONOMY_STOP_FILENAME
    log_path = repo_root / "foundation" / RECEIPT_LOG_NAME
    results: list[CycleResult] = []
    cycles = 0

    while max_cycles is None or cycles < max_cycles:
        result = run_one_cycle(repo_root)
        results.append(result)
        _append_receipt(log_path, result)
        cycles += 1

        if result.is_stop():
            break

        elapsed = 0
        while elapsed < sleep_seconds:
            if stop_file.exists():
                kill = CycleResult(
                    "STOPPED_KILL_SWITCH",
                    f"{stop_file} present (during sleep)",
                    datetime.now(timezone.utc).isoformat(),
                )
                results.append(kill)
                _append_receipt(log_path, kill)
                return results
            slice_len = min(sleep_slice_seconds, sleep_seconds - elapsed)
            if slice_len > 0:
                time.sleep(slice_len)
            elapsed += sleep_slice_seconds

    return results


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parents[1]
    print(f"autonomy_loop starting against {root}; drop {root / AUTONOMY_STOP_FILENAME} "
          f"to stop it at the next cycle boundary or during sleep.", file=sys.stderr)
    run_loop(root)
