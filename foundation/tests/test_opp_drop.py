"""Tests for `foundation/opp_drop.py` — the desktop opportunity package.

Pure file assembly, no network. The load-bearing properties: START_HERE is
always written and leads with opportunities-to-apply-for (Kyle applies; no
cold-call kit), one pack per live opportunity lands in TENDERS/, and the
package is honest about streams not yet built."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from foundation.opp_drop import build_opp_drop, OPP_ROOT_NAME
from foundation.team_targets import live_team_targets

NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)


class TestOppDrop(unittest.TestCase):
    def _build(self):
        d = tempfile.mkdtemp()
        written = build_opp_drop(Path(d), now=NOW)
        return Path(d) / OPP_ROOT_NAME, written

    def test_start_here_always_written(self):
        root, _ = self._build()
        self.assertTrue((root / "START_HERE.md").is_file())

    def test_one_pack_per_live_opportunity(self):
        root, _ = self._build()
        n = len(live_team_targets(NOW))
        packs = list((root / "TENDERS").glob("*.md"))
        self.assertEqual(len(packs), n)

    def test_start_here_leads_with_opportunities_and_actions(self):
        root, _ = self._build()
        text = (root / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("OPPORTUNITIES TO APPLY FOR", text)
        self.assertIn("ACTION", text)
        # a real opportunity and its pack pointer appear
        self.assertIn("TENDERS/", text)

    def test_no_cold_call_kit(self):
        # Kyle has his own leads/offer — the folder must NOT push a cold-call kit.
        root, _ = self._build()
        self.assertFalse((root / "SELL_TITANOS").exists())
        text = (root / "START_HERE.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("cold-call", text)
        self.assertNotIn("cold call", text)

    def test_honest_about_unbuilt_streams(self):
        root, _ = self._build()
        text = (root / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("NOT YET BUILT", text)

    def test_refresh_is_idempotent(self):
        d = tempfile.mkdtemp()
        build_opp_drop(Path(d), now=NOW)
        build_opp_drop(Path(d), now=NOW)
        root = Path(d) / OPP_ROOT_NAME
        packs = list((root / "TENDERS").glob("*.md"))
        self.assertEqual(len(packs), len(live_team_targets(NOW)))


if __name__ == "__main__":
    unittest.main()
