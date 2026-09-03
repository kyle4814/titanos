"""Tests for `foundation/ops_digest.py`.

Offline; no socket. These pin the disciplines the digest exists to keep:
every card is actionable and sourced, the money-winnable items sort to the
top, and no Telegram message can silently exceed the 4096-char limit or
truncate a figure.
"""

import unittest
from datetime import datetime, timezone

from foundation.ops_digest import (
    OPPORTUNITIES,
    STATUS_ORDER,
    Opportunity,
    OpsDigestError,
    format_phone_markdown,
    live_opportunities,
    render_portfolio_header,
    render_telegram_html,
)


def _opp(**kw):
    base = dict(opp_id="X", title="T", what="W", value="$1", gate="None",
                status="ACTIONABLE_NOW", deadline="None (standing)",
                link="https://example.org", actions=("do it",),
                source_ref="OPS_BOARD.md §x")
    base.update(kw)
    return Opportunity(**base)


class TestRosterIntegrity(unittest.TestCase):
    def test_every_opportunity_validates(self):
        # Construction itself enforces the invariants; a broken roster
        # would fail at import. This asserts the roster is non-trivial.
        self.assertGreaterEqual(len(OPPORTUNITIES), 10)

    def test_every_card_has_a_source_and_actions(self):
        for o in OPPORTUNITIES:
            self.assertTrue(o.source_ref.strip(), o.opp_id)
            self.assertTrue(o.actions, o.opp_id)

    def test_opp_ids_are_unique(self):
        ids = [o.opp_id for o in OPPORTUNITIES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_a_bad_status_is_refused(self):
        with self.assertRaises(OpsDigestError):
            _opp(status="LOOKS_GREAT")

    def test_an_empty_required_field_is_refused(self):
        with self.assertRaises(OpsDigestError):
            _opp(value="   ")

    def test_a_card_with_no_actions_is_refused(self):
        with self.assertRaises(OpsDigestError):
            _opp(actions=())


class TestOrdering(unittest.TestCase):
    def test_actionable_now_sorts_ahead_of_watch(self):
        opps = live_opportunities()
        statuses = [STATUS_ORDER.index(o.status) for o in opps]
        self.assertEqual(statuses, sorted(statuses))

    def test_a_dated_item_sorts_by_soonest_within_its_band(self):
        a = _opp(opp_id="A", status="ACT_SOON", deadline="2026-11-03")
        b = _opp(opp_id="B", status="ACT_SOON", deadline="2026-09-14 16:00 UTC")
        # reuse the module's key indirectly via live sort semantics
        from foundation.ops_digest import _deadline_sort_key
        self.assertLess(_deadline_sort_key(b.deadline),
                        _deadline_sort_key(a.deadline))

    def test_standing_sorts_after_a_real_date(self):
        from foundation.ops_digest import _deadline_sort_key
        self.assertLess(_deadline_sort_key("2026-09-14"),
                        _deadline_sort_key("None (standing)"))


class TestTelegramRender(unittest.TestCase):
    NOW = datetime(2026, 9, 4, 6, 0, tzinfo=timezone.utc)

    def test_header_plus_one_message_per_opportunity(self):
        msgs = render_telegram_html(now=self.NOW)
        self.assertEqual(len(msgs), len(OPPORTUNITIES) + 1)

    def test_no_message_exceeds_telegram_limit(self):
        for m in render_telegram_html(now=self.NOW):
            self.assertLessEqual(len(m), 4096)

    def test_every_card_carries_its_value_and_link(self):
        msgs = render_telegram_html(now=self.NOW)[1:]
        for o, m in zip(live_opportunities(), msgs):
            self.assertIn(o.link, m)
            self.assertIn("Value:", m)
            self.assertIn("Do this:", m)

    def test_html_special_chars_are_escaped(self):
        o = _opp(title="A & B <script>", what="x < y & z")
        from foundation.ops_digest import _render_one_html
        out = _render_one_html(o, 1, 1)
        self.assertNotIn("<script>", out)
        self.assertIn("&amp;", out)

    def test_an_oversized_card_raises_rather_than_truncates(self):
        o = _opp(what="A" * 5000)
        from foundation.ops_digest import _render_one_html
        with self.assertRaises(OpsDigestError):
            _render_one_html(o, 1, 1)

    def test_header_counts_the_bands(self):
        header = render_portfolio_header(live_opportunities(), now=self.NOW)
        self.assertIn("MONEY-PRINTER", header)
        self.assertIn("live opportunities", header)


class TestDeadlineExpiry(unittest.TestCase):
    """A passed deadline must never keep showing as DO NOW / ACT SOON —
    the one way the digest could actively mislead Kyle."""

    PAST = datetime(2027, 1, 1, tzinfo=timezone.utc)   # after every dated item
    BEFORE_BRADFORD = datetime(2026, 9, 4, tzinfo=timezone.utc)

    def test_iso_deadline_parses(self):
        from foundation.ops_digest import _parse_deadline_date
        self.assertEqual(_parse_deadline_date("2026-09-14 16:00 UTC"),
                         __import__("datetime").date(2026, 9, 14))

    def test_day_month_year_parses(self):
        from foundation.ops_digest import _parse_deadline_date
        import datetime as dt
        self.assertEqual(_parse_deadline_date("6 April 2029"),
                         dt.date(2029, 4, 6))

    def test_month_year_parses_conservatively_to_first(self):
        from foundation.ops_digest import _parse_deadline_date
        import datetime as dt
        self.assertEqual(_parse_deadline_date("Open for application till Feb 2029"),
                         dt.date(2029, 2, 1))

    def test_standing_and_unparseable_never_expire(self):
        o = _opp(deadline="None (standing)")
        self.assertFalse(o.is_expired(self.PAST))
        o2 = _opp(deadline="PQQ closes 'Before Jan 2029'")
        # 'Before Jan 2029' -> parses to Jan 2029; not yet past at BEFORE_BRADFORD
        self.assertFalse(o2.is_expired(self.BEFORE_BRADFORD))

    def test_a_passed_iso_deadline_expires(self):
        o = _opp(status="ACT_SOON", deadline="2026-09-14 16:00 UTC")
        self.assertFalse(o.is_expired(self.BEFORE_BRADFORD))
        self.assertTrue(o.is_expired(self.PAST))

    def test_expired_card_downgrades_to_watch(self):
        o = _opp(status="ACTIONABLE_NOW", deadline="2026-09-14")
        self.assertEqual(o.effective_status(self.PAST), "WATCH")
        self.assertEqual(o.badge(self.PAST), "⏱ CLOSED")

    def test_expired_card_hides_its_action_steps(self):
        # An expired card must not present "Do this" steps as if live.
        from foundation.ops_digest import _render_one_html
        o = _opp(status="ACT_SOON", deadline="2026-09-14", actions=("bid now",))
        html = _render_one_html(o, 1, 1, now=self.PAST)
        self.assertIn("CLOSED", html)
        self.assertNotIn("Do this", html)
        self.assertNotIn("bid now", html)

    def test_real_roster_has_no_expired_item_today(self):
        # Sanity: as written, nothing in the shipped roster is already
        # past — if this fails, an opportunity closed and the roster needs
        # updating (which is exactly the signal we want).
        now = datetime(2026, 9, 3, tzinfo=timezone.utc)
        self.assertEqual([o.opp_id for o in OPPORTUNITIES if o.is_expired(now)], [])


class TestPhoneMarkdown(unittest.TestCase):
    def test_markdown_lists_every_opportunity_with_links(self):
        md = format_phone_markdown(now=datetime(2026, 9, 4, tzinfo=timezone.utc))
        for o in OPPORTUNITIES:
            self.assertIn(o.title, md)
            self.assertIn(o.link, md)

    def test_markdown_carries_provenance(self):
        md = format_phone_markdown()
        self.assertIn("source:", md)


if __name__ == "__main__":
    unittest.main()
