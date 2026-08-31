"""The writer that closes the recurring README-drift finding."""

import tempfile
import unittest
from pathlib import Path

from foundation.readme_sync import (
    count_test_definitions, read_declared_count, render_count,
    sync_readme_test_count,
)
from foundation.sentinel import check_readme_test_count

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestAgreesWithTheSensor(unittest.TestCase):
    """The writer and the sensor must measure the same quantity, or they
    would disagree forever and the drift finding would never clear."""

    def test_repo_is_currently_in_sync(self):
        self.assertEqual(
            sync_readme_test_count(REPO_ROOT, dry_run=True)["status"],
            "ALREADY_CURRENT")

    def test_sensor_reports_no_drift_when_writer_says_synced(self):
        if sync_readme_test_count(REPO_ROOT, dry_run=True)["status"] \
                == "ALREADY_CURRENT":
            self.assertEqual(check_readme_test_count(REPO_ROOT), [])


class TestSyncBehaviour(unittest.TestCase):

    def _repo(self, d, claimed, n_tests):
        root = Path(d)
        (root / "pkg" / "tests").mkdir(parents=True)
        body = "\n".join(f"def test_{i}(self): pass" for i in range(n_tests))
        (root / "pkg" / "tests" / "test_x.py").write_text(body)
        (root / "README.md").write_text(
            f"intro\n\n**{claimed} tests across 11 subsystems, all passing**\n")
        return root

    def test_it_updates_a_stale_number(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._repo(d, "1,000", 7)
            result = sync_readme_test_count(root)
            self.assertEqual(result["status"], "UPDATED")
            self.assertEqual(result["real"], 7)
            self.assertEqual(read_declared_count(root / "README.md"), 7)

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._repo(d, "1,000", 7)
            before = (root / "README.md").read_text()
            self.assertEqual(
                sync_readme_test_count(root, dry_run=True)["status"],
                "WOULD_UPDATE")
            self.assertEqual((root / "README.md").read_text(), before)

    def test_an_already_current_readme_is_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._repo(d, "7", 7)
            before = (root / "README.md").read_text()
            self.assertEqual(sync_readme_test_count(root)["status"],
                             "ALREADY_CURRENT")
            self.assertEqual((root / "README.md").read_text(), before)

    def test_a_readme_with_no_claim_is_not_invented_into_one(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text("no numbers here\n")
            self.assertEqual(sync_readme_test_count(root)["status"],
                             "NO_CLAIM_FOUND")

    def test_a_missing_readme_is_reported_not_created(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sync_readme_test_count(Path(d))["status"],
                             "NO_README")
            self.assertFalse((Path(d) / "README.md").exists())

    def test_only_tests_directories_are_counted(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._repo(d, "7", 7)
            (root / "pkg" / "not_tests.py").write_text("def test_decoy(): pass")
            self.assertEqual(count_test_definitions(root), 7)

    def test_thousands_separator_is_preserved(self):
        self.assertEqual(render_count(2492), "2,492")


if __name__ == "__main__":
    unittest.main()
