"""Tests for foundation/historical_findings.py — the one honest
writer -> resolve -> regression_engine composition using this
repository's own real, already-fixed RPA validation-transfer finding.

Proves: OPEN is durable/queryable before resolution, resolution
requires and carries real evidence, RESOLVED never erases either
involved identity, the resolved contradiction reaches
regression_engine.check_for_regression() as a real reader, the
resulting RegressionDecision is proposal-only (never calls
PromotionStore.promote() itself), and no PromotionStore/MAGL
transition happens automatically anywhere in this chain.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kpm.contradictions.registry import ContradictionRegistry  # noqa: E402
from kpm.promotion.state_machine import PromotionStore  # noqa: E402
from foundation.historical_findings import (  # noqa: E402
    RPA_DESIGN_INTENT_CLAIM_ID,
    RPA_PRE_FIX_BLUEPRINT_ID,
    RPA_VALIDATION_BYPASS_CONTRADICTION_ID,
    record_rpa_validation_bypass_finding,
)
from foundation.regression_engine import check_for_regression  # noqa: E402


class TestOpenIsDurableBeforeResolution(unittest.TestCase):
    """Acceptance requirement 5: OPEN contradiction is durable/queryable."""

    def test_open_state_is_queryable_before_resolve(self):
        registry = ContradictionRegistry()
        registry.record(
            RPA_VALIDATION_BYPASS_CONTRADICTION_ID,
            "pre-resolution check",
            (RPA_PRE_FIX_BLUEPRINT_ID, RPA_DESIGN_INTENT_CLAIM_ID),
        )
        record = registry.get(RPA_VALIDATION_BYPASS_CONTRADICTION_ID)
        self.assertEqual(record.status, "OPEN")
        self.assertIn(record, registry.open_contradictions())


class TestRecordRpaValidationBypassFinding(unittest.TestCase):
    def test_records_and_resolves_with_real_evidence(self):
        registry = ContradictionRegistry()
        record = record_rpa_validation_bypass_finding(registry, resolved_by="recon-agent")
        self.assertEqual(record.status, "RESOLVED")
        self.assertTrue(record.resolution)
        self.assertGreater(len(record.resolution.get("evidence_refs", ())), 0)
        self.assertIn(
            "rpa/gates/human_jurisdiction.py::authorize_pilot",
            record.resolution["evidence_refs"],
        )

    def test_involved_identities_survive_resolution(self):
        """Requirement 8: RESOLVED does not erase either original claim
        -- both involved_ids remain exactly as recorded."""
        registry = ContradictionRegistry()
        record = record_rpa_validation_bypass_finding(registry, resolved_by="recon-agent")
        self.assertEqual(
            set(record.involved_ids),
            {RPA_PRE_FIX_BLUEPRINT_ID, RPA_DESIGN_INTENT_CLAIM_ID},
        )

    def test_cannot_be_recorded_twice(self):
        registry = ContradictionRegistry()
        record_rpa_validation_bypass_finding(registry, resolved_by="recon-agent")
        with self.assertRaises(ValueError):
            record_rpa_validation_bypass_finding(registry, resolved_by="recon-agent")

    def test_never_touches_a_promotion_store(self):
        """This file has no PromotionStore parameter at all -- confirms
        by construction that recording/resolving this contradiction
        cannot cause any promotion/authorization transition."""
        import inspect
        sig = inspect.signature(record_rpa_validation_bypass_finding)
        self.assertNotIn("promotion_store", sig.parameters)
        self.assertNotIn("store", sig.parameters)


class TestResolvedContradictionReachesRegressionEngine(unittest.TestCase):
    """Requirement 9/10/11: resolved contradiction reaches
    regression_engine, its output is proposal-only, and no
    PromotionStore transition occurs automatically."""

    def test_regression_engine_reads_the_resolved_finding_and_proposes_only(self):
        registry = ContradictionRegistry()
        record_rpa_validation_bypass_finding(registry, resolved_by="recon-agent")

        store = PromotionStore()
        store.register(RPA_PRE_FIX_BLUEPRINT_ID, created_by="rpa-pipeline")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "DISTILLED", reason="shipped design")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "PROVISIONAL", reason="shipped design")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "TESTED", reason="shipped design")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "STABLE", reason="shipped as-is",
                      reviewed_by="original-reviewer")

        decision = check_for_regression(
            store, registry, RPA_PRE_FIX_BLUEPRINT_ID,
            contradiction_id=RPA_VALIDATION_BYPASS_CONTRADICTION_ID,
        )
        self.assertTrue(decision.regression_proposed)
        # STABLE's only legal targets are DEPRECATED/SUPERSEDED; DEPRECATED
        # is the one entry of DOWNGRADE_PREFERENCE_ORDER reachable from STABLE.
        self.assertEqual(decision.proposed_target, "DEPRECATED")

        # Proposal-only: the blueprint's real state is untouched.
        self.assertEqual(store.get(RPA_PRE_FIX_BLUEPRINT_ID).state, "STABLE")

    def test_historical_contradiction_alone_does_not_change_current_state(self):
        """Requirement 15: a resolved historical contradiction cannot
        prove/force current truth by itself -- the proposal exists,
        but nothing acts on it without a separate, explicit call."""
        registry = ContradictionRegistry()
        record_rpa_validation_bypass_finding(registry, resolved_by="recon-agent")
        store = PromotionStore()
        store.register(RPA_PRE_FIX_BLUEPRINT_ID, created_by="rpa-pipeline")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "DISTILLED", reason="x")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "PROVISIONAL", reason="x")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "TESTED", reason="x")
        store.promote(RPA_PRE_FIX_BLUEPRINT_ID, "STABLE", reason="x",
                      reviewed_by="original-reviewer")

        check_for_regression(
            store, registry, RPA_PRE_FIX_BLUEPRINT_ID,
            contradiction_id=RPA_VALIDATION_BYPASS_CONTRADICTION_ID,
        )
        # Still STABLE -- a real, separate .promote() call would be
        # required to act on the proposal; nothing here does that.
        self.assertEqual(store.get(RPA_PRE_FIX_BLUEPRINT_ID).state, "STABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
