import unittest

from foundation import eligibility
from foundation.eligibility import (
    CodedRequirement, EligibilityAssessment, assess_eligibility, format_report,
)


def _degewo_notice():
    """A REDACTED-free, structurally real notice -- trimmed and
    slightly abbreviated from the live TED response for
    publication-number 578580-2026 (degewo AG, Berlin, "Rahmenvertrag
    Penetrationstests"), fetched 2026-09-02 via
    POST https://api.ted.europa.eu/v3/notices/search with this
    module's own FIELDS list. Shapes (bare string for procedure-type,
    {lang: str} for buyer-name, {lang: [str, ...]} for description
    fields, list-of-strings for selection-criterion-lot) are the real,
    unaltered shapes observed live -- not invented. Text content is the
    real (public, CC BY 4.0) notice text, unabridged for the exclusion
    grounds description and abbreviated with "..." for the longer
    selection-criteria description to keep this fixture readable."""
    return {
        "publication-number": "578580-2026",
        "notice-title": {"deu": "Rahmenvertrag Penetrationstests"},
        "buyer-name": {"deu": ["degewo AG"]},
        "links": {
            "html": {
                "ENG": "https://ted.europa.eu/en/notice/-/detail/578580-2026",
                "DEU": "https://ted.europa.eu/de/notice/-/detail/578580-2026",
            },
        },
        "document-url-lot": [
            "https://www.meinauftrag.rib.de/public/DetailsByPlatformIdAndTenderId/"
            "platformId/2/tenderId/208727",
        ],
        "procedure-type": "open",
        "submission-language": ["DEU"],
        "official-language": ["DEU"],
        "document-official-language-lot": ["DEU"],
        "selection-criterion-lot": [
            "slc-suit-reg-prof", "slc-stand-other",
            "slc-abil-ref-services", "slc-abil-staff-yrly-avg-mp",
        ],
        "selection-criterion-description-lot": {
            "deu": [
                "Folgende Angaben sind in dem von der Vergabestelle vorgegebenen "
                "Bieterbogen incl. Anlagen zu machen... Betriebshaftpflichtversicherung "
                "- Das anbietende Unternehmen hat den Nachweis ueber das Bestehen einer "
                "gueltigen Betriebshaftpflichtversicherung vorzulegen mit einer mind. "
                "Deckungssumme von 3 Mio. EUR.",
                "Der Auftraggeber behaelt sich vor, vor Zuschlagserteilung eine "
                "Bankerklaerung zu fordern.",
                "(1) Erfolgreich beendete Vertragsverhaeltnisse... mindestens zwei (2) "
                "vergleichbare Referenzen aus den letzten fuenf (5) Jahren nachzuweisen. "
                "Mindestauftragsvolumen von 50.000 EUR.",
                "Mindeststandard: Mindestens 3 Penetrationstester, mindestens 1 Projektmanager.",
            ],
        },
        "selection-criteria-source": ["epo-notice", "epo-procurement-document"],
        "exclusion-grounds": ["exg-natl-bre-nat-law"],
        "exclusion-grounds-description": {
            "deu": [
                "Es gelten die gesetzlichen Ausschlussvoraussetzungen nach "
                "Paragrafen 123 bis 126 GWB.",
            ],
        },
        "exclusion-grounds-source-proc": ["epo-notice", "epo-procurement-document"],
        "tenderer-legal-form-lot": ["true"],
        "tenderer-legal-form-description-lot": {
            "deu": [
                "Eine Bietergemeinschaft hat mit ihrem Angebot eine Erklaerung aller "
                "Mitglieder in Textform abzugeben.",
            ],
        },
        "variant-allowed-lot": ["not-allowed"],
        "place-of-performance-country-lot": ["DEU"],
        "place-of-performance-city-lot": ["Berlin"],
        "place-of-performance-post-code-lot": ["10785"],
        "place-of-performance-subdiv-lot": ["DE300"],
    }


def _rotterdam_notice():
    """Real shape for publication-number 305025-2026 (Gemeente
    Rotterdam, "Pentesten"), fetched live 2026-09-02 -- deliberately
    the case where `selection-criteria-source` names ONLY
    `epo-procurement-document`, and `selection-criterion-lot` /
    `selection-criterion-description-lot` are BOTH absent from the
    search projection (confirmed live: these keys are simply not
    present in the API response for this notice, even though they were
    requested), forcing a caller to the linked procurement documents
    for the actual criteria text. This fixture exists to pin that
    genuinely-UNKNOWN case, not to fabricate criteria TED did not
    return."""
    return {
        "publication-number": "305025-2026",
        "buyer-name": {"nld": ["Gemeente Rotterdam"]},
        "document-url-lot": ["https://s2c.mercell.com/today/209787"],
        "procedure-type": "open",
        "submission-language": ["NLD"],
        "official-language": ["NLD"],
        "selection-criteria-source": ["epo-procurement-document"],
        "exclusion-grounds-source-proc": ["epo-sub-espd"],
        "place-of-performance-country-lot": ["NLD"],
    }


class AssessEligibilityTests(unittest.TestCase):
    def test_requires_a_usable_publication_number(self):
        with self.assertRaises(ValueError):
            assess_eligibility({})
        with self.assertRaises(ValueError):
            assess_eligibility({"publication-number": "  "})
        with self.assertRaises(ValueError):
            assess_eligibility("not-a-dict")  # type: ignore[arg-type]

    def test_degewo_notice_full_extraction(self):
        a = assess_eligibility(_degewo_notice())
        self.assertIsInstance(a, EligibilityAssessment)
        self.assertEqual(a.publication_number, "578580-2026")
        self.assertEqual(a.notice_url, "https://ted.europa.eu/en/notice/-/detail/578580-2026")
        self.assertEqual(
            a.procurement_documents_urls,
            ("https://www.meinauftrag.rib.de/public/DetailsByPlatformIdAndTenderId/"
             "platformId/2/tenderId/208727",),
        )
        self.assertEqual(a.procedure_type_code, "open")
        self.assertEqual(a.procedure_type_label, "Open")
        self.assertEqual(a.submission_languages, ("DEU",))

    def test_selection_criteria_used_is_deduplicated_and_labelled(self):
        a = assess_eligibility(_degewo_notice())
        codes = {r.code for r in a.selection_criteria_used}
        self.assertEqual(
            codes,
            {"slc-suit-reg-prof", "slc-stand-other",
             "slc-abil-ref-services", "slc-abil-staff-yrly-avg-mp"},
        )
        by_code = {r.code: r.label for r in a.selection_criteria_used}
        self.assertEqual(by_code["slc-abil-ref-services"], "References on specified services")
        self.assertEqual(by_code["slc-stand-other"], "Other economic or financial requirements")
        # raw codes preserve the original, non-deduplicated, per-lot order
        self.assertEqual(len(a.selection_criteria_raw_codes), 4)

    def test_criteria_categorisation_is_structural_not_guessed(self):
        a = assess_eligibility(_degewo_notice())
        self.assertEqual({r.code for r in a.economic_financial_criteria}, {"slc-stand-other"})
        self.assertEqual(
            {r.code for r in a.technical_professional_criteria},
            {"slc-abil-ref-services", "slc-abil-staff-yrly-avg-mp"},
        )
        self.assertEqual({r.code for r in a.suitability_criteria}, {"slc-suit-reg-prof"})
        # No certification-specific code (slc-sche-*, slc-abil-qual-inst) was
        # present on this notice -- an explicit empty tuple, not None, because
        # the source field (selection-criterion-lot) WAS present.
        self.assertEqual(a.certification_criteria, ())

    def test_selection_criteria_description_text_is_not_falsely_aligned(self):
        a = assess_eligibility(_degewo_notice())
        # Four raw paragraphs, four codes -- coincidentally equal count on
        # this real notice, but assess_eligibility() must never claim a
        # pairing between them; the API exposes both fields independently.
        self.assertIn("deu", a.selection_criteria_description_text)
        self.assertEqual(len(a.selection_criteria_description_text["deu"]), 4)
        self.assertIn("3 Mio. EUR", a.selection_criteria_description_text["deu"][0])

    def test_exclusion_grounds(self):
        a = assess_eligibility(_degewo_notice())
        self.assertEqual(
            a.exclusion_grounds_used,
            (CodedRequirement(
                code="exg-natl-bre-nat-law",
                label="Breaching of obligations set under purely national exclusion grounds",
            ),),
        )
        self.assertIn("GWB", a.exclusion_grounds_description_text["deu"][0])

    def test_legal_form_and_consortium_text_preserved_verbatim(self):
        a = assess_eligibility(_degewo_notice())
        self.assertEqual(a.legal_form_required_raw, ("true",))
        self.assertIn("Bietergemeinschaft", a.legal_form_description_text["deu"][0])
        # This notice never populated tendering-party-leader/-name -- UNKNOWN.
        self.assertIsNone(a.tendering_party_leader_raw)
        self.assertIsNone(a.tendering_party_name_raw)

    def test_variants_and_place_of_performance(self):
        a = assess_eligibility(_degewo_notice())
        self.assertEqual(a.variant_allowed_raw, ("not-allowed",))
        self.assertEqual(a.place_of_performance_country, ("DEU",))
        self.assertEqual(a.place_of_performance_city, ("Berlin",))

    def test_subcontracting_wholly_absent_is_none_not_empty(self):
        a = assess_eligibility(_degewo_notice())
        self.assertIsNone(a.subcontracting_allowed_raw)
        self.assertIsNone(a.subcontracting_obligation_raw)
        self.assertIsNone(a.subcontracting_description_text)

    def test_absent_fields_names_every_missing_requested_field(self):
        a = assess_eligibility(_degewo_notice())
        self.assertIn("subcontracting-allowed-lot", a.absent_fields)
        self.assertIn("tendering-party-leader", a.absent_fields)
        self.assertNotIn("selection-criterion-lot", a.absent_fields)
        self.assertNotIn("publication-number", a.absent_fields)  # not in FIELDS at all is fine
        # Every absent field really is absent from the notice.
        notice = _degewo_notice()
        for f in a.absent_fields:
            self.assertTrue(
                f not in notice or notice[f] in (None, "", [], {}),
                f"{f} claimed absent but notice has {notice.get(f)!r}",
            )

    def test_rotterdam_notice_criteria_are_unknown_not_empty(self):
        """The load-bearing case: TED's own selection-criteria-source
        says the real criteria live only in the procurement documents,
        and the search projection genuinely returned nothing for
        selection-criterion-lot. This must surface as UNKNOWN (None),
        never as an empty tuple that could be misread as 'no criteria
        apply'."""
        a = assess_eligibility(_rotterdam_notice())
        self.assertIsNone(a.selection_criteria_used)
        self.assertIsNone(a.selection_criteria_raw_codes)
        self.assertIsNone(a.selection_criteria_description_text)
        self.assertEqual(
            a.selection_criteria_source,
            (CodedRequirement(code="epo-procurement-document", label="Procurement Document"),),
        )
        self.assertIn("selection-criterion-lot", a.absent_fields)
        # No notice-page link was supplied in this fixture (links omitted) --
        # notice_url must be None, not a fabricated fallback URL.
        self.assertIsNone(a.notice_url)
        self.assertEqual(
            a.procurement_documents_urls, ("https://s2c.mercell.com/today/209787",),
        )

    def test_unrecognised_codelist_code_keeps_raw_code_with_none_label(self):
        notice = _degewo_notice()
        notice["selection-criterion-lot"] = ["slc-totally-new-future-code"]
        a = assess_eligibility(notice)
        self.assertEqual(len(a.selection_criteria_used), 1)
        self.assertEqual(a.selection_criteria_used[0].code, "slc-totally-new-future-code")
        self.assertIsNone(a.selection_criteria_used[0].label)

    def test_procedure_type_as_bare_string_not_a_list(self):
        # Real TED shape: procedure-type is a bare string, not a list.
        notice = _degewo_notice()
        self.assertIsInstance(notice["procedure-type"], str)
        a = assess_eligibility(notice)
        self.assertEqual(a.procedure_type_code, "open")

    def test_malformed_field_types_do_not_crash(self):
        notice = _degewo_notice()
        notice["submission-language"] = {"unexpected": "dict-not-list"}
        notice["selection-criterion-lot"] = [1, 2, None, "slc-stand-other"]
        a = assess_eligibility(notice)
        self.assertIsNone(a.submission_languages)
        self.assertEqual({r.code for r in a.selection_criteria_used}, {"slc-stand-other"})


class FormatReportTests(unittest.TestCase):
    def test_report_contains_no_verdict_language(self):
        a = assess_eligibility(_degewo_notice())
        report = format_report(a)
        for banned in ("can bid", "cannot bid", "eligible", "ineligible", "you should"):
            self.assertNotIn(banned, report.lower())

    def test_report_marks_unknown_fields_explicitly(self):
        a = assess_eligibility(_rotterdam_notice())
        report = format_report(a)
        self.assertIn("UNKNOWN (not stated in notice)", report)
        self.assertIn("305025-2026", report)

    def test_report_is_a_nonempty_string_for_a_full_notice(self):
        a = assess_eligibility(_degewo_notice())
        report = format_report(a)
        self.assertIsInstance(report, str)
        self.assertIn("578580-2026", report)
        self.assertIn("SELECTION CRITERIA", report)
        self.assertIn("EXCLUSION GROUNDS", report)


class CodelistIntegrityTests(unittest.TestCase):
    def test_selection_criterion_labels_cover_every_code_used_live(self):
        # Every code observed live across all eleven notices this cycle
        # examined must resolve to a real label -- a regression here means
        # this module's static snapshot has drifted from what TED actually
        # emits.
        observed_codes = {
            "slc-suit-reg-prof", "slc-stand-other", "slc-abil-ref-services",
            "slc-abil-staff-yrly-avg-mp", "slc-suit-reg-trade", "slc-abil-staff-qual",
            "slc-abil-subc", "slc-abil-mgmt-supply", "slc-sec-inf", "slc-stand-ins",
            "slc-stand-to-spec", "slc-abil-mgmt-qual", "slc-abil-facil-tools",
            "slc-stand-to-gen", "slc-abil-qual-inst", "slc-abil-staff-tech-work",
            "slc-sche-qu-cert-indep",
        }
        for code in observed_codes:
            self.assertIn(code, eligibility.SELECTION_CRITERION_LABELS)

    def test_exclusion_ground_labels_cover_every_code_used_live(self):
        observed_codes = {
            "exg-natl-bre-nat-law", "exg-mis-sanction", "exg-crim-part",
            "exg-crim-terror", "exg-crim-laund", "exg-crim-fraud", "exg-crim-corrpt",
            "exg-crim-traffick", "exg-pmt-bre-tax", "exg-pmt-bre-ssc",
            "exg-mis-bre-env-law", "exg-mis-bre-soc-law", "exg-mis-bre-lab-law",
            "exg-sitn-insolvency", "exg-sitn-liq-admin", "exg-sitn-as-susp",
            "exg-sitn-other", "exg-mis-misconduct", "exg-mis-distortion",
            "exg-mis-partic-confl", "exg-mis-prep-confl", "exg-mis-misrepresent",
        }
        for code in observed_codes:
            self.assertIn(code, eligibility.EXCLUSION_GROUND_LABELS)

    def test_procedure_type_labels_cover_every_code_used_live(self):
        for code in ("open", "neg-w-call"):
            self.assertIn(code, eligibility.PROCEDURE_TYPE_LABELS)

    def test_fields_constant_matches_what_assess_eligibility_reads(self):
        # Every field name assess_eligibility() calls notice.get(...) with
        # must be listed in FIELDS, so a caller building a request from
        # FIELDS gets a complete notice.
        import inspect
        source = inspect.getsource(eligibility.assess_eligibility)
        for field_name in eligibility.FIELDS:
            self.assertIn(f'"{field_name}"', source)


if __name__ == "__main__":
    unittest.main()
