"""Tests for `foundation/portfolio_bundle.py`.

Offline. Verifies the bundle assembles the generated pieces (which never
depend on external files) and that START_HERE reflects the real roster.
Document copies are best-effort, so the assertions target only what the
module itself produces.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from foundation.portfolio_bundle import build_portfolio_bundle
from foundation.ops_digest import live_opportunities, ruled_out_count


class TestPortfolioBundle(unittest.TestCase):
    def test_bundle_produces_the_core_deliverables(self):
        with TemporaryDirectory() as d:
            dest = Path(d) / "PORTFOLIO"
            written = build_portfolio_bundle(dest)
            self.assertTrue((dest / "START_HERE.md").is_file())
            for rel in ("01_PORTFOLIO/portfolio_full.md",
                        "01_PORTFOLIO/close_pack.md",
                        "01_PORTFOLIO/bottleneck_analysis.txt",
                        "02_READY_TO_SEND/nsw_referee_email.txt",
                        "02_READY_TO_SEND/gni_round_question.txt"):
                self.assertTrue((dest / rel).is_file(), rel)
            self.assertGreaterEqual(len(written), 6)

    def test_start_here_reflects_the_real_counts(self):
        with TemporaryDirectory() as d:
            dest = Path(d) / "P"
            build_portfolio_bundle(dest)
            text = (dest / "START_HERE.md").read_text(encoding="utf-8")
        self.assertIn(f"{len(live_opportunities())} live", text)
        self.assertIn(f"{ruled_out_count()} ruled out", text)

    def test_drafts_contain_bracketed_placeholders_not_invented_data(self):
        with TemporaryDirectory() as d:
            dest = Path(d) / "P"
            build_portfolio_bundle(dest)
            nsw = (dest / "02_READY_TO_SEND" / "nsw_referee_email.txt").read_text()
        self.assertIn("[YOUR", nsw.upper())
        # no concrete 11-digit ABN
        import re
        self.assertNotRegex(nsw, r"\b\d{11}\b")


if __name__ == "__main__":
    unittest.main()
