"""An instrument that always fires is a constant, not an instrument.

`rank()` awarded points for CODE_PRESSURE that no instrument emitted, so
INVESTIGATE was structurally unreachable. The temptation was to lower the
threshold. This measures something real instead — and must be able to say
"no pressure here", or it is just the tuning it replaced.
"""

import unittest

from foundation.code_pressure import (
    COMMIT_CLASSES,
    MIN_SAMPLE,
    PRESSURE_SHARE,
    PressureProfile,
    classify_subject,
    measure_pressure,
)


def _c(subject, sha="abc12345"):
    return {"sha": sha, "subject": subject}


class TestSubjectClassification(unittest.TestCase):
    def test_plain_repair_words_are_remediation(self):
        for s in ("fix the alias import path", "hotfix: null deref",
                  "revert 3f2a1b", "rollback the migration",
                  "repair broken CI", "fixes regression in parser"):
            self.assertEqual(classify_subject(s), "REMEDIATION", s)

    def test_M_prefix_must_not_match_fix(self):
        """Word-bounded on purpose: substring matching would classify half
        the corpus as repair."""
        self.assertNotEqual(classify_subject("add prefix handling"),
                            "REMEDIATION")
        self.assertNotEqual(classify_subject("suffix parser rewrite"),
                            "REMEDIATION")

    def test_M_fixing_a_typo_is_housekeeping_not_pressure(self):
        """A repository correcting spelling is not a repository under
        strain, and counting it as such would inflate every window."""
        for s in ("fix typo in README", "fix docs formatting",
                  "fix comment spelling"):
            self.assertEqual(classify_subject(s), "MAINTENANCE", s)

    def test_repair_wins_over_a_feature_verb(self):
        """'add retry to fix flaky upload' is repair wearing a feature
        verb."""
        self.assertEqual(
            classify_subject("add retry to fix flaky upload"), "REMEDIATION")

    def test_feature_and_maintenance_are_distinguished(self):
        self.assertEqual(classify_subject("implement the new resolver"),
                         "FEATURE")
        self.assertEqual(classify_subject("bump pyyaml to 6.0.3"),
                         "MAINTENANCE")
        self.assertEqual(classify_subject("Merge pull request #244"),
                         "MAINTENANCE")

    def test_M_an_unreadable_subject_stays_unclassified(self):
        """Never guessed into a class in either direction."""
        for s in ("", "   ", "wip", "asdf"):
            self.assertEqual(classify_subject(s), "UNCLASSIFIED", repr(s))

    def test_every_class_is_declared(self):
        for s in ("fix it", "add it", "chore: x", "zzz"):
            self.assertIn(classify_subject(s), COMMIT_CLASSES)


class TestTheInstrumentCanSayNo(unittest.TestCase):
    def test_M_a_healthy_window_is_not_pressured(self):
        """The load-bearing case. An instrument that always fires is a
        constant, and wiring a constant into rank() is tuning."""
        p = measure_pressure([_c("implement the resolver"),
                              _c("add streaming support"),
                              _c("bump deps"),
                              _c("implement caching"),
                              _c("add docs page")])
        self.assertFalse(p.is_pressured())
        self.assertIsNotNone(p.share())
        self.assertEqual(p.remediation, 0)

    def test_M_a_pressured_window_is_reported(self):
        """Positive control: the discipline must not make detection
        impossible, only unearned."""
        p = measure_pressure([_c("fix the parser"), _c("hotfix null deref"),
                              _c("revert bad migration"),
                              _c("implement resolver"), _c("bump deps")])
        self.assertTrue(p.is_pressured())
        self.assertGreaterEqual(p.share(), PRESSURE_SHARE)

    def test_M_a_tiny_sample_is_never_pressured(self):
        """Three commits, two of them fixes, is not a pattern."""
        p = measure_pressure([_c("fix a"), _c("fix b"), _c("add c")])
        self.assertLess(p.sample, MIN_SAMPLE)
        self.assertFalse(p.is_pressured())
        self.assertFalse(p.is_measurable())
        self.assertIn("NOT MEASURABLE", p.show_the_math())

    def test_M_an_all_unclassified_window_has_no_share(self):
        """None, never a fabricated 0.0 -- unreadable subjects are not
        evidence of health either."""
        p = measure_pressure([_c("wip")] * 6)
        self.assertIsNone(p.share())
        self.assertFalse(p.is_pressured())
        self.assertFalse(p.is_measurable())

    def test_M_the_share_excludes_unclassified_commits(self):
        """Dividing by the whole window would let unreadable subjects
        silently dilute real pressure."""
        p = measure_pressure([_c("fix a"), _c("fix b"), _c("add c"),
                              _c("wip"), _c("wip"), _c("wip")])
        self.assertEqual(p.classified(), 3)
        self.assertAlmostEqual(p.share(), 2 / 3)

    def test_an_empty_window_is_not_measurable(self):
        p = measure_pressure([])
        self.assertFalse(p.is_measurable())
        self.assertIsNone(p.share())


class TestItShowsAndBoundsItsClaim(unittest.TestCase):
    def _pressured(self):
        return measure_pressure([_c("fix parser", "aaa11111"),
                                 _c("hotfix deref", "bbb22222"),
                                 _c("revert migration", "ccc33333"),
                                 _c("implement resolver"), _c("bump deps")])

    def test_the_math_names_the_threshold_and_model_version(self):
        text = self._pressured().show_the_math()
        self.assertIn("threshold", text)
        self.assertIn("model v", text)
        self.assertIn("remediation", text)

    def test_M_it_states_that_its_own_evidence_is_weak(self):
        """Subject lines describe what commits SAY, not what they changed.
        Said out loud rather than buried."""
        self.assertIn("weak", self._pressured().show_the_math())
        self.assertIn("not what they changed", self._pressured().show_the_math())

    def test_it_cites_the_commits_it_counted(self):
        text = self._pressured().show_the_math()
        self.assertIn("aaa11111", text)
        self.assertIn("evidence:", text)

    def test_M_it_never_claims_a_defect(self):
        p = self._pressured()
        surface = {f for f in dir(p) if not f.startswith("_")}
        for banned in ("bug", "defect", "vulnerability", "severity"):
            self.assertNotIn(banned, surface)
        self.assertNotIn("bug", p.show_the_math().lower())


class TestTheAdapterOnlyEmitsWhenEarned(unittest.TestCase):
    def _mapping(self, target="acme/widget"):
        from foundation.target_mapping import source_native_target
        return source_native_target(target)

    def _sig(self, items, target="acme/widget", event="2026-09-01T00:00:00Z"):
        from foundation.tentacles import code_pressure_signal
        return code_pressure_signal(measure_pressure(items),
                                    self._mapping(target), target,
                                    latest_event_at=event)

    def test_M_no_signal_is_emitted_for_a_healthy_repository(self):
        """The single most important test in this module."""
        self.assertIsNone(self._sig([_c("implement a"), _c("add b"),
                                     _c("bump c"), _c("add d"), _c("add e")]))

    def test_M_no_signal_for_a_sample_too_small_to_judge(self):
        self.assertIsNone(self._sig([_c("fix a"), _c("fix b")]))

    def test_a_pressured_window_yields_a_code_pressure_signal(self):
        s = self._sig([_c("fix a"), _c("hotfix b"), _c("revert c"),
                       _c("add d"), _c("bump e")])
        self.assertIsNotNone(s)
        self.assertEqual(s.kind, "CODE_PRESSURE")
        self.assertEqual(s.target_established_by, "SOURCE_NATIVE")

    def test_M_the_signal_claims_a_share_not_a_defect(self):
        s = self._sig([_c("fix a"), _c("hotfix b"), _c("revert c"),
                       _c("add d"), _c("bump e")])
        self.assertIn("remediation", s.claim)
        self.assertNotIn("bug", s.claim.lower())
        self.assertNotIn("defect", s.claim.lower())
        self.assertEqual(s.money_claim(), "NOT_MEASURED")

    def test_M_the_window_carries_no_target_level_facts(self):
        """A window is not a claim about the target that another source
        could contradict -- the issue-number defect, not repeated."""
        s = self._sig([_c("fix a"), _c("hotfix b"), _c("revert c"),
                       _c("add d"), _c("bump e")])
        self.assertEqual(dict(s.facts), {})

    def test_M_a_stale_pressured_window_reads_as_stale(self):
        s = self._sig([_c("fix a"), _c("hotfix b"), _c("revert c"),
                       _c("add d"), _c("bump e")],
                      event="2020-01-01T00:00:00Z")
        self.assertTrue(s.is_stale())

    def test_the_signal_records_its_weakness_as_an_unknown(self):
        s = self._sig([_c("fix a"), _c("hotfix b"), _c("revert c"),
                       _c("add d"), _c("bump e")])
        self.assertTrue(any("not what they changed" in u for u in s.unknowns))


class TestItActuallyMovesTheCeiling(unittest.TestCase):
    """The point of the whole exercise: INVESTIGATE was unreachable."""

    def _opp(self, extra=()):
        from foundation.opportunity import (OpportunityReceipt, SignalEvidence,
                                            opportunity_id_for)
        sigs = [SignalEvidence(kind="DEMAND", detail="d",
                               source_type="PLATFORM"),
                SignalEvidence(kind="ACTIVITY", detail="a",
                               source_type="PLATFORM")] + list(extra)
        return OpportunityReceipt(
            opportunity_id=opportunity_id_for("acme/widget", "p"),
            target="acme/widget", discovered_at="2026-09-01T00:00:00+00:00",
            signals=tuple(sigs), activity_class="ACTIVE",
            locally_reproducible="UNKNOWN")

    def test_M_without_code_pressure_the_target_is_still_capped(self):
        from foundation.opportunity import ceiling_analysis, rank
        self.assertEqual(rank(self._opp()).recommendation, "WATCH")
        self.assertTrue(ceiling_analysis(self._opp()).is_structurally_capped())

    def test_M_with_real_code_pressure_investigate_becomes_reachable(self):
        """Earned by evidence, not by lowering the threshold from 5 to 4."""
        from foundation.opportunity import SignalEvidence, rank, INVESTIGATE_THRESHOLD
        opp = self._opp(extra=[SignalEvidence(
            kind="CODE_PRESSURE",
            detail="60% of 5 classified commits are remediation",
            source_type="PLATFORM")])
        r = rank(opp)
        self.assertGreaterEqual(r.priority, INVESTIGATE_THRESHOLD)
        self.assertEqual(r.recommendation, "INVESTIGATE")

    def test_the_threshold_was_not_moved(self):
        from foundation.opportunity import INVESTIGATE_THRESHOLD
        self.assertEqual(INVESTIGATE_THRESHOLD, 5)


if __name__ == "__main__":
    unittest.main()


class TestTheClassifiedBaseMustBeBigEnough(unittest.TestCase):
    """Found by live execution: dotnet/runtime reported a 67% share from
    two remediation commits out of three classified, seven subjects
    unreadable. Guarding only the window size moved the small-sample
    problem down a level instead of solving it."""

    def test_M_a_thin_classified_base_is_not_measurable(self):
        p = measure_pressure([_c("fix a"), _c("hotfix b"), _c("add c")]
                             + [_c("wip")] * 7)
        self.assertEqual(p.sample, 10)
        self.assertEqual(p.classified(), 3)
        self.assertFalse(p.is_measurable())
        self.assertFalse(p.is_pressured())
        self.assertIn("classifiable subject", p.show_the_math())

    def test_the_share_is_still_computed_and_visible(self):
        """Not measurable does not mean not reported -- the number stays
        available, it simply does not authorise a signal."""
        p = measure_pressure([_c("fix a"), _c("hotfix b"), _c("add c")]
                             + [_c("wip")] * 7)
        self.assertAlmostEqual(p.share(), 2 / 3)

    def test_M_a_wide_classified_base_still_measures(self):
        p = measure_pressure([_c("fix a"), _c("hotfix b"), _c("revert c"),
                              _c("repair d"), _c("add e"), _c("bump f")])
        self.assertGreaterEqual(p.classified(), MIN_SAMPLE)
        self.assertTrue(p.is_measurable())
        self.assertTrue(p.is_pressured())

    def test_M_no_signal_is_emitted_from_a_thin_base(self):
        from foundation.target_mapping import source_native_target
        from foundation.tentacles import code_pressure_signal
        p = measure_pressure([_c("fix a"), _c("hotfix b"), _c("add c")]
                             + [_c("wip")] * 7)
        self.assertIsNone(code_pressure_signal(
            p, source_native_target("acme/widget"), "acme/widget"))
