"""Tests for `foundation/deal_pipeline.py`. Offline; this module has no
network path at all."""

import inspect
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from foundation import deal_pipeline
from foundation.deal_pipeline import (
    NOT_OBSERVED,
    STAGES,
    TERMINAL_STAGES,
    Deal,
    DealBoard,
    DealError,
    append_deal_event,
    load_deals,
    render_pipeline,
)


NOW = datetime(2026, 9, 3, 12, 0, 0, tzinfo=timezone.utc)


def iso(days_ago: int) -> str:
    return (NOW - timedelta(days=days_ago)).isoformat()


class TempLog:
    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        return Path(self._tmp.name) / "deals.jsonl"

    def __exit__(self, *exc):
        self._tmp.cleanup()


class TestDealRequiresRealSubstance(unittest.TestCase):
    def test_a_deal_must_name_a_counterparty(self):
        with self.assertRaises(DealError):
            Deal(deal_id="d1", counterparty="  ", lane="subcontract",
                 stage="IDENTIFIED", next_action="email them",
                 opened_at=iso(0), updated_at=iso(0))

    def test_a_live_deal_must_carry_a_next_action(self):
        """A deal with no next action is not being worked, it is being
        forgotten. That is the state this module exists to make
        impossible to hold silently."""
        with self.assertRaises(DealError):
            Deal(deal_id="d1", counterparty="Pulse Security", lane="subcontract",
                 stage="APPROACHED", next_action="", opened_at=iso(0),
                 updated_at=iso(0))

    def test_a_terminal_deal_needs_no_next_action(self):
        d = Deal(deal_id="d1", counterparty="Pulse Security", lane="subcontract",
                 stage="LOST", next_action="", opened_at=iso(9),
                 updated_at=iso(0))
        self.assertTrue(d.is_terminal)


class TestMoneyIsNeverOptimistic(unittest.TestCase):
    """MODELLED != OBSERVED != VERIFIED != REALIZED, enforced rather
    than restated."""

    def test_default_money_is_not_observed(self):
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="IDENTIFIED",
                 next_action="a", opened_at=iso(0), updated_at=iso(0))
        self.assertEqual(d.money_observed, NOT_OBSERVED)

    def test_money_cannot_be_recorded_before_a_deal_is_won(self):
        with self.assertRaises(DealError):
            Deal(deal_id="d1", counterparty="X", lane="l", stage="PROPOSED",
                 next_action="a", opened_at=iso(0), updated_at=iso(0),
                 money_observed="5000 AUD")

    def test_won_deal_may_record_a_real_number(self):
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="WON",
                 next_action="", opened_at=iso(9), updated_at=iso(0),
                 money_observed="5000 AUD")
        self.assertEqual(d.money_observed, "5000 AUD")

    def test_zero_is_refused_as_observed_money(self):
        """Zero is a measured value. An unagreed amount is not zero."""
        with self.assertRaises(DealError):
            Deal(deal_id="d1", counterparty="X", lane="l", stage="WON",
                 next_action="", opened_at=iso(9), updated_at=iso(0),
                 money_observed="0 AUD")

    def test_garbage_money_is_refused(self):
        with self.assertRaises(DealError):
            Deal(deal_id="d1", counterparty="X", lane="l", stage="WON",
                 next_action="", opened_at=iso(9), updated_at=iso(0),
                 money_observed="lots")


class TestForwardOnly(unittest.TestCase):
    """A pipeline that can be walked backwards is a pipeline that can be
    made to look better than it is."""

    def test_forward_movement_is_allowed(self):
        with TempLog() as log:
            append_deal_event(log, deal_id="d1", counterparty="Volkis",
                              lane="subcontract", stage="IDENTIFIED",
                              next_action="find contact", now=iso(3))
            d = append_deal_event(log, deal_id="d1", counterparty="Volkis",
                                  lane="subcontract", stage="APPROACHED",
                                  next_action="await reply", now=iso(1))
        self.assertEqual(d.stage, "APPROACHED")

    def test_backwards_movement_is_refused(self):
        with TempLog() as log:
            append_deal_event(log, deal_id="d1", counterparty="Volkis",
                              lane="subcontract", stage="PROPOSED",
                              next_action="await decision", now=iso(2))
            with self.assertRaises(DealError):
                append_deal_event(log, deal_id="d1", counterparty="Volkis",
                                  lane="subcontract", stage="IDENTIFIED",
                                  next_action="x", now=iso(0))

    def test_a_closed_deal_cannot_be_reopened(self):
        with TempLog() as log:
            append_deal_event(log, deal_id="d1", counterparty="X", lane="l",
                              stage="LOST", next_action="", now=iso(2))
            with self.assertRaises(DealError):
                append_deal_event(log, deal_id="d1", counterparty="X",
                                  lane="l", stage="IN_DIALOGUE",
                                  next_action="y", now=iso(0))

    def test_any_live_deal_may_be_lost_or_parked(self):
        with TempLog() as log:
            append_deal_event(log, deal_id="d1", counterparty="X", lane="l",
                              stage="IDENTIFIED", next_action="a", now=iso(5))
            d = append_deal_event(log, deal_id="d1", counterparty="X",
                                  lane="l", stage="PARKED", next_action="",
                                  now=iso(0))
        self.assertEqual(d.stage, "PARKED")


class TestDurability(unittest.TestCase):
    """This repository documents six stores calling themselves
    append-only ledgers while holding a dict that dies on exit. This is
    not a seventh."""

    def test_state_survives_with_no_shared_python_state(self):
        with TempLog() as log:
            append_deal_event(log, deal_id="d1", counterparty="Pulse Security",
                              lane="subcontract", stage="APPROACHED",
                              next_action="await reply", now=iso(2))
            raw = log.read_text(encoding="utf-8")
            self.assertIn("Pulse Security", raw)
            reloaded = load_deals(log)
        self.assertEqual(reloaded["d1"].counterparty, "Pulse Security")

    def test_later_event_supersedes_earlier(self):
        with TempLog() as log:
            append_deal_event(log, deal_id="d1", counterparty="X", lane="l",
                              stage="IDENTIFIED", next_action="a", now=iso(4))
            append_deal_event(log, deal_id="d1", counterparty="X", lane="l",
                              stage="IN_DIALOGUE", next_action="b", now=iso(1))
            self.assertEqual(load_deals(log)["d1"].stage, "IN_DIALOGUE")

    def test_opened_at_is_preserved_across_events(self):
        with TempLog() as log:
            first = append_deal_event(log, deal_id="d1", counterparty="X",
                                      lane="l", stage="IDENTIFIED",
                                      next_action="a", now=iso(9))
            later = append_deal_event(log, deal_id="d1", counterparty="X",
                                      lane="l", stage="APPROACHED",
                                      next_action="b", now=iso(0))
        self.assertEqual(first.opened_at, later.opened_at)

    def test_a_malformed_line_does_not_break_the_log(self):
        with TempLog() as log:
            append_deal_event(log, deal_id="d1", counterparty="X", lane="l",
                              stage="IDENTIFIED", next_action="a", now=iso(1))
            with log.open("a", encoding="utf-8") as fh:
                fh.write("{not json\n")
            self.assertEqual(len(load_deals(log)), 1)

    def test_missing_log_is_empty_not_an_error(self):
        with TempLog() as log:
            self.assertEqual(load_deals(log), {})


class TestStaleness(unittest.TestCase):
    """The deal most likely to die is the one nobody has touched."""

    def _board(self, *deals):
        return DealBoard(deals=tuple(deals))

    def test_untouched_deal_is_stale(self):
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="APPROACHED",
                 next_action="chase", opened_at=iso(30), updated_at=iso(11))
        self.assertIn(d, self._board(d).stale(7, NOW))

    def test_recent_deal_is_not_stale(self):
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="APPROACHED",
                 next_action="chase", opened_at=iso(3), updated_at=iso(1))
        self.assertNotIn(d, self._board(d).stale(7, NOW))

    def test_unknown_age_sorts_as_stale_not_fresh(self):
        """Being wrong toward looking again is cheap. Being wrong the
        other way is how a deal dies of silence."""
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="APPROACHED",
                 next_action="chase", opened_at="???", updated_at="not-a-date")
        self.assertIsNone(d.days_since_update(NOW))
        self.assertIn(d, self._board(d).stale(7, NOW))

    def test_terminal_deals_are_never_stale(self):
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="WON",
                 next_action="", opened_at=iso(90), updated_at=iso(60),
                 money_observed="1000 AUD")
        self.assertEqual(self._board(d).stale(7, NOW), ())


class TestNoOutwardAction(unittest.TestCase):
    """This module tracks approaches. It must be structurally incapable
    of making one."""

    FORBIDDEN = ("send", "email", "contact", "apply", "submit", "notify",
                 "publish", "register", "subscribe", "post", "message")

    def test_no_public_callable_names_an_outbound_verb(self):
        for name in deal_pipeline.__all__:
            obj = getattr(deal_pipeline, name)
            if not callable(obj):
                continue
            for bad in self.FORBIDDEN:
                self.assertNotIn(bad, name.lower(),
                                 f"{name!r} contains outbound verb {bad!r}")

    def test_no_module_level_function_names_an_outbound_verb(self):
        for name, obj in inspect.getmembers(deal_pipeline, inspect.isfunction):
            if obj.__module__ != deal_pipeline.__name__:
                continue
            for bad in self.FORBIDDEN:
                self.assertNotIn(bad, name.lower(),
                                 f"{name!r} contains outbound verb {bad!r}")

    def test_module_imports_no_network_library(self):
        src = Path(deal_pipeline.__file__).read_text(encoding="utf-8")
        for lib in ("urllib", "requests", "socket", "http.client"):
            self.assertNotIn(f"import {lib}", src)


class TestRender(unittest.TestCase):
    def test_empty_board_says_so_without_apology(self):
        text = render_pipeline(DealBoard(), now=NOW)
        self.assertIn("No live deals", text)
        self.assertIn("real state, not an error", text)

    def test_stale_deals_are_flagged_and_lead(self):
        fresh = Deal(deal_id="d2", counterparty="Fresh Co", lane="l",
                     stage="APPROACHED", next_action="wait",
                     opened_at=iso(2), updated_at=iso(1))
        stale = Deal(deal_id="d1", counterparty="Stale Co", lane="l",
                     stage="APPROACHED", next_action="chase",
                     opened_at=iso(40), updated_at=iso(20))
        text = render_pipeline(DealBoard(deals=(fresh, stale)), now=NOW)
        self.assertIn("STALE", text)
        self.assertLess(text.index("Stale Co"), text.index("Fresh Co"))

    def test_render_states_no_deal_has_been_won(self):
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="APPROACHED",
                 next_action="a", opened_at=iso(2), updated_at=iso(1))
        text = render_pipeline(DealBoard(deals=(d,)), now=NOW)
        self.assertIn("No deal has been won", text)

    def test_render_states_what_money_is_not(self):
        text = render_pipeline(DealBoard(), now=NOW)
        self.assertIn("a verbal yes is not revenue", text)

    def test_render_always_shows_the_next_action(self):
        d = Deal(deal_id="d1", counterparty="X", lane="l", stage="APPROACHED",
                 next_action="chase the reply", opened_at=iso(2),
                 updated_at=iso(1))
        self.assertIn("chase the reply",
                      render_pipeline(DealBoard(deals=(d,)), now=NOW))

    def test_render_rejects_a_non_board(self):
        with self.assertRaises(DealError):
            render_pipeline("not a board")


class TestStageContract(unittest.TestCase):
    def test_won_is_the_last_forward_stage(self):
        self.assertEqual(STAGES[-1], "WON")

    def test_terminal_stages_are_the_three_endings(self):
        self.assertEqual(set(TERMINAL_STAGES), {"WON", "LOST", "PARKED"})

    def test_unknown_stage_is_refused(self):
        with self.assertRaises(DealError):
            Deal(deal_id="d1", counterparty="X", lane="l", stage="MAYBE",
                 next_action="a", opened_at=iso(0), updated_at=iso(0))


if __name__ == "__main__":
    unittest.main()
