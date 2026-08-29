import subprocess
import tempfile
import unittest
from pathlib import Path

from foundation.autonomy_loop import (
    AUTONOMY_STOP_FILENAME,
    CycleResult,
    run_loop,
    run_one_cycle,
)

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
        (self.root / "foundation" / "BUILD_REPORT.md").write_text("# report\n")
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
