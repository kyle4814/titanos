"""Tests for `foundation/hunt_loop.py`. Offline only -- every test here
uses `fetch_notices_fn` to inject notices; nothing opens a socket."""

import inspect
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from foundation import hunt_loop
from foundation.hunt_loop import (
    DEFAULT_DEADLINE_WINDOW_DAYS,
    HuntCycleResult,
    HuntEntrySnapshot,
    load_hunt_state,
    render_hunt_cycle,
    run_hunt_loop,
    run_one_hunt_cycle,
)
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

CAP = CapabilityProfile(
    name="pentest", declared_by="operator",
    keywords=frozenset({"security"}),
)

NOW = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)


def notice(pn, deadline="", title="Security assessment services"):
    """A bare notice (no bidder conditions) in TED's REAL raw shape --
    the hyphenated field names the API actually returns.

    This fixture used to carry flat `key`/`title`/`deadline` keys as
    well, because `hunt()` passed the raw notice straight to
    `ted_signal()`, which reads the flat shape `mouth_ted.parse_items()`
    produces. That was a real defect in `hunt.py` -- every signal it
    built had an empty deadline -- and this fixture was modelling the
    defect rather than the API, so these tests passed against behaviour
    that could never occur on a live fetch.

    `hunt()` now re-shapes notices through `parse_items()` before
    building a signal, so the raw shape below is what both a real fetch
    and this module actually see. A fixture must never be the reason a
    test agrees with broken code.
    """
    raw = {
        "publication-number": pn,
        "notice-title": {"eng": [title]},
        "buyer-name": {"eng": ["Some Buyer"]},
        "procedure-type": ["open"],
    }
    if deadline:
        raw["deadline-receipt-request"] = [deadline]
    return raw


class TempRepo:
    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "foundation").mkdir(parents=True, exist_ok=True)
        return self.root

    def __exit__(self, *exc):
        self._tmp.cleanup()


class TestNoOutwardAction(unittest.TestCase):
    """This module must be structurally incapable of an outbound action."""

    FORBIDDEN_SUBSTRINGS = (
        "send", "apply", "contact", "email", "submit", "notify",
        "publish", "register", "subscribe", "post", "create_account",
    )

    def test_no_public_callable_names_an_outbound_verb(self):
        for name in hunt_loop.__all__:
            obj = getattr(hunt_loop, name)
            if not callable(obj):
                continue
            lowered = name.lower()
            for bad in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    bad, lowered,
                    f"public callable {name!r} contains forbidden verb {bad!r}")

    def test_no_module_level_function_names_an_outbound_verb(self):
        for name, obj in inspect.getmembers(hunt_loop, inspect.isfunction):
            if obj.__module__ != hunt_loop.__name__:
                continue
            lowered = name.lower()
            for bad in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    bad, lowered,
                    f"function {name!r} contains forbidden verb {bad!r}")


class TestDeadlineHonesty(unittest.TestCase):
    def test_absent_deadline_is_unknown_not_safe(self):
        with TempRepo() as root:
            r = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline="")])
        self.assertEqual(r.entries[0].deadline_status, "UNKNOWN")
        self.assertIn(r.entries[0], r.unknown_deadline_entries)
        self.assertNotIn(r.entries[0], r.closing_soon_entries)

    def test_unparseable_deadline_is_unknown(self):
        with TempRepo() as root:
            r = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline="soon-ish")])
        self.assertEqual(r.entries[0].deadline_status, "UNKNOWN")

    def test_deadline_within_window_is_closing_soon(self):
        soon = (NOW + timedelta(days=3)).date().isoformat()
        with TempRepo() as root:
            r = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=soon)])
        self.assertEqual(r.entries[0].deadline_status, "CLOSING_SOON")
        self.assertEqual(r.closing_soon_count, 1)

    def test_deadline_outside_window_is_not_closing_soon(self):
        far = (NOW + timedelta(days=90)).date().isoformat()
        with TempRepo() as root:
            r = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=far)])
        self.assertEqual(r.entries[0].deadline_status, "NOT_CLOSING_SOON")

    def test_past_deadline_is_closed_not_not_closing_soon(self):
        past = (NOW - timedelta(days=5)).date().isoformat()
        with TempRepo() as root:
            r = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=past)])
        self.assertEqual(r.entries[0].deadline_status, "CLOSED")

    def test_window_is_configurable(self):
        soon = (NOW + timedelta(days=10)).date().isoformat()
        with TempRepo() as root:
            narrow = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                deadline_window_days=5,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=soon)])
            wide = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                deadline_window_days=14,
                fetch_notices_fn=lambda: [notice("2-2026", deadline=soon)])
        self.assertEqual(narrow.entries[0].deadline_status, "NOT_CLOSING_SOON")
        self.assertEqual(wide.entries[0].deadline_status, "CLOSING_SOON")


class TestDiffIsGenuine(unittest.TestCase):
    def test_first_cycle_everything_is_new(self):
        with TempRepo() as root:
            r = run_one_hunt_cycle(
                root, "q", SOLO, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026"), notice("2-2026")])
        self.assertEqual(r.new_count, 2)
        self.assertEqual(r.action, "RAN_WITH_CHANGES")

    def test_second_cycle_repeated_notice_is_not_new(self):
        with TempRepo() as root:
            run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                               fetch_notices_fn=lambda: [notice("1-2026")])
            r2 = run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                                    fetch_notices_fn=lambda: [notice("1-2026")])
        self.assertEqual(r2.new_count, 0)
        self.assertEqual(r2.action, "RAN_NO_CHANGE")

    def test_second_cycle_only_the_added_notice_is_new(self):
        with TempRepo() as root:
            run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                               fetch_notices_fn=lambda: [notice("1-2026")])
            r2 = run_one_hunt_cycle(
                root, "q", SOLO, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026"), notice("2-2026")])
        self.assertEqual(r2.new_count, 1)
        self.assertEqual(r2.new_entries[0].publication_number, "2-2026")

    def test_never_fabricates_new_when_nothing_fetched(self):
        with TempRepo() as root:
            r = run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                                   fetch_notices_fn=lambda: [])
        self.assertEqual(r.action, "RAN_CLEAN")
        self.assertEqual(r.new_count, 0)
        self.assertEqual(r.assessed, 0)

    def test_newly_closing_flags_a_deadline_that_just_entered_the_window(self):
        just_outside = (NOW + timedelta(days=10)).date().isoformat()
        just_inside = (NOW + timedelta(days=3)).date().isoformat()
        with TempRepo() as root:
            run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=just_outside)])
            r2 = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=just_inside)])
        self.assertEqual(r2.newly_closing_count, 1)
        self.assertEqual(r2.new_count, 0)  # same notice, not a new one

    def test_already_closing_soon_notice_is_not_flagged_newly_closing_twice(self):
        soon = (NOW + timedelta(days=2)).date().isoformat()
        with TempRepo() as root:
            run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=soon)])
            r2 = run_one_hunt_cycle(
                root, "q", SOLO, capability=CAP, now=NOW,
                fetch_notices_fn=lambda: [notice("1-2026", deadline=soon)])
        self.assertEqual(r2.newly_closing_count, 0)


class TestReceiptsAndSilentLoop(unittest.TestCase):
    def test_a_clean_cycle_still_writes_a_receipt(self):
        with TempRepo() as root:
            run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                               fetch_notices_fn=lambda: [])
            log = root / "foundation" / hunt_loop.HUNT_LOG_NAME
            self.assertTrue(log.exists())
            lines = [l for l in log.read_text().splitlines() if l.strip()]
            self.assertEqual(len(lines), 1)

    def test_every_cycle_in_a_loop_writes_its_own_receipt(self):
        with TempRepo() as root:
            run_hunt_loop(root, "q", SOLO,
                          fetch_notices_fn=lambda: [notice("1-2026")],
                          max_cycles=3, sleep_seconds=0, sleep_slice_seconds=0)
            log = root / "foundation" / hunt_loop.HUNT_LOG_NAME
            lines = [l for l in log.read_text().splitlines() if l.strip()]
            self.assertEqual(len(lines), 3)

    def test_kill_switch_present_before_first_cycle_stops_immediately(self):
        with TempRepo() as root:
            (root / hunt_loop.HUNT_STOP_FILENAME).write_text("stop")
            results = run_hunt_loop(root, "q", SOLO,
                                    fetch_notices_fn=lambda: [notice("1-2026")],
                                    max_cycles=5, sleep_seconds=0,
                                    sleep_slice_seconds=0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].action, "STOPPED_KILL_SWITCH")

    def test_hunt_error_is_receipted_and_halts_the_loop(self):
        def boom():
            raise RuntimeError("network is down")
        with TempRepo() as root:
            results = run_hunt_loop(root, "q", SOLO, fetch_notices_fn=boom,
                                    max_cycles=5, sleep_seconds=0,
                                    sleep_slice_seconds=0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].action, "STOPPED_HUNT_ERROR")
        self.assertIn("network is down", results[0].detail)


class TestDurableStateSurvivesProcessRestart(unittest.TestCase):
    def test_a_fresh_call_with_no_shared_python_state_sees_prior_state(self):
        """Simulates a process restart: nothing but the file on disk is
        shared between the two calls below -- no module-level cache, no
        object handed from one call to the next."""
        with TempRepo() as root:
            run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                               fetch_notices_fn=lambda: [notice("1-2026")])
            # "Restart": read the durable state directly, the way a brand
            # new process would, with zero Python objects carried over.
            log_path = root / "foundation" / hunt_loop.HUNT_LOG_NAME
            ever_seen, _ = load_hunt_state(log_path)
            self.assertIn("1-2026", ever_seen)

            r2 = run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                                    fetch_notices_fn=lambda: [notice("1-2026")])
        self.assertEqual(r2.new_count, 0)

    def test_state_survives_a_truncated_trailing_line(self):
        with TempRepo() as root:
            run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                               fetch_notices_fn=lambda: [notice("1-2026")])
            log_path = root / "foundation" / hunt_loop.HUNT_LOG_NAME
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write('{"kind": "CYCLE", "entries": [{"publication')  # cut mid-write
            ever_seen, _ = load_hunt_state(log_path)
            self.assertIn("1-2026", ever_seen)


class TestRender(unittest.TestCase):
    def test_render_does_not_raise_on_a_clean_cycle(self):
        with TempRepo() as root:
            r = run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                                   fetch_notices_fn=lambda: [])
        text = render_hunt_cycle(r)
        self.assertIn("RAN_CLEAN", text)

    def test_render_leads_with_new_entries(self):
        with TempRepo() as root:
            r = run_one_hunt_cycle(root, "q", SOLO, now=NOW,
                                   fetch_notices_fn=lambda: [notice("1-2026")])
        text = render_hunt_cycle(r)
        self.assertIn("NEW:", text)
        self.assertIn("1-2026", text)


if __name__ == "__main__":
    unittest.main()
