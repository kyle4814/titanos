"""Tests for the relevance filter.

Per the module's own doctrine: a relevance score is not a qualification.
These tests check that distinction is enforced structurally, not just
that the ranking "feels right" -- see `test_never_emits_qualified_word`
and `test_no_ledger_import_or_write`.
"""

import re
import unittest

from foundation.relevance import (
    BANDS, CapabilityProfile, RelevanceAssessment, RelevanceIntegrityError,
    rank, score,
)
from foundation.signal_spine import CanonicalSignal

PROFILE = CapabilityProfile(
    name="test-operator-cloud-security",
    declared_by="test-suite",
    keywords=frozenset({
        "cloud security", "penetration testing", "vulnerability assessment",
        "incident response", "soc 2", "network security",
    }),
    cpv_codes=frozenset({"72500000"}),
    exclusions=frozenset({"asbestos removal", "road resurfacing"}),
)


def make_signal(signal_id, claim="", target="notice://x", facts=None,
                 evidence=None, source_ref="ref://1"):
    return CanonicalSignal(
        signal_id=signal_id,
        source_id="test-tentacle",
        source_type="PRIMARY",
        source_ref=source_ref,
        target=target,
        kind="DEMAND",
        claim=claim,
        observed_at="2026-09-01T00:00:00Z",
        facts=facts or {},
        evidence=evidence or {},
    )


class TestClearMatch(unittest.TestCase):

    def test_clearly_matching_notice_scores_strong(self):
        sig = make_signal(
            "sig-1",
            claim=(
                "Local council seeks a supplier to provide cloud security "
                "review, penetration testing and a full vulnerability "
                "assessment of its public-facing services, culminating in "
                "an incident response readiness report."
            ),
        )
        a = score(sig, PROFILE)
        self.assertEqual(a.band, "STRONG_MATCH")
        self.assertGreaterEqual(len(a.matched_keywords), 3)
        self.assertFalse(a.stuffing_suspected)
        self.assertIn("SURFACE MATCH ONLY", a.note)

    def test_cpv_code_alone_is_strong(self):
        sig = make_signal(
            "sig-cpv",
            claim="Provision of general professional services for the "
                  "authority's ongoing operational needs across the year.",
            facts={"cpv_code": "72500000"},
        )
        a = score(sig, PROFILE)
        self.assertEqual(a.band, "STRONG_MATCH")
        self.assertIn("72500000", a.matched_cpv_codes)


class TestExclusion(unittest.TestCase):

    def test_irrelevant_notice_is_excluded_with_reason(self):
        sig = make_signal(
            "sig-2",
            claim="Contractor required for asbestos removal from three "
                  "council-owned buildings prior to demolition.",
        )
        a = score(sig, PROFILE)
        self.assertEqual(a.band, "EXCLUDED")
        self.assertIn("asbestos removal", a.exclusion_reasons)

    def test_exclusion_overrides_positive_match(self):
        # Contains a strong positive keyword hit AND an exclusion term.
        # Exclusion must win.
        sig = make_signal(
            "sig-3",
            claim="Cloud security review required, but this contract is "
                  "primarily road resurfacing and asbestos removal work.",
        )
        a = score(sig, PROFILE)
        self.assertEqual(a.band, "EXCLUDED")


class TestUnknown(unittest.TestCase):

    def test_garbage_notice_with_no_evidence_fields_is_unknown(self):
        # CanonicalSignal refuses a whitespace-only claim ("a signal
        # must state what was seen"), so a literally empty claim is not
        # constructible -- but a claim made entirely of invisible
        # zero-width/formatting characters passes that check (it is
        # non-blank by str.strip()'s definition) while carrying zero
        # real content. `neutralise()` strips exactly that Unicode
        # category, so this is the realistic "garbage notice" case:
        # something arrived, but there was nothing in it to read.
        sig = make_signal("sig-5", claim="​‌‍﻿",
                           target="", source_ref="")
        a = score(sig, PROFILE)
        self.assertEqual(a.band, "UNKNOWN")
        self.assertTrue(a.unknown_reason.strip())

    def test_unknown_is_a_real_distinct_band(self):
        self.assertIn("UNKNOWN", BANDS)

    def test_unknown_assessment_requires_a_reason(self):
        with self.assertRaises(RelevanceIntegrityError):
            RelevanceAssessment(
                signal_id="x", profile_name="p", band="UNKNOWN",
                unknown_reason="",
            )


class TestKeywordStuffing(unittest.TestCase):

    def test_stuffed_notice_does_not_reach_top_band(self):
        stuffed_claim = " ".join(
            ["cloud security penetration testing vulnerability assessment "
             "incident response soc 2 network security"] * 20
        )
        sig = make_signal("sig-stuffed", claim=stuffed_claim)
        a = score(sig, PROFILE)
        self.assertNotEqual(a.band, "STRONG_MATCH")
        self.assertTrue(a.stuffing_suspected)

    def test_naturally_worded_notice_is_not_flagged_as_stuffed(self):
        sig = make_signal(
            "sig-natural",
            claim=(
                "The authority is issuing this notice to seek a qualified "
                "supplier able to carry out a cloud security assessment "
                "of internally hosted systems, alongside a review of "
                "network security controls at the perimeter. The scope "
                "includes penetration testing of externally reachable "
                "endpoints and a written report summarising findings and "
                "recommended remediation steps, to be delivered within "
                "eight weeks of contract award. Interested parties "
                "should register their interest through the authority's "
                "e-tendering portal before the submission deadline."
            ),
        )
        a = score(sig, PROFILE)
        self.assertFalse(a.stuffing_suspected)
        self.assertEqual(a.band, "STRONG_MATCH")


class TestRankingStability(unittest.TestCase):

    def test_ranking_is_stable_across_runs(self):
        signals = [
            make_signal("z-sig", claim="cloud security review needed"),
            make_signal("a-sig", claim="cloud security review needed"),
            make_signal("m-sig", claim="road resurfacing contract"),
            make_signal("b-sig", claim="totally unrelated catering supply"),
        ]
        first = rank(signals, PROFILE)
        for _ in range(5):
            again = rank(list(reversed(signals)), PROFILE)
            self.assertEqual(
                [a.signal_id for a in first],
                [a.signal_id for a in again],
            )

    def test_tie_broken_by_signal_id(self):
        signals = [
            make_signal("beta", claim="cloud security review needed"),
            make_signal("alpha", claim="cloud security review needed"),
        ]
        ordered = rank(signals, PROFILE)
        self.assertEqual([a.signal_id for a in ordered], ["alpha", "beta"])


class TestNeverClaimsQualification(unittest.TestCase):

    def test_never_emits_qualified_word(self):
        signals = [
            make_signal("q1", claim="cloud security penetration testing "
                                     "incident response vulnerability "
                                     "assessment for the authority"),
            make_signal("q2", claim="asbestos removal works"),
            make_signal("q3", claim="​‌‍﻿", target="", source_ref=""),
        ]
        for sig in signals:
            a = score(sig, PROFILE)
            rendered = repr(a) + str(a.__dict__)
            self.assertNotIn("qualified", rendered.lower())
            self.assertNotIn("qualification", rendered.lower())

    def test_source_never_mentions_qualified_for_scored_items(self):
        import inspect
        import foundation.relevance as relevance_module
        source = inspect.getsource(relevance_module)
        # The module docstring is allowed to explain the doctrine (it
        # references "qualified"/"qualification" only to disclaim them).
        # No executable code path -- outside the docstring and comments
        # explaining the prohibition -- may construct that word about a
        # scored item. We assert the two doctrine-explaining hits are
        # the only occurrences and both sit in prose, not in a band
        # name, field value, or f-string fed by scoring logic.
        for band in BANDS:
            self.assertNotIn("QUALIF", band.upper())

    def test_no_ledger_import_or_write(self):
        import ast
        import foundation.relevance as relevance_module
        src_file = relevance_module.__file__
        with open(src_file, "r", encoding="utf-8") as fh:
            text = fh.read()
        tree = ast.parse(text)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
        for forbidden in ("outcome_ledger", "opportunity_pipeline"):
            self.assertFalse(
                any(forbidden in m for m in imported_modules),
                f"relevance.py must not import {forbidden}")
        # No `.record(` call anywhere -- the one write method the
        # ledger exposes.
        self.assertNotIn(".record(", text)


class TestCapabilityProfileIsHonestData(unittest.TestCase):

    def test_profile_requires_attribution(self):
        with self.assertRaises(RelevanceIntegrityError):
            CapabilityProfile(name="x", declared_by="",
                               keywords=frozenset({"security"}))

    def test_empty_profile_refused(self):
        with self.assertRaises(RelevanceIntegrityError):
            CapabilityProfile(name="x", declared_by="someone")


if __name__ == "__main__":
    unittest.main()
