"""The canonical value artifact — and the reason it kept going missing.

THREE LAYERS THAT MUST NEVER COLLAPSE

    RECEIPT          the epistemic source of truth. What was observed,
                     what died, what survived. Never bent to look better.

    GOLD BRICK       the full human-facing artifact derived from it.
                     Carries the proof, the work, TitanOS identity, and a
                     legitimate return path.

    DELIVERY PAYLOAD a rendering optimised for one specific door. A
                     maintainer's issue tracker wants a good bug report,
                     not a portfolio piece.

WHY THIS MODULE EXISTS

The first live delivery found a real defect, reproduced it, patched it,
tested it, killed a mutation, ran the contribution gate, and opened a
clean issue. Then it reported "brick delivered".

It had not delivered a brick. It had delivered a payload. No `Receipt`
object was ever constructed for that investigation; the "brick" was a
hand-written markdown file. The pipeline was bypassed and the word
"brick" was applied to whatever came out.

Nothing in the code prevented that, because nothing in the code knew
what a brick *was*. This module makes the brick a real object with a
real identity, so "we delivered the brick" becomes a checkable claim
rather than a description of a feeling.

THE ATTRIBUTION / PRESSURE DISTINCTION

`NO_FORCED_OFFER` had quietly started to mean "remove TitanOS from the
artifact". That is the wrong correction and it costs the business its
return path.

    identity + contact  ALWAYS present on a recipient-facing brick.
                        Doing thousands of dollars of work anonymously
                        is not integrity, it is just waste.

    commercial offer    gated, exactly as before. Withholding an offer
                        must never strip attribution.

Two different things. The gate governs the second, never the first.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from foundation.business_receipt import BusinessReceipt
from foundation.receipt import Receipt

__all__ = [
    "BRICK_CONTEXTS",
    "RECIPIENT_FACING_CONTEXTS",
    "CONTACT",
    "BrickIntegrityError",
    "GoldBrick",
    "DeliveryRecord",
    "materialise",
]

# Which door this rendering is for. The truth data never changes between
# contexts; only what may be shown does.
BRICK_CONTEXTS = (
    "INTERNAL",
    "RECIPIENT_REQUESTED",
    "PARTNERSHIP",
    "PUBLIC_CASE_STUDY",
    "THIRD_PARTY_CONTRIBUTION",
    "PRIVATE_SECURITY",
)

# Contexts where a human on the other side is reading it as a TitanOS
# artifact, so identity and a return path belong on it.
RECIPIENT_FACING_CONTEXTS = ("RECIPIENT_REQUESTED", "PARTNERSHIP",
                             "PUBLIC_CASE_STUDY")

# The only contact surfaces. Email is deliberately absent: it is not the
# default return path, and the conditions under which it becomes available
# live in contribution_gate.EMAIL_PERMITTED_WHEN.
CONTACT = {
    "web": "titanos.tech",
    "whatsapp": "+61 414 244 544",
}


class BrickIntegrityError(ValueError):
    """A brick claimed something its receipt does not support."""


@dataclass(frozen=True)
class GoldBrick:
    """A materialised artifact with a content-derived identity.

    `brick_id` is a hash of the receipt's serialised form, so editing the
    receipt after materialisation produces a brick that no longer verifies
    against it. A derived artifact that silently drifts from its source is
    the same class of failure as a receipt that bends for an offer.
    """

    brick_id: str
    receipt_id: str
    target: str
    revision: str
    context: str
    what_we_found: str
    why_it_matters: str
    impact_class: str            # e.g. LATENT, ACTIVE, NOT_MEASURED
    work_completed: tuple[str, ...]
    what_changed: str
    delivery_status: str
    platform_result: str
    human_value_status: str      # UNKNOWN until a human actually acts
    offer_permitted: bool
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def verify_integrity(self, receipt: Receipt) -> bool:
        """Does this brick still correspond to that receipt?"""
        return self.brick_id == _brick_id_for(receipt)

    def is_recipient_facing(self) -> bool:
        return self.context in RECIPIENT_FACING_CONTEXTS

    def render(self) -> str:
        """The full artifact.

        Identity and contact are unconditional on a recipient-facing
        brick. The commercial invitation is separate and gated.
        """
        lines = [
            "=" * 70,
            "                            TITANOS",
            "                         GOLD BRICK",
            "               VERIFIED INVESTIGATION ARTIFACT",
            "=" * 70,
            "",
            f"BRICK      {self.brick_id}",
            f"RECEIPT    {self.receipt_id}",
            f"TARGET     {self.target}",
            f"REVISION   {self.revision}",
            f"CONTEXT    {self.context}",
            "",
            "-" * 70,
            "01 // WHAT WE FOUND",
            "-" * 70,
            self.what_we_found,
            "",
            "-" * 70,
            "02 // WHY IT MATTERS",
            "-" * 70,
            f"IMPACT: {self.impact_class}",
            "",
            self.why_it_matters,
            "",
            "-" * 70,
            "03 // WHAT WE DID",
            "-" * 70,
        ]
        lines += [f"  [x] {step}" for step in self.work_completed]
        lines += [
            "",
            "-" * 70,
            "04 // WHAT CHANGED",
            "-" * 70,
            self.what_changed,
            "",
            "-" * 70,
            "05 // CURRENT STATUS",
            "-" * 70,
            f"DELIVERY          {self.delivery_status}",
            f"PLATFORM RESULT   {self.platform_result}",
            f"HUMAN READ        {self.human_value_status}",
            f"VALUE WITNESSED   {self.human_value_status}",
            "",
        ]
        if self.is_recipient_facing():
            lines += self._return_sigil()
        lines.append("=" * 70)
        return "\n".join(lines)

    def _return_sigil(self) -> list[str]:
        """Identity and return path. Not an offer, and not gated on one."""
        block = [
            "-" * 70,
            "                            TITANOS",
            "",
            "              MORE SIGNAL. MORE PROOF. MORE VALUE.",
            "",
            f"                        {CONTACT['web']}",
            f"                   WhatsApp {CONTACT['whatsapp']}",
            "",
            "This artifact stands on its own. If it was useful, that is the",
            "whole point -- there is nothing to buy to make it true.",
        ]
        if self.offer_permitted:
            block += [
                "",
                "If you want TitanOS on a deeper problem, get in touch. Where a",
                "standard engagement is not the right fit, a partnership",
                "arrangement may be possible.",
            ]
        block.append("")
        return block


@dataclass(frozen=True)
class DeliveryRecord:
    """What actually went out of the door, and what it was derived from.

    `full_brick_delivered` is DERIVED, never asserted. A payload sent to a
    maintainer is not the brick, however good the payload is.
    """

    source_brick_id: str
    receipt_id: str
    delivery_context: str
    payload_summary: str
    platform_result: str
    omissions_applied: tuple[str, ...] = ()
    return_sigil_included: bool = False

    def __post_init__(self) -> None:
        if not self.source_brick_id.strip():
            raise BrickIntegrityError(
                "a delivery must name the brick it was derived from; a payload "
                "with no source brick is the exact collapse this prevents")
        if self.delivery_context not in BRICK_CONTEXTS:
            raise BrickIntegrityError(
                f"unknown delivery context {self.delivery_context!r}")

    def full_brick_delivered(self) -> bool:
        """True only when the recipient actually received the whole artifact.

        A third-party contribution payload never qualifies: the maintainer
        got a bug report. Saying otherwise is how "brick delivered" got
        applied to an issue body.
        """
        if self.delivery_context == "THIRD_PARTY_CONTRIBUTION":
            return False
        return self.return_sigil_included and not self.omissions_applied


def _brick_id_for(receipt: Receipt) -> str:
    payload = json.dumps(receipt.to_dict(), sort_keys=True, default=str)
    return "GB-" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def materialise(
    receipt: Receipt,
    business: Optional[BusinessReceipt],
    *,
    target: str,
    revision: str,
    context: str,
    what_we_found: str,
    why_it_matters: str,
    impact_class: str,
    work_completed: tuple[str, ...],
    what_changed: str,
    delivery_status: str = "NOT_DELIVERED",
    platform_result: str = "NOT_ATTEMPTED",
    human_value_status: str = "UNKNOWN",
) -> GoldBrick:
    """Derive a brick from a receipt. The receipt is the only source.

    Refuses a claim the receipt does not carry: a brick describing a
    finding needs at least one PROVEN claim behind it, exactly as
    DEFECT_ADMITTED does. Prose is not evidence.
    """
    if context not in BRICK_CONTEXTS:
        raise BrickIntegrityError(f"unknown brick context {context!r}")
    if not receipt.proven_claims():
        raise BrickIntegrityError(
            "a gold brick requires at least one PROVEN claim; an artifact "
            "built only from inference is a hypothesis with a logo on it")
    if not what_we_found.strip():
        raise BrickIntegrityError("a brick must say what was found")

    # The offer gate, unchanged. It governs the commercial invitation only
    # -- never whether TitanOS is named.
    offer_permitted = bool(
        business is not None
        and receipt.offer_eligible()
        and business.available_next_action != "NO_REMEDIATION_OFFER_RECOMMENDED"
    )

    return GoldBrick(
        brick_id=_brick_id_for(receipt),
        receipt_id=receipt.receipt_id,
        target=target,
        revision=revision,
        context=context,
        what_we_found=what_we_found.strip(),
        why_it_matters=why_it_matters.strip(),
        impact_class=impact_class,
        work_completed=tuple(work_completed),
        what_changed=what_changed.strip(),
        delivery_status=delivery_status,
        platform_result=platform_result,
        human_value_status=human_value_status,
        offer_permitted=offer_permitted,
    )
