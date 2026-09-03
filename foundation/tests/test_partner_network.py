"""Tests for `foundation/partner_network.py`.

Offline throughout; no test opens a socket, and NO test constructs a real
person or organisation -- every candidate here is synthetic. The suite is
built around the directive's adversarial cases: the module must fail safe
on fabricated credentials, AI-confidence state-skips, opt-outs, and the
core error of representing a contact as a partner.
"""

import unittest

from foundation.entry_gate import assess_entry
from foundation.partner_network import (
    EVIDENCE_TIERS,
    RELATIONSHIP_STATES,
    TERMINAL_STATES,
    EvidencedClaim,
    PartnerCandidate,
    PartnerNeed,
    PartnerNetworkError,
    advance_state,
    derive_partner_needs,
    format_partner_needs,
    is_partner,
)


def _candidate(**kw):
    base = dict(candidate_id="c1", organisation_name="Example Consulting Ltd",
                country="IE", relationship_status="DISCOVERED")
    base.update(kw)
    return PartnerCandidate(**base)


class TestAContactIsNeverAPartner(unittest.TestCase):
    """FIRST PRINCIPLE: real people > records. A scraped name, an email,
    a positive reply -- none is a partner. Only a signed active
    relationship is."""

    def test_a_discovered_candidate_is_not_a_partner(self):
        self.assertFalse(is_partner(_candidate(relationship_status="DISCOVERED")))

    def test_a_contacted_candidate_is_not_a_partner(self):
        self.assertFalse(is_partner(_candidate(relationship_status="CONTACTED")))

    def test_a_responded_candidate_is_not_a_partner(self):
        self.assertFalse(is_partner(_candidate(relationship_status="RESPONDED")))

    def test_only_an_active_relationship_is_a_partner(self):
        self.assertTrue(is_partner(_candidate(relationship_status="ACTIVE")))

    def test_an_opted_out_candidate_is_never_a_partner(self):
        self.assertFalse(is_partner(
            _candidate(relationship_status="ACTIVE", opted_out=True)))


class TestStatesCannotBeSkippedByConfidence(unittest.TestCase):
    """A partner cannot jump to ACTIVE because a model is confident. The
    lifecycle is stepwise and forward-only."""

    def test_a_single_forward_step_is_allowed(self):
        c = _candidate(relationship_status="DISCOVERED")
        self.assertEqual(advance_state(c, "UNVERIFIED").relationship_status,
                         "UNVERIFIED")

    def test_skipping_from_discovered_to_active_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            advance_state(_candidate(relationship_status="DISCOVERED"), "ACTIVE")

    def test_a_backwards_move_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            advance_state(_candidate(relationship_status="RESPONDED"),
                          "DISCOVERED")

    def test_a_terminal_state_is_reachable_from_anywhere(self):
        c = _candidate(relationship_status="NEGOTIATING")
        self.assertEqual(advance_state(c, "DECLINED").relationship_status,
                         "DECLINED")

    def test_a_terminal_candidate_cannot_advance(self):
        with self.assertRaises(PartnerNetworkError):
            advance_state(_candidate(relationship_status="REJECTED"), "ACTIVE")

    def test_advancing_never_mutates_the_original(self):
        c = _candidate(relationship_status="DISCOVERED")
        advance_state(c, "UNVERIFIED")
        self.assertEqual(c.relationship_status, "DISCOVERED")

    def test_the_full_pipeline_walks_one_step_at_a_time(self):
        c = _candidate(relationship_status="DISCOVERED")
        for nxt in RELATIONSHIP_STATES[1:]:
            c = advance_state(c, nxt)
        self.assertEqual(c.relationship_status, "ACTIVE")
        self.assertTrue(is_partner(c))


class TestOptOutIsRespected(unittest.TestCase):
    def test_an_opted_out_candidate_can_only_go_terminal(self):
        c = _candidate(relationship_status="RESPONDED", opted_out=True)
        with self.assertRaises(PartnerNetworkError):
            advance_state(c, "NEGOTIATING")
        # but may be moved to a terminal state
        self.assertEqual(advance_state(c, "INACTIVE").relationship_status,
                         "INACTIVE")


class TestSelfReportIsNotFact(unittest.TestCase):
    """A candidate's claims never become facts because the candidate says
    them. Evidence tiers separate a bare assertion from independent
    support."""

    def test_a_self_reported_claim_needs_no_source(self):
        c = EvidencedClaim("specialisation", "cybersecurity", "SELF_REPORTED")
        self.assertFalse(c.is_independently_evidenced)

    def test_a_verified_claim_without_a_source_is_refused(self):
        """A credential cannot be VERIFIED by nothing -- the exact
        fabrication the directive forbids."""
        with self.assertRaises(PartnerNetworkError):
            EvidencedClaim("certification", "CREST", "VERIFIED")

    def test_a_publicly_evidenced_claim_without_a_source_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            EvidencedClaim("references", "3 gov contracts", "PUBLICLY_EVIDENCED")

    def test_a_verified_claim_with_a_source_is_allowed(self):
        c = EvidencedClaim("certification", "CREST", "VERIFIED",
                           source_url="https://crest-approved.org/x")
        self.assertTrue(c.is_independently_evidenced)

    def test_an_unknown_capability_stays_unknown(self):
        c = EvidencedClaim("capacity", "UNKNOWN", "UNKNOWN")
        self.assertEqual(c.tier, "UNKNOWN")

    def test_a_bad_tier_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            EvidencedClaim("x", "y", "DEFINITELY_TRUE")


class TestCandidateIntegrity(unittest.TestCase):
    def test_a_candidate_must_name_the_organisation(self):
        with self.assertRaises(PartnerNetworkError):
            _candidate(organisation_name="   ")

    def test_a_bare_string_claim_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            _candidate(claims=("cybersecurity specialist",))

    def test_an_unknown_relationship_state_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            _candidate(relationship_status="BEST_FRIEND")

    def test_a_candidate_with_no_id_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            _candidate(candidate_id="")


class TestTheOpportunityToPartnerBridge(unittest.TestCase):
    """derive_partner_needs turns entry_gate's gate analysis into what a
    partner must supply -- the keystone. Verified against the real Irish
    documents' shape."""

    HELD_INSURANCE = ("P3 Minimum Insurance Requirements Pass/Fail. Tenderers "
                      "must maintain Public Liability Insurance of EUR6.5M.")
    TURNOVER_AND_REFS = ("Minimum annual turnover of 250k per annum. Evidence "
                         "of three reference contracts.")
    STAFFED_LOCAL = ("The service must be delivered by staff based within the "
                     "Republic of Ireland on a 24 hours a day, 7 days a week "
                     "basis.")
    DEFERRED = ("Applicants selected to Call-Off stage will be required to "
                "comply with the insurance requirements of the Contract.")

    def test_a_held_insurance_wall_becomes_a_partner_need(self):
        needs = derive_partner_needs(assess_entry(self.HELD_INSURANCE))
        self.assertIn("INSURANCE", {n.kind for n in needs})

    def test_turnover_and_references_become_partner_needs(self):
        needs = derive_partner_needs(assess_entry(self.TURNOVER_AND_REFS))
        kinds = {n.kind for n in needs}
        self.assertIn("MINIMUM_TURNOVER", kinds)
        self.assertIn("REFERENCES", kinds)

    def test_the_staffed_local_wall_becomes_a_local_partner_need(self):
        needs = derive_partner_needs(assess_entry(self.STAFFED_LOCAL))
        kinds = {n.kind for n in needs}
        self.assertTrue({"LOCAL_PRESENCE", "STAFFED_ROUND_THE_CLOCK"} & kinds)

    def test_a_deferred_requirement_is_NOT_a_partner_need(self):
        """The operator can meet a deferred/declaration gate himself -- no
        partner needed, and inventing one would be false."""
        needs = derive_partner_needs(assess_entry(self.DEFERRED))
        self.assertEqual(needs, ())

    def test_an_opportunity_with_no_gates_needs_no_partner(self):
        needs = derive_partner_needs(assess_entry(
            "The authority seeks a supplier of advisory services."))
        self.assertEqual(needs, ())
        self.assertIn("NO PARTNER NEEDED", format_partner_needs(needs))

    def test_every_need_quotes_the_opportunity_clause(self):
        for n in derive_partner_needs(assess_entry(self.TURNOVER_AND_REFS)):
            self.assertTrue(n.quote.strip())

    def test_a_partner_need_of_an_unknown_kind_is_refused(self):
        with self.assertRaises(PartnerNetworkError):
            PartnerNeed(kind="MAGIC", quote="x", reason="y")

    def test_the_render_states_a_need_is_not_a_match_or_authority(self):
        out = format_partner_needs(derive_partner_needs(
            assess_entry(self.HELD_INSURANCE)))
        self.assertIn("NOT a matched partner", out)
        self.assertIn("human-approved", out)


class TestNoNetworkNoOutreach(unittest.TestCase):
    """This slice is data and pure functions only -- no socket, no send
    verb, no scraping."""

    def test_module_has_no_network_import(self):
        from pathlib import Path
        from foundation import partner_network
        src = Path(partner_network.__file__).read_text(encoding="utf-8")
        for lib in ("urllib", "requests", "socket", "http.client", "smtplib"):
            self.assertNotIn(f"import {lib}", src)

    def test_no_public_name_suggests_sending_or_scraping(self):
        from foundation import partner_network
        for name in dir(partner_network):
            if name.startswith("_"):
                continue
            for bad in ("send", "email", "scrape", "fetch", "contact_partner",
                        "outreach"):
                self.assertNotIn(bad, name.lower())


if __name__ == "__main__":
    unittest.main()
