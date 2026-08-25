import inspect
import unittest

from foundation.conclusion_gate import (
    CycleConclusion, TerminalStatus, conclude_cycle,
)
from foundation import conclusion_gate as _module


VALID = dict(
    objective="close referential-integrity gap",
    changed="added rollback_candidate_ref check",
    proof="17/17 targeted, 8/8 regression",
    next_move="close value_flow.system_map_ref",
    next_move_executed=False,
)


class TestCompleteRequiresAllEvidence(unittest.TestCase):
    def test_1_complete_succeeds_with_full_valid_report(self):
        c = conclude_cycle(**VALID)
        self.assertEqual(c.status, TerminalStatus.COMPLETE)

    def test_2_complete_rejected_when_proof_absent(self):
        args = dict(VALID, proof="")
        c = conclude_cycle(**args)
        self.assertNotEqual(c.status, TerminalStatus.COMPLETE)
        self.assertIn("proof", c.reason)

    def test_complete_rejected_when_objective_absent(self):
        args = dict(VALID, objective="")
        c = conclude_cycle(**args)
        self.assertNotEqual(c.status, TerminalStatus.COMPLETE)
        self.assertIn("objective", c.reason)

    def test_complete_rejected_when_changed_absent(self):
        args = dict(VALID, changed="")
        c = conclude_cycle(**args)
        self.assertNotEqual(c.status, TerminalStatus.COMPLETE)

    def test_complete_rejected_when_next_move_absent(self):
        args = dict(VALID, next_move="")
        c = conclude_cycle(**args)
        self.assertNotEqual(c.status, TerminalStatus.COMPLETE)

    def test_whitespace_only_field_treated_as_blank(self):
        args = dict(VALID, proof="   ")
        c = conclude_cycle(**args)
        self.assertNotEqual(c.status, TerminalStatus.COMPLETE)


class TestBlockedTermination(unittest.TestCase):
    def test_3_blocked_with_explicit_blocker(self):
        args = dict(VALID, blocker="no GitHub remote exists")
        c = conclude_cycle(**args)
        self.assertEqual(c.status, TerminalStatus.BLOCKED)
        self.assertEqual(c.reason, "no GitHub remote exists")


class TestLimitedTermination(unittest.TestCase):
    def test_4_limited_with_explicit_limitation(self):
        args = dict(VALID, limitation="proves referential integrity only, not economic correctness")
        c = conclude_cycle(**args)
        self.assertEqual(c.status, TerminalStatus.LIMITED)

    def test_none_marker_does_not_trigger_limited(self):
        for marker in ("none", "N/A", "n/a", "Ø", ""):
            args = dict(VALID, limitation=marker)
            c = conclude_cycle(**args)
            self.assertEqual(c.status, TerminalStatus.COMPLETE, marker)


class TestHandoffTermination(unittest.TestCase):
    def test_5_handoff_required_preserves_durable_state(self):
        state = {"run_state": "PENDING", "relevant_task_ids": ("t-1",)}
        args = dict(VALID, handoff=True, handoff_state=state)
        c = conclude_cycle(**args)
        self.assertEqual(c.status, TerminalStatus.HANDOFF_REQUIRED)
        self.assertIs(c.handoff_state, state)


class TestNextMoveIsolation(unittest.TestCase):
    def test_6_executed_next_move_cannot_pass_as_complete(self):
        args = dict(VALID, next_move_executed=True)
        c = conclude_cycle(**args)
        self.assertNotEqual(c.status, TerminalStatus.COMPLETE)
        self.assertEqual(c.status, TerminalStatus.BLOCKED)
        self.assertIn("Isolation Law", c.reason)

    def test_isolation_law_beats_every_other_signal(self):
        """next_move_executed=True must win even when the caller also
        supplies a clean blocker-free, limitation-free, handoff-free
        report — the isolation violation is never masked by other
        fields looking otherwise valid."""
        args = dict(VALID, next_move_executed=True, limitation="", blocker="")
        c = conclude_cycle(**args)
        self.assertEqual(c.status, TerminalStatus.BLOCKED)
        self.assertIn("Isolation Law", c.reason)


class TestContradictoryDataIsResolvedDeterministically(unittest.TestCase):
    def test_7_blocker_and_handoff_together_resolves_via_fixed_precedence(self):
        args = dict(VALID, blocker="real blocker", handoff=True, handoff_state="x")
        c = conclude_cycle(**args)
        # blocker outranks handoff — deterministic, not an exception,
        # not silently combined.
        self.assertEqual(c.status, TerminalStatus.BLOCKED)
        self.assertEqual(c.reason, "real blocker")

    def test_next_move_executed_beats_blocker_and_handoff_together(self):
        args = dict(VALID, next_move_executed=True, blocker="real blocker", handoff=True)
        c = conclude_cycle(**args)
        self.assertIn("Isolation Law", c.reason)


class TestExistingPathsUnaffected(unittest.TestCase):
    def test_8_layer0_worker_and_task_queue_untouched(self):
        """This module has no import dependency on layer0_worker.py or
        task_queue.py (only docstring prose names them, to explain why
        they were not duplicated) — the existing CycleRecord/
        RecoveryHandoff paths are structurally unaffected by this
        addition, not just unaffected by convention."""
        self.assertNotIn("layer0_worker", _module.__dict__)
        self.assertNotIn("task_queue", _module.__dict__)
        source_lines = inspect.getsource(_module).splitlines()
        import_lines = [l for l in source_lines if l.startswith(("import ", "from "))]
        for line in import_lines:
            self.assertNotIn("layer0_worker", line)
            self.assertNotIn("task_queue", line)


class TestDeterminism(unittest.TestCase):
    def test_9_repeated_evaluation_is_deterministic(self):
        c1 = conclude_cycle(**VALID)
        c2 = conclude_cycle(**VALID)
        self.assertEqual(c1.to_dict(), c2.to_dict())


class TestCannotRecreateACycle(unittest.TestCase):
    def test_10_conclude_cycle_calls_nothing_and_spawns_nothing(self):
        func_source = inspect.getsource(_module.conclude_cycle)
        # Strip the `def conclude_cycle(...)` signature line itself so
        # only the function BODY is checked for a self-call.
        body = "\n".join(func_source.splitlines()[1:])
        for forbidden in ("subprocess", "conclude_cycle(", "Agent(", "os.system", "eval(", "exec("):
            self.assertEqual(body.count(forbidden), 0, forbidden)

    def test_conclude_cycle_is_a_pure_function_no_module_state(self):
        c1 = conclude_cycle(**VALID)
        c2 = conclude_cycle(**dict(VALID, blocker="x"))
        c3 = conclude_cycle(**VALID)
        self.assertEqual(c1.to_dict(), c3.to_dict())
        self.assertNotEqual(c1.status, c2.status)


if __name__ == "__main__":
    unittest.main()
