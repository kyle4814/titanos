import unittest

from foundation.crystal import Crystal, CrystalStore


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


if __name__ == "__main__":
    unittest.main()
