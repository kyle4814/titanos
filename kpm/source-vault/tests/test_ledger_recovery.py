"""A truncated final line must not brick the provenance vault.

REPRODUCED BEFORE IT WAS FIXED

`_replay()` called `json.loads(line)` with no guard. Appending one
partial line to a three-record ledger -- exactly what a process killed
mid-append leaves behind -- raised `json.JSONDecodeError` out through
`SourceRegistry.__init__`. The vault could not be constructed at all,
and three intact records still on disk became unreachable until a human
hand-edited the file.

The fix is position-sensitive on purpose. This is a provenance store:
silently skipping any malformed line would drop evidence and say nothing
about it, which is worse than crashing. A malformed LAST line is an
interrupted append and is recoverable; a malformed line with intact
lines after it is a hole nothing wrote by accident, and still refuses.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from registry import LedgerCorrupted, SourceRegistry  # noqa: E402

TRUNCATED = '{"artifact_id": "AR-partial", "conte'


class _Vault:
    def __init__(self, root: Path, n: int = 3):
        self.root = root
        self.ledger = root / "registry.jsonl"
        reg = self._open()
        for i in range(n):
            reg.ingest_source(f"content {i}".encode(), source_type="text",
                              source_location=f"test://{i}",
                              author_or_origin="regression")
        self.reg = reg

    def _open(self):
        return SourceRegistry(archive_dir=self.root / "archive",
                              registry_path=self.ledger)

    reopen = _open


class TestInterruptedAppendIsRecoverable(unittest.TestCase):

    def test_a_truncated_final_line_does_not_prevent_construction(self):
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            with open(v.ledger, "a") as fh:
                fh.write(TRUNCATED)
            reopened = v.reopen()           # must not raise
            self.assertEqual(len(reopened.all_records()), 3)

    def test_the_skipped_line_is_reported_not_hidden(self):
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            with open(v.ledger, "a") as fh:
                fh.write(TRUNCATED)
            warnings = v.reopen().recovery_warnings
            self.assertEqual(len(warnings), 1)
            self.assertIn("interrupted", warnings[0])

    def test_a_clean_ledger_reports_no_warnings(self):
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            self.assertEqual(v.reopen().recovery_warnings, ())

    def test_recovery_warnings_exists_even_with_no_ledger_file(self):
        """A caller must be able to check it unconditionally."""
        with tempfile.TemporaryDirectory() as d:
            reg = SourceRegistry(archive_dir=Path(d) / "a",
                                 registry_path=Path(d) / "absent.jsonl")
            self.assertEqual(reg.recovery_warnings, ())

    def test_a_final_line_with_wrong_fields_is_also_recoverable(self):
        """Valid JSON, wrong shape -- SourceRecord(**obj) raises TypeError,
        which is the same class of interrupted-write damage."""
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            with open(v.ledger, "a") as fh:
                fh.write(json.dumps({"unexpected": "shape"}) + "\n")
            self.assertEqual(len(v.reopen().all_records()), 3)


class TestAHoleInTheMiddleIsRefused(unittest.TestCase):
    """The half that keeps this honest. A recoverable tail must not become
    a licence to silently drop records anywhere in the file."""

    def _corrupt_line(self, ledger: Path, index: int) -> None:
        lines = ledger.read_text().splitlines()
        lines[index] = TRUNCATED
        ledger.write_text("\n".join(lines) + "\n")

    def test_a_corrupt_middle_line_refuses_to_load(self):
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            self._corrupt_line(v.ledger, 1)
            with self.assertRaises(LedgerCorrupted):
                v.reopen()

    def test_a_corrupt_first_line_refuses_to_load(self):
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            self._corrupt_line(v.ledger, 0)
            with self.assertRaises(LedgerCorrupted):
                v.reopen()

    def test_the_refusal_names_the_line_and_why(self):
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            self._corrupt_line(v.ledger, 1)
            with self.assertRaises(LedgerCorrupted) as ctx:
                v.reopen()
            msg = str(ctx.exception)
            self.assertIn("line 2 of 3", msg)
            self.assertIn("NOT the final line", msg)

    def test_partial_loading_never_happens_on_refusal(self):
        """A refusal must not leave a half-populated registry behind."""
        with tempfile.TemporaryDirectory() as d:
            v = _Vault(Path(d))
            self._corrupt_line(v.ledger, 1)
            try:
                v.reopen()
                self.fail("expected LedgerCorrupted")
            except LedgerCorrupted:
                pass
            # The on-disk ledger is untouched by a failed load.
            self.assertEqual(len(v.ledger.read_text().splitlines()), 3)


class TestTheAppendIsDurable(unittest.TestCase):

    def test_ledger_write_is_a_single_call_and_fsynced(self):
        """The two-write shape (body, then newline) left a second window
        in which a crash yields an unterminated line."""
        src = (Path(__file__).resolve().parents[1] / "registry.py").read_text()
        append = src.split("def _append_to_ledger")[1].split("def ")[0]
        self.assertIn("os.fsync", append)
        self.assertEqual(append.count("fh.write("), 1)


if __name__ == "__main__":
    unittest.main()
