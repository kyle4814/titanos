"""A signal is not a bug, and a listed reward is not money.

Every test here tries to get the radar to claim something it only
glimpsed.
"""

import unittest
from datetime import datetime, timedelta, timezone

from foundation.opportunity import (
    HARD_DISQUALIFIERS,
    OpportunityIntegrityError,
    OpportunityReceipt,
    SignalEvidence,
    opportunity_id_for,
    rank,
)


def _sig(kind="ACTIVITY", source_type="PLATFORM", detail="42 commits in 30 days"):
    return SignalEvidence(kind=kind, detail=detail, source_type=source_type,
                          source_ref="https://example.invalid/x")


def _opp(**kw):
    base = dict(
        opportunity_id="OPP-test", target="acme/widget",
        discovered_at="2026-08-30T00:00:00+00:00",
        signals=(_sig(),), activity_class="ACTIVE",
        locally_reproducible="YES")
    base.update(kw)
    return OpportunityReceipt(**base)


class TestTheRadarNeverClaimsADefect(unittest.TestCase):
    def test_bug_claim_is_always_none(self):
        """Load-bearing, and there is deliberately no setter."""
        self.assertEqual(_opp().bug_claim(), "NONE")

    def test_no_signal_kind_can_make_it_claim_one(self):
        o = _opp(signals=(_sig(kind="CODE_PRESSURE",
                               detail="large diff, no test movement"),))
        self.assertEqual(o.bug_claim(), "NONE")

    def test_it_carries_no_defect_field_at_all(self):
        surface = {f for f in dir(_opp()) if not f.startswith("_")}
        for forbidden in ("defect", "bug", "vulnerability", "finding"):
            self.assertNotIn(forbidden, surface)


class TestRewardIsNotMoney(unittest.TestCase):
    def test_a_third_party_snippet_cannot_be_verified_current(self):
        """'$50,000 BOUNTY!!!' on a blog is a lead, not evidence."""
        with self.assertRaises(OpportunityIntegrityError) as ctx:
            _opp(reward_state="VERIFIED_CURRENT",
                 reward_advertised="$50,000",
                 signals=(_sig(kind="REWARD", source_type="THIRD_PARTY"),))
        self.assertIn("lead, not evidence", str(ctx.exception))

    def test_an_official_source_may_support_verified_current(self):
        o = _opp(reward_state="VERIFIED_CURRENT", reward_advertised="up to $10,000",
                 signals=(_sig(kind="REWARD", source_type="OFFICIAL"),))
        self.assertEqual(o.reward_state, "VERIFIED_CURRENT")

    def test_expected_value_is_never_the_advertised_figure(self):
        """The single most tempting arithmetic in this whole system."""
        o = _opp(reward_state="OBSERVED", reward_advertised="up to $10,000",
                 reward_eligibility="UNKNOWN",
                 signals=(_sig(kind="REWARD", source_type="OFFICIAL"),))
        self.assertEqual(o.reward_expected(), "NOT_MEASURED")
        self.assertNotIn("10,000", o.reward_expected())

    def test_eligibility_unknown_is_the_default_not_an_omission(self):
        self.assertEqual(_opp().reward_eligibility, "UNKNOWN")

    def test_an_advertised_figure_must_carry_an_eligibility_state(self):
        with self.assertRaises(OpportunityIntegrityError):
            _opp(reward_advertised="$5,000", reward_eligibility="")

    def test_only_a_paid_reward_reports_an_amount(self):
        o = _opp(reward_state="PAID", reward_advertised="$1,200",
                 signals=(_sig(kind="REWARD", source_type="OFFICIAL"),))
        self.assertEqual(o.reward_expected(), "$1,200")


class TestNoScoreOutranksADisqualifier(unittest.TestCase):
    def test_security_sensitive_routes_to_human_review_however_good(self):
        o = _opp(disqualifiers=("SECURITY_SENSITIVE",),
                 reward_state="VERIFIED_CURRENT", reward_advertised="$100,000",
                 activity_class="HIGHLY_ACTIVE",
                 signals=(_sig(kind="REWARD", source_type="OFFICIAL"),
                          _sig(kind="DEMAND"), _sig(kind="CODE_PRESSURE")))
        r = rank(o)
        self.assertEqual(r.recommendation, "HUMAN_REVIEW_REQUIRED")
        self.assertEqual(r.priority, 0)
        self.assertIn("no score may outrank a disqualifier", r.inputs)

    def test_out_of_scope_withholds(self):
        self.assertEqual(rank(_opp(disqualifiers=("OUT_OF_SCOPE",))).recommendation,
                         "WITHHOLD")

    def test_a_dormant_target_is_ignored_however_large_the_reward(self):
        o = _opp(activity_class="DORMANT", reward_state="VERIFIED_CURRENT",
                 reward_advertised="$250,000",
                 signals=(_sig(kind="REWARD", source_type="OFFICIAL"),))
        r = rank(o)
        self.assertEqual(r.recommendation, "IGNORE")
        self.assertIn("corpse with stars", " ".join(r.inputs))

    def test_the_disqualifier_vocabulary_is_closed(self):
        self.assertIn("REQUIRES_SECRETS", HARD_DISQUALIFIERS)
        self.assertIn("REQUIRES_LIVE_INFRA", HARD_DISQUALIFIERS)


class TestStalenessAndRecheck(unittest.TestCase):
    def test_a_stale_observation_forces_a_recheck(self):
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        self.assertEqual(rank(_opp(observed_at=old)).recommendation, "RECHECK")

    def test_a_fresh_observation_is_not_stale(self):
        self.assertFalse(_opp().is_stale())

    def test_an_unparseable_timestamp_is_treated_as_stale(self):
        """Unreadable means unknown, and unknown must not read as fresh."""
        self.assertTrue(_opp(observed_at="whenever").is_stale())


class TestRankingIsExplainable(unittest.TestCase):
    def test_every_ranking_states_its_inputs(self):
        r = rank(_opp(signals=(_sig(), _sig(kind="DEMAND"),
                               _sig(kind="CODE_PRESSURE"))))
        self.assertTrue(r.inputs)
        self.assertIn("priority", " ".join(r.inputs))

    def test_a_strong_correlated_target_reaches_investigate(self):
        """Positive control: activity + demand + pressure + local repro."""
        r = rank(_opp(signals=(_sig(), _sig(kind="DEMAND"),
                               _sig(kind="CODE_PRESSURE"))))
        self.assertEqual(r.recommendation, "INVESTIGATE")

    def test_a_single_weak_signal_does_not(self):
        r = rank(_opp(activity_class="LOW", locally_reproducible="UNKNOWN"))
        self.assertIn(r.recommendation, ("IGNORE", "WATCH"))

    def test_priority_is_declared_a_queue_order_not_a_verdict(self):
        self.assertIn("not a verdict", " ".join(rank(_opp()).inputs))

    def test_unreproducible_work_is_penalised(self):
        strong = dict(signals=(_sig(), _sig(kind="DEMAND"),
                               _sig(kind="CODE_PRESSURE")))
        self.assertGreater(rank(_opp(**strong)).priority,
                           rank(_opp(locally_reproducible="NO", **strong)).priority)


class TestIdentityAndHygiene(unittest.TestCase):
    def test_the_same_lead_yields_the_same_id(self):
        a = opportunity_id_for("acme/widget", "issue-42")
        b = opportunity_id_for(" ACME/Widget ", "Issue-42")
        self.assertEqual(a, b)

    def test_different_leads_differ(self):
        self.assertNotEqual(opportunity_id_for("a/b", "issue-1"),
                            opportunity_id_for("a/b", "issue-2"))

    def test_a_signal_must_say_what_was_seen(self):
        with self.assertRaises(OpportunityIntegrityError):
            SignalEvidence(kind="ACTIVITY", detail="  ", source_type="PLATFORM")

    def test_an_invented_source_type_is_refused(self):
        with self.assertRaises(OpportunityIntegrityError):
            SignalEvidence(kind="REWARD", detail="x", source_type="TRUST_ME")

    def test_unknowns_are_carried_not_dropped(self):
        o = _opp(unknowns=("whether we are eligible", "whether it is fixed"))
        self.assertEqual(len(o.unknowns), 2)
        self.assertIn("unknown", " ".join(rank(o).inputs))


if __name__ == "__main__":
    unittest.main()
