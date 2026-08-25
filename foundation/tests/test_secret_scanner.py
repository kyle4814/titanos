import tempfile
import unittest
from pathlib import Path

from foundation.secret_scanner import scan


class TestScanSynthetic(unittest.TestCase):
    def test_aws_key_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.py").write_text('KEY = "AKIAABCDEFGHIJKLMNOP"\n')
            report = scan(root)
            self.assertTrue(any("AWS access key" in f.observation for f in report.findings))

    def test_pem_header_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "key.pem").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIExyz\n")
            report = scan(root)
            self.assertTrue(any("PEM private key" in f.observation for f in report.findings))

    def test_generic_secret_assignment_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings.py").write_text('api_key = "sk_live_abcdefghijklmnop123456"\n')
            report = scan(root)
            self.assertTrue(any("secret/token/password" in f.observation for f in report.findings))

    def test_clean_file_has_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.py").write_text("def add(a, b):\n    return a + b\n")
            report = scan(root)
            self.assertEqual(report.findings, ())
            self.assertEqual(report.files_scanned, 1)

    def test_binary_suffix_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "image.png").write_bytes(b"\x89PNG\r\n AKIAABCDEFGHIJKLMNOP")
            report = scan(root)
            self.assertEqual(report.files_scanned, 0)

    def test_excluded_dir_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            git_dir = root / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("AKIAABCDEFGHIJKLMNOP")
            report = scan(root)
            self.assertEqual(report.findings, ())

    def test_single_file_path_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "one.py"
            f.write_text('token = "AKIAABCDEFGHIJKLMNOP"\n')
            report = scan(f)
            self.assertEqual(report.files_scanned, 1)
            self.assertTrue(report.findings)

    def test_duplicate_matches_on_same_line_consolidated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text('KEY = "AKIAABCDEFGHIJKLMNOP"\n')
            (root / "b.py").write_text('KEY = "AKIAABCDEFGHIJKLMNOP"\n')
            report = scan(root)
            # Two distinct files -> two distinct evidence_locations -> not
            # merged by consolidate() (which dedups identical location+obs).
            self.assertEqual(len(report.findings), 2)


class TestToEvidenceString(unittest.TestCase):
    def test_clean_scan_produces_zero_findings_string(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.py").write_text("x = 1\n")
            report = scan(root)
            self.assertIn("0 findings", report.to_evidence_string())

    def test_dirty_scan_names_the_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bad.py").write_text('KEY = "AKIAABCDEFGHIJKLMNOP"\n')
            report = scan(root)
            evidence = report.to_evidence_string()
            self.assertIn("AWS access key", evidence)
            self.assertIn("bad.py", evidence)


class TestScanRealRepo(unittest.TestCase):
    """The real check this module exists for: does the actual tracked
    repository contain anything HIGH confidence right now?"""

    def test_no_high_confidence_findings_in_this_repository(self):
        repo_root = Path(__file__).resolve().parents[2]
        report = scan(repo_root)
        # This test file itself contains synthetic AKIA-shaped strings as
        # fixtures (test_aws_key_detected et al.) -- those are expected
        # matches proving the scanner works, not a real repository leak.
        this_file = str(Path(__file__).resolve())
        high = [f for f in report.findings
                if f.confidence == "HIGH" and not f.evidence_location.startswith(this_file)]
        self.assertEqual(high, [], f"unexpected HIGH-confidence findings: {high}")


if __name__ == "__main__":
    unittest.main()
