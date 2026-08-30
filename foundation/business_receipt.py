"""The one-way boundary between what is true and what may be sold.

The constitution this implements:

    THE OFFER MAY READ THE RECEIPT.
    THE RECEIPT MAY NOT BEND FOR THE OFFER.

That is easy to write in a doctrine file and easy to violate in code. The
usual violation is not malice -- it is a second set of prose fields. Once
a "business summary" can be authored independently of the evidence
record, it can drift from it, and nothing detects the drift. The summary
then becomes the thing the customer reads, and the evidence becomes
decoration.

So the business layer here is not a document you fill in. It is a
DERIVATION. `derive_business_receipt()` is a pure function of a
`Receipt`, and the fields that could be used to oversell -- the verdict,
the confidence boundary, and the available next action -- are computed
from the record and cannot be passed in. The only free-text a caller may
supply is interpretation (`why_it_matters`, `hard_truth`), and even that
cannot upgrade the verdict.

Financial impact defaults to NOT MEASURED and stays there unless the
caller supplies actual measured evidence. There is no code path that
produces a dollar figure from nothing, because "you could lose millions"
is the single most tempting lie in this business.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from foundation.receipt import Receipt, ReceiptIntegrityError
from foundation.value_model import ValueModel
from foundation.value_model import NOT_MEASURED as VALUE_NOT_MEASURED

__all__ = [
    "NOT_MEASURED",
    "NEXT_ACTIONS",
    "BusinessReceipt",
    "derive_business_receipt",
]

NOT_MEASURED = "NOT MEASURED"

# What the customer may be shown as an available next step. Note that
# NO_REMEDIATION_OFFER_RECOMMENDED is a first-class outcome and is the
# default: most honest investigations end there.
NEXT_ACTIONS = (
    "NO_REMEDIATION_OFFER_RECOMMENDED",
    "REQUEST_DEEPER_INVESTIGATION",
    "REQUEST_REMEDIATION",
    "REQUEST_CONTINUOUS_VERIFICATION",
)


@dataclass(frozen=True)
class BusinessReceipt:
    """The customer-facing layer. Every load-bearing field is derived."""

    receipt_id: str
    target: str
    verdict: str                 # copied verbatim from the truth layer
    hard_truth: str              # interpretation, may not contradict the record
    why_it_matters: str
    financial_impact: str
    confidence_boundary: dict    # derived counts, not authored
    reentry_condition: str       # copied verbatim
    available_next_action: str   # derived from the offer gate
    beneficiary: Optional[str]
    # The source state of the figure above, kept as a separate field so a
    # reader cannot lose it while quoting the impact string.
    value_state: str = VALUE_NOT_MEASURED

    def sells_nothing(self) -> bool:
        return self.available_next_action == "NO_REMEDIATION_OFFER_RECOMMENDED"

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "target": self.target,
            "verdict": self.verdict,
            "hard_truth": self.hard_truth,
            "why_it_matters": self.why_it_matters,
            "financial_impact": self.financial_impact,
            "confidence_boundary": dict(self.confidence_boundary),
            "reentry_condition": self.reentry_condition,
            "available_next_action": self.available_next_action,
            "beneficiary": self.beneficiary,
            "value_state": self.value_state,
        }


def _confidence_boundary(receipt: Receipt) -> dict:
    """Counts, computed from the claims. Nobody gets to author these."""
    counts = {status: 0 for status in
              ("PROVEN", "REFUTED", "INFERENCE", "UNKNOWN", "NOT_CLAIMABLE")}
    for claim in receipt.claims:
        counts[claim.status] += 1
    return counts


def derive_business_receipt(
    receipt: Receipt,
    *,
    hard_truth: str = "",
    why_it_matters: str = "",
    financial_impact_evidence: str = "",
    value_model: Optional[ValueModel] = None,
) -> BusinessReceipt:
    """Derive the sellable layer from the evidence layer.

    There is deliberately NO parameter for verdict, confidence, offer, or
    next action. A caller who wants a different verdict has to go and
    change the evidence, which is the entire point.

    `financial_impact_evidence` must describe a real measurement. Passing
    a bare number is refused: an unsupported figure is exactly the claim
    this module exists to make impossible.

    `value_model` is the structured alternative: a `ValueModel` whose
    exposure carries its own source state and refuses to multiply an
    unmeasured factor. It is READ here and never authored -- and it
    cannot reach the offer gate below. A large number does not earn an
    offer and NOT_MEASURED does not forfeit one; only the evidence layer
    decides that.

    Supplying both is refused. Two writable paths to one field is how the
    figure and its provenance drift apart.
    """
    if value_model is not None and financial_impact_evidence.strip():
        raise ReceiptIntegrityError(
            "financial impact was given both as free text and as a value model; "
            "one field cannot have two sources of truth"
        )

    value_state = VALUE_NOT_MEASURED
    if value_model is not None:
        exposure = value_model.exposure()
        value_state = exposure.status
        impact = exposure.render()
        return _assemble(receipt, hard_truth, why_it_matters, impact, value_state)

    impact = NOT_MEASURED
    if financial_impact_evidence.strip():
        stripped = financial_impact_evidence.strip()
        # A figure with no measurement behind it is not an impact claim.
        if not any(ch.isalpha() for ch in stripped):
            raise ReceiptIntegrityError(
                f"financial impact {stripped!r} carries no measurement, only a "
                f"figure; state what was measured or leave it as {NOT_MEASURED}"
            )
        impact = stripped

    # Free text carries no source state, so `value_state` stays
    # NOT_MEASURED even when the prose describes a real measurement. That
    # asymmetry is deliberate: an unstructured sentence cannot be checked,
    # and the only way to earn a stronger state is to supply a ValueModel
    # whose inputs each name their own origin.
    return _assemble(receipt, hard_truth, why_it_matters, impact, value_state)


def _assemble(receipt: Receipt, hard_truth: str, why_it_matters: str,
              impact: str, value_state: str) -> BusinessReceipt:
    """Build the object. The gate lives here so both impact paths cross it.

    Note what is NOT an input to the branch below: `impact` and
    `value_state`. A large exposure does not earn an offer, and
    NOT_MEASURED does not forfeit one. Only the evidence layer decides.
    """
    # THE GATE. Derived from the truth layer, never supplied.
    if not receipt.offer_eligible():
        action = "NO_REMEDIATION_OFFER_RECOMMENDED"
    elif receipt.verdict == "DEFECT_ADMITTED":
        action = "REQUEST_REMEDIATION"
    elif receipt.verdict == "CONVENTION_NOT_CONTRACT":
        action = "REQUEST_CONTINUOUS_VERIFICATION"
    else:
        action = "REQUEST_DEEPER_INVESTIGATION"

    return BusinessReceipt(
        receipt_id=receipt.receipt_id,
        target=receipt.target,
        verdict=receipt.verdict,
        hard_truth=hard_truth or receipt.question,
        why_it_matters=why_it_matters or receipt.business_consequence,
        financial_impact=impact,
        confidence_boundary=_confidence_boundary(receipt),
        reentry_condition=receipt.reentry_condition,
        available_next_action=action,
        beneficiary=receipt.beneficiary,
        value_state=value_state,
    )
