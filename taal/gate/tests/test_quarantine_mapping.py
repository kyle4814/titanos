"""
Integration tests: drive a REAL firewall.quarantine.QuarantineStore
through TAAL's stated vocabulary correspondences and verify they hold
against the actual TRANSITIONS table — not just asserted in a comment.
"""

from __future__ import annotations

import unittest

from firewall.quarantine import IllegalTransition, QuarantineStore, TRANSITIONS
from taal.gate.quarantine_mapping import (
    TAAL_TO_REAL_TRANSITION,
    taal_quarantine,
    taal_mark_reviewed,
    taal_mark_recovered,
    taal_mark_confirmed_policy_violation,
    taal_mark_contained,
)


class TestMappingMatchesRealTransitionsTable(unittest.TestCase):
    """Every documented TAAL correspondence must be a legal edge in the
    real store's TRANSITIONS table. If this fails, the mapping doc is
    wrong and must be fixed — not the test."""

    def test_all_documented_pairs_are_legal_real_transitions(self):
        for taal_name, (src, dst) in TAAL_TO_REAL_TRANSITION.items():
            self.assertIn(
                dst, TRANSITIONS.get(src, frozenset()),
                msg=(
                    f"TAAL '{taal_name}' claims {src} -> {dst} is legal, "
                    f"but the real TRANSITIONS table does not permit it. "
                    f"Legal targets from {src}: {sorted(TRANSITIONS.get(src, []))}"
                ),
            )


class TestQuarantinedThroughReviewedToRecovered(unittest.TestCase):
    """QUARANTINED -> (TAAL REVIEWED) -> (TAAL RECOVERED)."""

    def test_full_happy_path(self):
        store = QuarantineStore()
        rec = taal_quarantine(
            store, artifact_id="art-1", content="suspicious payload",
            reason="flagged by anomaly detector",
        )
        self.assertEqual(rec.state, "QUARANTINED")

        # TAAL "REVIEWED" == real QUARANTINED -> VERIFIED, human-reviewed.
        reviewed = taal_mark_reviewed(
            store, "art-1", reason="manual inspection found no issue",
            reviewed_by="analyst-kim",
        )
        self.assertEqual(reviewed.state, "VERIFIED")
        self.assertEqual(reviewed.human_review_status, "REVIEWED_BY:analyst-kim")

        # TAAL "RECOVERED" == real VERIFIED -> AUTHORIZED.
        recovered = taal_mark_recovered(
            store, "art-1", reason="cleared for use",
        )
        self.assertEqual(recovered.state, "AUTHORIZED")

        # History preserved throughout — nothing deleted.
        self.assertEqual(len(store.get("art-1").history), 3)  # QUARANTINE, REVIEWED, RECOVERED

    def test_reviewed_requires_reviewed_by_on_the_real_store(self):
        """Confirms REVIEWED really means human-reviewed, enforced by the
        real store, not just documented."""
        store = QuarantineStore()
        taal_quarantine(
            store, artifact_id="art-2", content="payload",
            reason="flagged",
        )
        with self.assertRaises(IllegalTransition):
            store.transition("art-2", "VERIFIED", reason="auto-cleared", reviewed_by=None)


class TestQuarantinedThroughConfirmedPolicyViolationToContained(unittest.TestCase):
    """QUARANTINED -> (TAAL CONFIRMED_POLICY_VIOLATION) -> (TAAL CONTAINED)."""

    def test_full_violation_path(self):
        store = QuarantineStore()
        taal_quarantine(
            store, artifact_id="art-3", content="malformed access request",
            reason="flagged by policy engine",
        )

        confirmed = taal_mark_confirmed_policy_violation(
            store, "art-3", reason="human review confirmed policy breach",
            reviewed_by="analyst-lee",
        )
        self.assertEqual(confirmed.state, "REJECTED")

        contained = taal_mark_contained(
            store, "art-3", reason="archived after rejection",
        )
        self.assertEqual(contained.state, "ARCHIVED")

        # ARCHIVED is terminal in the real store — no further transitions.
        self.assertEqual(TRANSITIONS["ARCHIVED"], frozenset())
        with self.assertRaises(IllegalTransition):
            store.transition("art-3", "VERIFIED", reason="attempt to revive")


class TestRecoveredIsNotAutomaticFromVerified(unittest.TestCase):
    """A VERIFIED record can legally go to DISPUTED/SUSPICIOUS/ARCHIVED
    instead of AUTHORIZED — proving 'recovered' is a real, non-guaranteed
    edge, not a rename of VERIFIED itself."""

    def test_verified_record_can_diverge_from_authorized(self):
        store = QuarantineStore()
        taal_quarantine(
            store, artifact_id="art-4", content="edge case content",
            reason="flagged",
        )
        taal_mark_reviewed(
            store, "art-4", reason="reviewed", reviewed_by="analyst-ng",
        )
        # Instead of RECOVERED, this record becomes newly SUSPICIOUS —
        # legal per the real TRANSITIONS["VERIFIED"] row, and it must NOT
        # be reachable as "recovered" without actually calling the
        # AUTHORIZED transition.
        diverged = store.transition(
            "art-4", "SUSPICIOUS", reason="new evidence surfaced",
        )
        self.assertEqual(diverged.state, "SUSPICIOUS")
        self.assertNotEqual(diverged.state, "AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
