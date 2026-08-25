import unittest

from foundation.recursion_guard import GuardDecision, check, child_env


class TestSafe(unittest.TestCase):
    def test_clean_root_execution_is_safe(self):
        result = check("op-a", environ={})
        self.assertEqual(result.decision, GuardDecision.SAFE)
        self.assertTrue(result.is_safe())
        self.assertEqual(result.depth, 0)

    def test_different_operation_in_ancestry_is_still_safe(self):
        env = child_env("op-a", base={})
        result = check("op-b", environ=env)
        self.assertEqual(result.decision, GuardDecision.SAFE)


class TestBlockedRepeat(unittest.TestCase):
    def test_same_operation_already_in_ancestry_is_blocked(self):
        env = child_env("op-a", base={})
        result = check("op-a", environ=env)
        self.assertEqual(result.decision, GuardDecision.BLOCKED_REPEAT)
        self.assertFalse(result.is_safe())
        self.assertIn("op-a", result.reason)

    def test_blocked_repeat_reports_depth_at_which_repeat_was_found(self):
        env = child_env("op-a", base={})
        env = child_env("op-a", base=env)  # depth now 2, still same operation
        result = check("op-a", environ=env)
        self.assertEqual(result.decision, GuardDecision.BLOCKED_REPEAT)
        self.assertEqual(result.depth, 2)


class TestBlockedDepth(unittest.TestCase):
    def test_depth_at_explicit_boundary_is_blocked(self):
        # A different operation each hop (so BLOCKED_REPEAT never fires),
        # depth alone crossing the boundary is what must trip here.
        env = {}
        for i in range(3):
            env = child_env(f"op-{i}", base=env)
        result = check("op-new", max_depth=3, environ=env)
        self.assertEqual(result.decision, GuardDecision.BLOCKED_DEPTH)
        self.assertFalse(result.is_safe())

    def test_depth_below_boundary_remains_safe(self):
        env = child_env("op-0", base={})
        result = check("op-new", max_depth=3, environ=env)
        self.assertEqual(result.decision, GuardDecision.SAFE)


class TestChildEnvDepthInheritance(unittest.TestCase):
    def test_child_env_stamps_operation_and_depth_zero_to_one(self):
        env = child_env("op-a", base={})
        self.assertEqual(env["TITANOS_GUARD_OPERATION"], "op-a")
        self.assertEqual(env["TITANOS_GUARD_DEPTH"], "1")

    def test_child_env_increments_existing_parent_depth(self):
        parent_env = child_env("op-a", base={})  # depth 1
        grandchild_env = child_env("op-b", base=parent_env)  # depth 2
        self.assertEqual(grandchild_env["TITANOS_GUARD_DEPTH"], "2")
        self.assertEqual(grandchild_env["TITANOS_GUARD_OPERATION"], "op-b")

    def test_child_env_preserves_unrelated_base_entries(self):
        base = {"PATH": "/usr/bin", "OTHER": "x"}
        env = child_env("op-a", base=base)
        self.assertEqual(env["PATH"], "/usr/bin")
        self.assertEqual(env["OTHER"], "x")


class TestMalformedDepthFailsClosed(unittest.TestCase):
    def test_non_numeric_depth_does_not_crash_and_does_not_become_unrelated_safe_root(self):
        env = {"TITANOS_GUARD_OPERATION": "op-a", "TITANOS_GUARD_DEPTH": "not-a-number"}
        result = check("op-a", environ=env)
        # Same operation is still in ancestry -- malformed depth must not
        # cause the repeat to be silently treated as an unrelated fresh
        # root just because the depth field could not be parsed.
        self.assertEqual(result.decision, GuardDecision.BLOCKED_REPEAT)
        self.assertEqual(result.depth, 0)  # fails closed to 0, never crashes

    def test_malformed_depth_on_unrelated_operation_defaults_depth_to_zero(self):
        env = {"TITANOS_GUARD_OPERATION": "op-a", "TITANOS_GUARD_DEPTH": "garbage"}
        result = check("op-different", environ=env)
        self.assertEqual(result.decision, GuardDecision.SAFE)
        self.assertEqual(result.depth, 0)

    def test_child_env_with_malformed_parent_depth_does_not_crash(self):
        base = {"TITANOS_GUARD_OPERATION": "op-a", "TITANOS_GUARD_DEPTH": "garbage"}
        env = child_env("op-b", base=base)
        self.assertEqual(env["TITANOS_GUARD_DEPTH"], "1")  # falls back to 0 + 1


if __name__ == "__main__":
    unittest.main()
