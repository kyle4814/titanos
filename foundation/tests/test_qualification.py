import unittest

from foundation import qualification
from foundation.eligibility import assess_eligibility
from foundation.qualification import (
    BANDS, DIMENSIONS,
    OperatorProfile, QualificationFactor, QualificationIntegrityError,
    QualificationResult, assess, format_result,
)


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

def _real_operator_profile():
    """The REAL, confirmed-today operator profile this module was built
    to model: a solo Australian trader with no certifications, no
    liability insurance, no evidenced corporate reference contracts,
    and English only."""
    return OperatorProfile(
        name="Real Operator (solo trader, AU)",
        staff_count=1,
        certifications=frozenset(),
        insurance_cover_eur=None,
        corporate_references=(),
        languages=frozenset({"ENG"}),
    )


def _degewo_notice():
    """Trimmed and slightly abbreviated from the live TED response for
    publication-number 578580-2026 (degewo AG, Berlin, "Rahmenvertrag
    Penetrationstests") -- same fixture shape as
    `foundation/tests/test_eligibility.py::_degewo_notice()`, kept
    independent per this module's file-territory rule (this file may
    not import that module's private fixture function). Real, public
    (CC BY 4.0) notice text: at least 3 penetration testers, at least 2
    comparable reference contracts of >= EUR 50,000 each, a EUR
    3,000,000 professional-indemnity-insurance minimum, submission in
    German."""
    return {
        "publication-number": "578580-2026",
        "notice-title": {"deu": "Rahmenvertrag Penetrationstests"},
        "buyer-name": {"deu": ["degewo AG"]},
        "procedure-type": "open",
        "submission-language": ["DEU"],
        "official-language": ["DEU"],
        "selection-criterion-lot": [
            "slc-suit-reg-prof", "slc-stand-other",
            "slc-abil-ref-services", "slc-abil-staff-yrly-avg-mp",
        ],
        "selection-criterion-description-lot": {
            "deu": [
                "Betriebshaftpflichtversicherung - Das anbietende "
                "Unternehmen hat den Nachweis ueber das Bestehen einer "
                "gueltigen Betriebshaftpflichtversicherung vorzulegen mit "
                "einer mind. Deckungssumme von 3 Mio. EUR.",
                "(1) Erfolgreich beendete Vertragsverhaeltnisse... "
                "mindestens zwei (2) vergleichbare Referenzen aus den "
                "letzten fuenf (5) Jahren nachzuweisen. "
                "Mindestauftragsvolumen von 50.000 EUR.",
                "Mindeststandard: Mindestens 3 Penetrationstester, "
                "mindestens 1 Projektmanager.",
            ],
        },
        "selection-criteria-source": ["epo-notice", "epo-procurement-document"],
    }


def _notice_with_no_criteria():
    """A minimal, real-shaped notice dict where TED simply did not
    return any selection-criterion/language fields at all -- the
    genuine UNKNOWN case, not a notice that states 'no requirements'."""
    return {
        "publication-number": "999999-2026",
        "buyer-name": {"eng": ["Example Buyer"]},
    }


def _notice_with_empty_criteria():
    """A notice where selection-criterion-lot IS present (so the
    category fields come back as real, present-but-empty tuples, not
    None) but every code present is a suitability code -- none of it
    falls into economic/technical/certification categories -- and
    submission language is English, matching the operator. Used to
    prove QUALIFIED is a reachable band, not merely a name."""
    return {
        "publication-number": "111111-2026",
        "buyer-name": {"eng": ["Example Buyer 2"]},
        "submission-language": ["ENG"],
        "selection-criterion-lot": ["slc-suit-reg-trade"],
        "selection-criterion-description-lot": {
            "eng": ["Enrolment in a trade register is required."],
        },
    }


# ---------------------------------------------------------------------
# OperatorProfile validation
# ---------------------------------------------------------------------

class OperatorProfileTests(unittest.TestCase):
    def test_valid_profile_constructs(self):
        p = _real_operator_profile()
        self.assertEqual(p.staff_count, 1)
        self.assertEqual(p.certifications, frozenset())
        self.assertIsNone(p.insurance_cover_eur)
        self.assertEqual(p.corporate_references, ())
        self.assertEqual(p.languages, frozenset({"ENG"}))

    def test_rejects_empty_name(self):
        with self.assertRaises(QualificationIntegrityError):
            OperatorProfile(name="  ", staff_count=1, languages=frozenset({"ENG"}))

    def test_rejects_negative_staff_count(self):
        with self.assertRaises(QualificationIntegrityError):
            OperatorProfile(name="X", staff_count=-1, languages=frozenset({"ENG"}))

    def test_rejects_empty_languages(self):
        with self.assertRaises(QualificationIntegrityError):
            OperatorProfile(name="X", staff_count=1, languages=frozenset())

    def test_rejects_negative_insurance(self):
        with self.assertRaises(QualificationIntegrityError):
            OperatorProfile(name="X", staff_count=1, languages=frozenset({"ENG"}),
                             insurance_cover_eur=-1.0)

    def test_normalises_case(self):
        p = OperatorProfile(name="X", staff_count=1,
                             certifications=frozenset({"oscp"}),
                             languages=frozenset({"eng"}))
        self.assertEqual(p.certifications, frozenset({"OSCP"}))
        self.assertEqual(p.languages, frozenset({"ENG"}))


# ---------------------------------------------------------------------
# QualificationFactor validation
# ---------------------------------------------------------------------

class QualificationFactorTests(unittest.TestCase):
    def test_unknown_dimension_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationFactor("not_a_real_dimension", "KNOWN", "NOT_BARRIER", "evidence")

    def test_unknown_status_with_non_info_verdict_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationFactor("insurance", "UNKNOWN", "BARRIER", "evidence")

    def test_barrier_requires_known_status(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationFactor("insurance", "UNKNOWN", "BARRIER", "evidence")

    def test_empty_evidence_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationFactor("insurance", "KNOWN", "NOT_BARRIER", "   ")

    def test_valid_factor_constructs(self):
        f = QualificationFactor("insurance", "KNOWN", "NOT_BARRIER", "no requirement found")
        self.assertEqual(f.dimension, "insurance")


# ---------------------------------------------------------------------
# QualificationResult structural validation (the two-independent-points
# enforcement of the CRITICAL SEMANTICS invariant)
# ---------------------------------------------------------------------

def _all_clear_factors():
    return tuple(
        QualificationFactor(d, "KNOWN", "NOT_BARRIER", f"{d}: nothing found")
        for d in DIMENSIONS
    )


class QualificationResultTests(unittest.TestCase):
    def test_unknown_band_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "MAYBE", _all_clear_factors())

    def test_incomplete_dimension_coverage_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "QUALIFIED", _all_clear_factors()[:-1])

    def test_qualified_with_barrier_factor_rejected(self):
        factors = list(_all_clear_factors())
        factors[0] = QualificationFactor(DIMENSIONS[0], "KNOWN", "BARRIER", "fails")
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "QUALIFIED", tuple(factors))

    def test_qualified_with_unresolved_factor_rejected(self):
        factors = list(_all_clear_factors())
        factors[0] = QualificationFactor(DIMENSIONS[0], "UNKNOWN", "INFO", "unknown")
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "QUALIFIED", tuple(factors))

    def test_disqualified_without_any_barrier_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "DISQUALIFIED", _all_clear_factors())

    def test_disqualified_without_blocking_clauses_rejected(self):
        factors = list(_all_clear_factors())
        factors[0] = QualificationFactor(DIMENSIONS[0], "KNOWN", "BARRIER", "fails")
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "DISQUALIFIED", tuple(factors), blocking_clauses=())

    def test_blocking_clause_must_match_a_barrier_evidence(self):
        factors = list(_all_clear_factors())
        factors[0] = QualificationFactor(DIMENSIONS[0], "KNOWN", "BARRIER", "the real evidence")
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "DISQUALIFIED", tuple(factors),
                                 blocking_clauses=("a fabricated unrelated string",))

    def test_insufficient_data_without_unresolved_factor_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "INSUFFICIENT_DATA", _all_clear_factors())

    def test_non_disqualified_with_blocking_clauses_rejected(self):
        with self.assertRaises(QualificationIntegrityError):
            QualificationResult("pub", "op", "QUALIFIED", _all_clear_factors(),
                                 blocking_clauses=("something",))

    def test_valid_qualified_result_constructs(self):
        r = QualificationResult("pub", "op", "QUALIFIED", _all_clear_factors())
        self.assertEqual(r.band, "QUALIFIED")
        self.assertEqual(r.blocking_clauses, ())

    def test_factor_lookup(self):
        r = QualificationResult("pub", "op", "QUALIFIED", _all_clear_factors())
        self.assertEqual(r.factor(DIMENSIONS[0]).dimension, DIMENSIONS[0])


# ---------------------------------------------------------------------
# assess() -- the actual behaviour that matters
# ---------------------------------------------------------------------

class AssessTests(unittest.TestCase):
    def test_rejects_wrong_types(self):
        profile = _real_operator_profile()
        with self.assertRaises(QualificationIntegrityError):
            assess("not an assessment", profile)
        elig = assess_eligibility(_notice_with_no_criteria())
        with self.assertRaises(QualificationIntegrityError):
            assess(elig, "not a profile")

    def test_no_published_criteria_is_insufficient_data_never_qualified(self):
        """THE load-bearing test: a notice TED returned almost nothing
        for must never be scored QUALIFIED. Absence of data is not
        evidence of a satisfied requirement."""
        elig = assess_eligibility(_notice_with_no_criteria())
        profile = _real_operator_profile()
        result = assess(elig, profile)
        self.assertEqual(result.band, "INSUFFICIENT_DATA")
        self.assertNotEqual(result.band, "QUALIFIED")
        self.assertEqual(result.blocking_clauses, ())
        for f in result.factors:
            self.assertEqual(f.status, "UNKNOWN")
            self.assertEqual(f.verdict, "INFO")

    def test_degewo_578580_2026_is_disqualified_with_quoted_clauses(self):
        """The real notice this module was built against. The confirmed
        real operator profile (no certs, no insurance, zero evidenced
        corporate references, English only, solo trader) must come out
        DISQUALIFIED, with the specific quoted clauses that produced it."""
        elig = assess_eligibility(_degewo_notice())
        profile = _real_operator_profile()
        result = assess(elig, profile)

        self.assertEqual(result.band, "DISQUALIFIED")
        self.assertGreaterEqual(len(result.blocking_clauses), 1)

        # References: dedicated slc-abil-ref-services code present,
        # operator has zero evidenced corporate references -> a clean,
        # positively-identified BARRIER (not an inference from silence).
        ref_factor = result.factor("corporate_references")
        self.assertEqual(ref_factor.verdict, "BARRIER")
        self.assertIn("slc-abil-ref-services", ref_factor.evidence)
        self.assertIn("50.000 EUR", ref_factor.evidence)
        self.assertIn(ref_factor.evidence, result.blocking_clauses)

        # Language: submission-language is DEU only, operator speaks
        # English only -> a clean, structural BARRIER.
        lang_factor = result.factor("submission_language")
        self.assertEqual(lang_factor.verdict, "BARRIER")
        self.assertIn("DEU", lang_factor.evidence)
        self.assertIn(lang_factor.evidence, result.blocking_clauses)

        # Insurance: the real EUR 3,000,000 requirement is coded
        # slc-stand-other (TED's generic bucket), not the dedicated
        # slc-stand-ins code -- this module honestly reports INFO
        # (unresolved, quoted for a human), never a false NOT_BARRIER
        # clearance and never a guessed BARRIER from an ambiguous code.
        insurance_factor = result.factor("insurance")
        self.assertEqual(insurance_factor.verdict, "INFO")
        self.assertIn("3 Mio. EUR", insurance_factor.evidence)

        # Staff: the "at least 3 penetration testers" figure lives only
        # in free text under a generic manpower code -- reported as
        # INFO with the real quoted number, never auto-derived into a
        # BARRIER this module didn't actually verify structurally.
        staff_factor = result.factor("technical_staff_capacity")
        self.assertEqual(staff_factor.verdict, "INFO")
        self.assertIn("Penetrationstester", staff_factor.evidence)

        # certifications: no dedicated certification code was among the
        # stated criteria for this notice.
        cert_factor = result.factor("certifications")
        self.assertEqual(cert_factor.verdict, "NOT_BARRIER")

        # format_result() must not raise and must surface the blocking
        # clauses to a human.
        report = format_result(result)
        self.assertIn("DISQUALIFIED", report)
        self.assertIn("BLOCKING CLAUSE", report)

    def test_clean_notice_with_no_barriers_and_no_unknowns_is_qualified(self):
        """Proves QUALIFIED is reachable, not just a name in BANDS: a
        notice whose criteria fields were all actually returned by TED,
        contain nothing this operator fails, and a submission language
        the operator speaks."""
        elig = assess_eligibility(_notice_with_empty_criteria())
        profile = _real_operator_profile()
        result = assess(elig, profile)
        self.assertEqual(result.band, "QUALIFIED")
        self.assertEqual(result.blocking_clauses, ())
        for f in result.factors:
            self.assertEqual(f.status, "KNOWN")
            self.assertIn(f.verdict, ("NOT_BARRIER",))

    def test_bands_tuple_matches_module_contract(self):
        self.assertEqual(BANDS, ("DISQUALIFIED", "QUALIFIED", "INSUFFICIENT_DATA"))
        self.assertEqual(len(DIMENSIONS), 5)


if __name__ == "__main__":
    unittest.main()
