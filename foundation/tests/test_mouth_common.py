import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from foundation.mouth_common import (
    FetchError, compute_state_hash, observe, read_mouth_log_continuity,
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
        for name in ("mouth_pypi_pyyaml_releases_log.jsonl", "mouth_github_pyyaml_releases_log.jsonl"):
            result = read_mouth_log_continuity(REPO_ROOT / "foundation" / name)
            self.assertTrue(result.available)
            self.assertFalse(result.stale, f"{name} unexpectedly stale — real clock check")


if __name__ == "__main__":
    unittest.main()
