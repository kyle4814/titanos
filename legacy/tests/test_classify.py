"""Unit tests for the legacy classification tool, using synthetic files —
not the real 3,058-file corpus (that's exercised by running classify.py
directly and is documented, not re-run on every test invocation)."""

import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from legacy.classify import classify_track_a, classify_track_b  # noqa: E402


class TestTrackA(unittest.TestCase):
    def test_everything_defaults_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.yaml"
            p.write_text("hello: world\n")
            recs = classify_track_a([p])
            self.assertEqual(recs[0].classification, "UNKNOWN")
            self.assertTrue(recs[0].review_required)
            self.assertEqual(recs[0].reason,
                             "Track A: default classification, no automated "
                             "evaluation performed")

    def test_content_is_never_read_for_classification(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.yaml"
            p.write_text("artifact_id: a1\nvalidation_status: VALID\n")
            recs = classify_track_a([p])
            self.assertEqual(recs[0].classification, "UNKNOWN")


class TestTrackB(unittest.TestCase):
    def test_non_conformant_legacy_yaml_is_unrecognised_not_contaminated(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "legacy.yaml"
            p.write_text("some_legacy_key: some_value\nother: 123\n")
            recs = classify_track_b([p])
            self.assertEqual(recs[0].classification, "UNRECOGNISED_YAML")
            self.assertIn("NOT evidence of contamination", recs[0].reason)
            self.assertTrue(recs[0].review_required)

    def test_schema_valid_file_still_requires_review(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "conformant.yaml"
            p.write_text(
                "artifact_id: art-x\nartifact_type: EVIDENCE_RECORD\n"
                'schema_version: "1.0.0"\n'
                'created_at: "2026-08-25T00:00:00Z"\n'
                f'content_hash: "sha256:{"a"*64}"\n'
                "contamination_state: VERIFIED\nclassification: EVIDENCE\n"
            )
            recs = classify_track_b([p])
            self.assertEqual(recs[0].classification, "REVIEW_REQUIRED")
            self.assertTrue(recs[0].review_required)
            self.assertEqual(recs[0].confidence, "STRUCTURAL_ONLY")

    def test_unreadable_file_is_unknown(self):
        recs = classify_track_b([Path("/nonexistent/path/x.yaml")])
        self.assertEqual(recs[0].classification, "UNKNOWN")
        self.assertTrue(recs[0].review_required)

    def test_oversized_file_not_evaluated_and_marked_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "big.yaml"
            p.write_text("x: y\n")
            recs = classify_track_b([p], max_bytes=1)
            self.assertEqual(recs[0].classification, "UNKNOWN")
            self.assertIn("scan ceiling", recs[0].reason)

    def test_no_source_file_is_modified(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.yaml"
            original = "some_legacy_key: some_value\n"
            p.write_text(original)
            classify_track_b([p])
            classify_track_a([p])
            self.assertEqual(p.read_text(), original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
