"""A delivery payload is not the brick, and an offer gate is not a gag.

These tests exist because of a real failure: the first live delivery
reported "brick delivered" when a maintainer had received a bug report
and no brick object existed at all.
"""

import unittest

from foundation.receipt import Claim, Receipt
from foundation.business_receipt import derive_business_receipt
from foundation.gold_brick import (
    BrickIntegrityError,
    DeliveryRecord,
    GoldBrick,
    materialise,
)


def _receipt(verdict="COVERAGE_GAP_RECORDED", beneficiary=None, claims=None):
    return Receipt(
        receipt_id="R-OPT-001", target="ethereum-optimism/optimism",
        question="does the suggested fix compile?", verdict=verdict,
        claims=claims or (Claim("the fix emits an unbound qualifier", "PROVEN",
                                "reproduced via RunWithSuggestedFixes"),),
        beneficiary=beneficiary)


def _brick(context="RECIPIENT_REQUESTED", receipt=None, business=None, **kw):
    r = receipt or _receipt()
    args = dict(
        target="ethereum-optimism/optimism", revision="2258ea57",
        context=context, what_we_found="The suggested fix emits `bigs.` "
        "regardless of how the package is actually imported.",
        why_it_matters="`--fix` would rewrite the file into code that does "
        "not compile.", impact_class="LATENT",
        work_completed=("reproduced", "patched", "tested", "mutation killed"),
        what_changed="Resolve the local import binding before emitting.")
    args.update(kw)
    return materialise(r, business, **args)


class TestThePayloadIsNotTheBrick(unittest.TestCase):
    def test_M1_a_delivery_must_name_the_brick_it_came_from(self):
        """A payload with no source brick is the exact collapse."""
        with self.assertRaises(BrickIntegrityError) as ctx:
            DeliveryRecord(source_brick_id="", receipt_id="R-1",
                           delivery_context="THIRD_PARTY_CONTRIBUTION",
                           payload_summary="issue", platform_result="ACCEPTED")
        self.assertIn("collapse", str(ctx.exception))

    def test_M2_a_third_party_payload_never_counts_as_full_brick_delivery(self):
        """The maintainer got a bug report. That is not the artifact."""
        d = DeliveryRecord(
            source_brick_id="GB-abc", receipt_id="R-1",
            delivery_context="THIRD_PARTY_CONTRIBUTION",
            payload_summary="github issue #22702",
            platform_result="ACCEPTED_BY_PLATFORM",
            omissions_applied=("return_sigil", "titanos_framing"),
            return_sigil_included=False)
        self.assertFalse(d.full_brick_delivered())

    def test_a_third_party_payload_cannot_be_upgraded_by_claiming_a_sigil(self):
        """Even asserting the sigil was included must not flip it."""
        d = DeliveryRecord(
            source_brick_id="GB-abc", receipt_id="R-1",
            delivery_context="THIRD_PARTY_CONTRIBUTION",
            payload_summary="issue", platform_result="ACCEPTED_BY_PLATFORM",
            return_sigil_included=True)
        self.assertFalse(d.full_brick_delivered())

    def test_a_complete_recipient_delivery_does_count(self):
        """Positive control: the distinction must not block real delivery."""
        d = DeliveryRecord(
            source_brick_id="GB-abc", receipt_id="R-1",
            delivery_context="RECIPIENT_REQUESTED",
            payload_summary="full artifact", platform_result="DELIVERED",
            return_sigil_included=True)
        self.assertTrue(d.full_brick_delivered())

    def test_omissions_prevent_a_full_brick_claim(self):
        d = DeliveryRecord(
            source_brick_id="GB-abc", receipt_id="R-1",
            delivery_context="RECIPIENT_REQUESTED",
            payload_summary="redacted", platform_result="DELIVERED",
            omissions_applied=("evidence_section",),
            return_sigil_included=True)
        self.assertFalse(d.full_brick_delivered())


class TestIdentityIsNotTheOffer(unittest.TestCase):
    def test_M3_a_recipient_facing_brick_always_carries_the_return_path(self):
        rendered = _brick().render()
        self.assertIn("titanos.tech", rendered)
        self.assertIn("+61 414 244 544", rendered)
        self.assertIn("TITANOS", rendered)

    def test_M5_withholding_the_offer_does_not_strip_attribution(self):
        """The correction. NO_FORCED_OFFER kills the sale, not the name."""
        r = _receipt(verdict="NO_DEFECT")          # not offer-eligible
        b = derive_business_receipt(r)
        brick = _brick(receipt=r, business=b)
        self.assertFalse(brick.offer_permitted)
        rendered = brick.render()
        self.assertIn("titanos.tech", rendered)
        self.assertIn("+61 414 244 544", rendered)
        # ...and no commercial invitation.
        self.assertNotIn("partnership", rendered.lower())

    def test_an_earned_offer_adds_the_invitation(self):
        r = _receipt(verdict="DEFECT_ADMITTED", beneficiary="the maintainer")
        brick = _brick(receipt=r, business=derive_business_receipt(r))
        self.assertTrue(brick.offer_permitted)
        self.assertIn("partnership", brick.render().lower())

    def test_M4_a_third_party_contribution_render_carries_no_sigil(self):
        """Someone else's issue tracker is not a distribution surface."""
        rendered = _brick(context="THIRD_PARTY_CONTRIBUTION").render()
        self.assertNotIn("titanos.tech", rendered)
        self.assertNotIn("+61 414 244 544", rendered)

    def test_the_invitation_is_never_pressure(self):
        r = _receipt(verdict="DEFECT_ADMITTED", beneficiary="the maintainer")
        rendered = _brick(receipt=r, business=derive_business_receipt(r)).render()
        for forbidden in ("buy now", "act now", "limited", "you owe",
                          "pay us", "click here to buy"):
            self.assertNotIn(forbidden, rendered.lower())

    def test_the_brick_states_the_artifact_stands_alone(self):
        self.assertIn("stands on its own", _brick().render())


class TestTheBrickCannotOutrunItsReceipt(unittest.TestCase):
    def test_a_brick_requires_a_proven_claim(self):
        r = _receipt(claims=(Claim("probably broken", "INFERENCE"),))
        with self.assertRaises(BrickIntegrityError) as ctx:
            _brick(receipt=r)
        self.assertIn("hypothesis with a logo on it", str(ctx.exception))

    def test_M6_editing_the_receipt_after_materialisation_is_detectable(self):
        """A derived artifact that silently drifts from its source is the
        same failure class as a receipt that bends for an offer."""
        r = _receipt()
        brick = _brick(receipt=r)
        self.assertTrue(brick.verify_integrity(r))

        edited = _receipt(claims=(
            Claim("something else entirely", "PROVEN", "different evidence"),))
        self.assertFalse(brick.verify_integrity(edited))

    def test_brick_id_is_derived_from_content_not_assigned(self):
        """Same receipt -> same id. Two receipts made moments apart are
        genuinely different receipts (recorded_at differs) and correctly
        yield different bricks, so the fixture must be shared."""
        r = _receipt()
        self.assertEqual(_brick(receipt=r).brick_id, _brick(receipt=r).brick_id)
        self.assertTrue(_brick(receipt=r).brick_id.startswith("GB-"))
        self.assertNotEqual(_brick().brick_id, _brick().brick_id)

    def test_human_value_defaults_to_unknown(self):
        """Platform acceptance is not a human outcome."""
        brick = _brick(platform_result="ACCEPTED_BY_PLATFORM")
        self.assertEqual(brick.human_value_status, "UNKNOWN")
        self.assertIn("UNKNOWN", brick.render())

    def test_an_unknown_context_is_refused(self):
        with self.assertRaises(BrickIntegrityError):
            _brick(context="WHEREVER_LOOKS_GOOD")

    def test_a_brick_must_say_what_was_found(self):
        with self.assertRaises(BrickIntegrityError):
            _brick(what_we_found="   ")


if __name__ == "__main__":
    unittest.main()
