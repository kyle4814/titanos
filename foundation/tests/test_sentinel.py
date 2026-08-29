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
    check_ci_matrix_coverage,
    check_subsystem_build_reports, has_substantive_build_report,
    SUBSYSTEMS_REQUIRING_BUILD_REPORT,
    check_protocol_document_targets,
    _LEVEL1_CHECKS,
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


class TestPulseContinuitySurfacesCompaction(unittest.TestCase):
    """Switch closed 2026-08-28. Every pulse record carries
    `raw_finding_count` and `compacted`; `PulseContinuity` carried
    neither, so a CT_141-throttled sweep of 45 findings truncated to 2
    was indistinguishable from an honest sweep of 2 to `/boot` step 4b —
    the only real consumer. The panic axiom engaging is precisely the
    thing a boot report must not swallow silently."""

    def _record(self, raw_count, compacted, n_findings, ts="2026-08-27T17:07:01+00:00"):
        return json.dumps({
            "timestamp": ts, "raw_finding_count": raw_count, "compacted": compacted,
            "findings": [{
                "observation": f"finding {i}", "evidence_location": f"loc{i}",
                "confidence": "HIGH", "interpretation": "x",
                "reversibility": "y", "recommended_next_action": "z",
            } for i in range(n_findings)],
        })

    def _repo_with(self, d, *records):
        repo = Path(d)
        (repo / "foundation").mkdir(exist_ok=True)
        (repo / "foundation" / "pulse_log.jsonl").write_text("\n".join(records) + "\n")
        return repo

    def test_a_compacted_sweep_is_no_longer_silent(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo_with(d, self._record(45, True, 2))
            r = sentinel.read_pulse_continuity(repo)
            self.assertTrue(r.compacted)
            self.assertEqual(r.raw_finding_count, 45)
            self.assertEqual(len(r.meaningful_findings), 2)
            self.assertEqual(r.truncated_findings, 43)
            self.assertTrue(any("CT_141-compacted" in w for w in r.warnings))

    def test_an_honest_small_sweep_is_not_flagged(self):
        # The discrimination that matters: 2 findings because there were
        # only 2 is a different state from 2 findings because 43 were cut.
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo_with(d, self._record(2, False, 2))
            r = sentinel.read_pulse_continuity(repo)
            self.assertFalse(r.compacted)
            self.assertEqual(r.raw_finding_count, 2)
            self.assertEqual(r.truncated_findings, 0)
            self.assertFalse(any("CT_141-compacted" in w for w in r.warnings))

    def test_compaction_earlier_in_the_window_is_not_hidden_by_a_clean_latest(self):
        # Reading only records[-1] would lose this — a throttle that fired
        # three ticks ago is still the most important thing in the window.
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo_with(
                d,
                self._record(45, True, 2, ts="2026-08-27T14:07:01+00:00"),
                self._record(0, False, 0, ts="2026-08-27T15:07:01+00:00"),
                self._record(0, False, 0, ts="2026-08-27T16:07:01+00:00"),
            )
            r = sentinel.read_pulse_continuity(repo)
            self.assertTrue(r.compacted)
            self.assertEqual(r.raw_finding_count, 45)

    def test_unparseable_raw_finding_count_is_warned_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "pulse_log.jsonl").write_text(json.dumps({
                "timestamp": "2026-08-27T17:07:01+00:00",
                "raw_finding_count": "not a number", "compacted": False, "findings": [],
            }) + "\n")
            r = sentinel.read_pulse_continuity(repo)
            self.assertEqual(r.raw_finding_count, 0)
            self.assertTrue(any("unparseable raw_finding_count" in w for w in r.warnings))

    def test_the_real_live_pulse_log_reports_a_clean_uncompacted_window(self):
        # Not a fixture: whatever the live hourly cron has actually written.
        r = sentinel.read_pulse_continuity(REPO_ROOT)
        if r.available and r.records_considered:
            self.assertIsInstance(r.compacted, bool)
            self.assertGreaterEqual(r.raw_finding_count, 0)
            self.assertGreaterEqual(r.truncated_findings, 0)


class TestReadCronStderr(unittest.TestCase):
    """Switch closed 2026-08-28. The live crontab entry redirects with
    `>> foundation/cron_pulse.err.log 2>&1`, making that file the only
    place a traceback lands if the one unattended process this repository
    runs dies. A grep across every .py and .md found zero readers: the
    machine could detect THAT the pulse stopped (read_pulse_continuity's
    stale warning) and never WHY."""

    def _repo(self, d, content=None):
        repo = Path(d)
        (repo / "foundation").mkdir(exist_ok=True)
        if content is not None:
            (repo / "foundation" / "cron_pulse.err.log").write_text(content)
        return repo

    def test_absent_is_not_a_failure_and_not_a_health_claim(self):
        with tempfile.TemporaryDirectory() as d:
            r = sentinel.read_cron_stderr(self._repo(d))
            self.assertFalse(r.available)
            self.assertFalse(r.failed)
            self.assertIn("fresh", r.warnings[0])
            self.assertIn("not evidence that the pulse is healthy", r.warnings[0])

    def test_empty_is_the_healthy_state_and_is_distinct_from_absent(self):
        with tempfile.TemporaryDirectory() as d:
            r = sentinel.read_cron_stderr(self._repo(d, ""))
            self.assertTrue(r.available)   # the redirect exists
            self.assertFalse(r.failed)     # and nothing has ever failed
            self.assertEqual(r.size_bytes, 0)
            self.assertEqual(r.warnings, ())

    def test_content_is_real_failure_evidence_and_is_retrievable(self):
        trace = (
            'Traceback (most recent call last):\n'
            '  File "foundation/cron_pulse.py", line 40, in <module>\n'
            '    from foundation.sentinel import pulse_sweep\n'
            'ModuleNotFoundError: No module named \'foundation.sentinel\'\n'
        )
        with tempfile.TemporaryDirectory() as d:
            r = sentinel.read_cron_stderr(self._repo(d, trace))
            self.assertTrue(r.available)
            self.assertTrue(r.failed)
            self.assertIn("ModuleNotFoundError", r.tail)
            self.assertIn("cron_pulse.py", r.tail)
            self.assertFalse(r.truncated)
            self.assertTrue(any("retrieval, not a diagnosis" in w for w in r.warnings))

    def test_a_crash_looping_process_cannot_flood_the_reader(self):
        # A process failing every hour appends forever; a boot sequence
        # must never read an unbounded file into memory.
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, "E" * 200_000)
            r = sentinel.read_cron_stderr(repo, tail_bytes=8192)
            self.assertTrue(r.failed)
            self.assertEqual(len(r.tail), 8192)
            self.assertTrue(r.truncated)
            self.assertEqual(r.size_bytes, 200_000)
            self.assertTrue(any("showing the trailing" in w for w in r.warnings))

    def test_undecodable_bytes_do_not_raise(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            (repo / "foundation").mkdir()
            (repo / "foundation" / "cron_pulse.err.log").write_bytes(b"\xff\xfe bad \xc3(")
            r = sentinel.read_cron_stderr(repo)
            self.assertTrue(r.failed)
            self.assertIsInstance(r.tail, str)

    def test_the_reader_never_writes_or_truncates_the_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            repo = self._repo(d, "boom\n")
            log = repo / "foundation" / "cron_pulse.err.log"
            before = log.stat().st_mtime_ns
            sentinel.read_cron_stderr(repo)
            sentinel.read_cron_stderr(repo)
            self.assertEqual(log.read_text(), "boom\n")
            self.assertEqual(log.stat().st_mtime_ns, before)

    def test_against_the_real_live_err_log(self):
        # Whatever state this machine's real cron entry has left it in.
        r = sentinel.read_cron_stderr(REPO_ROOT)
        self.assertIsInstance(r.available, bool)
        self.assertIsInstance(r.failed, bool)
        if not r.available:
            self.assertFalse(r.failed)


class TestCheckProtocolDocumentTargets(unittest.TestCase):
    """Clause 2 of the Consumer-Reality Contract (PARETO_FRONTIER.md
    FRONTIER-016): a callable named by a protocol document must resolve.

    Built 2026-08-28 (cycle demonblade_012) against a REPRODUCED defect:
    cycle demonblade_010 typo'd a documented function name in
    `.claude/commands/boot.md` and the whole suite stayed green. These
    tests replay that mutation and its neighbours.
    """

    def _repo(self, doc_text: str, module_text: str = "def real_one():\n    pass\n"):
        root = Path(self.tmp.name)
        (root / ".claude" / "commands").mkdir(parents=True, exist_ok=True)
        (root / "foundation").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "commands" / "boot.md").write_text(doc_text)
        (root / "foundation" / "widget.py").write_text(module_text)
        return root

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_real_repository_is_currently_clean(self):
        """Legitimate neighbours preserved: the 9 real qualified
        references in this repo's own command set must all resolve."""
        self.assertEqual(check_protocol_document_targets(REPO_ROOT), [])

    def test_typo_in_dotted_reference_is_caught(self):
        root = self._repo("call `foundation.widget.real_onee(x)` now")
        findings = check_protocol_document_targets(root)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].confidence, "HIGH")
        self.assertIn("real_onee", findings[0].observation)

    def test_typo_in_path_symbol_reference_is_caught(self):
        root = self._repo("run `foundation/widget.py::real_onee()`")
        self.assertEqual(len(check_protocol_document_targets(root)), 1)

    def test_missing_module_is_caught_and_distinguished(self):
        root = self._repo("call `foundation.gadget.real_one(x)`")
        findings = check_protocol_document_targets(root)
        self.assertEqual(len(findings), 1)
        self.assertIn("module file does not exist", findings[0].interpretation)

    def test_resolving_references_produce_no_finding(self):
        root = self._repo(
            "call `foundation.widget.real_one(x)` and "
            "`foundation/widget.py::real_one()`"
        )
        self.assertEqual(check_protocol_document_targets(root), [])

    def test_class_targets_resolve_too(self):
        root = self._repo("see `foundation.widget.Widget(x)`",
                          module_text="class Widget:\n    pass\n")
        self.assertEqual(check_protocol_document_targets(root), [])

    def test_bare_unqualified_call_is_not_guessed_at(self):
        """A bare `real_onee()` names no module. Matching it would mean
        guessing which module to resolve against — the declared scope
        limit, asserted so a future edit cannot silently widen it."""
        root = self._repo("then call `real_onee()` as documented")
        self.assertEqual(check_protocol_document_targets(root), [])

    def test_finding_key_is_stable_across_repeated_sweeps(self):
        """A persisting broken reference must not mint a new key every
        hour — the exact defect previously found in
        check_readme_test_count."""
        root = self._repo("call `foundation.widget.real_onee(x)`")
        keys = {f.key() for _ in range(3)
                for f in check_protocol_document_targets(root)}
        self.assertEqual(len(keys), 1)

    def test_missing_command_directory_is_not_a_finding(self):
        root = Path(self.tmp.name)
        (root / "foundation").mkdir(parents=True, exist_ok=True)
        self.assertEqual(check_protocol_document_targets(root), [])

    def test_wired_into_pulse_sweep(self):
        self.assertIn(check_protocol_document_targets, _LEVEL1_CHECKS)


class TestContinuationGovernor(unittest.TestCase):
    """The harness: formalises the difference between 'this board found
    nothing' and 'the accessible search space is exhausted', which every
    prior autonomous-cycle pass in this session decided in prose. Pure
    decision function -- executes nothing, SIGIL.NO_EXECUTION_AUTHORITY
    unaffected by construction (TestSentinelCannotExecute already scans
    every public callable in this module by name)."""

    def _swept(self, name):
        return sentinel.HuntSurface(name=name, status="SWEPT")

    def _blocked(self, name, evidence="stated reason"):
        return sentinel.HuntSurface(name=name, status="BLOCKED", evidence=evidence)

    def _deferred(self, name, wake="a named threshold crossing"):
        return sentinel.HuntSurface(
            name=name, status="DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION",
            evidence="deferred pending real pressure", reopen_condition=wake)

    def _unswept(self, name):
        return sentinel.HuntSurface(name=name, status="UNSWEPT")

    # TEST 1 — empty board does not imply stop
    def test_unswept_surface_forces_continue(self):
        surfaces = (self._swept("A"), self._blocked("B"), self._unswept("C"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertIn("C", d.unresolved_surfaces)

    # TEST 2 — a blocked item alone does not imply stop while another
    # eligible (unswept) surface remains
    def test_blocked_item_with_remaining_unswept_forces_continue(self):
        surfaces = (self._blocked("A"), self._unswept("B"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)

    # TEST 3 — all 8 conditions required; any single miss rejects stop
    def test_missing_state_revalidation_alone_blocks_stop(self):
        """Intent preserved (this must never certify STOP); mechanism
        corrected 2026-08-28. It previously asserted proceed=True, which
        pinned a real escape: CONTINUE with unresolved_surfaces=() means
        "work remains" while naming none. Absent revalidation is a
        jurisdiction failure, not governed openness."""
        surfaces = (self._swept("A"), self._blocked("B"), self._deferred("C"))
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            sentinel.evaluate_continuation(
                surfaces, state_revalidated=False, candidates_found=())
        self.assertIn("1_state_revalidated", str(ctx.exception))

    def test_new_wake_evidence_alone_blocks_stop(self):
        surfaces = (self._swept("A"), self._blocked("B"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, new_wake_evidence=True,
            candidates_found=())
        self.assertTrue(d.proceed)

    def test_zero_recorded_surfaces_cannot_stop(self):
        """Intent preserved (an empty universe must never certify STOP);
        mechanism corrected 2026-08-28 -- it is jurisdiction denial, not
        CONTINUE. An empty surface set is not an open universe."""
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            sentinel.evaluate_continuation(
                (), state_revalidated=True, candidates_found=())
        self.assertIn("2_at_least_one_surface_recorded", str(ctx.exception))

    # TEST 4 — true exhaustion can stop
    def test_full_coverage_with_no_new_evidence_allows_stop(self):
        surfaces = (
            self._swept("A"), self._swept("B"),
            self._blocked("C"), self._deferred("D"),
        )
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=())
        self.assertFalse(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ())
        self.assertTrue(all(d.conditions.values()))

    # A block or deferral without evidence cannot even be constructed —
    # fail-closed at the ledger row, not just at evaluation time.
    def test_blocked_surface_without_evidence_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="X", status="BLOCKED", evidence="")

    def test_deferred_surface_without_wake_condition_is_rejected_at_construction(self):
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(
                name="X", status="DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION",
                evidence="why", reopen_condition="")

    def test_unknown_status_is_rejected(self):
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="X", status="MAYBE")

    # TEST 5 — one-brick limit, enforced structurally
    def test_select_one_admitted_returns_exactly_one_of_many(self):
        result = sentinel.select_one_admitted(("cand-1", "cand-2", "cand-3"))
        self.assertEqual(result, "cand-1")

    def test_select_one_admitted_returns_none_when_empty(self):
        self.assertIsNone(sentinel.select_one_admitted(()))

    # TEST 6 — no constitutional authority expansion (governor never
    # executes; already covered structurally by TestSentinelCannotExecute
    # scanning this module's public callables, re-asserted here directly
    # against the new names)
    def test_governor_functions_are_not_named_as_actions(self):
        for name in ("evaluate_continuation", "select_one_admitted", "HuntSurface",
                     "ContinuationDecision"):
            first_word = re.split(r"[_A-Z]", name)[0].lower() or name.lower()
            self.assertNotIn(first_word, FORBIDDEN_VERBS)

    def test_decision_object_carries_no_executable_payload(self):
        surfaces = (self._swept("A"), self._blocked("B"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=())
        payload = d.to_dict()
        self.assertIsInstance(payload["proceed"], bool)
        # No field is a callable, a code string, or anything an actuator
        # could interpret as an instruction to execute.
        for v in payload.values():
            self.assertNotIsInstance(v, type(lambda: None))

    # Realistic composite scenario matching this session's own history:
    # several surfaces genuinely swept/blocked, one adjacent surface
    # never checked -- must continue, and must name it.
    def test_realistic_partial_coverage_continues_and_names_the_gap(self):
        surfaces = (
            self._swept("sensor_conveyor"), self._swept("jsonl_reader_crash_class"),
            self._swept("orchestration_isolation"), self._blocked("dormant_organs",
                evidence="zero non-test callers, deletion blocked on open human decision item 13"),
            self._deferred("unbounded_log_read", wake="pulse_log.jsonl exceeds 1MB"),
            self._unswept("cross_subsystem_contradictions_beyond_sigil_pair"),
        )
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("cross_subsystem_contradictions_beyond_sigil_pair",))


class TestDeferredLogSizeWakeCondition(unittest.TestCase):
    """Closes the gap in evaluate_continuation()'s own contract: condition
    6 (no_new_wake_evidence) for the one real DEFERRED surface on the
    board was being verified by a human reading `ls -la` each cycle --
    the exact hand-checked-snapshot shape already proven costly twice
    this session (README test count, sigil tier disagreement)."""

    def test_all_logs_under_threshold_is_false(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d); (repo / "foundation").mkdir()
            (repo / "foundation" / "pulse_log.jsonl").write_text("x" * 100)
            self.assertFalse(sentinel.check_deferred_log_size_wake_condition(repo))

    def test_one_oversized_tracked_log_triggers_true(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d); (repo / "foundation").mkdir()
            (repo / "foundation" / "authority_ledger.jsonl").write_bytes(
                b"x" * (sentinel.DEFERRED_LOG_SIZE_THRESHOLD_BYTES + 1))
            self.assertTrue(sentinel.check_deferred_log_size_wake_condition(repo))

    def test_exactly_at_threshold_is_not_yet_triggered(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d); (repo / "foundation").mkdir()
            (repo / "foundation" / "pulse_log.jsonl").write_bytes(
                b"x" * sentinel.DEFERRED_LOG_SIZE_THRESHOLD_BYTES)
            self.assertFalse(sentinel.check_deferred_log_size_wake_condition(repo))

    def test_an_untracked_large_file_does_not_trigger(self):
        """Fixed list, not a glob -- a stray file becoming 'tracked' is a
        human decision, matching LIVE_MOUTH_IDS' own discipline."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d); (repo / "foundation").mkdir()
            (repo / "foundation" / "some_other_file.jsonl").write_bytes(
                b"x" * (sentinel.DEFERRED_LOG_SIZE_THRESHOLD_BYTES + 1))
            self.assertFalse(sentinel.check_deferred_log_size_wake_condition(repo))

    def test_missing_files_do_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(sentinel.check_deferred_log_size_wake_condition(Path(d)))

    def test_never_reads_file_content(self):
        """Read-only means stat only -- never opens the file, so a huge
        file's cost is O(1), not O(size)."""
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d); (repo / "foundation").mkdir()
            path = repo / "foundation" / "pulse_log.jsonl"
            path.write_bytes(b"\xff" * 100)  # would crash a .read_text() call
            self.assertFalse(sentinel.check_deferred_log_size_wake_condition(repo))

    def test_writes_nothing(self):
        before = {n: (REPO_ROOT / "foundation" / n).stat().st_mtime_ns
                  for n in sentinel._TRACKED_JSONL_LOGS
                  if (REPO_ROOT / "foundation" / n).exists()}
        sentinel.check_deferred_log_size_wake_condition(REPO_ROOT)
        for n, mtime in before.items():
            self.assertEqual((REPO_ROOT / "foundation" / n).stat().st_mtime_ns, mtime)

    def test_the_real_repository_has_not_crossed_the_threshold(self):
        self.assertFalse(sentinel.check_deferred_log_size_wake_condition(REPO_ROOT))


class TestClosedAccountingUniverse(unittest.TestCase):
    """The escape hatch, reproduced before it was closed (2026-08-28):
    evaluate_continuation() validated the CONTENTS of `surfaces` but
    never that `surfaces` ACCOUNTED FOR WHAT THE CYCLE FOUND. A worker
    could find candidates X and Y, build Y under the one-brick limit,
    call X 'deferred / a one-line future addition' in receipt prose only,
    never create a HuntSurface row, and receive STOP while X remained
    real, known, ungoverned work.

    This was the author's own prior cycle -- `harness_boot_documentation`
    was reported DEFERRED with the words 'not lost' and 'no board created
    for it', and grep confirmed it appeared in no source file, no test,
    and no durable artifact."""

    def _swept(self, n): return sentinel.HuntSurface(name=n, status="SWEPT")

    # CASE 1 — the exact prior failure
    def test_the_exact_prior_escape_now_fails_closed(self):
        surfaces = (self._swept("Y_wake_check"),)
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                surfaces, state_revalidated=True,
                candidates_found=("Y_wake_check", "X_boot_documentation"))

    # CASE 2 — silent drop
    def test_found_two_disposed_one_fails_closed(self):
        surfaces = (self._swept("A"),)
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                surfaces, state_revalidated=True, candidates_found=("A", "B"))

    # CASE 3 — fake deferral (no wake condition) still blocked at construction
    def test_deferral_without_wake_condition_still_fails_closed(self):
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="X",
                status="DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION",
                evidence="why", reopen_condition="")

    # CASE 4 — block without unblocker
    def test_block_without_evidence_still_fails_closed(self):
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="X", status="BLOCKED", evidence="")

    # CASE 5 — legitimate duplicate merge, canonical target named
    def test_a_candidate_merged_as_duplicate_is_accounted(self):
        # `duplicate_of` is structural, not prose: this test originally
        # named the canonical target inside `evidence`, which the
        # 2026-08-28 adversarial pass proved was unenforceable.
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="DUPLICATE",
                        evidence="same producer/consumer path", duplicate_of="A"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=("A", "B"))
        self.assertFalse(d.proceed)

    # CASE 6 — killed with evidence (recorded as BLOCKED with the kill reason)
    def test_a_killed_candidate_with_evidence_is_accounted(self):
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="BLOCKED",
                        evidence="killed: no mechanical ground truth; prose only"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=("A", "B"))
        self.assertFalse(d.proceed)

    # CASE 7 — one-brick limit: survivors must all remain governed
    def test_unselected_survivors_must_still_be_accounted(self):
        found = ("A", "B", "C")
        self.assertEqual(sentinel.select_one_admitted(found), "A")
        # B and C were not selected -- they may not vanish.
        surfaces = (self._swept("A"),)
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                surfaces, state_revalidated=True, candidates_found=found)
        # Properly governed, the same cycle stops legitimately.
        governed = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION",
                        evidence="real but unselected", reopen_condition="next cycle"),
                    sentinel.HuntSurface(name="C", status="BLOCKED", evidence="killed: duplicate of A"))
        self.assertFalse(sentinel.evaluate_continuation(
            governed, state_revalidated=True, candidates_found=found).proceed)

    # CASE 8 — the most important: HARD STOP refused with open work
    def test_hard_stop_is_refused_when_known_work_is_ungoverned(self):
        surfaces = (self._swept("A"), self._swept("B"))
        # Without accounting this returns STOP...
        self.assertFalse(sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=()).proceed)
        # ...but declaring the real find makes STOP impossible.
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                surfaces, state_revalidated=True,
                candidates_found=("A", "B", "known_but_untracked"))

    # Backward compatibility: omitting candidates_found preserves prior behaviour
    def test_explicit_empty_accounting_preserves_existing_behaviour(self):
        """Was `test_omitting_candidates_found_preserves_existing_behaviour`
        -- it pinned the ATTACK B escape (omission silently disabling
        conservation). Omission now refuses a verdict; an explicit `()`
        is the honest way to claim a cycle found nothing."""
        surfaces = (self._swept("A"),)
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=())
        self.assertFalse(d.proceed)

    def test_fully_accounted_cycle_proceeds_normally(self):
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="UNSWEPT"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=("A", "B"))
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("B",))


class TestDuplicateDispositionMustResolve(unittest.TestCase):
    """Termination-assassination pass 2026-08-28: DUPLICATE was a trash
    chute. Four reproduced escapes -- no canonical target, a nonexistent
    target, self-reference, and a circular B->C->B chain -- every one
    certified HARD_STOP while the work was really unresolved. A
    disposition that resolves to nothing is not a disposition."""

    def _swept(self, n): return sentinel.HuntSurface(name=n, status="SWEPT")

    def test_duplicate_without_target_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="B", status="DUPLICATE", evidence="dupe")

    def test_self_referential_duplicate_cannot_be_constructed(self):
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="B", status="DUPLICATE",
                                 evidence="e", duplicate_of="B")

    def test_duplicate_of_a_nonexistent_target_refuses_verdict(self):
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="DUPLICATE",
                                         evidence="e", duplicate_of="Z_absent"))
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(surfaces, state_revalidated=True)

    def test_circular_duplicate_chain_refuses_verdict(self):
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="DUPLICATE", evidence="e", duplicate_of="C"),
                    sentinel.HuntSurface(name="C", status="DUPLICATE", evidence="e", duplicate_of="B"))
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(surfaces, state_revalidated=True)

    def test_three_hop_circular_chain_also_refuses(self):
        """Mutated replay: longer cycle, not the canned 2-hop input."""
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="DUPLICATE", evidence="e", duplicate_of="C"),
                    sentinel.HuntSurface(name="C", status="DUPLICATE", evidence="e", duplicate_of="D"),
                    sentinel.HuntSurface(name="D", status="DUPLICATE", evidence="e", duplicate_of="B"))
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(surfaces, state_revalidated=True)

    def test_a_legitimate_duplicate_chain_still_resolves_and_stops(self):
        """Mutated replay: a valid multi-hop chain B->C->A must PASS, so
        the fix rejects only unresolvable chains, not all chains."""
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="C", status="DUPLICATE", evidence="e", duplicate_of="A"),
                    sentinel.HuntSurface(name="B", status="DUPLICATE", evidence="e", duplicate_of="C"))
        d = sentinel.evaluate_continuation(surfaces, state_revalidated=True,
                                           candidates_found=("A", "B", "C"))
        self.assertFalse(d.proceed)

    def test_duplicate_pointing_at_an_unswept_surface_still_forces_continue(self):
        """A duplicate may resolve to real state that is itself unresolved
        -- that must CONTINUE, not STOP."""
        surfaces = (sentinel.HuntSurface(name="A", status="UNSWEPT"),
                    sentinel.HuntSurface(name="B", status="DUPLICATE", evidence="e", duplicate_of="A"))
        d = sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("A",))


class TestAccountingCannotBeSilentlyOmitted(unittest.TestCase):
    """Termination-assassination 2026-08-28, ATTACK B: `candidates_found`
    defaulted to `()`, so simply OMITTING the argument disabled the entire
    conservation mechanism and certified HARD_STOP with real unlisted
    work. An escape reachable by doing nothing -- no malformed input, no
    bad row, just a missing keyword.

    'zero candidates found' and 'candidate accounting not provided' are
    different states and must not be represented identically."""

    def _swept(self, n): return sentinel.HuntSurface(name=n, status="SWEPT")

    def test_omitting_accounting_refuses_a_verdict(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation((self._swept("A"),), state_revalidated=True)

    def test_explicit_empty_tuple_is_a_valid_positive_claim(self):
        """`()` means 'this cycle genuinely discovered nothing' -- a real
        assertion a worker can be held to, unlike silence."""
        d = sentinel.evaluate_continuation(
            (self._swept("A"),), state_revalidated=True, candidates_found=())
        self.assertFalse(d.proceed)

    def test_omission_refuses_even_when_everything_else_is_clean(self):
        surfaces = (self._swept("A"),
                    sentinel.HuntSurface(name="B", status="BLOCKED", evidence="real reason"))
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(surfaces, state_revalidated=True)

    def test_omission_refuses_even_when_it_would_have_said_continue(self):
        """Fail-closed applies to CONTINUE too -- a governor that cannot
        prove its universe must render no verdict at all, not a
        convenient one."""
        surfaces = (sentinel.HuntSurface(name="A", status="UNSWEPT"),)
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(surfaces, state_revalidated=True)

    def test_accounted_path_is_unaffected(self):
        d = sentinel.evaluate_continuation(
            (self._swept("A"),), state_revalidated=True, candidates_found=("A",))
        self.assertFalse(d.proceed)


class TestIdentityLaw(unittest.TestCase):
    """SIGIL IV. Reproduced 2026-08-28 in five distinct constructions, all
    certifying HARD_STOP: SWEPT+BLOCKED, the reversed order, SWEPT+
    DUPLICATE, SWEPT+DEFERRED, BLOCKED+DEFERRED, and a 3-row variant.
    There was no identity check at all -- a clean row sat beside a dirty
    row and the governor certified closure.

    SWEPT+UNSWEPT returned CONTINUE beforehand, but only because P3 trips
    on the UNSWEPT row: accidental safety from an unrelated predicate, not
    adjudication. Contradiction is neither work nor closure -- it is loss
    of jurisdiction, so it raises rather than returning CONTINUE."""

    def _ev(self, surfaces, **kw):
        kw.setdefault("state_revalidated", True)
        kw.setdefault("candidates_found", ())
        return sentinel.evaluate_continuation(surfaces, **kw)

    def test_swept_plus_blocked_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((sentinel.HuntSurface(name="X", status="SWEPT"),
                      sentinel.HuntSurface(name="X", status="BLOCKED", evidence="e")))

    def test_order_does_not_change_the_result(self):
        """Neither the first nor the last row may win."""
        pair = (sentinel.HuntSurface(name="X", status="BLOCKED", evidence="e"),
                sentinel.HuntSurface(name="X", status="SWEPT"))
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(pair)
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(tuple(reversed(pair)))

    def test_swept_plus_deferred_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((sentinel.HuntSurface(name="X", status="SWEPT"),
                      sentinel.HuntSurface(name="X",
                          status="DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION",
                          evidence="e", reopen_condition="t")))

    def test_blocked_plus_deferred_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((sentinel.HuntSurface(name="X", status="BLOCKED", evidence="e"),
                      sentinel.HuntSurface(name="X",
                          status="DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION",
                          evidence="e", reopen_condition="t")))

    def test_swept_plus_duplicate_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((sentinel.HuntSurface(name="A", status="SWEPT"),
                      sentinel.HuntSurface(name="X", status="SWEPT"),
                      sentinel.HuntSurface(name="X", status="DUPLICATE",
                                           evidence="e", duplicate_of="A")),
                     candidates_found=("A", "X"))

    def test_swept_plus_unswept_is_now_adjudicated_not_accidental(self):
        """Previously CONTINUE via P3 -- an unrelated predicate happening
        to catch it. Now denied as the contradiction it always was."""
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((sentinel.HuntSurface(name="X", status="SWEPT"),
                      sentinel.HuntSurface(name="X", status="UNSWEPT")))

    def test_three_rows_one_identity_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((sentinel.HuntSurface(name="X", status="SWEPT"),
                      sentinel.HuntSurface(name="X", status="BLOCKED", evidence="e"),
                      sentinel.HuntSurface(name="X", status="SWEPT")))

    def test_the_error_names_every_contradictory_identity(self):
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            self._ev((sentinel.HuntSurface(name="X", status="SWEPT"),
                      sentinel.HuntSurface(name="X", status="BLOCKED", evidence="e"),
                      sentinel.HuntSurface(name="Y", status="SWEPT"),
                      sentinel.HuntSurface(name="Y", status="UNSWEPT")))
        msg = str(ctx.exception)
        self.assertIn("'X'", msg)
        self.assertIn("'Y'", msg)

    # LEGITIMATE NEIGHBOURS -- must NOT be banned
    def test_identical_repeated_rows_remain_lawful(self):
        """Repetition is not contradiction. Only DISTINCT dispositions for
        one identity are unlawful."""
        d = self._ev((sentinel.HuntSurface(name="X", status="SWEPT"),
                      sentinel.HuntSurface(name="X", status="SWEPT")))
        self.assertFalse(d.proceed)

    def test_distinct_identities_with_distinct_dispositions_are_lawful(self):
        d = self._ev((sentinel.HuntSurface(name="A", status="SWEPT"),
                      sentinel.HuntSurface(name="B", status="BLOCKED", evidence="e")),
                     candidates_found=("A", "B"))
        self.assertFalse(d.proceed)

    def test_a_lawful_open_universe_still_continues(self):
        d = self._ev((sentinel.HuntSurface(name="A", status="SWEPT"),
                      sentinel.HuntSurface(name="B", status="UNSWEPT")),
                     candidates_found=("A", "B"))
        self.assertTrue(d.proceed)


class TestJurisdictionFailureIsNotContinuation(unittest.TestCase):
    """SIGIL III / LAW XVII, reproduced 2026-08-28. P1 (state not
    revalidated) and P2 (empty universe) both returned proceed=True with
    unresolved_surfaces=() -- "reachable work remains" while naming no
    work. A worker receiving that had no lawful next action: CONTINUE by
    accident of an unrelated predicate tripping, not governed openness.

    These two are categorically unlike P3-P6. They are not facts ABOUT a
    universe; they are the preconditions for having one to judge."""

    def test_absent_revalidation_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                (sentinel.HuntSurface(name="A", status="SWEPT"),),
                state_revalidated=False, candidates_found=())

    def test_empty_universe_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation((), state_revalidated=True, candidates_found=())

    def test_both_failures_deny_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            sentinel.evaluate_continuation((), state_revalidated=False, candidates_found=())
        msg = str(ctx.exception)
        self.assertIn("1_state_revalidated", msg)
        self.assertIn("2_at_least_one_surface_recorded", msg)

    def test_absent_revalidation_denies_even_with_open_work_present(self):
        """Mutation: jurisdiction is checked regardless of whether the
        universe would otherwise have said CONTINUE."""
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                (sentinel.HuntSurface(name="A", status="UNSWEPT"),),
                state_revalidated=False, candidates_found=())

    def test_absent_revalidation_denies_even_with_full_accounting(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                (sentinel.HuntSurface(name="A", status="SWEPT"),),
                state_revalidated=False, candidates_found=("A",))

    # LEGITIMATE NEIGHBOURS -- must be untouched
    def test_genuine_open_work_still_continues_and_names_the_surface(self):
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name="A", status="SWEPT"),
             sentinel.HuntSurface(name="B", status="UNSWEPT")),
            state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("B",))

    def test_genuine_closure_still_stops(self):
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name="A", status="SWEPT"),),
            state_revalidated=True, candidates_found=("A",))
        self.assertFalse(d.proceed)

    def test_wake_evidence_is_a_fact_not_a_jurisdiction_failure(self):
        """P6 firing is a real fact about a VALID universe -- it must stay
        an ordinary CONTINUE, not be swept into the jurisdiction denial."""
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name="A", status="SWEPT"),),
            state_revalidated=True, new_wake_evidence=True, candidates_found=())
        self.assertTrue(d.proceed)

    def test_a_continue_verdict_always_names_at_least_one_surface_or_a_real_fact(self):
        """The property the escape violated: proceed=True must never mean
        'work remains' while naming no work AND no universe-level fact."""
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name="A", status="UNSWEPT"),),
            state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertTrue(d.unresolved_surfaces)


class TestOneShotIteratorIsNotAClaim(unittest.TestCase):
    """Reproduced 2026-08-28. `candidates_found` was typed `Optional[tuple]`
    and never enforced, so a generator or iterator could be passed. Two
    escapes followed, both certifying HARD_STOP with real ungoverned work:

    1. RETRY-AFTER-REFUSAL: the SAME iterator yields NO_VERDICT on call 1
       (ghost detected) and HARD_STOP on call 2 (now exhausted, reads as
       an empty claim). Retrying after a refusal is the natural worker
       response, and it converted refusal into closure.
    2. EMPTY GENERATOR: generators are always truthy, so the guard passed
       while the object asserted nothing -- defeating the
       omitted-vs-explicitly-empty distinction the None default protects.

    The corruption reached the error text: call 1 read "cycle reported
    finding []" because the iterator was drained building the message."""

    S = (sentinel.HuntSurface(name="A", status="SWEPT"),)

    def _ev(self, cf):
        return sentinel.evaluate_continuation(
            self.S, state_revalidated=True, candidates_found=cf)

    def test_retry_after_refusal_cannot_become_closure(self):
        it = iter(["A", "ghost"])
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(it)
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(it)   # previously: HARD_STOP with 'ghost' ungoverned

    def test_empty_generator_is_not_an_empty_claim(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(x for x in ())

    def test_generator_with_real_candidates_is_refused(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(x for x in ("A", "ghost"))

    def test_generator_that_would_have_been_fully_accounted_is_still_refused(self):
        """Mutation: even a 'correct' generator is refused -- the class is
        one-shot readability, not whether this particular instance
        happened to be complete."""
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(x for x in ("A",))

    def test_map_and_filter_objects_are_refused(self):
        """Mutation: other one-shot iterator forms, not just generators."""
        for one_shot in (map(str, ["A"]), filter(None, ["A"]), iter(("A",))):
            with self.assertRaises(sentinel.UnaccountedCandidates):
                self._ev(one_shot)

    def test_the_refusal_names_the_actual_type(self):
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            self._ev(iter(["A"]))
        self.assertIn("one-shot iterator is not a claim", str(ctx.exception))

    # LEGITIMATE NEIGHBOURS -- concrete re-readable collections
    def test_tuple_list_set_frozenset_all_remain_lawful(self):
        for cf in (("A",), ["A"], {"A"}, frozenset({"A"})):
            self.assertFalse(self._ev(cf).proceed, f"{type(cf).__name__} rejected")

    def test_explicit_empty_forms_remain_lawful_claims(self):
        for cf in ((), [], set(), frozenset()):
            self.assertFalse(self._ev(cf).proceed, f"empty {type(cf).__name__} rejected")

    def test_omission_still_denies_jurisdiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(self.S, state_revalidated=True)

    def test_a_concrete_collection_can_be_read_twice_identically(self):
        """The property the escape violated: the same claim object must
        produce the same verdict every time it is evaluated."""
        cf = ("A", "ghost")
        for _ in range(3):
            with self.assertRaises(sentinel.UnaccountedCandidates):
                self._ev(cf)
        clean = ("A",)
        self.assertEqual([self._ev(clean).proceed for _ in range(3)], [False] * 3)


class _OneShotSized:
    """__len__ passes the non-empty gate; __iter__ yields only once."""
    def __init__(self, items): self._items = list(items); self._used = False
    def __len__(self): return len(self._items)
    def __iter__(self):
        if self._used: return iter([])
        self._used = True
        return iter(self._items)


class TestSurfacesMustBeARereadableCollection(unittest.TestCase):
    """Same root class as the candidates_found brick, on the sibling
    parameter. `surfaces` was declared `tuple` and never enforced, while
    being iterated SEVEN times per call (conservation, identity map,
    duplicate index, chain walk, unresolved scan, evidence/reopen all()
    checks, len()). A one-shot input therefore presented a DIFFERENT
    universe to each gate.

    Reproduced 2026-08-28 -- these are FALSE CLOSURE, not crashes:
      * real UNSWEPT work certified HARD_STOP with unresolved=()
      * a duplicate pointing at a nonexistent target certified HARD_STOP
    Plain generators/iterators additionally leaked a raw TypeError from
    len(), outside the three-verdict algebra entirely."""

    def test_one_shot_input_cannot_hide_unswept_work(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                _OneShotSized([sentinel.HuntSurface(name="A", status="SWEPT"),
                               sentinel.HuntSurface(name="B", status="UNSWEPT")]),
                state_revalidated=True, candidates_found=())

    def test_one_shot_input_cannot_hide_an_unresolvable_duplicate(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                _OneShotSized([sentinel.HuntSurface(name="A", status="SWEPT"),
                               sentinel.HuntSurface(name="B", status="DUPLICATE",
                                                    evidence="e", duplicate_of="GHOST")]),
                state_revalidated=True, candidates_found=())

    def test_generator_surfaces_are_refused_not_crashed(self):
        """Previously leaked TypeError from len() -- a fourth outcome."""
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                (s for s in [sentinel.HuntSurface(name="A", status="SWEPT")]),
                state_revalidated=True, candidates_found=("A",))

    def test_iterator_surfaces_are_refused_not_crashed(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                iter([sentinel.HuntSurface(name="A", status="SWEPT")]),
                state_revalidated=True, candidates_found=("A",))

    def test_map_and_filter_surfaces_are_refused(self):
        base = [sentinel.HuntSurface(name="A", status="SWEPT")]
        for one_shot in (map(lambda x: x, base), filter(None, base)):
            with self.assertRaises(sentinel.UnaccountedCandidates):
                sentinel.evaluate_continuation(
                    one_shot, state_revalidated=True, candidates_found=("A",))

    def test_the_refusal_explains_the_repeated_read(self):
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            sentinel.evaluate_continuation(
                iter([]), state_revalidated=True, candidates_found=())
        self.assertIn("reads surfaces repeatedly", str(ctx.exception))

    # LEGITIMATE NEIGHBOURS
    def test_concrete_collections_all_remain_lawful(self):
        row = sentinel.HuntSurface(name="A", status="SWEPT")
        for coll in ((row,), [row], {row}, frozenset({row})):
            d = sentinel.evaluate_continuation(
                coll, state_revalidated=True, candidates_found=("A",))
            self.assertFalse(d.proceed, f"{type(coll).__name__} rejected")

    def test_real_open_work_still_continues_and_names_it(self):
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name="A", status="SWEPT"),
             sentinel.HuntSurface(name="B", status="UNSWEPT")),
            state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("B",))

    def test_the_same_concrete_universe_verdicts_identically_on_replay(self):
        surfaces = (sentinel.HuntSurface(name="A", status="SWEPT"),
                    sentinel.HuntSurface(name="B", status="UNSWEPT"))
        results = [sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=()).unresolved_surfaces
            for _ in range(3)]
        self.assertEqual(results, [("B",)] * 3)


class _MutatingList(list):
    """Passes isinstance(list) but yields different membership per read."""
    def __init__(self, items, clean_after):
        super().__init__(items); self._n = 0; self._clean_after = clean_after
    def __iter__(self):
        self._n += 1
        if self._n > self._clean_after:
            return iter([x for x in list.__iter__(self)
                         if getattr(x, "status", "") == "SWEPT"])
        return list.__iter__(self)


class _EmptyYieldingList(list):
    """Truthy via list.__len__, but __iter__ yields nothing."""
    def __iter__(self): return iter([])


class TestObservationalUniverseIsPinned(unittest.TestCase):
    """The type guards reject one-shot inputs, but type is not stability:
    a list SUBCLASS passes isinstance() and can still change membership
    between reads. `surfaces` is read seven times per call, so without
    pinning, different jurisdiction gates adjudicated DIFFERENT UNIVERSES.

    Reproduced 2026-08-28, all FALSE CLOSURE:
      * dirty row yielded only on read 1 -> real UNSWEPT work certified
        HARD_STOP with unresolved=()
      * same shape hiding a duplicate whose target does not exist
      * candidates_found truthy via __len__ but yielding nothing -> a
        ghost candidate never checked, HARD_STOP issued"""

    def test_mutating_surfaces_cannot_hide_unswept_work(self):
        d = sentinel.evaluate_continuation(
            _MutatingList([sentinel.HuntSurface(name="A", status="SWEPT"),
                           sentinel.HuntSurface(name="B", status="UNSWEPT")], 1),
            state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("B",))

    def test_mutating_surfaces_cannot_hide_an_unresolvable_duplicate(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                _MutatingList([sentinel.HuntSurface(name="A", status="SWEPT"),
                               sentinel.HuntSurface(name="B", status="DUPLICATE",
                                                    evidence="e", duplicate_of="GHOST")], 1),
                state_revalidated=True, candidates_found=())

    def test_mutating_surfaces_cannot_hide_an_identity_contradiction(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                _MutatingList([sentinel.HuntSurface(name="X", status="SWEPT"),
                               sentinel.HuntSurface(name="X", status="BLOCKED",
                                                    evidence="e")], 1),
                state_revalidated=True, candidates_found=())

    def test_a_claim_that_lies_on_its_first_read_is_the_declared_ceiling(self):
        """HONEST LIMIT, not a closed hole. Pinning guarantees every gate
        reads ONE snapshot; it cannot make a caller tell the truth on the
        read it does get. An object truthy via __len__ but yielding
        nothing materialises to () and is then treated exactly as an
        explicit empty claim -- consistently, not accidentally.

        This is the same caller-assertion ceiling as `state_revalidated`,
        and is asserted here as a limit rather than papered over."""
        lying = _EmptyYieldingList(["A", "ghost"])
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name="A", status="SWEPT"),),
            state_revalidated=True, candidates_found=lying)
        explicit_empty = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name="A", status="SWEPT"),),
            state_revalidated=True, candidates_found=())
        # Identical outcome: the lie is indistinguishable from an honest
        # empty claim, which is precisely why it is a declared ceiling.
        self.assertEqual(d.proceed, explicit_empty.proceed)

    def test_every_gate_reads_the_same_snapshot(self):
        """The invariant directly: a universe that would differ per read
        must produce the verdict of the pinned snapshot, not a blend."""
        m = _MutatingList([sentinel.HuntSurface(name="A", status="SWEPT"),
                           sentinel.HuntSurface(name="B", status="UNSWEPT")], 1)
        first = sentinel.evaluate_continuation(
            m, state_revalidated=True, candidates_found=()).unresolved_surfaces
        self.assertEqual(first, ("B",))

    # LEGITIMATE NEIGHBOURS
    def test_plain_collections_are_unaffected(self):
        row = sentinel.HuntSurface(name="A", status="SWEPT")
        for coll in ((row,), [row], {row}, frozenset({row})):
            self.assertFalse(sentinel.evaluate_continuation(
                coll, state_revalidated=True, candidates_found=("A",)).proceed)

    def test_one_shot_inputs_are_still_refused_not_silently_materialised(self):
        """Pinning must not weaken the earlier law: an exhausted iterator
        is still not a lawful empty claim."""
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                iter([sentinel.HuntSurface(name="A", status="SWEPT")]),
                state_revalidated=True, candidates_found=())
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                (sentinel.HuntSurface(name="A", status="SWEPT"),),
                state_revalidated=True, candidates_found=iter(["A"]))

    def test_ghost_candidates_and_empty_universe_still_deny(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation(
                (sentinel.HuntSurface(name="A", status="SWEPT"),),
                state_revalidated=True, candidates_found=("A", "ghost"))
        with self.assertRaises(sentinel.UnaccountedCandidates):
            sentinel.evaluate_continuation((), state_revalidated=True, candidates_found=())


class _DuckSurface:
    """Duck-typed row that never runs HuntSurface.__post_init__, so every
    construction-time invariant is bypassed."""
    def __init__(self, name, status, evidence="", reopen_condition="", duplicate_of=""):
        self.name = name; self.status = status; self.evidence = evidence
        self.reopen_condition = reopen_condition; self.duplicate_of = duplicate_of


class TestSurfaceMembersMustBeLawfulRows(unittest.TestCase):
    """Pinning fixed WHICH objects the gates see; it never checked WHAT
    they are. Every invariant this governor relies on lives in
    HuntSurface.__post_init__, and all were bypassable by duck typing.

    Reproduced 2026-08-28 against current source:
      * status "TOTALLY_MADE_UP", outside the entire vocabulary,
        certified HARD_STOP -- unadjudicated work reported as closure
      * BLOCKED with no evidence and DEFERRED with no reopen condition
        each produced CONTINUE with unresolved=() -- continue naming no
        reachable work
      * a plain str element leaked a raw AttributeError, a fourth
        outcome outside the verdict algebra"""

    CLEAN = sentinel.HuntSurface(name="A", status="SWEPT")

    def _ev(self, surfaces, candidates_found=()):
        return sentinel.evaluate_continuation(
            surfaces, state_revalidated=True, candidates_found=candidates_found)

    def test_a_status_outside_the_vocabulary_cannot_certify_closure(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((self.CLEAN, _DuckSurface("B", "TOTALLY_MADE_UP")))

    def test_blocked_without_evidence_cannot_slip_in_duck_typed(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((self.CLEAN, _DuckSurface("B", "BLOCKED")))

    def test_deferred_without_reopen_condition_cannot_slip_in_duck_typed(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((self.CLEAN, _DuckSurface(
                "B", "DEFERRED_WITH_OBJECTIVE_WAKE_CONDITION", evidence="e")))

    def test_self_referential_duplicate_cannot_slip_in_duck_typed(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((self.CLEAN, _DuckSurface(
                "B", "DUPLICATE", evidence="e", duplicate_of="B")))

    def test_a_non_row_element_is_refused_not_crashed(self):
        """Previously leaked AttributeError -- an unclassified fourth
        outcome outside {NO_VERDICT, CONTINUE, HARD_STOP}."""
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((self.CLEAN, "not_a_surface"))

    def test_the_refusal_names_the_offending_index_and_type(self):
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            self._ev((self.CLEAN, 42))
        msg = str(ctx.exception)
        self.assertIn("index 1", msg)
        self.assertIn("int", msg)

    # LEGITIMATE NEIGHBOURS
    def test_real_rows_are_unaffected(self):
        self.assertFalse(self._ev((self.CLEAN,), candidates_found=("A",)).proceed)

    def test_real_open_work_still_continues_and_names_it(self):
        d = self._ev((self.CLEAN, sentinel.HuntSurface(name="B", status="UNSWEPT")))
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("B",))

    def test_a_lawful_duplicate_chain_still_closes(self):
        self.assertFalse(self._ev(
            (self.CLEAN, sentinel.HuntSurface(name="B", status="DUPLICATE",
                                              evidence="e", duplicate_of="A"))).proceed)

    def test_huntsurface_subclasses_remain_lawful(self):
        """Subclasses still run __post_init__, so their invariants hold."""
        class Sub(sentinel.HuntSurface): pass
        self.assertFalse(
            self._ev((Sub(name="A", status="SWEPT"),), candidates_found=("A",)).proceed)


class _LiarEq:
    """Lies about equality; __hash__ collides with a real surface name."""
    def __hash__(self): return hash("X")
    def __eq__(self, other): return True


class TestCandidateIdentitiesMustBeStrings(unittest.TestCase):
    """The conservation gate decides membership with `c not in named`,
    delegating "is this candidate accounted for" to the CANDIDATE'S OWN
    __eq__/__hash__. An arbitrary object adjudicated its own conservation.

    Reproduced 2026-08-28 against current source:
      * FALSE HARD_STOP -- an object with __hash__ = hash("X") and __eq__
        returning True was accepted as accounted for and certified
        proceed=False, with no HuntSurface row for it at all
      * list/dict elements raised raw TypeError ("unhashable type") from
        the membership test -- a fourth outcome outside the algebra
      * mixed int/str raised raw TypeError from sorted() while BUILDING
        the refusal message, so the fail-closed path threw the wrong type"""

    S = (sentinel.HuntSurface(name="X", status="SWEPT"),)

    def _ev(self, cf):
        return sentinel.evaluate_continuation(
            self.S, state_revalidated=True, candidates_found=cf)

    def test_a_lying_eq_cannot_certify_closure(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((_LiarEq(),))

    def test_unhashable_elements_are_refused_not_crashed(self):
        for bad in (["x"], {"k": 1}, {1, 2}):
            with self.assertRaises(sentinel.UnaccountedCandidates):
                self._ev((bad,))

    def test_unorderable_mixed_types_do_not_break_the_refusal_path(self):
        """The fail-closed path itself previously threw TypeError from
        sorted() while building its own error message."""
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((1, "a"))

    def test_none_element_is_refused(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((None,))

    def test_the_refusal_names_the_offending_index_and_type(self):
        with self.assertRaises(sentinel.UnaccountedCandidates) as ctx:
            self._ev(("X", 42))
        msg = str(ctx.exception)
        self.assertIn("index 1", msg)
        self.assertIn("int", msg)

    def test_an_object_whose_hash_collides_with_a_real_name_is_still_refused(self):
        """Mutation: hash collision alone must not buy membership."""
        class HashOnly:
            def __hash__(self): return hash("X")
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev((HashOnly(),))

    # LEGITIMATE NEIGHBOURS
    def test_string_identities_remain_lawful_in_every_container(self):
        for cf in (("X",), ["X"], {"X"}, frozenset({"X"})):
            self.assertFalse(self._ev(cf).proceed, f"{type(cf).__name__} rejected")

    def test_explicit_empty_claim_still_lawful(self):
        self.assertFalse(self._ev(()).proceed)

    def test_a_genuine_ghost_string_is_still_refused(self):
        with self.assertRaises(sentinel.UnaccountedCandidates):
            self._ev(("X", "ghost"))


class TestIdentitiesMustBeNameable(unittest.TestCase):
    """`name` was the only HuntSurface field never validated, while
    `duplicate_of` -- which merely POINTS AT a name -- has always required
    non-blank after .strip(). Reproduced 2026-08-28, all from that one
    asymmetry:

      * CONTINUE reported unresolved=('',) / ('   ',) / ('\\t',) --
        naming "work" no worker can act on
      * a blank-named SWEPT row plus a blank candidate certified
        HARD_STOP -- FALSE CLOSURE over an unnameable identity
      * '' and '   ' coexisted as DISTINCT identities, so identity
        singularity cannot protect what has no legible identity"""

    def test_every_blank_form_is_refused_at_construction(self):
        for blank in ("", "   ", "\t", "\n", "\r\n  ", " \t\n "):
            with self.assertRaises(ValueError, msg=f"{blank!r} constructed"):
                sentinel.HuntSurface(name=blank, status="UNSWEPT")

    def test_non_string_names_are_refused_not_crashed(self):
        """Previously escaped as a raw AttributeError from .strip() --
        a fourth outcome outside {NO_VERDICT, CONTINUE, HARD_STOP}."""
        for bad in (None, 42, ["A"], object(), 3.5):
            with self.assertRaises(ValueError, msg=f"{type(bad).__name__} constructed"):
                sentinel.HuntSurface(name=bad, status="UNSWEPT")

    def test_unicode_whitespace_names_are_refused(self):
        for ws in ("\xa0", "\u3000", "\u2003", "\u2009", "\u00a0\u3000"):
            with self.assertRaises(ValueError, msg=f"{ws!r} constructed"):
                sentinel.HuntSurface(name=ws, status="UNSWEPT")

    def test_wholly_invisible_format_character_names_are_refused(self):
        """isspace() is False for zero-width chars, so .strip() left them
        intact -- but a name made only of them is invisible, and therefore
        exactly as unnameable as "". Unicode category Cf is the separator:
        every legitimate name character tested (Lu/Nd/So/Lo/Pd) is not Cf."""
        for zw in ("\u200b", "\ufeff", "\u2060", "\u200b\ufeff", "\u200b \u2060"):
            with self.assertRaises(ValueError, msg=f"{zw!r} constructed"):
                sentinel.HuntSurface(name=zw, status="UNSWEPT")

    def test_an_invisible_character_inside_a_real_name_stays_lawful(self):
        """Only WHOLLY invisible names are refused -- the character itself
        is not banned."""
        sentinel.HuntSurface(name="a\u200bb", status="SWEPT")

    def test_a_blank_identity_can_no_longer_reach_unresolved_surfaces(self):
        """The paralysis mode: proceed=True naming a target nobody can act on."""
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="", status="UNSWEPT")

    def test_a_blank_identity_can_no_longer_certify_closure(self):
        """The rank-1 form: FALSE HARD_STOP over an unnameable row."""
        with self.assertRaises(ValueError):
            sentinel.HuntSurface(name="   ", status="SWEPT")

    def test_the_refusal_explains_the_duplicate_of_asymmetry(self):
        with self.assertRaises(ValueError) as ctx:
            sentinel.HuntSurface(name=" ", status="SWEPT")
        self.assertIn("duplicate_of", str(ctx.exception))

    # LEGITIMATE NEIGHBOURS -- strip() decides blankness only, never normalises
    def test_ordinary_names_remain_lawful(self):
        for name in ("A", " A", "A ", "my surface", "FRONTIER-009",
                     "x" * 200, "ünïcödé", "0", "-", "surface_001",
                     "\U0001F525", "\u65e5\u672c\u8a9e", " X "):
            sentinel.HuntSurface(name=name, status="SWEPT")   # must not raise

    def test_leading_and_trailing_space_names_stay_distinct_identities(self):
        """No canonicalisation: ' A' and 'A' are still two identities.
        Normalising them was separately killed with evidence."""
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name=" A", status="SWEPT"),
             sentinel.HuntSurface(name="A", status="UNSWEPT")),
            state_revalidated=True, candidates_found=())
        self.assertTrue(d.proceed)
        self.assertEqual(d.unresolved_surfaces, ("A",))

    def test_a_whitespace_padded_name_is_not_a_contradiction_with_its_bare_form(self):
        d = sentinel.evaluate_continuation(
            (sentinel.HuntSurface(name=" A", status="SWEPT"),
             sentinel.HuntSurface(name="A", status="BLOCKED", evidence="e")),
            state_revalidated=True, candidates_found=())
        self.assertFalse(d.proceed)   # two lawful distinct identities, both closed


class TestCheckCiMatrixCoverage(unittest.TestCase):
    """CI-matrix reachability (PARETO_FRONTIER.md FRONTIER-025/cycle
    ci_escape_001): every `test_*.py` file must be contained under at
    least one `-s <subsystem>` entry in `.github/workflows/tests.yml`'s
    matrix, or it silently never runs in CI.

    REPRODUCED 2026-08-28: `gems/claim_ledger/test_claim_ledger.py` (14
    real, passing tests) sat outside every matrix entry's reach — the
    whole 10-subsystem CI-equivalent run stayed green with zero mentions
    of it. This class proves the check catches that shape and does not
    false-positive on the real, now-fixed repository.
    """

    def _repo(self, subsystems, test_files):
        root = Path(self.tmp.name)
        (root / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
        matrix_yaml = "\n".join(f"          - {s}" for s in subsystems)
        (root / ".github" / "workflows" / "tests.yml").write_text(f"""\
jobs:
  test:
    strategy:
      matrix:
        subsystem:
{matrix_yaml}
""")
        for rel in test_files:
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("import unittest\n")
        return root

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_real_repository_is_currently_clean(self):
        """The actual fix this cycle made to tests.yml: gems/claim_ledger
        added as its own matrix entry. Must produce zero findings now."""
        self.assertEqual(check_ci_matrix_coverage(REPO_ROOT), [])

    def test_reproduces_the_real_escape_shape(self):
        """THE DISCRIMINATING MUTATION. A matrix missing the containing
        directory of a real test file must be caught -- this is the
        exact shape gems/claim_ledger regressed from before this cycle's
        fix. Fails against the pre-fix matrix, passes against the
        post-fix one (see test_real_repository_is_currently_clean)."""
        root = self._repo(
            subsystems=["schema", "compiler"],
            test_files=[
                "schema/tests/test_a.py",
                "compiler/tests/test_b.py",
                "gems/claim_ledger/test_claim_ledger.py",
            ],
        )
        findings = check_ci_matrix_coverage(root)
        self.assertEqual(len(findings), 1)
        self.assertIn("gems/claim_ledger", findings[0].observation)

    def test_a_file_reachable_via_a_leaf_matrix_entry_is_not_flagged(self):
        """The fix's own shape: a matrix entry naming the leaf directory
        directly (gems/claim_ledger, not gems) must satisfy reachability."""
        root = self._repo(
            subsystems=["schema", "gems/claim_ledger"],
            test_files=[
                "schema/tests/test_a.py",
                "gems/claim_ledger/test_claim_ledger.py",
            ],
        )
        self.assertEqual(check_ci_matrix_coverage(root), [])

    def test_a_naive_parent_only_entry_does_not_launder_a_nested_escape(self):
        """A matrix entry for a PARENT directory does cover files nested
        under it -- containment is real, not name-matching -- but a
        SIBLING directory with no matrix entry of its own is still
        flagged. Distinguishes real path containment from string
        prefix-matching bugs (e.g. 'gems' wrongly matching 'gems2')."""
        root = self._repo(
            subsystems=["schema"],
            test_files=[
                "schema/tests/nested/deep/test_a.py",  # covered: real containment
                "schema2/tests/test_b.py",             # NOT covered: distinct sibling dir
            ],
        )
        findings = check_ci_matrix_coverage(root)
        self.assertEqual(len(findings), 1)
        self.assertIn("schema2", findings[0].observation)

    def test_missing_workflow_file_is_a_finding_not_a_crash(self):
        root = Path(self.tmp.name)
        self.assertEqual(len(check_ci_matrix_coverage(root)), 1)

    def test_wired_into_pulse_sweep(self):
        self.assertIn(check_ci_matrix_coverage, _LEVEL1_CHECKS)


class TestBuildReportSubstanceNotJustExistence(unittest.TestCase):
    """REPRODUCED 2026-08-29: eight EMPTY BUILD_REPORT.md files scored
    IRON:10 and produced zero findings, while _dimension_iron()'s score
    is a required conjunct for tier T6 -- eight touched files could buy
    a tier. This check's own finding text already claimed the report
    carried limitations/human-decisions sections; it asserted more than
    it verified."""

    def _repo(self, content):
        d = tempfile.mkdtemp()
        root = Path(d)
        for name in SUBSYSTEMS_REQUIRING_BUILD_REPORT:
            (root / name).mkdir()
            (root / name / "BUILD_REPORT.md").write_text(content)
        return root

    def test_empty_report_is_now_a_finding_not_silence(self):
        findings = check_subsystem_build_reports(self._repo(""))
        self.assertEqual(len(findings), len(SUBSYSTEMS_REQUIRING_BUILD_REPORT))
        self.assertIn("no audit content", findings[0].observation)

    def test_heading_only_stub_is_rejected(self):
        # A bare "# report" is a placeholder, not an audit trail.
        self.assertEqual(
            len(check_subsystem_build_reports(self._repo("# report\n"))),
            len(SUBSYSTEMS_REQUIRING_BUILD_REPORT),
        )

    def test_body_without_any_heading_is_rejected(self):
        self.assertEqual(
            len(check_subsystem_build_reports(self._repo("just prose, no heading\n"))),
            len(SUBSYSTEMS_REQUIRING_BUILD_REPORT),
        )

    def test_minimal_real_report_is_accepted(self):
        self.assertEqual(
            len(check_subsystem_build_reports(self._repo("# Report\n\nWhat was built: x\n"))), 0)

    def test_missing_and_hollow_produce_distinguishable_observations(self):
        # The two states are different problems and must not be conflated.
        d = tempfile.mkdtemp()
        root = Path(d)
        names = list(SUBSYSTEMS_REQUIRING_BUILD_REPORT)
        (root / names[0]).mkdir()  # missing entirely
        (root / names[1]).mkdir()
        (root / names[1] / "BUILD_REPORT.md").write_text("")  # present but hollow
        observations = [f.observation for f in check_subsystem_build_reports(root)]
        self.assertIn(f"subsystem '{names[0]}' has no BUILD_REPORT.md", observations)
        self.assertIn(
            f"subsystem '{names[1]}' has a BUILD_REPORT.md with no audit content",
            observations)

    def test_the_real_repository_still_passes_unchanged(self):
        # The other half of the proof: a stricter rule must not penalise
        # the eight real reports (each 2.5-9.2KB, 8-12 headings).
        self.assertEqual(len(check_subsystem_build_reports(REPO_ROOT)), 0)
        for name in SUBSYSTEMS_REQUIRING_BUILD_REPORT:
            self.assertTrue(has_substantive_build_report(REPO_ROOT / name), name)

    def test_wired_into_pulse_sweep(self):
        self.assertIn(check_subsystem_build_reports, _LEVEL1_CHECKS)
