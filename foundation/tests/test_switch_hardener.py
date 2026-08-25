"""Tests for foundation/switch_hardener.py — a thin wrapper around the
real kpm.promotion.state_machine.PromotionStore, not a new lifecycle."""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from foundation.switch_hardener import (  # noqa: E402
    run_hardening_gates, classify_hardened_switch, advance_to_tested, harden,
    SWITCH_CATEGORIES, UnrecognisedSwitchCategory, HardeningGateReport,
)
from kpm.promotion.state_machine import PromotionStore, SelfPromotionForbidden  # noqa: E402


def _good_report(subject="lesson-1"):
    return run_hardening_gates(
        subject, provenance="observed in 6 independent sessions",
        evidence=("session log A", "session log B"),
        falsifiability_condition="fails if net_reality_yield goes negative",
        scope=("cosmic-library builds only",),
        failure_mode="over-applying outside declared scope produces false confidence",
        reversible=True,
        red_team_argument="this could entrench a pattern that stops applying once "
                          "session structure changes",
        reality_yield_positive=True, duplicate_of=None, reduces_human_agency=False,
    )


class TestHardeningGates(unittest.TestCase):
    def test_all_gates_pass_with_complete_input(self):
        r = _good_report()
        self.assertTrue(r.all_passed, r.failed_gates)
        self.assertEqual(len(r.findings), 10)

    def test_missing_provenance_fails_that_gate_only(self):
        r = run_hardening_gates(
            "x", provenance="", evidence=("e",), falsifiability_condition="f",
            scope=("s",), failure_mode="m", reversible=True,
            red_team_argument="r", reality_yield_positive=True,
            duplicate_of=None, reduces_human_agency=False,
        )
        self.assertFalse(r.all_passed)
        self.assertEqual(r.failed_gates, ("PROVENANCE",))

    def test_duplication_check_fails_when_duplicate_named(self):
        r = run_hardening_gates(
            "x", provenance="p", evidence=("e",), falsifiability_condition="f",
            scope=("s",), failure_mode="m", reversible=True,
            red_team_argument="r", reality_yield_positive=True,
            duplicate_of="existing-rule-42", reduces_human_agency=False,
        )
        self.assertIn("DUPLICATION_CHECK", r.failed_gates)

    def test_human_agency_gate_fails_when_reduces_agency(self):
        r = run_hardening_gates(
            "x", provenance="p", evidence=("e",), falsifiability_condition="f",
            scope=("s",), failure_mode="m", reversible=True,
            red_team_argument="r", reality_yield_positive=True,
            duplicate_of=None, reduces_human_agency=True,
        )
        self.assertIn("HUMAN_AGENCY", r.failed_gates)

    def test_irreversible_still_passes_its_own_gate(self):
        r = run_hardening_gates(
            "x", provenance="p", evidence=("e",), falsifiability_condition="f",
            scope=("s",), failure_mode="m", reversible=False,
            red_team_argument="r", reality_yield_positive=True,
            duplicate_of=None, reduces_human_agency=False,
        )
        self.assertTrue(r.all_passed)
        rev_finding = [f for f in r.findings if f.gate == "REVERSIBILITY"][0]
        self.assertIn("IRREVERSIBLE", rev_finding.detail)

    def test_multiple_failed_gates_all_reported(self):
        r = run_hardening_gates(
            "x", provenance="", evidence=(), falsifiability_condition="",
            scope=(), failure_mode="", reversible=True,
            red_team_argument="", reality_yield_positive=False,
            duplicate_of="dup", reduces_human_agency=True,
        )
        self.assertEqual(len(r.failed_gates), 9)  # all but REVERSIBILITY


class TestHardenReusesRealStore(unittest.TestCase):
    def test_full_path_raw_to_stable(self):
        store = PromotionStore()
        advance_to_tested(store, "lesson-1", created_by="agent-a")
        record = harden(store, "lesson-1", gate_report=_good_report(),
                        reviewed_by="reviewer-b", created_by="agent-a")
        self.assertEqual(record.state, "STABLE")

    def test_harden_refuses_on_failed_gates(self):
        store = PromotionStore()
        advance_to_tested(store, "lesson-2", created_by="agent-a")
        bad_report = run_hardening_gates(
            "lesson-2", provenance="", evidence=(), falsifiability_condition="",
            scope=(), failure_mode="", reversible=True, red_team_argument="",
            reality_yield_positive=False, duplicate_of="dup",
            reduces_human_agency=False,
        )
        with self.assertRaises(ValueError):
            harden(store, "lesson-2", gate_report=bad_report,
                  reviewed_by="reviewer-b", created_by="agent-a")
        # and the underlying record must still be TESTED, not silently STABLE
        self.assertEqual(store.get("lesson-2").state, "TESTED")

    def test_harden_cannot_be_self_reviewed(self):
        """Inherited guarantee from the real store — not re-implemented here."""
        store = PromotionStore()
        advance_to_tested(store, "lesson-3", created_by="same-person")
        with self.assertRaises(SelfPromotionForbidden):
            harden(store, "lesson-3", gate_report=_good_report(),
                  reviewed_by="same-person", created_by="same-person")

    def test_harden_cannot_skip_tested(self):
        """A raw, never-advanced record cannot be hardened directly —
        the real TRANSITIONS table (not reimplemented here) refuses it."""
        store = PromotionStore()
        store.promote("lesson-4", "DISTILLED", reason="x", created_by="a")
        with self.assertRaises(Exception):
            harden(store, "lesson-4", gate_report=_good_report(),
                  reviewed_by="b", created_by="a")


class TestClassifyHardenedSwitch(unittest.TestCase):
    def test_all_nine_categories_are_the_declared_set(self):
        self.assertEqual(SWITCH_CATEGORIES, frozenset({
            "INVARIANT", "GATE", "CIRCUIT_BREAKER", "ROUTER", "DEFAULT",
            "LEDGER_ENTRY", "OPEN_QUESTION", "DEPRECATED_PATH", "MAGL",
        }))

    def test_classify_after_stable_succeeds(self):
        store = PromotionStore()
        advance_to_tested(store, "lesson-5", created_by="a")
        harden(store, "lesson-5", gate_report=_good_report(),
              reviewed_by="b", created_by="a")
        result = classify_hardened_switch(store, "lesson-5", "CIRCUIT_BREAKER")
        self.assertEqual(result, "CIRCUIT_BREAKER")

    def test_classify_before_stable_refused(self):
        store = PromotionStore()
        advance_to_tested(store, "lesson-6", created_by="a")  # only TESTED
        with self.assertRaises(ValueError):
            classify_hardened_switch(store, "lesson-6", "INVARIANT")

    def test_unregistered_subject_refused(self):
        store = PromotionStore()
        with self.assertRaises(ValueError):
            classify_hardened_switch(store, "never-registered", "GATE")

    def test_unrecognised_category_refused_not_defaulted(self):
        store = PromotionStore()
        advance_to_tested(store, "lesson-7", created_by="a")
        harden(store, "lesson-7", gate_report=_good_report(),
              reviewed_by="b", created_by="a")
        with self.assertRaises(UnrecognisedSwitchCategory):
            classify_hardened_switch(store, "lesson-7", "TOTALLY_MADE_UP_CATEGORY")


class TestReportSerialization(unittest.TestCase):
    def test_to_dict_shape(self):
        d = _good_report().to_dict()
        self.assertIn("all_passed", d)
        self.assertIn("failed_gates", d)
        self.assertEqual(len(d["findings"]), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
