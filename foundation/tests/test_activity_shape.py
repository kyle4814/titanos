"""A dimension that agrees about everything ranks nothing.

These tests exist because the previous unit reduced eighteen commit reads
to one bit each and every target answered the same way.
"""

import unittest
from datetime import datetime, timedelta, timezone

from foundation.activity_shape import (
    ActivityShape,
    UNKNOWN_SHAPE,
    shape_of,
    spread,
)


def _now():
    return datetime.now(timezone.utc)


def _commit(days_ago=1.0, login="alice", kind="User", email="a@x.invalid",
            sha="abc"):
    return {"sha": sha,
            "authored_at": (_now() - timedelta(days=days_ago)).isoformat(),
            "author_login": login, "author_type": kind, "author_email": email}


class TestUnmeasuredIsNotZero(unittest.TestCase):
    """The lesson this project keeps having to defend."""

    def test_M_an_empty_window_is_not_a_repository_with_no_activity(self):
        s = shape_of([])
        self.assertFalse(s.observed)
        self.assertIsNone(s.latest_age_days)
        self.assertIsNone(s.span_days)
        self.assertIn("no commits", s.note)

    def test_an_unmeasured_shape_reports_no_quantities_at_all(self):
        self.assertFalse(UNKNOWN_SHAPE.observed)
        self.assertIsNone(UNKNOWN_SHAPE.span_days)
        self.assertIn("unmeasured", UNKNOWN_SHAPE.show_the_measurements())

    def test_unparseable_times_do_not_become_age_zero(self):
        s = shape_of([{"authored_at": "whenever", "author_login": "a"}])
        self.assertTrue(s.observed)
        self.assertIsNone(s.latest_age_days)
        self.assertIn("no parseable commit times", s.note)

    def test_a_single_commit_has_no_span(self):
        """Span needs two points. One commit is not a zero-day span."""
        s = shape_of([_commit()])
        self.assertIsNotNone(s.latest_age_days)
        self.assertIsNone(s.span_days)


class TestTheThreeFactsStaySeparate(unittest.TestCase):
    def test_recency_sustain_and_hands_are_three_measurements(self):
        s = shape_of([_commit(0.1, "alice"), _commit(3.0, "bob")], window=10)
        self.assertAlmostEqual(s.latest_age_days, 0.1, places=1)
        self.assertAlmostEqual(s.span_days, 2.9, places=1)
        self.assertEqual(s.hands(), 2)

    def test_there_is_no_single_number(self):
        s = shape_of([_commit()])
        surface = {f for f in dir(s) if not f.startswith("_")}
        for banned in ("score", "rating", "power", "value", "rank", "index"):
            self.assertNotIn(banned, surface)

    def test_the_measurements_carry_their_units(self):
        text = shape_of([_commit(0.5), _commit(2.0, "bob")]).show_the_measurements()
        self.assertIn("days ago", text)
        self.assertIn("days", text)
        self.assertIn("human authors", text)

    def test_span_is_named_as_a_property_of_the_window(self):
        """A ten-commit window sees a busy repo over hours and a quiet one
        over years; the number is about the window, not the lifetime."""
        s = shape_of([_commit(0.01), _commit(0.02)], window=10)
        self.assertEqual(s.window, 10)
        self.assertIn("window", s.show_the_measurements())


class TestBotsAreNotHands(unittest.TestCase):
    def test_M_a_bot_is_not_counted_as_a_collaborator(self):
        """A repository kept alive by dependabot is not a repository with
        people moving in it."""
        s = shape_of([_commit(1, "dependabot[bot]", "Bot"),
                      _commit(2, "renovate[bot]", "Bot"),
                      _commit(3, "alice", "User")])
        self.assertEqual(s.hands(), 1)
        self.assertEqual(s.bot_authors, 2)

    def test_a_bot_without_the_type_flag_is_still_caught(self):
        s = shape_of([_commit(1, "github-actions", ""),
                      _commit(2, "alice", "User")])
        self.assertEqual(s.hands(), 1)

    def test_bots_are_reported_not_hidden(self):
        s = shape_of([_commit(1, "dependabot[bot]", "Bot")])
        self.assertEqual(s.bot_authors, 1)
        self.assertIn("bot authors   1", s.show_the_measurements())

    def test_an_unattributed_commit_is_not_an_author(self):
        s = shape_of([{"authored_at": _commit()["authored_at"],
                       "author_login": "", "author_email": ""}])
        self.assertEqual(s.hands(), 0)


class TestBurstIsAShapeNotAVerdict(unittest.TestCase):
    def test_a_compressed_window_is_a_burst(self):
        s = shape_of([_commit(d) for d in (0.01, 0.02, 0.05, 0.1, 0.2)])
        self.assertTrue(s.is_burst())

    def test_the_same_commits_spread_out_are_not(self):
        s = shape_of([_commit(d) for d in (1, 20, 60, 200, 400)])
        self.assertFalse(s.is_burst())

    def test_M_a_burst_claims_no_urgency_and_no_demand(self):
        """Descriptive only. Many commits is not someone asking."""
        s = shape_of([_commit(d) for d in (0.01, 0.02, 0.05, 0.1, 0.2)])
        self.assertIsInstance(s.is_burst(), bool)
        text = s.show_the_measurements().lower()
        for banned in ("urgent", "demand", "hot", "valuable", "opportunity"):
            self.assertNotIn(banned, text)


class TestSpreadAnswersTheDiscriminationQuestion(unittest.TestCase):
    def test_M_a_dimension_that_agrees_about_everything_has_no_spread(self):
        """The exact failure the last unit measured: 18/18 fresh."""
        same = [shape_of([_commit(0.5, "a"), _commit(0.6, "a")])
                for _ in range(5)]
        self.assertLess(spread(same, "span_days"), 0.01)

    def test_a_dimension_that_varies_reports_it(self):
        varied = [shape_of([_commit(0.1), _commit(0.2)]),
                  shape_of([_commit(1), _commit(300)])]
        self.assertGreater(spread(varied, "span_days"), 100)

    def test_spread_of_one_observation_is_undefined_not_zero(self):
        self.assertIsNone(spread([shape_of([_commit()])], "latest_age_days"))

    def test_unmeasured_shapes_are_excluded_rather_than_counted_as_zero(self):
        mixed = [shape_of([]), shape_of([_commit(1), _commit(2)])]
        self.assertIsNone(spread(mixed, "span_days"))


if __name__ == "__main__":
    unittest.main()
