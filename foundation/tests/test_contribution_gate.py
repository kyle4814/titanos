"""A contribution surface is not a delivery channel.

D1-D19. The failure being defended against is subtle: every one of these
gates can be argued past by someone who wants the notification to fire.
"""

import unittest

from foundation.contribution_gate import (
    DELIVERY_DECISIONS,
    EMAIL_PERMITTED_WHEN,
    PLATFORM_RESULTS,
    ContributionTarget,
    admit_contribution,
    email_is_permitted,
    render_return_sigil,
)


def _target(**kw):
    base = dict(repository="acme/widget", is_public=True,
                accepts_pull_requests=True, accepts_issues=True,
                contributing_policy_read=True)
    base.update(kw)
    return ContributionTarget(**base)


def _admit(target=None, qualified=True, sensitive=False, value=True):
    return admit_contribution(target or _target(), brick_is_qualified=qualified,
                              security_sensitive=sensitive,
                              adds_reviewable_value=value)


class TestAdmission(unittest.TestCase):
    def test_D1_a_public_repo_with_a_qualified_brick_is_admitted(self):
        d = _admit()
        self.assertTrue(d.permits_delivery())
        self.assertIn(d.decision, ("ADMIT_ISSUE", "ADMIT_PR"))

    def test_the_least_intrusive_door_is_chosen_first(self):
        """An issue asks. A pull request presumes."""
        self.assertEqual(_admit().decision, "ADMIT_ISSUE")

    def test_D2_an_explicit_policy_prohibition_binds(self):
        t = _target(accepts_issues=False,
                    policy_forbids_mechanisms=("ADMIT_PR",))
        self.assertEqual(_admit(t).decision, "WITHHOLD")

    def test_a_forbidden_issue_path_falls_back_to_pr_not_to_withhold(self):
        t = _target(accepts_issues=False)
        self.assertEqual(_admit(t).decision, "ADMIT_PR")

    def test_D3_a_security_finding_takes_the_private_route(self):
        """Publishing an unremediated vulnerability into a public issue
        harms the people it is addressed to."""
        t = _target(has_security_policy=True,
                    security_contact="security@acme.example")
        d = _admit(t, sensitive=True)
        self.assertEqual(d.decision, "ADMIT_PRIVATE_SECURITY_CHANNEL")
        self.assertEqual(d.mechanism, "security@acme.example")

    def test_D3b_a_security_finding_with_no_private_route_escalates(self):
        d = _admit(sensitive=True)
        self.assertEqual(d.decision, "HUMAN_REVIEW_REQUIRED")
        self.assertFalse(d.permits_delivery())

    def test_a_security_finding_never_silently_takes_a_public_door(self):
        for t in (_target(), _target(accepts_issues=False),
                  _target(has_security_policy=True)):   # policy but no contact
            self.assertNotIn(_admit(t, sensitive=True).decision,
                             ("ADMIT_ISSUE", "ADMIT_PR"))

    def test_D4_unread_contribution_guidance_escalates(self):
        """An unread policy is not a permissive one."""
        d = _admit(_target(contributing_policy_read=False))
        self.assertEqual(d.decision, "HUMAN_REVIEW_REQUIRED")

    def test_a_private_repo_has_no_public_contribution_path(self):
        self.assertEqual(_admit(_target(is_public=False)).decision, "WITHHOLD")

    def test_an_unqualified_brick_has_no_door_at_all(self):
        """An open issue tracker does not make a failed finding deliverable."""
        d = _admit(qualified=False)
        self.assertEqual(d.decision, "WITHHOLD")
        self.assertIn("receipt gates", d.reason)

    def test_repository_noise_is_refused(self):
        d = _admit(value=False)
        self.assertEqual(d.decision, "WITHHOLD")
        self.assertIn("not a delivery channel", d.reason)

    def test_defaults_are_cautious_so_omission_cannot_look_permissive(self):
        t = ContributionTarget(repository="acme/widget")
        self.assertFalse(t.is_public)
        self.assertIsNone(t.accepts_pull_requests)
        self.assertFalse(t.contributing_policy_read)
        self.assertEqual(_admit(t).decision, "WITHHOLD")

    def test_every_decision_is_in_the_declared_vocabulary(self):
        for t in (_target(), _target(is_public=False),
                  _target(contributing_policy_read=False)):
            for sensitive in (True, False):
                self.assertIn(_admit(t, sensitive=sensitive).decision,
                              DELIVERY_DECISIONS)


class TestEmailIsNotTheDefault(unittest.TestCase):
    def test_D10_no_relationship_means_no_email(self):
        self.assertFalse(email_is_permitted("NONE"))
        self.assertFalse(email_is_permitted(""))

    def test_having_an_address_is_not_a_permitting_condition(self):
        self.assertFalse(email_is_permitted("we_have_their_address"))
        self.assertFalse(email_is_permitted("cold_lead"))

    def test_D11_an_explicit_request_or_partnership_permits_email(self):
        self.assertTrue(email_is_permitted("EXPLICIT_REQUEST"))
        self.assertTrue(email_is_permitted("ACTIVE_PARTNERSHIP"))

    def test_a_disclosure_policy_requiring_email_permits_it(self):
        self.assertTrue(email_is_permitted("NONE", policy_requires_email=True))

    def test_the_permitting_conditions_are_enumerated_not_open(self):
        self.assertEqual(len(EMAIL_PERMITTED_WHEN), 4)


class TestForbiddenFallbacks(unittest.TestCase):
    def test_D13_withhold_offers_no_alternative_mechanism(self):
        """'We could not find a door' must not become 'so we used another
        channel'. The decision carries no fallback field to abuse."""
        d = _admit(_target(is_public=False))
        self.assertEqual(d.decision, "WITHHOLD")
        self.assertIsNone(d.mechanism)
        self.assertFalse(d.permits_delivery())

    def test_D14_withhold_does_not_imply_email_permission(self):
        self.assertEqual(_admit(_target(is_public=False)).decision, "WITHHOLD")
        self.assertFalse(email_is_permitted("NONE"))

    def test_human_review_is_not_a_permission(self):
        self.assertFalse(_admit(sensitive=True).permits_delivery())


class TestPlatformStatesStaySeparate(unittest.TestCase):
    def test_D15_no_platform_result_means_a_human_saw_anything(self):
        for forbidden in ("DELIVERED_TO_HUMAN", "READ", "SEEN",
                          "ACKNOWLEDGED", "FIXED", "PAID"):
            self.assertNotIn(forbidden, PLATFORM_RESULTS)

    def test_acceptance_by_platform_is_its_own_state(self):
        self.assertIn("ACCEPTED_BY_PLATFORM", PLATFORM_RESULTS)
        self.assertIn("AMBIGUOUS", PLATFORM_RESULTS)


class TestTheReturnSigil(unittest.TestCase):
    def test_D9_it_carries_the_two_return_surfaces(self):
        sigil = render_return_sigil()
        self.assertIn("titanos.tech", sigil)
        self.assertIn("+61 414 244 544", sigil)
        self.assertIn("WhatsApp", sigil)

    def test_it_holds_no_evidence_hostage_and_applies_no_pressure(self):
        sigil = render_return_sigil().lower()
        for forbidden in ("buy now", "limited time", "pay $", "unlock",
                          "act now", "this isn't a sales pitch", "guarantee"):
            self.assertNotIn(forbidden, sigil)

    def test_D18_it_does_not_claim_a_partnership_is_approved(self):
        """'Arrangements are possible' invites a conversation. Anything
        stronger would promise something the system cannot keep."""
        sigil = render_return_sigil().lower()
        self.assertIn("possible", sigil)
        for overclaim in ("you qualify", "you are approved", "guaranteed",
                          "we will partner"):
            self.assertNotIn(overclaim, sigil)

    def test_D19_it_states_the_artifact_stands_alone(self):
        self.assertIn("STANDS ON ITS OWN", render_return_sigil())

    def test_it_carries_no_price(self):
        import re
        self.assertIsNone(re.search(r"[$£€]\s*\d", render_return_sigil()))

    def test_it_is_not_gated_on_an_offer(self):
        """The sigil makes no commercial claim; it names where the door is.
        Withholding it would hide who made the artifact."""
        self.assertTrue(render_return_sigil().strip())


if __name__ == "__main__":
    unittest.main()
