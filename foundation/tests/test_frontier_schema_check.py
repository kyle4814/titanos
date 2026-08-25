import tempfile
import unittest
from pathlib import Path

from foundation.sentinel import check_frontier_schema, pulse_sweep

VALID_FRONTIER = """# Pareto Frontier

## Active

### FRONTIER-100 — a real candidate
- **CURRENT:** something exists.
- **GAP:** something is missing.
- **LEVER:** why it matters.

## Blocked

### FRONTIER-200 — a blocked candidate
- **CURRENT:** something exists.
- **GAP:** something is missing.
- **blocked_by:** a real dependency.

## Archive (built)

| ID | Capability | Commit |
|---|---|---|
| FRONTIER-000 | some capability | `abc123` |

## Rejected / not on the frontier

- some rejected idea, no schema required here.
"""

MISSING_CURRENT = """## Active

### FRONTIER-100 — missing current
- **GAP:** something is missing.
"""

MISSING_GAP = """## Blocked

### FRONTIER-200 — missing gap
- **CURRENT:** something exists.
- **blocked_by:** a real dependency.
"""

UNKNOWN_PROSE_STILL_VALID = """## Active

### FRONTIER-100 — has extra unknown prose
- **CURRENT:** something exists.
- **GAP:** something is missing.
- **SOME_FUTURE_FIELD_NOT_YET_IN_THE_SCHEMA:** extra prose that should
  not cause a false failure.
"""


class TestFrontierSchemaCheck(unittest.TestCase):
    def _check(self, content: str) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PARETO_FRONTIER.md").write_text(content)
            return check_frontier_schema(root)

    def test_valid_entries_pass(self):
        self.assertEqual(self._check(VALID_FRONTIER), [])

    def test_missing_current_fails_explicitly(self):
        findings = self._check(MISSING_CURRENT)
        self.assertEqual(len(findings), 1)
        self.assertIn("CURRENT", findings[0].observation)
        self.assertIn("FRONTIER-100", findings[0].observation)

    def test_missing_gap_fails_explicitly(self):
        findings = self._check(MISSING_GAP)
        self.assertEqual(len(findings), 1)
        self.assertIn("GAP", findings[0].observation)
        self.assertIn("FRONTIER-200", findings[0].observation)

    def test_unknown_optional_prose_does_not_false_fail(self):
        self.assertEqual(self._check(UNKNOWN_PROSE_STILL_VALID), [])

    def test_archive_and_rejected_sections_not_checked(self):
        # VALID_FRONTIER's Archive table row and Rejected bullet have
        # neither CURRENT nor GAP fields -- and correctly produce no
        # findings, because only Active/Blocked are in scope.
        self.assertEqual(self._check(VALID_FRONTIER), [])

    def test_missing_file_produces_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(check_frontier_schema(Path(tmp)), [])

    def test_real_repository_frontier_currently_passes(self):
        repo_root = Path(__file__).resolve().parents[2]
        findings = check_frontier_schema(repo_root)
        self.assertEqual(findings, [], f"real PARETO_FRONTIER.md has drifted: {findings}")

    def test_wired_into_pulse_sweep(self):
        repo_root = Path(__file__).resolve().parents[2]
        report = pulse_sweep(repo_root)
        schema_findings = [f for f in report.findings if "required field" in f.observation]
        self.assertEqual(schema_findings, [])


if __name__ == "__main__":
    unittest.main()
