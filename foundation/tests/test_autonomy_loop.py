import ast
import json
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from foundation import autonomy_loop
from foundation.autonomy_loop import (
    AUTONOMY_STOP_FILENAME,
    RECEIPT_LOG_NAME,
    read_autonomy_receipts,
    CycleResult,
    run_loop,
    run_one_cycle,
)

# The complete set of git verbs this module is permitted to reach.
# `status` reads; `commit` writes LOCALLY via pathspec. Anything that
# publishes (push), rewrites history (reset/rebase/filter-branch),
# destroys work (clean/checkout/restore), or reaches the network
# (fetch/pull/remote) is outside the authorized envelope.
#
# NARROWED 2026-08-29 from {status, add, commit}: `add` was removed
# because a pathspec commit leaves the index untouched when the commit
# fails, whereas add-then-commit left the change STAGED on failure. This
# set may shrink freely; WIDENING it is an authority change.
AUTHORIZED_GIT_VERBS = frozenset({"status", "commit"})

REPO_ROOT = Path(__file__).resolve().parents[2]

_WORKFLOW = """\
jobs:
  test:
    strategy:
      matrix:
        subsystem:
          - a
          - b
          - c
          - d
          - e
"""


def _git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True,
    )


class _FixtureRepo:
    """Minimal real git repo pulse_sweep() can run against cleanly:
    no test_*.py files anywhere (so check_ci_matrix_coverage() and
    count_real_tests() both see zero), no @-imports, no subsystem dirs,
    no PARETO_FRONTIER.md, no mouth logs, no .claude/commands/ -- every
    Level-1 check other than check_readme_test_count() returns []
    against this shape by construction, not by luck (each one's own
    "absent -> not a finding" contract, read from sentinel.py directly)."""

    def __init__(self, tmpdir, readme_text):
        self.root = Path(tmpdir)
        (self.root / "CLAUDE.md").write_text("# doctrine\n")
        (self.root / "README.md").write_text(readme_text)
        # Pre-create foundation/ with its own BUILD_REPORT.md, matching
        # the real repository -- otherwise the receipt log's own mkdir
        # (a directory named "foundation" appearing with no
        # BUILD_REPORT.md) would itself trip check_subsystem_build_
        # reports(), a real check reacting correctly to a fixture
        # artifact that doesn't exist in the real repo.
        (self.root / "foundation").mkdir()
        (self.root / "foundation" / "BUILD_REPORT.md").write_text(
            "# report\n\nheading plus body: a bare heading is a stub, not an\n"
            "audit trail, and has been rejected since 2026-08-29.\n")
        (self.root / ".github" / "workflows").mkdir(parents=True)
        (self.root / ".github" / "workflows" / "tests.yml").write_text(_WORKFLOW)
        (self.root / ".gitignore").write_text(
            ".autonomy_stop\nfoundation/autonomy_loop_log.jsonl\n"
        )
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "test@example.com")
        _git(self.root, "config", "user.name", "Test")
        _git(self.root, "add", ".")
        _git(self.root, "commit", "-q", "-m", "initial")

    def is_clean(self):
        r = _git(self.root, "status", "--porcelain")
        return r.stdout.strip() == ""

    def last_commit_message(self):
        r = _git(self.root, "log", "-1", "--format=%B")
        return r.stdout


_DRIFTED_README = "**100 tests across 5 subsystems, all passing\n"
_CLEAN_README = "**0 tests across 5 subsystems, all passing\n"
_UNMATCHABLE_DRIFT_README = "**100 tests across many subsystems, all passing\n"


class TestRunOneCycleKillSwitch(unittest.TestCase):
    def test_kill_switch_present_stops_before_any_git_or_sensing_work(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            (fx.root / AUTONOMY_STOP_FILENAME).write_text("")
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_KILL_SWITCH")
            # Untouched: no fix attempted despite real drift present.
            self.assertEqual((fx.root / "README.md").read_text(), _DRIFTED_README)


class TestRunOneCycleDirtyTree(unittest.TestCase):
    def test_dirty_tree_stops_and_makes_no_changes(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            (fx.root / "untracked.txt").write_text("uncommitted")
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_DIRTY_TREE")


class TestRunOneCycleCleanIdle(unittest.TestCase):
    def test_no_findings_is_clean_idle_not_a_stop(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "CLEAN_IDLE")
            self.assertFalse(result.is_stop())


class TestRunOneCycleFixesReadmeDrift(unittest.TestCase):
    def test_the_one_authorized_finding_is_fixed_and_committed(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "FIXED_README_DRIFT")
            self.assertIn("100 tests across 5 subsystems", result.detail)
            self.assertIn("0 tests across 5 subsystems", result.detail)
            self.assertTrue(fx.is_clean(), "loop must leave a clean tree behind")
            self.assertIn("[autonomy-loop]", fx.last_commit_message())
            self.assertIn(
                "0 tests across 5 subsystems", (fx.root / "README.md").read_text(),
            )

    def test_the_fix_is_verified_before_being_trusted(self):
        # Re-running pulse_sweep after the fix must genuinely see no
        # finding -- proven by running a second cycle and getting
        # CLEAN_IDLE, not by trusting the write alone.
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            first = run_one_cycle(fx.root)
            self.assertEqual(first.action, "FIXED_README_DRIFT")
            second = run_one_cycle(fx.root)
            self.assertEqual(second.action, "CLEAN_IDLE")


class TestRunOneCycleUnexpectedFindings(unittest.TestCase):
    def test_readme_drift_plus_another_finding_stops_for_human_review(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            (fx.root / "broken.py").write_text("def f(:\n    pass\n")
            _git(fx.root, "add", ".")
            _git(fx.root, "commit", "-q", "-m", "add broken file")
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_UNEXPECTED_FINDINGS")
            # No fix attempted -- README left exactly as it was.
            self.assertEqual((fx.root / "README.md").read_text(), _DRIFTED_README)
            self.assertTrue(fx.is_clean())


class TestRunOneCyclePatternNotFound(unittest.TestCase):
    def test_a_real_drift_sentinel_catches_but_this_loop_cannot_safely_fix_halts(self):
        # sentinel.check_readme_test_count()'s own looser regex (just
        # "**N tests across") fires here; this loop's narrower,
        # verbatim fix-pattern (requires "N subsystems" immediately
        # after) does not match "many subsystems" -- proving it fails
        # closed rather than guessing at an unfamiliar shape.
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _UNMATCHABLE_DRIFT_README)
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_PATTERN_NOT_FOUND")
            self.assertEqual(
                (fx.root / "README.md").read_text(), _UNMATCHABLE_DRIFT_README,
            )


class TestCycleResultValidation(unittest.TestCase):
    def test_unknown_action_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            CycleResult("MADE_UP_ACTION", "x", "2026-01-01T00:00:00+00:00")

    def test_is_stop_true_only_for_stopped_actions(self):
        self.assertTrue(CycleResult("STOPPED_DIRTY_TREE", "x", "t").is_stop())
        self.assertFalse(CycleResult("CLEAN_IDLE", "x", "t").is_stop())
        self.assertFalse(CycleResult("FIXED_README_DRIFT", "x", "t").is_stop())


class TestRunLoop(unittest.TestCase):
    def test_stops_immediately_on_first_stop_result_no_sleep(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            (fx.root / AUTONOMY_STOP_FILENAME).write_text("")
            results = run_loop(fx.root, sleep_seconds=1, sleep_slice_seconds=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].action, "STOPPED_KILL_SWITCH")

    def test_max_cycles_hook_bounds_a_healthy_idle_loop(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            results = run_loop(
                fx.root, sleep_seconds=0, sleep_slice_seconds=0, max_cycles=3,
            )
            self.assertEqual(len(results), 3)
            self.assertTrue(all(r.action == "CLEAN_IDLE" for r in results))

    def test_fixes_then_goes_idle_across_two_cycles(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            results = run_loop(
                fx.root, sleep_seconds=0, sleep_slice_seconds=0, max_cycles=2,
            )
            self.assertEqual([r.action for r in results],
                              ["FIXED_README_DRIFT", "CLEAN_IDLE"])

    def test_kill_switch_dropped_mid_sleep_stops_the_loop(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            # sleep_seconds > 0 forces the loop through the sleep-slice
            # path; drop the kill switch before the first slice elapses
            # by writing it immediately after the first (CLEAN_IDLE)
            # cycle would have been logged -- simplest reliable way to
            # hit this branch in a fast test is a 0-length first slice.
            (fx.root / AUTONOMY_STOP_FILENAME).write_text("")
            results = run_loop(fx.root, sleep_seconds=5, sleep_slice_seconds=1)
            self.assertEqual(results[0].action, "STOPPED_KILL_SWITCH")

    def test_receipt_log_is_written(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            run_loop(fx.root, sleep_seconds=0, sleep_slice_seconds=0, max_cycles=1)
            log = fx.root / "foundation" / "autonomy_loop_log.jsonl"
            self.assertTrue(log.exists())
            self.assertIn("CLEAN_IDLE", log.read_text())


if __name__ == "__main__":
    unittest.main()


class TestGitCapabilityIsStructurallyConfined(unittest.TestCase):
    """The 'never pushes' claim, enforced instead of merely asserted.

    THE GAP THIS CLOSES (found 2026-08-29). `never pushes` was claimed in
    FOUR places -- this module's docstring, the commit message it writes,
    `.claude/commands/boot.md`, and `HUMAN_DECISIONS.md` item 14, whose
    entire argument that scheduling is comparatively low-risk RESTS on
    it -- and was enforced by ZERO tests. `_git()` is a generic wrapper
    that forwards arbitrary arguments to `git`, so the only thing
    preventing a push was that no call site happened to pass one. That is
    discipline, not a gate.

    This repository's own Critical Function Switch-Gate doctrine says a
    reminder is not an enforcement mechanism, and its Two-Point rule says
    a load-bearing invariant needs enforcement independent of the code
    path that honours it. Same structural-assertion pattern as
    `test_sentinel.py::TestSentinelCannotExecute`, reused rather than
    reinvented."""

    def _git_call_verbs(self):
        """Every literal verb passed to `_git()`, extracted from the AST
        rather than by grepping strings -- a grep would also match the
        word inside a docstring or comment."""
        tree = ast.parse(Path(autonomy_loop.__file__).read_text())
        verbs, dynamic = [], []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Name) and node.func.id == "_git"):
                continue
            # args[0] is repo_root; args[1] is the git verb.
            if len(node.args) < 2:
                dynamic.append(ast.dump(node))
                continue
            verb = node.args[1]
            if isinstance(verb, ast.Constant) and isinstance(verb.value, str):
                verbs.append(verb.value)
            else:
                dynamic.append(ast.dump(node))
        return verbs, dynamic

    def test_every_git_verb_reached_is_authorized(self):
        verbs, _ = self._git_call_verbs()
        self.assertTrue(verbs, "expected to find real _git() call sites")
        unauthorized = sorted(set(verbs) - AUTHORIZED_GIT_VERBS)
        self.assertEqual(
            unauthorized, [],
            f"autonomy_loop reached unauthorized git verb(s) {unauthorized}. "
            f"Only {sorted(AUTHORIZED_GIT_VERBS)} are inside this loop's "
            f"authorized envelope. Widening this set is an AUTHORITY "
            f"CHANGE and belongs in HUMAN_DECISIONS.md, not in a code edit.",
        )

    def test_no_git_verb_is_computed_at_runtime(self):
        # A dynamic verb (a variable, f-string, or *args splat) would let
        # a value chosen at runtime escape the static check above -- the
        # alternate-execution-path bypass this test exists to prevent.
        _, dynamic = self._git_call_verbs()
        self.assertEqual(
            dynamic, [],
            "every _git() call must pass a literal string verb so the "
            "authorized set is statically checkable",
        )

    def test_push_appears_nowhere_in_executable_code(self):
        # Independent second point, per the Two-Point Enforcement Rule:
        # even if the AST walk above were somehow evaded, no executable
        # line may contain the token. Docstrings/comments are stripped so
        # the module may still DOCUMENT that it never pushes.
        tree = ast.parse(Path(autonomy_loop.__file__).read_text())
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                continue  # string literals incl. docstrings handled below
            if isinstance(node, ast.Attribute) and "push" in node.attr.lower():
                offenders.append(node.attr)
            if isinstance(node, ast.Name) and "push" in node.id.lower():
                offenders.append(node.id)
        self.assertEqual(offenders, [], f"push-like identifiers found: {offenders}")

    def test_the_only_subprocess_entry_point_is_the_git_wrapper(self):
        # If a second subprocess call existed, confining _git() would not
        # confine the module -- the capability could flow around it.
        tree = ast.parse(Path(autonomy_loop.__file__).read_text())
        subprocess_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
        ]
        self.assertEqual(
            len(subprocess_calls), 1,
            "exactly one subprocess call may exist (inside _git); a second "
            "one would be an unconfined execution path",
        )


class TestStoppedResultLeavesNoMutation(unittest.TestCase):
    """TRAJECTORY confinement, not just terminal-state confinement.

    REPRODUCED 2026-08-29 before the fix: with a rejecting pre-commit
    hook, run_one_cycle() returned STOPPED_FIX_VERIFICATION_FAILED -- a
    terminal state that reads as "nothing happened" -- while
    `git status --porcelain` showed `M  README.md`: the change was
    written AND STAGED. A human's next unrelated `git commit` would have
    silently absorbed the loop's edit under their own authorship, with no
    receipt (run_one_cycle writes none).

    A safe final state is not a safe trajectory. These tests assert the
    repository is byte-identical after a failed cycle."""

    def _repo_with_failing_commit(self, tmp):
        fx = _FixtureRepo(tmp, _DRIFTED_README)
        hook = fx.root / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
        return fx

    def test_failed_commit_leaves_readme_byte_identical(self):
        with tempfile.TemporaryDirectory() as d:
            fx = self._repo_with_failing_commit(d)
            before = (fx.root / "README.md").read_text()
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_FIX_VERIFICATION_FAILED")
            self.assertEqual((fx.root / "README.md").read_text(), before)

    def test_failed_commit_leaves_no_staged_change(self):
        # The exact reproduced defect: porcelain column 1 == staged.
        with tempfile.TemporaryDirectory() as d:
            fx = self._repo_with_failing_commit(d)
            run_one_cycle(fx.root)
            porcelain = _git(fx.root, "status", "--porcelain").stdout
            self.assertEqual(
                porcelain.strip(), "",
                f"a STOPPED_* cycle left the tree dirty: {porcelain!r}",
            )

    def test_failed_commit_makes_no_commit(self):
        with tempfile.TemporaryDirectory() as d:
            fx = self._repo_with_failing_commit(d)
            before = _git(fx.root, "rev-list", "--count", "HEAD").stdout.strip()
            run_one_cycle(fx.root)
            after = _git(fx.root, "rev-list", "--count", "HEAD").stdout.strip()
            self.assertEqual(before, after)

    def test_the_receipt_states_the_rollback_happened(self):
        # The result must not merely be clean -- it must SAY it rolled
        # back, so a reader is not left guessing what touched the disk.
        with tempfile.TemporaryDirectory() as d:
            fx = self._repo_with_failing_commit(d)
            result = run_one_cycle(fx.root)
            self.assertIn("restored", result.detail)

    def test_next_cycle_is_not_poisoned_by_a_failed_cycle(self):
        # Restart behaviour: a failed cycle must not leave a dirty tree
        # that turns every future cycle into STOPPED_DIRTY_TREE.
        with tempfile.TemporaryDirectory() as d:
            fx = self._repo_with_failing_commit(d)
            run_one_cycle(fx.root)
            (fx.root / ".git" / "hooks" / "pre-commit").unlink()
            second = run_one_cycle(fx.root)
            self.assertEqual(second.action, "FIXED_README_DRIFT")
            self.assertTrue(fx.is_clean())

    def test_happy_path_still_commits_without_staging_first(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "FIXED_README_DRIFT")
            self.assertTrue(fx.is_clean())
            self.assertIn("[autonomy-loop]", fx.last_commit_message())


class TestEveryCycleIsReceipted(unittest.TestCase):
    """Attribution, the half that recovery does not cover.

    REPRODUCED 2026-08-29: a cycle that wrote README.md, failed to commit,
    and correctly rolled back left HEAD unmoved, the tree byte-identical,
    and NO receipt file -- zero durable evidence that a real mutation had
    been attempted and reverted. `git` cannot carry this fact by
    construction: a correct rollback restores the exact prior bytes, so
    there is nothing for git to show.

    That made "never ran" and "ran, attempted, failed, recovered"
    indistinguishable to any later reader."""

    def _receipts(self, root):
        log = root / "foundation" / RECEIPT_LOG_NAME
        if not log.exists():
            return []
        return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]

    def _failing_commit_repo(self, tmp):
        fx = _FixtureRepo(tmp, _DRIFTED_README)
        hook = fx.root / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
        return fx

    def test_rolled_back_attempt_leaves_a_durable_receipt(self):
        # The exact reproduced gap: git shows nothing, so the receipt is
        # the ONLY possible record.
        with tempfile.TemporaryDirectory() as d:
            fx = self._failing_commit_repo(d)
            head_before = _git(fx.root, "rev-parse", "HEAD").stdout.strip()
            result = run_one_cycle(fx.root)
            self.assertEqual(result.action, "STOPPED_FIX_VERIFICATION_FAILED")
            # git genuinely carries nothing
            self.assertEqual(head_before,
                             _git(fx.root, "rev-parse", "HEAD").stdout.strip())
            self.assertTrue(fx.is_clean())
            # ...so the receipt must
            receipts = self._receipts(fx.root)
            self.assertEqual(len(receipts), 1)
            self.assertEqual(receipts[0]["action"], "STOPPED_FIX_VERIFICATION_FAILED")
            self.assertIn("restored", receipts[0]["detail"])

    def test_every_outcome_class_is_receipted(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            run_one_cycle(fx.root)                       # CLEAN_IDLE
            (fx.root / AUTONOMY_STOP_FILENAME).write_text("")
            run_one_cycle(fx.root)                       # STOPPED_KILL_SWITCH
            (fx.root / AUTONOMY_STOP_FILENAME).unlink()
            (fx.root / "untracked.txt").write_text("x")
            run_one_cycle(fx.root)                       # STOPPED_DIRTY_TREE
            actions = [r["action"] for r in self._receipts(fx.root)]
            self.assertEqual(
                actions,
                ["CLEAN_IDLE", "STOPPED_KILL_SWITCH", "STOPPED_DIRTY_TREE"])

    def test_run_loop_does_not_double_log(self):
        # run_one_cycle now receipts itself; run_loop must not write a
        # second entry for the same cycle.
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            run_loop(fx.root, sleep_seconds=0, sleep_slice_seconds=0, max_cycles=3)
            actions = [r["action"] for r in self._receipts(fx.root)]
            self.assertEqual(actions, ["CLEAN_IDLE"] * 3)

    def test_mid_sleep_kill_switch_is_still_receipted_exactly_once(self):
        # That receipt is NOT produced by run_one_cycle, so it must still
        # be written by run_loop itself.
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _CLEAN_README)
            (fx.root / AUTONOMY_STOP_FILENAME).write_text("")
            run_loop(fx.root, sleep_seconds=5, sleep_slice_seconds=1)
            actions = [r["action"] for r in self._receipts(fx.root)]
            self.assertEqual(actions.count("STOPPED_KILL_SWITCH"), 1)

    def test_a_successful_fix_is_receipted_as_well_as_committed(self):
        with tempfile.TemporaryDirectory() as d:
            fx = _FixtureRepo(d, _DRIFTED_README)
            run_one_cycle(fx.root)
            receipts = self._receipts(fx.root)
            self.assertEqual(receipts[-1]["action"], "FIXED_README_DRIFT")


class TestReceiptsHaveAReader(unittest.TestCase):
    """The receipts written since ce18f91 had NO reader anywhere.

    Three sibling machine-local logs each have a reader routed into
    boot.md (read_pulse_continuity, read_cron_stderr,
    read_dependency_pressure_log). autonomy_loop_log.jsonl had none, so
    the facts it carries -- above all the count of cycles that really
    wrote to disk and rolled back, which git cannot show by construction
    -- could not reach any decision, including HUMAN_DECISIONS item 14."""

    def _write(self, root, records):
        d = root / "foundation"
        d.mkdir(parents=True, exist_ok=True)
        (d / RECEIPT_LOG_NAME).write_text(
            "".join(json.dumps(r) + "\n" for r in records))

    def test_absent_log_is_not_available_and_does_not_raise(self):
        with tempfile.TemporaryDirectory() as d:
            r = read_autonomy_receipts(Path(d))
            self.assertFalse(r.available)
            self.assertEqual(r.records_considered, 0)
            self.assertIn("never run", r.warnings[0])

    def test_counts_outcomes_and_fixes(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), [
                {"action": "CLEAN_IDLE", "detail": "x", "occurred_at": "t1"},
                {"action": "FIXED_README_DRIFT", "detail": "y", "occurred_at": "t2"},
                {"action": "FIXED_README_DRIFT", "detail": "z", "occurred_at": "t3"},
            ])
            r = read_autonomy_receipts(Path(d))
            self.assertTrue(r.available)
            self.assertEqual(r.fixes_applied, 2)
            self.assertEqual(r.outcome_counts["CLEAN_IDLE"], 1)
            self.assertEqual(r.latest_timestamp, "t3")

    def test_counts_attempted_and_recovered_the_fact_git_cannot_show(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), [
                {"action": "STOPPED_FIX_VERIFICATION_FAILED",
                 "detail": "git commit failed: hook (README.md restored to its pre-fix contents)",
                 "occurred_at": "t1"},
                # A stop that never reached the write stage must NOT count
                # as a recovered mutation.
                {"action": "STOPPED_DIRTY_TREE", "detail": "not clean", "occurred_at": "t2"},
            ])
            r = read_autonomy_receipts(Path(d))
            self.assertEqual(r.attempted_and_recovered, 1)

    def test_verification_failure_without_a_rollback_marker_is_not_counted(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), [
                {"action": "STOPPED_FIX_VERIFICATION_FAILED",
                 "detail": "no marker here", "occurred_at": "t1"},
            ])
            self.assertEqual(read_autonomy_receipts(Path(d)).attempted_and_recovered, 0)

    def test_consecutive_stops_at_tail(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), [
                {"action": "FIXED_README_DRIFT", "detail": "a", "occurred_at": "t1"},
                {"action": "STOPPED_DIRTY_TREE", "detail": "b", "occurred_at": "t2"},
                {"action": "STOPPED_DIRTY_TREE", "detail": "c", "occurred_at": "t3"},
            ])
            self.assertEqual(read_autonomy_receipts(Path(d)).consecutive_stops_at_tail, 2)

    def test_fails_soft_on_malformed_lines(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "foundation").mkdir(parents=True)
            (root / "foundation" / RECEIPT_LOG_NAME).write_text(
                "not json\n"
                "12345\n"
                '{"action": "NOT_A_REAL_ACTION", "detail": "x", "occurred_at": "t"}\n'
                '{"action": "CLEAN_IDLE", "detail": "ok", "occurred_at": "t9"}\n'
            )
            r = read_autonomy_receipts(root)
            self.assertTrue(r.available)
            self.assertEqual(r.records_considered, 1)
            self.assertEqual(len(r.warnings), 3)

    def test_is_bounded_and_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._write(root, [
                {"action": "CLEAN_IDLE", "detail": str(i), "occurred_at": f"t{i}"}
                for i in range(500)
            ])
            log = root / "foundation" / RECEIPT_LOG_NAME
            before = log.stat().st_mtime_ns
            r = read_autonomy_receipts(root, max_records=10)
            self.assertEqual(r.records_considered, 10)
            self.assertEqual(log.stat().st_mtime_ns, before)

    def test_reads_the_real_repository_without_raising(self):
        r = read_autonomy_receipts(REPO_ROOT)
        self.assertIsInstance(r.outcome_counts, dict)


class TestZeroFailuresIsNotEvidenceOfReliability(unittest.TestCase):
    """The misreading this reader invited, closed at the source.

    `attempted_and_recovered == 0` reads as "no failures, looks
    reliable". It is not. With n observations and zero observed failures
    the 95% upper bound on the true failure rate is 3/n (statistical rule
    of three). At the real n on 2026-08-29 -- FOUR recorded cycles -- the
    bound was 0.75: consistent with a loop that fails three quarters of
    the time.

    HUMAN_DECISIONS item 14 (schedule this loop unattended?) is exactly
    the decision that could be answered from that false confidence, and
    the previous cycle had just made the zero visible without its bound."""

    def _write(self, root, records):
        d = root / "foundation"
        d.mkdir(parents=True, exist_ok=True)
        (d / RECEIPT_LOG_NAME).write_text(
            "".join(json.dumps(r) + "\n" for r in records))

    def _clean(self, n):
        return [{"action": "CLEAN_IDLE", "detail": "x", "occurred_at": f"t{i}"}
                for i in range(n)]

    def test_bound_is_three_over_n_when_no_failures_observed(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), self._clean(4))
            r = read_autonomy_receipts(Path(d))
            self.assertEqual(r.attempted_and_recovered, 0)
            self.assertAlmostEqual(r.failure_rate_upper_bound_95, 0.75)

    def test_bound_tightens_only_with_more_observations(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), self._clean(60))
            r = read_autonomy_receipts(Path(d), max_records=100)
            self.assertAlmostEqual(r.failure_rate_upper_bound_95, 0.05)

    def test_four_clean_cycles_do_not_support_a_five_percent_claim(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), self._clean(4))
            r = read_autonomy_receipts(Path(d))
            self.assertFalse(r.evidence_is_sufficient_for(0.05))

    def test_no_observations_can_never_satisfy_a_reliability_claim(self):
        # Absence of data must not read as evidence of reliability.
        with tempfile.TemporaryDirectory() as d:
            r = read_autonomy_receipts(Path(d))
            self.assertIsNone(r.failure_rate_upper_bound_95)
            self.assertFalse(r.evidence_is_sufficient_for(0.99))

    def test_bound_is_absent_once_real_failures_are_observed(self):
        # The rule of three applies only to the zero-failure case; with
        # observed failures the raw counts stand on their own.
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), [
                {"action": "STOPPED_FIX_VERIFICATION_FAILED",
                 "detail": "boom (README.md restored to its pre-fix contents)",
                 "occurred_at": "t1"},
            ] + self._clean(3))
            r = read_autonomy_receipts(Path(d))
            self.assertEqual(r.attempted_and_recovered, 1)
            self.assertIsNone(r.failure_rate_upper_bound_95)
            self.assertFalse(r.evidence_is_sufficient_for(0.05))

    def test_the_real_repository_bound_is_reported(self):
        r = read_autonomy_receipts(REPO_ROOT)
        if r.available and r.records_considered and r.attempted_and_recovered == 0:
            self.assertIsNotNone(r.failure_rate_upper_bound_95)
            self.assertAlmostEqual(
                r.failure_rate_upper_bound_95, 3.0 / r.records_considered)


class TestReliabilityLineCannotSeparateCountFromUncertainty(unittest.TestCase):
    """A point estimate reported without its uncertainty invites the
    wrong decision.

    REPRODUCED 2026-08-29: `.claude/commands/boot.md` step 4b instructed
    the operator to report `attempted_and_recovered` (the numerator) and
    `records_considered` (the denominator) but contained ZERO references
    to `failure_rate_upper_bound_95` or `evidence_is_sufficient_for`,
    though both were already computed. The operator had to know the rule
    of three and derive 3/n themselves to avoid reading "0" as
    "reliable" -- and the decision downstream is item 14, scheduling an
    unattended commit-capable loop.

    The fix is structural, not a longer checklist: these four facts are
    emitted together or not at all."""

    def _write(self, root, records):
        d = root / "foundation"
        d.mkdir(parents=True, exist_ok=True)
        (d / RECEIPT_LOG_NAME).write_text(
            "".join(json.dumps(r) + "\n" for r in records))

    def _clean(self, n):
        return [{"action": "CLEAN_IDLE", "detail": "x", "occurred_at": f"t{i}"}
                for i in range(n)]

    def test_the_line_always_carries_all_four_facts(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), self._clean(6))
            line = read_autonomy_receipts(Path(d)).format_reliability_line()
            self.assertIn("n=6", line)                     # sample size
            self.assertIn("attempted_and_recovered=0", line)  # observation
            self.assertIn("0.50", line)                    # uncertainty
            self.assertIn("NOT sufficient", line)          # sufficiency

    def test_the_verdict_actually_varies_not_hardcoded(self):
        # POSITIVE CONTROL with an EXPLICIT precondition: at n=100 the
        # bound is 0.03, which IS sufficient for the 5% test. Without
        # this, "NOT sufficient" could be a constant string and the test
        # above would still pass.
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), self._clean(100))
            r = read_autonomy_receipts(Path(d), max_records=200)
            self.assertEqual(r.records_considered, 100)
            self.assertAlmostEqual(r.failure_rate_upper_bound_95, 0.03)
            line = r.format_reliability_line()
            self.assertIn("evidence is sufficient", line)
            self.assertNotIn("NOT sufficient", line)

    def test_the_line_never_claims_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), self._clean(100))
            line = read_autonomy_receipts(Path(d), max_records=200).format_reliability_line()
            # Even when the evidence IS sufficient, the line must not
            # read as permission -- evidence never becomes authority.
            self.assertIn("not an authorization", line)

    def test_absent_log_states_no_claim_is_supportable(self):
        with tempfile.TemporaryDirectory() as d:
            line = read_autonomy_receipts(Path(d)).format_reliability_line()
            self.assertIn("n=0", line)
            self.assertIn("no reliability claim is supportable", line)

    def test_observed_failures_disable_the_rule_of_three_honestly(self):
        with tempfile.TemporaryDirectory() as d:
            self._write(Path(d), [
                {"action": "STOPPED_FIX_VERIFICATION_FAILED",
                 "detail": "boom (README.md restored to its pre-fix contents)",
                 "occurred_at": "t1"}] + self._clean(5))
            line = read_autonomy_receipts(Path(d)).format_reliability_line()
            self.assertIn("failures observed", line)
            self.assertIn("NOT sufficient", line)

    def test_boot_protocol_routes_to_the_line_not_the_bare_count(self):
        # LENS B (routing): the operator path must name the inseparable
        # formatter. Independent of the formatter's own behaviour --
        # this fails if boot.md stops routing to it even while the
        # method itself stays perfect.
        boot = (REPO_ROOT / ".claude" / "commands" / "boot.md").read_text()
        self.assertIn("format_reliability_line", boot)
