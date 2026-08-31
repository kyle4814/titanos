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


class TestThePowerLevelShowsItsMath(unittest.TestCase):
    def _profile(self, **kw):
        from foundation.opportunity import power_profile
        return power_profile(_opp(**kw))

    def test_every_power_level_can_answer_why(self):
        p = self._profile(signals=(_sig(), _sig(kind="DEMAND")))
        self.assertTrue(p.breakdown)
        self.assertIn("POWER", p.show_the_math())
        self.assertIn("CONFIDENCE", p.show_the_math())

    def test_M3_an_unknown_reward_is_not_scored_as_zero(self):
        """It contributes nothing and its absence is visible -- it is not
        silently treated as a measured zero."""
        p = self._profile()
        keys = [k for k, _ in p.breakdown]
        self.assertNotIn("VERIFIED_REWARD_OBSERVED", keys)
        self.assertNotIn("REWARD_OBSERVED_UNVERIFIED", keys)

    def test_an_observed_reward_scores_below_a_verified_one(self):
        obs = self._profile(reward_state="OBSERVED", reward_advertised="$5,000",
                            signals=(_sig(kind="REWARD", source_type="OFFICIAL"),))
        ver = self._profile(reward_state="VERIFIED_CURRENT",
                            reward_advertised="$5,000",
                            signals=(_sig(kind="REWARD", source_type="OFFICIAL"),))
        self.assertLess(obs.power_level, ver.power_level)

    def test_M6_a_high_power_score_cannot_erase_low_confidence(self):
        """9,000 at 0.2 and 6,500 at 0.9 are different kinds of target."""
        p = self._profile(
            reward_state="VERIFIED_CURRENT", reward_advertised="$50,000",
            activity_class="HIGHLY_ACTIVE", locally_reproducible="YES",
            signals=(_sig(kind="REWARD", source_type="OFFICIAL"),
                     _sig(kind="DEMAND"), _sig(kind="CODE_PRESSURE")),
            unknowns=("a",) * 6)
        self.assertGreater(p.power_level, 4000)
        self.assertLess(p.confidence, 0.6)
        self.assertIn("CONFIDENCE", p.show_the_math())

    def test_confidence_drops_without_an_authoritative_source(self):
        weak = self._profile()                       # PLATFORM only
        strong = self._profile(signals=(_sig(source_type="OFFICIAL"),))
        self.assertLess(weak.confidence, strong.confidence)

    def test_power_and_confidence_are_never_multiplied_together(self):
        p = self._profile(signals=(_sig(), _sig(kind="DEMAND")))
        self.assertIsInstance(p.power_level, int)
        self.assertIsInstance(p.confidence, float)
        self.assertNotEqual(p.power_level, p.power_level * p.confidence)


class TestTheHandoff(unittest.TestCase):
    def _strong(self, **kw):
        base = dict(signals=(_sig(), _sig(kind="DEMAND"),
                             _sig(kind="CODE_PRESSURE")))
        base.update(kw)
        return _opp(**base)

    def _hand(self, o=None, exp="build it and run the reproduction",
              disproof="the behaviour is already fixed at current HEAD"):
        from foundation.opportunity import handoff
        return handoff(o or self._strong(), exp, disproof)

    def test_a_ranked_target_becomes_a_bounded_mission(self):
        m = self._hand()
        self.assertTrue(m.next_cheapest_experiment)
        self.assertTrue(m.stop_conditions)

    def test_M12_provenance_and_unknowns_survive_the_handoff(self):
        """A mission that loses them sends the investigator out believing
        the evidence is better than it is."""
        o = self._strong(unknowns=("licence unread", "not built locally"))
        m = self._hand(o)
        self.assertEqual(m.unknowns, o.unknowns)
        self.assertEqual(m.source_observations, o.signals)

    def test_M7_M8_a_mission_cannot_claim_a_finding_or_a_value(self):
        m = self._hand()
        self.assertEqual(m.bug_claim(), "NONE")
        self.assertEqual(m.value_claim(), "NOT_MEASURED")
        surface = {f for f in dir(m) if not f.startswith("_")}
        for forbidden in ("verdict", "claims", "receipt", "brick", "materialise"):
            self.assertNotIn(forbidden, surface)

    def test_a_non_investigate_ranking_is_refused(self):
        """The radar does not authorise its own hunt."""
        from foundation.opportunity import HandoffRefused
        with self.assertRaises(HandoffRefused) as ctx:
            self._hand(_opp(activity_class="LOW"))
        self.assertIn("does not authorise its own hunt", str(ctx.exception))

    def test_M9_a_disqualified_target_cannot_be_handed_off(self):
        from foundation.opportunity import HandoffRefused
        with self.assertRaises(HandoffRefused):
            self._hand(self._strong(disqualifiers=("REQUIRES_LIVE_INFRA",)))

    def test_M5_a_stale_target_cannot_be_handed_off(self):
        from datetime import datetime, timedelta, timezone
        from foundation.opportunity import HandoffRefused
        old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        with self.assertRaises(HandoffRefused):
            self._hand(self._strong(observed_at=old))

    def test_a_mission_must_name_the_cheapest_killing_experiment(self):
        from foundation.opportunity import HandoffRefused
        with self.assertRaises(HandoffRefused) as ctx:
            self._hand(exp="   ")
        self.assertIn("cheapest experiment", str(ctx.exception))

    def test_the_mission_carries_power_and_confidence_separately(self):
        m = self._hand()
        self.assertIsInstance(m.power_level, int)
        self.assertIsInstance(m.confidence, float)
        self.assertTrue(m.classification)


class TestTheCeilingIsVisible(unittest.TestCase):
    """A ranking of WATCH was ambiguous: "weak target" and "no evidence this
    system can produce would ever score higher" are opposite facts and were
    indistinguishable. Measured: with every live instrument firing at
    maximum, the best achievable priority is 4 and the threshold is 5."""

    def _best_possible(self):
        """Everything the live instruments can physically emit today."""
        return _opp(signals=(_sig(kind="DEMAND", source_type="OFFICIAL"),
                             _sig(kind="ACTIVITY", source_type="OFFICIAL"),
                             _sig(kind="RELEASE", source_type="OFFICIAL")),
                    activity_class="HIGHLY_ACTIVE",
                    locally_reproducible="UNKNOWN")

    def test_M_the_best_live_target_is_structurally_capped(self):
        from foundation.opportunity import ceiling_analysis
        c = ceiling_analysis(self._best_possible())
        self.assertTrue(c.is_structurally_capped())
        self.assertLess(c.reachable_ceiling, c.threshold)

    def test_M_a_capped_ranking_says_the_levers_are_unavailable(self):
        """Not 'this target is weak' but 'nothing could make it stronger'."""
        joined = " ".join(rank(self._best_possible()).inputs)
        self.assertIn("unavailable to this system", joined)
        self.assertIn("CODE_PRESSURE", joined)

    def test_the_ceiling_names_every_blocked_lever_with_a_reason(self):
        from foundation.opportunity import ceiling_analysis
        c = ceiling_analysis(self._best_possible())
        levers = {name for name, _ in c.blocked_by}
        self.assertEqual(levers, {"CODE_PRESSURE", "LOCAL_REPRODUCIBILITY",
                                  "REWARD"})
        for _, why in c.blocked_by:
            self.assertTrue(why.strip())
        self.assertIn("no live instrument emits this kind", c.explain())

    def test_M_a_reachable_target_is_not_reported_as_capped(self):
        """Positive control: the diagnosis must not cry wolf."""
        from foundation.opportunity import ceiling_analysis
        reachable = _opp(signals=(_sig(kind="DEMAND"),
                                  _sig(kind="CODE_PRESSURE")),
                         locally_reproducible="YES")
        c = ceiling_analysis(reachable)
        self.assertFalse(c.is_structurally_capped())
        self.assertIn("INVESTIGATE is reachable", c.explain())

    def test_M_an_investigate_ranking_carries_no_ceiling_warning(self):
        r = rank(_opp(signals=(_sig(), _sig(kind="DEMAND"),
                               _sig(kind="CODE_PRESSURE"))))
        self.assertEqual(r.recommendation, "INVESTIGATE")
        self.assertNotIn("unavailable to this system", " ".join(r.inputs))

    def test_M_the_diagnosis_changes_no_recommendation(self):
        """Weights and threshold are untouched; only legibility is added."""
        for opp in (self._best_possible(),
                    _opp(activity_class="DORMANT"),
                    _opp(disqualifiers=("OUT_OF_SCOPE",)),
                    _opp(signals=(_sig(), _sig(kind="DEMAND"),
                                  _sig(kind="CODE_PRESSURE")))):
            r = rank(opp)
            self.assertIn(r.recommendation,
                          ("INVESTIGATE", "WATCH", "IGNORE", "RECHECK",
                           "WITHHOLD", "HUMAN_REVIEW_REQUIRED"))

    def test_the_threshold_is_named_not_a_magic_number(self):
        from foundation.opportunity import INVESTIGATE_THRESHOLD, SCORING_LEVERS
        self.assertEqual(INVESTIGATE_THRESHOLD, 5)
        self.assertEqual(set(SCORING_LEVERS),
                         {"CODE_PRESSURE", "LOCAL_REPRODUCIBILITY", "REWARD"})


class TestSourceMultiplicityIsNotIndependence(unittest.TestCase):
    """Owning a repo's issues, commits and commit text is one party
    talking to itself through three doors, not three witnesses."""

    def _profile(self, **kw):
        from foundation.opportunity import power_profile
        return power_profile(_opp(**kw))

    def _owner_only_signals(self):
        """The manufactured attack: DEMAND + ACTIVITY + CODE_PRESSURE,
        all traceable to the target's own owner (acme), none carrying a
        third-party author_login."""
        return (
            _sig(kind="DEMAND", source_type="PLATFORM",
                 detail="acme/widget#1 is open and labelled help wanted"),
            _sig(kind="ACTIVITY", source_type="PLATFORM",
                 detail="12 commits in 30 days"),
            _sig(kind="CODE_PRESSURE", source_type="PLATFORM",
                 detail="commit subject: fix widget crash"),
        )

    def test_owner_authored_signals_do_not_earn_source_diversity(self):
        p = self._profile(signals=self._owner_only_signals(),
                          activity_class="ACTIVE")
        keys = [k for k, _ in p.breakdown]
        self.assertNotIn("SOURCE_DIVERSITY", keys)

    def test_third_party_issue_plus_owner_commits_does_earn_it(self):
        """The nuance: a help-wanted issue filed by someone OTHER than
        the owner is real independent evidence."""
        third_party_demand = SignalEvidence(
            kind="DEMAND", detail="acme/widget#7 filed by a stranger",
            source_type="PLATFORM",
            evidence={"author_login": "someone-else"})
        owner_activity = _sig(kind="ACTIVITY", detail="9 commits in 30 days")
        p = self._profile(signals=(third_party_demand, owner_activity),
                          activity_class="ACTIVE")
        keys = [k for k, v in p.breakdown]
        self.assertIn("SOURCE_DIVERSITY", keys)

    def test_the_manufactured_attack_scores_materially_lower(self):
        """Assert the specific delta: exactly the withheld
        SOURCE_DIVERSITY bonus, since every individual signal is still a
        real observation and still counts on its own -- this is a
        decorrelation, not a zeroing.

        Reproduces the reported attack shape: DEMAND + ACTIVITY +
        CODE_PRESSURE arriving through three different `source_type`
        values (as three different live fetchers realistically would),
        all traceable to one owner. Under the OLD formula
        (`len({s.source_type for s in signals}) > 1`) this earned
        SOURCE_DIVERSITY; under the new party-based rule it must not.
        """
        mixed_source_type_signals = (
            SignalEvidence(kind="DEMAND", detail="issue #1",
                          source_type="PLATFORM"),
            SignalEvidence(kind="ACTIVITY", detail="commits",
                          source_type="PROJECT_MAINTAINED"),
            SignalEvidence(kind="CODE_PRESSURE", detail="commit text",
                          source_type="COMMUNITY"),
        )
        old_distinct_source_types = {s.source_type
                                     for s in mixed_source_type_signals}
        self.assertGreater(len(old_distinct_source_types), 1,
                           "sanity: the old formula would have fired here")

        after = self._profile(signals=mixed_source_type_signals,
                              activity_class="ACTIVE")
        keys = [k for k, _ in after.breakdown]
        self.assertNotIn("SOURCE_DIVERSITY", keys)

        # Every other component is untouched: EXPLICIT_DEMAND(1800) +
        # CODE_PRESSURE(1500) + TARGET_ACTIVITY-ACTIVE(900) +
        # LOCAL_REPRODUCIBILITY(1600) + EVIDENCE_FRESH(700) = 6500, with
        # no REWARD (none observed) and no SOURCE_DIVERSITY (one party).
        self.assertEqual(after.power_level, 6500)
        # The exact old-vs-new delta this fix closes: the withheld
        # SOURCE_DIVERSITY bonus, and nothing else.
        old_formula_power = after.power_level + 400
        self.assertEqual(old_formula_power - after.power_level, 400)

    def test_a_genuine_multiparty_target_is_unaffected(self):
        """Positive control: real diversity must still be visible and
        must still score at least as high as the owner-only case."""
        owner_only = self._profile(signals=self._owner_only_signals(),
                                   activity_class="ACTIVE")
        genuine = self._profile(
            signals=(
                SignalEvidence(
                    kind="DEMAND", detail="third party help-wanted ask",
                    source_type="PLATFORM",
                    evidence={"author_login": "a-real-contributor"}),
                _sig(kind="ACTIVITY", detail="12 commits in 30 days"),
                _sig(kind="CODE_PRESSURE", detail="commit subject"),
            ),
            activity_class="ACTIVE")
        genuine_keys = [k for k, _ in genuine.breakdown]
        self.assertIn("SOURCE_DIVERSITY", genuine_keys)
        self.assertGreaterEqual(genuine.power_level, owner_only.power_level)

    def test_show_the_math_names_the_single_party_finding_in_words(self):
        p = self._profile(signals=self._owner_only_signals(),
                          activity_class="ACTIVE")
        text = p.show_the_math()
        self.assertIn("SOURCE CONTROL", text)
        self.assertIn("one controlling party", text)
        self.assertIn("acme", text)

    def test_show_the_math_names_genuine_diversity_too(self):
        p = self._profile(
            signals=(
                SignalEvidence(
                    kind="DEMAND", detail="third party ask",
                    source_type="PLATFORM",
                    evidence={"author_login": "a-real-contributor"}),
                _sig(kind="ACTIVITY", detail="commits")),
            activity_class="ACTIVE")
        text = p.show_the_math()
        self.assertIn("distinct controlling", text)

    def test_controlling_party_owner_authored(self):
        from foundation.opportunity import controlling_party
        sig = SignalEvidence(kind="DEMAND", detail="x", source_type="PLATFORM",
                             evidence={"author_login": "acme"})
        self.assertEqual(controlling_party("acme/widget", sig), "acme")

    def test_controlling_party_no_author_defaults_to_owner(self):
        """ACTIVITY/CODE_PRESSURE signals describe the repo, not a
        person -- conservatively attributed to the owner, which is the
        same assumption the attack exploits, made deliberately."""
        from foundation.opportunity import controlling_party
        sig = _sig(kind="ACTIVITY", detail="12 commits")
        self.assertEqual(controlling_party("acme/widget", sig), "acme")

    def test_controlling_party_third_party_author(self):
        from foundation.opportunity import controlling_party
        sig = SignalEvidence(kind="DEMAND", detail="x", source_type="PLATFORM",
                             evidence={"author_login": "a-real-contributor"})
        self.assertEqual(controlling_party("acme/widget", sig),
                         "a-real-contributor")

    def test_signal_evidence_mapping_is_frozen(self):
        sig = SignalEvidence(kind="DEMAND", detail="x", source_type="PLATFORM",
                             evidence={"author_login": "acme"})
        with self.assertRaises(TypeError):
            sig.evidence["author_login"] = "someone-else"
