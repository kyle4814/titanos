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
    DiscoveryBudgetExhausted, DiscoveryPolicy, UnboundedDiscoveryObjective,
    budget_spent, reset_budgets,
)
from foundation.mouth_common import fetch_feed

# Build outputs are copies of the source tree, not new code. `pip wheel .`
# and an sdist build leave `build/` and `*.egg-info/` behind, each holding a
# duplicate of every production module, and a scan that walks them reports
# the copy as a second network caller -- a false alarm about a file that is
# byte-identical to one already checked. They are gitignored; walking the
# filesystem does not respect that, so the exclusion is explicit.
_BUILD_DIRS = ("build/", "dist/", ".eggs/", "corpus/")


def _is_build_output(rel: str) -> bool:
    return rel.startswith(_BUILD_DIRS) or ".egg-info/" in rel


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
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed")

    def test_an_object_merely_shaped_like_a_policy_is_refused(self):
        """A caller cannot hand over a duck-typed stand-in that claims
        to be authorized."""
        class Impostor:
            objective = "observe one named repository"
            requested_scope = "READ_URL"
            max_queries = 5
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed", policy=Impostor())

    def test_an_unauthorized_scope_never_reaches_the_socket(self):
        policy = DiscoveryPolicy(objective="receive a callback",
                                 requested_scope="RECEIVE_WEBHOOK")
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed", policy=policy)

    def test_none_is_not_a_scope(self):
        policy = DiscoveryPolicy(objective="observe one repository",
                                 requested_scope="")
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", _never_called):
            with self.assertRaises(CommunicationDenied):
                fetch_feed("https://example.invalid/feed", policy=policy)


# Tests below mock `urllib.request.urlopen` and use `.invalid` placeholder
# hosts, which by RFC 6761 never resolve. The SSRF guard added in cycle 006
# resolves the host BEFORE the socket opens, so it correctly refuses those
# placeholders and these tests would fail for the wrong reason.
#
# They bypass the guard deliberately. Each is testing a DIFFERENT property
# -- budget accounting, objective validation, method selection -- and the
# guard itself is covered by `TestSsrfGuard` below, which does not mock it.
# Bypassing here does not reduce coverage of the guard; it stops unrelated
# tests from depending on DNS, which would also make the suite
# network-dependent and break the offline-CI rule every other suite obeys.
def _no_ssrf_check():
    return mock.patch("foundation.mouth_common._reject_unsafe_url")


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
                with _no_ssrf_check(), mock.patch("urllib.request.urlopen", _never_called):
                    with self.assertRaises(UnboundedDiscoveryObjective):
                        fetch_feed("https://example.invalid/f", policy=policy)

    def test_an_empty_objective_is_refused(self):
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", _never_called):
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
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", return_value=_Resp()):
            self.assertEqual(
                fetch_feed("https://example.invalid/f", policy=VALID),
                b"<feed/>")


class TestThereIsExactlyOneSocket(unittest.TestCase):
    """Every socket in this repository lives in a SANCTIONED, GATED module.

    The control plane's guarantee is not "there is one door" — it is "no
    UNGATED door exists". As of 2026-09-04 there are two sockets, each
    behind its own independent gate:

      - foundation/mouth_common.py    — reads, gated on the DISCOVERY
        control plane (authorize_discovery / DiscoveryPolicy).
      - foundation/telegram_notify.py — the operator push (Kyle's own
        Telegram), gated on communication_gate's NOTIFY_OPERATOR scope
        (authorize_communication, re-derived from a named authorization
        before any send). Proven gated in test_telegram_notify.py
        (authorization is checked before credentials are even read).

    A THIRD, unsanctioned caller still fails this test — which is the
    property that actually matters. The earlier "exactly mouth_common"
    form was correct only while reads were the sole network action; the
    same "re-check an absence claim when the thing gets built" lesson the
    communication_gate docstring teaches is applied here rather than
    leaving a now-false invariant as camouflage.
    """

    ALLOWED = {"foundation/mouth_common.py", "foundation/telegram_notify.py"}
    # Every ALLOWED socket module must reference its gate — a widened
    # allowlist that dropped this check would be a real weakening.
    GATE_REFERENCE = {
        "foundation/mouth_common.py": "authorize_discovery",
        "foundation/telegram_notify.py": "authorize_communication",
    }

    def _network_callers(self):
        found = set()
        for path in sorted(REPO_ROOT.rglob("*.py")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if "/tests/" in rel or rel.startswith("tests/"):
                continue
            if _is_build_output(rel):
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

    def test_only_sanctioned_gated_modules_open_a_socket(self):
        callers = self._network_callers()
        self.assertEqual(
            callers, self.ALLOWED,
            f"a new network caller appeared outside the sanctioned set: "
            f"{sorted(callers - self.ALLOWED)}. Route it through an existing "
            f"gated module, or the control plane is bypassable.")

    def test_every_socket_module_references_its_gate(self):
        # A socket without its gate in the same module is an ungated door
        # wearing a sanctioned name. Check the gate symbol is present.
        for rel, gate in self.GATE_REFERENCE.items():
            src = (REPO_ROOT / rel).read_text(errors="ignore")
            self.assertIn(
                gate, src,
                f"{rel} opens a socket but does not reference its gate "
                f"{gate!r} — an ungated egress.")


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


class TestQuantifiedClassObjectivesAreRefused(unittest.TestCase):
    """An independent adversarial review broke the first quantifier check.

    `_UNBOUNDED_QUANTIFIER` matched bare pronouns only, while the comment
    beside it claimed an unbounded objective was caught "however it is
    phrased". These five strings all passed validation and would have
    reached `urlopen`. A quantifier applied to a NOUN was invisible to a
    pronoun-only pattern -- the whole class the first version missed.
    """

    BYPASSES = (
        "download every release across every repository on github",
        "collect all public github repos matching *",
        "mirror the full github issue tracker",
        "monitor every repo in this github org",
        "crawl each page under this domain",
        "index all packages on pypi",
        "fetch any user account data",
    )

    def test_each_known_bypass_is_refused(self):
        for objective in self.BYPASSES:
            with self.subTest(objective=objective):
                policy = DiscoveryPolicy(objective=objective,
                                         requested_scope="READ_URL")
                with _no_ssrf_check(), mock.patch("urllib.request.urlopen", _never_called):
                    with self.assertRaises(UnboundedDiscoveryObjective):
                        fetch_feed("https://example.invalid/f", policy=policy)

    def test_the_six_real_mouth_objectives_still_pass(self):
        """The other half of the proof. A validator that refuses every
        objective is not a gate, it is an outage."""
        import importlib
        from foundation.discovery_authorization import authorize_discovery
        for name in ("mouth_github_releases", "mouth_pypi",
                     "mouth_github_issues", "mouth_github_commits",
                     "mouth_npm", "target_mapping"):
            with self.subTest(mouth=name):
                mod = importlib.import_module(f"foundation.{name}")
                self.assertTrue(authorize_discovery(mod.DISCOVERY_POLICY))


class TestTheBudgetIsRealNotDecorative(unittest.TestCase):
    """`max_queries` / `max_wall_clock_seconds` / `max_results` were
    declared, serialised by to_dict(), and read by NOTHING -- confirmed
    by a repo-wide grep. Meanwhile fetch_feed's docstring told callers a
    policy names a budget. The gate advertised a limit it did not have.
    """

    class _Resp:
        def read(self, n=-1): return b"<feed/>"
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def setUp(self):
        reset_budgets()
        self.addCleanup(reset_budgets)
        self.policy = DiscoveryPolicy(
            objective="observe the release feed of one named repository",
            requested_scope="READ_URL", max_queries=3)

    def test_the_budget_stops_the_fourth_request(self):
        opened = []
        def counting(*a, **k):
            opened.append(1)
            return self._Resp()
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", counting):
            for _ in range(3):
                fetch_feed("https://example.invalid/f", policy=self.policy)
            with self.assertRaises(DiscoveryBudgetExhausted):
                fetch_feed("https://example.invalid/f", policy=self.policy)
        self.assertEqual(len(opened), 3,
                         "a refused request must cost no socket")

    def test_a_freshly_constructed_identical_policy_shares_the_budget(self):
        """Otherwise a caller resets its own budget by rebuilding the
        object in a loop -- the exact bypass this closes."""
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", lambda *a, **k: self._Resp()):
            for _ in range(3):
                fetch_feed("https://example.invalid/f", policy=self.policy)
            twin = DiscoveryPolicy(
                objective="observe the release feed of one named repository",
                requested_scope="READ_URL", max_queries=3)
            with self.assertRaises(DiscoveryBudgetExhausted):
                fetch_feed("https://example.invalid/f", policy=twin)

    def test_exhaustion_is_a_refusal_not_a_silent_false(self):
        """DiscoveryBudgetExhausted subclasses CommunicationDenied so an
        existing caller that handles refusal handles this too."""
        self.assertTrue(issubclass(DiscoveryBudgetExhausted,
                                   CommunicationDenied))

    def test_the_budget_is_observable(self):
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", lambda *a, **k: self._Resp()):
            fetch_feed("https://example.invalid/f", policy=self.policy)
        self.assertEqual(budget_spent(self.policy), 1)

    def test_a_different_objective_has_its_own_budget(self):
        other = DiscoveryPolicy(
            objective="observe the npm registry record for one named package",
            requested_scope="READ_API", max_queries=3)
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen", lambda *a, **k: self._Resp()):
            for _ in range(3):
                fetch_feed("https://example.invalid/f", policy=self.policy)
            fetch_feed("https://example.invalid/f", policy=other)
        self.assertEqual(budget_spent(other), 1)

    def test_the_window_expires_and_a_new_burst_is_allowed(self):
        """max_wall_clock_seconds bounds one burst. Refusing forever would
        make a long-lived process permanently mute."""
        from foundation.discovery_authorization import spend_query
        for _ in range(3):
            spend_query(self.policy, now=100.0)
        with self.assertRaises(DiscoveryBudgetExhausted):
            spend_query(self.policy, now=100.0)
        # Past the window: a fresh burst is permitted.
        self.assertEqual(
            spend_query(self.policy,
                        now=100.0 + self.policy.max_wall_clock_seconds + 1), 1)


class TestPostIsNotASecondPathAroundTheGate(unittest.TestCase):
    """POST was added to `fetch_feed` on 2026-09-01 so EU TED could be
    reached (its search endpoint is POST-only; GET returns 405). TED
    publishes ~397,000 open notices under CC BY 4.0 with no key.

    The danger of adding a method to the only socket in the repository is
    that it becomes a second door with weaker locks. These tests exist to
    prove it is the same door: every gate that guards GET must guard POST
    identically, and the request body must not be a way to smuggle a
    different content type through.
    """

    URL = "https://example.invalid/search"
    BODY = {"query": "x", "limit": 1}

    def test_post_without_a_policy_is_refused(self):
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=None, json_body=self.BODY)

    def test_post_with_a_fake_policy_object_is_refused(self):
        class NotAPolicy:
            objective = "looks real"
            requested_scope = "READ_API"
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=NotAPolicy(), json_body=self.BODY)

    def test_raw_bytes_body_is_refused(self):
        """A caller handing over raw bytes could choose its own content
        type, or a chunked/multipart shape, through the one socket."""
        reset_budgets()
        p = DiscoveryPolicy(objective="test: raw body refusal on the search endpoint",
                            requested_scope="READ_API", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=p, json_body=b"raw bytes")

    def test_an_oversized_request_body_is_refused(self):
        reset_budgets()
        p = DiscoveryPolicy(objective="test: oversized body refusal on search",
                            requested_scope="READ_API", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=p, json_body={"q": "A" * 70_000})

    def test_budget_is_charged_for_post_exactly_as_for_get(self):
        """The gate that matters most. If POST skipped spend_query, an
        attacker-influenced caller could drain a source for free."""
        reset_budgets()
        p = DiscoveryPolicy(objective="test: budget is charged on the post path",
                            requested_scope="READ_API", max_queries=1)
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen") as m:
            m.return_value.__enter__.return_value.read.return_value = b"{}"
            fetch_feed(self.URL, policy=p, json_body=self.BODY)
            with self.assertRaises(DiscoveryBudgetExhausted):
                fetch_feed(self.URL, policy=p, json_body=self.BODY)

    def test_no_body_still_sends_a_get(self):
        """POST must be reachable only by supplying a body, so PUT/DELETE/
        PATCH stay unreachable by construction rather than by validation."""
        reset_budgets()
        p = DiscoveryPolicy(objective="test: default method remains get",
                            requested_scope="READ_API", max_queries=2)
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen") as m:
            m.return_value.__enter__.return_value.read.return_value = b"{}"
            fetch_feed(self.URL, policy=p)
            request = m.call_args[0][0]
            self.assertEqual(request.get_method(), "GET")
            self.assertIsNone(request.data)


class TestFormBodyIsTheSameDoor(unittest.TestCase):
    """Form-encoded POST was added on 2026-09-02 for one measured
    reason: Ireland's eTenders export endpoint is a Struts-era form
    handler that ignores a JSON body entirely, so the largest
    concentration of English-language procurement this project has found
    was unreachable purely because this function could serialise only one
    content type.

    Same danger as when POST itself was added, same answer: widening what
    may be SENT must never widen who may send it. Every guard the JSON
    path carries is asserted here against the form path.
    """

    URL = "https://example.invalid/export"
    FORM = {"isExport": "true", "searchType": "cft"}

    def test_form_post_without_a_policy_is_refused(self):
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=None, form_body=self.FORM)

    def test_form_body_must_be_a_mapping(self):
        p = DiscoveryPolicy(objective="probe form body type",
                            requested_scope="READ_API", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=p, form_body=b"raw bytes")

    def test_form_body_respects_the_request_size_cap(self):
        p = DiscoveryPolicy(objective="probe form body size",
                            requested_scope="READ_API", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=p, form_body={"q": "A" * 70_000})

    def test_read_url_scope_cannot_send_a_form_body(self):
        """The scope check must cover BOTH body kinds. A guard that
        covered only json_body would let READ_URL drive a form POST --
        the exact bypass the scope check was added to close."""
        p = DiscoveryPolicy(objective="probe form body scope",
                            requested_scope="READ_URL", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=p, form_body=self.FORM)

    def test_supplying_both_bodies_is_refused(self):
        """One request, one body, one content type. A caller that passed
        both has not decided what request it is making, and guessing for
        it is how a content type gets chosen by accident."""
        p = DiscoveryPolicy(objective="probe dual body refusal",
                            requested_scope="READ_API", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed(self.URL, policy=p,
                       json_body={"a": 1}, form_body={"b": 2})

    def test_form_post_is_charged_against_the_budget(self):
        p = DiscoveryPolicy(objective="probe form body budget",
                            requested_scope="READ_API", max_queries=1)
        with self.assertRaises(Exception):
            fetch_feed(self.URL, policy=p, form_body=self.FORM)
        with self.assertRaises(DiscoveryBudgetExhausted):
            fetch_feed(self.URL, policy=p, form_body=self.FORM)

    def test_form_post_still_cannot_reach_a_private_address(self):
        p = DiscoveryPolicy(objective="probe form body ssrf",
                            requested_scope="READ_API", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed("https://localhost/export", policy=p,
                       form_body=self.FORM)


class TestSsrfGuard(unittest.TestCase):
    """Blue-team pass 006, highest-severity finding, confirmed statically.

    `url` is caller-supplied and was passed straight into
    `urllib.request.Request`. Grepping the entire control plane for any
    scheme, host or IP check returned nothing. Authorization answered
    "may this caller fetch?"; nothing answered "fetch WHAT?".

    Adding POST made it worse: a request that can carry a body to an
    internal address is a far more useful weapon than one that can only
    GET.
    """

    def _policy(self, scope="READ_API"):
        reset_budgets()
        return DiscoveryPolicy(
            objective="test: ssrf guard on the fetch path",
            requested_scope=scope, max_queries=4)

    def test_file_scheme_is_refused(self):
        with self.assertRaises(CommunicationDenied):
            fetch_feed("file:///etc/hostname", policy=self._policy())

    def test_plaintext_http_is_refused(self):
        with self.assertRaises(CommunicationDenied):
            fetch_feed("http://example.com/feed", policy=self._policy())

    def test_cloud_metadata_address_is_refused(self):
        """169.254.169.254 is the single most valuable SSRF target in any
        cloud environment: it serves instance credentials."""
        with self.assertRaises(CommunicationDenied):
            fetch_feed("https://169.254.169.254/latest/meta-data/",
                       policy=self._policy())

    def test_loopback_is_refused_even_by_name(self):
        """Refusing the literal 127.0.0.1 and allowing 'localhost' would
        be a guard that only catches the careless attacker."""
        with self.assertRaises(CommunicationDenied):
            fetch_feed("https://localhost:8080/x", policy=self._policy())

    def test_rfc1918_is_refused(self):
        with self.assertRaises(CommunicationDenied):
            fetch_feed("https://10.0.0.1/x", policy=self._policy())

    def test_an_unresolvable_host_is_refused_not_attempted(self):
        """A host that cannot be resolved cannot be shown to be public, so
        it is refused rather than tried and hoped about."""
        with self.assertRaises(CommunicationDenied):
            fetch_feed("https://this-host-does-not-exist.invalid/x",
                       policy=self._policy())


class TestScopeIsNotDecorative(unittest.TestCase):
    """Blue-team pass 006: READ_URL and READ_API were only ever checked
    for set-membership. Nothing compared the declared scope against what
    the request actually did, so a READ_URL policy could drive a POST
    carrying a caller-controlled body.

    A scope that constrains nothing is a label, and this repository's
    entire argument is that a label is not a control.
    """

    def test_read_url_scope_cannot_send_a_body(self):
        reset_budgets()
        p = DiscoveryPolicy(objective="test: read_url must not permit a post body",
                            requested_scope="READ_URL", max_queries=2)
        with self.assertRaises(CommunicationDenied):
            fetch_feed("https://example.com/x", policy=p,
                       json_body={"query": "x"})

    def test_read_url_scope_may_still_get(self):
        reset_budgets()
        p = DiscoveryPolicy(objective="test: read_url still permits a plain get",
                            requested_scope="READ_URL", max_queries=2)
        with _no_ssrf_check(), mock.patch("urllib.request.urlopen") as m:
            m.return_value.__enter__.return_value.read.return_value = b"{}"
            self.assertEqual(fetch_feed("https://example.com/x", policy=p), b"{}")
