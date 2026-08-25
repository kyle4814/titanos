import unittest

from narrative.store.narrative_atom_store import (
    AtomRecord, IllegalAtomTransition, NarrativeAtomStore, SelfCanonizationForbidden,
)


class TestRegister(unittest.TestCase):
    def test_valid_atom_registers(self):
        store = NarrativeAtomStore()
        rec = store.register("A1", created_by="alice")
        self.assertEqual(rec.state, "RAW")
        self.assertEqual(rec.created_by, "alice")

    def test_duplicate_id_rejected(self):
        store = NarrativeAtomStore()
        store.register("A1", created_by="alice")
        with self.assertRaises(ValueError):
            store.register("A1", created_by="bob")

    def test_empty_created_by_rejected(self):
        store = NarrativeAtomStore()
        with self.assertRaises(ValueError):
            store.register("A1", created_by="")


class TestLegalPromotion(unittest.TestCase):
    def test_raw_to_observed_succeeds(self):
        store = NarrativeAtomStore()
        store.register("A1", created_by="alice")
        rec = store.promote("A1", "OBSERVED", reason="first pass")
        self.assertEqual(rec.state, "OBSERVED")

    def test_full_chain_to_supported(self):
        store = NarrativeAtomStore()
        store.register("A1", created_by="alice")
        store.promote("A1", "CLASSIFIED", reason="x")
        store.promote("A1", "CONNECTED", reason="x")
        store.promote("A1", "CHALLENGED", reason="x")
        store.promote("A1", "TESTED", reason="x")
        rec = store.promote("A1", "SUPPORTED", reason="x")
        self.assertEqual(rec.state, "SUPPORTED")


class TestIllegalPromotion(unittest.TestCase):
    def test_raw_to_canonical_abstraction_rejected(self):
        store = NarrativeAtomStore()
        store.register("A1", created_by="alice")
        with self.assertRaises(IllegalAtomTransition):
            store.promote("A1", "CANONICAL_ABSTRACTION", reason="x", reviewed_by="bob")

    def test_unregistered_atom_raises_keyerror(self):
        store = NarrativeAtomStore()
        with self.assertRaises(KeyError):
            store.promote("GHOST", "OBSERVED", reason="x")


class TestReviewSeparation(unittest.TestCase):
    def _to_supported(self, store, atom_id="A1", created_by="alice"):
        store.register(atom_id, created_by=created_by)
        store.promote(atom_id, "CLASSIFIED", reason="x")
        store.promote(atom_id, "CONNECTED", reason="x")
        store.promote(atom_id, "CHALLENGED", reason="x")
        store.promote(atom_id, "TESTED", reason="x")
        store.promote(atom_id, "SUPPORTED", reason="x")

    def test_self_canonization_forbidden(self):
        store = NarrativeAtomStore()
        self._to_supported(store, created_by="alice")
        with self.assertRaises(SelfCanonizationForbidden):
            store.promote("A1", "CANONICAL_ABSTRACTION", reason="x", reviewed_by="alice")

    def test_independent_reviewer_succeeds(self):
        store = NarrativeAtomStore()
        self._to_supported(store, created_by="alice")
        rec = store.promote("A1", "CANONICAL_ABSTRACTION", reason="strong evidence", reviewed_by="bob")
        self.assertEqual(rec.state, "CANONICAL_ABSTRACTION")

    def test_missing_reviewer_fails_closed(self):
        store = NarrativeAtomStore()
        self._to_supported(store, created_by="alice")
        with self.assertRaises(IllegalAtomTransition):
            store.promote("A1", "CANONICAL_ABSTRACTION", reason="x", reviewed_by=None)

    def test_empty_reviewer_string_fails_closed(self):
        store = NarrativeAtomStore()
        self._to_supported(store, created_by="alice")
        with self.assertRaises(IllegalAtomTransition):
            store.promote("A1", "CANONICAL_ABSTRACTION", reason="x", reviewed_by="")

    def test_missing_reason_rejected(self):
        store = NarrativeAtomStore()
        self._to_supported(store, created_by="alice")
        with self.assertRaises(ValueError):
            store.promote("A1", "CANONICAL_ABSTRACTION", reason="   ", reviewed_by="bob")


class TestAppendOnlySurface(unittest.TestCase):
    def test_no_delete_purge_clear_remove_methods(self):
        store = NarrativeAtomStore()
        for method in ("delete", "purge", "clear", "remove"):
            self.assertFalse(hasattr(store, method), f"must not expose '{method}'")


class TestHistory(unittest.TestCase):
    def test_registration_and_promotions_remain_in_history(self):
        store = NarrativeAtomStore()
        store.register("A1", created_by="alice")
        store.promote("A1", "OBSERVED", reason="first")
        store.promote("A1", "CLASSIFIED", reason="second")
        rec = store.get("A1")
        self.assertEqual(len(rec.history), 3)
        self.assertEqual(rec.history[0]["to"], "RAW")
        self.assertEqual(rec.history[1]["to"], "OBSERVED")
        self.assertEqual(rec.history[2]["to"], "CLASSIFIED")

    def test_failed_promotion_does_not_corrupt_history(self):
        store = NarrativeAtomStore()
        store.register("A1", created_by="alice")
        with self.assertRaises(IllegalAtomTransition):
            store.promote("A1", "CANONICAL_ABSTRACTION", reason="x", reviewed_by="bob")
        rec = store.get("A1")
        self.assertEqual(len(rec.history), 1)  # only the initial registration
        self.assertEqual(rec.state, "RAW")

    def test_get_missing_atom_returns_none(self):
        store = NarrativeAtomStore()
        self.assertIsNone(store.get("GHOST"))


if __name__ == "__main__":
    unittest.main()
