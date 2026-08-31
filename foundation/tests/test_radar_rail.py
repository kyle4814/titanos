import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from foundation import radar_rail
from foundation.communication_gate import CommunicationDenied


def _item(number, repo="owner/repo", labels=("help wanted",), comments=5,
          assignees=(), author_login="alice", state="open"):
    return {
        "html_url": f"https://github.com/{repo}/issues/{number}",
        "repository_url": f"https://api.github.com/repos/{repo}",
        "number": number,
        "title": f"please help with thing {number}",
        "labels": [{"name": l} for l in labels],
        "comments": comments,
        "assignees": [{"login": a} for a in assignees],
        "user": {"login": author_login},
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-02T00:00:00Z",
        "state": state,
        "html_url": f"https://github.com/{repo}/issues/{number}",
    }


def _feed(*items):
    return json.dumps({"items": list(items)}).encode()


class RadarSweepTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_normal_ask_becomes_explicit_demand(self):
        item = _item(1, repo="owner/needy", labels=("help wanted",),
                     assignees=(), author_login="alice")
        result = radar_rail.sweep(
            self.state_dir, fetch_fn=lambda: _feed(item))
        self.assertEqual(result.status, "FIRST_SEEN")
        self.assertEqual(len(result.signals), 1)
        self.assertEqual(len(result.explicit_demand), 1)
        self.assertEqual(len(result.rejected), 0)
        self.assertEqual(result.explicit_demand[0].pressure_class,
                         "EXPLICIT_DEMAND")
        self.assertIn("owner/needy", result.targets)

    def test_bot_authored_ask_is_rejected_with_reason(self):
        item = _item(2, repo="owner/botrepo", labels=("help wanted",),
                     assignees=(), author_login="releasebot[bot]")
        result = radar_rail.sweep(
            self.state_dir, fetch_fn=lambda: _feed(item))
        self.assertEqual(len(result.explicit_demand), 0)
        self.assertEqual(len(result.rejected), 1)
        signal, reason = result.rejected[0]
        self.assertEqual(reason, "bot-authored")
        self.assertTrue(signal.evidence["author_is_bot"])

    def test_assigned_ask_is_rejected_with_reason(self):
        item = _item(3, repo="owner/claimed", labels=("help wanted",),
                     assignees=("carol",), author_login="dave")
        result = radar_rail.sweep(
            self.state_dir, fetch_fn=lambda: _feed(item))
        self.assertEqual(len(result.explicit_demand), 0)
        self.assertEqual(len(result.rejected), 1)
        signal, reason = result.rejected[0]
        self.assertEqual(reason, "assigned")
        self.assertTrue(signal.evidence["claimed"])

    def test_recruitment_taxonomy_is_rejected_with_reason(self):
        item = _item(
            4, repo="owner/farm",
            labels=("good first issue", "difficulty:beginner", "size:xs",
                    "cohort:wave1"),
            assignees=(), author_login="eve")
        result = radar_rail.sweep(
            self.state_dir, fetch_fn=lambda: _feed(item))
        self.assertEqual(len(result.explicit_demand), 0)
        self.assertEqual(len(result.rejected), 1)
        signal, reason = result.rejected[0]
        self.assertEqual(reason, "recruitment")
        self.assertEqual(signal.evidence["demand_direction"], "WORK_OFFERED")

    def test_no_help_label_is_rejected_with_reason(self):
        item = _item(5, repo="owner/unlabelled", labels=("bug",),
                     assignees=(), author_login="frank")
        result = radar_rail.sweep(
            self.state_dir, fetch_fn=lambda: _feed(item))
        self.assertEqual(len(result.explicit_demand), 0)
        self.assertEqual(len(result.rejected), 1)
        _signal, reason = result.rejected[0]
        self.assertEqual(reason, "no help label")

    def test_empty_feed_produces_empty_sweep_not_a_crash(self):
        result = radar_rail.sweep(
            self.state_dir, fetch_fn=lambda: json.dumps({"items": []}).encode())
        self.assertEqual(result.fetched_count, 0)
        self.assertEqual(result.signals, ())
        self.assertEqual(result.explicit_demand, ())
        self.assertEqual(result.rejected, ())
        self.assertEqual(result.targets, ())
        self.assertIn("RADAR SWEEP", result.show_the_math())

    def test_malformed_json_is_reported_not_raised(self):
        try:
            result = radar_rail.sweep(
                self.state_dir, fetch_fn=lambda: b"not json at all {{{")
        except Exception as exc:  # pragma: no cover - failure path itself
            self.fail(f"malformed payload raised {exc!r} instead of being "
                     f"reported")
        self.assertEqual(result.fetched_count, 0)
        self.assertEqual(result.signals, ())

    def test_show_the_math_names_each_rejection_reason(self):
        items = [
            _item(10, repo="owner/a", labels=("help wanted",),
                 author_login="bot[bot]"),
            _item(11, repo="owner/b", labels=("help wanted",),
                 assignees=("someone",), author_login="human"),
        ]
        result = radar_rail.sweep(self.state_dir, fetch_fn=lambda: _feed(*items))
        report = result.show_the_math()
        self.assertIn("bot-authored", report)
        self.assertIn("assigned", report)

    def test_never_opens_a_socket_when_fetch_fn_injected(self):
        def _forbidden(*a, **k):
            raise AssertionError("urlopen must never be called when "
                                 "fetch_fn is injected")
        item = _item(20, repo="owner/offline")
        with mock.patch.object(urllib.request, "urlopen", _forbidden):
            result = radar_rail.sweep(
                self.state_dir, fetch_fn=lambda: _feed(item))
        self.assertEqual(len(result.signals), 1)

    def test_fetch_fn_none_still_routes_through_the_gate(self):
        # Prove the gate is genuinely in the path when this module does
        # NOT inject a fetcher, without touching the network: patch the
        # gate itself to refuse, and confirm the refusal surfaces rather
        # than being bypassed or swallowed.
        with mock.patch(
                "foundation.discovery_authorization.authorize_discovery",
                side_effect=CommunicationDenied("no standing authorization")):
            with self.assertRaises(CommunicationDenied):
                radar_rail.sweep(self.state_dir, fetch_fn=None)


if __name__ == "__main__":
    unittest.main()
