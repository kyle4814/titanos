import json
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

from foundation.mouth_common import (
    FetchError, MAX_FEED_BYTES, compute_state_hash, fetch_feed, observe,
    read_mouth_log_continuity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _items(keys):
    return tuple({"key": k, "title": k} for k in keys)


class TestComputeStateHash(unittest.TestCase):
    def test_deterministic_order_independent(self):
        a = _items(["x", "y"])
        b = _items(["y", "x"])
        self.assertEqual(compute_state_hash(a), compute_state_hash(b))

    def test_different_keys_different_hash(self):
        self.assertNotEqual(compute_state_hash(_items(["x"])), compute_state_hash(_items(["y"])))


class TestObserveGeneric(unittest.TestCase):
    def test_first_seen_unchanged_changed_unavailable_cycle(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"

            obs1 = observe("m", state_path, lambda: b"v1", lambda raw: _items(["a", "b"]))
            self.assertEqual(obs1.status, "FIRST_SEEN")

            obs2 = observe("m", state_path, lambda: b"v1", lambda raw: _items(["a", "b"]))
            self.assertEqual(obs2.status, "UNCHANGED")

            obs3 = observe("m", state_path, lambda: b"v2", lambda raw: _items(["a", "b", "c"]))
            self.assertEqual(obs3.status, "CHANGED")
            self.assertEqual([i["key"] for i in obs3.new_items], ["c"])

            def bad_parse(raw):
                raise FetchError("parse blew up")
            before = state_path.read_text()
            obs4 = observe("m", state_path, lambda: b"v3", bad_parse)
            self.assertEqual(obs4.status, "UNAVAILABLE")
            self.assertEqual(state_path.read_text(), before)

    def test_mouth_id_is_threaded_through(self):
        with tempfile.TemporaryDirectory() as d:
            state_path = Path(d) / "state.json"
            obs = observe("my_mouth_id", state_path, lambda: b"x", lambda raw: _items(["a"]))
            self.assertEqual(obs.mouth_id, "my_mouth_id")


class TestReadMouthLogContinuity(unittest.TestCase):
    def test_missing_log_fails_soft(self):
        with tempfile.TemporaryDirectory() as d:
            result = read_mouth_log_continuity(Path(d) / "nope.jsonl")
            self.assertFalse(result.available)
            self.assertIn("never fired", result.warnings[0])

    def test_empty_log_is_valid_zero_state(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "log.jsonl"
            log_path.write_text("")
            result = read_mouth_log_continuity(log_path)
            self.assertTrue(result.available)
            self.assertEqual(result.records_considered, 0)

    def test_fresh_record_not_stale(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "log.jsonl"
            now = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
            rec = {"observed_at": "2026-08-27T11:30:00+00:00", "status": "UNCHANGED"}
            log_path.write_text(json.dumps(rec) + "\n")
            result = read_mouth_log_continuity(log_path, now=now)
            self.assertFalse(result.stale)
            self.assertEqual(result.latest_status, "UNCHANGED")

    def test_old_record_flagged_stale(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "log.jsonl"
            now = datetime(2026, 8, 27, 12, 0, 0, tzinfo=timezone.utc)
            rec = {"observed_at": "2026-08-27T00:00:00+00:00", "status": "UNCHANGED"}
            log_path.write_text(json.dumps(rec) + "\n")
            result = read_mouth_log_continuity(log_path, now=now)
            self.assertTrue(result.stale)

    def test_malformed_line_skipped_not_fatal(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "log.jsonl"
            now = datetime(2026, 8, 27, 0, 0, 0, tzinfo=timezone.utc)
            good = {"observed_at": "2026-08-27T00:00:00+00:00", "status": "OK"}
            log_path.write_text("{not json\n" + json.dumps(good) + "\n")
            result = read_mouth_log_continuity(log_path, now=now)
            self.assertTrue(result.available)
            self.assertEqual(result.records_considered, 1)
            self.assertTrue(any("malformed JSON" in w for w in result.warnings))

    def test_repeated_calls_do_not_mutate_the_log(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "log.jsonl"
            log_path.write_text(json.dumps({"observed_at": "2026-08-27T00:00:00+00:00"}) + "\n")
            before = log_path.read_text()
            read_mouth_log_continuity(log_path)
            read_mouth_log_continuity(log_path)
            self.assertEqual(log_path.read_text(), before)

    def test_large_log_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            log_path = Path(d) / "log.jsonl"
            lines = [json.dumps({"observed_at": f"2026-08-27T{i%24:02d}:00:00+00:00"}) for i in range(500)]
            log_path.write_text("\n".join(lines) + "\n")
            result = read_mouth_log_continuity(log_path, max_records=20)
            self.assertEqual(result.records_considered, 20)

    def test_works_on_the_real_mouth_logs_in_this_repo(self):
        # These logs are foundation/cron_pulse.py's real, machine-local
        # output (gitignored -- not shipped with the repo, see
        # .gitignore's note). A fresh checkout correctly reports
        # available=False ("never fired yet"); a machine with real cron
        # history correctly reports available=True. Both are valid
        # states -- this test proves read_mouth_log_continuity() handles
        # whichever real state this checkout has without crashing, and
        # checks freshness only when a log is actually present. Asserting
        # available=True unconditionally here was a real bug: it silently
        # depended on this specific machine's local cron history and
        # failed on a fresh CI checkout (caught 2026-08-27 when this repo
        # was actually pushed and the real CI matrix ran it).
        for name in ("mouth_pypi_pyyaml_releases_log.jsonl", "mouth_github_pyyaml_releases_log.jsonl"):
            result = read_mouth_log_continuity(REPO_ROOT / "foundation" / name)
            if result.available:
                self.assertFalse(result.stale, f"{name} unexpectedly stale — real clock check")
            else:
                self.assertIn("never fired", result.warnings[0])


if __name__ == "__main__":
    unittest.main()


class TestFetchFeedIsByteBounded(unittest.TestCase):
    """Adversarial review 2026-08-28: fetch_feed() used an unbounded
    response.read(). `timeout` bounds a stalled socket operation, not
    total transfer size, so a compromised or redirected feed endpoint
    could stream an arbitrarily large body straight into memory."""

    class _FakeResponse:
        def __init__(self, payload): self._payload = payload
        def read(self, n=-1): return self._payload[:n] if n and n > 0 else self._payload
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _patched(self, payload):
        return mock.patch("urllib.request.urlopen", return_value=self._FakeResponse(payload))

    def test_an_oversized_response_is_refused_as_a_fetch_error(self):
        with self._patched(b"A" * (MAX_FEED_BYTES + 10)):
            with self.assertRaises(FetchError) as ctx:
                fetch_feed("https://example.invalid/feed")
        self.assertIn("MAX_FEED_BYTES", str(ctx.exception))

    def test_a_normal_sized_response_is_returned_intact(self):
        payload = b"<rss>ok</rss>"
        with self._patched(payload):
            self.assertEqual(fetch_feed("https://example.invalid/feed"), payload)

    def test_a_response_exactly_at_the_cap_is_still_accepted(self):
        payload = b"B" * MAX_FEED_BYTES
        with self._patched(payload):
            self.assertEqual(len(fetch_feed("https://example.invalid/feed")), MAX_FEED_BYTES)

    def test_an_oversized_feed_becomes_UNAVAILABLE_and_preserves_prior_state(self):
        """The consequence that matters: a refused fetch must never look
        like 'the items disappeared', which observe() would otherwise
        record as a real CHANGED observation."""
        with tempfile.TemporaryDirectory() as d:
            state = Path(d) / "state.json"
            observe("m", state, lambda: b"v1", lambda raw: ({"key": "a"},))
            before = state.read_text()

            def oversized():
                raise FetchError("response exceeds MAX_FEED_BYTES")

            obs = observe("m", state, oversized, lambda raw: ())
            self.assertEqual(obs.status, "UNAVAILABLE")
            self.assertEqual(state.read_text(), before, "prior baseline was destroyed")

    def test_pure_removal_is_CHANGED_with_empty_new_items_not_a_bug(self):
        """Documents current, deliberate behavior after a real cycle
        demonstrated it (2026-08-28 GH Pulse recursive payload): a
        removed item is NOT surfaced in `new_items` (which reports only
        additions relative to the immediately prior checkpoint), but the
        removal IS visible via a `item_count` decrease and a changed
        `content_hash`. This is not a defect for the current sole
        consumer, dependency_pressure.py, which explicitly treats
        CHANGED-with-empty-new_items as "no finding" -- it only cares
        about new releases, never removals. A future consumer wanting
        first-class removal semantics would need to diff item_count or
        add a dedicated field; this test locks in the current behavior
        so any future change to it is a deliberate, visible decision."""
        with tempfile.TemporaryDirectory() as d:
            state = Path(d) / "state.json"
            observe("m", state, lambda: b"v1",
                     lambda raw: ({"key": "A"}, {"key": "B"}))
            obs = observe("m", state, lambda: b"v2",
                           lambda raw: ({"key": "A"},))
            self.assertEqual(obs.status, "CHANGED")
            self.assertEqual(obs.new_items, ())
            self.assertEqual(obs.item_count, 1, "the drop from 2 to 1 is "
                              "the only currently-persisted removal signal")


class TestReadMouthLogContinuitySurvivesNonDictLines(unittest.TestCase):
    """Same systemic bug class as sentinel.py::read_pulse_continuity(),
    found in the same 2026-08-28 hunt: `.get()` on a non-dict JSON value
    crashed this reader too."""

    def test_a_non_dict_line_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "m.jsonl"
            log.write_text('42\n"str"\n[1,2]\nnull\n')
            result = read_mouth_log_continuity(log)
            self.assertEqual(result.records_considered, 0)
            self.assertTrue(any("not an object" in w for w in result.warnings))

    def test_a_real_record_still_parses_when_mixed_with_junk(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "m.jsonl"
            log.write_text('99\n' + json.dumps({
                "mouth_id": "x", "observed_at": "2026-08-27T00:00:00+00:00",
                "status": "UNCHANGED"}) + '\n')
            result = read_mouth_log_continuity(log)
            self.assertEqual(result.records_considered, 1)
