"""The Receipt: a structured evidence record that cannot overclaim.

WHY THIS EXISTS (written after a recon pass, before any code):

An investigation pipeline generally already owns the parts either side
of this module -- intake, payment/entitlement, alerting, and some
renderer that turns a data structure into a customer-readable artifact.
Those must not be rebuilt.

The gap is the object in the middle. A renderer's input is typically a
hand-authored dict per client, so nothing carries an investigation's
epistemic structure -- what was proven, what was merely inferred, what
stayed unknown, and who actually benefits from acting -- from the sensor
to the artifact. Without that object there is no mechanical barrier
between "what we found" and "what we would like to sell", which is
exactly where this kind of work goes bad.

This module deliberately names no infrastructure, customer, or
commercial detail. It is the machine, not the operator.

WHAT MAKES THIS DIFFERENT FROM A REPORT TEMPLATE

A template lets you write anything. This module makes three specific
lies structurally impossible, enforced at construction rather than
promised in a docstring:

  1. A receipt cannot admit a defect without at least one PROVEN claim.
     Fear needs evidence.
  2. A receipt cannot admit a defect without a named beneficiary --
     someone or something that actually suffers if nothing changes.
  3. A receipt cannot be offer-eligible without a beneficiary. No
     beneficiary, no offer. NO_FORCED_OFFER is the default and is a
     first-class, non-failure outcome.

This is the sensor/business firewall expressed as code. The sensor is
the court; the business layer may only argue from the record.

WHAT IS DELIBERATELY ABSENT

There is no price, product id, currency, or discount field anywhere in
this module, and no way to add one without editing it. Pricing lives in
the existing entitlement layer, which already owns it. A receipt that
could carry a price could be tuned to justify one.

RELATIONSHIP TO `foundation/crystal.py`

`Crystal` records "what was believed and what would change that belief"
for an internal cycle. It is NOT extended here, on purpose: a Crystal is
an internal epistemic note, while a Receipt is a customer-facing
artifact with a beneficiary test and an offer gate. Merging them would
put commercial fields on the internal record -- the exact contamination
this firewall exists to prevent. A Receipt may cite a crystal id in
`evidence_refs`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

__all__ = [
    "CLAIM_STATUSES",
    "VERDICTS",
    "Claim",
    "Receipt",
    "ReceiptIntegrityError",
    "format_executive_summary",
]


# The epistemic partition every receipt in this project's history has
# actually used. Deliberately NOT
# `kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS`: that vocabulary
# answers "what KIND of knowledge is this" (CREATIVE_CONCEPT,
# ARCHITECTURAL_METAPHOR, ...). This one answers a different and
# orthogonal question -- "how strongly did THIS investigation establish
# THIS claim" -- so reusing the other enum would have forced every claim
# into a category that does not describe evidential strength.
CLAIM_STATUSES = ("PROVEN", "REFUTED", "INFERENCE", "UNKNOWN", "NOT_CLAIMABLE")

# The verdict is about what the investigation ESTABLISHED, never about
# what it is worth. "NO_DEFECT" and "CONVENTION_NOT_CONTRACT" are
# successful outcomes, not empty ones.
VERDICTS = (
    "DEFECT_ADMITTED",
    "NO_DEFECT",
    "COVERAGE_GAP_RECORDED",
    "CONVENTION_NOT_CONTRACT",
    "REFUTED_PRIOR_CLAIM",
    "INADMISSIBLE",
    "UNKNOWN",
)


class ReceiptIntegrityError(ValueError):
    """A receipt tried to claim more than its evidence supports."""


@dataclass(frozen=True)
class Claim:
    """One statement plus how strongly this investigation established it.

    `evidence` is required for a PROVEN claim and must be a description
    of what was actually observed -- a command run, a measured value, a
    file read. A PROVEN claim with empty evidence is the cheapest
    possible lie, so it is refused here rather than in review.
    """

    statement: str
    status: str
    evidence: str = ""

    def __post_init__(self) -> None:
        if self.status not in CLAIM_STATUSES:
            raise ReceiptIntegrityError(
                f"claim status {self.status!r} is not one of {CLAIM_STATUSES}"
            )
        if not self.statement.strip():
            raise ReceiptIntegrityError("a claim must have a statement")
        if self.status == "PROVEN" and not self.evidence.strip():
            raise ReceiptIntegrityError(
                f"PROVEN claim {self.statement!r} carries no evidence; a claim "
                f"asserted as proven must name what was actually observed"
            )

    def to_dict(self) -> dict:
        return {
            "statement": self.statement,
            "status": self.status,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class Receipt:
    """A finalized, self-consistent evidence record.

    Immutable by construction (`frozen=True`). A later investigation does
    not edit a receipt -- it issues a new one whose `supersedes` names
    the old id, exactly as `CrystalStore` already does for crystals, so
    the earlier judgment and the correction both remain readable.
    """

    receipt_id: str
    target: str
    question: str
    verdict: str
    claims: tuple[Claim, ...]
    # The beneficiary test. Who or what actually suffers if nothing
    # changes? `None` means nobody identified -- a legitimate and common
    # result, and the reason most receipts must not carry an offer.
    beneficiary: Optional[str] = None
    business_consequence: str = ""
    recommended_action: str = "NO_ACTION_REQUIRED"
    reentry_condition: str = ""
    authority_used: str = "READ_ONLY"
    evidence_refs: tuple[str, ...] = ()
    methodology_version: str = "1"
    supersedes: Optional[str] = None
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ReceiptIntegrityError(
                f"verdict {self.verdict!r} is not one of {VERDICTS}"
            )
        if not self.claims:
            raise ReceiptIntegrityError(
                "a receipt with no claims asserts nothing and cannot be issued"
            )

        # RULE 1 -- fear requires evidence.
        if self.verdict == "DEFECT_ADMITTED" and not self.proven_claims():
            raise ReceiptIntegrityError(
                "DEFECT_ADMITTED requires at least one PROVEN claim; a defect "
                "asserted only from inference is a hypothesis, not a finding"
            )

        # RULE 2 -- a defect requires somebody who is actually hurt.
        if self.verdict == "DEFECT_ADMITTED" and not (self.beneficiary or "").strip():
            raise ReceiptIntegrityError(
                "DEFECT_ADMITTED requires a named beneficiary; a defect nobody "
                "suffers from is a coverage gap, not a defect -- use "
                "COVERAGE_GAP_RECORDED"
            )

    def proven_claims(self) -> tuple[Claim, ...]:
        return tuple(c for c in self.claims if c.status == "PROVEN")

    def unknowns(self) -> tuple[Claim, ...]:
        return tuple(c for c in self.claims if c.status == "UNKNOWN")

    def offer_eligible(self) -> bool:
        """RULE 3 -- the offer gate.

        An offer may exist only when a real beneficiary was identified AND
        the investigation established something worth acting on. Every
        other receipt is honest and offerless. This returns a bool and
        never a price: what it is worth is not this module's business.
        """
        if not (self.beneficiary or "").strip():
            return False
        return self.verdict in ("DEFECT_ADMITTED", "COVERAGE_GAP_RECORDED",
                                "CONVENTION_NOT_CONTRACT")

    def offer_status(self) -> str:
        return "OFFER_ELIGIBLE" if self.offer_eligible() else "NO_FORCED_OFFER"

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "target": self.target,
            "question": self.question,
            "verdict": self.verdict,
            "claims": [c.to_dict() for c in self.claims],
            "beneficiary": self.beneficiary,
            "business_consequence": self.business_consequence,
            "recommended_action": self.recommended_action,
            "reentry_condition": self.reentry_condition,
            "authority_used": self.authority_used,
            "evidence_refs": list(self.evidence_refs),
            "methodology_version": self.methodology_version,
            "supersedes": self.supersedes,
            "recorded_at": self.recorded_at,
            "offer_status": self.offer_status(),
        }


def format_executive_summary(receipt: Receipt) -> str:
    """The customer-facing layer, derived ONLY from the record.

    Every line is computed from `receipt`; nothing here can introduce a
    claim the forensic layer does not already carry. That is why this is
    a function over a Receipt rather than a second set of prose fields --
    an executive summary that could be written independently could
    disagree with its own evidence.
    """
    lines = [
        f"RECEIPT {receipt.receipt_id}",
        f"TARGET: {receipt.target}",
        f"QUESTION: {receipt.question}",
        "",
        f"VERDICT: {receipt.verdict}",
        f"BENEFICIARY: {receipt.beneficiary or 'NONE IDENTIFIED'}",
        f"OFFER: {receipt.offer_status()}",
        "",
        f"PROVEN ({len(receipt.proven_claims())}):",
    ]
    for c in receipt.proven_claims():
        lines.append(f"  - {c.statement}")
    unknowns = receipt.unknowns()
    lines.append("")
    lines.append(f"STILL UNKNOWN ({len(unknowns)}):")
    for c in unknowns:
        lines.append(f"  - {c.statement}")
    lines.append("")
    lines.append(f"RECOMMENDED ACTION: {receipt.recommended_action}")
    if receipt.business_consequence:
        lines.append(f"CONSEQUENCE OF DOING NOTHING: {receipt.business_consequence}")
    if receipt.reentry_condition:
        lines.append(f"THIS CHANGES IF: {receipt.reentry_condition}")
    return "\n".join(lines)
