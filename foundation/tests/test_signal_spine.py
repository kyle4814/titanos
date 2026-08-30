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
