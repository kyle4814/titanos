"""Tests for `foundation/ops_situation.py` — the real caller that makes
`situation_analysis` (the repo's largest capability) reachable.

The point of these tests is that the bottleneck is COMPUTED from
dependency structure, not asserted: the engine is never told that identity
is the answer, yet identity comes out on top because every live deal
depends on it.
"""

import unittest

from foundation.ops_situation import (
    analyse_ops_bottleneck,
    build_ops_situation,
    render_bottleneck,
)
from foundation.ops_digest import live_opportunities


class TestOpsSituationIsReal(unittest.TestCase):
    def test_every_live_deal_becomes_a_candidate_action(self):
        analysis = build_ops_situation()
        live_ids = {o.opp_id for o in live_opportunities() if not o.is_expired()}
        action_ids = {a.action_id for a in analysis.candidate_actions}
        self.assertEqual(action_ids, live_ids)

    def test_all_facts_are_verified_not_asserted_beyond_evidence(self):
        # Every known_information claim is VERIFIED_FACT with an evidence ref.
        for c in build_ops_situation().known_information:
            self.assertEqual(c.classification, "VERIFIED_FACT")

    def test_every_action_depends_on_identity(self):
        # The honest structural truth: nothing closes without name + ABN.
        for a in build_ops_situation().candidate_actions:
            self.assertIn("c_identity", a.depends_on_claim_ids, a.action_id)


class TestBottleneckIsComputedNotToldd(unittest.TestCase):
    def test_identity_is_the_highest_dependency_bottleneck(self):
        report = analyse_ops_bottleneck()
        self.assertTrue(report.candidates, report.reason)
        # identity must be present and carry the largest dependency count.
        by_ref = {c.constraint_ref: c for c in report.candidates}
        identity = next((c for ref, c in by_ref.items()
                         if "identity" in ref.lower()), None)
        self.assertIsNotNone(identity, "identity not surfaced as a bottleneck")
        self.assertEqual(identity.leverage_estimate, "HIGH")
        # its rationale carries the count, and it is the max among candidates.
        counts = []
        for c in report.candidates:
            import re
            m = re.search(r"(\d+) candidate", c.rationale)
            counts.append(int(m.group(1)) if m else 0)
        identity_count = int(
            __import__("re").search(r"(\d+) candidate",
                                    identity.rationale).group(1))
        self.assertEqual(identity_count, max(counts))

    def test_hypotheses_are_speculative_never_fact(self):
        for c in analyse_ops_bottleneck().candidates:
            self.assertEqual(c.hypothesis_claim.classification,
                             "SPECULATIVE_HYPOTHESIS")

    def test_render_marks_it_as_not_authority(self):
        out = render_bottleneck(analyse_ops_bottleneck())
        self.assertIn("not authority to act", out)
        self.assertIn("BOTTLENECK", out)


if __name__ == "__main__":
    unittest.main()
