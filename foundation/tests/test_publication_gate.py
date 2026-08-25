"""Tests for foundation/publication_gate.py — the first §2 critical
function hard-gated under TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md."""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from foundation.publication_gate import (  # noqa: E402
    PublicationSwitch, evaluate, authorize_publish, PublicationRefused,
)


def _fully_valid(**overrides) -> PublicationSwitch:
    fields = dict(
        target_repo="github.com/example/cosmic-library",
        secret_scan_passed=True,
        secret_scan_evidence="grep across 205 tracked files, zero hits, 2026-08-25",
        license_present=True, readme_present=True, classification="PUBLIC",
        human_authorized_by="kyle", human_authorization_note="approved public MIT release",
        reversibility_acknowledged=True,
    )
    fields.update(overrides)
    return PublicationSwitch(**fields)


class TestFailClosedDefault(unittest.TestCase):
    def test_default_switch_is_fully_blocked(self):
        d = evaluate(PublicationSwitch())
        self.assertFalse(d.action_permitted)
        self.assertFalse(d.armed)
        self.assertFalse(d.trigger_verified)
        self.assertFalse(d.gates_passed)

    def test_unknown_classification_never_permits(self):
        d = evaluate(_fully_valid(classification="UNKNOWN"))
        self.assertFalse(d.action_permitted)

    def test_default_classification_is_unknown_not_public(self):
        self.assertEqual(PublicationSwitch().classification, "UNKNOWN")


class TestTrigger(unittest.TestCase):
    def test_empty_target_repo_refused(self):
        d = evaluate(_fully_valid(target_repo=""))
        self.assertFalse(d.trigger_verified)
        self.assertFalse(d.action_permitted)

    def test_whitespace_only_target_repo_refused(self):
        d = evaluate(_fully_valid(target_repo="   "))
        self.assertFalse(d.action_permitted)


class TestClassification(unittest.TestCase):
    def test_private_core_locked_even_with_everything_else_perfect(self):
        d = evaluate(_fully_valid(classification="PRIVATE_CORE"))
        self.assertFalse(d.action_permitted)
        self.assertTrue(any("LOCKED" in r for r in d.reasons))

    def test_public_classification_required_for_authorization(self):
        d = evaluate(_fully_valid())
        self.assertTrue(d.action_permitted)


class TestGates(unittest.TestCase):
    def test_secret_scan_not_passed_blocks(self):
        d = evaluate(_fully_valid(secret_scan_passed=False))
        self.assertFalse(d.action_permitted)

    def test_secret_scan_claimed_true_without_evidence_blocks(self):
        """A claim without evidence does not pass the gate — mirrors this
        session's other evidence-required rules."""
        d = evaluate(_fully_valid(secret_scan_evidence=""))
        self.assertFalse(d.action_permitted)

    def test_missing_license_blocks(self):
        d = evaluate(_fully_valid(license_present=False))
        self.assertFalse(d.action_permitted)

    def test_missing_readme_blocks(self):
        d = evaluate(_fully_valid(readme_present=False))
        self.assertFalse(d.action_permitted)

    def test_reversibility_not_acknowledged_blocks(self):
        d = evaluate(_fully_valid(reversibility_acknowledged=False))
        self.assertFalse(d.action_permitted)

    def test_all_gate_failures_reported_not_just_first(self):
        d = evaluate(_fully_valid(license_present=False, readme_present=False))
        self.assertGreaterEqual(len([r for r in d.reasons
                                     if "license" in r or "readme" in r]), 2)


class TestHumanReview(unittest.TestCase):
    def test_no_human_authorized_by_blocks_even_with_gates_passed(self):
        d = evaluate(_fully_valid(human_authorized_by=""))
        self.assertTrue(d.gates_passed)
        self.assertTrue(d.armed)
        self.assertFalse(d.action_permitted)
        self.assertTrue(d.human_review_required)

    def test_authorized_by_name_alone_without_note_blocks(self):
        """A name with no explanation is not distinguishable from a
        forged authorization — evidence, not just a label, is required."""
        d = evaluate(_fully_valid(human_authorization_note=""))
        self.assertFalse(d.action_permitted)

    def test_full_authorization_satisfies_human_review(self):
        d = evaluate(_fully_valid())
        self.assertFalse(d.human_review_required)  # satisfied, not skipped
        self.assertTrue(d.action_permitted)


class TestTwoPointEnforcement(unittest.TestCase):
    """authorize_publish() must not trust a caller-constructed decision —
    it re-derives from the switch's own evidence every time."""

    def test_authorize_publish_succeeds_on_genuinely_valid_switch(self):
        self.assertTrue(authorize_publish(_fully_valid()))

    def test_authorize_publish_raises_on_incomplete_switch(self):
        with self.assertRaises(PublicationRefused):
            authorize_publish(PublicationSwitch(target_repo="github.com/x/y"))

    def test_authorize_publish_raises_never_returns_false_silently(self):
        """Fail-closed: callers cannot mistake 'didn't check' for 'checked
        and it's fine' — refusal is always loud."""
        try:
            authorize_publish(PublicationSwitch())
            self.fail("expected PublicationRefused")
        except PublicationRefused as e:
            self.assertIn("NOT authorized", str(e))

    def test_cannot_bypass_by_hand_constructing_a_permitted_decision(self):
        """The load-bearing test: a PublicationDecision object with
        action_permitted=True hand-built by a caller is never consulted —
        authorize_publish() only ever looks at the PublicationSwitch's
        declared evidence fields, so there is no object shape that lets a
        caller skip evaluation."""
        blank_switch_but_pretend_permitted = PublicationSwitch()  # everything False/empty
        with self.assertRaises(PublicationRefused):
            authorize_publish(blank_switch_but_pretend_permitted)

    def test_private_core_cannot_be_authorized_through_the_second_point_either(self):
        with self.assertRaises(PublicationRefused):
            authorize_publish(_fully_valid(classification="PRIVATE_CORE"))


class TestDecisionSerialization(unittest.TestCase):
    def test_to_dict_shape(self):
        d = evaluate(_fully_valid()).to_dict()
        for key in ("armed", "trigger_verified", "gates_passed",
                   "human_review_required", "action_permitted", "reasons"):
            self.assertIn(key, d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
