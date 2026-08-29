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
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

# Same convention as foundation/cron_pulse.py -- the one other script in
# this repository actually invoked as `python3 foundation/<name>.py`
# rather than `python3 -m foundation.<name>`. Reproduced directly before
# this fix: without this, plain script invocation failed at import time
# with `ModuleNotFoundError: No module named 'foundation'`, because
# Python only puts the SCRIPT's own directory on sys.path, not the repo
# root -- `-m` invocation works without this, but a bare script
# invocation (the form this file's own __main__ block is written for)
# does not.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from foundation.sentinel import pulse_sweep, count_real_tests  # noqa: E402

__all__ = [
    "AUTONOMY_STOP_FILENAME", "RECEIPT_LOG_NAME", "README_DRIFT_OBSERVATION",
    "CycleResult", "run_one_cycle", "run_loop",
    "AutonomyReceipts", "RECEIPTS_MAX_RECORDS", "read_autonomy_receipts",
]

RECEIPTS_MAX_RECORDS = 50

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


def _attempt_readme_fix(repo_root: Path) -> tuple[bool, str, Optional[str]]:
    """Narrow, verbatim string-replace only -- never a general rewrite.
    Returns (applied, detail, original_text). Refuses (applied=False)
    rather than guessing if the exact expected pattern isn't present, or
    if the computed replacement can't be determined.

    `original_text` is the file's exact prior contents when a write
    actually happened, so the caller can roll the working tree back if a
    later step fails. It is None when nothing was written."""
    readme = repo_root / "README.md"
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"could not read README.md: {exc}", None

    match = _README_COUNT_PATTERN.search(text)
    if match is None:
        return False, "expected README pattern not found verbatim", None

    new_count = count_real_tests(repo_root)
    new_subsystems = _subsystem_count(repo_root)
    if new_subsystems is None:
        return False, "could not determine subsystem count from tests.yml", None

    old_snippet = match.group(0)
    new_snippet = f"**{new_count:,} tests across {new_subsystems} subsystems"
    if old_snippet == new_snippet:
        return (False,
                "computed replacement identical to current text -- nothing to fix",
                None)

    new_text = text.replace(old_snippet, new_snippet, 1)
    try:
        readme.write_text(new_text, encoding="utf-8")
    except OSError as exc:
        return False, f"could not write README.md: {exc}", None
    return True, f"{old_snippet!r} -> {new_snippet!r}", text


def _rollback_readme(repo_root: Path, original_text: Optional[str]) -> bool:
    """Restore README.md to exactly its pre-fix contents.

    TRAJECTORY LAW (added 2026-08-29 after direct reproduction): a
    `STOPPED_*` result must mean the repository is as the cycle found it.
    Previously the fix was written to disk BEFORE verification, so any
    later failure returned a terminal state that reads as "nothing
    happened" while leaving a real mutation behind -- a safe-looking
    outcome concealing an unsafe trajectory.

    Restores by plain file write, deliberately NOT by `git checkout`/
    `restore`/`reset`. Those are destructive verbs outside this module's
    authorized envelope (see AUTHORIZED_GIT_VERBS in the tests); rolling
    back must not require widening the very capability set that keeps
    this loop bounded."""
    if original_text is None:
        return True
    try:
        (repo_root / "README.md").write_text(original_text, encoding="utf-8")
        return True
    except OSError:
        return False


def run_one_cycle(repo_root: Path) -> CycleResult:
    """One bounded unit of work. Never raises on ordinary drift/absence
    conditions -- every real failure mode is a `CycleResult`, not an
    exception, so `run_loop()` never needs its own except-clause around
    this call to stay receipted.

    EVERY outcome is receipted here, by the function that produces it.

    Previously only `run_loop()` wrote receipts, so a cycle invoked
    directly -- which is exactly what `.claude/commands/boot.md` step 4b
    routes an operator to do -- left no durable record. REPRODUCED
    2026-08-29: a cycle that wrote README.md, failed to commit, and
    correctly rolled back left HEAD unmoved, the tree byte-identical, and
    no log file. A real mutation was attempted and reverted with ZERO
    durable evidence anywhere that it had happened.

    That made two very different states indistinguishable to any later
    reader: "the loop never ran" and "the loop ran, attempted a repair,
    failed verification, and recovered". The second means the repair path
    is broken and needs a human; the first means nothing happened. Fifty
    silent failures looked identical to none.

    The rollback (the recovery half) was already correct. This closes the
    attribution half: an attempt that leaves no trace cannot be audited,
    counted, or noticed when it starts recurring."""
    result = _run_one_cycle_uncounted(repo_root)
    _append_receipt(repo_root / "foundation" / RECEIPT_LOG_NAME, result)
    return result


def _run_one_cycle_uncounted(repo_root: Path) -> CycleResult:
    """The decision logic itself. Split out so `run_one_cycle()` can
    guarantee exactly one receipt per cycle at a single point, rather
    than every early-return remembering to write one."""
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
        applied, detail, original = _attempt_readme_fix(repo_root)
        if not applied:
            return CycleResult("STOPPED_PATTERN_NOT_FOUND", detail, now)

        def _stopped(reason: str) -> CycleResult:
            """Every failure after the write rolls the tree back, so a
            STOPPED_* result always means "the repository is as I found
            it". If the rollback itself fails, say so in the receipt
            rather than reporting a clean stop that isn't one."""
            restored = _rollback_readme(repo_root, original)
            suffix = (
                " (README.md restored to its pre-fix contents)" if restored else
                " -- WARNING: rollback FAILED, README.md is left modified "
                "and requires human cleanup"
            )
            return CycleResult("STOPPED_FIX_VERIFICATION_FAILED", reason + suffix, now)

        post = pulse_sweep(repo_root)
        if post.findings:
            return _stopped(
                f"fix applied but pulse_sweep() still reports "
                f"{len(post.findings)} finding(s) -- the fix did not "
                f"actually clear the condition it targeted"
            )

        commit_msg = (
            "[autonomy-loop] README.md: correct test-count drift\n\n"
            f"{detail}\n\n"
            "Applied and verified by foundation/autonomy_loop.py -- "
            "local commit only, never pushed by this loop."
        )
        # Pathspec commit, deliberately WITHOUT a preceding `git add`:
        # committing the path directly leaves the index untouched when the
        # commit fails (a pre-commit hook, a GPG signing failure, a
        # concurrent index.lock). The previous `add`-then-`commit` shape
        # left the change STAGED on failure, where a human's next
        # unrelated `git commit` would silently absorb it into their own
        # authorship. Reproduced directly before this change.
        commit = _git(repo_root, "commit", "-m", commit_msg, "--", "README.md")
        if commit.returncode != 0:
            return _stopped(f"git commit failed: {commit.stderr.strip()}")
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
        # No _append_receipt here: run_one_cycle() now writes its own
        # receipt, so doing it again would double-log every cycle. The
        # mid-sleep kill-switch below is NOT produced by run_one_cycle(),
        # so that one still records itself.
        result = run_one_cycle(repo_root)
        results.append(result)
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


@dataclass(frozen=True)
class AutonomyReceipts:
    """Bounded, read-only view of what the actuator actually did.

    WHY THIS EXISTS. Three sibling machine-local runtime logs each have a
    reader routed into `.claude/commands/boot.md`
    (`read_pulse_continuity`, `read_cron_stderr`,
    `read_dependency_pressure_log`). `autonomy_loop_log.jsonl` had none:
    it was written and never read anywhere outside its own tests. The
    receipts existed; no decision could reach them.

    THE DECISION THIS SERVES is `HUMAN_DECISIONS.md` item 14 -- should
    this loop run unattended on a schedule? That is a sandbox-to-
    production move, and it was being weighed with no failure-rate
    evidence at all, because the only record of a failed-and-recovered
    attempt is this log (a correct rollback leaves git byte-identical).

    `attempted_and_recovered` is the number this exists for: cycles that
    really wrote to disk and rolled back. Git cannot show them by
    construction, so before this reader they were unreachable.

    Reporting only. A `Finding`-style rule applies: these counts are
    evidence to weigh, never an authorization to schedule anything.
    Nothing here decides; item 14 remains a human decision.
    """

    available: bool
    records_considered: int
    latest_timestamp: Optional[str]
    outcome_counts: dict
    fixes_applied: int
    attempted_and_recovered: int
    consecutive_stops_at_tail: int
    failure_rate_upper_bound_95: Optional[float]
    warnings: tuple
    source: str

    def evidence_is_sufficient_for(self, target_failure_rate: float) -> bool:
        """Would this observation window support a claim that the true
        failure rate is below `target_failure_rate`?

        This is the guard against the exact misreading this dataclass
        invites. `attempted_and_recovered == 0` reads as "no failures,
        looks reliable"; it is not. With n observations and zero
        failures, the 95% upper bound on the true failure rate is 3/n
        (the statistical rule of three), which is large until n is large.

        Returns False when the bound is unknown (no observations), so
        absence of data can never satisfy a reliability claim."""
        if self.failure_rate_upper_bound_95 is None:
            return False
        return self.failure_rate_upper_bound_95 < target_failure_rate


def read_autonomy_receipts(
    repo_root: Path,
    max_records: int = RECEIPTS_MAX_RECORDS,
) -> AutonomyReceipts:
    """Summarise the tail of `foundation/autonomy_loop_log.jsonl`.

    Read-only -- never writes, truncates, or rotates the log. Bounded --
    reads at most `max_records` trailing lines regardless of file size.
    Fails soft at every layer: a missing file, an empty file, a malformed
    JSON line, a valid-JSON-but-not-an-object line, and a record with an
    unrecognised action are all reported in `warnings`, never raised.
    Same contract as `sentinel.read_pulse_continuity()`, deliberately --
    a boot sequence must not fail because the loop has never run here or
    because one line was cut mid-write.

    An absent log means "this actuator has never run on this machine",
    which is the honest state for a fresh clone -- the log is gitignored
    machine-local runtime state, not source.
    """
    log_path = repo_root / "foundation" / RECEIPT_LOG_NAME
    source = str(log_path)
    empty_counts: dict = {}

    if not log_path.exists():
        return AutonomyReceipts(
            available=False, records_considered=0, latest_timestamp=None,
            outcome_counts=empty_counts, fixes_applied=0,
            attempted_and_recovered=0, consecutive_stops_at_tail=0,
            failure_rate_upper_bound_95=None,
            warnings=(
                f"{RECEIPT_LOG_NAME} does not exist -- this actuator has "
                f"never run in this working copy",
            ),
            source=source,
        )

    try:
        raw = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return AutonomyReceipts(
            available=False, records_considered=0, latest_timestamp=None,
            outcome_counts=empty_counts, fixes_applied=0,
            attempted_and_recovered=0, consecutive_stops_at_tail=0,
            failure_rate_upper_bound_95=None,
            warnings=(f"could not read {RECEIPT_LOG_NAME}: {exc}",),
            source=source,
        )

    lines = [ln for ln in raw.splitlines() if ln.strip()]
    tail = lines[-max_records:] if max_records > 0 else []

    records: list = []
    warnings: list = []
    for line in tail:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            warnings.append(f"skipped malformed JSON line: {exc}")
            continue
        # Same class of hole already found once in read_pulse_continuity:
        # a line can be valid JSON without being a record (a bare number
        # or string from a truncated write). .get() on that would crash
        # the reader, and this reader is meant to be safe at boot.
        if not isinstance(obj, dict):
            warnings.append(f"skipped non-record JSON line: {obj!r}"[:200])
            continue
        action = obj.get("action")
        if action not in _ACTIONS:
            warnings.append(f"skipped record with unrecognised action: {action!r}"[:200])
            continue
        records.append(obj)

    if not records:
        return AutonomyReceipts(
            available=True, records_considered=0, latest_timestamp=None,
            outcome_counts=empty_counts, fixes_applied=0,
            attempted_and_recovered=0, consecutive_stops_at_tail=0,
            failure_rate_upper_bound_95=None,
            warnings=tuple(warnings) or ("no usable records in the bounded window",),
            source=source,
        )

    counts: dict = {}
    for rec in records:
        counts[rec["action"]] = counts.get(rec["action"], 0) + 1

    # A cycle that wrote to disk and rolled back. Identified by its
    # action AND the rollback marker run_one_cycle() puts in the detail,
    # so a verification failure that never reached the write stage is not
    # miscounted as a recovered mutation.
    recovered = sum(
        1 for rec in records
        if rec["action"] == "STOPPED_FIX_VERIFICATION_FAILED"
        and "restored" in str(rec.get("detail", ""))
    )

    trailing_stops = 0
    for rec in reversed(records):
        if str(rec["action"]).startswith("STOPPED_"):
            trailing_stops += 1
        else:
            break

    # Statistical rule of three: with n observations and zero observed
    # failures, the 95% upper bound on the true failure rate is 3/n.
    # Computed HERE rather than left to each caller, so the count and its
    # confidence bound cannot become separated -- a bare
    # "attempted_and_recovered: 0" is exactly the number a reader would
    # over-trust. When failures HAVE been observed the rule does not
    # apply, so the bound is None and the raw counts stand on their own.
    if recovered == 0 and len(records) > 0:
        upper_bound: Optional[float] = 3.0 / len(records)
    else:
        upper_bound = None

    return AutonomyReceipts(
        available=True,
        records_considered=len(records),
        latest_timestamp=records[-1].get("occurred_at"),
        outcome_counts=counts,
        fixes_applied=counts.get("FIXED_README_DRIFT", 0),
        attempted_and_recovered=recovered,
        consecutive_stops_at_tail=trailing_stops,
        failure_rate_upper_bound_95=upper_bound,
        warnings=tuple(warnings),
        source=source,
    )


if __name__ == "__main__":
    print(f"autonomy_loop starting against {REPO_ROOT}; drop "
          f"{REPO_ROOT / AUTONOMY_STOP_FILENAME} to stop it at the next "
          f"cycle boundary or during sleep.", file=sys.stderr)
    run_loop(REPO_ROOT)
