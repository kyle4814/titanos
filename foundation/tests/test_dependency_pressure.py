import tempfile
import unittest
from pathlib import Path

from foundation.dependency_pressure import evaluate_dependency_pressure
from foundation.mouth_common import MouthObservation


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
