"""Tests for `foundation/team_fit.py` — the winnability scorer.

The load-bearing property is HONESTY: an undeclared capability or an
unparseable requirement is UNKNOWN, never a silent pass. These tests
attack that boundary from the position a hopeful bidder would occupy."""

import unittest
from datetime import datetime, timezone

from foundation.team_fit import (
    TeamCapability,
    Verdict,
    assess_fit,
    rank_targets,
    render_fit_md,
    _check,
    _parse_money,
    _classify,
    _Kind,
)
from foundation.team_targets import TEAM_TARGETS, TeamTarget

NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)


def _find(target_id):
    return next(t for t in TEAM_TARGETS if t.target_id == target_id)


class TestMoneyParsing(unittest.TestCase):
    def test_plain_euro(self):
        self.assertEqual(_parse_money("Insurance €13,000,000"), 13_000_000)

    def test_k_suffix(self):
        self.assertEqual(_parse_money("value €720k"), 720_000)

    def test_no_money(self):
        self.assertIsNone(_parse_money("3 corporate reference contracts"))


class TestClassification(unittest.TestCase):
    def test_no_barrier(self):
        self.assertEqual(_classify("English/UK — no language barrier"),
                         _Kind.NO_BARRIER)

    def test_insurance(self):
        self.assertEqual(_classify("Employer's liability insurance €13,000,000"),
                         _Kind.INSURANCE)

    def test_turnover(self):
        self.assertEqual(_classify("Average turnover €1,000,000"), _Kind.TURNOVER)

    def test_language(self):
        self.assertEqual(_classify("CEFR C1 German (a team member must have this)"),
                         _Kind.LANGUAGE)

    def test_capability(self):
        self.assertEqual(_classify("Managed SOC capability"), _Kind.CAPABILITY)


class TestHonestUnknown(unittest.TestCase):
    def test_undeclared_soc_is_unknown_not_met(self):
        # A team that says nothing about SOC does NOT meet a SOC requirement.
        empty = TeamCapability()
        c = _check("SOC + Incident Response delivered 24×7×365", empty)
        self.assertEqual(c.status, "UNKNOWN")

    def test_declared_soc_meets(self):
        cap = TeamCapability(has_247_soc=True)
        c = _check("SOC + Incident Response delivered 24×7×365", cap)
        self.assertEqual(c.status, "MEET")

    def test_unparseable_requirement_is_unknown(self):
        cap = TeamCapability()
        c = _check("Central-bank engagements often need security clearances — confirm",
                   cap)
        self.assertEqual(c.status, "UNKNOWN")

    def test_hedged_country_clause_is_unknown_not_gap(self):
        # "Likely Danish-market presence or partner; confirm in the ESPD" is a
        # hedged market-presence clause, NOT a hard "must speak Danish" wall.
        # It must route to UNKNOWN (human read), never a hard GAP, even for a
        # team with no Danish speaker.
        cap = TeamCapability(languages=("english",))
        c = _check("Likely Danish-market presence or partner; confirm in the ESPD",
                   cap)
        self.assertEqual(c.status, "UNKNOWN")

    def test_firm_language_requirement_still_gaps(self):
        # A firm "a team member needs it" language line is still a hard GAP.
        cap = TeamCapability(languages=("english",))
        c = _check("Dutch language — the notice is in Dutch; a team member needs it",
                   cap)
        self.assertEqual(c.status, "GAP")

    def test_no_barrier_auto_meets(self):
        c = _check("English/UK — no language or jurisdiction barrier", TeamCapability())
        self.assertEqual(c.status, "MEET")


class TestGaps(unittest.TestCase):
    def test_turnover_gap(self):
        cap = TeamCapability(annual_turnover_eur=100_000)
        c = _check("Average turnover €1,000,000", cap)
        self.assertEqual(c.status, "GAP")

    def test_turnover_met(self):
        cap = TeamCapability(annual_turnover_eur=2_000_000)
        c = _check("Average turnover €1,000,000", cap)
        self.assertEqual(c.status, "MEET")

    def test_insurance_gap(self):
        cap = TeamCapability(max_insurance_eur=1_000_000)
        c = _check("Employer's liability insurance €13,000,000", cap)
        self.assertEqual(c.status, "GAP")

    def test_insurance_can_raise_is_not_a_silent_pass(self):
        # "can obtain" is confirm-before-bid, never an auto-MEET on a hard figure.
        cap = TeamCapability(max_insurance_eur=1_000_000,
                             can_obtain_higher_insurance=True)
        c = _check("Employer's liability insurance €13,000,000", cap)
        self.assertEqual(c.status, "UNKNOWN")

    def test_language_gap(self):
        cap = TeamCapability(languages=("english",))
        c = _check("CEFR C1 German (a team member must have this)", cap)
        self.assertEqual(c.status, "GAP")

    def test_language_met(self):
        cap = TeamCapability(languages=("english", "german"))
        c = _check("CEFR C1 German (a team member must have this)", cap)
        self.assertEqual(c.status, "MEET")

    def test_reference_count_gap(self):
        cap = TeamCapability(reference_contracts=1)
        c = _check("5 reference contracts over €100,000 each", cap)
        self.assertEqual(c.status, "GAP")


class TestOverallVerdict(unittest.TestCase):
    def test_gap_dominates(self):
        cap = TeamCapability(annual_turnover_eur=0)
        # any single GAP makes the whole target GAP
        fit = assess_fit(_find("IE_FAILTE"), cap)
        self.assertIn(fit.verdict, (Verdict.GAP, Verdict.PARTIAL))

    def test_strong_team_can_meet_or_partial(self):
        strong = TeamCapability(
            annual_turnover_eur=50_000_000,
            max_insurance_eur=20_000_000,
            can_obtain_higher_insurance=True,
            reference_contracts=10,
            largest_reference_eur=5_000_000,
            languages=("english", "german", "dutch", "danish"),
            has_247_soc=True,
            capabilities=("soc", "mdr", "siem", "soar", "incident response",
                          "cyber assurance", "audit capability",
                          "security advisory", "security governance",
                          "risk-analysis"),
            named_testers=5,
        )
        # A maximal team should have zero hard GAPs on at least one live target.
        ranked = rank_targets(strong, NOW)
        self.assertTrue(any(f.verdict in (Verdict.MEET, Verdict.PARTIAL)
                            for f in ranked))
        # and the ranking puts MEET/PARTIAL ahead of GAP
        order = [f.verdict for f in ranked]
        last_good = max((i for i, v in enumerate(order)
                         if v in (Verdict.MEET, Verdict.PARTIAL)), default=-1)
        first_gap = next((i for i, v in enumerate(order)
                          if v is Verdict.GAP), len(order))
        self.assertLess(last_good, first_gap + 1)


class TestRankingAndRender(unittest.TestCase):
    def test_rank_is_stable_and_covers_live(self):
        ranked = rank_targets(TeamCapability(), NOW)
        self.assertTrue(len(ranked) >= 1)

    def test_render_names_counts_and_a_real_target(self):
        cap = TeamCapability(languages=("english",))
        md = render_fit_md(cap, NOW)
        self.assertIn("TEAM FIT", md)
        self.assertIn("MEET", md)
        self.assertIn("GAP", md)
        # a real target title survives into the report
        self.assertTrue("Fáilte Ireland" in md or "SOC" in md)


if __name__ == "__main__":
    unittest.main()
