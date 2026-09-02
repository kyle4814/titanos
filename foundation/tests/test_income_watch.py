"""Tests for `foundation/income_watch.py`. Every test is offline --
`fetch_fn` is always injected; no test touches the real network."""

from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from foundation import income_watch
from foundation import mouth_bounty
from foundation import mouth_gigs
from foundation.mouth_common import FetchError


def _bounty_raw(items: list[dict]) -> bytes:
    return json.dumps({"items": items}).encode("utf-8")


def _bounty_item(slug="acme-web", title="Acme Web", bounty=True,
                  reward_min=100, reward_max=5000, currency="USD",
                  vdp=False, public=True, disabled=False, archived=False,
                  company_name="Acme"):
    return {
        "slug": slug, "public": public, "disabled": disabled,
        "archived": archived, "title": title, "bounty": bounty,
        "vdp": vdp, "bounty_reward_min": reward_min,
        "bounty_reward_max": reward_max,
        "business_unit": {"name": company_name, "currency": currency},
    }


def _gig_raw(story_id="1", story_title="Ask HN: Who is hiring? (Sep 2026)",
             hits=None):
    return json.dumps({
        "story_id": story_id, "story_title": story_title,
        "hits": hits or [],
    }).encode("utf-8")


def _gig_hit(object_id="c1", author="alice", comment_text="Contract pentest role"):
    return {"objectID": object_id, "author": author, "comment_text": comment_text}


def _bounty_source(fetch_fn):
    return income_watch.IncomeSource(
        source_id="test_bounty", kind=income_watch.BOUNTY_PROGRAM,
        fetch_fn=fetch_fn, parse_fn=mouth_bounty.parse_items,
        to_fields=income_watch._bounty_fields,
    )


def _gig_source(fetch_fn):
    return income_watch.IncomeSource(
        source_id="test_gigs", kind=income_watch.CONTRACT_GIG,
        fetch_fn=fetch_fn, parse_fn=mouth_gigs.parse_items,
        to_fields=income_watch._gig_fields,
    )


class IncomeSignalTests(unittest.TestCase):

    def test_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            income_watch.IncomeSignal(
                source_id="s", identifier="i", title="t", url="",
                kind="NOT_A_KIND", first_seen="2026-01-01T00:00:00+00:00")

    def test_rejects_empty_identifier(self):
        with self.assertRaises(ValueError):
            income_watch.IncomeSignal(
                source_id="s", identifier="", title="t", url="",
                kind=income_watch.BOUNTY_PROGRAM,
                first_seen="2026-01-01T00:00:00+00:00")

    def test_rejects_empty_payout_observed(self):
        with self.assertRaises(ValueError):
            income_watch.IncomeSignal(
                source_id="s", identifier="i", title="t", url="",
                kind=income_watch.BOUNTY_PROGRAM,
                first_seen="2026-01-01T00:00:00+00:00", payout_observed="")

    def test_default_payout_observed_is_not_observed(self):
        sig = income_watch.IncomeSignal(
            source_id="s", identifier="i", title="t", url="",
            kind=income_watch.BOUNTY_PROGRAM,
            first_seen="2026-01-01T00:00:00+00:00")
        self.assertEqual(sig.payout_observed, income_watch.NOT_OBSERVED)


class FieldNormalisationTests(unittest.TestCase):

    def test_bounty_fields_paying_program_carries_verbatim_range(self):
        raw = _bounty_raw([_bounty_item(reward_min=100, reward_max=5000, currency="USD")])
        item = mouth_bounty.parse_items(raw)[0]
        fields = income_watch._bounty_fields(item)
        self.assertEqual(fields["payout_observed"], "100-5000 USD")

    def test_bounty_fields_vdp_only_is_not_observed(self):
        raw = _bounty_raw([_bounty_item(bounty=False, reward_min=None, reward_max=None, vdp=True)])
        item = mouth_bounty.parse_items(raw)[0]
        fields = income_watch._bounty_fields(item)
        self.assertEqual(fields["payout_observed"], income_watch.NOT_OBSERVED)

    def test_bounty_fields_never_fabricates_zero(self):
        # bounty True but reward_max missing/zero must never render "0"
        raw = _bounty_raw([_bounty_item(bounty=True, reward_min=None, reward_max=0)])
        item = mouth_bounty.parse_items(raw)[0]
        fields = income_watch._bounty_fields(item)
        self.assertEqual(fields["payout_observed"], income_watch.NOT_OBSERVED)

    def test_gig_fields_always_not_observed(self):
        raw = _gig_raw(hits=[_gig_hit()])
        item = mouth_gigs.parse_items(raw)[0]
        fields = income_watch._gig_fields(item)
        self.assertEqual(fields["payout_observed"], income_watch.NOT_OBSERVED)


class WatchTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self._tmp.name) / "income_watch_state.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_first_cycle_all_items_are_new(self):
        raw = _bounty_raw([_bounty_item(slug="a"), _bounty_item(slug="b")])
        source = _bounty_source(lambda: raw)
        report = income_watch.watch([source], self.state_path,
                                     now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        self.assertEqual(len(report.signals), 2)
        self.assertEqual(len(report.new_signals), 2)
        self.assertEqual(report.results[0].status, "OK")

    def test_second_cycle_same_items_yields_zero_new(self):
        raw = _bounty_raw([_bounty_item(slug="a"), _bounty_item(slug="b")])
        source = _bounty_source(lambda: raw)
        income_watch.watch([source], self.state_path,
                            now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        report2 = income_watch.watch([source], self.state_path,
                                      now=datetime(2026, 9, 3, tzinfo=timezone.utc))
        self.assertEqual(len(report2.signals), 2)
        self.assertEqual(len(report2.new_signals), 0)

    def test_third_cycle_one_genuinely_new_item(self):
        raw1 = _bounty_raw([_bounty_item(slug="a")])
        raw2 = _bounty_raw([_bounty_item(slug="a"), _bounty_item(slug="b")])
        source1 = _bounty_source(lambda: raw1)
        income_watch.watch([source1], self.state_path,
                            now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        source2 = _bounty_source(lambda: raw2)
        report2 = income_watch.watch([source2], self.state_path,
                                      now=datetime(2026, 9, 3, tzinfo=timezone.utc))
        self.assertEqual(len(report2.signals), 2)
        self.assertEqual(len(report2.new_signals), 1)
        self.assertEqual(report2.new_signals[0].identifier, "b")

    def test_fetch_error_marks_unavailable_and_does_not_touch_state(self):
        def _boom():
            raise FetchError("simulated outage")
        source = _bounty_source(_boom)
        report = income_watch.watch([source], self.state_path,
                                     now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        self.assertEqual(report.results[0].status, "UNAVAILABLE")
        self.assertIn("simulated outage", report.results[0].error)
        self.assertEqual(report.signals, ())
        self.assertFalse(self.state_path.exists())

    def test_one_source_failing_does_not_block_the_other(self):
        def _boom():
            raise FetchError("simulated outage")
        raw = _gig_raw(hits=[_gig_hit(object_id="c1")])
        failing = _bounty_source(_boom)
        working = _gig_source(lambda: raw)
        report = income_watch.watch([failing, working], self.state_path,
                                     now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        statuses = {r.source_id: r.status for r in report.results}
        self.assertEqual(statuses["test_bounty"], "UNAVAILABLE")
        self.assertEqual(statuses["test_gigs"], "OK")
        self.assertEqual(len(report.new_signals), 1)

    def test_items_with_no_identifier_are_dropped(self):
        raw = _bounty_raw([_bounty_item(slug="")])
        source = _bounty_source(lambda: raw)
        report = income_watch.watch([source], self.state_path)
        self.assertEqual(report.signals, ())

    def test_multiple_sources_kept_separate_by_source_id(self):
        bounty_raw = _bounty_raw([_bounty_item(slug="same-id")])
        gig_raw = _gig_raw(hits=[_gig_hit(object_id="same-id")])
        bsource = _bounty_source(lambda: bounty_raw)
        gsource = _gig_source(lambda: gig_raw)
        report = income_watch.watch([bsource, gsource], self.state_path,
                                     now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        # Same literal identifier text on two different sources must not
        # collide -- keyed on (source_id, identifier).
        self.assertEqual(len(report.new_signals), 2)


class DurableStateTests(unittest.TestCase):
    """Proves the state file is a real file on disk, read back fresh --
    not a Python object shared between calls. Each `watch()` call below
    is made through a fresh, independent code path with no shared
    variable except the path string itself, matching the deliverable's
    own requirement: 'a test that reads the file between two calls
    sharing no Python state.'"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_path_str = str(Path(self._tmp.name) / "durable.jsonl")

    def tearDown(self):
        self._tmp.cleanup()

    def test_state_file_is_real_and_survives_between_independent_calls(self):
        raw = _bounty_raw([_bounty_item(slug="only-one")])

        def _call_one():
            path = Path(self.state_path_str)
            src = _bounty_source(lambda: raw)
            return income_watch.watch([src], path,
                                       now=datetime(2026, 9, 2, tzinfo=timezone.utc))

        report1 = _call_one()
        self.assertEqual(len(report1.new_signals), 1)

        # Confirm it is a real file with real bytes -- not an in-memory
        # stand-in -- before the second call ever runs.
        self.assertTrue(Path(self.state_path_str).exists())
        on_disk = Path(self.state_path_str).read_text(encoding="utf-8")
        record = json.loads(on_disk.strip().splitlines()[0])
        self.assertEqual(record["identifier"], "only-one")

        def _call_two():
            # A fresh Path object, a fresh source, a fresh lambda -- no
            # variable from _call_one() is referenced here except the
            # path string, proving durability is on disk, not in memory.
            path = Path(self.state_path_str)
            src = _bounty_source(lambda: raw)
            return income_watch.watch([src], path,
                                       now=datetime(2026, 9, 3, tzinfo=timezone.utc))

        report2 = _call_two()
        self.assertEqual(len(report2.new_signals), 0,
                          "the second, independent call must see the item "
                          "already recorded by the first via the file on disk")

    def test_state_file_survives_a_fresh_module_reimport_style_read(self):
        # Simulates a fresh process: nothing here touches any object
        # created above. _load_seen() is called directly against the
        # path, exactly as watch() itself does at the top of every call.
        raw = _bounty_raw([_bounty_item(slug="proc-boundary")])
        src = _bounty_source(lambda: raw)
        income_watch.watch([src], Path(self.state_path_str),
                            now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        seen = income_watch._load_seen(Path(self.state_path_str))
        self.assertIn(("test_bounty", "proc-boundary"), seen)


class RenderTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self._tmp.name) / "state.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def test_new_items_lead_the_render(self):
        raw = _bounty_raw([_bounty_item(slug="fresh-one")])
        source = _bounty_source(lambda: raw)
        report = income_watch.watch([source], self.state_path,
                                     now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        text = income_watch.render_income_watch(report)
        new_idx = text.index("NEW THIS CYCLE")
        all_idx = text.index("ALL CURRENTLY OBSERVED")
        self.assertLess(new_idx, all_idx)

    def test_empty_result_renders_honest_zero_new_line(self):
        source = _bounty_source(lambda: _bounty_raw([]))
        report = income_watch.watch([source], self.state_path)
        text = income_watch.render_income_watch(report)
        self.assertIn("zero new programs/gigs observed this cycle", text)

    def test_unavailable_source_is_named_in_render(self):
        def _boom():
            raise FetchError("down")
        source = _bounty_source(_boom)
        report = income_watch.watch([source], self.state_path)
        text = income_watch.render_income_watch(report)
        self.assertIn("UNAVAILABLE", text)
        self.assertIn("down", text)


class DisclaimerLanguageTests(unittest.TestCase):
    """Pins the value-discipline requirement: a listed, unworked
    program/gig must never be described with promotional/certain
    language."""

    FORBIDDEN_WORDS = ("lead", "guaranteed", "earnings")

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self._tmp.name) / "state.jsonl"

    def tearDown(self):
        self._tmp.cleanup()

    def _assert_no_forbidden_words(self, text: str) -> None:
        lowered = text.lower()
        for word in self.FORBIDDEN_WORDS:
            self.assertNotIn(word, lowered,
                              f"forbidden word {word!r} found in rendered output")

    def test_disclaimer_present_and_clean_with_new_items(self):
        raw = _bounty_raw([_bounty_item(slug="x", reward_min=10, reward_max=99)])
        source = _bounty_source(lambda: raw)
        report = income_watch.watch([source], self.state_path,
                                     now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        text = income_watch.render_income_watch(report)
        self.assertIn("PUBLISHED OPPORTUNITY", text)
        self.assertIn("not a promise of income", text)
        self._assert_no_forbidden_words(text)

    def test_disclaimer_clean_with_zero_items(self):
        source = _bounty_source(lambda: _bounty_raw([]))
        report = income_watch.watch([source], self.state_path)
        text = income_watch.render_income_watch(report)
        self._assert_no_forbidden_words(text)

    def test_disclaimer_clean_with_gig_items(self):
        raw = _gig_raw(hits=[_gig_hit(comment_text="Contract security work, great earning potential")])
        source = _gig_source(lambda: raw)
        report = income_watch.watch([source], self.state_path,
                                     now=datetime(2026, 9, 2, tzinfo=timezone.utc))
        text = income_watch.render_income_watch(report)
        # The disclaimer/report scaffolding itself must stay clean even
        # though a comment's own free text might contain "earning" --
        # only the exact forbidden words are checked, and the scaffold
        # text (not attacker-influenced free text) is what this pins.
        for word in ("lead", "guaranteed"):
            self.assertNotIn(word, text.lower())


class TestNoOutwardAction(unittest.TestCase):
    """This module must be structurally incapable of an outbound
    action. Same shape as `hunt_loop.py`'s own `TestNoOutwardAction`."""

    FORBIDDEN_SUBSTRINGS = (
        "send", "apply", "contact", "email", "submit", "notify",
        "publish", "register", "subscribe", "post", "create_account",
    )

    def test_no_public_callable_names_an_outbound_verb(self):
        for name in income_watch.__all__:
            obj = getattr(income_watch, name)
            if not callable(obj):
                continue
            lowered = name.lower()
            for bad in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    bad, lowered,
                    f"public callable {name!r} contains forbidden verb {bad!r}")

    def test_no_module_level_function_names_an_outbound_verb(self):
        for name, obj in inspect.getmembers(income_watch, inspect.isfunction):
            if obj.__module__ != income_watch.__name__:
                continue
            lowered = name.lower()
            for bad in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(
                    bad, lowered,
                    f"function {name!r} contains forbidden verb {bad!r}")


class DefaultSourcesTests(unittest.TestCase):

    def test_default_sources_wires_bounty_and_gigs(self):
        sources = income_watch.default_sources()
        source_ids = {s.source_id for s in sources}
        self.assertEqual(source_ids, {mouth_bounty.MOUTH_ID, mouth_gigs.MOUTH_ID})
        kinds = {s.kind for s in sources}
        self.assertEqual(kinds, {income_watch.BOUNTY_PROGRAM, income_watch.CONTRACT_GIG})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
