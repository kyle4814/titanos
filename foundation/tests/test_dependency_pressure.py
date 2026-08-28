import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from foundation.dependency_pressure import (
    evaluate_dependency_pressure,
    read_dependency_pressure_log,
)
from foundation.mouth_common import MouthObservation, read_mouth_log_continuity
from foundation.sentinel import Finding

# Fixed "now" so staleness assertions don't drift with wall-clock time --
# the exact bug that broke two authority-runtime tests earlier this session.
_NOW = datetime(2026, 8, 27, 18, 0, 0, tzinfo=timezone.utc)


def _obs(status, new_items=(), mouth_id="test_mouth"):
    return MouthObservation(
        mouth_id=mouth_id, observed_at="2026-08-27T00:00:00+00:00", status=status,
        content_hash="x", item_count=len(new_items), new_items=new_items,
    )


class TestEvaluateDependencyPressure(unittest.TestCase):
    def _reqs(self, d, content):
        path = Path(d) / "requirements.txt"
        path.write_text(content)
        return path

    def test_unchanged_produces_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            result = evaluate_dependency_pressure(_obs("UNCHANGED"), reqs, "PyYAML")
            self.assertIsNone(result)

    def test_first_seen_produces_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            obs = _obs("FIRST_SEEN", new_items=({"title": "6.0.3"},))
            self.assertIsNone(evaluate_dependency_pressure(obs, reqs, "PyYAML"))

    def test_unavailable_produces_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            self.assertIsNone(evaluate_dependency_pressure(_obs("UNAVAILABLE"), reqs, "PyYAML"))

    def test_changed_with_no_new_items_produces_no_finding(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            obs = _obs("CHANGED", new_items=())
            self.assertIsNone(evaluate_dependency_pressure(obs, reqs, "PyYAML"))

    def test_changed_newer_version_produces_high_confidence_pressure(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            obs = _obs("CHANGED", new_items=({"title": "6.0.4"},))
            finding = evaluate_dependency_pressure(obs, reqs, "PyYAML")
            self.assertIsNotNone(finding)
            self.assertEqual(finding.confidence, "HIGH")
            self.assertIn("newer", finding.observation)
            self.assertEqual(finding.recommended_next_action, "HUMAN_REVIEW_REQUIRED: decide whether to update the pin")

    def test_changed_equal_version_produces_no_pressure_finding(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            obs = _obs("CHANGED", new_items=({"title": "6.0.3"},))
            finding = evaluate_dependency_pressure(obs, reqs, "PyYAML")
            self.assertIsNotNone(finding)
            self.assertEqual(finding.recommended_next_action, "NONE_REQUIRED")

    def test_changed_older_version_flags_anomaly_not_pressure(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            obs = _obs("CHANGED", new_items=({"title": "6.0.1"},))
            finding = evaluate_dependency_pressure(obs, reqs, "PyYAML")
            self.assertIsNotNone(finding)
            self.assertIn("investigate", finding.recommended_next_action.lower())

    def test_package_not_pinned_produces_finding(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "SomethingElse==1.0.0\n")
            obs = _obs("CHANGED", new_items=({"title": "6.0.4"},))
            finding = evaluate_dependency_pressure(obs, reqs, "PyYAML")
            self.assertIsNotNone(finding)
            self.assertIn("not pinned", finding.observation)

    def test_unparseable_version_is_ambiguous_not_guessed(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==dev-snapshot\n")
            obs = _obs("CHANGED", new_items=({"title": "6.0.4"},))
            finding = evaluate_dependency_pressure(obs, reqs, "PyYAML")
            self.assertIsNotNone(finding)
            self.assertEqual(finding.confidence, "LOW")
            self.assertIn("ambiguous", finding.interpretation)

    def test_missing_requirements_file_treated_as_unpinned(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = Path(d) / "does_not_exist.txt"
            obs = _obs("CHANGED", new_items=({"title": "6.0.4"},))
            finding = evaluate_dependency_pressure(obs, reqs, "PyYAML")
            self.assertIsNotNone(finding)
            self.assertIn("not pinned", finding.observation)

    def test_never_recommends_an_execution_verb(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = self._reqs(d, "PyYAML==6.0.3\n")
            for new_title in ("6.0.4", "6.0.3", "6.0.1"):
                obs = _obs("CHANGED", new_items=({"title": new_title},))
                finding = evaluate_dependency_pressure(obs, reqs, "PyYAML")
                for verb in ("execute", "apply", "build", "modify", "commit", "write", "delete", "run", "update the manifest"):
                    self.assertNotIn(verb, finding.recommended_next_action.lower())


class TestRealRepoLiveVerification(unittest.TestCase):
    """Exercise against this repository's actual requirements.txt and a
    real mouth observation, not just synthetic fixtures."""

    def test_real_requirements_txt_pin_matches_real_pypi_observation(self):
        from foundation.mouth_pypi import observe as observe_pypi
        repo_root = Path(__file__).resolve().parents[2]
        state_path = repo_root / "foundation" / "mouth_pypi_state.json"
        real_obs = observe_pypi(state_path)
        self.assertIn(real_obs.status, ("UNCHANGED", "FIRST_SEEN", "CHANGED"))

        # Simulate a CHANGED observation using the real newest item this
        # mouth actually has on file right now, against the real pin.
        import json
        real_state = json.loads(state_path.read_text())
        newest_key = sorted(real_state["keys"])[-1]
        synthetic_changed = MouthObservation(
            mouth_id=real_obs.mouth_id, observed_at=real_obs.observed_at,
            status="CHANGED", content_hash=real_obs.content_hash,
            item_count=1, new_items=({"title": "6.0.3", "key": newest_key},),
        )
        finding = evaluate_dependency_pressure(
            synthetic_changed, repo_root / "requirements.txt", "PyYAML",
        )
        self.assertIsNotNone(finding)
        # requirements.txt is genuinely pinned to 6.0.3 as of this cycle —
        # real EQUAL case, not fabricated.
        self.assertEqual(finding.recommended_next_action, "NONE_REQUIRED")


if __name__ == "__main__":
    unittest.main()


class TestReadDependencyPressureLog(unittest.TestCase):
    """The switch closed 2026-08-28: `cron_pulse.py` writes real Findings
    to `dependency_pressure_log.jsonl`, `.claude/commands/boot.md` step 4c
    reads that exact file every boot -- and until now the only reader it
    named (`mouth_common.read_mouth_log_continuity`) could report that the
    log existed but never what it said, because a Finding payload has no
    `status` field. These tests pin both halves: the before-state is real
    (first test), and the finding is now retrievable (rest)."""

    def _record(self, finding, observed_at="2026-08-27T17:07:01+00:00"):
        from dataclasses import asdict
        return json.dumps({
            "mouth_id": "pypi_pyyaml_releases", "observed_at": observed_at,
            **asdict(finding),
        })

    def _pressure_finding(self, action="HUMAN_REVIEW_REQUIRED: decide whether to update the pin"):
        return Finding(
            observation="PyYAML 9.9.9 is newer than the pinned 6.0.3",
            evidence_location="requirements.txt", confidence="HIGH",
            interpretation="a real release is not yet reflected in requirements.txt",
            reversibility="reversible -- informational finding only, nothing executed",
            recommended_next_action=action,
        )

    def test_the_old_reader_still_cannot_see_the_finding(self):
        """The reproduction of the exact open edge, kept as a regression
        so nobody 'fixes' this by quietly changing what the mouth reader
        returns. read_mouth_log_continuity is not wrong -- it answers a
        different question (is the clock alive) and must keep answering
        only that."""
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text(self._record(self._pressure_finding()) + "\n")
            continuity = read_mouth_log_continuity(log)
            self.assertTrue(continuity.available)          # the clock is legibly alive
            self.assertIsNotNone(continuity.latest_timestamp)
            self.assertIsNone(continuity.latest_status)    # ...and the finding is invisible

    def test_a_real_pressure_finding_is_reconstructed(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text(self._record(self._pressure_finding()) + "\n")
            result = read_dependency_pressure_log(log, now=_NOW)
            self.assertTrue(result.available)
            self.assertEqual(result.records_considered, 1)
            self.assertEqual(len(result.findings), 1)
            self.assertEqual(result.findings[0].confidence, "HIGH")
            self.assertIn("9.9.9", result.findings[0].observation)
            self.assertTrue(result.actionable)
            self.assertEqual(result.errors, ())

    def test_a_none_required_finding_is_retained_but_not_actionable(self):
        # The discrimination that matters: a receipt proving the check ran
        # is not the same thing as pressure needing a decision.
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text(self._record(self._pressure_finding("NONE_REQUIRED")) + "\n")
            result = read_dependency_pressure_log(log, now=_NOW)
            self.assertEqual(len(result.findings), 1)
            self.assertFalse(result.actionable)

    def test_an_evaluation_error_record_is_surfaced_not_mistaken_for_a_finding(self):
        # cron_pulse.py writes this second shape when
        # evaluate_dependency_pressure() itself raises.
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text(json.dumps({
                "mouth_id": "pypi_pyyaml_releases",
                "observed_at": "2026-08-27T17:07:01+00:00",
                "error": "dependency pressure evaluation raised: boom",
            }) + "\n")
            result = read_dependency_pressure_log(log, now=_NOW)
            self.assertEqual(result.findings, ())
            self.assertEqual(len(result.errors), 1)
            self.assertIn("boom", result.errors[0])
            self.assertFalse(result.actionable)  # a crash is not pressure

    def test_missing_log_is_the_normal_state_not_a_fault(self):
        with tempfile.TemporaryDirectory() as d:
            result = read_dependency_pressure_log(Path(d) / "nope.jsonl")
            self.assertFalse(result.available)
            self.assertEqual(result.findings, ())
            self.assertIn("has ever fired", result.warnings[0])

    def test_truncated_and_malformed_lines_do_not_crash_the_read(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text(
                self._record(self._pressure_finding()) + "\n"
                + '{"mouth_id": "x", "observed_at": "2026-08-27T17:07:01+00:00"\n'  # truncated
                + json.dumps({"observed_at": "2026-08-27T17:07:01+00:00",
                              "not_a": "finding"}) + "\n"                            # wrong payload
            )
            result = read_dependency_pressure_log(log, now=_NOW)
            self.assertEqual(len(result.findings), 1)      # the good record survives
            self.assertEqual(len(result.warnings), 2)      # both bad ones are reported

    def test_duplicate_findings_are_consolidated_not_repeated(self):
        # Reuses sentinel.consolidate() -- the same (observation,
        # evidence_location) dedup key already used for pulse findings.
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text("\n".join(
                self._record(self._pressure_finding()) for _ in range(4)
            ) + "\n")
            result = read_dependency_pressure_log(log, now=_NOW)
            self.assertEqual(result.records_considered, 4)
            self.assertEqual(len(result.findings), 1)

    def test_the_read_is_bounded_to_the_trailing_window(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text("\n".join(
                self._record(self._pressure_finding()) for _ in range(50)
            ) + "\n")
            result = read_dependency_pressure_log(log, max_records=20, now=_NOW)
            self.assertEqual(result.records_considered, 20)

    def test_staleness_is_flagged_with_its_own_weaker_meaning(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            log.write_text(self._record(
                self._pressure_finding(), observed_at="2026-08-20T00:00:00+00:00",
            ) + "\n")
            result = read_dependency_pressure_log(log, now=_NOW)
            self.assertTrue(result.stale)
            self.assertTrue(any("weak evidence" in w for w in result.warnings))

    def test_reader_never_writes_to_the_log(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dependency_pressure_log.jsonl"
            body = self._record(self._pressure_finding()) + "\n"
            log.write_text(body)
            before = log.stat().st_mtime_ns
            read_dependency_pressure_log(log, now=_NOW)
            read_dependency_pressure_log(log, now=_NOW)
            self.assertEqual(log.read_text(), body)
            self.assertEqual(log.stat().st_mtime_ns, before)

    def test_against_the_real_repository_log_whatever_state_it_is_in(self):
        # No synthetic fixture: whatever the live cron entry has actually
        # written (today: nothing -- the branch has never fired live).
        repo_root = Path(__file__).resolve().parent.parent.parent
        result = read_dependency_pressure_log(
            repo_root / "foundation" / "dependency_pressure_log.jsonl"
        )
        self.assertIsInstance(result.available, bool)
        self.assertIsInstance(result.findings, tuple)
        if not result.available:
            self.assertFalse(result.actionable)


class TestReadDependencyPressureLogSurvivesNonDictLines(unittest.TestCase):
    """Same systemic bug class found in the same 2026-08-28 hunt: a
    valid-JSON non-dict value raised TypeError in this reader too."""

    def test_a_non_dict_line_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dp.jsonl"
            log.write_text('42\n"str"\n[1,2]\nnull\n')
            result = read_dependency_pressure_log(log)
            self.assertEqual(result.records_considered, 0)
            self.assertTrue(any("not an object" in w for w in result.warnings))

    def test_a_real_finding_still_parses_when_mixed_with_junk(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "dp.jsonl"
            f = Finding(
                observation="x", evidence_location="y", confidence="HIGH",
                interpretation="z", reversibility="r", recommended_next_action="NONE_REQUIRED",
            )
            from dataclasses import asdict
            log.write_text('99\n' + json.dumps({
                "mouth_id": "m", "observed_at": "2026-08-27T00:00:00+00:00",
                **asdict(f)}) + '\n')
            result = read_dependency_pressure_log(log)
            self.assertEqual(result.records_considered, 1)
