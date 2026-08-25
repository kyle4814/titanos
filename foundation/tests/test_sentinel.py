import inspect
import re
import tempfile
import unittest
from pathlib import Path

from foundation import sentinel
from foundation.sentinel import (
    Finding, FourPaths, PathProposal, consolidate, format_four_paths,
    pulse_sweep, COMPACTION_THRESHOLD,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN_VERBS = ("execute", "apply", "build", "modify", "commit", "write", "delete", "run")


def _finding(obs="x", loc="a", confidence="HIGH"):
    return Finding(
        observation=obs, evidence_location=loc, confidence=confidence,
        interpretation="i", reversibility="r", recommended_next_action="n",
    )


class TestSentinelCannotExecute(unittest.TestCase):
    def test_no_public_callable_uses_a_forbidden_execution_verb(self):
        for name, obj in inspect.getmembers(sentinel):
            if name.startswith("_") or not (inspect.isfunction(obj) or inspect.isclass(obj)):
                continue
            words = re.split(r"[_A-Z]", name)
            words = [w.lower() for w in words if w]
            first_word = words[0] if words else ""
            self.assertNotIn(
                first_word, FORBIDDEN_VERBS,
                f"'{name}' starts with forbidden execution verb "
                f"'{first_word}' — a Sentinel callable named as an action "
                f"verb (vs. a check/report noun) would imply it performs "
                f"that action.",
            )

    def test_module_has_no_write_text_or_unlink_calls(self):
        source = Path(sentinel.__file__).read_text()
        for banned in ("write_text(", "unlink(", "os.remove(", "shutil.rmtree(", "subprocess."):
            self.assertNotIn(banned, source)


class TestFinding(unittest.TestCase):
    def test_valid_finding_constructs(self):
        f = _finding()
        self.assertEqual(f.confidence, "HIGH")

    def test_bad_confidence_rejected(self):
        with self.assertRaises(ValueError):
            _finding(confidence="VERY_SURE")

    def test_empty_location_rejected(self):
        with self.assertRaises(ValueError):
            Finding(
                observation="x", evidence_location="", confidence="HIGH",
                interpretation="i", reversibility="r", recommended_next_action="n",
            )

    def test_key_is_observation_plus_location(self):
        f = _finding(obs="dup", loc="file.py")
        self.assertEqual(f.key(), ("dup", "file.py"))


class TestConsolidate(unittest.TestCase):
    def test_duplicate_findings_collapse_to_one(self):
        a = _finding(obs="same", loc="x.py")
        b = _finding(obs="same", loc="x.py", confidence="LOW")
        result = consolidate([a, b])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], a)  # first occurrence wins

    def test_distinct_findings_both_kept(self):
        a = _finding(obs="one", loc="x.py")
        b = _finding(obs="two", loc="y.py")
        result = consolidate([a, b])
        self.assertEqual(len(result), 2)

    def test_empty_input_returns_empty(self):
        self.assertEqual(consolidate([]), ())


class TestPulseSweepOnRealRepo(unittest.TestCase):
    """Runs against the real repository root — a genuine, not synthetic, check."""

    def test_returns_health_report(self):
        report = pulse_sweep(REPO_ROOT)
        self.assertIsInstance(report.findings, tuple)
        self.assertGreaterEqual(report.raw_finding_count, 0)

    def test_no_python_syntax_errors_in_this_repo(self):
        report = pulse_sweep(REPO_ROOT)
        syntax_findings = [f for f in report.findings if "syntax error" in f.observation]
        self.assertEqual(syntax_findings, [], f"unexpected syntax errors: {syntax_findings}")

    def test_claude_md_imports_all_resolve(self):
        report = pulse_sweep(REPO_ROOT)
        missing = [f for f in report.findings if "@-imports a missing file" in f.observation]
        self.assertEqual(missing, [], f"broken @-imports: {missing}")

    def test_finds_subsystems_missing_build_report(self):
        # Real, known finding at time of writing: schema/, firewall/,
        # narrative/ have no BUILD_REPORT.md. This asserts the check
        # actually surfaces it, not just that it runs without crashing.
        report = pulse_sweep(REPO_ROOT)
        missing_names = {
            f.evidence_location.rsplit("/", 1)[-1]
            for f in report.findings
            if "has no BUILD_REPORT.md" in f.observation
        }
        self.assertTrue(missing_names, "expected at least one subsystem missing BUILD_REPORT.md")


class TestPulseSweepOnSyntheticRepo(unittest.TestCase):
    def test_syntax_error_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "broken.py").write_text("def f(:\n    pass\n")
            report = pulse_sweep(root)
            observations = [f.observation for f in report.findings]
            self.assertTrue(any("syntax error" in o for o in observations))

    def test_missing_evidence_location_never_produced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = pulse_sweep(root)
            for f in report.findings:
                self.assertTrue(f.evidence_location)

    def test_empty_synthetic_repo_produces_compact_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = pulse_sweep(Path(tmp))
            self.assertFalse(report.compacted)

    def test_duplicate_frontier_ids_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "PARETO_FRONTIER.md").write_text(
                "### FRONTIER-001 — a\n\n### FRONTIER-001 — b (duplicate)\n"
            )
            report = pulse_sweep(root)
            dupes = [f for f in report.findings if "duplicate frontier id" in f.observation]
            self.assertEqual(len(dupes), 1)


class TestCT141Compaction(unittest.TestCase):
    def test_high_finding_volume_triggers_compaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # One broken python file per byte over the threshold, all distinct
            # locations so consolidate() cannot collapse them.
            for i in range(COMPACTION_THRESHOLD + 5):
                (root / f"broken_{i}.py").write_text("def f(:\n")
            report = pulse_sweep(root)
            self.assertTrue(report.compacted)
            self.assertLessEqual(len(report.findings), COMPACTION_THRESHOLD)
            self.assertGreater(report.raw_finding_count, COMPACTION_THRESHOLD)

    def test_low_finding_volume_not_compacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "broken.py").write_text("def f(:\n")
            report = pulse_sweep(root)
            self.assertFalse(report.compacted)


class TestFourPaths(unittest.TestCase):
    def _proposal(self, name="LEVER"):
        return PathProposal(
            name=name, purpose="do X", why_now="because Y", expected_benefit="Z",
            cost="low", evidence="observed W", scope="foundation/",
            success_criteria="tests pass", stop_condition="on merge",
        )

    def test_all_four_present_formats_without_error(self):
        paths = FourPaths(
            lever=self._proposal("LEVER"), foundation=self._proposal("FOUNDATION"),
            reality=self._proposal("REALITY"), compaction=self._proposal("COMPACTION"),
            recommended="LEVER", why_this_one="highest leverage",
        )
        text = format_four_paths(paths)
        self.assertIn("FOUR PATHS OF EVOLUTION", text)
        self.assertIn("do X", text)

    def test_weak_path_may_be_absent(self):
        paths = FourPaths(lever=self._proposal("LEVER"), foundation=None, reality=None, compaction=None)
        text = format_four_paths(paths)
        self.assertIn("NO STRONG PATH IDENTIFIED", text)

    def test_cannot_recommend_a_path_with_no_proposal(self):
        with self.assertRaises(ValueError):
            FourPaths(lever=None, foundation=None, reality=None, compaction=None, recommended="LEVER")

    def test_recommending_none_is_allowed(self):
        paths = FourPaths(lever=None, foundation=None, reality=None, compaction=None, recommended=None)
        self.assertIsNone(paths.recommended)

    def test_all_four_absent_is_valid(self):
        paths = FourPaths(lever=None, foundation=None, reality=None, compaction=None)
        text = format_four_paths(paths)
        self.assertEqual(text.count("NO STRONG PATH IDENTIFIED"), 4)


if __name__ == "__main__":
    unittest.main()
