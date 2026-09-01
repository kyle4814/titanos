import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from foundation import opportunity_watch as ow
from foundation.signal_spine import CanonicalSignal


def _signal(signal_id, deadline="", buyer_safe="Buyer", title_safe="Title",
            source_id="tender_radar_eu_ted", extra_facts=None,
            extra_evidence=None):
    facts = {"deadline": deadline}
    if extra_facts:
        facts.update(extra_facts)
    evidence = {
        "buyer_name_safe": buyer_safe,
        "title_safe": title_safe,
        "deadline": deadline,
        "tender_id": signal_id,
    }
    if extra_evidence:
        evidence.update(extra_evidence)
    return CanonicalSignal(
        signal_id=signal_id,
        source_id=source_id,
        source_type="OFFICIAL",
        source_ref=f"https://example/{signal_id}",
        target=buyer_safe,
        kind="DEMAND",
        claim="open tender for testing",
        observed_at=datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
        target_established_by="SOURCE_NATIVE",
        facts=facts,
        evidence=evidence,
        pressure_class="EXPLICIT_DEMAND",
        pressure_evidence="a public notice stating intent to purchase",
    )


NOW = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)


class DeadlineClassificationTests(unittest.TestCase):
    def test_absent_deadline_is_unknown(self):
        info = ow.classify_deadline(_signal("s1", deadline=""), now=NOW)
        self.assertEqual(info.status, "UNKNOWN")
        self.assertIsNone(info.parsed)

    def test_malformed_deadline_is_unknown(self):
        info = ow.classify_deadline(_signal("s1", deadline="not-a-date"), now=NOW)
        self.assertEqual(info.status, "UNKNOWN")
        self.assertIsNone(info.parsed)

    def test_past_deadline_is_expired_not_dropped(self):
        info = ow.classify_deadline(
            _signal("s1", deadline="2020-01-01T00:00:00Z"), now=NOW)
        self.assertEqual(info.status, "EXPIRED")
        self.assertIsNotNone(info.parsed)
        self.assertEqual(info.raw, "2020-01-01T00:00:00Z")

    def test_future_deadline_is_future(self):
        info = ow.classify_deadline(
            _signal("s1", deadline="2026-12-01T00:00:00Z"), now=NOW)
        self.assertEqual(info.status, "FUTURE")

    def test_deadline_exactly_now_is_future_inclusive(self):
        info = ow.classify_deadline(
            _signal("s1", deadline=NOW.isoformat()), now=NOW)
        self.assertEqual(info.status, "FUTURE")

    def test_z_suffix_and_offset_both_parse(self):
        z = ow.classify_deadline(_signal("s1", deadline="2026-09-09T12:00:00Z"), now=NOW)
        offset = ow.classify_deadline(
            _signal("s2", deadline="2026-09-09T15:00:00+03:00"), now=NOW)
        self.assertEqual(z.status, "FUTURE")
        self.assertEqual(offset.status, "FUTURE")
        # 15:00+03:00 == 12:00Z -- same instant, must compare equal.
        self.assertEqual(z.parsed, offset.parsed)

    def test_naive_deadline_treated_as_utc(self):
        info = ow.classify_deadline(
            _signal("s1", deadline="2026-12-01T00:00:00"), now=NOW)
        self.assertEqual(info.status, "FUTURE")
        self.assertIsNotNone(info.parsed.tzinfo)


class TimezoneOrderingTests(unittest.TestCase):
    def test_offsets_sort_correctly_against_each_other_and_utc(self):
        # All three are the same real instant, expressed three ways.
        # A naive/aware bug would silently mis-sort or crash here.
        signals = [
            _signal("s_utc", deadline="2026-09-10T10:00:00Z"),
            _signal("s_plus2", deadline="2026-09-10T12:00:00+02:00"),
            _signal("s_minus5", deadline="2026-09-10T05:00:00-05:00"),
        ]
        entries = ow.closing_within(signals, days=30, now=NOW)
        # Same instant -> all three included, tie-break by signal_id.
        self.assertEqual(len(entries), 3)
        ids = [e.signal_id for e in entries]
        self.assertEqual(ids, sorted(ids))
        deadlines = {e.deadline for e in entries}
        self.assertEqual(len(deadlines), 1)

    def test_earlier_offset_deadline_sorts_before_later_utc_deadline(self):
        signals = [
            _signal("s_later", deadline="2026-09-20T00:00:00Z"),
            _signal("s_earlier", deadline="2026-09-05T23:00:00-01:00"),  # == 09-06T00:00Z
        ]
        entries = ow.closing_within(signals, days=30, now=NOW)
        self.assertEqual([e.signal_id for e in entries], ["s_earlier", "s_later"])


class ClosingWithinTests(unittest.TestCase):
    def test_boundary_inclusive_exact_edge(self):
        window_end = NOW + timedelta(days=10)
        signals = [_signal("s1", deadline=window_end.isoformat())]
        entries = ow.closing_within(signals, days=10, now=NOW)
        self.assertEqual(len(entries), 1)

    def test_boundary_excludes_one_microsecond_past(self):
        just_past = NOW + timedelta(days=10, microseconds=1)
        signals = [_signal("s1", deadline=just_past.isoformat())]
        entries = ow.closing_within(signals, days=10, now=NOW)
        self.assertEqual(len(entries), 0)

    def test_expired_never_appears_in_closing_within(self):
        signals = [_signal("s1", deadline="2020-01-01T00:00:00Z")]
        entries = ow.closing_within(signals, days=3650, now=NOW)
        self.assertEqual(entries, ())

    def test_unknown_never_appears_in_closing_within(self):
        signals = [_signal("s1", deadline="")]
        entries = ow.closing_within(signals, days=99999, now=NOW)
        self.assertEqual(entries, ())

    def test_sorted_soonest_first(self):
        signals = [
            _signal("far", deadline="2026-09-25T00:00:00Z"),
            _signal("near", deadline="2026-09-05T00:00:00Z"),
            _signal("mid", deadline="2026-09-15T00:00:00Z"),
        ]
        entries = ow.closing_within(signals, days=30, now=NOW)
        self.assertEqual([e.signal_id for e in entries], ["near", "mid", "far"])

    def test_negative_days_rejected(self):
        with self.assertRaises(ValueError):
            ow.closing_within([], days=-1, now=NOW)


class NewSinceTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.state_path = Path(self._tmpdir.name) / "watch_state.json"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_first_run_everything_is_new(self):
        signals = [_signal("s1"), _signal("s2"), _signal("s3")]
        result = ow.new_since(signals, self.state_path, now=NOW)
        self.assertEqual({s.signal_id for s in result.new}, {"s1", "s2", "s3"})
        self.assertTrue(self.state_path.exists())

    def test_second_identical_run_yields_nothing_new(self):
        signals = [_signal("s1"), _signal("s2")]
        ow.new_since(signals, self.state_path, now=NOW)
        result = ow.new_since(signals, self.state_path, now=NOW)
        self.assertEqual(result.new, ())

    def test_partial_overlap_only_new_ones_returned(self):
        ow.new_since([_signal("s1"), _signal("s2")], self.state_path, now=NOW)
        result = ow.new_since(
            [_signal("s1"), _signal("s2"), _signal("s3")], self.state_path, now=NOW)
        self.assertEqual({s.signal_id for s in result.new}, {"s3"})

    def test_empty_signals_is_valid_not_an_error(self):
        result = ow.new_since([], self.state_path, now=NOW)
        self.assertEqual(result.new, ())
        self.assertEqual(result.total_seen_after, 0)

    def test_missing_state_file_treated_as_first_run(self):
        self.assertFalse(self.state_path.exists())
        result = ow.new_since([_signal("s1")], self.state_path, now=NOW)
        self.assertEqual(len(result.new), 1)

    def test_corrupt_state_file_treated_as_empty_not_fatal(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text("{not valid json", encoding="utf-8")
        result = ow.new_since([_signal("s1")], self.state_path, now=NOW)
        self.assertEqual(len(result.new), 1)

    def test_crash_between_read_and_write_does_not_lose_track(self):
        # First run publishes s1, s2 as seen.
        ow.new_since([_signal("s1"), _signal("s2")], self.state_path, now=NOW)
        before = self.state_path.read_text(encoding="utf-8")

        # Simulate a crash during the atomic publish of the second run:
        # os.replace raises after the temp file was written but before
        # the rename lands. The prior state must be completely untouched.
        with patch("foundation.opportunity_watch.os.replace",
                   side_effect=OSError("simulated crash")):
            with self.assertRaises(OSError):
                ow.new_since(
                    [_signal("s1"), _signal("s2"), _signal("s3")],
                    self.state_path, now=NOW)

        after = self.state_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)

        # No leftover temp file from the aborted write.
        leftovers = [p for p in self.state_path.parent.iterdir()
                     if p.name.startswith(".tmp-opportunity-watch-")]
        self.assertEqual(leftovers, [])

        # The next (non-crashing) run must still see s3 as new -- the
        # crash cost nothing, because nothing was ever durably marked.
        result = ow.new_since(
            [_signal("s1"), _signal("s2"), _signal("s3")], self.state_path, now=NOW)
        self.assertEqual({s.signal_id for s in result.new}, {"s3"})

    def test_crash_on_first_run_leaves_no_state_file(self):
        with patch("foundation.opportunity_watch.os.replace",
                   side_effect=OSError("simulated crash")):
            with self.assertRaises(OSError):
                ow.new_since([_signal("s1")], self.state_path, now=NOW)
        self.assertFalse(self.state_path.exists())
        # Next run still sees s1 as new.
        result = ow.new_since([_signal("s1")], self.state_path, now=NOW)
        self.assertEqual(len(result.new), 1)


class WatchReportTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.state_path = Path(self._tmpdir.name) / "watch_state.json"

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_combined_report_sections(self):
        signals = [
            _signal("new_and_closing", deadline="2026-09-05T00:00:00Z"),
            _signal("closing_only", deadline="2026-09-10T00:00:00Z"),
            _signal("expired", deadline="2020-01-01T00:00:00Z"),
            _signal("unknown", deadline=""),
        ]
        # Pre-seed "closing_only" as already seen.
        ow.new_since([_signal("closing_only", deadline="2026-09-10T00:00:00Z")],
                     self.state_path, now=NOW)

        report = ow.watch_report(signals, self.state_path, days=30, now=NOW)

        self.assertEqual(
            {e.signal_id for e in report.new_and_closing}, {"new_and_closing"})
        self.assertEqual(
            {e.signal_id for e in report.closing_soon},
            {"new_and_closing", "closing_only"})
        self.assertEqual(
            {e.signal_id for e in report.new},
            {"new_and_closing", "expired", "unknown"})
        self.assertEqual({e.signal_id for e in report.expired}, {"expired"})
        self.assertEqual({e.signal_id for e in report.unknown_deadline}, {"unknown"})

    def test_render_watch_never_raises_and_has_header_discipline(self):
        report = ow.watch_report([], self.state_path, days=30, now=NOW)
        text = ow.render_watch(report)
        self.assertIn("NOT LEADS. NOT OPPORTUNITIES. NOT REVENUE.", text)
        self.assertIn("(none)", text)

    def test_render_watch_with_entries_contains_expected_sections(self):
        signals = [_signal("s1", deadline="2026-09-05T00:00:00Z")]
        report = ow.watch_report(signals, self.state_path, days=30, now=NOW)
        text = ow.render_watch(report)
        self.assertIn("CLOSING WITHIN 30 DAYS", text)
        self.assertIn("NEW SINCE LAST RUN", text)
        self.assertIn("EXPIRED, STILL IN CORPUS", text)
        self.assertIn("UNKNOWN DEADLINE", text)


if __name__ == "__main__":
    unittest.main()
