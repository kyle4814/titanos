"""`run_all_tests.sh --fast` must never print a verdict the release gate
would accept as authoritative (TITANOS_V12_CONSTITUTION.md Art. V).

`release.sh` takes the runner's last line and accepts it only if it
matches `PASS*`. A `--fast` run skips a real proof, so its verdict is
prefixed `ADVISORY`. This test runs the real script against a throwaway
tree with one trivial test per suite, so it takes seconds, not hours.
"""
from __future__ import annotations

import fnmatch
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "run_all_tests.sh"


def _suites() -> list[str]:
    m = re.search(r"SUITES=\(([^)]*)\)", RUNNER.read_text())
    return m.group(1).split()


def _release_gate_accepts(last_line: str) -> bool:
    """release.sh: `case "$TESTOUT" in PASS*) pass ...`"""
    return fnmatch.fnmatchcase(last_line, "PASS*")


class TestRunnerVerdictLabels(unittest.TestCase):

    def _run(self, *, fail: bool, fast: bool) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copy(RUNNER, root / "run_all_tests.sh")
            for suite in _suites():
                d = root / suite
                d.mkdir(parents=True)
                body = "self.assertTrue(False)" if (fail and suite == "firewall") else "pass"
                (d / "test_trivial.py").write_text(
                    "import unittest\n"
                    "class T(unittest.TestCase):\n"
                    f"    def test_x(self):\n        {body}\n")
            args = ["bash", str(root / "run_all_tests.sh")] + (["--fast"] if fast else [])
            r = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=300)
            lines = [l for l in r.stdout.splitlines() if l.strip()]
            return r.returncode, lines[-1]

    def test_authoritative_pass_is_accepted_by_the_release_gate(self):
        rc, last = self._run(fail=False, fast=False)
        self.assertEqual(rc, 0)
        self.assertTrue(last.startswith("PASS "), last)
        self.assertTrue(_release_gate_accepts(last))

    def test_fast_pass_is_labelled_advisory_and_refused_by_the_release_gate(self):
        rc, last = self._run(fail=False, fast=True)
        self.assertEqual(rc, 0)
        self.assertTrue(last.startswith("ADVISORY PASS "), last)
        self.assertFalse(_release_gate_accepts(last))

    def test_fast_failure_is_still_a_failure(self):
        rc, last = self._run(fail=True, fast=True)
        self.assertNotEqual(rc, 0)
        self.assertTrue(last.startswith("ADVISORY FAIL "), last)
        self.assertIn("firewall", last)

    def test_authoritative_failure_is_unchanged(self):
        rc, last = self._run(fail=True, fast=False)
        self.assertNotEqual(rc, 0)
        self.assertTrue(last.startswith("FAIL "), last)


if __name__ == "__main__":
    unittest.main()
