"""Tests for `foundation/operator_cli.py`.

Offline. No test here passes --live or otherwise reaches
`hunt_multi()`/`run_hunt_loop()`'s real network path -- every network-
touching command is exercised only in its dry-run (default) form, which
this module's own contract guarantees never opens a socket.
"""

import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from foundation import operator_cli
from foundation.dossier import BusinessFacts, Referee
from foundation.qualification import OperatorProfile


def _run(argv):
    """Run main() capturing stdout/stderr, return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = operator_cli.main(argv)
    return code, out.getvalue(), err.getvalue()


class TestLoadOperatorProfileFallback(unittest.TestCase):
    def test_falls_back_to_example_when_real_file_absent(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "operator_profile.json"
            with patch.object(operator_cli, "PROFILE_PATH", missing):
                loaded = operator_cli.load_operator_profile()
        self.assertTrue(loaded.is_example)
        self.assertEqual(loaded.source_path, operator_cli.PROFILE_EXAMPLE_PATH)
        self.assertIsInstance(loaded.operator, OperatorProfile)
        # The example file documents the real current operator state.
        self.assertEqual(loaded.operator.staff_count, 1)
        self.assertEqual(loaded.operator.certifications, frozenset())
        self.assertIsNone(loaded.operator.insurance_cover_eur)
        self.assertEqual(loaded.operator.corporate_references, ())
        self.assertEqual(loaded.operator.languages, frozenset({"ENG"}))

    def test_reads_real_file_when_present_and_ignores_doc_keys(self):
        with tempfile.TemporaryDirectory() as td:
            real = Path(td) / "operator_profile.json"
            real.write_text(json.dumps({
                "_comment": "ignore me",
                "name": "Real Operator Pty Ltd",
                "staff_count": 3,
                "certifications": ["ISO27001"],
                "insurance_cover_eur": 250000.0,
                "corporate_references": ["Acme Corp 2024"],
                "languages": ["ENG", "DEU"],
                "business_facts": {
                    "abn": "12 345 678 901",
                    "skills": ["penetration testing"],
                    "referees": [
                        {"name": "Jane Doe", "organisation": "Acme",
                         "contact": "jane@acme.example"},
                    ],
                },
            }))
            with patch.object(operator_cli, "PROFILE_PATH", real):
                loaded = operator_cli.load_operator_profile()
        self.assertFalse(loaded.is_example)
        self.assertEqual(loaded.operator.name, "Real Operator Pty Ltd")
        self.assertEqual(loaded.operator.staff_count, 3)
        self.assertEqual(loaded.operator.certifications, frozenset({"ISO27001"}))
        self.assertEqual(loaded.operator.languages, frozenset({"ENG", "DEU"}))
        self.assertIsInstance(loaded.business_facts, BusinessFacts)
        self.assertEqual(loaded.business_facts.abn, "12 345 678 901")
        self.assertEqual(loaded.business_facts.skills, ("penetration testing",))
        self.assertEqual(len(loaded.business_facts.referees), 1)
        self.assertIsInstance(loaded.business_facts.referees[0], Referee)

    def test_missing_required_field_raises_profile_load_error(self):
        with tempfile.TemporaryDirectory() as td:
            real = Path(td) / "operator_profile.json"
            real.write_text(json.dumps({"name": "No Staff Count"}))
            with patch.object(operator_cli, "PROFILE_PATH", real):
                with self.assertRaises(operator_cli.ProfileLoadError):
                    operator_cli.load_operator_profile()

    def test_malformed_json_raises_profile_load_error(self):
        with tempfile.TemporaryDirectory() as td:
            real = Path(td) / "operator_profile.json"
            real.write_text("{not valid json")
            with patch.object(operator_cli, "PROFILE_PATH", real):
                with self.assertRaises(operator_cli.ProfileLoadError):
                    operator_cli.load_operator_profile()

    def test_neither_real_nor_example_present_raises(self):
        with tempfile.TemporaryDirectory() as td:
            missing_real = Path(td) / "operator_profile.json"
            missing_example = Path(td) / "operator_profile.example.json"
            with patch.object(operator_cli, "PROFILE_PATH", missing_real), \
                 patch.object(operator_cli, "PROFILE_EXAMPLE_PATH", missing_example):
                with self.assertRaises(operator_cli.ProfileLoadError):
                    operator_cli.load_operator_profile()


class TestExampleProfileFileItself(unittest.TestCase):
    """The example file this repo ships must actually document the real
    current operator state (staff_count=1, no certs, no insurance, no
    corporate references, ENG only) -- not placeholder nonsense."""

    def test_example_file_matches_real_current_state(self):
        raw = json.loads(operator_cli.PROFILE_EXAMPLE_PATH.read_text())
        self.assertEqual(raw["staff_count"], 1)
        self.assertEqual(raw["certifications"], [])
        self.assertIsNone(raw["insurance_cover_eur"])
        self.assertEqual(raw["corporate_references"], [])
        self.assertEqual(raw["languages"], ["ENG"])

    def test_example_file_loads_cleanly_through_the_real_loader(self):
        loaded = operator_cli.load_operator_profile(
            path=Path("/nonexistent/operator_profile.json"))
        self.assertTrue(loaded.is_example)
        self.assertIsInstance(loaded.operator, OperatorProfile)


class TestNoArguments(unittest.TestCase):
    def test_bare_invocation_prints_help_and_succeeds(self):
        code, out, err = _run([])
        self.assertEqual(code, 0)
        self.assertIn("usage", out.lower())


class TestProfileCommand(unittest.TestCase):
    def test_profile_command_prints_fields_and_succeeds(self):
        code, out, err = _run(["profile"])
        self.assertEqual(code, 0)
        self.assertIn("name", out)
        self.assertIn("staff_count", out)
        self.assertIn("languages", out)
        self.assertIn("business_facts", out)


class TestDossierCommand(unittest.TestCase):
    def test_dossier_command_renders_draft_and_missing_facts(self):
        code, out, err = _run(["dossier"])
        self.assertEqual(code, 0)
        self.assertIn("DRAFT", out)
        self.assertIn("MISSING FACTS BY SCHEME", out)
        for scheme in ("NSW_ICT_SERVICES_SCHEME", "UK_CCS_CYBER_SECURITY_SERVICES_3_DPS",
                       "ICN_GATEWAY", "QLD_SUPPLIER_PORTAL"):
            self.assertIn(scheme, out)


class TestHuntDryRunDefault(unittest.TestCase):
    """`--live` is never passed here -- these tests assert dry-run is the
    default and that no network call is attempted."""

    def test_hunt_with_no_arguments_is_dry_run_and_succeeds(self):
        code, out, err = _run(["hunt"])
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertIn("Pass --live", out)

    def test_brief_with_no_arguments_is_dry_run_and_succeeds(self):
        code, out, err = _run(["brief"])
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)

    def test_loop_with_no_arguments_is_dry_run_and_succeeds(self):
        code, out, err = _run(["loop"])
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertIn("kill switch", out)

    def test_hunt_dry_run_never_calls_hunt_multi(self):
        with patch.object(operator_cli, "hunt_multi") as mock_hunt_multi:
            code, out, err = _run(["hunt"])
        mock_hunt_multi.assert_not_called()
        self.assertEqual(code, 0)

    def test_loop_dry_run_never_calls_run_hunt_loop(self):
        with patch.object(operator_cli, "run_hunt_loop") as mock_loop:
            code, out, err = _run(["loop"])
        mock_loop.assert_not_called()
        self.assertEqual(code, 0)

    def test_hunt_custom_keyword_reflected_in_dry_run_output(self):
        code, out, err = _run(["hunt", "--keyword", "penetration testing"])
        self.assertEqual(code, 0)
        self.assertIn("penetration testing", out)


class TestIncomeCommand(unittest.TestCase):
    """`income` follows the same dry-run-by-default, --live-required
    pattern as `hunt`/`brief`/`loop`."""

    def test_income_with_no_arguments_is_dry_run_and_succeeds(self):
        code, out, err = _run(["income"])
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertIn("Pass --live", out)
        self.assertIn("mouth_bounty", out)
        self.assertIn("mouth_gigs", out)

    def test_income_dry_run_never_calls_watch(self):
        with patch.object(operator_cli.income_watch, "watch") as mock_watch:
            code, out, err = _run(["income"])
        mock_watch.assert_not_called()
        self.assertEqual(code, 0)

    def test_income_live_calls_watch_and_renders_report(self):
        from foundation import income_watch as iw

        fake_report = iw.IncomeWatchReport(
            observed_at="2026-09-02T00:00:00+00:00",
            results=(),
            signals=(),
            new_signals=(),
        )
        with patch.object(operator_cli.income_watch, "watch",
                           return_value=fake_report) as mock_watch:
            code, out, err = _run(["income", "--live"])
        mock_watch.assert_called_once()
        self.assertEqual(code, 0)
        self.assertIn("zero new programs/gigs observed this cycle", out)

    def test_income_empty_result_exits_zero(self):
        from foundation import income_watch as iw

        fake_report = iw.IncomeWatchReport(
            observed_at="2026-09-02T00:00:00+00:00",
            results=(), signals=(), new_signals=(),
        )
        with patch.object(operator_cli.income_watch, "watch", return_value=fake_report):
            code, out, err = _run(["income", "--live"])
        self.assertEqual(code, 0)

    def test_income_live_failure_from_watch_is_reported_not_a_traceback(self):
        with patch.object(operator_cli.income_watch, "watch",
                           side_effect=RuntimeError("boom")):
            code, out, err = _run(["income", "--live"])
        self.assertEqual(code, 1)
        self.assertIn("INCOME WATCH FAILED", err)


class TestHuntLiveUsesInjectedFetch(unittest.TestCase):
    """Proves the live path builds a real DiscoveryPolicy and calls
    `hunt_multi()` -- without ever letting a real socket open, by
    replacing `hunt_multi` itself with a fake that asserts on its
    arguments rather than fetching anything."""

    def test_live_hunt_builds_a_real_policy_and_calls_hunt_multi(self):
        from foundation.hunt import HuntReport
        from foundation.discovery_authorization import DiscoveryPolicy

        captured = {}

        def fake_hunt_multi(query, operator, sources, *, capability=None, now=None):
            captured["query"] = query
            captured["operator"] = operator
            captured["sources"] = sources
            return HuntReport(entries=(), fetched=0, assessed=0, skipped=(),
                               objective="test")

        def fake_sources_for_query(ted_query, *, ted_limit=50, ted_policy=None,
                                    include=None):
            self.assertIsInstance(ted_policy, DiscoveryPolicy)
            self.assertTrue(ted_policy.objective.strip())
            captured["ted_query"] = ted_query
            captured["policy"] = ted_policy
            return ()

        with patch.object(operator_cli, "hunt_multi", side_effect=fake_hunt_multi), \
             patch.object(operator_cli, "sources_for_query",
                          side_effect=fake_sources_for_query):
            code, out, err = _run(["hunt", "--live", "--keyword", "cyber security"])

        self.assertEqual(code, 0)
        self.assertEqual(captured["query"], "cyber security")
        self.assertIn('FT ~ ("cyber security")', captured["ted_query"])
        self.assertIsInstance(captured["policy"], DiscoveryPolicy)

    def test_live_hunt_with_unbounded_objective_is_refused_not_crashed(self):
        # DiscoveryPolicy construction itself does not validate eagerly
        # (see discovery_authorization.py) -- the real hunt_multi()
        # catches an UnboundedDiscoveryObjective per-source and records
        # it as a skip, never a crash. Simulated here with a fake
        # hunt_multi so this test never opens a socket.
        from foundation.hunt import HuntReport
        from foundation.discovery_authorization import UnboundedDiscoveryObjective

        def fake_hunt_multi(query, operator, sources, *, capability=None, now=None):
            return HuntReport(
                entries=(), fetched=0, assessed=0,
                skipped=(f"TED: fetch failed ({UnboundedDiscoveryObjective.__name__}: "
                          f"objective is unbounded)",),
                objective="test")

        with patch.object(operator_cli, "hunt_multi", side_effect=fake_hunt_multi), \
             patch.object(operator_cli, "sources_for_query", return_value=()):
            code, out, err = _run(["hunt", "--live", "--objective", "everything"])
        self.assertEqual(code, 0)
        self.assertIn("UnboundedDiscoveryObjective", out)


class TestExitCodes(unittest.TestCase):
    def test_empty_hunt_report_is_success_not_failure(self):
        from foundation.hunt import HuntReport

        def fake_hunt_multi(query, operator, sources, *, capability=None, now=None):
            return HuntReport(entries=(), fetched=0, assessed=0, skipped=(),
                               objective="test")

        with patch.object(operator_cli, "hunt_multi", side_effect=fake_hunt_multi), \
             patch.object(operator_cli, "sources_for_query", return_value=()):
            code, out, err = _run(["hunt", "--live"])
        self.assertEqual(code, 0)
        self.assertIn("No notice was assessed", out)

    def test_hunt_multi_raising_is_a_real_failure(self):
        with patch.object(operator_cli, "hunt_multi", side_effect=RuntimeError("boom")), \
             patch.object(operator_cli, "sources_for_query", return_value=()):
            code, out, err = _run(["hunt", "--live"])
        self.assertNotEqual(code, 0)
        self.assertIn("HUNT FAILED", err)


class TestBuildParser(unittest.TestCase):
    def test_every_registered_subcommand_is_runnable(self):
        """Was `test_all_six_subcommands_registered` and asserted a
        frozen set of six names. That is the same defect already found
        in `test_sources.py`: a test pinned to a hardcoded list cannot
        notice the list growing, so a seventh subcommand can be added
        and the test still passes without ever exercising it.

        Now it asserts a property instead -- every registered subcommand
        has a callable bound to it -- which stays true as the CLI
        grows and would fail on a subcommand wired up with no handler."""
        parser = operator_cli.build_parser()
        actions = [a for a in parser._subparsers._group_actions
                   if hasattr(a, "choices")]
        self.assertTrue(actions)
        choices = actions[0].choices
        self.assertGreaterEqual(len(choices), 6)
        for name, subparser in choices.items():
            func = subparser.get_default("func")
            self.assertTrue(
                callable(func),
                f"subcommand {name!r} is registered with no handler")

    def test_the_core_subcommands_are_present(self):
        """Named separately from the property above: these six are the
        documented interface in HOW_TO_RUN.md, and removing one is a
        breaking change a property test would not catch."""
        parser = operator_cli.build_parser()
        actions = [a for a in parser._subparsers._group_actions
                   if hasattr(a, "choices")]
        choices = set(actions[0].choices.keys())
        for required in ("hunt", "brief", "loop", "income", "dossier",
                         "profile"):
            self.assertIn(required, choices)


class TestDealsCommand(unittest.TestCase):
    """`deal_pipeline.py` was built, seeded with twelve real positions,
    and tested at 33 cases -- and reachable only by someone who knew to
    import it. This repository has already documented four mouths and a
    classifier that reached exactly that state; the audit called it the
    highest-severity finding of that session. This pins the wiring."""

    def test_deals_is_a_registered_subcommand(self):
        from foundation.operator_cli import build_parser
        parser = build_parser()
        actions = [a for a in parser._actions if hasattr(a, "choices") and a.choices]
        names = set()
        for a in actions:
            names.update(a.choices.keys())
        self.assertIn("deals", names)

    def test_deals_runs_with_no_arguments(self):
        from foundation.operator_cli import main
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["deals"])
        self.assertEqual(rc, 0)
        self.assertIn("DEAL PIPELINE", buf.getvalue())

    def test_deals_never_touches_the_network(self):
        """Reading a local ledger must not open a socket. `deals` has no
        --live flag for exactly this reason."""
        from foundation.operator_cli import main
        with patch("urllib.request.urlopen",
                        side_effect=AssertionError("network touched")):
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(["deals"])
        self.assertEqual(rc, 0)

    def test_malformed_move_is_refused_without_a_traceback(self):
        from foundation.operator_cli import main
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            rc = main(["deals", "--move", "no-colon-here"])
        self.assertEqual(rc, 1)
        self.assertIn("REFUSED", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_unknown_deal_id_is_refused_with_a_useful_message(self):
        from foundation.operator_cli import main
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            rc = main(["deals", "--move", "does-not-exist:APPROACHED"])
        self.assertEqual(rc, 1)
        self.assertIn("no deal with id", err.getvalue())


if __name__ == "__main__":
    unittest.main()
