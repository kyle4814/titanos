"""Offline tests for foundation/currency.py. No test here fetches the
real ECB feed -- every RateTable is constructed in-memory or fed through
parse_rate_table() on inline bytes, per this cycle's mandate."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from foundation.currency import (
    Conversion,
    RateTable,
    RateTableError,
    STATUS_OK,
    STATUS_UNKNOWN,
    load_rate_table,
    parse_rate_table,
    to_eur,
)

REAL_SHAPE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
	<gesmes:subject>Reference rates</gesmes:subject>
	<gesmes:Sender>
		<gesmes:name>European Central Bank</gesmes:name>
	</gesmes:Sender>
	<Cube>
		<Cube time='2026-08-31'>
			<Cube currency='USD' rate='1.1596'/>
			<Cube currency='HUF' rate='364.35'/>
			<Cube currency='DKK' rate='7.4751'/>
		</Cube>
	</Cube>
</gesmes:Envelope>"""


def make_table(date_str="2026-08-31", rates=None) -> RateTable:
    return RateTable(date_str=date_str, rates=rates or {
        "USD": 1.1596, "HUF": 364.35, "DKK": 7.4751,
    })


class TestParseRateTable(unittest.TestCase):
    def test_parses_real_feed_shape(self):
        table = parse_rate_table(REAL_SHAPE_XML)
        self.assertEqual(table.date_str, "2026-08-31")
        self.assertEqual(table.rates["USD"], 1.1596)
        self.assertEqual(table.rates["HUF"], 364.35)
        self.assertNotIn("EUR", table.rates)

    def test_malformed_xml_is_structured_refusal_not_crash(self):
        with self.assertRaises(RateTableError):
            parse_rate_table(b"<not><valid xml")

    def test_missing_time_cube_is_structured_refusal(self):
        xml = b"<Cube><Cube><Cube currency='USD' rate='1.1'/></Cube></Cube>"
        with self.assertRaises(RateTableError):
            parse_rate_table(xml)

    def test_empty_rate_table_is_structured_refusal(self):
        xml = b"<Cube><Cube time='2026-08-31'></Cube></Cube>"
        with self.assertRaises(RateTableError):
            parse_rate_table(xml)

    def test_skips_bad_individual_entries_without_crashing(self):
        xml = (b"<Cube><Cube time='2026-08-31'>"
               b"<Cube currency='USD' rate='1.1'/>"
               b"<Cube currency='ZZZ' rate='not-a-number'/>"
               b"<Cube rate='2.0'/>"
               b"<Cube currency='' rate='3.0'/>"
               b"</Cube></Cube>")
        table = parse_rate_table(xml)
        self.assertEqual(table.rates, {"USD": 1.1})


class TestToEur(unittest.TestCase):
    def test_known_rate_converts_correctly(self):
        table = make_table()
        conv = to_eur(100.0, "USD", table)
        self.assertEqual(conv.status, STATUS_OK)
        self.assertAlmostEqual(conv.eur_amount, 100.0 / 1.1596)
        self.assertEqual(conv.rate_used, 1.1596)
        self.assertEqual(conv.rate_date, "2026-08-31")
        self.assertEqual(conv.original_amount, 100.0)
        self.assertEqual(conv.original_currency, "USD")

    def test_unknown_currency_yields_unknown_never_a_guess(self):
        table = make_table()
        conv = to_eur(500.0, "XYZ", table)
        self.assertEqual(conv.status, STATUS_UNKNOWN)
        self.assertIsNone(conv.eur_amount)
        self.assertIsNone(conv.rate_used)
        self.assertIsNone(conv.rate_date)
        # original is preserved even when unconvertible
        self.assertEqual(conv.original_amount, 500.0)
        self.assertEqual(conv.original_currency, "XYZ")

    def test_eur_converts_to_itself_exactly(self):
        table = make_table()
        conv = to_eur(250.0, "EUR", table)
        self.assertEqual(conv.status, STATUS_OK)
        self.assertEqual(conv.eur_amount, 250.0)
        self.assertEqual(conv.rate_used, 1.0)

    def test_currency_code_is_case_insensitive(self):
        table = make_table()
        conv = to_eur(100.0, "usd", table)
        self.assertEqual(conv.status, STATUS_OK)

    def test_stale_table_is_flagged_and_still_usable(self):
        from datetime import date
        old_table = RateTable(date_str="2020-01-01", rates={"USD": 1.1})
        self.assertTrue(old_table.is_stale(today=date(2026, 8, 31)))
        conv = to_eur(100.0, "USD", old_table)
        # still usable -- produces a real converted figure
        self.assertEqual(conv.status, STATUS_OK)
        self.assertIsNotNone(conv.eur_amount)
        # but visibly flagged as stale
        self.assertTrue(conv.stale)

    def test_fresh_table_is_not_flagged_stale(self):
        table = RateTable(date_str="2026-08-30", rates={"USD": 1.1})
        self.assertFalse(old_stale(table))

    def test_rate_and_date_travel_with_every_converted_figure(self):
        table = make_table()
        for amount, currency in [(1.0, "USD"), (1.0, "HUF"), (1.0, "DKK")]:
            conv = to_eur(amount, currency, table)
            self.assertIsNotNone(conv.rate_used)
            self.assertEqual(conv.rate_date, table.date_str)

    def test_original_is_never_replaced(self):
        table = make_table()
        conv = to_eur(900000000.0, "HUF", table)
        self.assertEqual(conv.original_amount, 900000000.0)
        self.assertEqual(conv.original_currency, "HUF")
        self.assertLess(conv.eur_amount, conv.original_amount)


def old_stale(table):
    from datetime import date
    return table.is_stale(today=date.fromisoformat(table.date_str))


class TestRateTableIsStale(unittest.TestCase):
    def test_within_window_not_stale(self):
        from datetime import date
        table = RateTable(date_str="2026-08-28", rates={"USD": 1.1})
        self.assertFalse(table.is_stale(today=date(2026, 8, 31)))

    def test_beyond_window_is_stale(self):
        from datetime import date
        table = RateTable(date_str="2026-08-20", rates={"USD": 1.1})
        self.assertTrue(table.is_stale(today=date(2026, 8, 31)))

    def test_unparseable_date_treated_as_stale(self):
        table = RateTable(date_str="not-a-date", rates={"USD": 1.1})
        self.assertTrue(table.is_stale())

    def test_future_dated_table_is_stale_not_eternally_fresh(self):
        """Blue-team pass 014: is_stale() only checked whether the table
        was OLDER than STALE_AFTER_DAYS. A table dated in the future
        makes `(ref - table_date).days` negative, which is never greater
        than STALE_AFTER_DAYS, so a future-dated table passed as fresh
        forever and every conversion from it looked current while being
        silently wrong. A table dated even one day ahead of `today` is
        already impossible for a real ECB publication and must be
        flagged, exactly like a too-old one."""
        from datetime import date
        future_table = RateTable(date_str="2027-06-01", rates={"USD": 1.1})
        self.assertTrue(future_table.is_stale(today=date(2026, 9, 2)))

    def test_far_future_dated_table_is_stale(self):
        from datetime import date
        table = RateTable(date_str="2026-09-10", rates={"USD": 1.1})
        self.assertTrue(table.is_stale(today=date(2026, 8, 31)))


class TestLoadRateTableCaching(unittest.TestCase):
    def test_fetches_once_and_caches_to_disk(self):
        calls = {"n": 0}

        def fake_fetch():
            calls["n"] += 1
            return REAL_SHAPE_XML

        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "rates.json"
            t1 = load_rate_table(cache_path=cache_path, fetch_fn=fake_fetch)
            t2 = load_rate_table(cache_path=cache_path, fetch_fn=fake_fetch)
            self.assertEqual(calls["n"], 1)  # second call hit the cache
            self.assertEqual(t1.date_str, t2.date_str)
            self.assertEqual(dict(t1.rates), dict(t2.rates))

    def test_force_refresh_refetches(self):
        calls = {"n": 0}

        def fake_fetch():
            calls["n"] += 1
            return REAL_SHAPE_XML

        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "rates.json"
            load_rate_table(cache_path=cache_path, fetch_fn=fake_fetch)
            load_rate_table(cache_path=cache_path, fetch_fn=fake_fetch,
                             force_refresh=True)
            self.assertEqual(calls["n"], 2)

    def test_fetch_failure_falls_back_to_existing_cache(self):
        from foundation.mouth_common import FetchError

        good_calls = {"n": 0}

        def good_fetch():
            good_calls["n"] += 1
            return REAL_SHAPE_XML

        def bad_fetch():
            raise FetchError("network down")

        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "rates.json"
            load_rate_table(cache_path=cache_path, fetch_fn=good_fetch)
            # force refresh with a failing fetch -- must degrade to cache,
            # not raise, since a cache already exists
            table = load_rate_table(cache_path=cache_path, fetch_fn=bad_fetch,
                                     force_refresh=True)
            self.assertEqual(table.date_str, "2026-08-31")

    def test_fetch_failure_with_no_cache_raises(self):
        from foundation.mouth_common import FetchError

        def bad_fetch():
            raise FetchError("network down")

        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "rates_missing.json"
            with self.assertRaises(RateTableError):
                load_rate_table(cache_path=cache_path, fetch_fn=bad_fetch)

    def test_cache_write_is_atomic_no_partial_file_on_crash_path(self):
        # The temp file is created alongside the target and only ever
        # reaches the target path via os.replace -- verified indirectly:
        # after a successful load, the cache file is valid JSON and no
        # .tmp-currency-cache-* file is left behind.
        def fetch():
            return REAL_SHAPE_XML

        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "rates.json"
            load_rate_table(cache_path=cache_path, fetch_fn=fetch)
            leftovers = list(Path(tmp).glob(".tmp-currency-cache-*"))
            self.assertEqual(leftovers, [])
            self.assertTrue(cache_path.exists())


if __name__ == "__main__":
    unittest.main()


class TestHostileRatesAreRefused(unittest.TestCase):
    """Blue-team pass 014. `rate <= 0` is not enough.

    Every comparison involving NaN is False, so `NaN <= 0` is False and NaN
    passed the filter. Infinity is genuinely greater than zero and also
    passed. Both were accepted from a crafted ECB feed:

        rate NaN       -> status=OK, eur_amount=nan
        rate Infinity  -> status=OK, eur_amount=0.0

    The Infinity case is the worse one: it silently turns a million-euro
    contract into zero, which sorts quietly to the bottom of the operator's
    ranked list instead of announcing itself. NaN at least looks wrong.
    """

    def _feed(self, rate_text):
        return (
            '<?xml version="1.0"?><gesmes:Envelope '
            'xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01" '
            'xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
            '<Cube><Cube time="2026-08-31">'
            f'<Cube currency="ZZZ" rate="{rate_text}"/>'
            '<Cube currency="USD" rate="1.1596"/>'
            '</Cube></Cube></gesmes:Envelope>').encode()

    def test_nan_and_infinity_rates_are_not_accepted(self):
        for bad in ("NaN", "Infinity", "-Infinity", "-5", "0"):
            with self.subTest(rate=bad):
                table = parse_rate_table(self._feed(bad))
                self.assertNotIn("ZZZ", table.rates,
                                 f"rate {bad!r} was accepted into the table")
                self.assertIn("USD", table.rates,
                              "a hostile rate must not discard the good ones")

    def test_a_string_rate_from_a_corrupted_cache_does_not_crash(self):
        """The on-disk cache was read without validation, so a string-typed
        rate reached the arithmetic and raised an unhandled TypeError --
        contradicting this module's own never-crash contract."""
        table = RateTable(date_str="2026-08-31",
                          rates={"ZZZ": "not-a-number"}, fetched_at="x")
        result = to_eur(1000, "ZZZ", table)
        self.assertEqual(result.status, STATUS_UNKNOWN)
        self.assertIsNone(result.eur_amount)
