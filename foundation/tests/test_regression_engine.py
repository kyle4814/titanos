"""Tests for foundation/regression_engine.py — proposes, never executes,
a downgrade for a promotion record with a RESOLVED, evidence-backed
contradiction against it. See the module docstring for why this reuses
ContradictionRegistry's own RESOLVED/evidence_refs gate rather than a
second threshold, and why it never calls PromotionStore.promote()."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from foundation.regression_engine import (  # noqa: E402
    check_for_regression, RegressionDecision, DOWNGRADE_PREFERENCE_ORDER,
)
from kpm.contradictions.registry import ContradictionRegistry  # noqa: E402
from kpm.promotion.state_machine import PromotionStore  # noqa: E402


class TestNoContradictionNoRegression(unittest.TestCase):
    """Negative case: no contradiction exists -> no regression proposed."""

    def test_unknown_contradiction_id(self):
        store = PromotionStore()
        registry = ContradictionRegistry()
        store.register("bp-1", created_by="alice")

        decision = check_for_regression(
            store, registry, "bp-1", contradiction_id="does-not-exist",
        )
        self.assertFalse(decision.regression_proposed)
        self.assertIsNone(decision.proposed_target)
        self.assertFalse(decision.no_legal_target)

    def test_open_contradiction_is_not_sufficient_evidence(self):
        store = PromotionStore()
        registry = ContradictionRegistry()
        store.register("bp-1", created_by="alice")
        registry.record("c-1", "bp-1 conflicts with bp-2", ["bp-1", "bp-2"])

        decision = check_for_regression(store, registry, "bp-1", contradiction_id="c-1")
        self.assertFalse(decision.regression_proposed)
        self.assertIn("not RESOLVED", decision.reason)

    def test_wont_fix_contradiction_is_not_sufficient_evidence(self):
        store = PromotionStore()
        registry = ContradictionRegistry()
        store.register("bp-1", created_by="alice")
        registry.record("c-1", "bp-1 conflicts with bp-2", ["bp-1", "bp-2"])
        registry.resolve(
            "c-1", "not worth pursuing", evidence_refs=(), resolved_by="bob",
            final_status="WONT_FIX",
        )

        decision = check_for_regression(store, registry, "bp-1", contradiction_id="c-1")
        self.assertFalse(decision.regression_proposed)

    def test_contradiction_not_naming_this_record(self):
        store = PromotionStore()
        registry = ContradictionRegistry()
        store.register("bp-3", created_by="alice")
        registry.record("c-1", "bp-1 conflicts with bp-2", ["bp-1", "bp-2"])
        registry.resolve("c-1", "verified false", evidence_refs=("doc-1",), resolved_by="bob")

        decision = check_for_regression(store, registry, "bp-3", contradiction_id="c-1")
        self.assertFalse(decision.regression_proposed)
        self.assertIn("does not name", decision.reason)

    def test_no_promotion_record(self):
        store = PromotionStore()
        registry = ContradictionRegistry()
        registry.record("c-1", "bp-1 conflicts with bp-2", ["bp-1", "bp-2"])
        registry.resolve("c-1", "verified false", evidence_refs=("doc-1",), resolved_by="bob")

        decision = check_for_regression(store, registry, "bp-1", contradiction_id="c-1")
        self.assertFalse(decision.regression_proposed)
        self.assertIn("no promotion record", decision.reason)


class TestRegressionProposedButNotExecuted(unittest.TestCase):
    """Positive case, full integration: register -> advance -> real
    contradiction with real evidence -> propose -> caller executes."""

    def test_full_flow_tested_downgrades_to_quarantined(self):
        store = PromotionStore()
        registry = ContradictionRegistry()

        store.register("bp-1", created_by="alice")
        store.promote("bp-1", "DISTILLED", reason="abstraction identified")
        store.promote("bp-1", "PROVISIONAL", reason="scoped and evidenced")
        store.promote("bp-1", "TESTED", reason="hardening gates run")
        self.assertEqual(store.get("bp-1").state, "TESTED")

        registry.record(
            "c-1", "bp-1's claim contradicts bp-9's independently verified claim",
            ["bp-1", "bp-9"],
        )
        registry.resolve(
            "c-1", "bp-9's claim reproduced under independent test; bp-1's did not",
            evidence_refs=("test-run-42.log",), resolved_by="carol",
        )

        decision = check_for_regression(store, registry, "bp-1", contradiction_id="c-1")

        self.assertIsInstance(decision, RegressionDecision)
        self.assertTrue(decision.regression_proposed)
        self.assertEqual(decision.current_state, "TESTED")
        self.assertEqual(decision.proposed_target, "QUARANTINED")
        self.assertEqual(decision.triggering_contradiction_id, "c-1")
        self.assertFalse(decision.no_legal_target)

        # The engine must NOT have touched the store itself.
        self.assertEqual(store.get("bp-1").state, "TESTED")

        # The CALLER executes the proposal, as a normal, already-legal
        # promote() call -- not a new delete/overwrite mechanism.
        executed = store.promote(
            "bp-1", decision.proposed_target,
            reason=f"regression engine proposal: {decision.reason}",
        )
        self.assertEqual(executed.state, "QUARANTINED")
        self.assertEqual(executed.history[-1]["from"], "TESTED")
        self.assertEqual(executed.history[-1]["to"], "QUARANTINED")

    def test_stable_record_downgrades_to_deprecated_not_quarantined(self):
        """STABLE has no direct edge to QUARANTINED or CONTESTED in
        TRANSITIONS -- only DEPRECATED/SUPERSEDED. The engine must find
        DEPRECATED via the real table, not fabricate a QUARANTINED edge
        that doesn't exist."""
        store = PromotionStore()
        registry = ContradictionRegistry()

        store.register("bp-2", created_by="alice")
        store.promote("bp-2", "DISTILLED", reason="r")
        store.promote("bp-2", "PROVISIONAL", reason="r")
        store.promote("bp-2", "TESTED", reason="r")
        store.promote("bp-2", "STABLE", reason="reviewed", reviewed_by="bob")
        self.assertEqual(store.get("bp-2").state, "STABLE")

        registry.record("c-2", "bp-2 contradicts bp-8", ["bp-2", "bp-8"])
        registry.resolve("c-2", "verified", evidence_refs=("e",), resolved_by="carol")

        decision = check_for_regression(store, registry, "bp-2", contradiction_id="c-2")
        self.assertTrue(decision.regression_proposed)
        self.assertEqual(decision.proposed_target, "DEPRECATED")

        executed = store.promote("bp-2", "DEPRECATED", reason="regression: contradicted")
        self.assertEqual(executed.state, "DEPRECATED")

    def test_deprecated_record_has_no_legal_downgrade_target(self):
        """DEPRECATED is terminal in TRANSITIONS -- the engine must
        report this honestly rather than inventing a target."""
        store = PromotionStore()
        registry = ContradictionRegistry()

        store.register("bp-4", created_by="alice")
        store.promote("bp-4", "DISTILLED", reason="r")
        store.promote("bp-4", "PROVISIONAL", reason="r")
        store.promote("bp-4", "TESTED", reason="r")
        store.promote("bp-4", "STABLE", reason="reviewed", reviewed_by="bob")
        store.promote("bp-4", "DEPRECATED", reason="superseded already")
        self.assertEqual(store.get("bp-4").state, "DEPRECATED")

        registry.record("c-4", "bp-4 contradicts bp-7", ["bp-4", "bp-7"])
        registry.resolve("c-4", "verified", evidence_refs=("e",), resolved_by="carol")

        decision = check_for_regression(store, registry, "bp-4", contradiction_id="c-4")
        self.assertFalse(decision.regression_proposed)
        self.assertTrue(decision.no_legal_target)
        self.assertIsNone(decision.proposed_target)
        self.assertEqual(decision.current_state, "DEPRECATED")

    def test_human_review_downgrades_to_quarantined(self):
        store = PromotionStore()
        registry = ContradictionRegistry()

        store.register("bp-5", created_by="alice")
        store.promote("bp-5", "DISTILLED", reason="r")
        store.promote("bp-5", "PROVISIONAL", reason="r")
        store.promote("bp-5", "CONTESTED", reason="disputed")
        store.promote("bp-5", "HUMAN_REVIEW", reason="escalated")
        self.assertEqual(store.get("bp-5").state, "HUMAN_REVIEW")

        registry.record("c-5", "bp-5 contradicts bp-6", ["bp-5", "bp-6"])
        registry.resolve("c-5", "verified", evidence_refs=("e",), resolved_by="carol")

        decision = check_for_regression(store, registry, "bp-5", contradiction_id="c-5")
        self.assertTrue(decision.regression_proposed)
        self.assertEqual(decision.proposed_target, "QUARANTINED")

    def test_decision_is_a_dict_exportable(self):
        store = PromotionStore()
        registry = ContradictionRegistry()
        store.register("bp-1", created_by="alice")
        decision = check_for_regression(store, registry, "bp-1", contradiction_id="none")
        d = decision.to_dict()
        self.assertIn("regression_proposed", d)
        self.assertIn("reason", d)

    def test_preference_order_is_fixed_and_public(self):
        self.assertEqual(
            DOWNGRADE_PREFERENCE_ORDER,
            ("QUARANTINED", "CONTESTED", "HUMAN_REVIEW", "DEPRECATED"),
        )


class TestEngineNeverExecutes(unittest.TestCase):
    """Structural check mirroring foundation/sentinel.py's
    TestSentinelCannotExecute: this module's public callables must not
    include promote/execute/apply/downgrade-as-verb."""

    def test_no_action_verb_public_callables(self):
        import foundation.regression_engine as mod
        forbidden = {"promote", "execute", "apply", "downgrade", "quarantine", "deprecate"}
        for name in mod.__all__:
            obj = getattr(mod, name)
            if callable(obj) and not isinstance(obj, type):
                self.assertNotIn(name.lower(), forbidden, f"{name} looks like an action verb")

    def test_check_for_regression_never_calls_promote(self):
        # Direct behavioural proof, not just a naming check: run the
        # positive-case flow and confirm the store's state is untouched
        # until the CALLER separately promotes.
        store = PromotionStore()
        registry = ContradictionRegistry()
        store.register("bp-1", created_by="alice")
        store.promote("bp-1", "DISTILLED", reason="r")
        store.promote("bp-1", "PROVISIONAL", reason="r")
        store.promote("bp-1", "TESTED", reason="r")
        registry.record("c-1", "x", ["bp-1", "bp-9"])
        registry.resolve("c-1", "verified", evidence_refs=("e",), resolved_by="carol")

        before = store.get("bp-1").state
        check_for_regression(store, registry, "bp-1", contradiction_id="c-1")
        after = store.get("bp-1").state
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
