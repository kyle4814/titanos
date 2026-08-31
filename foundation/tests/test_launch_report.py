"""The module that decides READY must not itself be untested.

`foundation/capability_registry.py` measures every capability here and
classified this one as UNTESTED. That is the worst possible module to
leave uncovered: it computes whether the system is fit to launch, and a
launch verdict from an unverified verdict-maker is exactly the
substitution this repository exists to refuse.

These tests pin the two properties that matter most: the status is
DERIVED rather than chosen, and an unsupplied test result is never read
as a passing one.
"""

import json
import tempfile
import unittest
from pathlib import Path

from foundation.launch_report import (
    REPO_ROOT, Criterion, LaunchAssessment, assess, render_receipt,
    write_artifacts, _clean_ignoring_own_output,
)


def _assessment(**kw):
    base = dict(
        generated_at="2026-09-01T00:00:00+00:00", revision="abc1234",
        state_digest="d" * 16, worktree_clean=True, tests_run=10,
        tests_failed=0, autonomy_ratio=0.0, scheduled_entrypoints=1,
        runnable_entrypoints=9, human_gated_operations=19,
        pulse_findings=0, receipt_head="OC-x", criteria=(), notes=())
    base.update(kw)
    return LaunchAssessment(**base)


class TestStatusIsDerivedNeverChosen(unittest.TestCase):

    def test_all_criteria_met_and_tests_green_is_ready(self):
        a = _assessment(criteria=(Criterion("X", "MET", "e"),))
        self.assertEqual(a.status(), "READY")

    def test_a_single_unmet_criterion_blocks_ready(self):
        a = _assessment(criteria=(Criterion("X", "MET", "e"),
                                  Criterion("Y", "UNMET", "e")))
        self.assertEqual(a.status(), "READY_WITH_LIMITATIONS")

    def test_a_failing_test_run_is_no_go_regardless_of_criteria(self):
        """A green criteria list cannot rescue a red suite."""
        a = _assessment(tests_failed=3, criteria=(Criterion("X", "MET", "e"),))
        self.assertEqual(a.status(), "NO_GO")

    def test_unsupplied_test_results_are_never_read_as_passing(self):
        """The whole point. Silence about the suite is not a green suite."""
        a = _assessment(tests_run=None, tests_failed=None,
                        criteria=(Criterion("X", "MET", "e"),))
        self.assertEqual(a.status(), "UNVERIFIED_NO_TEST_RESULTS")

    def test_not_measured_is_treated_as_blocking_not_as_met(self):
        """NOT_MEASURED and MET are different facts. Collapsing them
        would let an unmeasured criterion read as a passing one."""
        a = _assessment(criteria=(Criterion("X", "NOT_MEASURED", "e"),))
        self.assertEqual(len(a.unmet()), 1)
        self.assertEqual(a.status(), "READY_WITH_LIMITATIONS")


class TestCriterionVocabulary(unittest.TestCase):

    def test_only_met_is_non_blocking(self):
        self.assertFalse(Criterion("A", "MET", "e").is_blocking())
        for state in ("UNMET", "NOT_MEASURED"):
            self.assertTrue(Criterion("A", state, "e").is_blocking())

    def test_every_criterion_carries_evidence(self):
        a = assess(REPO_ROOT, tests_run=1, tests_failed=0)
        for c in a.criteria:
            self.assertTrue(c.evidence.strip(),
                            f"{c.name} states no evidence")

    def test_autonomy_measured_and_achieved_are_separate_criteria(self):
        """Measuring a thing and achieving it are different facts. This
        generator must never merge them into one flattering row."""
        names = {c.name for c in assess(REPO_ROOT, tests_run=1,
                                        tests_failed=0).criteria}
        self.assertIn("AUTONOMY_MEASURED", names)
        self.assertIn("AUTONOMY_ACHIEVED", names)


class TestAgainstTheRealRepository(unittest.TestCase):

    def setUp(self):
        self.a = assess(REPO_ROOT, tests_run=2690, tests_failed=0)

    def test_it_reports_the_real_autonomy_ratio_without_rounding_it_up(self):
        self.assertGreaterEqual(self.a.autonomy_ratio, 0.0)
        if self.a.autonomy_ratio == 0.0:
            achieved = [c for c in self.a.criteria
                        if c.name == "AUTONOMY_ACHIEVED"]
            self.assertEqual(achieved[0].state, "UNMET",
                             "a zero ratio must not report as achieved")

    def test_commercial_outcome_is_unmet_until_something_external_happens(self):
        c = [x for x in self.a.criteria if x.name == "COMMERCIAL_OUTCOME"][0]
        self.assertEqual(c.state, "UNMET")

    def test_the_receipt_is_valid_json_and_carries_provenance(self):
        d = json.loads(render_receipt(self.a))
        for key in ("revision", "state_digest", "status", "criteria",
                    "unmet_count"):
            self.assertIn(key, d)

    def test_the_digest_is_present_so_a_reader_can_detect_staleness(self):
        self.assertTrue(self.a.state_digest)


class TestTheCleanlinessCheckIsNotSelfReferential(unittest.TestCase):
    """Writing the artifacts dirties the tree. A naive check therefore
    reported UNMET forever: generate -> dirty -> regenerate -> still
    dirty. A criterion no action can satisfy is worse than none."""

    def test_the_generators_own_output_does_not_count_as_dirty(self):
        from foundation.launch_report import _GENERATED
        self.assertIn("FINAL_SYSTEM_RECEIPT.json", _GENERATED)
        self.assertIn("CAPABILITY_MATRIX.md", _GENERATED)

    def test_other_modified_files_still_count(self):
        """The fix must not become a blanket excuse for a dirty tree."""
        import foundation.launch_report as lr
        original = lr._dirty_paths
        lr._dirty_paths = lambda root: ["some/other/file.py"]
        try:
            self.assertFalse(_clean_ignoring_own_output(REPO_ROOT))
        finally:
            lr._dirty_paths = original


class TestWritingArtifacts(unittest.TestCase):

    def test_it_writes_exactly_the_declared_files_and_no_others(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            before = {p for p in root.rglob("*") if p.is_file()}
            written = write_artifacts(root, tests_run=1, tests_failed=0)
            after = {p for p in root.rglob("*") if p.is_file()}
            self.assertEqual(set(written), {
                "FINAL_SYSTEM_RECEIPT.json", "CAPABILITY_MATRIX.md",
                "REMAINING_LIMITATIONS.md"})
            self.assertEqual(after - before, set(written.values()))

    def test_assessing_writes_nothing(self):
        """assess() must be safe to call anywhere, including from a
        pre-flight check that has not been authorised to mutate."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            assess(root, tests_run=1, tests_failed=0)
            self.assertEqual([p for p in root.rglob("*") if p.is_file()], [])

    def test_it_does_not_crash_on_an_unfamiliar_directory(self):
        with tempfile.TemporaryDirectory() as d:
            a = assess(Path(d))
            self.assertIsInstance(a, LaunchAssessment)

    def test_the_matrix_marks_generated_so_nobody_hand_edits_it(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_artifacts(root, tests_run=1, tests_failed=0)
            text = (root / "CAPABILITY_MATRIX.md").read_text()
            self.assertIn("do not hand-edit", text.lower())

    def test_limitations_lists_every_unmet_criterion(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_artifacts(root, tests_run=1, tests_failed=0)
            text = (root / "REMAINING_LIMITATIONS.md").read_text()
            a = assess(root, tests_run=1, tests_failed=0)
            for c in a.unmet():
                self.assertIn(c.name, text)


if __name__ == "__main__":
    unittest.main()
