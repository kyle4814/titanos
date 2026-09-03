"""Tests for `foundation/pit_report.py`. Offline; the fixture is a
faithful miniature of the 2026 Swiss Post PIT final report structure,
not the 485 MB PDF."""

import unittest

from foundation.pit_report import (
    ConfirmedFinding,
    PitReportError,
    format_pit_summary,
    summarise_pit_report,
)

# Structured exactly as the real 2026 report: a summary sentence, a
# classification sentence, and per-finding Title/Number/Severity/Reward
# blocks.
REPORT_2026 = (
    "Swiss Post received a total of 85 reports. Following detailed "
    "analysis, 1 High severity finding, 1 Medium severity finding and 4 "
    "Low severity findings were confirmed. In addition, 46 reports were "
    "classified as\nInformative, 23 as duplicates, and 10 as out of scope.\n"
    "Title Cache Poisoning in Encryption Group Handling Causes Voting "
    "Server Availability Impact Number YWH-PGM2323-1597 Date of receipt "
    "9.7.2026 Severity High Description The report identifies an "
    "availability issue. Reward 19,000 €\n"
    "Title Send-Vote Context ID confusion allows targeted voting process "
    "disruption Number YWH-PGM2323-1732 Severity Medium Description missing "
    "context validation. Reward 6,400 €\n"
    "Title Path Normalization Bypass of Voting Card Manager Number "
    "YWH-3 Severity Low Description a path issue."
)


class TestTheNumbersThatDecideWhetherToSpendAMonth(unittest.TestCase):
    def test_reports_received_is_extracted(self):
        self.assertEqual(summarise_pit_report(REPORT_2026).reports_received, 85)

    def test_confirmed_is_summed_across_severities(self):
        # 1 High + 1 Medium + 4 Low = 6
        self.assertEqual(summarise_pit_report(REPORT_2026).confirmed_count, 6)

    def test_acceptance_rate_is_computed_from_extracted_numbers(self):
        s = summarise_pit_report(REPORT_2026)
        self.assertAlmostEqual(s.acceptance_rate, 100 * 6 / 85, places=2)

    def test_duplicate_rate_is_computed(self):
        s = summarise_pit_report(REPORT_2026)
        self.assertAlmostEqual(s.duplicate_rate, 100 * 23 / 85, places=2)

    def test_informative_is_read_across_a_line_break(self):
        """The real report wraps 'classified as \\n Informative'. A
        count regex that stops at the newline reports UNKNOWN -- absence
        manufactured by extraction."""
        self.assertEqual(summarise_pit_report(REPORT_2026).informative, 46)


class TestFindingTitlesAreNotTruncated(unittest.TestCase):
    """The first version stopped the title at the first space and
    produced one-word titles like 'Cache'."""

    def test_a_full_multi_word_title_is_captured(self):
        s = summarise_pit_report(REPORT_2026)
        self.assertEqual(
            s.findings[0].title,
            "Cache Poisoning in Encryption Group Handling Causes Voting "
            "Server Availability Impact")

    def test_severity_and_reward_are_paired_to_the_right_finding(self):
        s = summarise_pit_report(REPORT_2026)
        self.assertEqual((s.findings[0].severity, s.findings[0].reward_eur),
                         ("High", 19000))
        self.assertEqual((s.findings[1].severity, s.findings[1].reward_eur),
                         ("Medium", 6400))

    def test_a_finding_with_no_stated_reward_is_none_not_zero(self):
        s = summarise_pit_report(REPORT_2026)
        self.assertEqual(s.findings[2].severity, "Low")
        self.assertIsNone(s.findings[2].reward_eur)

    def test_top_reward_ignores_the_none_rewards(self):
        self.assertEqual(summarise_pit_report(REPORT_2026).top_reward_eur, 19000)


class TestUnknownIsNeverZero(unittest.TestCase):
    def test_a_missing_figure_is_none(self):
        s = summarise_pit_report("Swiss Post ran a test. Some findings.")
        self.assertIsNone(s.reports_received)
        self.assertIsNone(s.acceptance_rate)

    def test_a_report_this_parser_cannot_read_returns_none_not_wrong_numbers(self):
        """The 2022-2025 reports use different prose ('received four
        reports'). All-None is the correct failure -- UNKNOWN, not a
        guessed statistic."""
        s = summarise_pit_report("Swiss Post received four reports in 2023.")
        self.assertIsNone(s.reports_received)

    def test_empty_text_is_not_assessed(self):
        self.assertEqual(summarise_pit_report("").status, "NOT_ASSESSED")

    def test_the_render_says_unknown_is_not_zero(self):
        out = format_pit_summary(summarise_pit_report("a report with no numbers"))
        self.assertIn("not a zero", out)

    def test_the_unread_render_states_its_own_blindness(self):
        out = format_pit_summary(summarise_pit_report(""))
        self.assertIn("not the same as a target with no history", out)


class TestIntegrity(unittest.TestCase):
    def test_non_string_input_is_refused(self):
        with self.assertRaises(PitReportError):
            summarise_pit_report(None)

    def test_a_bad_severity_is_refused(self):
        with self.assertRaises(PitReportError):
            ConfirmedFinding(title="x", severity="Scary", reward_eur=None)

    def test_a_finding_with_no_title_is_refused(self):
        with self.assertRaises(PitReportError):
            ConfirmedFinding(title="  ", severity="Low", reward_eur=1)

    def test_format_refuses_a_non_summary(self):
        with self.assertRaises(PitReportError):
            format_pit_summary("SUMMARISED")

    def test_module_has_no_network_import(self):
        from pathlib import Path
        from foundation import pit_report
        src = Path(pit_report.__file__).read_text(encoding="utf-8")
        for lib in ("urllib", "requests", "socket", "http.client"):
            self.assertNotIn(f"import {lib}", src)


if __name__ == "__main__":
    unittest.main()
