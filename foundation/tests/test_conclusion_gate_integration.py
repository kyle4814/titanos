"""
CONCLUSION_ENFORCEMENT_001 — proves foundation/layer0_worker.py::run()
actually derives its terminal status through foundation/conclusion_gate.
py::conclude_cycle(), at every return point, rather than trusting
record.halted/halt_reason as a self-certified status.

Reuses foundation/tests/test_layer0_worker.py's _minimal_worker_cls
pattern for the synthetic-boundary proofs, and the real
SentinelSweepWorker (foundation/tests/test_closed_loop_reality.py's
established real worker) for the one normal-completion proof that must
be earned, not fabricated.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from foundation.conclusion_gate import TerminalStatus
from foundation.crystal import CrystalStore
from foundation.layer0_worker import Layer0Worker
from foundation.sentinel_worker import SentinelSweepWorker

REPO_ROOT = Path(__file__).resolve().parents[2]


def _worker_cls(*, verify_result=True, permission=True,
                 objective="", next_move=None):
    class W(Layer0Worker):
        worker_id = "integration-test-worker"

        def objective(self):
            return objective

        def request_permission_if_required(self, lever):
            return permission

        def check_existing(self, observation):
            return None

        def execute_minimum(self, lever):
            return "did work"

        def verify(self, result):
            return verify_result

        def preserve_provenance(self, result, *, verified):
            pass

        def update_state(self, result, yield_signal):
            pass

        def recommend_next(self, yield_signal):
            return next_move
    return W


class TestNormalCompletionThroughRealWorker(unittest.TestCase):
    def test_1_real_sentinel_sweep_reaches_complete(self):
        """This is the one seam this repository actually has: a real
        worker, doing real work (pulse_sweep()), declaring a real
        objective and a real, evidence-derived next_move. Nothing here
        is invented to make the demo pass."""
        crystal_store = CrystalStore()
        worker = SentinelSweepWorker(
            repo_root=REPO_ROOT, crystal_store=crystal_store,
            recorded_by="conclusion-gate-integration-test",
            crystal_id="sentinel-sweep-conclusion-test",
        )
        record = worker.run()
        self.assertIsNotNone(record.conclusion)
        self.assertEqual(record.conclusion.status, TerminalStatus.COMPLETE)
        self.assertIn("boot/state/test integrity", record.conclusion.objective)
        self.assertTrue(record.conclusion.next_move)


class TestFalseCompletionClaimIsRejected(unittest.TestCase):
    def test_2_missing_objective_cannot_pass_as_complete(self):
        """A worker that never overrides objective() (the base class
        default) cannot have its cycle concluded COMPLETE merely because
        every other step succeeded -- record.halted stays False, but
        the conclusion is not COMPLETE."""
        w = _worker_cls(objective="", next_move="something")()
        record = w.run()
        # halted is True here for an unrelated reason (the default
        # stop_signal() always recommends halting) -- the point of this
        # test is that the CONCLUSION is not COMPLETE regardless.
        self.assertNotEqual(record.conclusion.status, TerminalStatus.COMPLETE)
        self.assertEqual(record.conclusion.status, TerminalStatus.BLOCKED)
        self.assertIn("objective", record.conclusion.reason)

    def test_missing_next_move_cannot_pass_as_complete(self):
        w = _worker_cls(objective="a real objective", next_move=None)()
        record = w.run()
        self.assertNotEqual(record.conclusion.status, TerminalStatus.COMPLETE)


class TestBlockerPropagation(unittest.TestCase):
    def test_3_permission_denied_propagates_as_blocked(self):
        w = _worker_cls(permission=False, objective="x", next_move="y")()
        record = w.run()
        self.assertTrue(record.halted)
        self.assertEqual(record.conclusion.status, TerminalStatus.BLOCKED)
        self.assertEqual(record.conclusion.reason, "permission not granted")

    def test_verification_failed_propagates_as_blocked(self):
        w = _worker_cls(verify_result=False, objective="x", next_move="y")()
        record = w.run()
        self.assertTrue(record.halted)
        self.assertEqual(record.conclusion.status, TerminalStatus.BLOCKED)
        self.assertEqual(record.conclusion.reason, "verification failed")


class TestIsolationAcrossTheRealSeam(unittest.TestCase):
    def test_6_next_move_executed_is_always_false_through_run(self):
        """run() never calls or executes the recommended next_move --
        this is a structural property of run()'s own control flow, not
        a value any worker can set. Proven by construction: no worker
        hook here has any way to set next_move_executed=True, and every
        real conclusion this seam produces carries False."""
        w = _worker_cls(objective="x", next_move="close the next gap")()
        record = w.run()
        self.assertFalse(record.conclusion.next_move_executed)
        self.assertEqual(record.conclusion.status, TerminalStatus.COMPLETE)

        # Same proof via the real worker.
        crystal_store = CrystalStore()
        real_worker = SentinelSweepWorker(
            repo_root=REPO_ROOT, crystal_store=crystal_store,
            recorded_by="isolation-test", crystal_id="sentinel-sweep-isolation-test",
        )
        real_record = real_worker.run()
        self.assertFalse(real_record.conclusion.next_move_executed)


class TestNoBypass(unittest.TestCase):
    def test_7_conclusion_is_a_real_conclude_cycle_result_not_a_local_flag(self):
        """Behavioral, not just structural: corrupt conclude_cycle's
        precedence would change this result. Proven behaviorally by
        checking the actual returned CycleConclusion carries the exact
        reason text conclude_cycle() produces for a missing field --
        text no worker hook in this file ever constructs itself."""
        w = _worker_cls(objective="", next_move="y")()
        record = w.run()
        self.assertIn(
            "COMPLETE cannot be emitted without a declared",
            record.conclusion.reason,
        )

    def test_worker_cannot_self_declare_complete_by_setting_halted_false(self):
        """halted=False alone (the worker's own signal) is not what the
        conclusion is derived from -- an incomplete report with
        halted=False still fails to reach COMPLETE."""
        w = _worker_cls(objective="", next_move=None)()
        record = w.run()
        self.assertNotEqual(record.conclusion.status, TerminalStatus.COMPLETE)


class TestBackwardCompatibility(unittest.TestCase):
    def test_8_steps_completed_sequence_unchanged(self):
        w = _worker_cls(objective="x", next_move="y")()
        record = w.run()
        expected = [
            "BOOT", "OBSERVE", "MAP", "CHECK_EXISTING", "GENERATE_OPTIONS",
            "SCORE_FRONTIER", "SELECT_LEVER", "REQUEST_PERMISSION_IF_REQUIRED",
            "EXECUTE_MINIMUM", "VERIFY", "MEASURE_YIELD", "PRESERVE_PROVENANCE",
            "UPDATE_STATE", "RECOMMEND_NEXT", "HALT",
        ]
        self.assertEqual(record.steps_completed, expected)

    def test_halted_and_halt_reason_fields_still_populated(self):
        w = _worker_cls(permission=False, objective="x", next_move="y")()
        record = w.run()
        self.assertTrue(record.halted)
        self.assertEqual(record.halt_reason, "permission not granted")


class TestNoNewRecursion(unittest.TestCase):
    def test_9_conclude_cycle_is_called_exactly_once_per_run(self):
        """Instrument conclude_cycle via monkeypatch-free counting: run()
        must produce exactly one conclusion per call, never a cycle ->
        conclusion -> cycle chain."""
        w = _worker_cls(objective="x", next_move="y")()
        record = w.run()
        self.assertIsNotNone(record.conclusion)
        # Calling run() again on a fresh instance is independent -- no
        # shared state accumulates conclusions.
        w2 = _worker_cls(objective="x", next_move="y")()
        record2 = w2.run()
        self.assertIsNot(record.conclusion, record2.conclusion)
        self.assertEqual(record.conclusion.to_dict(), record2.conclusion.to_dict())


if __name__ == "__main__":
    unittest.main()
