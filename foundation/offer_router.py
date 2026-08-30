"""Receipt state -> exactly one terminal commercial route.

THE DISTINCTION THIS MODULE EXISTS TO HOLD

    epistemic eligibility  !=  commercial availability

A receipt can honestly permit a next step that the business has no way to
sell. The tempting resolution is to invent a product so the state looks
complete. This module makes that unnecessary by giving the gap its own
terminal route, `UNSUPPORTED_OFFER_PATH`, so "we could help and have
nothing to sell you" is a first-class, sayable outcome.

WHY THE REGISTRY IS INJECTED

The routing logic is here; the catalogue is not. Callers pass a registry
describing what genuinely exists. That keeps route ids, links, prices and
product identifiers out of the evidence layer entirely -- this module
never sees a price and has nowhere to put one. It also means the
catalogue can be wrong without the routing rules being wrong.

WHY A GENERIC CTA IS TREATED AS AN OFFER

"Book a call", "get in touch", "free audit" are offers when their purpose
is to sell the remediation. A firewall that blocks a price panel and
waves through a booking link for the same remediation has not blocked
anything. Registry entries therefore declare `sells_remediation`, and a
route that sells remediation is subject to the same gate as a price.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from foundation.business_receipt import BusinessReceipt
from foundation.receipt import Receipt

__all__ = [
    "TERMINAL_ROUTES",
    "FULFILMENT_MODES",
    "OfferCapability",
    "RoutingDecision",
    "route_offer",
]

TERMINAL_ROUTES = (
    "EXISTING_SUPPORTED_OFFER",
    "HUMAN_REVIEW_REQUIRED",
    "NO_FORCED_OFFER",
    "UNSUPPORTED_OFFER_PATH",
)

FULFILMENT_MODES = ("AUTOMATED", "MANUAL_BY_OWNER")

# The receipt actions this router understands. Kept as a tuple so an
# unrecognised action escalates rather than silently selecting a default.
_KNOWN_ACTIONS = (
    "NO_REMEDIATION_OFFER_RECOMMENDED",
    "REQUEST_DEEPER_INVESTIGATION",
    "REQUEST_REMEDIATION",
    "REQUEST_CONTINUOUS_VERIFICATION",
)


@dataclass(frozen=True)
class OfferCapability:
    """One thing the business can actually do today.

    `reference` is a route, link id, or process name -- never a price. A
    capability that cannot name how it is fulfilled is not a capability.
    """

    satisfies: str            # one of _KNOWN_ACTIONS
    reference: str            # e.g. "POST /checkout/monitor"
    fulfilment: str           # AUTOMATED | MANUAL_BY_OWNER
    sells_remediation: bool   # true => subject to the offer gate
    human_action_required: bool

    def __post_init__(self) -> None:
        if self.satisfies not in _KNOWN_ACTIONS:
            raise ValueError(f"capability satisfies unknown action {self.satisfies!r}")
        if self.fulfilment not in FULFILMENT_MODES:
            raise ValueError(f"unknown fulfilment mode {self.fulfilment!r}")
        if not self.reference.strip():
            raise ValueError("a capability must name how it is fulfilled")


@dataclass(frozen=True)
class RoutingDecision:
    route: str
    reason: str
    capability: Optional[OfferCapability] = None

    def sells_nothing(self) -> bool:
        return self.route in ("NO_FORCED_OFFER", "HUMAN_REVIEW_REQUIRED",
                              "UNSUPPORTED_OFFER_PATH")


def route_offer(
    receipt: Receipt,
    business: Optional[BusinessReceipt],
    registry: Sequence[OfferCapability] = (),
) -> RoutingDecision:
    """Return exactly one terminal route.

    Order of checks is the whole design. The epistemic gate runs FIRST and
    unconditionally: no amount of available inventory can open a door the
    receipt closed. Only once the gate opens does the catalogue matter.
    """
    # ---- The gate. Nothing below can reopen it. -------------------------
    if business is None:
        return RoutingDecision(
            "NO_FORCED_OFFER",
            "no business receipt was derived, so nothing authorises an offer")

    if not receipt.offer_eligible():
        return RoutingDecision(
            "NO_FORCED_OFFER",
            f"receipt is not offer-eligible (verdict {receipt.verdict}, "
            f"beneficiary {'named' if receipt.beneficiary else 'NONE'})")

    action = business.available_next_action
    if action == "NO_REMEDIATION_OFFER_RECOMMENDED":
        return RoutingDecision(
            "NO_FORCED_OFFER",
            "the derived next action recommends no remediation offer")

    if action not in _KNOWN_ACTIONS:
        return RoutingDecision(
            "HUMAN_REVIEW_REQUIRED",
            f"unrecognised next action {action!r}; a router must not guess "
            f"which product an unknown state maps to")

    # ---- The catalogue. Only reached once the gate has opened. -----------
    matches = [c for c in registry if c.satisfies == action]
    if not matches:
        return RoutingDecision(
            "UNSUPPORTED_OFFER_PATH",
            f"the receipt permits {action} but no existing capability "
            f"satisfies it. This gap is reported rather than filled by "
            f"inventing a product")

    if len(matches) > 1:
        return RoutingDecision(
            "HUMAN_REVIEW_REQUIRED",
            f"{len(matches)} capabilities satisfy {action}; choosing between "
            f"them is a commercial judgement, not a routing rule")

    capability = matches[0]
    if capability.human_action_required or capability.fulfilment == "MANUAL_BY_OWNER":
        return RoutingDecision(
            "HUMAN_REVIEW_REQUIRED",
            f"{capability.reference} is fulfilled manually, so a human must "
            f"act before anything is promised to a customer",
            capability)

    return RoutingDecision("EXISTING_SUPPORTED_OFFER",
                           f"{capability.reference} satisfies {action}",
                           capability)
