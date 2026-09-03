"""Tests for `foundation/entry_gate.py`.

Offline throughout; no test here opens a socket. Every quoted fixture is
verbatim from a real Irish procurement document downloaded and read on
2026-09-03/04 through eTenders' own anonymous-download control.

This file is mostly a record of the module getting it WRONG first. Its
first ranking put Asiera's EUR175M DPS -- which demands a 24x7x365
staffed Security Operations Centre -- at the top of the list as the
cheapest thing to start, and buried the EUR250k penetration-testing
qualification system that is actually reachable. Each class below pins
one of the defects that produced that inversion.
"""

import unittest

from foundation.entry_gate import (
    DISCHARGEABLE_BY_WORK,
    EntryAssessment,
    EntryGateError,
    GATE_KINDS,
    GateFinding,
    REQUIRES_OPERATOR,
    SHORT_DOCUMENT_CHARS,
    assess_entry,
    format_entry,
    rank_by_entry_cost,
)

# --- verbatim fixtures ------------------------------------------------

# Iarnrod Eireann 7289, the reachable one. Its ONLY insurance sentence.
IRISH_RAIL_DEFERRED = (
    "Applicants should note that those who have been selected to "
    "Call-Off stage, will be required to comply with the insurance "
    "requirements of the IE Standard Contract and will be required to "
    "be in possession of and produce a Tax Clearance Certificate from "
    "the Revenue Commissioners of Ireland at time of contract award."
)

# RTE 25P041, the unreachable one. Same requirement, admission stage.
RTE_ADMISSION = (
    "P3 Minimum Insurance Requirements Pass/Fail. Tenderers must "
    "maintain the following minimum levels of insurance cover: "
    "Public Liability EUR6.5M Cyber Insurance EUR1.0m Professional "
    "Liability EUR1.0m"
)

# The applicant-details form every PQQ in existence carries.
FORM_FIELD = (
    "1.4 Registered Address/Registered Office 1.5 Company registration "
    "number: 1.6 Contact details for queries in relation to this "
    "questionnaire"
)

# RTE describing the SERVICES IT IS BUYING, not a condition on bidders.
SERVICES_DESCRIPTION = (
    "consultancy services, including but not limited to: Penetration "
    "testing and vulnerability assessments, Incident response and "
    "forensic investigations, Support for certification and regulatory "
    "compliance (e.g., ISO 27001, GDPR)"
)

# Irish Rail asking a scored question that may be answered "no".
SCORED_QUESTION = (
    "Is the Applicants Quality Management System currently certified as "
    "compliant with EN ISO 9001:2000 or an equivalent internationally "
    "recognised Standard"
)

ASIERA_247 = (
    "1.5.4 24x7 Security Operations Centre (SOC). Interested Party must "
    "provide their SOC and Incident Response Services on a 24 hour a "
    "day, 7 days a week, 365 days a year basis."
)

HSE_LOCAL = (
    "IV.5 Service Provision: the service is delivered by staff based "
    "within Republic of Ireland, Cyber IR onsite within 24hrs, and the "
    "Service provider must be able to provide Dublin based non-contract "
    "resources to support on-site."
)

IRISH_RAIL_TURNOVER = (
    "(1) Minimum Financial Qualification Criteria: (PASS/FAIL) TURNOVER "
    "(exclusive of VAT): A minimum annual turnover of 250k per annum "
    "for the last three audited financial year ends."
)


class TestTheInversionThisModuleWasRebuiltToFix(unittest.TestCase):
    """The whole point, stated as one test: the document that defers its
    requirements must rank cheaper to start than the one that demands
    them up front, and a round-the-clock staffed service must rank
    dearer than a turnover figure."""

    def test_deferred_insurance_ranks_cheaper_than_admission_insurance(self):
        deferred = assess_entry(IRISH_RAIL_DEFERRED + IRISH_RAIL_TURNOVER)
        upfront = assess_entry(RTE_ADMISSION + IRISH_RAIL_TURNOVER)
        self.assertLess(deferred.entry_cost, upfront.entry_cost)

    def test_a_deferred_gate_does_not_need_the_operator_to_start(self):
        a = assess_entry(IRISH_RAIL_DEFERRED)
        self.assertEqual(a.operator_gates, ())
        self.assertTrue(a.deferred_gates)

    def test_an_admission_gate_does_need_the_operator_to_start(self):
        a = assess_entry(RTE_ADMISSION)
        self.assertIn("INSURANCE", {g.kind for g in a.operator_gates})

    def test_a_round_the_clock_service_outweighs_a_turnover_figure(self):
        """Both are 'dischargeable by work'. One needs a partner's
        accounts; the other needs a night shift, forever. Weighting them
        equally is what put a 24x7 SOC at the top of the list."""
        staffed = assess_entry(ASIERA_247)
        money = assess_entry(IRISH_RAIL_TURNOVER)
        self.assertGreater(staffed.entry_cost, money.entry_cost)


class TestStagingReadsTheDocumentsOwnWords(unittest.TestCase):
    def test_call_off_language_defers_the_requirement(self):
        a = assess_entry(IRISH_RAIL_DEFERRED)
        self.assertEqual(a.gate("INSURANCE").stage, "POST_ADMISSION")

    def test_pass_fail_language_pins_it_at_admission(self):
        a = assess_entry(RTE_ADMISSION)
        self.assertEqual(a.gate("INSURANCE").stage, "ADMISSION")

    def test_admission_evidence_beats_deferral_evidence(self):
        """A REAL BUG. RTE's Pass/Fail insurance table sat within the
        old 400-character window of an unrelated tax-clearance sentence
        ('prior to the award'), and was reported as POST_ADMISSION --
        inverting the single distinction this module exists to make."""
        both = RTE_ADMISSION + " Prior to the award of any contract, the " \
               "successful Tenderer shall be required to produce a Tax " \
               "Clearance Certificate."
        self.assertEqual(assess_entry(both).gate("INSURANCE").stage,
                         "ADMISSION")

    def test_a_requirement_with_no_staging_language_is_unknown(self):
        a = assess_entry("Tenderers must hold valid professional indemnity.")
        self.assertEqual(a.gate("INSURANCE").stage, "UNKNOWN")

    def test_unknown_staging_is_treated_as_blocking_not_as_deferred(self):
        """Guessing 'probably later' on silence is the optimistic read
        this repository refuses everywhere else."""
        a = assess_entry("Tenderers must hold valid professional indemnity.")
        self.assertTrue(a.gate("INSURANCE").blocks_starting)


class TestFalsePositivesThatFiredOnEveryDocument(unittest.TestCase):
    """Both false positives were the same failure in different clothes:
    a thing NAMED in a document read as a thing DEMANDED of you. It is
    the same class as the TED sweep matching 'Market research services'
    as market engagement when it was the service being procured."""

    def test_a_form_field_asking_for_a_company_number_is_not_a_requirement(self):
        a = assess_entry(FORM_FIELD)
        self.assertIsNone(a.gate("LEGAL_ENTITY"))

    def test_a_standard_named_in_the_scope_of_services_is_not_a_requirement(self):
        """RTE lists ISO 27001 among the things it wants CONSULTING ON."""
        a = assess_entry(SERVICES_DESCRIPTION)
        self.assertIsNone(a.gate("CERTIFICATION"))

    def test_a_scored_question_about_iso_is_not_a_mandatory_certification(self):
        a = assess_entry(SCORED_QUESTION)
        self.assertIsNone(a.gate("CERTIFICATION"))

    def test_a_real_certification_demand_is_still_caught(self):
        a = assess_entry("Tenderers must hold a valid ISO 27001 certification.")
        self.assertIsNotNone(a.gate("CERTIFICATION"))

    def test_a_real_legal_entity_demand_is_still_caught(self):
        a = assess_entry("Applicants must be a registered company in the EU.")
        self.assertIsNotNone(a.gate("LEGAL_ENTITY"))


class TestGatesThisCouldNotSeeAtAll(unittest.TestCase):
    def test_insurance_named_only_by_reference_to_a_contract_is_found(self):
        """Iarnrod Eireann's three PQQs name no policy type at all --
        'comply with the insurance requirements of the Contract'. A gate
        the module cannot see cannot be reported as deferred, and being
        deferred is the entire finding for those documents."""
        a = assess_entry("will be required to comply with the insurance "
                         "requirements of the Contract")
        self.assertIsNotNone(a.gate("INSURANCE"))


class TestSilenceIsNeverClearance(unittest.TestCase):
    def test_empty_text_is_not_assessed(self):
        self.assertEqual(assess_entry("").status, "NOT_ASSESSED")

    def test_a_clean_read_is_never_called_ungated(self):
        """`NO_GATE_STATED`, not `UNGATED`. A document that does not
        mention insurance has not told you none is needed."""
        a = assess_entry("The authority seeks a supplier of advisory services.")
        self.assertEqual(a.status, "NO_GATE_STATED")
        self.assertNotIn("UNGATED", a.status)

    def test_the_render_says_unknown_not_zero(self):
        text = format_entry(assess_entry("A short ordinary notice."))
        self.assertIn("UNKNOWN, not zero", text)

    def test_the_render_of_an_unread_document_states_its_own_blindness(self):
        self.assertIn("not a clean bill of health", format_entry(assess_entry("")))

    def test_a_fragment_is_flagged_so_a_cheap_score_is_not_believed(self):
        """Asiera's Part B is 7,569 characters of a multi-file pack and
        scored cheapest on the first run because most of its
        requirements live in files this never saw."""
        a = assess_entry(ASIERA_247)
        self.assertLess(a.chars_read, SHORT_DOCUMENT_CHARS)
        self.assertIn("CAUTION", format_entry(a))

    def test_a_full_document_carries_no_fragment_caution(self):
        a = assess_entry(IRISH_RAIL_DEFERRED + "x" * SHORT_DOCUMENT_CHARS)
        self.assertNotIn("CAUTION", format_entry(a))


class TestEachGateKind(unittest.TestCase):
    def test_round_the_clock_staffing(self):
        self.assertIsNotNone(assess_entry(ASIERA_247).gate(
            "STAFFED_ROUND_THE_CLOCK"))

    def test_local_presence(self):
        self.assertIsNotNone(assess_entry(HSE_LOCAL).gate("LOCAL_PRESENCE"))

    def test_minimum_turnover(self):
        self.assertIsNotNone(assess_entry(IRISH_RAIL_TURNOVER).gate(
            "MINIMUM_TURNOVER"))

    def test_references(self):
        a = assess_entry("Evidence of three customers for whom they have "
                         "delivered similar services.")
        self.assertIsNotNone(a.gate("REFERENCES"))

    def test_tax_clearance_is_identity_verification(self):
        self.assertIsNotNone(assess_entry(IRISH_RAIL_DEFERRED).gate(
            "IDENTITY_VERIFICATION"))

    def test_entry_fee(self):
        a = assess_entry("upon payment of a non-refundable fee of PGK5,000.00")
        self.assertIsNotNone(a.gate("ENTRY_FEE"))

    def test_account_registration(self):
        a = assess_entry("Suppliers must first register on the portal.")
        self.assertIsNotNone(a.gate("ACCOUNT_REGISTRATION"))


class TestNoFalsePositivesOnOrdinaryNoticeText(unittest.TestCase):
    def test_plain_notice_text_states_no_gate(self):
        for text in (
            "The Contracting Authority seeks a supplier of penetration "
            "testing services for a period of three years.",
            "Award criteria: quality 60%, price 40%.",
            "The estimated value of the contract is EUR 300,000.",
            "Tenders must be submitted electronically via the portal.",
        ):
            self.assertEqual(assess_entry(text).gates, (),
                             f"false positive on: {text!r}")


class TestRanking(unittest.TestCase):
    def test_cheapest_to_start_comes_first(self):
        pairs = [("expensive", assess_entry(HSE_LOCAL + ASIERA_247)),
                 ("cheap", assess_entry(IRISH_RAIL_DEFERRED))]
        self.assertEqual(rank_by_entry_cost(pairs)[0][0], "cheap")

    def test_ties_break_deterministically_on_label(self):
        a = assess_entry(IRISH_RAIL_DEFERRED)
        pairs = [("b", a), ("a", a)]
        self.assertEqual([p[0] for p in rank_by_entry_cost(pairs)], ["a", "b"])

    def test_it_refuses_anything_that_is_not_an_assessment(self):
        with self.assertRaises(EntryGateError):
            rank_by_entry_cost([("x", "not an assessment")])


class TestIntegrity(unittest.TestCase):
    def test_every_kind_is_classified_exactly_once(self):
        self.assertEqual(set(GATE_KINDS),
                         REQUIRES_OPERATOR | DISCHARGEABLE_BY_WORK)
        self.assertEqual(REQUIRES_OPERATOR & DISCHARGEABLE_BY_WORK, set())

    def test_an_unknown_kind_is_refused(self):
        with self.assertRaises(EntryGateError):
            GateFinding(kind="EXPENSIVE", matched="x", quote="y",
                        stage="UNKNOWN")

    def test_an_unknown_stage_is_refused(self):
        with self.assertRaises(EntryGateError):
            GateFinding(kind="INSURANCE", matched="x", quote="y",
                        stage="LATER_MAYBE")

    def test_a_finding_with_no_quote_is_refused(self):
        with self.assertRaises(EntryGateError):
            GateFinding(kind="INSURANCE", matched="x", quote="  ",
                        stage="UNKNOWN")

    def test_non_string_input_is_refused(self):
        with self.assertRaises(EntryGateError):
            assess_entry(None)

    def test_format_refuses_a_non_assessment(self):
        with self.assertRaises(EntryGateError):
            format_entry("GATES_FOUND")

    def test_each_kind_is_reported_at_most_once(self):
        """A 40-page PQQ mentions insurance eleven times; eleven
        identical findings is noise, not evidence."""
        text = (RTE_ADMISSION + " ") * 5
        kinds = [g.kind for g in assess_entry(text).gates]
        self.assertEqual(len(kinds), len(set(kinds)))

    def test_module_has_no_network_import(self):
        from pathlib import Path
        from foundation import entry_gate
        src = Path(entry_gate.__file__).read_text(encoding="utf-8")
        for lib in ("urllib", "requests", "socket", "http.client"):
            self.assertNotIn(f"import {lib}", src)


if __name__ == "__main__":
    unittest.main()
