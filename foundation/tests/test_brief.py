"""Tests for `foundation/brief.py`.

Offline. Every notice is a real-shaped TED dict (same style as
`test_hunt.py`'s fixtures). No test here opens a socket.

`hunt()` itself only ever calls `mouth_ted.ted_signal()` with the RAW
notice dict, which reads `item.get("deadline", ...)` -- a key the raw
TED notice dict never carries (`deadline-receipt-request` is the raw
key; `"deadline"` only exists on `parse_items()`'s POST-parse item
shape). That means every `HuntEntry` produced by `hunt()` itself
carries an UNKNOWN deadline today, regardless of capability profile --
confirmed below rather than assumed. To test this module's actual
day-arithmetic (which is the point of `foundation/brief.py`), several
tests build a `HuntEntry` directly with a hand-attached `CanonicalSignal`
carrying a real `facts["deadline"]` -- `HuntEntry` is a public dataclass
from `hunt.py` and this is exactly the kind of already-computed-fields
composition `brief.py`'s own docstring says it consumes.
"""

import unittest
from datetime import datetime, timezone

from foundation.brief import (
    Brief,
    BriefIntegrityError,
    DeadlineEntry,
    UnresolvedEntry,
    BlockedEntry,
    build_brief,
    render_brief,
)
from foundation.eligibility import assess_eligibility
from foundation.hunt import HuntEntry, HuntReport, hunt
from foundation.qualification import OperatorProfile, assess
from foundation.signal_spine import CanonicalSignal


SOLO = OperatorProfile(
    name="solo operator (AU)",
    staff_count=1,
    certifications=frozenset(),
    insurance_cover_eur=None,
    corporate_references=(),
    languages=frozenset({"ENG"}),
)

# An operator with everything a real notice might ask for, used to build
# a genuinely QUALIFIED fixture.
FULL = OperatorProfile(
    name="full operator (AU)",
    staff_count=10,
    certifications=frozenset({"ISO27001"}),
    insurance_cover_eur=5_000_000.0,
    corporate_references=("ref-1", "ref-2"),
    languages=frozenset({"ENG"}),
)


def degewo_notice():
    """Real shape, real clauses, from TED 578580-2026 -- DISQUALIFIED
    against SOLO (no certifications, no insurance, no references)."""
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
                "Referenzen aus den letzten fuenf (5) Jahren nachzuweisen.",
            ]
        },
    }


def bare_notice(pn="111111-2026"):
    """No bidder conditions published at all -- every dimension UNKNOWN,
    so this always lands INSUFFICIENT_DATA regardless of operator."""
    return {
        "publication-number": pn,
        "notice-title": {"eng": ["Security assessment services"]},
        "buyer-name": {"eng": ["Some Buyer"]},
        "procedure-type": ["open"],
    }


def qualified_notice(pn="222222-2026"):
    """`selection-criterion-lot` is present (so every category is KNOWN,
    not UNKNOWN) but the only code is a suitability code, which falls
    into none of the four barrier-eligible categories -- every dimension
    resolves NOT_BARRIER, and `submission-language` matches FULL's
    declared ENG. QUALIFIED against FULL."""
    return {
        "publication-number": pn,
        "notice-title": {"eng": ["Cyber advisory services"]},
        "buyer-name": {"eng": ["Clean Buyer"]},
        "procedure-type": ["open"],
        "submission-language": ["ENG"],
        "selection-criterion-lot": ["slc-suit-reg-prof"],
        "document-url-lot": ["https://ted.europa.eu/docs/222222-2026"],
        "links": {"html": {"ENG": "https://ted.europa.eu/notice/222222-2026"}},
    }


def hunt_entry(notice: dict, operator: OperatorProfile, deadline: str = "") -> HuntEntry:
    """Build one HuntEntry the way `hunt()` does internally, then
    optionally attach a CanonicalSignal carrying a real deadline --
    see module docstring for why `hunt()` itself cannot produce this."""
    eligibility = assess_eligibility(notice)
    qualification = assess(eligibility, operator)
    signal = None
    if deadline:
        signal = CanonicalSignal(
            signal_id=f"tender:test:{eligibility.publication_number}",
            source_id="test",
            source_type="OFFICIAL",
            source_ref=eligibility.notice_url or "https://example.test",
            target=eligibility.publication_number,
            kind="DEMAND",
            claim=f"open EU TED public-sector tender: {eligibility.publication_number}",
            observed_at="2026-09-02T00:00:00+00:00",
            facts={"deadline": deadline},
        )
    return HuntEntry(
        publication_number=eligibility.publication_number,
        band=qualification.band,
        eligibility=eligibility,
        qualification=qualification,
        relevance=None,
        signal=signal,
    )


def report_of(*entries: HuntEntry, objective: str = "test") -> HuntReport:
    return HuntReport(
        entries=tuple(entries),
        fetched=len(entries),
        assessed=len(entries),
        skipped=(),
        objective=objective,
    )


NOW = datetime(2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc)


class TestPipelineDeadline(unittest.TestCase):
    """This class used to be `TestPipelineDeadlineIsAlwaysUnknown` and
    asserted that `hunt()` could never produce a real deadline. That was
    true when written -- `hunt()` passed the raw notice to
    `ted_signal()`, which reads `parse_items()`'s flat keys -- and it is
    no longer true: `hunt()` now re-shapes through `parse_items()`.

    The old test kept passing after the fix, because its fixture carries
    no `deadline-receipt-request` at all. A test that passes for a
    reason other than the one in its name is a test that will mislead
    the next person to read it, so both cases are now pinned
    explicitly."""

    def _signal_deadline(self, notice):
        from foundation.relevance import CapabilityProfile
        cap = CapabilityProfile(name="x", declared_by="y",
                                keywords=frozenset({"advisory"}))
        r = hunt("q", FULL, capability=cap, fetch_notices_fn=lambda: [notice])
        entry = r.entries[0]
        self.assertIsNotNone(entry.signal)
        return entry.signal.facts.get("deadline", "")

    def test_notice_without_a_deadline_field_yields_no_deadline(self):
        self.assertEqual(self._signal_deadline(qualified_notice()), "")

    def test_notice_with_a_real_deadline_field_yields_it(self):
        notice = qualified_notice()
        notice["deadline-receipt-request"] = ["2026-10-01T12:00:00+00:00"]
        self.assertEqual(
            self._signal_deadline(notice), "2026-10-01T12:00:00+00:00",
            "hunt() re-shapes through parse_items() now; a real "
            "deadline-receipt-request must reach the signal")


class TestEmptyBrief(unittest.TestCase):
    def test_empty_report_produces_empty_brief(self):
        brief = build_brief(report_of(), now=NOW)
        self.assertEqual(brief.action_required, ())
        self.assertEqual(brief.unresolved, ())
        self.assertEqual(brief.blocked, ())
        self.assertFalse(brief.has_previous_state)

    def test_empty_brief_renders_plainly(self):
        brief = build_brief(report_of(), now=NOW)
        text = render_brief(brief)
        self.assertIn("Nothing closing, nothing new, nothing unresolved, "
                       "nothing blocked", text)
        self.assertIn("A quiet morning is a real and useful result", text)


class TestActionRequired(unittest.TestCase):
    def test_disqualified_never_appears(self):
        entry = hunt_entry(degewo_notice(), SOLO)
        brief = build_brief(report_of(entry), now=NOW)
        self.assertEqual(brief.action_required, ())

    def test_unknown_deadline_is_always_included_and_labeled(self):
        entry = hunt_entry(bare_notice(), SOLO)  # no signal -> UNKNOWN
        brief = build_brief(report_of(entry), now=NOW, closing_within_days=1)
        self.assertEqual(len(brief.action_required), 1)
        e = brief.action_required[0]
        self.assertIsNone(e.days_remaining)
        self.assertEqual(e.deadline_display, "UNKNOWN")

    def test_within_window_is_included(self):
        entry = hunt_entry(qualified_notice(), FULL,
                            deadline="2026-09-10T00:00:00Z")  # 8 days out
        brief = build_brief(report_of(entry), now=NOW, closing_within_days=14)
        self.assertEqual(len(brief.action_required), 1)
        self.assertEqual(brief.action_required[0].days_remaining, 8)

    def test_exactly_at_window_boundary_is_included(self):
        entry = hunt_entry(qualified_notice(), FULL,
                            deadline="2026-09-16T00:00:00Z")  # 14 days out
        brief = build_brief(report_of(entry), now=NOW, closing_within_days=14)
        self.assertEqual(len(brief.action_required), 1)
        self.assertEqual(brief.action_required[0].days_remaining, 14)

    def test_one_day_past_window_is_excluded(self):
        entry = hunt_entry(qualified_notice(), FULL,
                            deadline="2026-09-17T00:00:00Z")  # 15 days out
        brief = build_brief(report_of(entry), now=NOW, closing_within_days=14)
        self.assertEqual(brief.action_required, ())

    def test_deadline_already_passed_is_excluded(self):
        entry = hunt_entry(qualified_notice(), FULL,
                            deadline="2026-08-01T00:00:00Z")  # in the past
        brief = build_brief(report_of(entry), now=NOW, closing_within_days=14)
        self.assertEqual(brief.action_required, ())

    def test_unparseable_deadline_text_is_unknown_not_dropped(self):
        entry = hunt_entry(qualified_notice(), FULL, deadline="not-a-date")
        brief = build_brief(report_of(entry), now=NOW, closing_within_days=1)
        self.assertEqual(len(brief.action_required), 1)
        self.assertIsNone(brief.action_required[0].days_remaining)

    def test_unknown_sorts_ahead_of_known_urgency(self):
        known = hunt_entry(qualified_notice("222222-2026"), FULL,
                            deadline="2026-09-03T00:00:00Z")  # 1 day out
        unknown = hunt_entry(bare_notice("333333-2026"), SOLO)  # UNKNOWN
        brief = build_brief(report_of(known, unknown), now=NOW,
                             closing_within_days=14)
        self.assertEqual(brief.action_required[0].publication_number,
                          "333333-2026")

    def test_ranked_by_ascending_days_remaining(self):
        far = hunt_entry(qualified_notice("444444-2026"), FULL,
                          deadline="2026-09-14T00:00:00Z")  # 12 days
        near = hunt_entry(qualified_notice("555555-2026"), FULL,
                           deadline="2026-09-04T00:00:00Z")  # 2 days
        brief = build_brief(report_of(far, near), now=NOW,
                             closing_within_days=14)
        self.assertEqual(
            [e.publication_number for e in brief.action_required],
            ["555555-2026", "444444-2026"])


class TestNewSinceLastBrief(unittest.TestCase):
    def test_no_prior_state_marks_section_uncomputed(self):
        entry = hunt_entry(qualified_notice(), FULL)
        brief = build_brief(report_of(entry), now=NOW)
        self.assertFalse(brief.has_previous_state)
        self.assertEqual(brief.new_since_last, ())
        self.assertIn("cannot be computed",
                       render_brief(brief))

    def test_previously_seen_publication_is_not_new(self):
        entry = hunt_entry(qualified_notice("222222-2026"), FULL)
        brief = build_brief(report_of(entry), now=NOW,
                             previous_publication_numbers=["222222-2026"])
        self.assertTrue(brief.has_previous_state)
        self.assertEqual(brief.new_since_last, ())

    def test_unseen_publication_is_new(self):
        entry = hunt_entry(qualified_notice("222222-2026"), FULL)
        brief = build_brief(report_of(entry), now=NOW,
                             previous_publication_numbers=["999999-2026"])
        self.assertEqual(len(brief.new_since_last), 1)
        self.assertEqual(brief.new_since_last[0].publication_number,
                          "222222-2026")

    def test_disqualified_never_counts_as_new(self):
        entry = hunt_entry(degewo_notice(), SOLO)
        brief = build_brief(report_of(entry), now=NOW,
                             previous_publication_numbers=[])
        self.assertEqual(brief.new_since_last, ())


class TestUnresolved(unittest.TestCase):
    def test_bare_notice_is_unresolved_with_document_url(self):
        entry = hunt_entry(bare_notice(), SOLO)
        brief = build_brief(report_of(entry), now=NOW)
        self.assertEqual(len(brief.unresolved), 1)
        u = brief.unresolved[0]
        self.assertEqual(u.publication_number, "111111-2026")
        self.assertTrue(u.unresolved_dimensions)

    def test_no_url_at_all_renders_unknown_never_blank(self):
        entry = hunt_entry(bare_notice(), SOLO)
        brief = build_brief(report_of(entry), now=NOW)
        self.assertEqual(brief.unresolved[0].document_url, "UNKNOWN")

    def test_real_document_url_is_carried_through(self):
        # qualified_notice() is QUALIFIED, not INSUFFICIENT_DATA, so
        # build one with published criteria this module cannot resolve
        # (a staffing code with no parseable threshold) to land
        # INSUFFICIENT_DATA while still carrying a document URL.
        notice = {
            "publication-number": "666666-2026",
            "notice-title": {"eng": ["Advisory"]},
            "buyer-name": {"eng": ["Buyer"]},
            "procedure-type": ["open"],
            "submission-language": ["ENG"],
            "selection-criterion-lot": ["slc-abil-staff-yrly-avg-mp"],
            "document-url-lot": ["https://ted.europa.eu/docs/666666-2026"],
        }
        entry = hunt_entry(notice, FULL)
        self.assertEqual(entry.band, "INSUFFICIENT_DATA")
        brief = build_brief(report_of(entry), now=NOW)
        self.assertEqual(brief.unresolved[0].document_url,
                          "https://ted.europa.eu/docs/666666-2026")

    def test_qualified_and_disqualified_never_appear_unresolved(self):
        q = hunt_entry(qualified_notice(), FULL)
        d = hunt_entry(degewo_notice(), SOLO)
        brief = build_brief(report_of(q, d), now=NOW)
        self.assertEqual(brief.unresolved, ())


class TestBlocked(unittest.TestCase):
    def test_degewo_is_blocked_with_quoted_clause(self):
        entry = hunt_entry(degewo_notice(), SOLO)
        brief = build_brief(report_of(entry), now=NOW)
        self.assertEqual(len(brief.blocked), 1)
        b = brief.blocked[0]
        self.assertEqual(b.publication_number, "578580-2026")
        self.assertTrue(b.blocking_clause.strip())
        # the clause must be verbatim evidence, checked upstream by
        # QualificationResult itself -- this module only carries it.
        self.assertIn(b.blocking_clause,
                       " | ".join(entry.blocking_clauses))

    def test_qualified_and_unresolved_never_appear_blocked(self):
        q = hunt_entry(qualified_notice(), FULL)
        u = hunt_entry(bare_notice(), SOLO)
        brief = build_brief(report_of(q, u), now=NOW)
        self.assertEqual(brief.blocked, ())


class TestDeadlineFactKeys(unittest.TestCase):
    """A source that publishes perfectly good closing dates must not
    read as a source with none.

    Found live 2026-09-02: a multi-source brief put all 30 NZ GETS
    notices into ACTION REQUIRED as "closes in: UNKNOWN -- treat as
    urgent". GETS publishes a real closing date on every notice;
    `gets_signal()` carries it as `close_date` while `ted_signal()`
    uses `deadline`, and this module read only `deadline`.

    The failure direction was safe, which is exactly why it hid: it
    looked like the honest-unknown rule firing correctly, while the
    brief's most important section quietly filled with noise.
    """

    def _entry_with_facts(self, facts):
        eligibility = assess_eligibility(qualified_notice())
        operator = SOLO
        qualification = assess(eligibility, operator)
        signal = CanonicalSignal(
            signal_id="tender:test:222222-2026",
            source_id="test", source_type="OFFICIAL",
            source_ref="https://example.test",
            target="222222-2026", kind="DEMAND",
            claim="test notice", observed_at="2026-09-02T00:00:00+00:00",
            facts=facts,
        )
        return HuntEntry(
            publication_number=eligibility.publication_number,
            band=qualification.band, eligibility=eligibility,
            qualification=qualification, relevance=None, signal=signal)

    def _days(self, entry):
        report = HuntReport(entries=(entry,), fetched=1, assessed=1,
                            skipped=(), objective="test")
        brief = build_brief(report, now=NOW, closing_within_days=30)
        return brief.action_required[0].days_remaining

    def test_gets_close_date_key_is_read(self):
        entry = self._entry_with_facts(
            {"close_date": "Friday, 4 September 2026 5:00 PM +12:00"})
        self.assertIsNotNone(
            self._days(entry),
            "a GETS notice with a real close_date must not read as UNKNOWN")

    def test_ted_deadline_key_still_wins(self):
        entry = self._entry_with_facts(
            {"deadline": "2026-09-04T17:00:00+00:00",
             "close_date": "Friday, 30 October 2026 5:00 PM +12:00"})
        # `deadline` is first in priority order; the earlier date proves
        # it was the one used.
        self.assertEqual(self._days(entry), 2)

    def test_genuinely_absent_date_is_still_unknown(self):
        entry = self._entry_with_facts({"categories": "81110000"})
        self.assertIsNone(
            self._days(entry),
            "no date anywhere must still be UNKNOWN, not a fabricated one")

    def test_malformed_date_is_unknown_not_coerced(self):
        entry = self._entry_with_facts({"close_date": "sometime next spring"})
        self.assertIsNone(
            self._days(entry),
            "an unreadable date must stay UNKNOWN rather than be coerced "
            "into a plausible-looking wrong one")


class TestVocabularyDiscipline(unittest.TestCase):
    """The brief must never call an unassessed public notice a 'lead',
    an 'opportunity', or a 'prospect'. Checked against every section in
    a non-trivially populated brief, not just the header."""

    def _full_brief_text(self) -> str:
        qualified = hunt_entry(qualified_notice("222222-2026"), FULL,
                                deadline="2026-09-05T00:00:00Z")
        unresolved = hunt_entry(bare_notice("333333-2026"), SOLO)
        blocked = hunt_entry(degewo_notice(), SOLO)
        brief = build_brief(
            report_of(qualified, unresolved, blocked), now=NOW,
            closing_within_days=14,
            previous_publication_numbers=["000000-2026"])
        return render_brief(brief)

    def test_forbidden_words_absent(self):
        text = self._full_brief_text().lower()
        for word in ("lead", "opportunity", "prospect"):
            self.assertNotIn(word, text,
                              f"forbidden word {word!r} found in rendered brief")

    def test_empty_brief_also_clean(self):
        text = render_brief(build_brief(report_of(), now=NOW)).lower()
        for word in ("lead", "opportunity", "prospect"):
            self.assertNotIn(word, text)


class TestIntegrity(unittest.TestCase):
    def test_rejects_non_hunt_report(self):
        with self.assertRaises(BriefIntegrityError):
            build_brief("not a report", now=NOW)

    def test_rejects_non_datetime_now(self):
        with self.assertRaises(BriefIntegrityError):
            build_brief(report_of(), now="2026-09-02")

    def test_rejects_negative_window(self):
        with self.assertRaises(BriefIntegrityError):
            build_brief(report_of(), now=NOW, closing_within_days=-1)

    def test_render_rejects_non_brief(self):
        with self.assertRaises(BriefIntegrityError):
            render_brief("not a brief")

    def test_deadline_entry_rejects_disqualified_band(self):
        with self.assertRaises(BriefIntegrityError):
            DeadlineEntry(publication_number="1", band="DISQUALIFIED",
                          days_remaining=1, deadline_display="2026-09-03",
                          notice_url="")

    def test_deadline_entry_rejects_inconsistent_unknown(self):
        with self.assertRaises(BriefIntegrityError):
            DeadlineEntry(publication_number="1", band="QUALIFIED",
                          days_remaining=None, deadline_display="2026-09-03",
                          notice_url="")

    def test_deadline_entry_rejects_negative_days(self):
        with self.assertRaises(BriefIntegrityError):
            DeadlineEntry(publication_number="1", band="QUALIFIED",
                          days_remaining=-1, deadline_display="2026-09-03",
                          notice_url="")

    def test_unresolved_entry_rejects_blank_url(self):
        with self.assertRaises(BriefIntegrityError):
            UnresolvedEntry(publication_number="1", document_url="",
                            unresolved_dimensions=("certifications",))

    def test_unresolved_entry_rejects_no_dimensions(self):
        with self.assertRaises(BriefIntegrityError):
            UnresolvedEntry(publication_number="1", document_url="UNKNOWN",
                            unresolved_dimensions=())

    def test_blocked_entry_rejects_blank_clause(self):
        with self.assertRaises(BriefIntegrityError):
            BlockedEntry(publication_number="1", blocking_clause="")

    def test_brief_rejects_new_entries_without_prior_state(self):
        from foundation.brief import NewEntry
        with self.assertRaises(BriefIntegrityError):
            Brief(
                generated_at=NOW, objective="x", closing_within_days=14,
                action_required=(), has_previous_state=False,
                new_since_last=(NewEntry("1", "QUALIFIED", ""),),
                unresolved=(), blocked=(),
            )


if __name__ == "__main__":
    unittest.main()


class TestNoticeClassReachesTheBrief(unittest.TestCase):
    """`notice_class.py` classifies a notice as answerable-by-anyone or
    not. That distinction is worthless in a module nothing calls — this
    repository already documents four mouths that were built, tested,
    confidently documented, and reachable by nobody.

    Five Irish tenders closed at €400k–€2.6M turnover and three notices
    with no barrier at all scored INSUFFICIENT_DATA identically. Ranking
    them together tells the operator to spend equal attention on a door
    and a wall."""

    def test_market_engagement_reaches_the_rendered_brief(self):
        notice = qualified_notice()
        notice["notice-title"] = {"eng": ["Preliminary market engagement notice"]}
        entry = hunt_entry(notice, FULL, deadline="2026-09-09T12:00:00+00:00")
        text = render_brief(build_brief(report_of(entry), now=NOW,
                                        closing_within_days=30))
        self.assertIn("MARKET_ENGAGEMENT", text)

    def test_rolling_admission_reaches_the_rendered_brief(self):
        notice = qualified_notice()
        notice["notice-title"] = {"eng": ["Dynamic Purchasing System for X"]}
        entry = hunt_entry(notice, FULL, deadline="2026-09-09T12:00:00+00:00")
        text = render_brief(build_brief(report_of(entry), now=NOW,
                                        closing_within_days=30))
        self.assertIn("ROLLING_ADMISSION", text)

    def test_unclassifiable_notice_adds_no_class_line(self):
        """An unknown class must print nothing rather than the word
        UNKNOWN — the brief already carries UNKNOWN for deadlines, and a
        second unrelated UNKNOWN in the same block reads as one fact."""
        entry = hunt_entry(qualified_notice(), FULL,
                           deadline="2026-09-09T12:00:00+00:00")
        text = render_brief(build_brief(report_of(entry), now=NOW,
                                        closing_within_days=30))
        self.assertNotIn("class:", text)
