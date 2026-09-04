"""Tests for `foundation/team_targets.py` — the credential-walled contracts
a team can win. No fabrication: every target names concrete requirements
quoted from a source, and dated targets sort by real deadline."""

import unittest
from datetime import datetime, timezone

from foundation.team_targets import (
    TEAM_TARGETS,
    TeamTarget,
    TeamTargetError,
    live_team_targets,
    render_team_targets_md,
)


class TestTeamTargets(unittest.TestCase):
    def test_registry_is_substantial(self):
        self.assertGreaterEqual(len(TEAM_TARGETS), 12)

    def test_every_target_lists_requirements_and_a_source(self):
        for t in TEAM_TARGETS:
            self.assertTrue(t.requirements, t.target_id)
            self.assertTrue(t.source_ref.strip(), t.target_id)

    def test_a_target_with_no_requirements_is_refused(self):
        with self.assertRaises(TeamTargetError):
            TeamTarget("X", "t", "€1", "Standing", "http://x", "what", (), "src")

    def test_dated_targets_sort_soonest_first(self):
        now = datetime(2026, 9, 4, tzinfo=timezone.utc)
        dated = [t for t in live_team_targets(now)
                 if t.deadline_date() is not None]
        ords = [t.deadline_date().toordinal() for t in dated]
        self.assertEqual(ords, sorted(ords))

    def test_expired_targets_drop_out(self):
        future = datetime(2031, 1, 1, tzinfo=timezone.utc)  # past every deadline
        live = live_team_targets(future)
        # only the standing/rolling ones (no parseable deadline) survive
        self.assertTrue(all(t.deadline_date() is None for t in live))

    def test_render_leads_with_time_critical(self):
        md = render_team_targets_md(datetime(2026, 9, 4, tzinfo=timezone.utc))
        self.assertIn("TEAM TARGETS", md)
        self.assertIn("Time-critical", md)
        self.assertIn("Your team must bring", md)
        # a real dated tender and a real requirement appear
        self.assertIn("Fáilte Ireland", md)
        self.assertIn("insurance", md.lower())


if __name__ == "__main__":
    unittest.main()
