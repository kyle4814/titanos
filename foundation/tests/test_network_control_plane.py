"""The control plane must be unbypassable at the socket, not above it.

WHY THIS FILE EXISTS

`communication_gate.py` and `discovery_authorization.py` were built,
tested, and armed several cycles before this. Neither had a single
consumer. `mouth_common.fetch_feed()` -- the only place in this
repository that opens a socket -- called `urllib.request.urlopen`
without ever consulting them, and both modules' own docstrings asserted
that no such fetcher existed, which is why nobody noticed.

A switch with no consumer is a reminder, not an enforcement point. These
tests exist so that stays fixed: they attack the gate from the positions
a buggy or careless caller would actually occupy.
"""

import ast
import pathlib
import unittest
from unittest import mock

from foundation.communication_gate import CommunicationDenied
from foundation.discovery_authorization import (
    DiscoveryPolicy, UnboundedDiscoveryObjective,
)
from foundation.mouth_common import fetch_feed

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

VALID = DiscoveryPolicy(
    objective="observe the release feed of one named repository",
    requested_scope="READ_URL")


def _never_called(*a, **k):                                   # pragma: no cover
    raise AssertionError(
        "urlopen was reached despite the gate refusing -- the control "
        "plane was bypassed")


class TestTheSocketIsGated(unittest.TestCase):

    def test_no_policy_never_reaches_the_socket(self):
        with mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed")

    def test_an_object_merely_shaped_like_a_policy_is_refused(self):
        """A caller cannot hand over a duck-typed stand-in that claims
        to be authorized."""
        class Impostor:
            objective = "observe one named repository"
            requested_scope = "READ_URL"
            max_queries = 5
        with mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed", policy=Impostor())

    def test_an_unauthorized_scope_never_reaches_the_socket(self):
        policy = DiscoveryPolicy(objective="receive a callback",
                                 requested_scope="RECEIVE_WEBHOOK")
        with mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed", policy=policy)

    def test_none_is_not_a_scope(self):
        policy = DiscoveryPolicy(objective="observe one repository",
                                 requested_scope="")
        with mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed", policy=policy)


class TestUnboundedObjectivesNeverReachTheSocket(unittest.TestCase):
    """The defect that was found by attacking this gate immediately
    after wiring it: `find everything` passed the phrase blocklist and
    reached `urlopen`, failing only because DNS did not resolve."""

    UNBOUNDED = (
        "find everything",
        "search the web",
        "scrape the entire internet",
        "grab as much as you can",
        "collect anything you find",
        "index the whole web",
        "anything interesting",
        "keep searching",
    )

    def test_unbounded_objectives_are_refused(self):
        for objective in self.UNBOUNDED:
            with self.subTest(objective=objective):
                policy = DiscoveryPolicy(objective=objective,
                                         requested_scope="READ_URL")
                with mock.patch("urllib.request.urlopen", _never_called):
                    with self.assertRaises(UnboundedDiscoveryObjective):
                        fetch_feed("https://example.invalid/f", policy=policy)

    def test_an_empty_objective_is_refused(self):
        with mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(UnboundedDiscoveryObjective):
                fetch_feed("https://example.invalid/f",
                           policy=DiscoveryPolicy(objective="   ",
                                                  requested_scope="READ_URL"))

    def test_a_concrete_objective_is_allowed_through(self):
        """The other half of the proof. A gate that refuses everything
        is not enforcement, it is breakage."""
        class _Resp:
            def read(self, n=-1): return b"<feed/>"
            def __enter__(self): return self
            def __exit__(self, *a): return False
        with mock.patch("urllib.request.urlopen", return_value=_Resp()):
            self.assertEqual(
                fetch_feed("https://example.invalid/f", policy=VALID),
                b"<feed/>")


class TestThereIsExactlyOneSocket(unittest.TestCase):
    """The gate's guarantee rests entirely on there being one door.

    If a second module starts calling urlopen directly, everything above
    is worthless -- so that premise is checked rather than assumed.
    """

    ALLOWED = {"foundation/mouth_common.py"}

    def _network_callers(self):
        found = set()
        for path in sorted(REPO_ROOT.rglob("*.py")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if "/tests/" in rel or rel.startswith("tests/"):
                continue
            try:
                tree = ast.parse(path.read_text(errors="ignore"))
            except SyntaxError:                               # pragma: no cover
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = ast.unparse(node.func)
                    if "urlopen" in name or name.endswith("socket.socket"):
                        found.add(rel)
        return found

    def test_only_mouth_common_opens_a_socket(self):
        callers = self._network_callers()
        self.assertEqual(
            callers, self.ALLOWED,
            f"a new network caller appeared outside the gate: "
            f"{sorted(callers - self.ALLOWED)}. Route it through "
            f"mouth_common.fetch_feed() or the control plane is bypassable.")


class TestEveryFetcherDeclaresAnObjective(unittest.TestCase):
    """Each mouth must name what it fetches for, and that objective must
    itself survive the validator -- otherwise a module could ship a
    policy that fails only in production."""

    MOUTHS = ("mouth_github_releases", "mouth_pypi", "mouth_github_issues",
              "mouth_github_commits", "mouth_npm", "target_mapping")

    def test_each_mouth_has_a_valid_discovery_policy(self):
        import importlib
        for name in self.MOUTHS:
            with self.subTest(mouth=name):
                mod = importlib.import_module(f"foundation.{name}")
                policy = getattr(mod, "DISCOVERY_POLICY", None)
                self.assertIsInstance(
                    policy, DiscoveryPolicy,
                    f"foundation/{name}.py fetches but declares no objective")
                from foundation.discovery_authorization import authorize_discovery
                self.assertTrue(authorize_discovery(policy))


class TestTheDocumentationMatchesReality(unittest.TestCase):
    """The stale-claim class that caused this whole defect.

    Both gate modules asserted in prose that no fetcher existed. That was
    true when written and false for several cycles afterwards, and the
    false statement is precisely why the unwired switch survived review.
    """

    def test_gate_modules_do_not_claim_there_is_no_fetcher(self):
        dead_claims = (
            "no such operation exists",
            "no fetcher/adapter exists yet",
            "Nothing in this repository calls a real fetcher",
        )
        for mod in ("communication_gate.py", "discovery_authorization.py"):
            text = (REPO_ROOT / "foundation" / mod).read_text()
            for claim in dead_claims:
                with self.subTest(module=mod, claim=claim):
                    # Permitted only inside an explicit correction note.
                    idx = text.find(claim)
                    if idx == -1:
                        continue
                    window = text[max(0, idx - 400):idx]
                    self.assertTrue(
                        "CORRECTION" in window or "previously" in window,
                        f"{mod} still asserts {claim!r} as current fact; a "
                        f"fetcher does exist and calls this gate")


if __name__ == "__main__":
    unittest.main()
