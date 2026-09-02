"""Tests for `foundation/hunt.py`.

Offline. Every notice here is a real-shaped TED dict, and the degewo
fixture carries the real clauses read off publication 578580-2026 on
2026-09-02. No test in this file opens a socket.
"""

import unittest

from foundation.hunt import (
    BAND_ORDER,
    HuntEntry,
    HuntIntegrityError,
    HuntReport,
    REQUEST_FIELDS_UNION,
    hunt,
    render_hunt,
    with_recency,
    with_open_deadline,
)
from foundation.eligibility import FIELDS as ELIGIBILITY_FIELDS
from foundation.mouth_ted import REQUEST_FIELDS as TED_FIELDS
from foundation.qualification import OperatorProfile
from foundation.relevance import CapabilityProfile


SOLO = OperatorProfile(
    name="solo operator (AU)",
    staff_count=1,
    certifications=frozenset(),
    insurance_cover_eur=None,
    corporate_references=(),
    languages=frozenset({"ENG"}),
)


def degewo_notice():
    """Real shape, real clauses, from TED 578580-2026."""
    return {
        "publication-number": "578580-2026",
        "notice-title": {"eng": ["Framework: penetration testing"]},
        "buyer-name": {"deu": ["degewo AG"]},
        "procedure-type": ["open"],
        "submission-language": ["DEU"],
        "selection-criterion-lot": [
            "slc-suit-reg-prof", "slc-stand-other",
            "slc-abil-ref-services", "slc-abil-staff-yrly-avg-mp",
        ],
        "selection-criterion-description-lot": {
            "deu": [
                "Der Anbieter hat mindestens zwei (2) vergleichbare "
                "Referenzen aus den letzten fuenf (5) Jahren nachzuweisen. "
                "Die Referenzen muessen jeweils ein Mindestauftragsvolumen "
                "von 50.000 EUR aufweisen.",
                "Mindeststandard: Mindestens 3 Penetrationstester, "
                "mindestens 1 Projektmanager.",
            ]
        },
    }


def bare_notice(pn="111111-2026"):
    """A notice TED publishes with no bidder conditions at all -- the
    Rotterdam/Metz/Loef shape, where criteria live only in the linked
    procurement documents."""
    return {
        "publication-number": pn,
        "notice-title": {"eng": ["Security assessment services"]},
        "buyer-name": {"eng": ["Some Buyer"]},
        "procedure-type": ["open"],
    }


class TestFieldUnion(unittest.TestCase):
    def test_union_covers_both_modules_without_editing_either(self):
        for f in TED_FIELDS:
            self.assertIn(f, REQUEST_FIELDS_UNION)
        for f in ELIGIBILITY_FIELDS:
            self.assertIn(f, REQUEST_FIELDS_UNION)

    def test_union_is_deduplicated(self):
        self.assertEqual(len(REQUEST_FIELDS_UNION),
                         len(set(REQUEST_FIELDS_UNION)))


class TestHuntBasics(unittest.TestCase):
    def test_assesses_every_notice_it_fetches(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice(),
                                                      bare_notice()])
        self.assertEqual(r.fetched, 2)
        self.assertEqual(r.assessed, 2)
        self.assertEqual(len(r.entries), 2)

    def test_degewo_is_disqualified_with_a_quoted_clause(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        entry = r.entries[0]
        self.assertEqual(entry.band, "DISQUALIFIED")
        self.assertTrue(entry.blocking_clauses,
                        "a DISQUALIFIED entry must carry its evidence")

    def test_notice_without_published_criteria_is_never_qualified(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [bare_notice()])
        self.assertNotEqual(r.entries[0].band, "QUALIFIED")

    def test_report_is_deterministic(self):
        notices = [bare_notice("333-2026"), degewo_notice(),
                   bare_notice("222-2026")]
        a = hunt("q", SOLO, fetch_notices_fn=lambda: list(notices))
        b = hunt("q", SOLO, fetch_notices_fn=lambda: list(notices))
        self.assertEqual([e.publication_number for e in a.entries],
                         [e.publication_number for e in b.entries])


class TestOrdering(unittest.TestCase):
    def test_unresolved_outranks_disqualified(self):
        r = hunt("q", SOLO,
                 fetch_notices_fn=lambda: [degewo_notice(), bare_notice()])
        bands = [e.band for e in r.entries]
        self.assertLess(bands.index("INSUFFICIENT_DATA"),
                        bands.index("DISQUALIFIED"),
                        "a proven-blocked notice must never be presented "
                        "above an unresolved one")

    def test_band_order_places_qualified_first(self):
        self.assertEqual(BAND_ORDER[0], "QUALIFIED")
        self.assertEqual(BAND_ORDER[-1], "DISQUALIFIED")

    def test_ties_broken_by_publication_number(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [
            bare_notice("999-2026"), bare_notice("111-2026")])
        self.assertEqual([e.publication_number for e in r.entries],
                         ["111-2026", "999-2026"])


class TestSkipping(unittest.TestCase):
    def test_notice_without_identity_is_recorded_not_dropped(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [
            {"notice-title": {"eng": ["no publication number"]}},
            degewo_notice()])
        self.assertEqual(r.fetched, 2)
        self.assertEqual(r.assessed, 1)
        self.assertEqual(len(r.skipped), 1)

    def test_non_dict_entries_are_ignored_before_counting(self):
        r = hunt("q", SOLO,
                 fetch_notices_fn=lambda: [degewo_notice(), "junk", None])
        self.assertEqual(r.fetched, 1)


class TestGuards(unittest.TestCase):
    def test_refuses_without_policy_or_injected_fetch(self):
        with self.assertRaises(HuntIntegrityError):
            hunt("q", SOLO)

    def test_refuses_empty_query(self):
        with self.assertRaises(HuntIntegrityError):
            hunt("   ", SOLO, fetch_notices_fn=lambda: [])

    def test_refuses_wrong_operator_type(self):
        with self.assertRaises(HuntIntegrityError):
            hunt("q", "not a profile", fetch_notices_fn=lambda: [])

    def test_refuses_out_of_range_limit(self):
        with self.assertRaises(HuntIntegrityError):
            hunt("q", SOLO, limit=0, fetch_notices_fn=lambda: [])
        with self.assertRaises(HuntIntegrityError):
            hunt("q", SOLO, limit=10_000, fetch_notices_fn=lambda: [])

    def test_entry_cannot_restate_its_own_band(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        real = r.entries[0]
        with self.assertRaises(HuntIntegrityError):
            HuntEntry(
                publication_number=real.publication_number,
                band="QUALIFIED",
                eligibility=real.eligibility,
                qualification=real.qualification,
                relevance=None,
                signal=None,
            )

    def test_report_cannot_overclaim_assessed_count(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        with self.assertRaises(HuntIntegrityError):
            HuntReport(entries=r.entries, fetched=1, assessed=99,
                       skipped=(), objective="x")

    def test_report_cannot_assess_more_than_it_fetched(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        with self.assertRaises(HuntIntegrityError):
            HuntReport(entries=r.entries, fetched=0, assessed=1,
                       skipped=(), objective="x")

    def test_by_band_rejects_an_unknown_band(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        with self.assertRaises(HuntIntegrityError):
            r.by_band("PROMISING")


class TestRelevanceIsAdditive(unittest.TestCase):
    def test_signal_is_built_from_the_correctly_reshaped_notice(self):
        # Regression: hunt() used to hand ted_signal() the RAW,
        # hyphenated notice dict (deadline-receipt-request, notice-title)
        # instead of mouth_ted.parse_items()'s flat shape (deadline,
        # title) that ted_signal() actually reads -- silently producing
        # a signal with an empty deadline and no title. A test asserting
        # only "a signal exists" passes even while the signal is hollow,
        # so this asserts the actual field content.
        notice = degewo_notice()
        notice["deadline-receipt-request"] = ["2026-09-22T12:00:00+02:00"]
        cap = CapabilityProfile(
            name="pentest", declared_by="operator",
            keywords=frozenset({"penetration"}))
        r = hunt("q", SOLO, capability=cap, fetch_notices_fn=lambda: [notice])
        entry = r.entries[0]
        self.assertIsNotNone(entry.signal)
        self.assertEqual(
            entry.signal.facts["deadline"], "2026-09-22T12:00:00+02:00")
        self.assertIn("penetration testing", entry.signal.claim)

    def test_relevance_absent_when_no_capability_profile(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        self.assertIsNone(r.entries[0].relevance)

    def test_relevance_present_when_capability_profile_given(self):
        cap = CapabilityProfile(
            name="pentest", declared_by="operator",
            keywords=frozenset({"penetration"}))
        r = hunt("q", SOLO, capability=cap,
                 fetch_notices_fn=lambda: [degewo_notice()])
        self.assertIsNotNone(r.entries[0].relevance)

    def test_qualification_band_unchanged_by_relevance(self):
        cap = CapabilityProfile(
            name="pentest", declared_by="operator",
            keywords=frozenset({"penetration"}))
        without = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        with_cap = hunt("q", SOLO, capability=cap,
                        fetch_notices_fn=lambda: [degewo_notice()])
        self.assertEqual(without.entries[0].band, with_cap.entries[0].band)


class TestRecency(unittest.TestCase):
    def test_appends_a_publication_date_bound(self):
        q = with_recency('FT ~ ("x")', 30)
        self.assertIn("publication-date >= today(-30)", q)
        self.assertTrue(q.startswith('FT ~ ("x")'))

    def test_rejects_empty_query(self):
        with self.assertRaises(HuntIntegrityError):
            with_recency("  ", 30)

    def test_rejects_out_of_range_days(self):
        with self.assertRaises(HuntIntegrityError):
            with_recency("q", 0)
        with self.assertRaises(HuntIntegrityError):
            with_recency("q", 99_999)

    def test_does_not_filter_on_deadline(self):
        # with_recency() is the FT-oriented lever; deadline-receipt-request
        # is a separate, genuinely-working filter (see with_open_deadline)
        # that must never be silently folded into this one.
        self.assertNotIn("deadline", with_recency("q", 30))


class TestOpenDeadline(unittest.TestCase):
    def test_appends_a_bare_today_deadline_bound(self):
        q = with_open_deadline("classification-cpv IN (72000000)")
        self.assertIn("deadline-receipt-request >= today()", q)

    def test_never_emits_today_with_a_zero_argument(self):
        # today(0) is wrong grammar -- measured live to silently return
        # zero results. This function must never regress to emitting it.
        q = with_open_deadline("classification-cpv IN (72000000)")
        self.assertNotIn("today(0)", q)

    def test_rejects_empty_query(self):
        with self.assertRaises(HuntIntegrityError):
            with_open_deadline("  ")

    def test_rejects_combination_with_full_text_clause(self):
        # Measured live: FT ~ (...) combined with deadline-receipt-request
        # silently returns zero results even though each half matches
        # plenty alone. This function refuses to build that query.
        with self.assertRaises(HuntIntegrityError):
            with_open_deadline('FT ~ ("penetration testing")')
        with self.assertRaises(HuntIntegrityError):
            with_open_deadline('FT~("penetration testing")')


class TestRender(unittest.TestCase):
    def test_render_states_what_the_bands_are_not(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        text = render_hunt(r)
        self.assertIn("not revenue", text)
        self.assertIn("UNRESOLVED, not promising", text)

    def test_render_prints_blocking_clauses(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [degewo_notice()])
        self.assertIn("BLOCKED BY:", render_hunt(r))

    def test_render_reports_an_empty_hunt_honestly(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [])
        self.assertIn("real result, not an error", render_hunt(r))

    def test_render_lists_skipped_reasons(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [{"x": 1},
                                                      degewo_notice()])
        self.assertIn("skipped:", render_hunt(r))

    def test_render_rejects_a_non_report(self):
        with self.assertRaises(HuntIntegrityError):
            render_hunt("not a report")

    def test_render_limit_truncates(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [
            degewo_notice(), bare_notice("222-2026"), bare_notice("333-2026")])
        self.assertLess(len(render_hunt(r, limit=1)), len(render_hunt(r)))


if __name__ == "__main__":
    unittest.main()


class TestSourceFailureIsLoud(unittest.TestCase):
    """A whole source failing is not the same as one notice being
    skipped, and burying both in one undifferentiated list hides the
    worse of the two.

    2026-09-03: a nightly multi-source sweep reported "fetched 360,
    assessed 50, skipped 1" while TED -- the largest source -- had
    returned HTTP 400 and contributed nothing. Nothing lied; the failure
    was in `skipped`. It was simply one line among per-notice noise,
    under a total that looked entirely plausible. An operator who
    believes they swept five sources and actually swept four has a false
    picture of the market, not a smaller one."""

    def _failing_source(self):
        from foundation.sources import Source

        def boom():
            raise RuntimeError("simulated 400")
        return Source(source_id="BROKEN", fetch_items=boom,
                      normalise=lambda i: None,
                      server_side_filterable=False, keyword_fields=("title",))

    def test_source_failure_is_prefixed(self):
        from foundation.hunt import hunt_multi
        r = hunt_multi("q", SOLO, (self._failing_source(),))
        self.assertTrue(any(s.startswith("SOURCE FAILED") for s in r.skipped))

    def test_render_warns_loudly_about_a_failed_source(self):
        from foundation.hunt import hunt_multi
        r = hunt_multi("q", SOLO, (self._failing_source(),))
        text = render_hunt(r)
        self.assertIn("SOURCE(S) RETURNED NOTHING", text)
        self.assertIn("covers less than it appears to", text)

    def test_per_notice_skip_does_not_trigger_the_source_warning(self):
        r = hunt("q", SOLO, fetch_notices_fn=lambda: [
            {"notice-title": {"eng": ["no publication number"]}},
            degewo_notice()])
        self.assertEqual(len(r.skipped), 1)
        self.assertNotIn("SOURCE(S) RETURNED NOTHING", render_hunt(r))
