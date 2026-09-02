import re
import unittest

from foundation.dossier import (
    DRAFT_STAMP, SCHEMES, UNKNOWN_MARKER,
    BusinessFacts, MissingFact, Referee, SupplierDossier,
    missing_facts_for_scheme, render_dossier,
)
from foundation.qualification import OperatorProfile


def _empty_profile():
    return OperatorProfile(
        name="Solo Operator",
        staff_count=1,
        certifications=frozenset(),
        insurance_cover_eur=None,
        corporate_references=(),
        languages=frozenset({"ENG"}),
    )


def _real_profile():
    return OperatorProfile(
        name="Real Cairns Security Solo Trader",
        staff_count=1,
        certifications=frozenset({"OSCP"}),
        insurance_cover_eur=None,
        corporate_references=(),
        languages=frozenset({"ENG"}),
    )


class TestBusinessFactsAndReferee(unittest.TestCase):
    def test_default_business_facts_all_absent(self):
        f = BusinessFacts()
        self.assertIsNone(f.abn)
        self.assertIsNone(f.acn)
        self.assertEqual(f.skills, ())
        self.assertEqual(f.referees, ())

    def test_referee_requires_all_fields_non_blank(self):
        with self.assertRaises(ValueError):
            Referee(name="", organisation="Acme", contact="a@acme.com")
        with self.assertRaises(ValueError):
            Referee(name="Jane", organisation="  ", contact="a@acme.com")

    def test_referees_must_be_referee_instances(self):
        with self.assertRaises(ValueError):
            BusinessFacts(referees=("just a string",))

    def test_negative_experience_rejected(self):
        with self.assertRaises(ValueError):
            BusinessFacts(years_experience=-1)

    def test_negative_insurance_rejected(self):
        with self.assertRaises(ValueError):
            BusinessFacts(insurance_pi_cover_aud=-1.0)
        with self.assertRaises(ValueError):
            BusinessFacts(insurance_pl_cover_aud=-1.0)


class TestSupplierDossierConstruction(unittest.TestCase):
    def test_requires_operator_profile(self):
        with self.assertRaises(ValueError):
            SupplierDossier(profile="not a profile")

    def test_requires_business_facts_type(self):
        with self.assertRaises(ValueError):
            SupplierDossier(profile=_empty_profile(), facts="not facts")

    def test_default_facts_is_empty_business_facts(self):
        d = SupplierDossier(profile=_empty_profile())
        self.assertEqual(d.facts.skills, ())


class TestAbsoluteRuleNoFabrication(unittest.TestCase):
    """The whole safety property of this module: an empty profile must
    never produce a plausible-looking invented value anywhere in the
    rendered output."""

    def setUp(self):
        self.dossier = SupplierDossier(profile=_empty_profile())
        self.output = render_dossier(self.dossier)

    def test_abn_renders_literal_unknown_marker(self):
        # ABN section must contain the literal marker, never a digit
        # string standing in for a real ABN.
        m = re.search(r"^- ABN: (.+)$", self.output, re.MULTILINE)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), UNKNOWN_MARKER)

    def test_acn_renders_literal_unknown_marker(self):
        m = re.search(r"^- ACN: (.+)$", self.output, re.MULTILINE)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), UNKNOWN_MARKER)

    def test_no_plausible_abn_digit_sequence_anywhere(self):
        # An ABN is 11 digits, an ACN is 9 digits. Nothing in the
        # rendered output -- with an empty profile -- should contain a
        # bare 9- or 11-digit run, which is the shape a fabricated
        # ABN/ACN would take.
        digit_runs = re.findall(r"\d{9,}", self.output)
        self.assertEqual(digit_runs, [])

    def test_no_invented_insurance_figures(self):
        self.assertNotIn("$", self.output)
        # No dollar-formatted figure (e.g. "1,000,000.00") anywhere.
        self.assertNotRegex(self.output, r"\d[\d,]*\.\d{2}")

    def test_no_invented_referees(self):
        self.assertIn(f"No referees declared. {UNKNOWN_MARKER}", self.output)
        # No referee line (the "- Name (Org) — contact" shape) exists.
        self.assertNotRegex(self.output, r"^- .+\(.+\) — .+$", )

    def test_no_invented_certifications_or_licence_numbers(self):
        self.assertIn(f"- Licence number: {UNKNOWN_MARKER}", self.output)
        self.assertIn(f"- Registration number: {UNKNOWN_MARKER}", self.output)
        # No certification name appears anywhere -- the capability
        # statement short-circuits to the honest "nothing declared"
        # line rather than listing a fabricated certification.
        self.assertIn(
            "No skills, certifications, or years of experience have "
            f"been declared. {UNKNOWN_MARKER}", self.output)

    def test_no_invented_years_of_experience(self):
        # With nothing declared at all, the capability statement
        # short-circuits to one honest line rather than a field-by-
        # field breakdown that could imply a fabricated "0 years".
        self.assertIn(
            "No skills, certifications, or years of experience have "
            f"been declared. {UNKNOWN_MARKER}", self.output)
        self.assertNotRegex(self.output, r"Years of relevant experience: \d")

    def test_every_unknown_marker_is_the_literal_string(self):
        # Every occurrence of the word UNKNOWN in the output must be
        # exactly the sanctioned marker string, never a fragment mixed
        # with a fabricated value.
        for line in self.output.splitlines():
            if "UNKNOWN" in line:
                self.assertIn(UNKNOWN_MARKER, line)


class TestDraftStampEverywhere(unittest.TestCase):
    def test_every_section_carries_draft_stamp(self):
        d = SupplierDossier(profile=_empty_profile())
        output = render_dossier(d)
        # Six numbered sections (1-6) plus the top banner and the
        # missing-facts checklist (7) all carry the stamp.
        self.assertGreaterEqual(output.count(DRAFT_STAMP), 7)

    def test_render_dossier_rejects_non_dossier(self):
        with self.assertRaises(ValueError):
            render_dossier("not a dossier")

    def test_output_states_it_is_not_a_submission(self):
        d = SupplierDossier(profile=_empty_profile())
        output = render_dossier(d)
        self.assertIn("not a submission", output)


class TestGenuineFactsRenderHonestly(unittest.TestCase):
    """The other half of the property: real, supplied facts DO appear
    verbatim -- this module is not merely a stub that always prints
    UNKNOWN regardless of input."""

    def test_supplied_abn_appears_verbatim(self):
        facts = BusinessFacts(abn="51 824 753 556")
        d = SupplierDossier(profile=_empty_profile(), facts=facts)
        output = render_dossier(d)
        self.assertIn("51 824 753 556", output)
        self.assertNotIn(f"- ABN: {UNKNOWN_MARKER}", output)

    def test_supplied_referee_appears_verbatim(self):
        ref = Referee(name="Jane Smith", organisation="Acme Pty Ltd",
                       contact="jane@acme.com.au")
        facts = BusinessFacts(referees=(ref,))
        d = SupplierDossier(profile=_empty_profile(), facts=facts)
        output = render_dossier(d)
        self.assertIn("Jane Smith (Acme Pty Ltd) — jane@acme.com.au", output)

    def test_supplied_insurance_figures_appear(self):
        facts = BusinessFacts(insurance_pi_cover_aud=1_000_000.0,
                               insurance_pl_cover_aud=5_000_000.0)
        d = SupplierDossier(profile=_empty_profile(), facts=facts)
        output = render_dossier(d)
        self.assertIn("1,000,000.00", output)
        self.assertIn("5,000,000.00", output)

    def test_certifications_from_operator_profile_appear(self):
        d = SupplierDossier(profile=_real_profile())
        output = render_dossier(d)
        self.assertIn("OSCP", output)


class TestCategoryMapping(unittest.TestCase):
    def test_no_skills_gives_unknown_category(self):
        d = SupplierDossier(profile=_empty_profile())
        output = render_dossier(d)
        self.assertIn(
            f"No declared skill matched a Category K label. "
            f"{UNKNOWN_MARKER}", output)

    def test_penetration_testing_skill_maps_to_k03(self):
        facts = BusinessFacts(skills=("penetration testing",))
        d = SupplierDossier(profile=_empty_profile(), facts=facts)
        output = render_dossier(d)
        self.assertIn("K03: Security testing", output)

    def test_unrelated_skill_does_not_map(self):
        facts = BusinessFacts(skills=("graphic design",))
        d = SupplierDossier(profile=_empty_profile(), facts=facts)
        output = render_dossier(d)
        self.assertNotIn("K01:", output)
        self.assertNotIn("K02:", output)
        self.assertNotIn("K03:", output)
        self.assertNotIn("K04:", output)


class TestMissingFactsChecklist(unittest.TestCase):
    def test_unknown_scheme_rejected(self):
        d = SupplierDossier(profile=_empty_profile())
        with self.assertRaises(ValueError):
            missing_facts_for_scheme(d, "NOT_A_REAL_SCHEME")

    def test_empty_dossier_flags_nsw_abn_and_referees(self):
        d = SupplierDossier(profile=_empty_profile())
        missing = missing_facts_for_scheme(d, "NSW_ICT_SERVICES_SCHEME")
        facts_missing = {m.fact for m in missing}
        self.assertIn("ABN", facts_missing)
        self.assertIn("two referee reports", facts_missing)

    def test_supplying_abn_removes_it_from_nsw_missing_list(self):
        facts = BusinessFacts(abn="51 824 753 556")
        d = SupplierDossier(profile=_empty_profile(), facts=facts)
        missing = missing_facts_for_scheme(d, "NSW_ICT_SERVICES_SCHEME")
        self.assertNotIn("ABN", {m.fact for m in missing})

    def test_two_referees_removes_referee_requirement(self):
        refs = (
            Referee("Jane Smith", "Acme Pty Ltd", "jane@acme.com.au"),
            Referee("John Doe", "Beta Pty Ltd", "john@beta.com.au"),
        )
        facts = BusinessFacts(abn="51 824 753 556", skills=("penetration testing",),
                               referees=refs)
        d = SupplierDossier(profile=_empty_profile(), facts=facts)
        missing = missing_facts_for_scheme(d, "NSW_ICT_SERVICES_SCHEME")
        self.assertNotIn("two referee reports", {m.fact for m in missing})

    def test_all_four_schemes_return_missing_facts_for_empty_dossier(self):
        d = SupplierDossier(profile=_empty_profile())
        for scheme in SCHEMES:
            missing = missing_facts_for_scheme(d, scheme)
            self.assertIsInstance(missing, tuple)
            self.assertGreater(len(missing), 0)
            for m in missing:
                self.assertIsInstance(m, MissingFact)
                self.assertEqual(m.scheme, scheme)

    def test_missing_fact_rejects_unknown_scheme(self):
        with self.assertRaises(ValueError):
            MissingFact(scheme="NOT_REAL", fact="x", why_needed="y")

    def test_dossier_missing_checklist_section_present_in_render(self):
        d = SupplierDossier(profile=_empty_profile())
        output = render_dossier(d)
        self.assertIn(
            "Facts still missing before submission, by scheme", output)
        for scheme in SCHEMES:
            self.assertIn(scheme, output)


class TestSelfDeclaredDeclarationsNeverAutoAffirmed(unittest.TestCase):
    def test_declarations_render_as_checkboxes_not_statements(self):
        d = SupplierDossier(profile=_empty_profile())
        output = render_dossier(d)
        self.assertIn("- [ ] Confirm financially solvent", output)
        self.assertIn("- [ ] Supplier Declaration", output)
        # Never a bare affirmative statement standing alone as fact.
        self.assertNotIn("Operator confirms it is financially solvent.",
                          output)


if __name__ == "__main__":
    unittest.main()
