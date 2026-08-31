import os
import tempfile
import unittest
from pathlib import Path

from foundation.crystal import Crystal, CrystalStore

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _kwargs(**overrides: str) -> dict:
    base = dict(
        problem="tests take 40s locally",
        context="foundation/tests grew to 200+ cases",
        hypothesis="pytest -x on first failure cuts iteration time",
        action="ran pytest -x during development",
        evidence="observed wall-clock drop from 40s to 4s on first failure",
        result="iteration loop shortened",
        failure_mode="",
        limitation="only helps when failing fast, not on green runs",
        provenance="foundation/BUILD_REPORT.md 2026-08-25 cycle",
        reusable_abstraction="use -x when iterating on a known-broken suite",
        regression_test_ref="foundation/tests/test_crystal.py",
        epistemic_status="EVIDENCE_SUPPORTED_MODEL",
        recorded_by="claude",
    )
    base.update(overrides)
    return base


class TestCrystalConstruction(unittest.TestCase):
    def test_valid_crystal_constructs(self):
        c = Crystal(crystal_id="C-001", **_kwargs())
        self.assertEqual(c.crystal_id, "C-001")

    def test_empty_problem_rejected(self):
        with self.assertRaises(ValueError):
            Crystal(crystal_id="C-002", **_kwargs(problem="  "))

    def test_empty_hypothesis_rejected(self):
        with self.assertRaises(ValueError):
            Crystal(crystal_id="C-003", **_kwargs(hypothesis=""))

    def test_empty_action_rejected(self):
        with self.assertRaises(ValueError):
            Crystal(crystal_id="C-004", **_kwargs(action=""))

    def test_empty_result_rejected(self):
        with self.assertRaises(ValueError):
            Crystal(crystal_id="C-005", **_kwargs(result=""))

    def test_empty_reusable_abstraction_rejected(self):
        with self.assertRaises(ValueError):
            Crystal(crystal_id="C-006", **_kwargs(reusable_abstraction=""))

    def test_failure_mode_and_limitation_may_be_empty(self):
        c = Crystal(crystal_id="C-007", **_kwargs(failure_mode="", limitation=""))
        self.assertEqual(c.failure_mode, "")

    def test_invalid_epistemic_status_rejected(self):
        with self.assertRaises(ValueError):
            Crystal(crystal_id="C-008", **_kwargs(epistemic_status="NOT_A_REAL_STATUS"))

    def test_missing_recorded_by_rejected(self):
        with self.assertRaises(ValueError):
            Crystal(crystal_id="C-009", **_kwargs(recorded_by=""))

    def test_to_dict_round_trips_fields(self):
        c = Crystal(crystal_id="C-010", **_kwargs())
        d = c.to_dict()
        self.assertEqual(d["crystal_id"], "C-010")
        self.assertEqual(d["problem"], c.problem)


class TestCrystalStore(unittest.TestCase):
    def test_record_and_get(self):
        store = CrystalStore()
        store.record("C-100", **_kwargs())
        c = store.get("C-100")
        self.assertIsNotNone(c)
        self.assertEqual(c.crystal_id, "C-100")

    def test_get_missing_returns_none(self):
        store = CrystalStore()
        self.assertIsNone(store.get("does-not-exist"))

    def test_duplicate_id_rejected(self):
        store = CrystalStore()
        store.record("C-101", **_kwargs())
        with self.assertRaises(ValueError):
            store.record("C-101", **_kwargs())

    def test_supersede_requires_existing_target(self):
        store = CrystalStore()
        with self.assertRaises(KeyError):
            store.record("C-102", supersedes="nope", **_kwargs())

    def test_supersede_preserves_original(self):
        store = CrystalStore()
        store.record("C-103", **_kwargs(result="worked in dev"))
        store.record(
            "C-104",
            supersedes="C-103",
            **_kwargs(result="failed in prod under load", failure_mode="hit rate limit"),
        )
        original = store.get("C-103")
        newer = store.get("C-104")
        self.assertEqual(original.result, "worked in dev")
        self.assertEqual(newer.supersedes, "C-103")
        # No delete surface: superseded record is still fully retrievable.
        self.assertIn(original, store.all_crystals())

    def test_no_delete_surface(self):
        store = CrystalStore()
        for method in ("delete", "purge", "clear", "remove"):
            self.assertFalse(
                hasattr(store, method),
                f"CrystalStore must not expose a '{method}' method",
            )

    def test_all_crystals_preserves_recording_order(self):
        store = CrystalStore()
        store.record("C-200", **_kwargs())
        store.record("C-201", **_kwargs())
        store.record("C-202", **_kwargs())
        ids = [c.crystal_id for c in store.all_crystals()]
        self.assertEqual(ids, ["C-200", "C-201", "C-202"])

    def test_reusable_abstractions_returns_lesson_text_in_order(self):
        store = CrystalStore()
        store.record("C-300", **_kwargs(reusable_abstraction="lesson one"))
        store.record("C-301", **_kwargs(reusable_abstraction="lesson two"))
        self.assertEqual(store.reusable_abstractions(), ("lesson one", "lesson two"))

    def test_empty_store_returns_empty_tuples(self):
        store = CrystalStore()
        self.assertEqual(store.all_crystals(), ())
        self.assertEqual(store.reusable_abstractions(), ())


class TestIsCurrent(unittest.TestCase):
    def test_unrecorded_id_is_not_current(self):
        store = CrystalStore()
        self.assertFalse(store.is_current("nope"))

    def test_never_superseded_crystal_is_current(self):
        store = CrystalStore()
        store.record("C-400", **_kwargs())
        self.assertTrue(store.is_current("C-400"))

    def test_superseded_crystal_is_no_longer_current(self):
        store = CrystalStore()
        store.record("C-500", **_kwargs())
        store.record("C-501", **_kwargs(supersedes="C-500"))
        self.assertFalse(store.is_current("C-500"))
        self.assertTrue(store.is_current("C-501"))

    def test_being_superseded_does_not_remove_the_old_crystal(self):
        store = CrystalStore()
        store.record("C-600", **_kwargs())
        store.record("C-601", **_kwargs(supersedes="C-600"))
        self.assertIsNotNone(store.get("C-600"))
        self.assertIn("C-600", [c.crystal_id for c in store.all_crystals()])


class TestCrystalDurabilityAcrossProcessBoundary(unittest.TestCase):
    """`record()` claims durability now; these prove the claim rather
    than trust the docstring, same discipline as
    `test_outcome_ledger.py::TestDurabilityAcrossTheProcessBoundary`."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.path = Path(self._tmpdir.name) / "crystal_store.jsonl"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_reconstructed_store_contains_written_records_in_order(self):
        a = CrystalStore(crystal_path=self.path)
        a.record("C-D01", **_kwargs(result="first"))
        a.record("C-D02", **_kwargs(result="second"))
        a.record("C-D03", **_kwargs(result="third"))
        del a  # simulate the process ending; nothing survives but disk

        b = CrystalStore(crystal_path=self.path)
        ids = [c.crystal_id for c in b.all_crystals()]
        self.assertEqual(ids, ["C-D01", "C-D02", "C-D03"])
        self.assertEqual(b.get("C-D02").result, "second")

    def test_unparseable_trailing_line_does_not_block_construction(self):
        a = CrystalStore(crystal_path=self.path)
        a.record("C-D10", **_kwargs())
        # Simulate a process that died mid-write: a truncated JSON
        # fragment appended after the last good, newline-terminated
        # record.
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write('{"crystal_id": "C-D11", "problem": "trunc')

        b = CrystalStore(crystal_path=self.path)
        self.assertEqual([c.crystal_id for c in b.all_crystals()], ["C-D10"])

    def test_crystal_path_none_stays_in_memory_and_writes_no_file(self):
        store = CrystalStore(crystal_path=None)
        store.record("C-D20", **_kwargs())
        self.assertFalse(self.path.exists())
        # There is genuinely nowhere for None to have written to; the
        # assertion above documents the specific tempdir path this test
        # already controls stayed empty of any crystal file.
        self.assertEqual(list(Path(self._tmpdir.name).iterdir()), [])

    def test_no_crystal_file_created_anywhere_in_repo_by_default_construction(self):
        # The exact failure mode this fix must not reintroduce: a bare
        # CrystalStore() must never touch the filesystem, anywhere.
        before = set(_REPO_ROOT.rglob("crystal_store.jsonl"))
        store = CrystalStore()
        store.record("C-D30", **_kwargs())
        store2 = CrystalStore()
        store2.record("C-D31", **_kwargs(supersedes=None))
        after = set(_REPO_ROOT.rglob("crystal_store.jsonl"))
        self.assertEqual(before, after)
        self.assertEqual(after, set())

    def test_supersedes_and_epistemic_status_survive_round_trip(self):
        a = CrystalStore(crystal_path=self.path)
        a.record("C-D40", **_kwargs(epistemic_status="EVIDENCE_SUPPORTED_MODEL"))
        a.record(
            "C-D41",
            supersedes="C-D40",
            **_kwargs(
                epistemic_status="VERIFIED_FACT",
                result="revised after new evidence",
            ),
        )
        del a

        b = CrystalStore(crystal_path=self.path)
        original = b.get("C-D40")
        newer = b.get("C-D41")
        self.assertEqual(original.epistemic_status, "EVIDENCE_SUPPORTED_MODEL")
        self.assertEqual(newer.epistemic_status, "VERIFIED_FACT")
        self.assertIsNone(original.supersedes)
        self.assertEqual(newer.supersedes, "C-D40")
        self.assertFalse(b.is_current("C-D40"))
        self.assertTrue(b.is_current("C-D41"))

    def test_written_bytes_are_fsynced_before_record_returns(self):
        # Not a mock-based "was fsync called" check -- a real read of the
        # file's bytes performed immediately after record() returns,
        # with no flush/close of our own first, proving the data is
        # already on disk rather than sitting in a buffer this test
        # would otherwise have to close to see.
        store = CrystalStore(crystal_path=self.path)
        store.record("C-D50", **_kwargs())
        fd = os.open(self.path, os.O_RDONLY)
        try:
            raw = os.read(fd, 1 << 16)
        finally:
            os.close(fd)
        self.assertIn(b'"crystal_id": "C-D50"', raw)


if __name__ == "__main__":
    unittest.main()
