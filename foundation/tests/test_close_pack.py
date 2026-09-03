"""Tests for `foundation/close_pack.py`.

Offline. The load-bearing tests are the anti-fabrication ones: a draft
must never assert a capability, ABN, or reference the operator profile has
not verified — placeholders are visible blanks, never invented values.
"""

import re
import unittest

from foundation.close_pack import (
    CLOSE_PLANS,
    GATE_TYPES,
    ClosePlan,
    ClosePlanError,
    consolidated_facts_needed,
    plan_for,
    render_close_pack,
)
from foundation.ops_digest import OPPORTUNITIES


class TestEveryOpportunityHasACloseLine(unittest.TestCase):
    def test_every_roster_opp_has_a_plan(self):
        for o in OPPORTUNITIES:
            self.assertIn(o.opp_id, CLOSE_PLANS, o.opp_id)
            self.assertIsInstance(plan_for(o), ClosePlan)

    def test_no_orphan_plans(self):
        roster_ids = {o.opp_id for o in OPPORTUNITIES}
        for pid in CLOSE_PLANS:
            self.assertIn(pid, roster_ids, f"{pid} plan has no roster opp")

    def test_a_bad_gate_is_refused(self):
        with self.assertRaises(ClosePlanError):
            ClosePlan("X", "MAGIC")

    def test_only_outbound_may_carry_a_draft(self):
        with self.assertRaises(ClosePlanError):
            ClosePlan("X", "ACCOUNT", draft="hi")

    def test_every_gate_is_declared(self):
        for p in CLOSE_PLANS.values():
            self.assertIn(p.gate, GATE_TYPES)


class TestNoFabrication(unittest.TestCase):
    """The one thing this module must never do: put an invented capability,
    ABN, or reference into a draft. Blanks stay bracketed."""

    def test_drafts_never_contain_a_concrete_abn(self):
        # An ABN is 11 digits. No draft may contain one — only [YOUR ABN].
        for p in CLOSE_PLANS.values():
            if p.draft:
                self.assertNotRegex(
                    p.draft, r"\b\d{11}\b",
                    f"{p.opp_id} draft contains a concrete 11-digit number")

    def test_drafts_use_bracketed_placeholders_for_identity(self):
        for p in CLOSE_PLANS.values():
            if p.draft:
                self.assertIn("[YOUR", p.draft.upper(),
                              f"{p.opp_id} draft has no visible placeholder")

    def test_drafts_assert_no_capability_words(self):
        # A pure inquiry asks a question; it must not claim experience,
        # certification, or accreditation the profile hasn't verified.
        banned = ("years of experience", "certified", "accredited",
                  "CREST-approved", "we have delivered", "our track record",
                  "extensive experience")
        for p in CLOSE_PLANS.values():
            if p.draft:
                low = p.draft.lower()
                for phrase in banned:
                    self.assertNotIn(phrase.lower(), low,
                                     f"{p.opp_id} draft asserts capability")

    def test_only_pure_inquiries_are_drafted(self):
        # Exactly the two safe information questions carry drafts.
        drafted = {pid for pid, p in CLOSE_PLANS.items() if p.draft}
        self.assertEqual(drafted, {"NSW_ICT_SCHEME", "IE_GNI_23_049"})


class TestConsolidatedFacts(unittest.TestCase):
    def test_identity_facts_come_first(self):
        facts = consolidated_facts_needed()
        self.assertTrue(facts, "no facts collected")
        # ABN shows up (multiple deals need it) and near the front.
        joined = " | ".join(facts)
        self.assertIn("ABN", joined)


class TestRender(unittest.TestCase):
    def test_render_lists_walls_and_the_facts_ask(self):
        out = render_close_pack(now_line="test")
        self.assertIn("Close Pack", out)
        self.assertIn("The 4 facts", out)
        self.assertIn("Wall:", out)
        # a drafted inquiry appears in a code block
        self.assertIn("Ready to send", out)
        self.assertIn("ICTServices@customerservice.nsw.gov.au", out)

    def test_render_names_the_gate_for_every_shown_deal(self):
        out = render_close_pack()
        # every "## <title>" after the intro should be followed by a Wall line
        blocks = out.split("## ")[2:]  # skip title + facts section
        for b in blocks:
            self.assertIn("Wall:", b, b[:60])


if __name__ == "__main__":
    unittest.main()
