import inspect
import json
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
        # As of 2026-08-25 all eight subsystems have a BUILD_REPORT.md
        # (schema/firewall/narrative were the last three, closed the same
        # day this test's synthetic sibling below was added) — so the
        # real-repo assertion here is now that the check finds NOTHING
        # missing, not that it finds something. The check's actual
        # detection behaviour is proven against a synthetic repo instead
        # (test_check_surfaces_a_missing_build_report below), which does
        # not go stale every time this repository's own state improves.
        report = pulse_sweep(REPO_ROOT)
        missing_names = {
            f.evidence_location.rsplit("/", 1)[-1]
            for f in report.findings
            if "has no BUILD_REPORT.md" in f.observation
        }
        self.assertEqual(missing_names, set())

    def test_check_surfaces_a_missing_build_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "schema").mkdir()
            # No BUILD_REPORT.md written for it.
            report = pulse_sweep(root)
            missing = [f for f in report.findings if "has no BUILD_REPORT.md" in f.observation]
            self.assertEqual(len(missing), 1)
            self.assertIn("schema", missing[0].evidence_location)


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


class TestReadPulseContinuity(unittest.TestCase):
    def _repo(self, tmp_path):
        (tmp_path / "foundation").mkdir()
        return tmp_path

    def test_missing_log_fails_soft(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            result = sentinel.read_pulse_continuity(repo)
            self.assertFalse(result.available)
            self.assertEqual(result.records_considered, 0)
            self.assertIn("never run", result.warnings[0])

    def test_empty_log_is_valid_zero_state(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            (repo / "foundation" / "pulse_log.jsonl").write_text("")
            result = sentinel.read_pulse_continuity(repo)
            self.assertTrue(result.available)
            self.assertEqual(result.records_considered, 0)
            self.assertEqual(result.meaningful_findings, ())

    def test_normal_log_surfaces_recent_evidence(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            rec = {
                "timestamp": "2026-08-27T00:00:00+00:00",
                "raw_finding_count": 1,
                "compacted": False,
                "findings": [{
                    "observation": "x", "evidence_location": "y",
                    "confidence": "HIGH", "interpretation": "i",
                    "reversibility": "r", "recommended_next_action": "n",
                }],
            }
            (repo / "foundation" / "pulse_log.jsonl").write_text(json.dumps(rec) + "\n")
            from datetime import datetime, timezone
            result = sentinel.read_pulse_continuity(
                repo, now=datetime(2026, 8, 27, 0, 0, 0, tzinfo=timezone.utc)
            )
            self.assertTrue(result.available)
            self.assertEqual(result.latest_timestamp, "2026-08-27T00:00:00+00:00")
            self.assertEqual(result.records_considered, 1)
            self.assertEqual(len(result.meaningful_findings), 1)
            self.assertEqual(result.warnings, ())
            self.assertFalse(result.stale)

    def test_malformed_json_line_skipped_not_fatal(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            good = {
                "timestamp": "2026-08-27T00:00:00+00:00",
                "raw_finding_count": 0, "compacted": False, "findings": [],
            }
            (repo / "foundation" / "pulse_log.jsonl").write_text(
                "{not valid json\n" + json.dumps(good) + "\n"
            )
            from datetime import datetime, timezone
            result = sentinel.read_pulse_continuity(
                repo, now=datetime(2026, 8, 27, 0, 0, 0, tzinfo=timezone.utc)
            )
            self.assertTrue(result.available)
            self.assertEqual(result.records_considered, 1)
            self.assertEqual(len(result.warnings), 1)
            self.assertIn("malformed JSON", result.warnings[0])

    def test_malformed_finding_skipped_not_fatal(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            rec = {
                "timestamp": "t", "raw_finding_count": 1, "compacted": False,
                "findings": [{"observation": "missing required fields"}],
            }
            (repo / "foundation" / "pulse_log.jsonl").write_text(json.dumps(rec) + "\n")
            result = sentinel.read_pulse_continuity(repo)
            self.assertTrue(result.available)
            self.assertEqual(result.meaningful_findings, ())
            self.assertTrue(any("malformed finding" in w for w in result.warnings))

    def test_repeated_calls_do_not_mutate_the_log(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            log = repo / "foundation" / "pulse_log.jsonl"
            rec = {"timestamp": "t", "raw_finding_count": 0, "compacted": False, "findings": []}
            log.write_text(json.dumps(rec) + "\n")
            before = log.read_text()
            sentinel.read_pulse_continuity(repo)
            sentinel.read_pulse_continuity(repo)
            sentinel.read_pulse_continuity(repo)
            self.assertEqual(log.read_text(), before)

    def test_large_log_is_bounded(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            log = repo / "foundation" / "pulse_log.jsonl"
            lines = []
            for i in range(500):
                lines.append(json.dumps({
                    "timestamp": f"t{i}", "raw_finding_count": 0,
                    "compacted": False, "findings": [],
                }))
            log.write_text("\n".join(lines) + "\n")
            result = sentinel.read_pulse_continuity(repo, max_records=20)
            self.assertEqual(result.records_considered, 20)
            self.assertEqual(result.latest_timestamp, "t499")

    def test_dedupes_meaningful_findings_across_records(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            finding = {
                "observation": "same", "evidence_location": "same",
                "confidence": "HIGH", "interpretation": "i",
                "reversibility": "r", "recommended_next_action": "n",
            }
            rec1 = {"timestamp": "t1", "raw_finding_count": 1, "compacted": False, "findings": [finding]}
            rec2 = {"timestamp": "t2", "raw_finding_count": 1, "compacted": False, "findings": [finding]}
            (repo / "foundation" / "pulse_log.jsonl").write_text(
                json.dumps(rec1) + "\n" + json.dumps(rec2) + "\n"
            )
            result = sentinel.read_pulse_continuity(repo)
            self.assertEqual(len(result.meaningful_findings), 1)

    def test_real_pulse_log_in_this_repo_is_readable(self):
        # Whatever real state cron_pulse.py has left in this actual repo
        # must parse without raising — the strongest available proof that
        # this works against the real log format, not just a synthetic one.
        result = sentinel.read_pulse_continuity(REPO_ROOT)
        self.assertTrue(result.available)

    def test_fresh_pulse_is_not_stale(self):
        import tempfile
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            now = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
            rec = {
                "timestamp": "2026-08-27T11:30:00+00:00",
                "raw_finding_count": 0, "compacted": False, "findings": [],
            }
            (repo / "foundation" / "pulse_log.jsonl").write_text(json.dumps(rec) + "\n")
            result = sentinel.read_pulse_continuity(repo, now=now)
            self.assertFalse(result.stale)
            self.assertEqual(result.warnings, ())

    def test_old_pulse_is_flagged_stale(self):
        import tempfile
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            now = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
            rec = {
                "timestamp": "2026-08-27T00:00:00+00:00",  # 12h old, threshold is 3h
                "raw_finding_count": 0, "compacted": False, "findings": [],
            }
            (repo / "foundation" / "pulse_log.jsonl").write_text(json.dumps(rec) + "\n")
            result = sentinel.read_pulse_continuity(repo, now=now)
            self.assertTrue(result.stale)
            self.assertEqual(len(result.warnings), 1)
            self.assertIn("stale", result.warnings[0])

    def test_boundary_just_under_threshold_is_not_stale(self):
        import tempfile
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            now = datetime(2026, 8, 27, 3, 0, 0, tzinfo=timezone.utc)
            rec = {
                "timestamp": "2026-08-27T00:00:00+00:00",  # exactly 3h before `now`
                "raw_finding_count": 0, "compacted": False, "findings": [],
            }
            (repo / "foundation" / "pulse_log.jsonl").write_text(json.dumps(rec) + "\n")
            result = sentinel.read_pulse_continuity(repo, now=now)
            self.assertFalse(result.stale)  # exactly 3h == threshold, not > threshold

    def test_unparseable_timestamp_does_not_crash_and_is_not_marked_stale(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(Path(d))
            rec = {
                "timestamp": "not-a-real-timestamp",
                "raw_finding_count": 0, "compacted": False, "findings": [],
            }
            (repo / "foundation" / "pulse_log.jsonl").write_text(json.dumps(rec) + "\n")
            result = sentinel.read_pulse_continuity(repo)
            self.assertFalse(result.stale)
            self.assertTrue(any("could not be parsed" in w for w in result.warnings))

    def test_real_pulse_log_staleness_is_computable_without_crashing(self):
        # Contradiction check (§VI): does adding staleness detection to a
        # bounded read-only report accidentally create a new failure mode
        # against the real, currently-healthy log? It must not raise.
        result = sentinel.read_pulse_continuity(REPO_ROOT)
        self.assertIn(result.stale, (True, False))


class TestClassifyHold(unittest.TestCase):
    def test_authority_wins_over_everything_else(self):
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            discovery_authorized=True, budget_exhausted=True,
            authority_required=True,
        )
        self.assertEqual(result, "AUTHORITY_HOLD")

    def test_budget_wins_over_blocked_and_input_starved(self):
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            budget_exhausted=True, blocked_reason="waiting on X",
        )
        self.assertEqual(result, "BUDGET_HOLD")

    def test_named_blocker_is_blocked_hold(self):
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            blocked_reason="F-007 git history contamination unresolved",
        )
        self.assertEqual(result, "BLOCKED_HOLD")

    def test_no_objective_is_terminal_hold(self):
        result = sentinel.classify_hold(
            has_concrete_objective=False, internal_levers_exhausted=True,
        )
        self.assertEqual(result, "TERMINAL_HOLD")

    def test_no_objective_wins_even_if_levers_not_exhausted(self):
        # nothing is being sought, so whether levers are exhausted is moot
        result = sentinel.classify_hold(
            has_concrete_objective=False, internal_levers_exhausted=False,
        )
        self.assertEqual(result, "TERMINAL_HOLD")

    def test_objective_plus_exhausted_levers_plus_no_discovery_is_input_starved(self):
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            discovery_authorized=False,
        )
        self.assertEqual(result, "INPUT_STARVED_HOLD")

    def test_objective_but_levers_not_exhausted_is_not_a_hold_state(self):
        with self.assertRaises(ValueError):
            sentinel.classify_hold(
                has_concrete_objective=True, internal_levers_exhausted=False,
            )

    def test_discovery_authorized_and_exhausted_is_not_a_hold_state(self):
        # this is the trigger condition for a bounded discovery attempt,
        # not a HOLD — classify_hold refuses to mislabel it
        with self.assertRaises(ValueError):
            sentinel.classify_hold(
                has_concrete_objective=True, internal_levers_exhausted=True,
                discovery_authorized=True,
            )

    def test_result_is_always_a_declared_hold_class(self):
        for kwargs in (
            {"has_concrete_objective": True, "internal_levers_exhausted": True, "authority_required": True},
            {"has_concrete_objective": True, "internal_levers_exhausted": True, "budget_exhausted": True},
            {"has_concrete_objective": True, "internal_levers_exhausted": True, "blocked_reason": "x"},
            {"has_concrete_objective": False, "internal_levers_exhausted": True},
            {"has_concrete_objective": True, "internal_levers_exhausted": True},
            {"has_concrete_objective": True, "internal_levers_exhausted": True, "awaiting_external_signal": True},
        ):
            self.assertIn(sentinel.classify_hold(**kwargs), sentinel.HOLD_CLASSES)

    def test_awaiting_external_signal_is_signal_wait_hold(self):
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            awaiting_external_signal=True,
        )
        self.assertEqual(result, "SIGNAL_WAIT_HOLD")

    def test_signal_wait_beats_terminal_even_with_no_objective(self):
        # a live channel with nobody home yet is not "nothing being
        # sought" -- engagement IS being sought, just not by discovery
        result = sentinel.classify_hold(
            has_concrete_objective=False, internal_levers_exhausted=True,
            awaiting_external_signal=True,
        )
        self.assertEqual(result, "SIGNAL_WAIT_HOLD")

    def test_authority_beats_signal_wait(self):
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            awaiting_external_signal=True, authority_required=True,
        )
        self.assertEqual(result, "AUTHORITY_HOLD")

    def test_blocked_beats_signal_wait(self):
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            awaiting_external_signal=True, blocked_reason="waiting on X",
        )
        self.assertEqual(result, "BLOCKED_HOLD")

    def test_signal_wait_beats_input_starved(self):
        # waiting for a person is not a discovery objective, even though
        # both share "levers exhausted, discovery not authorized"
        result = sentinel.classify_hold(
            has_concrete_objective=True, internal_levers_exhausted=True,
            awaiting_external_signal=True, discovery_authorized=False,
        )
        self.assertEqual(result, "SIGNAL_WAIT_HOLD")


if __name__ == "__main__":
    unittest.main()
