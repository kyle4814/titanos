import unittest

from foundation.flow_switch import (
    ALL_MODES,
    MODE_TRANSITIONS,
    FlowSwitchStore,
    IllegalModeTransition,
    PanicSample,
    can_transition,
    detect_panic,
    recommend_transition,
)


def sample(info: float, verify: float) -> PanicSample:
    return PanicSample(
        information_velocity=info,
        verification_velocity=verify,
        timestamp="2026-08-25T00:00:00Z",
    )


class TestDetectPanic(unittest.TestCase):
    def test_general_panic_case(self):
        self.assertTrue(detect_panic(sample(10, 5)))

    def test_general_no_panic_case(self):
        self.assertFalse(detect_panic(sample(5, 10)))

    def test_equal_velocities_not_panic(self):
        self.assertFalse(detect_panic(sample(5, 5)))

    def test_zero_verification_positive_information_is_panic(self):
        self.assertTrue(detect_panic(sample(1, 0)))

    def test_zero_verification_zero_information_is_not_panic(self):
        self.assertFalse(detect_panic(sample(0, 0)))


class TestModeTransitionsTable(unittest.TestCase):
    def test_all_modes_present_as_keys(self):
        self.assertEqual(set(MODE_TRANSITIONS.keys()), ALL_MODES)

    def test_normal_to_high_complexity_legal(self):
        self.assertTrue(can_transition("NORMAL", "HIGH_COMPLEXITY"))

    def test_normal_to_signal_collapse_legal(self):
        self.assertTrue(can_transition("NORMAL", "SIGNAL_COLLAPSE"))

    def test_high_complexity_to_normal_legal(self):
        self.assertTrue(can_transition("HIGH_COMPLEXITY", "NORMAL"))

    def test_high_complexity_to_signal_collapse_legal(self):
        self.assertTrue(can_transition("HIGH_COMPLEXITY", "SIGNAL_COLLAPSE"))

    def test_signal_collapse_to_recovery_legal(self):
        self.assertTrue(can_transition("SIGNAL_COLLAPSE", "RECOVERY"))

    def test_recovery_to_normal_legal(self):
        self.assertTrue(can_transition("RECOVERY", "NORMAL"))

    def test_recovery_to_high_complexity_legal(self):
        self.assertTrue(can_transition("RECOVERY", "HIGH_COMPLEXITY"))

    def test_signal_collapse_to_normal_illegal(self):
        self.assertFalse(can_transition("SIGNAL_COLLAPSE", "NORMAL"))

    def test_signal_collapse_to_high_complexity_illegal(self):
        self.assertFalse(can_transition("SIGNAL_COLLAPSE", "HIGH_COMPLEXITY"))

    def test_recovery_to_signal_collapse_illegal(self):
        self.assertFalse(can_transition("RECOVERY", "SIGNAL_COLLAPSE"))

    def test_normal_to_recovery_illegal(self):
        self.assertFalse(can_transition("NORMAL", "RECOVERY"))

    def test_no_self_loops_declared(self):
        for mode, targets in MODE_TRANSITIONS.items():
            self.assertNotIn(mode, targets)


class TestFlowSwitchStore(unittest.TestCase):
    def setUp(self):
        self.store = FlowSwitchStore()

    def test_start_session_default_mode(self):
        rec = self.store.start_session("s1")
        self.assertEqual(rec.mode, "NORMAL")
        self.assertEqual(len(rec.history), 1)

    def test_start_session_custom_mode(self):
        rec = self.store.start_session("s2", initial_mode="HIGH_COMPLEXITY")
        self.assertEqual(rec.mode, "HIGH_COMPLEXITY")

    def test_legal_transition_updates_mode(self):
        self.store.start_session("s3")
        rec = self.store.transition(
            "s3", "HIGH_COMPLEXITY",
            reason="rising ambiguity", evidence_for_exit="two independent confirmations",
        )
        self.assertEqual(rec.mode, "HIGH_COMPLEXITY")
        self.assertEqual(len(rec.history), 2)
        self.assertEqual(rec.history[-1]["from"], "NORMAL")
        self.assertEqual(rec.history[-1]["to"], "HIGH_COMPLEXITY")

    def test_illegal_transition_signal_collapse_to_normal_raises(self):
        self.store.start_session("s4", initial_mode="SIGNAL_COLLAPSE")
        with self.assertRaises(IllegalModeTransition):
            self.store.transition(
                "s4", "NORMAL",
                reason="feels fine now", evidence_for_exit="nothing concrete",
            )

    def test_illegal_transition_signal_collapse_to_high_complexity_raises(self):
        self.store.start_session("s5", initial_mode="SIGNAL_COLLAPSE")
        with self.assertRaises(IllegalModeTransition):
            self.store.transition(
                "s5", "HIGH_COMPLEXITY",
                reason="want to keep moving", evidence_for_exit="none",
            )

    def test_illegal_transition_recovery_to_signal_collapse_raises(self):
        self.store.start_session("s6", initial_mode="RECOVERY")
        with self.assertRaises(IllegalModeTransition):
            self.store.transition(
                "s6", "SIGNAL_COLLAPSE",
                reason="re-panicking", evidence_for_exit="none",
            )

    def test_empty_evidence_for_exit_rejected(self):
        self.store.start_session("s7")
        with self.assertRaises(ValueError):
            self.store.transition(
                "s7", "HIGH_COMPLEXITY",
                reason="rising ambiguity", evidence_for_exit="   ",
            )

    def test_empty_reason_rejected(self):
        self.store.start_session("s8")
        with self.assertRaises(ValueError):
            self.store.transition(
                "s8", "HIGH_COMPLEXITY",
                reason="", evidence_for_exit="two independent confirmations",
            )

    def test_full_legal_lifecycle_normal_to_recovery_to_normal(self):
        self.store.start_session("s9")
        self.store.transition("s9", "SIGNAL_COLLAPSE", reason="panic detected",
                               evidence_for_exit="stable invariants identified")
        self.store.transition("s9", "RECOVERY", reason="beginning reconstruction",
                               evidence_for_exit="minimal flow resumed without new panic")
        rec = self.store.transition("s9", "NORMAL", reason="invariants confirmed stable",
                                     evidence_for_exit="n/a")
        self.assertEqual(rec.mode, "NORMAL")
        self.assertEqual(len(rec.history), 4)

    def test_transition_unknown_session_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.store.transition("ghost", "NORMAL", reason="x", evidence_for_exit="y")

    def test_no_delete_method(self):
        self.assertFalse(hasattr(self.store, "delete"))

    def test_no_purge_method(self):
        self.assertFalse(hasattr(self.store, "purge"))

    def test_no_clear_method(self):
        self.assertFalse(hasattr(self.store, "clear"))

    def test_no_remove_method(self):
        self.assertFalse(hasattr(self.store, "remove"))

    def test_get_returns_none_for_unknown(self):
        self.assertIsNone(self.store.get("nope"))

    def test_all_records_reflects_started_sessions(self):
        self.store.start_session("a")
        self.store.start_session("b")
        self.assertEqual(len(self.store.all_records()), 2)


class TestRecommendTransition(unittest.TestCase):
    def test_normal_panicking_recommends_signal_collapse(self):
        self.assertEqual(recommend_transition(sample(10, 1), "NORMAL"), "SIGNAL_COLLAPSE")

    def test_normal_not_panicking_recommends_none(self):
        self.assertIsNone(recommend_transition(sample(1, 10), "NORMAL"))

    def test_high_complexity_panicking_recommends_signal_collapse(self):
        self.assertEqual(recommend_transition(sample(10, 1), "HIGH_COMPLEXITY"), "SIGNAL_COLLAPSE")

    def test_high_complexity_not_panicking_recommends_none(self):
        self.assertIsNone(recommend_transition(sample(1, 10), "HIGH_COMPLEXITY"))

    def test_signal_collapse_panicking_recommends_recovery(self):
        self.assertEqual(recommend_transition(sample(10, 1), "SIGNAL_COLLAPSE"), "RECOVERY")

    def test_signal_collapse_not_panicking_still_recommends_recovery(self):
        # Collapse has no panic-based exit at all — only RECOVERY, whether
        # or not the current sample reads as panicking.
        self.assertEqual(recommend_transition(sample(1, 10), "SIGNAL_COLLAPSE"), "RECOVERY")

    def test_signal_collapse_never_recommends_normal_or_high_complexity(self):
        for info, verify in [(10, 1), (1, 10), (0, 0), (5, 5)]:
            rec = recommend_transition(sample(info, verify), "SIGNAL_COLLAPSE")
            self.assertNotIn(rec, ("NORMAL", "HIGH_COMPLEXITY"))

    def test_recovery_not_panicking_recommends_normal(self):
        self.assertEqual(recommend_transition(sample(1, 10), "RECOVERY"), "NORMAL")

    def test_recovery_panicking_does_not_recommend_signal_collapse(self):
        rec = recommend_transition(sample(10, 1), "RECOVERY")
        self.assertNotEqual(rec, "SIGNAL_COLLAPSE")

    def test_recommend_transition_output_always_legal_or_none(self):
        for mode in ALL_MODES:
            for info, verify in [(10, 1), (1, 10), (0, 0)]:
                rec = recommend_transition(sample(info, verify), mode)
                if rec is not None:
                    self.assertTrue(
                        can_transition(mode, rec),
                        f"recommend_transition suggested illegal edge {mode} -> {rec}",
                    )

    def test_unknown_current_mode_raises(self):
        with self.assertRaises(ValueError):
            recommend_transition(sample(1, 1), "BOGUS_MODE")


if __name__ == "__main__":
    unittest.main()
