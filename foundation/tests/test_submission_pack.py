"""Tests for `foundation/submission_pack.py` — the ready-to-file pack builder.

The load-bearing properties: nothing is invented (unsupplied facts are UNKNOWN
and surface under MISSING), and the pack always stops at the human Submit."""

import unittest

from foundation.submission_pack import (
    TeamProfile,
    build_submission_pack,
    render_pack_md,
    portal_of,
    UNKNOWN,
)
from foundation.team_targets import TEAM_TARGETS


def _target(tid):
    return next(t for t in TEAM_TARGETS if t.target_id == tid)


class TestPortalRouting(unittest.TestCase):
    def test_irish_target_routes_to_etenders(self):
        self.assertEqual(portal_of(_target("IE_HSA")), "eTenders (IE)")

    def test_ted_target_routes_to_buyer_portal(self):
        self.assertEqual(portal_of(_target("DE_UKF")), "TED / buyer portal (EU)")

    def test_uk_target_routes_to_find_a_tender(self):
        self.assertEqual(portal_of(_target("UK_MDR")),
                         "Find a Tender / eSourcing (UK)")


class TestHonesty(unittest.TestCase):
    def test_empty_profile_marks_everything_unknown_and_missing(self):
        pack = build_submission_pack(_target("IE_HSA"), TeamProfile())
        # every ESPD identity answer is UNKNOWN
        self.assertTrue(all(a == UNKNOWN for _, a in pack.espd_answers))
        # and each is listed under MISSING — never silently absent
        self.assertEqual(len(pack.missing), len(pack.espd_answers))
        self.assertFalse(pack.ready)

    def test_supplied_facts_are_used_not_reinvented(self):
        prof = TeamProfile(
            legal_name="Acme Cyber Ltd",
            registration="IE1234567",
            contact_name="A. Operator",
            contact_email="ops@acme.example",
            address="1 Test St, Cairns",
            annual_turnover_eur=2_000_000,
            insurance_cover={"professional indemnity": 5_000_000},
            references=("SOC for a health body, 2024",),
            certifications=("ISO 27001",),
        )
        pack = build_submission_pack(_target("IE_HSA"), prof)
        answers = dict(pack.espd_answers)
        self.assertEqual(answers["Legal name of economic operator"], "Acme Cyber Ltd")
        self.assertIn("ISO 27001", answers["Certifications"])
        self.assertEqual(pack.missing, ())      # all standard fields supplied
        self.assertTrue(pack.ready)

    def test_partial_profile_lists_only_the_real_gaps(self):
        prof = TeamProfile(legal_name="Acme Cyber Ltd")
        pack = build_submission_pack(_target("IE_HSA"), prof)
        self.assertNotIn("Legal name of economic operator", pack.missing)
        self.assertIn("Annual turnover (EUR)", pack.missing)


class TestSubmitAlwaysHuman(unittest.TestCase):
    def test_final_step_is_a_human_submit_on_every_portal(self):
        for tid in ("IE_HSA", "DE_UKF", "UK_MDR"):
            pack = build_submission_pack(_target(tid), TeamProfile())
            self.assertIn("SUBMIT", pack.steps[-1].upper())
            self.assertIn("human", pack.steps[-1].lower())

    def test_render_states_it_stops_at_submit(self):
        md = render_pack_md(build_submission_pack(_target("IE_HSA"), TeamProfile()))
        self.assertIn("stops at the Submit button", md)
        self.assertIn("MISSING", md)
        # the upload checklist carries the target's real quoted requirements
        self.assertTrue(any("[ ]" in line for line in md.splitlines()))


if __name__ == "__main__":
    unittest.main()
