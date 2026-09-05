"""Tests for `foundation/mouth_nlnet.py` — the NLnet/NGI Zero grant source.

No network: fetch_fn injected. Honest: an unparseable deadline is None (UNKNOWN),
never guessed."""

import unittest
from datetime import date

from foundation.mouth_nlnet import (
    parse_deadline, fetch_open_call, NlnetCall, GRANT_RANGE,
)

PAGE = (b"<html><body>"
        b"<p>Submit your proposals. Next deadline November 3. 2026</p>"
        b"<p>R&D grants between 5.000 and 50.000 euro. Available to both "
        b"individuals and organisations.</p></body></html>")


class TestParseDeadline(unittest.TestCase):
    def test_parses_dotted_form(self):
        self.assertEqual(parse_deadline("Next deadline November 3. 2026"),
                         date(2026, 11, 3))

    def test_parses_comma_form(self):
        self.assertEqual(parse_deadline("deadline April 1, 2027"),
                         date(2027, 4, 1))

    def test_no_deadline_is_none_not_guessed(self):
        self.assertIsNone(parse_deadline("no dates here at all"))

    def test_bad_month_is_none(self):
        self.assertIsNone(parse_deadline("deadline Smarch 3 2026"))


class TestFetchOpenCall(unittest.TestCase):
    def test_returns_the_open_call_from_the_page(self):
        call = fetch_open_call(fetch_fn=lambda: PAGE)
        self.assertIsInstance(call, NlnetCall)
        self.assertEqual(call.deadline, date(2026, 11, 3))
        self.assertEqual(call.grant_range, GRANT_RANGE)
        self.assertIn("individuals", call.eligibility.lower())
        self.assertTrue(call.apply_url.startswith("https://nlnet.nl"))

    def test_unparseable_page_gives_unknown_deadline(self):
        call = fetch_open_call(fetch_fn=lambda: b"<html>no deadline</html>")
        self.assertIsNone(call.deadline)


if __name__ == "__main__":
    unittest.main()
