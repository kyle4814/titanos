"""One fact echoed five times is still one fact.

Every test here tries to make the fusion layer mistake repetition for
evidence, a rumour for money, or a score for a reason.
"""

import unittest
from datetime import datetime, timedelta, timezone

from foundation.signal_spine import (
    CanonicalSignal,
    LOCK_THRESHOLD,
    SignalIntegrityError,
    fuse,
    gravity,
    raw_value_map_entry,
    relate,
    target_lock,
)


def _now():
    return datetime.now(timezone.utc)


def _stamp(days_ago=0):
    return (_now() - timedelta(days=days_ago)).isoformat()


def _sig(sid="S1", source_id="mouth_a", **kw):
    base = dict(
        signal_id=sid, source_id=source_id, source_type="PLATFORM",
        source_ref="https://example.invalid/x", target="acme/widget",
        kind="RELEASE", claim="widget 6.0.2 was released",
        observed_at=_stamp(), event_at=_stamp(1),
        facts={"latest_version": "6.0.2"})
    base.update(kw)
    return CanonicalSignal(**base)


def _entry(signals, **kw):
    args = dict(
        why_on_the_map=("two independent sources agree",),
        what_would_kill_it="the version is already superseded",
        next_cheapest_experiment="read the changelog")
    args.update(kw)
    return raw_value_map_entry(fuse(signals), **args)


class TestTheCanonicalShapeKeepsDifferences(unittest.TestCase):
    def test_a_signal_must_name_the_tentacle_that_saw_it(self):
        with self.assertRaises(SignalIntegrityError) as ctx:
            _sig(source_id="  ")
        self.assertIn("provenance is already lost", str(ctx.exception))

    def test_source_specific_evidence_is_preserved_not_flattened(self):
        """A GitHub issue has labels; a package index has downloads.
        Normalising those away destroys the reason for a second source."""
        s = _sig(evidence={"labels": ["help wanted"], "comments": 3})
        self.assertEqual(s.evidence["labels"], ["help wanted"])

    def test_evidence_cannot_be_edited_after_a_decision_was_made_from_it(self):
        s = _sig(evidence={"labels": ["a"]})
        with self.assertRaises(TypeError):
            s.evidence["labels"] = ["tampered"]
        with self.assertRaises(TypeError):
            s.facts["latest_version"] = "9.9.9"

    def test_a_tentacle_cannot_invent_its_own_authority(self):
        with self.assertRaises(SignalIntegrityError):
            _sig(source_type="TRUST_ME")

    def test_time_survives_per_signal_not_per_target(self):
        """A fresh observation of an ancient fact is not a fresh fact."""
        old = _sig(observed_at=_stamp(0), event_at=_stamp(400))
        self.assertTrue(old.is_stale())

    def test_an_unreadable_timestamp_is_stale_not_fresh(self):
        self.assertTrue(_sig(event_at="last Tuesday").is_stale())

    def test_a_fresh_signal_is_not_stale(self):
        self.assertFalse(_sig().is_stale())


class TestMoneyIsNotPower(unittest.TestCase):
    def test_only_paid_money_is_money(self):
        s = _sig(money_state="ADVERTISED", money_observed="up to $50,000")
        self.assertEqual(s.money_claim(), "NOT_MEASURED")
        self.assertNotIn("50,000", s.money_claim())

    def test_paid_money_reports_its_amount(self):
        s = _sig(money_state="PAID", money_observed="$1,200")
        self.assertEqual(s.money_claim(), "$1,200")

    def test_a_money_state_with_no_figure_is_refused(self):
        with self.assertRaises(SignalIntegrityError):
            _sig(money_state="VERIFIED_CURRENT", money_observed="")

    def test_a_figure_with_no_state_is_refused(self):
        with self.assertRaises(SignalIntegrityError):
            _sig(money_state="NOT_OBSERVED", money_observed="$9,000")

    def test_M_money_never_enters_the_gravity_breakdown(self):
        """The most tempting arithmetic in the whole module."""
        rich = _sig(money_state="ADVERTISED", money_observed="$500,000")
        poor = _sig(sid="S2", source_id="mouth_b", source_lineage="lineage-b",
                    claim="widget six point zero point two shipped")
        g_rich = gravity(fuse([rich, poor]))
        plain = gravity(fuse([_sig(), poor]))
        self.assertEqual(g_rich.mass, plain.mass)
        self.assertNotIn("MONEY", " ".join(k for k, _ in g_rich.breakdown))

    def test_unknown_money_is_reported_as_unknown_not_zero(self):
        g = gravity(fuse([_sig()]))
        self.assertTrue(g.money_unknown)
        self.assertIn("contributes nothing", g.show_the_math())


class TestSourceMultiplicityIsNotIndependence(unittest.TestCase):
    def test_M_the_load_bearing_case_two_feeds_one_upstream_release(self):
        """The real shape: GitHub's atom feed and PyPI's RSS both announce
        one release. Two observations. One fact."""
        gh = _sig(sid="GH", source_id="github_releases",
                  source_lineage="pyyaml-release-6.0.2",
                  claim="Release 6.0.2 published on GitHub")
        pypi = _sig(sid="PYPI", source_id="pypi_releases",
                    source_lineage="pyyaml-release-6.0.2",
                    claim="6.0.2 appeared on the package index")
        rel = relate(gh, pypi)
        self.assertEqual(rel.kind, "DUPLICATE")
        self.assertIn("one fact observed twice", rel.reason)
        f = fuse([gh, pypi])
        self.assertEqual(f.independent_facts, 1)
        self.assertEqual(f.echoes, 1)

    def test_M_five_copies_of_one_blog_post_are_one_fact(self):
        sigs = [_sig(sid=f"S{i}", source_id=f"aggregator_{i}",
                     source_lineage="blogpost-42") for i in range(5)]
        f = fuse(sigs)
        self.assertEqual(f.independent_facts, 1)
        self.assertEqual(f.echoes, 4)
        self.assertLess(f.independent_facts, len(sigs))

    def test_identical_claim_text_is_an_echo_even_without_lineage(self):
        a = _sig(sid="A", source_id="one")
        b = _sig(sid="B", source_id="two")
        self.assertEqual(relate(a, b).kind, "DUPLICATE")

    def test_one_instrument_agreeing_with_itself_is_correlated(self):
        # Different wording, so not an echo by text -- but one instrument.
        a = _sig(sid="A", source_id="same_mouth", claim="version is 6.0.2")
        b = _sig(sid="B", source_id="same_mouth", claim="latest is 6.0.2 now")
        self.assertEqual(relate(a, b).kind, "CORRELATED")

    def test_genuinely_independent_sources_do_support_each_other(self):
        """Positive control: the discipline must not make corroboration
        impossible, only unearned."""
        a = _sig(sid="A", source_id="github", source_lineage="gh-observation")
        b = _sig(sid="B", source_id="package_index",
                 source_lineage="index-observation",
                 claim="the index lists 6.0.2 as current")
        rel = relate(a, b)
        self.assertEqual(rel.kind, "SUPPORTING")
        self.assertTrue(rel.counts_as_independent_support())
        self.assertEqual(fuse([a, b]).independent_facts, 2)

    def test_M_no_overlapping_facts_is_unknown_not_supporting(self):
        """Two signals about different aspects of one target are not
        corroboration, and this is the quietest way to fake evidence."""
        a = _sig(sid="A", facts={"latest_version": "6.0.2"})
        b = _sig(sid="B", source_id="other", facts={"open_issues": "12"},
                 claim="twelve issues are open")
        rel = relate(a, b)
        self.assertEqual(rel.kind, "UNKNOWN")
        self.assertIn("not corroboration", rel.reason)

    def test_signals_about_different_targets_are_not_comparable(self):
        self.assertEqual(
            relate(_sig(), _sig(target="other/thing")).kind, "UNKNOWN")

    def test_fusing_mixed_targets_is_refused(self):
        with self.assertRaises(SignalIntegrityError):
            fuse([_sig(), _sig(sid="B", target="other/thing")])

    def test_fusing_nothing_is_refused(self):
        with self.assertRaises(SignalIntegrityError):
            fuse([])


class TestContradictionSurvives(unittest.TestCase):
    def test_M_disagreeing_sources_are_contradictory_not_averaged(self):
        a = _sig(sid="A", source_id="one", facts={"latest_version": "6.0.2"})
        b = _sig(sid="B", source_id="two", facts={"latest_version": "5.4.1"},
                 claim="current release is 5.4.1")
        rel = relate(a, b)
        self.assertEqual(rel.kind, "CONTRADICTORY")
        self.assertIn("latest_version", rel.reason)
        self.assertIn("one", rel.reason)
        self.assertTrue(fuse([a, b]).has_contradiction())

    def test_a_contradiction_reduces_gravity(self):
        a = _sig(sid="A", source_id="one", facts={"latest_version": "6.0.2"})
        b = _sig(sid="B", source_id="two", facts={"latest_version": "5.4.1"},
                 claim="current release is 5.4.1")
        self.assertIn("UNRESOLVED_CONTRADICTION",
                      [k for k, _ in gravity(fuse([a, b])).breakdown])

    def test_M_a_contradicted_target_cannot_lock_however_strong(self):
        a = _sig(sid="A", source_id="one", source_type="OFFICIAL",
                 facts={"latest_version": "6.0.2"})
        b = _sig(sid="B", source_id="two", source_type="OFFICIAL",
                 facts={"latest_version": "5.4.1"},
                 claim="current release is 5.4.1")
        lock = target_lock(_entry([a, b]))
        self.assertEqual(lock.state, "RESOLVE_CONTRADICTION_FIRST")
        self.assertFalse(lock.authorises_investigation())

    def test_agreement_on_a_stale_event_is_stale_not_supporting(self):
        a = _sig(sid="A", source_id="one", event_at=_stamp(400),
                 source_lineage="l-a")
        b = _sig(sid="B", source_id="two", event_at=_stamp(1),
                 source_lineage="l-b", claim="also confirms 6.0.2")
        self.assertEqual(relate(a, b).kind, "STALE")


class TestGravityShowsItsMass(unittest.TestCase):
    def _independent_pair(self):
        return [_sig(sid="A", source_id="one", source_lineage="l-a"),
                _sig(sid="B", source_id="two", source_lineage="l-b",
                     claim="the index confirms 6.0.2 is current")]

    def test_every_gravity_score_can_be_broken_down(self):
        g = gravity(fuse(self._independent_pair()))
        self.assertTrue(g.breakdown)
        for label, _ in g.breakdown:
            self.assertTrue(label.isupper())

    def test_M_echoes_are_counted_and_ignored(self):
        echo = [_sig(sid=f"S{i}", source_id=f"agg_{i}",
                     source_lineage="one-post") for i in range(5)]
        g = gravity(fuse(echo))
        self.assertEqual(g.echoes_ignored, 4)
        self.assertNotIn("INDEPENDENT_CORROBORATION",
                         [k for k, _ in g.breakdown])
        self.assertIn("ECHO_ONLY_NO_CORROBORATION",
                      [k for k, _ in g.breakdown])

    def test_five_echoes_never_outweigh_two_independent_facts(self):
        echo = [_sig(sid=f"S{i}", source_id=f"agg_{i}",
                     source_lineage="one-post") for i in range(5)]
        self.assertLess(gravity(fuse(echo)).mass,
                        gravity(fuse(self._independent_pair())).mass)

    def test_an_authoritative_source_adds_mass_and_says_so(self):
        pair = self._independent_pair()
        weak = gravity(fuse(pair)).mass
        official = [_sig(sid="A", source_id="one", source_type="OFFICIAL",
                         source_lineage="l-a"), pair[1]]
        g = gravity(fuse(official))
        self.assertGreater(g.mass, weak)
        self.assertIn("AUTHORITATIVE_SOURCE_PRESENT",
                      [k for k, _ in g.breakdown])

    def test_gravity_is_not_power_and_not_confidence(self):
        """Three separate readings; no single magic number."""
        g = gravity(fuse(self._independent_pair()))
        surface = {f for f in dir(g) if not f.startswith("_")}
        self.assertNotIn("power_level", surface)
        self.assertNotIn("confidence", surface)


class TestTheMapEntryAnswersItsQuestions(unittest.TestCase):
    def _pair(self):
        return [_sig(sid="A", source_id="one", source_lineage="l-a"),
                _sig(sid="B", source_id="two", source_lineage="l-b",
                     claim="the index confirms 6.0.2 is current")]

    def test_an_entry_that_cannot_say_why_is_refused(self):
        with self.assertRaises(SignalIntegrityError) as ctx:
            _entry(self._pair(), why_on_the_map=())
        self.assertIn("bookmark", str(ctx.exception))

    def test_an_entry_must_name_what_would_kill_it(self):
        with self.assertRaises(SignalIntegrityError):
            _entry(self._pair(), what_would_kill_it="  ")

    def test_an_entry_must_name_the_cheapest_experiment(self):
        with self.assertRaises(SignalIntegrityError):
            _entry(self._pair(), next_cheapest_experiment="")

    def test_M_a_map_entry_is_never_a_finding(self):
        e = _entry(self._pair())
        self.assertEqual(e.bug_claim(), "NONE")
        self.assertEqual(e.value_claim(), "NOT_MEASURED")
        surface = {f for f in dir(e) if not f.startswith("_")}
        for forbidden in ("defect", "verdict", "receipt", "brick", "claims"):
            self.assertNotIn(forbidden, surface)

    def test_it_records_who_said_what_and_when(self):
        rows = _entry(self._pair()).who_said_what_when()
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertTrue(row["source"])
            self.assertTrue(row["observed_at"])
            self.assertTrue(row["event_at"])
            self.assertTrue(row["ref"])

    def test_value_signals_without_money_are_reported_separately(self):
        e = _entry(self._pair())
        self.assertEqual(e.money_observed(), "NONE")
        self.assertTrue(e.money_unknown())
        self.assertEqual(len(e.value_signals_without_money()), 2)

    def test_unknowns_survive_into_the_entry(self):
        pair = self._pair()
        pair[0] = _sig(sid="A", source_id="one", source_lineage="l-a",
                       unknowns=("licence unread",))
        self.assertIn("licence unread", _entry(pair).fused.unknowns)

    def test_the_render_shows_the_shape_not_just_a_number(self):
        text = _entry(self._pair()).render()
        for expected in ("GRAVITY", "WHO SAID WHAT", "MONEY OBSERVED",
                         "UNKNOWNS", "DISQUALIFIERS", "independent facts",
                         "echoes"):
            self.assertIn(expected, text)


class TestTheLockDoesNotAuthoriseItself(unittest.TestCase):
    def _strong(self):
        return [_sig(sid="A", source_id="one", source_type="OFFICIAL",
                     source_lineage="l-a"),
                _sig(sid="B", source_id="two", source_lineage="l-b",
                     claim="the index confirms 6.0.2 is current")]

    def test_a_strong_target_locks(self):
        lock = target_lock(_entry(self._strong()))
        self.assertEqual(lock.state, "LOCKED")
        self.assertGreaterEqual(
            gravity(fuse(self._strong())).mass, LOCK_THRESHOLD)

    def test_M_a_lock_recommends_but_does_not_authorise(self):
        lock = target_lock(_entry(self._strong()))
        self.assertTrue(lock.authorises_investigation())
        self.assertIn("does not authorise it", " ".join(lock.reasons))

    def test_M_no_gravity_outranks_a_disqualifier(self):
        lock = target_lock(_entry(self._strong(),
                                  disqualifiers=("SECURITY_SENSITIVE",)))
        self.assertEqual(lock.state, "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(lock.authorises_investigation())
        self.assertIn("no gravity may outrank a disqualifier",
                      " ".join(lock.reasons))

    def test_M_a_single_independent_fact_only_earns_a_watch(self):
        echo = [_sig(sid=f"S{i}", source_id=f"agg_{i}",
                     source_lineage="one-post") for i in range(5)]
        lock = target_lock(_entry(echo, why_on_the_map=("five mentions",)))
        self.assertEqual(lock.state, "WATCH")
        self.assertIn("multiplicity of sources was not multiplicity of "
                      "evidence", " ".join(lock.reasons))


if __name__ == "__main__":
    unittest.main()


class TestTheBridgeIntoTheExistingHunter(unittest.TestCase):
    """No second hunter. No mission_v2. No radar_hunter_final_final.py."""

    def _strong(self):
        return [_sig(sid="A", source_id="one", source_type="OFFICIAL",
                     source_lineage="l-a", unknowns=("licence unread",)),
                _sig(sid="B", source_id="two", source_lineage="l-b",
                     claim="the index confirms 6.0.2 is current")]

    def test_M_an_unlocked_entry_cannot_become_a_hunt(self):
        from foundation.signal_spine import LockNotEarned, to_opportunity
        echo = [_sig(sid=f"S{i}", source_id=f"agg_{i}",
                     source_lineage="one-post") for i in range(5)]
        e = _entry(echo, why_on_the_map=("five mentions",))
        with self.assertRaises(LockNotEarned) as ctx:
            to_opportunity(e, target_lock(e))
        self.assertIn("does not authorise its own hunt", str(ctx.exception))

    def test_a_locked_entry_produces_the_existing_opportunity_type(self):
        from foundation.opportunity import OpportunityReceipt, rank
        from foundation.signal_spine import to_opportunity
        e = _entry(self._strong())
        opp = to_opportunity(e, target_lock(e))
        self.assertIsInstance(opp, OpportunityReceipt)
        self.assertEqual(opp.bug_claim(), "NONE")
        self.assertIn(rank(opp).recommendation,
                      ("INVESTIGATE", "WATCH", "RECHECK", "IGNORE"))

    def test_M_echoes_are_left_behind_at_the_bridge(self):
        """Carrying five copies of one fact into the hunt would rebuild the
        inflation one layer later."""
        from foundation.signal_spine import to_opportunity
        sigs = self._strong() + [
            _sig(sid="C", source_id="agg", source_lineage="l-a",
                 claim="a third site repeats the same thing")]
        e = _entry(sigs)
        opp = to_opportunity(e, target_lock(e))
        self.assertEqual(len(sigs), 3)
        self.assertEqual(len(opp.signals), 2)

    def test_M_unknowns_and_disqualifiers_survive_the_bridge(self):
        from foundation.signal_spine import to_opportunity
        e = _entry(self._strong())
        opp = to_opportunity(e, target_lock(e))
        self.assertIn("licence unread", opp.unknowns)

    def test_the_bridge_creates_no_second_mission_type(self):
        import foundation.signal_spine as spine
        names = " ".join(spine.__all__).lower()
        for forbidden in ("mission", "hunter", "investigat"):
            self.assertNotIn(forbidden, names)


class TestValuePressure(unittest.TestCase):
    """Pressure is observed pull, never inferred popularity."""

    def _demand(self, **kw):
        base = dict(sid="D", source_id="github_issues", kind="DEMAND",
                    claim="maintainer asked for help on #42",
                    source_lineage="acme-issue-42",
                    facts={"open_help_wanted_issue": "42"},
                    pressure_class="EXPLICIT_DEMAND",
                    pressure_evidence="labelled help wanted; 12 comments")
        base.update(kw)
        return _sig(**base)

    def test_a_pressure_class_must_name_its_evidence(self):
        with self.assertRaises(SignalIntegrityError) as ctx:
            self._demand(pressure_evidence="")
        self.assertIn("names no evidence", str(ctx.exception))

    def test_an_invented_pressure_class_is_refused(self):
        with self.assertRaises(SignalIntegrityError):
            self._demand(pressure_class="LOOKS_HOT")

    def test_no_pressure_is_the_default_and_not_a_deficiency(self):
        self.assertEqual(_sig().pressure_class, "NONE")

    def test_observed_pressure_creates_mass(self):
        plain = gravity(fuse([_sig()])).mass
        self.assertGreater(gravity(fuse([self._demand()])).mass, plain)

    def test_M5_stale_pressure_creates_no_mass(self):
        """An expired complaint is not current pull."""
        stale = self._demand(event_at=_stamp(400))
        g = gravity(fuse([stale]))
        self.assertNotIn("VALUE_PRESSURE_EXPLICIT_DEMAND",
                         [k for k, _ in g.breakdown])
        # ...but it stays visible rather than being silently dropped.
        self.assertIn("EXPLICIT_DEMAND", g.pressure_observed)

    def test_pressure_is_reported_in_the_breakdown_by_name(self):
        g = gravity(fuse([self._demand()]))
        self.assertIn("VALUE_PRESSURE_EXPLICIT_DEMAND",
                      [k for k, _ in g.breakdown])
        self.assertIn("pressure observed", g.show_the_math())


class TestCorroborationIsNotConvergence(unittest.TestCase):
    """The defect the demand source class exposed: relate() said 'not
    corroboration' while gravity() scored INDEPENDENT_CORROBORATION for
    the very same pair."""

    def _release(self):
        return _sig(sid="R", source_id="github_releases", kind="RELEASE",
                    source_lineage="acme-release-7.0.0",
                    facts={"latest_version": "7.0.0"},
                    claim="7.0.0 was released")

    def _demand(self):
        return _sig(sid="D", source_id="github_issues", kind="DEMAND",
                    source_lineage="acme-issue-42",
                    facts={"open_help_wanted_issue": "42"},
                    claim="someone asked for help on #42",
                    pressure_class="EXPLICIT_DEMAND",
                    pressure_evidence="labelled help wanted; 12 comments")

    def test_M8_different_dimensions_are_never_called_corroboration(self):
        f = fuse([self._release(), self._demand()])
        self.assertEqual(f.corroborations, 0)
        self.assertEqual(f.convergences, 1)
        labels = [k for k, _ in gravity(f).breakdown]
        self.assertNotIn("INDEPENDENT_CORROBORATION", labels)
        self.assertIn("MULTI_DIMENSIONAL_CONVERGENCE", labels)

    def test_agreement_on_one_fact_is_corroboration_not_convergence(self):
        a = _sig(sid="A", source_id="one", source_lineage="l-a")
        b = _sig(sid="B", source_id="two", source_lineage="l-b",
                 claim="the index confirms 6.0.2 is current")
        f = fuse([a, b])
        self.assertEqual(f.corroborations, 1)
        self.assertEqual(f.convergences, 0)

    def test_the_relation_layer_and_the_mass_layer_now_agree(self):
        """The two layers described the same pair in contradictory words.
        Whatever relate() reports, gravity must not overstate."""
        f = fuse([self._release(), self._demand()])
        kinds = {rel.kind for _, _, rel in f.relations}
        self.assertEqual(kinds, {"UNKNOWN"})
        self.assertEqual(f.corroborations, 0)

    def test_M4_two_mirrors_of_one_demand_event_stay_one_fact(self):
        """A bounty board mirroring a GitHub issue is not a second voice."""
        issue = self._demand()
        mirror = _sig(sid="M", source_id="bounty_board", kind="DEMAND",
                      source_lineage="acme-issue-42",
                      facts={"open_help_wanted_issue": "42"},
                      claim="a board relists acme#42 as open work",
                      pressure_class="EXPLICIT_DEMAND",
                      pressure_evidence="relisted; 0 independent detail")
        f = fuse([issue, mirror])
        self.assertEqual(f.independent_facts, 1)
        self.assertEqual(f.echoes, 1)
        self.assertEqual(f.corroborations, 0)

    def test_convergence_requires_both_signals_to_be_current(self):
        stale_release = _sig(sid="R", source_id="github_releases",
                             kind="RELEASE", source_lineage="acme-release-1",
                             facts={"latest_version": "1.0"},
                             claim="1.0 released", event_at=_stamp(400))
        f = fuse([stale_release, self._demand()])
        self.assertEqual(f.convergences, 0)


class TestMoneyCannotBuyALock(unittest.TestCase):
    def _rich_demand(self, **kw):
        base = dict(sid="B", source_id="bounty_board", kind="REWARD",
                    source_lineage="acme-bounty-9",
                    facts={"bounty_open": "9"},
                    claim="a board advertises $50,000 for acme#9",
                    money_state="ADVERTISED", money_observed="$50,000",
                    pressure_class="INCENTIVE",
                    pressure_evidence="advertised reward listing")
        base.update(kw)
        return _sig(**base)

    def test_M1_an_advertised_reward_is_not_a_verified_one(self):
        s = self._rich_demand()
        self.assertEqual(s.money_state, "ADVERTISED")
        self.assertNotEqual(s.money_state, "VERIFIED_CURRENT")

    def test_M2_observed_money_is_never_reported_as_realised(self):
        for state in ("ADVERTISED", "VERIFIED_CURRENT"):
            s = self._rich_demand(money_state=state)
            self.assertEqual(s.money_claim(), "NOT_MEASURED")

    def test_M3_an_absent_reward_stays_absent_rather_than_becoming_zero(self):
        g = gravity(fuse([_sig()]))
        self.assertTrue(g.money_unknown)
        self.assertEqual(g.money_observed, "")
        self.assertNotIn("MONEY", " ".join(k for k, _ in g.breakdown))

    def test_M7_a_large_reward_cannot_force_a_lock_past_a_disqualifier(self):
        other = _sig(sid="X", source_id="github_issues", kind="DEMAND",
                     source_lineage="acme-issue-1",
                     facts={"open_help_wanted_issue": "1"},
                     claim="help is wanted on #1",
                     pressure_class="EXPLICIT_DEMAND",
                     pressure_evidence="labelled help wanted; 9 comments")
        e = _entry([self._rich_demand(), other],
                   why_on_the_map=("a large advertised reward",),
                   disqualifiers=("REQUIRES_SECRETS",))
        lock = target_lock(e)
        self.assertEqual(lock.state, "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(lock.authorises_investigation())

    def test_a_huge_reward_does_not_change_the_mass_at_all(self):
        other = _sig(sid="X", source_id="github_issues", kind="DEMAND",
                     source_lineage="acme-issue-1",
                     facts={"open_help_wanted_issue": "1"},
                     claim="help is wanted on #1")
        rich = gravity(fuse([self._rich_demand(), other]))
        poor = gravity(fuse([
            self._rich_demand(money_state="NOT_OBSERVED", money_observed="",
                              pressure_class="NONE", pressure_evidence=""),
            other]))
        # Only the pressure class differs in mass; money itself adds none.
        self.assertNotIn("MONEY", " ".join(k for k, _ in rich.breakdown))
        self.assertEqual(
            rich.mass - poor.mass,
            dict(rich.breakdown).get("VALUE_PRESSURE_INCENTIVE", 0))


class TestATentacleCannotBypassTheSpine(unittest.TestCase):
    def test_M6_the_tentacle_module_creates_no_opportunity_or_mission(self):
        """The tentacle sees. The spine thinks. The gate decides."""
        import foundation.tentacles as tentacles
        import ast, inspect
        tree = ast.parse(inspect.getsource(tentacles))
        called = {n.func.id for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        for forbidden in ("OpportunityReceipt", "handoff", "materialise",
                          "Receipt", "GoldBrick", "to_opportunity"):
            self.assertNotIn(forbidden, called)

    def test_the_tentacle_module_imports_no_receipt_or_mission_machinery(self):
        import foundation.tentacles as tentacles
        import ast, inspect
        tree = ast.parse(inspect.getsource(tentacles))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        for forbidden in ("foundation.opportunity", "foundation.receipt",
                          "foundation.gold_brick"):
            self.assertNotIn(forbidden, imported)

    def test_a_demand_signal_still_claims_no_bug_and_no_value(self):
        from foundation.tentacles import github_issue_demand_signal
        s = github_issue_demand_signal({
            "repo": "acme/widget", "number": 42, "title": "help please",
            "labels": ["help wanted"], "comments": 5,
            "created_at": "2026-08-01T00:00:00Z",
            "updated_at": "2026-08-29T00:00:00Z", "state": "open",
            "html_url": "https://github.invalid/acme/widget/issues/42"})
        self.assertEqual(s.kind, "DEMAND")
        self.assertEqual(s.money_claim(), "NOT_MEASURED")
        self.assertEqual(s.pressure_class, "EXPLICIT_DEMAND")
        self.assertTrue(s.unknowns)


class TestTheDemandAdapter(unittest.TestCase):
    def _item(self, **kw):
        base = dict(repo="acme/widget", number=42, title="Looking for help",
                    labels=["help wanted"], comments=12,
                    created_at="2021-08-16T07:47:38Z",
                    updated_at="2026-08-29T12:00:00Z", state="open",
                    html_url="https://github.invalid/acme/widget/issues/42")
        base.update(kw)
        return base

    def test_event_time_is_last_activity_not_creation(self):
        """A 2021 request still argued about this week is live pressure;
        using creation time would call it stale and get it backwards."""
        from foundation.tentacles import github_issue_demand_signal
        s = github_issue_demand_signal(self._item())
        self.assertTrue(s.event_at.startswith("2026-08-29"))
        self.assertEqual(s.evidence["first_expressed"],
                         "2021-08-16T07:47:38Z")

    def test_the_age_of_the_ask_stays_visible(self):
        from foundation.tentacles import github_issue_demand_signal
        s = github_issue_demand_signal(self._item())
        self.assertEqual(s.evidence["first_expressed"], "2021-08-16T07:47:38Z")

    def test_M_two_asks_on_one_repo_are_not_a_contradiction(self):
        """Found live: issue numbers in `facts` made two separate asks
        collide on one key and read as disagreement. #1 and #2 do not
        disagree -- two people asked."""
        from foundation.tentacles import github_issue_demand_signal
        from foundation.signal_spine import fuse
        a = github_issue_demand_signal(self._item(number=1))
        b = github_issue_demand_signal(self._item(number=2))
        f = fuse([a, b])
        self.assertEqual(f.contradictions, ())
        self.assertEqual(f.independent_facts, 2)

    def test_M_two_asks_are_two_voices_not_two_dimensions(self):
        """Convergence is across dimensions. Same-kind signals are not it."""
        from foundation.tentacles import github_issue_demand_signal
        from foundation.signal_spine import fuse
        f = fuse([github_issue_demand_signal(self._item(number=1)),
                  github_issue_demand_signal(self._item(number=2))])
        self.assertEqual(f.convergences, 0)

    def test_an_unlabelled_issue_carries_no_pressure(self):
        """Popularity is not demand."""
        from foundation.tentacles import github_issue_demand_signal
        s = github_issue_demand_signal(self._item(labels=["bug"], comments=900))
        self.assertEqual(s.pressure_class, "NONE")
        self.assertEqual(s.pressure_evidence, "")

    def test_two_issues_in_one_repo_are_two_separate_asks(self):
        from foundation.tentacles import demand_lineage
        self.assertNotEqual(demand_lineage("acme/widget", 1),
                            demand_lineage("acme/widget", 2))

    def test_the_mouth_refuses_to_harvest(self):
        from foundation.mouth_github_issues import build_url, MAX_PER_PAGE
        with self.assertRaises(ValueError) as ctx:
            build_url(500)
        self.assertIn("does not harvest", str(ctx.exception))
        self.assertIn("per_page=10", build_url(MAX_PER_PAGE))

    def test_malformed_payload_yields_no_signals_rather_than_guesses(self):
        from foundation.mouth_github_issues import parse_items
        self.assertEqual(parse_items(b"not json"), ())
        self.assertEqual(parse_items(b'{"items":[{"no":"url"}]}'), ())


class TestConvergenceIsNotQuadraticInSignalCount(unittest.TestCase):
    """Found by running the full chain live: five demand issues plus one
    activity signal plus one pressure signal reported ELEVEN convergent
    dimensions when three were present, inflating gravity by 5,500."""

    def _d(self, n):
        return _sig(sid=f"D{n}", source_id="issues", kind="DEMAND",
                    source_lineage=f"acme-issue-{n}", facts={},
                    claim=f"issue {n} asks for help",
                    pressure_class="EXPLICIT_DEMAND",
                    pressure_evidence="labelled help wanted")

    def _a(self):
        return _sig(sid="A", source_id="commits", kind="ACTIVITY",
                    source_lineage="acme-commit-1", facts={},
                    claim="a commit landed")

    def _p(self):
        return _sig(sid="P", source_id="commits", kind="CODE_PRESSURE",
                    source_lineage="acme-pressure", facts={},
                    claim="50% remediation")

    def test_M_three_dimensions_report_three_not_eleven(self):
        f = fuse([self._d(1), self._d(2), self._d(3), self._d(4), self._d(5),
                  self._a(), self._p()])
        # kind-pairs: DEMAND/ACTIVITY, DEMAND/CODE_PRESSURE, ACTIVITY/CODE_PRESSURE
        self.assertEqual(f.convergences, 3)

    def test_M_adding_more_of_the_same_kind_does_not_add_convergence(self):
        """The load-bearing property: convergence is bounded by how many
        DIMENSIONS exist, not how many signals arrived."""
        few = fuse([self._d(1), self._a()])
        many = fuse([self._d(i) for i in range(1, 21)] + [self._a()])
        self.assertEqual(few.convergences, many.convergences)
        self.assertEqual(many.convergences, 1)

    def test_M_gravity_no_longer_inflates_with_signal_count(self):
        few = gravity(fuse([self._d(1), self._a()]))
        many = gravity(fuse([self._d(i) for i in range(1, 21)] + [self._a()]))
        self.assertEqual(
            dict(few.breakdown)["MULTI_DIMENSIONAL_CONVERGENCE"],
            dict(many.breakdown)["MULTI_DIMENSIONAL_CONVERGENCE"])

    def test_a_genuinely_new_dimension_still_counts(self):
        """Positive control: the fix must not make convergence unreachable."""
        two = fuse([self._d(1), self._a()])
        three = fuse([self._d(1), self._a(), self._p()])
        self.assertEqual(two.convergences, 1)
        self.assertEqual(three.convergences, 3)


class TestAClaimedAskIsNotOpenDemand(unittest.TestCase):
    """Found by the first killing experiment the radar ever ran: all five
    "help wanted" issues on a LOCKED target were already assigned, and the
    demand instrument had counted every one as an open request."""

    def _item(self, assignees=(), **kw):
        base = dict(repo="acme/widget", number=42, title="help please",
                    labels=["help wanted"], comments=6,
                    created_at="2026-08-01T00:00:00Z",
                    updated_at="2026-09-01T00:00:00Z", state="open",
                    assignees=list(assignees),
                    html_url="https://github.invalid/acme/widget/issues/42")
        base.update(kw)
        return base

    def test_M_an_assigned_ask_carries_no_demand_pressure(self):
        from foundation.tentacles import github_issue_demand_signal
        try:
            s = github_issue_demand_signal(self._item(assignees=["someone"]))
        except Exception as exc:                 # noqa: BLE001 -- the point
            self.fail(f"a claimed ask must build a signal carrying NO demand "
                      f"pressure, not fail construction. Raised: {exc!r}")
        self.assertEqual(
            s.pressure_class, "NONE",
            "an ask somebody has already taken is not open demand")
        self.assertEqual(s.pressure_evidence, "")

    def test_M_an_unassigned_ask_still_carries_demand(self):
        """Positive control: the fix must not silence real demand."""
        from foundation.tentacles import github_issue_demand_signal
        s = github_issue_demand_signal(self._item())
        self.assertEqual(s.pressure_class, "EXPLICIT_DEMAND")
        self.assertIn("unassigned", s.pressure_evidence)

    def test_M_a_claimed_ask_says_so_in_its_unknowns(self):
        from foundation.tentacles import github_issue_demand_signal
        s = github_issue_demand_signal(self._item(assignees=["someone"]))
        self.assertTrue(any("already claimed" in u for u in s.unknowns))
        self.assertTrue(s.evidence["claimed"])

    def test_M_claimed_asks_create_no_pressure_mass(self):
        """The whole point: five claimed asks must not build gravity."""
        from foundation.tentacles import github_issue_demand_signal
        from foundation.signal_spine import fuse, gravity
        sigs = [github_issue_demand_signal(
            self._item(number=n, assignees=["dev"],
                       html_url=f"https://github.invalid/i/{n}"))
            for n in range(1, 6)]
        g = gravity(fuse(sigs))
        self.assertNotIn("VALUE_PRESSURE_EXPLICIT_DEMAND",
                         [k for k, _ in g.breakdown])
        self.assertEqual(g.pressure_observed, ())

    def test_the_mouth_preserves_assignment_from_the_payload(self):
        from foundation.mouth_github_issues import parse_items
        import json
        raw = json.dumps({"items": [{
            "html_url": "https://x.invalid/1", "repository_url": "/repos/a/b",
            "number": 1, "title": "t", "labels": [],
            "assignees": [{"login": "dev1"}, {"login": "dev2"}],
            "comments": 0, "state": "open"}]}).encode()
        self.assertEqual(parse_items(raw)[0]["assignees"], ["dev1", "dev2"])
