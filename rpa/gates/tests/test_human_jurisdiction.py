"""
Human Jurisdiction Gate tests.

rpa/gates/human_jurisdiction.py is a thin wrapper around
kpm.promotion.state_machine — these tests verify the wrapper sequences
the two real gates correctly (TESTED -> HUMAN_REVIEW via authorize_pilot,
then a SEPARATE HUMAN_REVIEW -> STABLE call), that it never suppresses
SelfPromotionForbidden, and that confirm_pilot_authorized re-derives its
answer from the record's actual history rather than trusting the state
label.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from kpm.promotion.state_machine import (  # noqa: E402
    IllegalTransition,
    PromotionStore,
    SelfPromotionForbidden,
)
from rpa.gates.human_jurisdiction import (  # noqa: E402
    authorize_pilot,
    confirm_pilot_authorized,
)


def _tested_store(candidate_id="ac-001", created_by="agent-alice"):
    """A store with one candidate walked up to TESTED, ready for the gate."""
    store = PromotionStore()
    store.register(candidate_id, created_by=created_by)
    store.promote(candidate_id, "DISTILLED", reason="distilled")
    store.promote(candidate_id, "PROVISIONAL", reason="provisional")
    store.promote(candidate_id, "TESTED", reason="tested")
    return store


class TestCannotReachStableWithoutHumanReview(unittest.TestCase):
    """No path to STABLE for an automation candidate that skips
    HUMAN_REVIEW via this gate's intended TESTED -> HUMAN_REVIEW ->
    STABLE sequence — and more generally, PromotionStore's own
    TRANSITIONS table has no edge from RAW/DISTILLED/PROVISIONAL/
    CONTESTED/QUARANTINED directly to STABLE at all."""

    def test_raw_cannot_transition_directly_to_stable(self):
        store = PromotionStore()
        store.register("ac-002", created_by="agent-alice")
        with self.assertRaises(IllegalTransition):
            store.promote("ac-002", "STABLE", reason="skip", reviewed_by="agent-bob")

    def test_distilled_cannot_transition_directly_to_stable(self):
        store = PromotionStore()
        store.register("ac-003", created_by="agent-alice")
        store.promote("ac-003", "DISTILLED", reason="distilled")
        with self.assertRaises(IllegalTransition):
            store.promote("ac-003", "STABLE", reason="skip", reviewed_by="agent-bob")

    def test_authorize_pilot_only_reaches_human_review_not_stable(self):
        store = _tested_store()
        rec = authorize_pilot(
            store, "ac-001", reviewed_by="agent-alice",
            created_by="agent-alice", reason="queue for human review",
        )
        self.assertEqual(rec.state, "HUMAN_REVIEW")
        self.assertNotEqual(rec.state, "STABLE")
        # A second, separate call is required to actually reach STABLE —
        # authorize_pilot does not and must not perform it.
        self.assertFalse(confirm_pilot_authorized(store, "ac-001"))

    def test_full_authorized_path_requires_two_separate_calls(self):
        store = _tested_store()
        authorize_pilot(
            store, "ac-001", reviewed_by="agent-alice",
            created_by="agent-alice", reason="queue for human review",
        )
        # Second, separate call: an independent human actually approves.
        rec = store.promote(
            "ac-001", "STABLE", reason="reviewed and approved",
            reviewed_by="agent-bob",
        )
        self.assertEqual(rec.state, "STABLE")
        self.assertTrue(confirm_pilot_authorized(store, "ac-001"))


class TestAuthorizePilotCannotSelfApprove(unittest.TestCase):
    """authorize_pilot itself only reaches HUMAN_REVIEW, which has no
    reviewed_by-must-differ requirement in TRANSITIONS (queueing your own
    candidate for review is legitimate). Self-approval is forbidden at
    the STABLE step, which lives outside authorize_pilot by design — this
    test proves SelfPromotionForbidden propagates unchanged through the
    real gate (the second, separate store.promote call), i.e. the wrapper
    does nothing to weaken or hide that guarantee."""

    def test_self_promotion_to_stable_raises_through_the_real_gate(self):
        store = _tested_store(created_by="agent-alice")
        authorize_pilot(
            store, "ac-001", reviewed_by="agent-alice",
            created_by="agent-alice", reason="queue for human review",
        )
        with self.assertRaises(SelfPromotionForbidden):
            store.promote(
                "ac-001", "STABLE", reason="i approve my own work",
                reviewed_by="agent-alice",
            )
        # The forbidden attempt must not have moved the record forward.
        self.assertEqual(store.get("ac-001").state, "HUMAN_REVIEW")
        self.assertFalse(confirm_pilot_authorized(store, "ac-001"))

    def test_self_promotion_forbidden_is_an_illegal_transition_subclass(self):
        # SelfPromotionForbidden IS-A IllegalTransition — a caller
        # catching the broader exception still catches this.
        self.assertTrue(issubclass(SelfPromotionForbidden, IllegalTransition))


class TestConfirmPilotAuthorized(unittest.TestCase):
    def test_true_for_properly_authorized_record(self):
        store = _tested_store(created_by="agent-alice")
        authorize_pilot(
            store, "ac-001", reviewed_by="agent-alice",
            created_by="agent-alice", reason="queue for human review",
        )
        store.promote(
            "ac-001", "STABLE", reason="reviewed and approved",
            reviewed_by="agent-bob",
        )
        self.assertTrue(confirm_pilot_authorized(store, "ac-001"))

    def test_false_for_missing_record(self):
        store = PromotionStore()
        self.assertFalse(confirm_pilot_authorized(store, "does-not-exist"))

    def test_false_for_record_not_yet_stable(self):
        store = _tested_store()
        self.assertFalse(confirm_pilot_authorized(store, "ac-001"))
        authorize_pilot(
            store, "ac-001", reviewed_by="agent-alice",
            created_by="agent-alice", reason="queue for human review",
        )
        self.assertFalse(confirm_pilot_authorized(store, "ac-001"))

    def test_false_for_stable_reached_via_tested_not_human_review(self):
        """STABLE is reachable two ways per the real TRANSITIONS table:
        TESTED -> STABLE and HUMAN_REVIEW -> STABLE. This gate's design
        always routes through HUMAN_REVIEW (authorize_pilot's whole job).
        A record that reached STABLE via the OTHER legal edge —
        TESTED -> STABLE directly, bypassing this gate's queueing step —
        is proven reachable here (the edge is real, per TRANSITIONS), but
        confirm_pilot_authorized deliberately does NOT consider it
        pilot-authorized, because it never passed through this gate's
        HUMAN_REVIEW checkpoint at all. This is the documented finding:
        the state machine permits TESTED -> STABLE for promotable units
        in general, and this gate intentionally narrows what counts as
        'authorized' for automation candidates specifically."""
        store = _tested_store(created_by="agent-alice")
        rec = store.promote(
            "ac-001", "STABLE", reason="tested and approved directly",
            reviewed_by="agent-bob",
        )
        self.assertEqual(rec.state, "STABLE")
        # Reachable via the state machine's real rules...
        self.assertTrue(rec.state == "STABLE")
        # ...but NOT considered authorized by this gate, because it did
        # not go through HUMAN_REVIEW.
        self.assertFalse(confirm_pilot_authorized(store, "ac-001"))

    def test_does_not_trust_state_label_alone(self):
        """Defensive check: confirm_pilot_authorized inspects history,
        not just the state field. A record manually forced into a shape
        where state says STABLE but history's last STABLE-producing
        entry has no reviewed_by (or reviewed_by == created_by) must
        still return False. Since PromotionRecord's public API always
        produces consistent history via promote(), we simulate a
        corrupted/foreign record shape directly to prove the function
        checks history rather than merely `state == 'STABLE'`."""
        store = _tested_store(created_by="agent-alice")
        authorize_pilot(
            store, "ac-001", reviewed_by="agent-alice",
            created_by="agent-alice", reason="queue for human review",
        )
        store.promote(
            "ac-001", "STABLE", reason="reviewed and approved",
            reviewed_by="agent-bob",
        )
        rec = store.get("ac-001")
        self.assertTrue(confirm_pilot_authorized(store, "ac-001"))

        # Corrupt the history entry that produced STABLE so its
        # reviewed_by collapses onto created_by, while leaving
        # rec.state == "STABLE" untouched. A naive
        # "state == STABLE" check would still say authorized; the real
        # implementation must not.
        for entry in reversed(rec.history):
            if entry.get("to") == "STABLE":
                entry["reviewed_by"] = rec.created_by
                break
        self.assertEqual(rec.state, "STABLE")
        self.assertFalse(confirm_pilot_authorized(store, "ac-001"))


if __name__ == "__main__":
    unittest.main()
