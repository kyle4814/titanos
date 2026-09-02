"""Tests for `foundation/notice_class.py`.

Every fixture below is a real value read off a live notice during the
2026-09 campaign. Offline; this module has no network path at all.
"""

import unittest

from foundation.notice_class import (
    CLASSES,
    CLASS_ORDER,
    NoticeClassError,
    NoticeClassification,
    classify_notice,
    format_classification,
)


class TestRealNotices(unittest.TestCase):
    """The eight notices that motivated this module. Five are closed
    tenders, three are answerable — and before this module every one of
    them scored INSUFFICIENT_DATA, identically."""

    def test_ukri_market_engagement_from_ocds_status(self):
        """UKRI-6251, UK Research & Innovation, GBP1,250,000. Returned
        tender.status 'planning' with no tenderPeriod — the structured
        marker that a notice precedes the tender itself."""
        c = classify_notice(
            title="UKRI-6251 Cyber Security - Managed Service and Detection "
                  "Response & Security Operations Centre service",
            ocds_status="planning")
        self.assertEqual(c.notice_class, "MARKET_ENGAGEMENT")
        self.assertTrue(c.answerable_without_qualification)

    def test_ukri_market_engagement_from_notice_type(self):
        c = classify_notice(
            notice_type="Preliminary market engagement notice (UK2)")
        self.assertEqual(c.notice_class, "MARKET_ENGAGEMENT")

    def test_health_nz_rfi(self):
        """Health NZ RFI26-663, Enterprise Observability, regions
        International, Required Pre-qualifications: None."""
        c = classify_notice(
            title="Enterprise Observability Capability and Platform",
            notice_type="Request for Information (Market research) (RFI)")
        self.assertEqual(c.notice_class, "MARKET_ENGAGEMENT")

    def test_nz_defence_advance_notice(self):
        """NZ Ministry of Defence TSS-2026-AN, panel reset, closes
        30 Sep. Two markers — the notice type says advance notice, the
        title says panel reset."""
        c = classify_notice(
            title="Advance Notice - Technical Support Services (TSS) "
                  "Panel Reset 2026",
            notice_type="Notice of Information (Advance Notice) (NOI)")
        self.assertEqual(c.notice_class, "MARKET_ENGAGEMENT")

    def test_ccs_dps_is_rolling_admission(self):
        """Crown Commercial Service Cyber Security Services 3, open to
        13 Feb 2029, admits suppliers throughout its life."""
        c = classify_notice(title="Cyber Security Services 3",
                            description="Crown Commercial Service set up a "
                                        "dynamic purchasing system")
        self.assertEqual(c.notice_class, "ROLLING_ADMISSION")
        self.assertFalse(
            c.answerable_without_qualification,
            "a DPS removes the deadline, not the selection criteria")

    def test_bradford_open_framework_is_rolling_admission(self):
        c = classify_notice(
            title="Ad-Hoc Application Penetration Testing and IT Health "
                  "Checks (PSN) and Other Security Services",
            procedure="Open Framework under the Procurement Act 2023")
        self.assertEqual(c.notice_class, "ROLLING_ADMISSION")

    def test_an_post_pqq_is_competitive(self):
        c = classify_notice(
            title="0055 - The Provision of Security Operations Centre (SOC) "
                  "and Security Information and Event Management (SIEM)",
            notice_type="PQQ")
        self.assertEqual(c.notice_class, "COMPETITIVE")

    def test_hsa_rft_is_competitive(self):
        c = classify_notice(
            title="Security Operations Centre (SOC), Security Information "
                  "and Event Management (SIEM) and Managed Incident Response",
            notice_type="Request for Tenders (RFT)")
        self.assertEqual(c.notice_class, "COMPETITIVE")

    def test_award_notice_is_already_decided(self):
        c = classify_notice(notice_type="Contract award notice")
        self.assertEqual(c.notice_class, "ALREADY_DECIDED")

    def test_ted_can_standard_is_already_decided(self):
        c = classify_notice(notice_type="can-standard")
        self.assertEqual(c.notice_class, "ALREADY_DECIDED")


class TestUnknownIsNeverInferred(unittest.TestCase):
    """The load-bearing rule. Mistaking a tender for market engagement
    wastes an afternoon. Mistaking market engagement for a tender means
    never answering the one class with no barrier — and that is the
    error silence produces."""

    def test_empty_notice_is_unknown(self):
        self.assertEqual(classify_notice().notice_class, "UNKNOWN")

    def test_unrecognised_text_is_unknown_not_competitive(self):
        c = classify_notice(title="Supply of office furniture",
                            notice_type="something the codelist omits")
        self.assertEqual(c.notice_class, "UNKNOWN")
        self.assertNotEqual(c.notice_class, "COMPETITIVE")

    def test_unknown_carries_no_fabricated_evidence(self):
        c = classify_notice()
        self.assertEqual(c.evidence, "")
        self.assertEqual(c.matched_on, "")

    def test_unknown_is_not_answerable(self):
        self.assertFalse(classify_notice().answerable_without_qualification)


class TestPrecedence(unittest.TestCase):
    """Structured fields outrank prose, because a tender whose
    description mentions a past market-engagement exercise is still a
    tender."""

    def test_ocds_status_outranks_a_contradicting_title(self):
        c = classify_notice(title="Request for Tenders for X",
                            ocds_status="planning")
        self.assertEqual(c.notice_class, "MARKET_ENGAGEMENT")
        self.assertEqual(c.matched_on, "ocds_status")

    def test_notice_type_outranks_description(self):
        c = classify_notice(
            notice_type="Request for Tenders (RFT)",
            description="following our earlier preliminary market engagement")
        self.assertEqual(c.notice_class, "COMPETITIVE")
        self.assertEqual(c.matched_on, "notice_type")

    def test_title_outranks_description(self):
        c = classify_notice(
            title="Dynamic Purchasing System for security services",
            description="request for tender documents attached")
        self.assertEqual(c.notice_class, "ROLLING_ADMISSION")
        self.assertEqual(c.matched_on, "title")

    def test_already_decided_wins_within_one_field(self):
        """An award notice for a DPS is still an award notice — the work
        is gone regardless of the vehicle it was bought through."""
        c = classify_notice(
            notice_type="Contract award notice for a dynamic purchasing system")
        self.assertEqual(c.notice_class, "ALREADY_DECIDED")


class TestIntegrity(unittest.TestCase):
    def test_unknown_class_is_refused(self):
        with self.assertRaises(NoticeClassError):
            NoticeClassification(notice_class="PROMISING", evidence="x",
                                 matched_on="title")

    def test_classified_notice_must_carry_evidence(self):
        with self.assertRaises(NoticeClassError):
            NoticeClassification(notice_class="MARKET_ENGAGEMENT",
                                 evidence="   ", matched_on="title")

    def test_unknown_may_carry_no_evidence(self):
        c = NoticeClassification(notice_class="UNKNOWN", evidence="",
                                 matched_on="")
        self.assertEqual(c.notice_class, "UNKNOWN")

    def test_every_class_appears_in_the_display_order(self):
        self.assertEqual(sorted(CLASSES), sorted(CLASS_ORDER))

    def test_market_engagement_leads_the_display_order(self):
        self.assertEqual(CLASS_ORDER[0], "MARKET_ENGAGEMENT")
        self.assertEqual(CLASS_ORDER[-1], "ALREADY_DECIDED")

    def test_unknown_ranks_above_competitive(self):
        """An unresolved notice may still be answerable; a competitive
        one has known criteria to fail. Unknown therefore deserves a
        look first."""
        self.assertLess(CLASS_ORDER.index("UNKNOWN"),
                        CLASS_ORDER.index("COMPETITIVE"))


class TestRender(unittest.TestCase):
    def test_render_states_what_unknown_is_not(self):
        text = format_classification(classify_notice())
        self.assertIn("NOT 'probably a tender'", text)

    def test_render_flags_a_zero_barrier_notice(self):
        text = format_classification(classify_notice(ocds_status="planning"))
        self.assertIn("no turnover, insurance, references", text)

    def test_render_does_not_flag_a_dps(self):
        text = format_classification(
            classify_notice(title="dynamic purchasing system"))
        self.assertNotIn("no turnover, insurance, references", text)

    def test_render_rejects_a_non_classification(self):
        with self.assertRaises(NoticeClassError):
            format_classification("MARKET_ENGAGEMENT")


if __name__ == "__main__":
    unittest.main()
