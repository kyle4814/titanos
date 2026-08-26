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

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))

from kpm.promotion.state_machine import (  # noqa: E402
    IllegalTransition,
    PromotionStore,
    SelfPromotionForbidden,
)
from rpa.gates.human_jurisdiction import (  # noqa: E402
    AmbiguousValidatedSource,
    NoValidatedSource,
    SourceRegistry,
    authorize_pilot,
    confirm_pilot_authorized,
)

_FIXTURES_DIR = _REPO_ROOT / "rpa" / "fixtures"


def _tested_store(candidate_id="ac-001", created_by="agent-alice"):
    """A store with one candidate walked up to TESTED, ready for the gate."""
    store = PromotionStore()
    store.register(candidate_id, created_by=created_by)
    store.promote(candidate_id, "DISTILLED", reason="distilled")
    store.promote(candidate_id, "PROVISIONAL", reason="provisional")
    store.promote(candidate_id, "TESTED", reason="tested")
    return store


def _fresh_registry_with_valid_candidate():
    """A real SourceRegistry with the real, valid automation_candidate.yaml
    fixture ingested — used so these tests exercise the actual new guard
    against real content, not a mock."""
    import tempfile
    tmp = tempfile.mkdtemp()
    registry = SourceRegistry(archive_dir=tmp + "/archive", registry_path=None)
    text = (_FIXTURES_DIR / "automation_candidate.yaml").read_bytes()
    rec = registry.ingest_source(text, source_type="yaml",
                                  source_location="rpa/fixtures/automation_candidate.yaml",
                                  author_or_origin="test")
    return registry, rec.content_hash


def _authorize(store, candidate_id, *, reviewed_by, created_by, reason,
               registry=None, source_hashes=None):
    """Helper threading the new required source_registry/source_hashes
    params through authorize_pilot, defaulting to a real valid candidate
    fixture so existing test call sites stay close to their original
    shape."""
    if registry is None or source_hashes is None:
        registry, content_hash = _fresh_registry_with_valid_candidate()
        source_hashes = (content_hash,)
    return authorize_pilot(
        store, candidate_id, reviewed_by=reviewed_by, created_by=created_by,
        reason=reason, source_registry=registry, source_hashes=source_hashes,
    )


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
        rec = _authorize(
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
        _authorize(
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
        _authorize(
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
        _authorize(
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
        _authorize(
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
        _authorize(
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


class TestSourceContentValidationGuard(unittest.TestCase):
    """The real fix this session's own adversarial recon converged on:
    authorize_pilot() now requires the declared source_hashes to recover
    to exactly one real, structurally validated automation candidate
    before queueing anything for human review."""

    def test_valid_real_fixture_authorizes_normally(self):
        store = _tested_store()
        rec = _authorize(
            store, "ac-001", reviewed_by="agent-alice",
            created_by="agent-alice", reason="queue for human review",
        )
        self.assertEqual(rec.state, "HUMAN_REVIEW")

    def test_no_validated_source_is_refused(self):
        registry, _ = _fresh_registry_with_valid_candidate()
        # Ingest garbage that is NOT a real automation_candidate document.
        bad_rec = registry.ingest_source(
            b"not: a\nreal: automation candidate\n", source_type="yaml",
            source_location="garbage", author_or_origin="test",
        )
        store = _tested_store()
        with self.assertRaises(NoValidatedSource):
            _authorize(
                store, "ac-001", reviewed_by="agent-alice",
                created_by="agent-alice", reason="queue for human review",
                registry=registry, source_hashes=(bad_rec.content_hash,),
            )
        # The refused attempt must not have moved the record forward.
        self.assertEqual(store.get("ac-001").state, "TESTED")

    def test_unresolvable_hash_is_refused(self):
        registry, _ = _fresh_registry_with_valid_candidate()
        store = _tested_store()
        with self.assertRaises(NoValidatedSource):
            _authorize(
                store, "ac-001", reviewed_by="agent-alice",
                created_by="agent-alice", reason="queue for human review",
                registry=registry, source_hashes=("sha256:doesnotexist",),
            )

    def test_two_valid_sources_are_ambiguous_and_refused(self):
        registry, hash_a = _fresh_registry_with_valid_candidate()
        # A second, independently valid automation candidate.
        second_text = (
            (_FIXTURES_DIR / "automation_candidate.yaml").read_text()
            .replace("candidate-backup-approver-alert", "candidate-second-one")
        )
        second_rec = registry.ingest_source(
            second_text.encode(), source_type="yaml",
            source_location="second", author_or_origin="test",
        )
        store = _tested_store()
        with self.assertRaises(AmbiguousValidatedSource):
            _authorize(
                store, "ac-001", reviewed_by="agent-alice",
                created_by="agent-alice", reason="queue for human review",
                registry=registry, source_hashes=(hash_a, second_rec.content_hash),
            )
        self.assertEqual(store.get("ac-001").state, "TESTED")

    def test_end_to_end_bypass_is_now_refused_not_just_theoretically_possible(self):
        """This is the exact bypass the original recon constructed: queue
        an arbitrary blueprint_id for review with content that was never
        validated at all. It must now be refused."""
        registry, _ = _fresh_registry_with_valid_candidate()
        unrelated_rec = registry.ingest_source(
            b"completely unrelated content", source_type="text",
            source_location="unrelated", author_or_origin="test",
        )
        store = _tested_store(candidate_id="magl-arbitrary-unvalidated")
        with self.assertRaises(NoValidatedSource):
            _authorize(
                store, "magl-arbitrary-unvalidated", reviewed_by="agent-alice",
                created_by="agent-alice", reason="queue for human review",
                registry=registry, source_hashes=(unrelated_rec.content_hash,),
            )
        self.assertFalse(confirm_pilot_authorized(store, "magl-arbitrary-unvalidated"))


if __name__ == "__main__":
    unittest.main()
