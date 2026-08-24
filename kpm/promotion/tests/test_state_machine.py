import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from kpm.promotion.state_machine import (
    ALL_STATES, TRANSITIONS, IllegalTransition, PromotionStore,
    SelfPromotionForbidden, can_transition,
)


FORBIDDEN_TO_STABLE = ("RAW", "QUARANTINED", "CONTESTED", "DISTILLED", "PROVISIONAL")


class TestTransitionTable(unittest.TestCase):
    def test_all_states_present_as_keys(self):
        for state in ALL_STATES:
            self.assertIn(state, TRANSITIONS)

    def test_only_two_edges_into_stable(self):
        sources_reaching_stable = [
            src for src, dsts in TRANSITIONS.items() if "STABLE" in dsts
        ]
        self.assertEqual(set(sources_reaching_stable), {"TESTED", "HUMAN_REVIEW"})

    def test_forbidden_edges_absent(self):
        for src in FORBIDDEN_TO_STABLE:
            self.assertFalse(can_transition(src, "STABLE"),
                              f"{src} -> STABLE must not be a legal edge")

    def test_deprecated_and_superseded_are_terminal(self):
        self.assertEqual(TRANSITIONS["DEPRECATED"], frozenset())
        self.assertEqual(TRANSITIONS["SUPERSEDED"], frozenset())

    def test_contested_and_quarantined_only_reach_human_review(self):
        self.assertEqual(TRANSITIONS["CONTESTED"], frozenset({"HUMAN_REVIEW"}))
        self.assertEqual(TRANSITIONS["QUARANTINED"], frozenset({"HUMAN_REVIEW"}))

    def test_forward_path_exists(self):
        self.assertTrue(can_transition("RAW", "DISTILLED"))
        self.assertTrue(can_transition("DISTILLED", "PROVISIONAL"))
        self.assertTrue(can_transition("PROVISIONAL", "TESTED"))
        self.assertTrue(can_transition("TESTED", "STABLE"))


class TestPromotionStoreNoDelete(unittest.TestCase):
    def test_no_delete_surface(self):
        store = PromotionStore()
        for name in ("delete", "purge", "clear", "remove"):
            self.assertFalse(hasattr(store, name),
                              f"PromotionStore must not expose '{name}'")


class TestIllegalTransitions(unittest.TestCase):
    def setUp(self):
        self.store = PromotionStore()
        self.store.register("bp-1", created_by="alice")

    def test_raw_to_stable_raises(self):
        with self.assertRaises(IllegalTransition):
            self.store.promote("bp-1", "STABLE", reason="skip ahead",
                                reviewed_by="bob")

    def test_quarantined_to_stable_raises(self):
        self.store.promote("bp-1", "QUARANTINED", reason="held")
        with self.assertRaises(IllegalTransition):
            self.store.promote("bp-1", "STABLE", reason="try to skip",
                                reviewed_by="bob")

    def test_contested_to_stable_raises(self):
        self.store.promote("bp-1", "DISTILLED", reason="distilled")
        self.store.promote("bp-1", "CONTESTED", reason="challenged")
        with self.assertRaises(IllegalTransition):
            self.store.promote("bp-1", "STABLE", reason="try to skip",
                                reviewed_by="bob")

    def test_distilled_to_stable_raises(self):
        self.store.promote("bp-1", "DISTILLED", reason="distilled")
        with self.assertRaises(IllegalTransition):
            self.store.promote("bp-1", "STABLE", reason="try to skip",
                                reviewed_by="bob")

    def test_provisional_to_stable_raises(self):
        self.store.promote("bp-1", "DISTILLED", reason="distilled")
        self.store.promote("bp-1", "PROVISIONAL", reason="provisional")
        with self.assertRaises(IllegalTransition):
            self.store.promote("bp-1", "STABLE", reason="try to skip",
                                reviewed_by="bob")


class TestSelfPromotionForbidden(unittest.TestCase):
    def test_author_cannot_self_promote_via_tested(self):
        store = PromotionStore()
        store.register("bp-2", created_by="alice")
        store.promote("bp-2", "DISTILLED", reason="d")
        store.promote("bp-2", "PROVISIONAL", reason="p")
        store.promote("bp-2", "TESTED", reason="t")
        with self.assertRaises(SelfPromotionForbidden):
            store.promote("bp-2", "STABLE", reason="ship it",
                           reviewed_by="alice")
        # state must not have changed
        self.assertEqual(store.get("bp-2").state, "TESTED")

    def test_author_cannot_self_promote_via_human_review(self):
        store = PromotionStore()
        store.register("bp-3", created_by="alice")
        store.promote("bp-3", "DISTILLED", reason="d")
        store.promote("bp-3", "CONTESTED", reason="c")
        store.promote("bp-3", "HUMAN_REVIEW", reason="escalate")
        with self.assertRaises(SelfPromotionForbidden):
            store.promote("bp-3", "STABLE", reason="ship it",
                           reviewed_by="alice")

    def test_independent_reviewer_can_promote(self):
        store = PromotionStore()
        store.register("bp-4", created_by="alice")
        store.promote("bp-4", "DISTILLED", reason="d")
        store.promote("bp-4", "PROVISIONAL", reason="p")
        store.promote("bp-4", "TESTED", reason="t")
        rec = store.promote("bp-4", "STABLE", reason="reviewed and good",
                             reviewed_by="bob")
        self.assertEqual(rec.state, "STABLE")

    def test_stable_requires_reviewed_by_at_all(self):
        store = PromotionStore()
        store.register("bp-5", created_by="alice")
        store.promote("bp-5", "DISTILLED", reason="d")
        store.promote("bp-5", "PROVISIONAL", reason="p")
        store.promote("bp-5", "TESTED", reason="t")
        with self.assertRaises(IllegalTransition):
            store.promote("bp-5", "STABLE", reason="no reviewer set")


class TestAppendOnlyHistory(unittest.TestCase):
    def test_history_grows_and_is_never_removed(self):
        store = PromotionStore()
        store.register("bp-6", created_by="alice")
        store.promote("bp-6", "DISTILLED", reason="d")
        store.promote("bp-6", "PROVISIONAL", reason="p")
        rec = store.get("bp-6")
        self.assertEqual(len(rec.history), 3)
        self.assertEqual(rec.history[0]["to"], "RAW")
        self.assertEqual(rec.history[1]["to"], "DISTILLED")
        self.assertEqual(rec.history[2]["to"], "PROVISIONAL")


if __name__ == "__main__":
    unittest.main()
