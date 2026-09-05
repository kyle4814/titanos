"""Tests for `foundation/opp_drop.py` — the desktop opportunity package.

No network: include_sample=False skips the live-DNS sample. The load-bearing
properties: a START_HERE and the cold-call kit are always written, one pack per
live tender lands in TENDERS/, and the package is real (no invented streams)."""

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
        written = build_opp_drop(Path(d), now=NOW, include_sample=False)
        return Path(d) / OPP_ROOT_NAME, written

    def test_start_here_and_cold_call_kit_always_written(self):
        root, _ = self._build()
        self.assertTrue((root / "START_HERE.md").is_file())
        self.assertTrue((root / "SELL_TITANOS" / "COLD_CALL_KIT.md").is_file())

    def test_one_pack_per_live_tender(self):
        root, _ = self._build()
        n = len(live_team_targets(NOW))
        packs = list((root / "TENDERS").glob("*.md"))
        self.assertEqual(len(packs), n)

    def test_start_here_leads_with_selling_titanos(self):
        root, _ = self._build()
        text = (root / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("sell titanos.tech", text.lower())
        self.assertIn("security-report --domain", text)

    def test_cold_call_kit_has_the_command_and_stays_honest(self):
        root, _ = self._build()
        kit = (root / "SELL_TITANOS" / "COLD_CALL_KIT.md").read_text(encoding="utf-8")
        self.assertIn("security-report --domain", kit)
        # public-data honesty: never claim to have hacked/scanned their systems
        self.assertIn("PUBLIC", kit)
        self.assertIn("never say you", kit.lower())

    def test_no_sample_when_disabled(self):
        root, _ = self._build()
        self.assertFalse((root / "SELL_TITANOS" / "sample_report.md").is_file())

    def test_honest_about_unbuilt_streams(self):
        root, _ = self._build()
        text = (root / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn("NOT YET BUILT", text)

    def test_refresh_is_idempotent(self):
        # running twice into the same dest overwrites, does not duplicate
        d = tempfile.mkdtemp()
        build_opp_drop(Path(d), now=NOW, include_sample=False)
        build_opp_drop(Path(d), now=NOW, include_sample=False)
        root = Path(d) / OPP_ROOT_NAME
        packs = list((root / "TENDERS").glob("*.md"))
        self.assertEqual(len(packs), len(live_team_targets(NOW)))


if __name__ == "__main__":
    unittest.main()
