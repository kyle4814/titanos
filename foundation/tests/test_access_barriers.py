"""Tests for `foundation/access_barriers.py`.

The PNG fixtures below are verbatim from NPC/2026-26's own RFP, which is
the notice that proved this module was needed. Offline; no network path
exists in the module at all.
"""

import unittest
from pathlib import Path

from foundation import access_barriers
from foundation.access_barriers import (
    BARRIER_KINDS,
    AccessAssessment,
    AccessBarrier,
    AccessBarrierError,
    assess_access,
    format_access,
)


# Verbatim from the PNG RFP, downloaded and read 2026-09-03.
PNG_RFP = (
    "Bidding will be conducted through competitive procurement using a "
    "Request for Proposals (RFP), a two-envelope system with rated "
    "criteria, without prequalification as specified in the National "
    "Procurement Act, 2018 as amended, and is open to all eligible "
    "Bidders. The bidding document in English may be requested by "
    "interested eligible Bidders upon the submission of a written "
    "application to the address below and upon payment of a "
    "non-refundable fee of PGK5,000.00. Proposals must be delivered to "
    "the address below on or before June 15, 2026, 17:00 pm local PNG "
    "time. Electronic Bidding will not be permitted. Late Bids will be "
    "rejected. The outer Bid envelopes marked \"ORIGINAL BID\" and the "
    "inner envelopes marked \"TECHNICAL PART\""
)


class TestThePngNoticeThisWasBuiltFor(unittest.TestCase):
    """This notice had ZERO eligibility criteria -- its own words:
    'without prequalification ... open to all eligible Bidders' -- and
    was still unreachable. Every filter in this repository scored it as
    unresolved-but-promising. None could see either wall."""

    def test_the_document_fee_is_caught(self):
        a = assess_access(PNG_RFP)
        kinds = {b.kind for b in a.barriers}
        self.assertIn("DOCUMENT_FEE", kinds)

    def test_the_paper_only_submission_is_caught(self):
        a = assess_access(PNG_RFP)
        kinds = {b.kind for b in a.barriers}
        self.assertIn("PHYSICAL_SUBMISSION", kinds)

    def test_it_blocks_a_remote_solo_operator(self):
        self.assertTrue(assess_access(PNG_RFP).blocks_remote_solo_operator)

    def test_every_barrier_carries_quotable_evidence(self):
        for b in assess_access(PNG_RFP).barriers:
            self.assertTrue(b.evidence.strip())
            self.assertTrue(b.matched.strip())

    def test_the_render_names_the_fee_in_the_evidence(self):
        text = format_access(assess_access(PNG_RFP))
        self.assertIn("PGK5,000", text)


class TestSilenceIsNeverClearance(unittest.TestCase):
    """The rule this whole project rests on, applied here. An unread
    notice and a genuinely free one look identical from inside this
    module, and it must say so rather than imply otherwise."""

    def test_empty_text_is_not_assessed_not_clean(self):
        a = assess_access("")
        self.assertEqual(a.status, "NOT_ASSESSED")
        self.assertNotEqual(a.status, "NONE_DETECTED")

    def test_whitespace_is_also_not_assessed(self):
        self.assertEqual(assess_access("   \n  ").status, "NOT_ASSESSED")

    def test_not_assessed_does_not_claim_to_block_or_clear(self):
        self.assertFalse(assess_access("").blocks_remote_solo_operator)

    def test_none_detected_render_states_its_own_limit(self):
        text = format_access(assess_access("An ordinary notice about "
                                           "consultancy services."))
        self.assertIn("not proof there is none", text)

    def test_not_assessed_render_says_no_text_was_supplied(self):
        text = format_access(assess_access(""))
        self.assertIn("No document text was supplied", text)


class TestEachBarrierKind(unittest.TestCase):
    def test_local_entity_requirement(self):
        a = assess_access("Bidders must be registered in the Emirate and "
                          "hold a valid trade licence.")
        self.assertIn("LOCAL_ENTITY", {b.kind for b in a.barriers})
        self.assertTrue(a.blocks_remote_solo_operator)

    def test_mandatory_site_visit(self):
        a = assess_access("A mandatory site visit will be held on 12 June. "
                          "Attendance is compulsory.")
        self.assertIn("IN_PERSON_REQUIRED", {b.kind for b in a.barriers})
        self.assertTrue(a.blocks_remote_solo_operator)

    def test_bid_security(self):
        a = assess_access("Bidders shall furnish a bid security of "
                          "EUR 20,000 with their tender.")
        self.assertIn("BID_SECURITY", {b.kind for b in a.barriers})

    def test_bid_security_alone_does_not_claim_to_block(self):
        """A bond is a cash-flow problem, not an impossibility. Deciding
        it is fatal would be this module making the operator's call for
        him."""
        a = assess_access("A bid bond is required.")
        self.assertFalse(a.blocks_remote_solo_operator)

    def test_document_fee_alone_does_not_claim_to_block(self):
        """A fee is a cost decision, not a wall -- reported loudly,
        never treated as a refusal."""
        a = assess_access("Documents are available upon payment of a "
                          "non-refundable fee of AUD 500.")
        self.assertIn("DOCUMENT_FEE", {b.kind for b in a.barriers})
        self.assertFalse(a.blocks_remote_solo_operator)


class TestNoFalsePositivesOnOrdinaryText(unittest.TestCase):
    """A module that flags everything gets ignored, which returns it to
    the state it was built to fix."""

    def test_plain_notice_text_is_clean(self):
        for text in (
            "The Contracting Authority seeks a supplier of penetration "
            "testing services for a period of three years.",
            "Tenders must be submitted electronically via the portal.",
            "Award criteria: quality 60%, price 40%.",
            "The estimated value of the contract is EUR 300,000.",
        ):
            a = assess_access(text)
            self.assertEqual(a.barriers, (), f"false positive on: {text!r}")

    def test_electronic_submission_is_not_a_physical_barrier(self):
        a = assess_access("All bids shall be lodged through the e-tendering "
                          "portal. Paper submissions are not accepted.")
        self.assertNotIn("PHYSICAL_SUBMISSION", {b.kind for b in a.barriers})


class TestIntegrity(unittest.TestCase):
    def test_unknown_kind_is_refused(self):
        with self.assertRaises(AccessBarrierError):
            AccessBarrier(kind="EXPENSIVE", matched="x", evidence="y")

    def test_a_barrier_without_evidence_is_refused(self):
        with self.assertRaises(AccessBarrierError):
            AccessBarrier(kind="DOCUMENT_FEE", matched="fee", evidence="  ")

    def test_non_string_input_is_refused(self):
        with self.assertRaises(AccessBarrierError):
            assess_access(None)

    def test_render_rejects_a_non_assessment(self):
        with self.assertRaises(AccessBarrierError):
            format_access("BARRIERS_FOUND")

    def test_each_kind_is_reported_at_most_once(self):
        a = assess_access(PNG_RFP)
        kinds = [b.kind for b in a.barriers]
        self.assertEqual(len(kinds), len(set(kinds)))

    def test_module_has_no_network_import(self):
        src = Path(access_barriers.__file__).read_text(encoding="utf-8")
        for lib in ("urllib", "requests", "socket", "http.client"):
            self.assertNotIn(f"import {lib}", src)



class TestTheNegationGuard(unittest.TestCase):
    """Two errors, found in sequence on live documents, each caused by
    the fix for the other. Both are pinned here.

    ONE: scanned against six real tender documents, this module flagged
    FOUR for PHYSICAL_SUBMISSION on 'hand delivery' — inside the clause
    'Tenders submitted by any other means (including but not limited to:
    by email, fax, post, hand delivery, etc.) will NOT be accepted'.
    That is an electronic-only requirement listing hand delivery among
    the FORBIDDEN methods. It would have told the operator four
    reachable Irish notices were closed.

    TWO: guarding every barrier kind then suppressed the PNG document
    fee, because 'Electronic Bidding will not be permitted' sat two
    sentences after it. A fee is never cancelled by rejection language
    about something else."""

    IRISH_ELECTRONIC_ONLY = (
        "Tenders submitted by any other means (including but not limited "
        "to: by email, fax, post, hand delivery, etc.) will NOT be "
        "accepted by the Contracting Authority.")

    def test_an_excluded_methods_list_is_not_a_physical_requirement(self):
        a = assess_access(self.IRISH_ELECTRONIC_ONLY)
        self.assertNotIn("PHYSICAL_SUBMISSION", {b.kind for b in a.barriers})
        self.assertFalse(a.blocks_remote_solo_operator)

    def test_electronic_bidding_prohibited_is_still_caught(self):
        """The negation guard must not silence the case this module was
        built for: 'will not be permitted' here means paper only."""
        a = assess_access("Electronic Bidding will not be permitted.")
        self.assertIn("PHYSICAL_SUBMISSION", {b.kind for b in a.barriers})

    def test_a_fee_survives_nearby_rejection_language(self):
        a = assess_access(
            "upon payment of a non-refundable fee of PGK5,000.00. "
            "Proposals must be delivered to the address below. "
            "Electronic Bidding will not be permitted.")
        self.assertIn("DOCUMENT_FEE", {b.kind for b in a.barriers})

    def test_a_bid_bond_survives_nearby_rejection_language(self):
        a = assess_access(
            "A bid security is required. Late bids will NOT be accepted.")
        self.assertIn("BID_SECURITY", {b.kind for b in a.barriers})

    def test_a_local_entity_rule_survives_nearby_rejection_language(self):
        a = assess_access(
            "Bidders must be registered in the Emirate. "
            "Incomplete submissions will not be accepted.")
        self.assertIn("LOCAL_ENTITY", {b.kind for b in a.barriers})

    def test_only_delivery_methods_are_guarded(self):
        from foundation.access_barriers import _NEGATABLE_KINDS
        self.assertEqual(_NEGATABLE_KINDS, {"PHYSICAL_SUBMISSION"})


if __name__ == "__main__":
    unittest.main()
