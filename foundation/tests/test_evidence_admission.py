import unittest
from foundation.evidence_admission import admit_evidence, normalize_observation

class EvidenceAdmissionTests(unittest.TestCase):
    def test_normalization_is_provenance_bound_and_deterministic(self):
        a = normalize_observation("github", {"b": 2, "a": 1}, source_url="https://example.test/x", observed_at="2026-09-24T00:00:00Z")
        b = normalize_observation("github", {"a": 1, "b": 2}, source_url="https://example.test/x", observed_at="2026-09-24T00:00:00Z")
        self.assertEqual(a.fingerprint, b.fingerprint)
        self.assertEqual(admit_evidence(a), a)

    def test_missing_provenance_is_rejected(self):
        with self.assertRaises(ValueError):
            normalize_observation("github", {"x": 1}, source_url="", observed_at="2026-09-24T00:00:00Z")

    def test_integrity_marker_is_required_for_admission(self):
        a = normalize_observation("github", {"x": 1}, source_url="https://example.test/x", observed_at="2026-09-24T00:00:00Z")
        broken = type(a)(a.source_id, a.source_url, a.observed_at, a.payload, "bad")
        with self.assertRaises(ValueError):
            admit_evidence(broken)

if __name__ == "__main__":
    unittest.main()
