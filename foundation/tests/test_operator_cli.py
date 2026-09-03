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


class TestTedQueryIsBoundedByPublicationDate(unittest.TestCase):
    """A LIVE SWEEP ON 2026-09-03 ASSESSED 120 NOTICES AND 100 OF THEM
    WERE PUBLISHED IN 2016 AND 2017.

    Nothing raised, nothing looked broken -- the CLI just never bounded
    TED by date, so every sweep spent its entire budget banding notices
    that closed years ago and printing them as findings. These tests
    exist so the bound cannot quietly go missing again."""

    def test_the_default_query_carries_a_publication_date_bound(self):
        code, out, err = _run(["hunt"])
        self.assertEqual(code, 0)
        self.assertIn("publication-date >= today(-365)", out)

    def test_the_bound_is_a_publication_date_not_a_deadline(self):
        """`deadline-receipt-request` is the filter that would actually
        mean 'still open', and it measures ZERO results when combined
        with an FT clause. Emitting it here would silently return
        nothing -- a hunt that finds no notices at all, forever."""
        code, out, err = _run(["hunt"])
        self.assertNotIn("deadline-receipt-request", out)

    def test_the_window_is_configurable(self):
        code, out, err = _run(["hunt", "--published-within-days", "30"])
        self.assertEqual(code, 0)
        self.assertIn("today(-30)", out)

    def test_zero_days_sweeps_the_whole_archive_deliberately(self):
        code, out, err = _run(["hunt", "--published-within-days", "0"])
        self.assertEqual(code, 0)
        self.assertNotIn("publication-date", out)

    def test_an_explicit_ted_query_is_passed_through_untouched(self):
        """A caller who writes their own expert query is the authority
        on it -- appending a date clause to someone else's query could
        silently change what it matches."""
        code, out, err = _run(
            ["hunt", "--ted-query", 'classification-cpv IN (72000000)'])
        self.assertEqual(code, 0)
        self.assertIn("classification-cpv IN (72000000)", out)
        self.assertNotIn("publication-date", out)

    def test_brief_gets_the_same_bound_as_hunt(self):
        """The bug was one line repeated in three subcommands. Fixing
        only the one that was measured would have left the others
        sweeping the archive."""
        code, out, err = _run(["brief"])
        self.assertEqual(code, 0)
        self.assertIn("publication-date >= today(-365)", out)

    def test_loop_gets_the_same_bound_as_hunt(self):
        code, out, err = _run(["loop"])
        self.assertEqual(code, 0)
        self.assertIn("publication-date >= today(-365)", out)


class TestSourceListIsReadFromTheRegistry(unittest.TestCase):
    """This file printed a frozen `TED, NZ_GETS, UK_CONTRACTS_FINDER`
    for several cycles after the registry grew past three -- telling
    the operator which sources were swept, and being wrong."""

    def test_dry_run_names_every_registered_source(self):
        from foundation.sources import ALL_SOURCES
        code, out, err = _run(["hunt"])
        self.assertEqual(code, 0)
        for source in ALL_SOURCES:
            self.assertIn(source.source_id, out,
                          f"{source.source_id} is registered but not named")

    def test_no_hand_written_source_list_survives_in_the_source(self):
        from pathlib import Path as _P
        src = _P(operator_cli.__file__).read_text(encoding="utf-8")
        self.assertNotIn('"  sources     : TED, NZ_GETS', src)


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


class TestDocumentTextExtraction(unittest.TestCase):
    """Both bugs below were found the same way on 2026-09-03: by trying
    to read the selection criteria out of real Irish procurement
    documents and getting markup instead of words. `assess_access()`
    then scans that markup and reports on it."""

    def _write(self, data: bytes, name="doc.bin"):
        d = tempfile.mkdtemp()
        p = Path(d) / name
        p.write_bytes(data)
        return p

    def _docx(self, paragraphs):
        import io
        import zipfile
        body = "".join(
            f'<w:p w14:paraId="672A6659" w:rsidR="006D172B">'
            f'<w:r><w:t>{p}</w:t></w:r></w:p>' for p in paragraphs)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("word/document.xml",
                       f'<?xml version="1.0"?><w:document><w:body>{body}'
                       f'</w:body></w:document>')
        return buf.getvalue()

    def test_docx_paragraph_attributes_do_not_leak_into_the_text(self):
        """The old substitution ate `<w:p` and left `w14:paraId="..."`
        behind as ordinary text, because the remainder no longer began
        with `<` for the tag-strip to match. Measured on RTE's real
        25P041 document: 191,868 characters of Word revision ids."""
        path = self._write(self._docx(["Minimum turnover of EUR 350,000."]))
        text = operator_cli._read_document_text(path)
        self.assertIn("Minimum turnover of EUR 350,000.", text)
        self.assertNotIn("paraId", text)
        self.assertNotIn("rsidR", text)
        self.assertNotIn("w:p", text)

    def test_docx_paragraphs_are_separated(self):
        path = self._write(self._docx(["First clause.", "Second clause."]))
        text = operator_cli._read_document_text(path)
        self.assertIn("First clause.", text)
        self.assertIn("Second clause.", text)
        self.assertNotIn("First clause.Second clause.", text)

    def test_rtf_is_detected_by_magic_bytes_not_extension(self):
        r"""`{\rtf` is FIVE bytes. The magic-byte read was four bytes
        wide, so this detection silently never fired and RTF fell to
        the plain-text branch -- 2.7 million characters of control
        words, handed to the barrier scanner as document text."""
        rtf = (rb"{\rtf1\ansi{\fonttbl{\f0 Times New Roman;}}"
               rb"\f0 A minimum annual turnover of 250k per annum.\par}")
        path = self._write(rtf, name="pqq.unknown")
        text = operator_cli._read_document_text(path)
        self.assertIn("A minimum annual turnover of 250k per annum.", text)
        self.assertNotIn("rtf1", text)
        self.assertNotIn(r"\ansi", text)

    def test_rtf_font_and_style_tables_are_dropped_whole(self):
        """Font and style NAMES are indistinguishable from prose once
        the control words are stripped -- keeping them buries the
        document under hundreds of typeface names."""
        rtf = (rb"{\rtf1\ansi{\fonttbl{\f0 Wingdings;}{\f1 Courier New;}}"
               rb"{\stylesheet{\s1 Heading Style Name;}}"
               rb"\f0 Real clause text.\par}")
        text = operator_cli._read_document_text(self._write(rtf))
        self.assertIn("Real clause text.", text)
        self.assertNotIn("Wingdings", text)
        self.assertNotIn("Heading Style Name", text)

    def test_rtf_paragraph_and_cell_breaks_become_whitespace(self):
        rtf = rb"{\rtf1\ansi One\par Two\cell Three\par}"
        text = operator_cli._read_document_text(self._write(rtf))
        self.assertIn("One", text)
        self.assertIn("Two", text)
        self.assertIn("Three", text)
        self.assertNotIn("OneTwo", text.replace(" ", ""))

    def test_rtf_hex_escapes_decode_rather_than_showing_as_backslash_codes(self):
        r"""`\'93` is a curly quote. Left raw it lands in the middle of
        a quoted clause the operator is meant to read and check."""
        rtf = rb"{\rtf1\ansi \'93Penetration Testing\'94 services.\par}"
        text = operator_cli._read_document_text(self._write(rtf))
        self.assertIn("Penetration Testing", text)
        self.assertNotIn("'93", text)

    def test_an_unreadable_file_is_empty_not_a_crash(self):
        path = self._write(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08")
        self.assertIsInstance(operator_cli._read_document_text(path), str)


class TestDeepIrelandCommand(unittest.TestCase):
    """`deep_sweep()` was built, tested and then reachable only from a
    Python shell -- the same unwired-capability shape as the mouths that
    sat outside `sources_for_query()` for a cycle. These tests pin the
    command AND the honesty rule it exists to carry."""

    def test_dry_run_is_the_default_and_touches_nothing(self):
        with patch.object(operator_cli.mouth_etenders_ie, "deep_sweep") as m:
            code, out, err = _run(["deep-ireland"])
        m.assert_not_called()
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)

    def test_dry_run_states_the_time_cost_before_the_operator_commits(self):
        """~293 sequential requests against one public government server
        is not something to discover halfway through."""
        code, out, err = _run(["deep-ireland"])
        self.assertIn("minutes", out)
        self.assertIn("throttle", out)

    def test_live_walk_prints_the_security_relevant_notices(self):
        walk = operator_cli.mouth_etenders_ie.DeepWalk(
            items=({"key": "1", "title": "Penetration Testing Framework",
                    "organisation": "Irish Rail", "deadline": "",
                    "value_text": "", "description": "cyber security"},
                   {"key": "2", "title": "Road resurfacing",
                    "organisation": "Council", "deadline": "Fri Oct 02 2026",
                    "value_text": "100", "description": "asphalt"}),
            pages_walked=293, complete=True,
            stopped_because="page 294 carried no rows -- end of register")
        with patch.object(operator_cli.mouth_etenders_ie, "deep_sweep",
                          return_value=walk):
            code, out, err = _run(["deep-ireland", "--live"])
        self.assertEqual(code, 0)
        self.assertIn("Penetration Testing Framework", out)
        self.assertNotIn("Road resurfacing", out)

    def test_all_flag_shows_everything(self):
        walk = operator_cli.mouth_etenders_ie.DeepWalk(
            items=({"key": "2", "title": "Road resurfacing",
                    "organisation": "Council", "deadline": "x",
                    "value_text": "", "description": "asphalt"},),
            pages_walked=293, complete=True,
            stopped_because="end of register")
        with patch.object(operator_cli.mouth_etenders_ie, "deep_sweep",
                          return_value=walk):
            code, out, err = _run(["deep-ireland", "--live", "--all"])
        self.assertIn("Road resurfacing", out)

    def test_an_empty_deadline_is_labelled_not_left_blank(self):
        """On this source an empty deadline is not missing data -- it is
        the defining property of a Dynamic Purchasing System, which is
        the whole finding of 2026-09-03. Printing a gap there buries it."""
        walk = operator_cli.mouth_etenders_ie.DeepWalk(
            items=({"key": "1", "title": "Cyber Security Services DPS",
                    "organisation": "RTE", "deadline": "  ",
                    "value_text": "", "description": "cyber"},),
            pages_walked=293, complete=True, stopped_because="end of register")
        with patch.object(operator_cli.mouth_etenders_ie, "deep_sweep",
                          return_value=walk):
            code, out, err = _run(["deep-ireland", "--live"])
        self.assertIn("NO CLOSING DATE", out)

    def test_an_incomplete_walk_is_warned_about_loudly(self):
        """The load-bearing case. A truncated walk that reads as a whole
        one turns 'Ireland has no security tender' into a conclusion
        drawn from the part that happened to be read."""
        walk = operator_cli.mouth_etenders_ie.DeepWalk(
            items=(), pages_walked=3, complete=False,
            stopped_because="stopped at page 4: FetchError: connection reset")
        with patch.object(operator_cli.mouth_etenders_ie, "deep_sweep",
                          return_value=walk):
            code, out, err = _run(["deep-ireland", "--live"])
        self.assertIn("WARNING", out)
        self.assertIn("PREFIX", out)
        self.assertIn("connection reset", out)

    def test_a_complete_walk_carries_no_warning(self):
        walk = operator_cli.mouth_etenders_ie.DeepWalk(
            items=(), pages_walked=293, complete=True,
            stopped_because="page 294 carried no rows -- end of register")
        with patch.object(operator_cli.mouth_etenders_ie, "deep_sweep",
                          return_value=walk):
            code, out, err = _run(["deep-ireland", "--live"])
        self.assertNotIn("WARNING", out)

    def test_page_and_throttle_limits_are_passed_through(self):
        walk = operator_cli.mouth_etenders_ie.DeepWalk(
            items=(), pages_walked=1, complete=True,
            stopped_because="end of register")
        with patch.object(operator_cli.mouth_etenders_ie, "deep_sweep",
                          return_value=walk) as m:
            _run(["deep-ireland", "--live", "--max-pages", "5",
                  "--throttle-seconds", "0.5"])
        m.assert_called_once_with(max_pages=5, throttle_seconds=0.5)


class TestGatesCommand(unittest.TestCase):
    """`gates` answers a question no other surface here answers: what
    does starting cost the operator personally. It is deliberately not
    folded into `access`, which answers whether the notice can be
    reached at all."""

    def _doc(self, text):
        d = tempfile.mkdtemp()
        p = Path(d) / "notice.txt"
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_a_deferred_requirement_is_reported_as_not_needed_to_start(self):
        path = self._doc(
            "Applicants should note that those who have been selected to "
            "Call-Off stage, will be required to comply with the insurance "
            "requirements of the IE Standard Contract.")
        code, out, err = _run(["gates", path])
        self.assertEqual(code, 0)
        self.assertIn("NOT required to start", out)

    def test_an_admission_requirement_is_reported_against_the_operator(self):
        path = self._doc(
            "P3 Minimum Insurance Requirements Pass/Fail. Tenderers must "
            "maintain the following minimum levels of insurance cover: "
            "Public Liability EUR6.5M.")
        code, out, err = _run(["gates", path])
        self.assertIn("needs the operator personally : 1", out)

    def test_a_missing_document_is_a_named_refusal_not_a_traceback(self):
        code, out, err = _run(["gates", "/nonexistent/notice.pdf"])
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)

    def test_an_unreadable_document_is_never_reported_as_permissive(self):
        d = tempfile.mkdtemp()
        p = Path(d) / "scan.bin"
        p.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07")
        code, out, err = _run(["gates", str(p)])
        self.assertEqual(code, 0)
        self.assertIn("NOT_ASSESSED", out)

    def test_it_never_calls_a_clean_read_ungated(self):
        path = self._doc("The authority seeks a supplier of advisory services.")
        code, out, err = _run(["gates", path])
        self.assertIn("NO_GATE_STATED", out)
        self.assertNotIn("UNGATED", out)


class TestSpecCommand(unittest.TestCase):
    """`spec_crossref.py` shipped with 39 tests and no way to invoke it
    -- the THIRD capability in three days finished and left unwired
    (the Denmark/Netherlands mouths, then deep_sweep). These tests pin
    the door, not the machinery behind it."""

    def _doc(self, text, name="spec.txt"):
        d = tempfile.mkdtemp()
        p = Path(d) / name
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_a_clean_specification_reports_no_candidates(self):
        path = self._doc("Algorithm 1.1 GenKeyPair\nsee algorithm 1.1")
        code, out, err = _run(["spec", path])
        self.assertEqual(code, 0)
        self.assertIn("NO CANDIDATES", out)

    def test_a_dangling_reference_is_raised_as_a_candidate(self):
        path = self._doc("Algorithm 1.1 GenKeyPair\nsee algorithm 9.9")
        code, out, err = _run(["spec", path])
        self.assertIn("REFERENCED_NEVER_DEFINED", out)
        self.assertIn("NOT findings", out)

    def test_trace_reports_which_documents_omit_the_term(self):
        """The SGSP shape: a term present in one document and absent
        from the one that implements the control protecting it."""
        a = self._doc("The proof relies on the SGSP problem.", "proof.txt")
        b = self._doc("The seed is restricted to a fixed format.", "spec.txt")
        code, out, err = _run(["spec", "--trace", "SGSP", a, b])
        self.assertEqual(code, 0)
        self.assertIn("ABSENT FROM", out)
        self.assertIn("spec.txt", out)

    def test_trace_accepts_repeatable_aliases(self):
        a = self._doc("relies on the Subgroup Generated by Small Primes")
        code, out, err = _run(
            ["spec", "--trace", "SGSP",
             "--alias", "Subgroup Generated by Small Primes", a])
        self.assertIn("1 mention", out)

    def test_a_missing_document_is_a_named_refusal_not_a_traceback(self):
        code, out, err = _run(["spec", "/nonexistent/spec.pdf"])
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)

    def test_an_unreadable_document_says_so_rather_than_reading_as_empty(self):
        """A scanned PDF and a clean one look identical from here, and
        absence is the finding shape for --trace."""
        d = tempfile.mkdtemp()
        p = Path(d) / "scan.bin"
        p.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07")
        code, out, err = _run(["spec", str(p)])
        self.assertEqual(code, 0)
        self.assertIn("nothing extractable", err)

    def test_the_patterns_are_overridable_not_frozen(self):
        """They are tuned to one real corpus. A different specification
        numbers its algorithms differently, and a checker that silently
        finds nothing is worse than one that refuses."""
        path = self._doc("Rule 4.2 CheckThing\nsee rule 4.2")
        code, out, err = _run([
            "spec", path,
            "--definition-pattern", r"Rule\s+(\d+\.\d+)\s+([A-Z][A-Za-z0-9]{3,60})",
            "--reference-pattern", r"[Rr]ule\s+(\d+\.\d+)"])
        self.assertEqual(code, 0)
        self.assertIn("definitions found : 1", out)


class TestReachabilityCommand(unittest.TestCase):
    def test_it_reports_against_the_real_repository(self):
        code, out, err = _run(["reachability"])
        self.assertEqual(code, 0)
        self.assertIn("CAPABILITY REACHABILITY", out)
        self.assertIn("UNREACHABLE", out)

    def test_it_states_that_unreachable_is_not_a_verdict(self):
        """Some modules are unreachable on purpose. A report that read
        as an accusation would get argued with instead of worked down."""
        code, out, err = _run(["reachability"])
        self.assertIn("FACT, not a verdict", out)

    def test_an_unknown_package_is_a_named_error_not_a_traceback(self):
        with self.assertRaises(Exception) as ctx:
            _run(["reachability", "--package", "nosuchpackage"])
        self.assertIn("not a package directory", str(ctx.exception))


class TestPitCommand(unittest.TestCase):
    def _report(self, text):
        d = tempfile.mkdtemp()
        p = Path(d) / "pit.txt"
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_it_reports_the_contest_statistics(self):
        path = self._report(
            "Swiss Post received a total of 85 reports. 1 High severity "
            "finding and 4 Low severity findings were confirmed. 23 as "
            "duplicates, and 10 as out of scope.")
        code, out, err = _run(["pit", path])
        self.assertEqual(code, 0)
        self.assertIn("acceptance rate", out)
        self.assertIn("85", out)

    def test_a_missing_report_is_a_named_refusal(self):
        code, out, err = _run(["pit", "/nonexistent/pit.pdf"])
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)

    def test_an_unreadable_report_says_so(self):
        d = tempfile.mkdtemp()
        p = Path(d) / "scan.bin"
        p.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07")
        code, out, err = _run(["pit", str(p)])
        self.assertEqual(code, 0)
        self.assertIn("nothing extractable", err)


class TestTriageCommand(unittest.TestCase):
    def _dir(self, files):
        d = Path(tempfile.mkdtemp())
        for name, body in files.items():
            (d / name).write_text(body, encoding="utf-8")
        return str(d)

    def test_it_reports_a_verdict_and_measurements(self):
        path = self._dir({f"d{i}.md": f"# {i}\nprose {i}\n" for i in range(12)})
        code, out, err = _run(["triage", path])
        self.assertEqual(code, 0)
        self.assertIn("verdict", out)
        self.assertIn("SCAFFOLD_ONLY", out)

    def test_source_it_cannot_parse_is_unassessed_not_scaffold(self):
        path = self._dir({f"C{i}.java": f"class C{i} {{ int f() {{ return {i}; }} }}\n"
                          for i in range(20)})
        code, out, err = _run(["triage", path])
        self.assertIn("UNASSESSED_CODE", out)

    def test_a_missing_directory_is_a_named_refusal(self):
        code, out, err = _run(["triage", "/nonexistent/corpus"])
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)


class TestFatNoticeCommand(unittest.TestCase):
    """Reads a UK notice's real criteria by OCID via the OCDS release
    API. Dry-run by default; the live path is exercised only via a
    mocked fetch so no test opens a socket."""

    def test_dry_run_is_the_default_and_touches_nothing(self):
        code, out, err = _run(["fat-notice", "ocds-h6vhtk-06e59c"])
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertIn("ocds-h6vhtk-06e59c", out)

    def test_live_runs_the_criteria_through_entry_gate(self):
        release = {"tender": {"title": "Bradford Pen Testing",
                              "description": "suitably experienced Provider",
                              "value": {"amountGross": 300327.0, "currency": "GBP"},
                              "status": "active"}}
        with patch.object(operator_cli.mouth_find_a_tender_uk, "fetch_release",
                          return_value=release):
            code, out, err = _run(["fat-notice", "ocds-x", "--live"])
        self.assertEqual(code, 0)
        self.assertIn("Bradford Pen Testing", out)
        self.assertIn("WHAT IT COSTS TO START", out)

    def test_a_real_barrier_in_the_release_is_surfaced(self):
        release = {"tender": {"title": "X",
                              "description": "Tenderers must hold a valid "
                              "ISO 27001 certification.", "status": "active"}}
        with patch.object(operator_cli.mouth_find_a_tender_uk, "fetch_release",
                          return_value=release):
            code, out, err = _run(["fat-notice", "ocds-x", "--live"])
        self.assertIn("CERTIFICATION", out)

    def test_a_fetch_failure_is_a_named_refusal_not_a_traceback(self):
        with patch.object(operator_cli.mouth_find_a_tender_uk, "fetch_release",
                          side_effect=RuntimeError("boom")):
            code, out, err = _run(["fat-notice", "ocds-x", "--live"])
        self.assertEqual(code, 1)
        self.assertIn("FETCH FAILED", err)


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


class TestAccessCommand(unittest.TestCase):
    """`access_barriers.py` needs the tender DOCUMENT, which a hunt never
    has -- a hunt only carries notice metadata. Folding it into `hunt`
    would return NOT_ASSESSED on every entry and teach the operator to
    ignore it, which is how a real signal becomes noise. So it is wired
    as a document command instead."""

    def _write(self, tmp, name, data: bytes):
        p = Path(tmp) / name
        p.write_bytes(data)
        return p

    def test_access_is_registered_with_a_handler(self):
        from foundation.operator_cli import build_parser
        parser = build_parser()
        actions = [a for a in parser._subparsers._group_actions
                   if hasattr(a, "choices")]
        choices = actions[0].choices
        self.assertIn("access", choices)
        self.assertTrue(callable(choices["access"].get_default("func")))

    def test_missing_file_is_refused_without_a_traceback(self):
        from foundation.operator_cli import main
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            rc = main(["access", "/definitely/not/here.pdf"])
        self.assertEqual(rc, 1)
        self.assertIn("REFUSED", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_a_fee_and_paper_only_document_is_flagged(self):
        from foundation.operator_cli import main
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, "rfp.txt", (
                b"Bidders may obtain the document upon payment of a "
                b"non-refundable fee of PGK5,000.00. Electronic Bidding "
                b"will not be permitted."))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(["access", str(p)])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("BARRIERS_FOUND", out)
        self.assertIn("DOCUMENT_FEE", out)

    def test_an_unreadable_document_is_not_assessed_not_clean(self):
        """A scanned image extracts nothing. It must never read as a
        document with no barriers -- PNG's own addendum is exactly this."""
        from foundation.operator_cli import main
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, "scan.pdf", b"%PDF-1.4\n%garbage\n")
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(io.StringIO()):
                rc = main(["access", str(p)])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("NOT_ASSESSED", out)
        self.assertNotIn("NONE_DETECTED", out)

    def test_file_type_is_detected_by_content_not_extension(self):
        """A REAL DEFECT THIS CAUGHT. A genuine tender .docx arrived with
        a .bin extension, fell through to the plain-text branch, and
        yielded 752,954 characters of raw ZIP bytes reported as
        NONE_DETECTED -- a confident clean verdict on binary noise.
        Portals name downloads whatever they like, so the extension is
        not trustworthy."""
        from foundation.operator_cli import _read_document_text
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "downloaded.bin"
            with zipfile.ZipFile(p, "w") as z:
                z.writestr("word/document.xml",
                           "<w:p>Electronic Bidding will not be permitted.</w:p>")
            text = _read_document_text(p)
        self.assertIn("Electronic Bidding will not be permitted", text)
        self.assertNotIn("PK", text[:4])
