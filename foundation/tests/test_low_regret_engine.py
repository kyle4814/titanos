import unittest

from foundation.low_regret_engine import (
    Candidate,
    LowRegretDecision,
    select_lowest_regret,
)


def cand(name, expected, worst, reversible, confidence="MEDIUM"):
    return Candidate(
        name=name,
        expected_value=expected,
        worst_case_value=worst,
        reversibility=reversible,
        confidence=confidence,
    )


class TestCandidateValidation(unittest.TestCase):
    def test_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            cand("", 10, 5, True)

    def test_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            cand("   ", 10, 5, True)

    def test_rejects_bad_confidence(self):
        with self.assertRaises(ValueError):
            cand("A", 10, 5, True, confidence="VERY_SURE")

    def test_rejects_worst_case_above_expected(self):
        with self.assertRaises(ValueError):
            cand("A", 5, 10, True)

    def test_allows_worst_case_equal_to_expected(self):
        c = cand("A", 5, 5, True)
        self.assertEqual(c.worst_case_value, 5)

    def test_to_dict_roundtrip_shape(self):
        c = cand("A", 10, 5, True, confidence="HIGH")
        d = c.to_dict()
        self.assertEqual(d["name"], "A")
        self.assertEqual(d["expected_value"], 10)
        self.assertEqual(d["worst_case_value"], 5)
        self.assertTrue(d["reversibility"])
        self.assertEqual(d["confidence"], "HIGH")


class TestSelectLowestRegretBasic(unittest.TestCase):
    def test_empty_candidates_raises(self):
        with self.assertRaises(ValueError):
            select_lowest_regret([])

    def test_single_candidate_is_selected_with_zero_regret(self):
        decision = select_lowest_regret([cand("Only", 10, 2, True)])
        self.assertEqual(decision.selected.name, "Only")
        self.assertEqual(decision.selected.regret, 0.0)
        self.assertEqual(decision.best_worst_case, 2)
        self.assertEqual(decision.tied_with, [])

    def test_selects_least_bad_worst_case_over_highest_expected_value(self):
        # High-EV, high-downside option vs modest-EV, safe-downside option.
        # Minimax regret must prefer the safe worst case even though its
        # expected value is lower -- this is the entire point of the rule.
        risky = cand("Risky", expected=1000, worst=-500, reversible=False)
        safe = cand("Safe", expected=50, worst=10, reversible=True)
        decision = select_lowest_regret([risky, safe])
        self.assertEqual(decision.selected.name, "Safe")

    def test_regret_values_match_minimax_formula(self):
        a = cand("A", expected=100, worst=0, reversible=True)
        b = cand("B", expected=100, worst=40, reversible=True)
        c = cand("C", expected=100, worst=-20, reversible=True)
        decision = select_lowest_regret([a, b, c])
        # best_worst_case = 40 (B's worst case)
        self.assertEqual(decision.best_worst_case, 40)
        regrets = {r.name: r.regret for r in decision.all_regrets}
        self.assertEqual(regrets["A"], 40)   # 40 - 0
        self.assertEqual(regrets["B"], 0)    # 40 - 40
        self.assertEqual(regrets["C"], 60)   # 40 - (-20)
        self.assertEqual(decision.selected.name, "B")

    def test_all_regrets_present_for_every_candidate(self):
        candidates = [
            cand("A", 10, 1, True),
            cand("B", 10, 2, True),
            cand("C", 10, 3, True),
        ]
        decision = select_lowest_regret(candidates)
        names = {r.name for r in decision.all_regrets}
        self.assertEqual(names, {"A", "B", "C"})
        self.assertEqual(len(decision.all_regrets), 3)

    def test_regret_is_never_negative(self):
        candidates = [
            cand("A", 10, -100, True),
            cand("B", 10, 5, True),
            cand("C", 10, 9, True),
        ]
        decision = select_lowest_regret(candidates)
        for r in decision.all_regrets:
            self.assertGreaterEqual(r.regret, 0.0)


class TestTieBreak(unittest.TestCase):
    def test_tie_broken_by_reversibility_not_expected_value(self):
        # Both candidates tie on worst_case_value (regret == 0 for both).
        # The irreversible one has the higher expected_value -- if the
        # tie-break silently preferred EV it would pick the wrong one.
        reversible_lower_ev = cand(
            "SafeChoice", expected=20, worst=10, reversible=True
        )
        irreversible_higher_ev = cand(
            "RiskyChoice", expected=500, worst=10, reversible=False
        )
        decision = select_lowest_regret(
            [irreversible_higher_ev, reversible_lower_ev]
        )
        self.assertEqual(decision.selected.name, "SafeChoice")
        self.assertEqual(decision.tied_with, [])

    def test_tie_with_no_reversible_option_falls_back_to_first(self):
        a = cand("A", expected=10, worst=5, reversible=False)
        b = cand("B", expected=10, worst=5, reversible=False)
        decision = select_lowest_regret([a, b])
        self.assertEqual(decision.selected.name, "A")
        self.assertEqual(decision.tied_with, ["B"])

    def test_tie_among_multiple_reversible_options_surfaces_remaining_tie(self):
        a = cand("A", expected=10, worst=5, reversible=True)
        b = cand("B", expected=20, worst=5, reversible=True)
        c = cand("C", expected=5, worst=5, reversible=True)
        decision = select_lowest_regret([a, b, c])
        self.assertEqual(decision.selected.name, "A")
        self.assertEqual(set(decision.tied_with), {"B", "C"})

    def test_decision_to_dict_shape(self):
        a = cand("A", expected=10, worst=5, reversible=True)
        b = cand("B", expected=10, worst=5, reversible=False)
        decision = select_lowest_regret([a, b])
        self.assertIsInstance(decision, LowRegretDecision)
        d = decision.to_dict()
        self.assertIn("selected", d)
        self.assertIn("best_worst_case", d)
        self.assertIn("all_regrets", d)
        self.assertIn("tied_with", d)
        self.assertEqual(len(d["all_regrets"]), 2)


class TestAdversarialReviewFindings(unittest.TestCase):
    """Two real findings from adversarial review, 2026-08-26: duplicate
    candidate names made results ambiguous, and exact float equality on
    subtracted regret values missed floating-point-representation ties."""

    def test_duplicate_candidate_names_rejected(self):
        a = cand("X", expected=10, worst=5, reversible=True)
        b = cand("X", expected=20, worst=8, reversible=False)
        with self.assertRaises(ValueError):
            select_lowest_regret([a, b])

    def test_float_representation_tie_is_detected(self):
        # worst_case_value=0.1+0.2 vs 0.3 are mathematically equal but
        # not bit-identical -- proven live by the reviewer to previously
        # produce regrets of 0.0 and 5.55e-17, missed by exact `==`.
        a = cand("A", expected=1.0, worst=0.1 + 0.2, reversible=False)
        b = cand("B", expected=1.0, worst=0.3, reversible=True)
        decision = select_lowest_regret([a, b])
        # Both are within REGRET_TIE_EPSILON of each other -- the tie
        # must be detected, and the reversible one must win the tie-break.
        self.assertEqual(decision.selected.name, "B")

    def test_genuinely_different_regret_is_not_falsely_tied(self):
        # Epsilon must not be so large it treats real differences as ties.
        a = cand("A", expected=10, worst=5, reversible=True)
        b = cand("B", expected=10, worst=5.01, reversible=False)
        decision = select_lowest_regret([a, b])
        self.assertEqual(decision.selected.name, "B")
        self.assertEqual(decision.tied_with, [])


if __name__ == "__main__":
    unittest.main()
