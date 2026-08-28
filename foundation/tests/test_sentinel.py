import inspect
import json
import os
import re
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

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
        # foundation/pulse_log.jsonl is cron_pulse.py's real, machine-local
        # output (gitignored -- not shipped with the repo). A fresh
        # checkout correctly reports available=False ("never fired yet");
        # asserting available=True unconditionally was a real bug that
        # only worked by accident on a machine with real cron history and
        # failed on a fresh CI checkout (caught 2026-08-27 on the real
        # push). This proves read_pulse_continuity() doesn't crash against
        # whichever real state this checkout has, matching the same
        # tolerant pattern test_real_pulse_log_staleness_is_computable_
        # without_crashing already uses below.
        result = sentinel.read_pulse_continuity(REPO_ROOT)
        self.assertIn(result.available, (True, False))

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


class TestOneCheckFailureNeverSinksTheWholeSweep(unittest.TestCase):
    """Fresh hunt-surface rotation 2026-08-28: pulse_sweep() called every
    check bare, in sequence, with no isolation. Several checks call
    .read_text() with no guard -- one undecodable byte or one
    permission-denied file in CLAUDE.md/README.md/PARETO_FRONTIER.md
    crashed the ENTIRE hourly sweep, losing every finding from every
    check that tick. Worse blast radius than the mouth-log crash class
    fixed earlier this chain (which only lost mouth-related findings)."""

    def test_undecodable_bytes_do_not_crash_the_sweep(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "CLAUDE.md").write_bytes(b"\xff\xfe garbage")
            report = sentinel.pulse_sweep(repo)  # must not raise
            self.assertTrue(any(
                "Level-1 check" in f.observation and "failed to run" in f.observation
                for f in report.findings
            ))

    def test_a_permission_denied_file_does_not_crash_the_sweep(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            path = repo / "CLAUDE.md"
            path.write_text("@nonexistent.md\n")
            os.chmod(path, 0o000)
            # No addCleanup chmod: it would fire after the TemporaryDirectory
            # is gone. The containing dir stays writable, so teardown works
            # regardless of this file's own mode.
            report = sentinel.pulse_sweep(repo)
            self.assertTrue(any("failed to run" in f.observation for f in report.findings))

    def test_other_checks_still_produce_their_real_findings(self):
        """The actual point: a broken CLAUDE.md must not silence an
        unrelated real defect elsewhere, like a genuine Python syntax
        error."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "CLAUDE.md").write_bytes(b"\xff\xfe garbage")
            (repo / "broken.py").write_text("def f(:\n    pass\n")
            report = sentinel.pulse_sweep(repo)
            self.assertTrue(any("syntax error" in f.observation for f in report.findings))
            self.assertTrue(any("failed to run" in f.observation for f in report.findings))

    def test_the_failure_finding_key_is_stable_across_different_exception_messages(self):
        """The exception message (which can vary -- byte offsets, etc.)
        must live in interpretation, never in the dedupe key."""
        f1 = sentinel._run_check_safely(
            lambda r: (_ for _ in ()).throw(ValueError("message A")), Path("/x"))[0]
        f2 = sentinel._run_check_safely(
            lambda r: (_ for _ in ()).throw(ValueError("message B, totally different")), Path("/x"))[0]
        # Different callables (lambdas) legitimately get different names in
        # a real scenario every check is a distinct named function, so
        # compare the shape: observation never contains the message.
        self.assertNotIn("message A", f1.observation)
        self.assertNotIn("message B", f2.observation)
        self.assertIn("message A", f1.interpretation)

    def test_a_healthy_repo_is_unaffected(self):
        report = sentinel.pulse_sweep(REPO_ROOT)
        self.assertFalse(any("failed to run" in f.observation for f in report.findings))


class TestMouthHealthSensor(unittest.TestCase):
    """The blind spot, reproduced before it was closed: five consecutive
    UNAVAILABLE mouth observations produced ZERO mouth-related findings,
    so the hourly sweep reported raw_finding_count=0 -- indistinguishable
    from perfect health -- while the organism's only sensory organ was
    dead. Silent sensory loss reported as health."""

    def _log(self, repo, mouth_id, statuses, now=None, spacing_hours=1):
        now = now or datetime.now(timezone.utc)
        (repo / "foundation").mkdir(exist_ok=True)
        path = repo / "foundation" / f"mouth_{mouth_id}_log.jsonl"
        n = len(statuses)
        path.write_text("\n".join(json.dumps({
            "mouth_id": mouth_id,
            "observed_at": (now - timedelta(hours=(n - i) * spacing_hours)).isoformat(),
            "status": s, "content_hash": None, "item_count": 0, "new_items": [],
            "error": "name resolution failure" if s == "UNAVAILABLE" else None,
        }) for i, s in enumerate(statuses)) + "\n")
        return path

    def test_a_persistent_failure_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self._log(repo, "pypi_pyyaml_releases", ["UNAVAILABLE"] * 5)
            findings = sentinel.check_mouth_health(repo)
            self.assertEqual(len(findings), 1)
            self.assertIn("persistent fetch failure", findings[0].observation)
            self.assertEqual(findings[0].confidence, "HIGH")

    def test_a_single_transient_blip_is_not_reported(self):
        """The false-positive bound: one failed fetch is normal network
        variation, and prior state is preserved untouched by design."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self._log(repo, "pypi_pyyaml_releases", ["UNCHANGED", "UNCHANGED", "UNAVAILABLE", "UNCHANGED"])
            self.assertEqual(sentinel.check_mouth_health(repo), [])

    def test_a_failure_that_recovered_is_not_reported(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self._log(repo, "pypi_pyyaml_releases", ["UNAVAILABLE", "UNAVAILABLE", "UNCHANGED"])
            self.assertEqual(sentinel.check_mouth_health(repo), [])

    def test_healthy_mouths_produce_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self._log(repo, "pypi_pyyaml_releases", ["UNCHANGED"] * 5)
            self._log(repo, "github_pyyaml_releases", ["UNCHANGED"] * 5)
            self.assertEqual(sentinel.check_mouth_health(repo), [])

    def test_the_finding_is_stable_so_it_dedupes_across_ticks(self):
        """A streak counter in the observation would change Finding.key()
        every tick and spam the boot report."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self._log(repo, "pypi_pyyaml_releases", ["UNAVAILABLE"] * 2)
            first = sentinel.check_mouth_health(repo)[0]
            self._log(repo, "pypi_pyyaml_releases", ["UNAVAILABLE"] * 9)
            later = sentinel.check_mouth_health(repo)[0]
            self.assertEqual(first.key(), later.key())
            self.assertEqual(len(consolidate([first, later])), 1)

    def test_a_stopped_clock_is_distinct_from_a_failing_fetch(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            # Healthy statuses, but the newest record is days old.
            self._log(repo, "pypi_pyyaml_releases", ["UNCHANGED"] * 3,
                      now=datetime.now(timezone.utc) - timedelta(days=3))
            findings = sentinel.check_mouth_health(repo)
            self.assertEqual(len(findings), 1)
            self.assertIn("stopped writing", findings[0].observation)
            self.assertIn("cron", findings[0].interpretation)

    def test_a_missing_log_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "foundation").mkdir()
            self.assertEqual(sentinel.check_mouth_health(Path(d)), [])

    def test_malformed_lines_do_not_crash_the_sensor(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            path = self._log(repo, "pypi_pyyaml_releases", ["UNAVAILABLE"] * 2)
            path.write_text(path.read_text() + '{"truncated": \n')
            self.assertEqual(len(sentinel.check_mouth_health(repo)), 1)

    def test_the_orphan_log_is_not_globbed_and_reported_forever(self):
        """foundation/mouth_pypi_log.jsonl is a real orphan from an older
        MOUTH_ID naming. A glob would report it stale eternally with no
        remedy but deletion -- a static fact re-reported forever."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "mouth_pypi_log.jsonl").write_text(json.dumps({
                "mouth_id": "pypi", "observed_at": "2026-01-01T00:00:00+00:00",
                "status": "UNCHANGED"}) + "\n")
            self.assertEqual(sentinel.check_mouth_health(repo), [])

    def test_it_is_wired_into_the_hourly_sweep(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            self._log(repo, "pypi_pyyaml_releases", ["UNAVAILABLE"] * 3)
            report = sentinel.pulse_sweep(repo)
            self.assertTrue(any("persistent fetch failure" in f.observation
                                for f in report.findings),
                            "the live cron would never run this sensor")

    def test_the_real_repository_mouths_are_currently_healthy(self):
        self.assertEqual(sentinel.check_mouth_health(REPO_ROOT), [])

    def test_the_sensor_writes_nothing(self):
        path = REPO_ROOT / "foundation" / "mouth_pypi_pyyaml_releases_log.jsonl"
        before = path.stat().st_mtime_ns
        sentinel.check_mouth_health(REPO_ROOT)
        self.assertEqual(path.stat().st_mtime_ns, before)


class TestReadPulseContinuitySurvivesNonDictLines(unittest.TestCase):
    """Systemic hunt 2026-08-28: the same class of bug fixed once in
    check_mouth_health() (a valid-JSON non-dict line crashing `.get()`)
    was unsearched in the CENTRAL consumer every sensor on the conveyor
    feeds through /boot. One malformed line anywhere would have taken
    down the whole boot report, not just one check's findings."""

    def test_a_non_dict_line_does_not_crash_and_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "pulse_log.jsonl").write_text('42\n"str"\n[1,2]\nnull\n')
            result = sentinel.read_pulse_continuity(repo)
            self.assertEqual(result.records_considered, 0)
            self.assertTrue(any("not an object" in w for w in result.warnings))

    def test_a_real_record_still_parses_when_mixed_with_junk(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "pulse_log.jsonl").write_text(
                '99\n' + json.dumps({
                    "timestamp": "2026-08-27T00:00:00+00:00",
                    "raw_finding_count": 0, "compacted": False, "findings": [],
                }) + '\n')
            result = sentinel.read_pulse_continuity(repo)
            self.assertEqual(result.records_considered, 1)


class TestReadmeTestCountDriftCheck(unittest.TestCase):
    """The most-repeated stale-claim class in this repository's history,
    finally given a mechanical detector. Corrected by hand at least twice
    for README alone (`cdce3df`, whose own message says "second real
    drift instance found"), plus CAPABILITY_MANIFEST.json (`f75a418`),
    CLAUDE.md's sigil paragraph, and two BUILD_REPORTs (`8c6e18f`,
    `289c2e1`) -- every one caught by a human recounting by hand."""

    def _repo(self, d, readme_text, n_tests=0):
        repo = Path(d)
        tests_dir = repo / "sub" / "tests"
        tests_dir.mkdir(parents=True)
        (repo / "README.md").write_text(readme_text)
        body = "\n".join(f"    def test_thing_{i}(self):\n        pass" for i in range(n_tests))
        (tests_dir / "test_x.py").write_text("class T:\n" + (body or "    pass"))
        return repo

    def test_a_drifted_claim_is_detected_with_the_real_delta(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, "**1,461 tests across 9 subsystems**", n_tests=3)
            findings = sentinel.check_readme_test_count(repo)
            self.assertEqual(len(findings), 1)
            # The numbers live in `interpretation`, NOT `observation` --
            # observation must stay stable so Finding.key() dedupes a
            # persisting condition instead of spamming /boot.
            self.assertIn("1,461", findings[0].interpretation)
            self.assertIn("3", findings[0].interpretation)
            self.assertNotIn("1,461", findings[0].observation)
            self.assertEqual(findings[0].confidence, "HIGH")

    def test_an_accurate_claim_produces_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, "**3 tests across 1 subsystems**", n_tests=3)
            self.assertEqual(sentinel.check_readme_test_count(repo), [])

    def test_a_readme_with_no_such_claim_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, "# A README with no test-count claim at all", n_tests=3)
            self.assertEqual(sentinel.check_readme_test_count(repo), [])

    def test_a_missing_readme_is_not_a_finding_from_this_check(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sentinel.check_readme_test_count(Path(d)), [])

    def test_count_real_tests_skips_excluded_directories(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, "**3 tests across 1 subsystems**", n_tests=3)
            junk = repo / "__pycache__"
            junk.mkdir()
            (junk / "test_cached.py").write_text("def test_ghost():\n    pass\n")
            self.assertEqual(sentinel.count_real_tests(repo), 3)

    def test_the_check_is_wired_into_the_hourly_sweep(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, "**9,999 tests across 9 subsystems**", n_tests=2)
            report = sentinel.pulse_sweep(repo)
            self.assertTrue(
                any("declared test count disagrees" in f.observation
                    for f in report.findings),
                "drift check is not reachable from pulse_sweep -- the live cron would never run it",
            )
            self.assertTrue(any("9,999" in f.interpretation for f in report.findings))

    def test_it_is_read_only_against_the_real_repository(self):
        readme = REPO_ROOT / "README.md"
        before = readme.stat().st_mtime_ns
        sentinel.check_readme_test_count(REPO_ROOT)
        sentinel.count_real_tests(REPO_ROOT)
        self.assertEqual(readme.stat().st_mtime_ns, before)


class TestSigilSnapshotAgreementCheck(unittest.TestCase):
    """Second member of the drift family, and the exact historical case:
    CLAUDE.md carried TIER:T7 | REALITY:10 after SIGIL.md had recorded the
    real evidenced drop to TIER:T3 | REALITY:6. A session booting off the
    stale snapshot orients from a capability index four tiers too high."""

    T3 = ("TIER:T3 | IRON:10 | LATTICE:6 | PROOF:10 | SIGHT:10 | "
          "FRONTIER:10 | ORCH:10 | MEMORY:10 | REALITY:6")
    T7 = ("TIER:T7 | IRON:10 | LATTICE:6 | PROOF:10 | SIGHT:10 | "
          "FRONTIER:10 | ORCH:10 | MEMORY:10 | REALITY:10")

    def _repo(self, d, claude=None, sigil=None):
        repo = Path(d)
        if claude is not None:
            (repo / "CLAUDE.md").write_text(f"# Doctrine\n\nsome prose\n\n{claude}\n\nmore\n")
        if sigil is not None:
            (repo / "SIGIL.md").write_text(f"# Capability Sigil\n\n```\n{sigil}\n```\n")
        return repo

    def test_the_real_historical_divergence_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, claude=self.T7, sigil=self.T3)
            findings = sentinel.check_sigil_snapshot_agreement(repo)
            self.assertEqual(len(findings), 1)
            self.assertIn("tier", findings[0].observation)
            self.assertIn("reality", findings[0].observation)
            self.assertEqual(findings[0].confidence, "HIGH")

    def test_agreeing_snapshots_produce_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, claude=self.T3, sigil=self.T3)
            self.assertEqual(sentinel.check_sigil_snapshot_agreement(repo), [])

    def test_it_never_claims_which_document_is_correct(self):
        """Load-bearing honesty: neither file is ground truth, and the
        finding must route to compute_sigil() rather than to 'fix the
        other file to match'."""
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, claude=self.T7, sigil=self.T3)
            f = sentinel.check_sigil_snapshot_agreement(repo)[0]
            self.assertIn("cannot say", f.interpretation)
            self.assertIn("compute_sigil", f.interpretation)
            self.assertIn("never reconcile the two documents to each other",
                          f.recommended_next_action)

    def test_a_single_snapshot_has_nothing_to_disagree_with(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(
                sentinel.check_sigil_snapshot_agreement(self._repo(d, sigil=self.T3)), [])

    def test_missing_files_are_not_a_finding_from_this_check(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sentinel.check_sigil_snapshot_agreement(Path(d)), [])

    def test_a_partial_sigil_line_in_prose_is_not_mistaken_for_a_snapshot(self):
        """CLAUDE.md really does contain the string 'TIER:T7 | REALITY:10'
        inside its own correction narrative. parse_sigil() fails closed on
        a partial line, so the prose mention must not be read as a
        competing snapshot -- otherwise this check would fire forever on a
        file that is actually correct."""
        with tempfile.TemporaryDirectory() as d:
            narrative = ("the paragraph said `TIER:T7 | REALITY:10` after SIGIL.md "
                         "had already documented the drop\n\n" + self.T3)
            repo = self._repo(d, claude=narrative, sigil=self.T3)
            self.assertEqual(sentinel.check_sigil_snapshot_agreement(repo), [])

    def test_it_is_wired_into_the_hourly_sweep(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, claude=self.T7, sigil=self.T3)
            report = sentinel.pulse_sweep(repo)
            self.assertTrue(any("snapshots disagree" in f.observation for f in report.findings))

    def test_the_real_repository_snapshots_currently_agree(self):
        # Not a fixture: CLAUDE.md and SIGIL.md as they actually are.
        self.assertEqual(sentinel.check_sigil_snapshot_agreement(REPO_ROOT), [])

    def test_the_check_writes_nothing(self):
        before = [(p, (REPO_ROOT / p).stat().st_mtime_ns) for p in ("CLAUDE.md", "SIGIL.md")]
        sentinel.check_sigil_snapshot_agreement(REPO_ROOT)
        for name, mtime in before:
            self.assertEqual((REPO_ROOT / name).stat().st_mtime_ns, mtime)


class TestFindingKeyStabilityUnderPersistingConditions(unittest.TestCase):
    """Adversarial review 2026-08-28 found a HIGH defect in
    check_readme_test_count(): the observation interpolated the live count
    and the delta, so Finding.key() changed on every tick where the real
    test count moved while README stayed stale -- exactly the normal
    development lag the check's own text calls expected. Reproduced: three
    ticks of ONE persisting condition produced THREE distinct keys, which
    spams /boot instead of deduping.

    This is the single most important property of every sensor feeding the
    conveyor, so it is tested here for all three of them at once."""

    def test_readme_finding_key_is_stable_while_the_count_moves(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "sub" / "tests").mkdir(parents=True)
            (repo / "README.md").write_text("**500 tests across 9 subsystems**")
            keys = set()
            for n in (510, 511, 512, 900):
                with mock.patch.object(sentinel, "count_real_tests", return_value=n):
                    keys.add(sentinel.check_readme_test_count(repo)[0].key())
            self.assertEqual(len(keys), 1, "key changed while one condition persisted")

    def test_the_readme_numbers_are_still_reported_just_not_in_the_key(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "sub" / "tests").mkdir(parents=True)
            (repo / "README.md").write_text("**500 tests across 9 subsystems**")
            with mock.patch.object(sentinel, "count_real_tests", return_value=512):
                f = sentinel.check_readme_test_count(repo)[0]
            self.assertIn("500", f.interpretation)
            self.assertIn("512", f.interpretation)
            self.assertNotIn("512", f.observation)

    def test_every_sensor_dedupes_a_persisting_condition_to_one_finding(self):
        """Cross-sensor guard: a future check that embeds a varying number
        in its observation would fail here."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "sub" / "tests").mkdir(parents=True)
            (repo / "README.md").write_text("**500 tests across 9 subsystems**")
            now = datetime.now(timezone.utc)
            log = repo / "foundation" / "mouth_pypi_pyyaml_releases_log.jsonl"
            collected = []
            for n_records in (2, 5, 9):          # a failure streak that keeps growing
                log.write_text("\n".join(json.dumps({
                    "mouth_id": "pypi_pyyaml_releases",
                    "observed_at": (now - timedelta(hours=n_records - i)).isoformat(),
                    "status": "UNAVAILABLE", "error": "boom",
                }) for i in range(n_records)) + "\n")
                collected.extend(sentinel.check_mouth_health(repo))
                collected.extend(sentinel.check_readme_test_count(repo))
            # Two distinct real conditions, however many ticks observed them.
            self.assertEqual(len(consolidate(collected)), 2)


class TestSweepSurvivesMalformedRecords(unittest.TestCase):
    """A line can be valid JSON and still not be a record. Adversarial
    review 2026-08-28: `.get()` on a bare int raised AttributeError out of
    check_mouth_health AND out of pulse_sweep(), so one malformed byte in
    one mouth log disabled EVERY other check's findings for that tick."""

    def test_a_non_dict_json_line_does_not_crash_the_mouth_sensor(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "mouth_pypi_pyyaml_releases_log.jsonl").write_text(
                '42\n"not a dict"\n[1,2,3]\nnull\n')
            self.assertEqual(sentinel.check_mouth_health(repo), [])

    def test_a_non_dict_json_line_does_not_take_down_the_whole_sweep(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "mouth_pypi_pyyaml_releases_log.jsonl").write_text('42\n')
            report = sentinel.pulse_sweep(repo)   # must not raise
            self.assertIsInstance(report.raw_finding_count, int)

    def test_real_records_still_parse_when_mixed_with_junk(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            now = datetime.now(timezone.utc)
            good = [json.dumps({
                "mouth_id": "pypi_pyyaml_releases",
                "observed_at": (now - timedelta(hours=2 - i)).isoformat(),
                "status": "UNAVAILABLE", "error": "boom"}) for i in range(2)]
            (repo / "foundation" / "mouth_pypi_pyyaml_releases_log.jsonl").write_text(
                "99\n" + "\n".join(good) + "\n")
            self.assertEqual(len(sentinel.check_mouth_health(repo)), 1)


class TestFrontierHashPlaceholderCheck(unittest.TestCase):
    """The recurring class: PARETO_FRONTIER.md Archive rows carry a
    literal "(this commit)" hash placeholder pending backfill, and this
    repo's own history shows it repeatedly forgotten (5a9ca9f fixed one
    row, naming 4 prior occurrences). Confirmed live 2026-08-28: 7 real
    unresolved cells on disk, working tree matching HEAD exactly (not a
    mid-edit false positive)."""

    def _frontier(self, d, body):
        (Path(d) / "PARETO_FRONTIER.md").write_text(body)
        return Path(d)

    def test_a_real_placeholder_cell_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._frontier(d, "| FRONTIER-X | did a thing | (this commit) |\n")
            findings = sentinel.check_frontier_hash_placeholders(repo)
            self.assertEqual(len(findings), 1)
            self.assertIn("7", "7")  # placeholder assertion below is the real one
            self.assertIn("1 unresolved", findings[0].interpretation)

    def test_a_real_backfilled_hash_produces_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._frontier(d, "| FRONTIER-X | did a thing | `dd9a7fd` |\n")
            self.assertEqual(sentinel.check_frontier_hash_placeholders(repo), [])

    def test_a_prose_mention_of_the_phrase_is_not_a_false_positive(self):
        """The real bug found and fixed before shipping: PARETO_FRONTIER.md
        itself discusses this exact historical class using the phrase
        'their `(this commit)` tags were false' -- a bare substring count
        would double-count that discussion as a second live placeholder."""
        with tempfile.TemporaryDirectory() as d:
            repo = self._frontier(d, (
                "| FRONTIER-Y | fixed rows above (their `(this commit)` "
                "tags were false) | `dd9a7fd` |\n"
            ))
            self.assertEqual(sentinel.check_frontier_hash_placeholders(repo), [])

    def test_a_row_with_both_a_real_placeholder_and_a_prose_mention_counts_once(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._frontier(d, (
                "| FRONTIER-Z | discusses `(this commit)` in prose | (this commit) |\n"
            ))
            findings = sentinel.check_frontier_hash_placeholders(repo)
            self.assertEqual(len(findings), 1)
            self.assertIn("1 unresolved", findings[0].interpretation)

    def test_the_observation_is_stable_regardless_of_count(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._frontier(d, "| A | x | (this commit) |\n")
            key1 = sentinel.check_frontier_hash_placeholders(repo)[0].key()
            repo = self._frontier(d, "\n".join(
                f"| R{i} | x | (this commit) |" for i in range(5)))
            key2 = sentinel.check_frontier_hash_placeholders(repo)[0].key()
        self.assertEqual(key1, key2)

    def test_a_missing_file_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(sentinel.check_frontier_hash_placeholders(Path(d)), [])

    def test_it_is_wired_into_the_hourly_sweep(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._frontier(d, "| A | x | (this commit) |\n")
            report = sentinel.pulse_sweep(repo)
            self.assertTrue(any("Archive hash placeholder" in f.observation
                                for f in report.findings))

    def test_the_real_repository_is_now_clean(self):
        """Was `test_the_real_repository_currently_has_seven`, pinned to
        7 unresolved placeholders. Closed 2026-08-28 (FRONTIER-018,
        cycle demonblade_013): all 7 attributed to real commits via
        `git show`-verified diff evidence, none guessed. See
        PARETO_FRONTIER.md FRONTIER-018."""
        f = sentinel.check_frontier_hash_placeholders(REPO_ROOT)
        self.assertEqual(f, [])

    def test_it_writes_nothing(self):
        path = REPO_ROOT / "PARETO_FRONTIER.md"
        before = path.stat().st_mtime_ns
        sentinel.check_frontier_hash_placeholders(REPO_ROOT)
        self.assertEqual(path.stat().st_mtime_ns, before)
