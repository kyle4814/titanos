"""Tests for foundation/layer0_worker.py."""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from foundation.layer0_worker import (  # noqa: E402
    Layer0Worker, StopSignal, should_halt,
    DEFAULT_INFORMATION_GAIN_THRESHOLD, DEFAULT_YIELD_THRESHOLD,
)


class TestABCEnforcesMandatoryHooks(unittest.TestCase):
    """The doctrine: 'NO WORKER MAY SKIP: CHECK_EXISTING, VERIFY,
    PRESERVE_PROVENANCE, UPDATE_STATE.' Python's ABC mechanism enforces
    this even more strongly than the doctrine asked — a subclass missing
    any of the four cannot even be INSTANTIATED, not just fails at
    runtime."""

    def test_bare_layer0worker_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            Layer0Worker()

    def test_subclass_missing_check_existing_cannot_instantiate(self):
        class Incomplete(Layer0Worker):
            def verify(self, result): return True
            def preserve_provenance(self, result, *, verified): pass
            def update_state(self, result, yield_signal): pass
        with self.assertRaises(TypeError):
            Incomplete()

    def test_subclass_missing_verify_cannot_instantiate(self):
        class Incomplete(Layer0Worker):
            def check_existing(self, observation): return None
            def preserve_provenance(self, result, *, verified): pass
            def update_state(self, result, yield_signal): pass
        with self.assertRaises(TypeError):
            Incomplete()

    def test_subclass_missing_preserve_provenance_cannot_instantiate(self):
        class Incomplete(Layer0Worker):
            def check_existing(self, observation): return None
            def verify(self, result): return True
            def update_state(self, result, yield_signal): pass
        with self.assertRaises(TypeError):
            Incomplete()

    def test_subclass_missing_update_state_cannot_instantiate(self):
        class Incomplete(Layer0Worker):
            def check_existing(self, observation): return None
            def verify(self, result): return True
            def preserve_provenance(self, result, *, verified): pass
        with self.assertRaises(TypeError):
            Incomplete()

    def test_subclass_implementing_all_four_can_instantiate(self):
        class Complete(Layer0Worker):
            def check_existing(self, observation): return None
            def verify(self, result): return True
            def preserve_provenance(self, result, *, verified): pass
            def update_state(self, result, yield_signal): pass
        Complete()  # must not raise


def _minimal_worker_cls(*, verify_result=True, permission=True):
    class W(Layer0Worker):
        worker_id = "test-worker"
        calls: list

        def __init__(self):
            self.calls = []

        def request_permission_if_required(self, lever):
            self.calls.append("permission")
            return permission

        def check_existing(self, observation):
            self.calls.append("check_existing")
            return None

        def execute_minimum(self, lever):
            self.calls.append("execute_minimum")
            return "did work"

        def verify(self, result):
            self.calls.append("verify")
            return verify_result

        def preserve_provenance(self, result, *, verified):
            self.calls.append(f"preserve_provenance(verified={verified})")

        def update_state(self, result, yield_signal):
            self.calls.append("update_state")
    return W


class TestRunSequencesAllSteps(unittest.TestCase):
    def test_full_run_completes_all_fourteen_named_steps_in_order(self):
        w = _minimal_worker_cls()()
        record = w.run()
        expected = [
            "BOOT", "OBSERVE", "MAP", "CHECK_EXISTING", "GENERATE_OPTIONS",
            "SCORE_FRONTIER", "SELECT_LEVER", "REQUEST_PERMISSION_IF_REQUIRED",
            "EXECUTE_MINIMUM", "VERIFY", "MEASURE_YIELD", "PRESERVE_PROVENANCE",
            "UPDATE_STATE", "RECOMMEND_NEXT", "HALT",
        ]
        self.assertEqual(record.steps_completed, expected)

    def test_denied_permission_halts_before_execute_minimum(self):
        w = _minimal_worker_cls(permission=False)()
        record = w.run()
        self.assertTrue(record.halted)
        self.assertIn("permission", record.halt_reason)
        self.assertNotIn("EXECUTE_MINIMUM", record.steps_completed)

    def test_failed_verification_halts_but_still_preserves_provenance(self):
        """The doctrine's own quarantine principle: a failure must still
        be recorded, never silently dropped."""
        w = _minimal_worker_cls(verify_result=False)()
        record = w.run()
        self.assertTrue(record.halted)
        self.assertIn("verification failed", record.halt_reason)
        self.assertIn("PRESERVE_PROVENANCE", record.steps_completed)
        self.assertIn("preserve_provenance(verified=False)", w.calls)

    def test_successful_run_preserves_provenance_with_verified_true(self):
        w = _minimal_worker_cls()()
        w.run()
        self.assertIn("preserve_provenance(verified=True)", w.calls)

    def test_permissive_default_permission_hook_is_documented_risk(self):
        """The default request_permission_if_required() returns True —
        deliberately permissive for low-stakes workers. A worker for
        anything critical MUST override it; this test just confirms the
        default behaves as documented, so a future reader can't be
        surprised by it."""
        class Bare(Layer0Worker):
            def check_existing(self, observation): return None
            def verify(self, result): return True
            def preserve_provenance(self, result, *, verified): pass
            def update_state(self, result, yield_signal): pass
        w = Bare()
        self.assertTrue(w.request_permission_if_required(lever=None))


class TestStopCondition(unittest.TestCase):
    def test_low_gain_low_yield_no_risk_halts(self):
        s = StopSignal(new_information_gain=0.0, expected_real_world_yield=0.0,
                       critical_risk_requires_action=False)
        self.assertTrue(should_halt(s))

    def test_high_gain_does_not_halt(self):
        s = StopSignal(new_information_gain=5.0, expected_real_world_yield=0.0,
                       critical_risk_requires_action=False)
        self.assertFalse(should_halt(s))

    def test_high_yield_does_not_halt(self):
        s = StopSignal(new_information_gain=0.0, expected_real_world_yield=5.0,
                       critical_risk_requires_action=False)
        self.assertFalse(should_halt(s))

    def test_critical_risk_never_halts_regardless_of_gain_and_yield(self):
        """The load-bearing test: a critical risk requiring action blocks
        halting even when gain and yield are both zero — the recursion
        must not stop just because nothing interesting is left to build
        while something dangerous is unaddressed."""
        s = StopSignal(new_information_gain=0.0, expected_real_world_yield=0.0,
                       critical_risk_requires_action=True)
        self.assertFalse(should_halt(s))

    def test_default_thresholds_are_zero(self):
        self.assertEqual(DEFAULT_INFORMATION_GAIN_THRESHOLD, 0.0)
        self.assertEqual(DEFAULT_YIELD_THRESHOLD, 0.0)

    def test_custom_thresholds_respected(self):
        s = StopSignal(new_information_gain=0.5, expected_real_world_yield=0.5,
                       critical_risk_requires_action=False)
        self.assertFalse(should_halt(s))  # above default zero thresholds
        self.assertTrue(should_halt(s, information_gain_threshold=1.0, yield_threshold=1.0))


class TestRunCannotBeOverridden(unittest.TestCase):
    """run() is the template method — a subclass technically CAN
    override it in Python (no language-level final), but doing so is
    against the contract's design intent. This test documents the
    expectation that a normal subclass should never need to, by proving
    the default run() alone (with no override) already exercises the
    full sequence correctly."""

    def test_no_subclass_in_this_test_file_overrides_run(self):
        w = _minimal_worker_cls()()
        self.assertIs(type(w).run, Layer0Worker.run)


if __name__ == "__main__":
    unittest.main(verbosity=2)
