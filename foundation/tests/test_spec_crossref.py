"""Tests for `foundation/spec_crossref.py`.

Offline; no test opens a socket and none reads the 485 MB corpus. The
fixtures below reproduce, in miniature, the exact text shapes that
produced four candidates against Swiss Post's real System and Verifier
Specifications on 2026-09-04 -- all four of which were innocent, and
two of which were caused by this checker's own handling of the text.
"""

import unittest

from foundation.spec_crossref import (
    CANDIDATE_KINDS,
    CrossRefCandidate,
    LIGATURES,
    SpecCrossRefError,
    crossref,
    format_crossref,
    normalise_extracted_text,
)

DEF = r"Algorithm\s+(\d+\.\d+)\s+([A-Z][A-Za-z0-9]{3,60})"
REF = r"[Aa]lgorithm\s+(\d+\.\d+)"


def _spec(*chunks):
    return "\n".join(chunks)


class TestTheLigatureBugThatManufacturedTwoFalseCandidates(unittest.TestCase):
    r"""THE REASON THIS MODULE NORMALISES BEFORE IT MATCHES.

    PDF extraction preserves `fi` as U+FB01. `ConfirmVoteAgreement`
    comes out as `Con` + U+FB01 + `rmVoteAgreement`, and U+FB01 is not
    in [A-Za-z], so an identifier pattern truncates the name to `Con`
    and the definition disappears. On the real Swiss Post specification
    that produced a REFERENCED_NEVER_DEFINED candidate for Algorithm
    6.7 -- which is defined, on page 137, in plain sight.
    """

    LIGATURE_SPEC = _spec(
        "Algorithm 6.7 ConﬁrmVoteAgreement",
        "Context: the long Vote Cast Return Codes allow list",
        "6: Verif <- ConﬁrmVoteAgreement(...) . See algorithm 6.7",
    )

    def test_without_normalisation_the_definition_would_vanish(self):
        """Establishes the bug is real, by checking the raw text really
        does defeat the pattern this module is given."""
        import re
        self.assertIsNone(re.search(DEF, self.LIGATURE_SPEC))

    def test_with_normalisation_the_definition_is_found(self):
        r = crossref(self.LIGATURE_SPEC,
                     definition_pattern=DEF, reference_pattern=REF)
        self.assertIn("6.7", r.definitions)
        self.assertEqual(r.definitions["6.7"], ("ConfirmVoteAgreement",))

    def test_no_false_dangling_candidate_is_raised(self):
        r = crossref(self.LIGATURE_SPEC,
                     definition_pattern=DEF, reference_pattern=REF)
        self.assertEqual(r.candidates, ())

    def test_the_report_counts_the_ligatures_it_had_to_repair(self):
        """Surfaced because a document full of them is a document whose
        every identifier-based result should be re-checked."""
        r = crossref(self.LIGATURE_SPEC,
                     definition_pattern=DEF, reference_pattern=REF)
        self.assertEqual(r.ligatures_found, 2)

    def test_every_known_ligature_expands(self):
        for lig, plain in LIGATURES.items():
            self.assertIn(plain, normalise_extracted_text(f"x{lig}y"))

    def test_nfkc_is_off_by_default(self):
        """NFKC rewrites superscripts, which in a cryptographic spec are
        content -- `g^2` and `g2` are not the same claim."""
        text = "E1ⱼ superscript ²"
        self.assertIn("²", normalise_extracted_text(text))
        self.assertNotIn("²", normalise_extracted_text(text, nfkc=True))


class TestTheOtherFalseCandidate(unittest.TestCase):
    """`ExtractVeri` appeared to be one name at two numbers. It was two
    different names truncated at the same ligature."""

    TRUNCATION_SPEC = _spec(
        "Algorithm 3.17 ExtractVeriﬁcationCardSecret",
        "Algorithm 3.19 ExtractVeriﬁcationCardKeystore",
        "See algorithm 3.17 and algorithm 3.19",
    )

    def test_two_distinct_names_are_not_collapsed(self):
        r = crossref(self.TRUNCATION_SPEC,
                     definition_pattern=DEF, reference_pattern=REF)
        self.assertEqual(r.candidates, ())
        self.assertEqual(r.definitions["3.17"], ("ExtractVerificationCardSecret",))
        self.assertEqual(r.definitions["3.19"], ("ExtractVerificationCardKeystore",))


class TestRealStructuralProblemsAreStillCaught(unittest.TestCase):
    """Normalising away the false positives must not blunt the check."""

    def test_a_genuinely_undefined_reference_is_raised(self):
        r = crossref(_spec("Algorithm 1.1 GenKeyPair",
                           "See algorithm 9.9 for details"),
                     definition_pattern=DEF, reference_pattern=REF)
        kinds = {(c.kind, c.subject) for c in r.candidates}
        self.assertIn(("REFERENCED_NEVER_DEFINED", "9.9"), kinds)

    def test_one_number_with_two_genuinely_different_names_is_raised(self):
        r = crossref(_spec("Algorithm 4.2 GenKeyPair",
                           "Algorithm 4.2 DecryptVotes",
                           "see algorithm 4.2"),
                     definition_pattern=DEF, reference_pattern=REF)
        kinds = {(c.kind, c.subject) for c in r.candidates}
        self.assertIn(("NUMBER_WITH_SEVERAL_NAMES", "4.2"), kinds)

    def test_one_name_at_two_genuinely_different_numbers_is_raised(self):
        r = crossref(_spec("Algorithm 4.2 GenKeyPair",
                           "Algorithm 7.3 GenKeyPair",
                           "see algorithm 4.2 and algorithm 7.3"),
                     definition_pattern=DEF, reference_pattern=REF)
        kinds = {(c.kind, c.subject) for c in r.candidates}
        self.assertIn(("NAME_WITH_SEVERAL_NUMBERS", "GenKeyPair"), kinds)

    def test_unreferenced_definitions_are_opt_in_only(self):
        """An algorithm cited only from a SIBLING document is normal.
        Reporting it by default would bury the real candidates."""
        spec = _spec("Algorithm 4.2 GenKeyPair", "Algorithm 4.3 DecryptVotes",
                     "see algorithm 4.2")
        quiet = crossref(spec, definition_pattern=DEF, reference_pattern=REF)
        loud = crossref(spec, definition_pattern=DEF, reference_pattern=REF,
                        report_unreferenced=True)
        self.assertEqual(quiet.candidates, ())
        self.assertIn("DEFINED_NEVER_REFERENCED",
                      {c.kind for c in loud.candidates})


class TestCandidatesAreNeverCalledFindings(unittest.TestCase):
    """Every candidate raised against the real specification was
    innocent. The vocabulary has to carry that or the next reader files
    a false report to a public issue tracker."""

    def test_a_candidate_cannot_exist_without_an_innocent_explanation(self):
        with self.assertRaises(SpecCrossRefError):
            CrossRefCandidate(kind="REFERENCED_NEVER_DEFINED", subject="6.7",
                              detail="no definition", why_it_might_be_fine="")

    def test_the_render_never_uses_the_word_finding(self):
        r = crossref(_spec("Algorithm 1.1 GenKeyPair", "see algorithm 9.9"),
                     definition_pattern=DEF, reference_pattern=REF)
        out = format_crossref(r)
        self.assertIn("CANDIDATES", out)
        # The word appears exactly once, in the disclaimer that these
        # are NOT findings. It must never label a candidate.
        self.assertIn("NOT findings", out)
        self.assertNotIn("FINDINGS (", out)
        self.assertNotIn("vulnerability", out.lower())

    def test_the_render_carries_the_innocent_explanation(self):
        r = crossref(_spec("Algorithm 1.1 GenKeyPair", "see algorithm 9.9"),
                     definition_pattern=DEF, reference_pattern=REF)
        self.assertIn("might be fine because", format_crossref(r))

    def test_a_clean_document_is_not_called_correct(self):
        """No candidates means not-inconsistent-in-the-ways-checked. It
        does not mean the specification is right."""
        out = format_crossref(crossref(
            _spec("Algorithm 1.1 GenKeyPair", "see algorithm 1.1"),
            definition_pattern=DEF, reference_pattern=REF))
        self.assertIn("NO CANDIDATES", out)
        self.assertIn("not a statement that the document is", out)


class TestSilenceIsNeverClearance(unittest.TestCase):
    def test_empty_text_is_not_assessed(self):
        r = crossref("", definition_pattern=DEF, reference_pattern=REF)
        self.assertEqual(r.status, "NOT_ASSESSED")

    def test_the_unread_render_says_nothing_was_checked(self):
        out = format_crossref(crossref("", definition_pattern=DEF,
                                       reference_pattern=REF))
        self.assertIn("not the same as nothing being wrong", out)


class TestIntegrity(unittest.TestCase):
    def test_non_string_input_is_refused(self):
        with self.assertRaises(SpecCrossRefError):
            crossref(None, definition_pattern=DEF, reference_pattern=REF)

    def test_a_definition_pattern_with_one_group_is_refused(self):
        with self.assertRaises(SpecCrossRefError):
            crossref("Algorithm 1.1 X", definition_pattern=r"Algorithm (\d+)",
                     reference_pattern=REF)

    def test_a_bad_regex_is_a_named_error_not_a_traceback(self):
        with self.assertRaises(SpecCrossRefError):
            crossref("x", definition_pattern=r"(unclosed", reference_pattern=REF)

    def test_an_unknown_candidate_kind_is_refused(self):
        with self.assertRaises(SpecCrossRefError):
            CrossRefCandidate(kind="SCARY", subject="x", detail="y",
                              why_it_might_be_fine="z")

    def test_format_refuses_a_non_report(self):
        with self.assertRaises(SpecCrossRefError):
            format_crossref("NO_CANDIDATES")

    def test_every_kind_is_reachable(self):
        self.assertEqual(len(CANDIDATE_KINDS), len(set(CANDIDATE_KINDS)))

    def test_module_has_no_network_import(self):
        from pathlib import Path
        from foundation import spec_crossref
        src = Path(spec_crossref.__file__).read_text(encoding="utf-8")
        for lib in ("urllib", "requests", "socket", "http.client"):
            self.assertNotIn(f"import {lib}", src)


if __name__ == "__main__":
    unittest.main()


class TestNameCitationCountsAsCitation(unittest.TestCase):
    """A 27-OUT-OF-27 FALSE POSITIVE RATE, MEASURED.

    The first version raised DEFINED_NEVER_REFERENCED for any algorithm
    not cited by NUMBER. Against Swiss Post's real System Specification
    that was 27 candidates and every one was innocent, for one
    systematic reason: the pseudocode calls algorithms by name.
    `MixDecOnline` is written 26 times; its number never is.
    """

    def test_an_algorithm_cited_only_by_name_is_not_raised(self):
        spec = _spec("Algorithm 6.3 MixDecOnline",
                     "Algorithm 1.1 GenKeyPair",
                     "3: c <- MixDecOnline(votes) . mix and decrypt",
                     "see algorithm 1.1")
        r = crossref(spec, definition_pattern=DEF, reference_pattern=REF,
                     report_unreferenced=True)
        self.assertEqual(r.candidates, ())

    def test_an_algorithm_cited_by_neither_number_nor_name_is_raised(self):
        spec = _spec("Algorithm 6.3 MixDecOnline",
                     "Algorithm 1.1 GenKeyPair",
                     "see algorithm 1.1")
        r = crossref(spec, definition_pattern=DEF, reference_pattern=REF,
                     report_unreferenced=True)
        subjects = {c.subject for c in r.candidates
                    if c.kind == "DEFINED_NEVER_REFERENCED"}
        self.assertEqual(subjects, {"6.3"})

    def test_the_detail_names_what_was_searched_for(self):
        spec = _spec("Algorithm 6.3 MixDecOnline", "Algorithm 1.1 GenKeyPair",
                     "see algorithm 1.1")
        r = crossref(spec, definition_pattern=DEF, reference_pattern=REF,
                     report_unreferenced=True)
        c = [c for c in r.candidates if c.kind == "DEFINED_NEVER_REFERENCED"][0]
        self.assertIn("MixDecOnline", c.detail)
        self.assertIn("neither by number nor by name", c.detail)
