import unittest

from foundation.state_space_mapper import (
    DIMENSIONS,
    StateSpaceMap,
    UnknownDimensionError,
    build_state_space,
    diff_state_spaces,
)


class TestDimensionVocabulary(unittest.TestCase):
    def test_exactly_eleven_dimensions(self):
        self.assertEqual(len(DIMENSIONS), 11)

    def test_dimensions_match_doctrine_text(self):
        expected = {
            "time", "scale", "domain", "actor", "incentive", "threat",
            "uncertainty", "evidence", "consequence", "intervention",
            "recovery",
        }
        self.assertEqual(DIMENSIONS, frozenset(expected))


class TestBuildStateSpace(unittest.TestCase):
    def test_empty_call_is_legal(self):
        m = build_state_space()
        self.assertIsInstance(m, StateSpaceMap)
        self.assertEqual(m.declared(), frozenset())
        self.assertEqual(m.to_dict(), {})

    def test_single_dimension(self):
        m = build_state_space(time="near-term")
        self.assertEqual(m.declared(), frozenset({"time"}))
        self.assertEqual(m.to_dict(), {"time": "near-term"})

    def test_partial_subset_of_dimensions(self):
        m = build_state_space(threat="low", actor="internal")
        self.assertEqual(m.declared(), frozenset({"threat", "actor"}))

    def test_all_eleven_dimensions_allowed(self):
        kwargs = {d: f"value-{d}" for d in DIMENSIONS}
        m = build_state_space(**kwargs)
        self.assertEqual(m.declared(), DIMENSIONS)

    def test_unknown_dimension_rejected(self):
        with self.assertRaises(UnknownDimensionError) as ctx:
            build_state_space(tiem="now")
        self.assertIn("tiem", ctx.exception.unknown_keys)

    def test_unknown_dimension_error_names_all_bad_keys(self):
        with self.assertRaises(UnknownDimensionError) as ctx:
            build_state_space(tiem="now", scael="big")
        self.assertEqual(ctx.exception.unknown_keys, frozenset({"tiem", "scael"}))

    def test_mixing_valid_and_unknown_still_rejects(self):
        with self.assertRaises(UnknownDimensionError):
            build_state_space(time="now", bogus="x")

    def test_empty_value_rejected(self):
        with self.assertRaises(ValueError):
            build_state_space(scale="")

    def test_whitespace_only_value_rejected(self):
        with self.assertRaises(ValueError):
            build_state_space(scale="   ")

    def test_non_string_value_rejected(self):
        with self.assertRaises(ValueError):
            build_state_space(scale=123)  # type: ignore[arg-type]

    def test_map_is_immutable(self):
        m = build_state_space(time="now")
        with self.assertRaises(Exception):
            m.dimensions["time"] = "later"  # type: ignore[index]

    def test_dataclass_itself_is_frozen(self):
        m = build_state_space(time="now")
        with self.assertRaises(Exception):
            m.dimensions = {}  # type: ignore[misc]


class TestDiffStateSpaces(unittest.TestCase):
    def test_identical_maps_have_no_difference(self):
        a = build_state_space(time="now", threat="low")
        b = build_state_space(time="now", threat="low")
        diff = diff_state_spaces(a, b)
        self.assertEqual(diff.shared_equal, frozenset({"time", "threat"}))
        self.assertEqual(diff.shared_different, frozenset())
        self.assertEqual(diff.only_in_first, frozenset())
        self.assertEqual(diff.only_in_second, frozenset())
        self.assertFalse(diff.differs())

    def test_two_empty_maps_do_not_differ(self):
        diff = diff_state_spaces(build_state_space(), build_state_space())
        self.assertFalse(diff.differs())

    def test_shared_dimension_different_value(self):
        a = build_state_space(threat="low")
        b = build_state_space(threat="high")
        diff = diff_state_spaces(a, b)
        self.assertEqual(diff.shared_different, frozenset({"threat"}))
        self.assertTrue(diff.differs())

    def test_dimension_only_in_first(self):
        a = build_state_space(actor="internal")
        b = build_state_space()
        diff = diff_state_spaces(a, b)
        self.assertEqual(diff.only_in_first, frozenset({"actor"}))
        self.assertEqual(diff.only_in_second, frozenset())
        self.assertTrue(diff.differs())

    def test_dimension_only_in_second(self):
        a = build_state_space()
        b = build_state_space(recovery="fast")
        diff = diff_state_spaces(a, b)
        self.assertEqual(diff.only_in_second, frozenset({"recovery"}))
        self.assertTrue(diff.differs())

    def test_dimension_absent_from_both_is_silent(self):
        # "domain" is never declared by either map — it must not appear
        # in any of the diff's four sets.
        a = build_state_space(time="now")
        b = build_state_space(time="now")
        diff = diff_state_spaces(a, b)
        for bucket in (
            diff.shared_equal, diff.shared_different,
            diff.only_in_first, diff.only_in_second,
        ):
            self.assertNotIn("domain", bucket)

    def test_mixed_realistic_comparison(self):
        a = build_state_space(time="near-term", threat="low", actor="internal")
        b = build_state_space(time="near-term", threat="high", recovery="slow")
        diff = diff_state_spaces(a, b)
        self.assertEqual(diff.shared_equal, frozenset({"time"}))
        self.assertEqual(diff.shared_different, frozenset({"threat"}))
        self.assertEqual(diff.only_in_first, frozenset({"actor"}))
        self.assertEqual(diff.only_in_second, frozenset({"recovery"}))
        self.assertTrue(diff.differs())

    def test_diff_has_no_score_or_ranking_attribute(self):
        # Structural guardrail against future scope creep: this module
        # must never grow a similarity score, distance metric, or rank.
        a = build_state_space(time="now")
        b = build_state_space(time="later")
        diff = diff_state_spaces(a, b)
        forbidden_names = {"score", "similarity", "rank", "distance", "weight"}
        actual_fields = set(diff.__dataclass_fields__.keys())
        self.assertEqual(actual_fields & forbidden_names, set())


class TestNoScenarioGenerationSurface(unittest.TestCase):
    """Structural guardrail: this module is a data/reasoning structure,
    not a scenario generator or predictor (that is MAGL_004's job, not
    this module's). No public callable should be named as a prediction/
    generation verb."""

    def test_no_prediction_or_generation_verbs_in_public_api(self):
        import foundation.state_space_mapper as mod

        forbidden_substrings = ("predict", "generate", "forecast", "simulate")
        for name in mod.__all__:
            lowered = name.lower()
            for bad in forbidden_substrings:
                self.assertNotIn(
                    bad, lowered,
                    f"public name '{name}' looks like a scenario-generation "
                    f"surface — that capability belongs to MAGL_004, not "
                    f"this module.",
                )


if __name__ == "__main__":
    unittest.main()
