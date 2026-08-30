"""The boundary between a Receipt and the artifact a customer actually reads.

WHY THIS EXISTS

`receipt.py` enforces what may be claimed. A renderer enforces nothing --
it prints what it is handed. Between them sits the place where every
epistemic guarantee is silently lost: a `NOT_MEASURED` value formatted
into a sentence, an `INFERENCE` claim rendered in the same typeface as a
`PROVEN` one, a price block emitted beside a finding on a receipt that
was never offer-eligible.

An audit of the real generator (`vuln_report.py`, the path behind 31 real
deliveries) found exactly that: an unconditional monthly-subscription
panel in `generate_full_report`, and an unconditional call-to-action in
`generate_teaser`. Neither was gated on anything, so the canonical
customer artifact was structurally incapable of `NO_FORCED_OFFER`.

This module is the gate. It decides whether an offer is PERMITTED. It
does not decide what the offer is.

TWO AXES THAT MUST NOT COLLAPSE

  severity   CRITICAL/HIGH/MEDIUM/LOW  -- how bad the thing is if true.
             A property of the target. Owned by the scanner.

  status     PROVEN/INFERENCE/UNKNOWN  -- how strongly THIS investigation
             established it. Owned by the Receipt.

A finding can be CRITICAL and merely INFERRED (a version banner with no
CVE confirmation), or LOW and PROVEN (a directly observed missing
header). Deriving either axis from the other would let a confident red
badge stand in for evidence it never had. This module therefore refuses
to invent a severity from a claim status, and refuses to invent a status
from a severity.

WHAT STAYS OUT OF HERE

No price, amount, currency, or product id is stored, defaulted, or
derived in this module. The caller supplies the commercial content and
this module decides only whether the caller is allowed to show it. That
keeps pricing at the routing boundary, where policy belongs, and out of
the evidence layer, where it could anchor a verdict.
"""

from __future__ import annotations

from typing import Any, Optional

from foundation.receipt import Receipt
from foundation.business_receipt import BusinessReceipt

__all__ = [
    "OFFER_WITHHELD",
    "BrickIntegrityError",
    "offer_permitted",
    "build_brick_input",
]

OFFER_WITHHELD = "NO_FORCED_OFFER"

# Scanner severities. Listed only so this module can REFUSE to invent one.
_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")


class BrickIntegrityError(ValueError):
    """The artifact tried to say more than its receipt permits."""


def offer_permitted(receipt: Receipt,
                    business: Optional[BusinessReceipt]) -> bool:
    """The gate. Fail-closed, and both layers must agree.

    Requiring BOTH `receipt.offer_eligible()` and a business receipt whose
    derived action is not the withhold value is deliberate duplication:
    the two are computed by different modules from the same record, so a
    future change that loosens one still meets the other. A single check
    would be one edit away from an ungated CTA.
    """
    if business is None:
        return False
    if not receipt.offer_eligible():
        return False
    return business.available_next_action != "NO_REMEDIATION_OFFER_RECOMMENDED"


def _claims_payload(receipt: Receipt) -> list[dict]:
    """Carry claims across WITH their status attached to each one.

    Status travels on the claim itself rather than as a separate list, so
    a renderer cannot display the statements while dropping the strengths
    -- the failure mode that makes an INFERENCE look PROVEN.
    """
    return [
        {
            "statement": c.statement,
            "status": c.status,
            "evidence": c.evidence,
            # Rendered label. Present so a template that only knows how to
            # print strings still shows the strength.
            "label": f"[{c.status}]",
        }
        for c in receipt.claims
    ]


def build_brick_input(
    scan_result: dict,
    receipt: Receipt,
    business: Optional[BusinessReceipt] = None,
    *,
    offer_content: Optional[dict] = None,
) -> dict[str, Any]:
    """Produce the generator's input dict from a scan plus its receipt.

    `scan_result` passes through essentially verbatim: severity, ports,
    services, TLS and DNS are scanner facts with no Receipt equivalent,
    and inventing them here is exactly what this module forbids.

    `offer_content` is the caller's commercial copy. It is emitted ONLY
    if the gate opens. Supplying it does not make it appear -- that is
    the whole point of passing it in rather than letting the template
    hold it.

    Raises rather than silently dropping when a caller tries to smuggle a
    claim into the findings list, because a silent drop would look like
    success.
    """
    if not isinstance(scan_result, dict):
        raise BrickIntegrityError("scan_result must be the scanner's dict")

    out = dict(scan_result)

    # A caller must not hand us findings whose severity was derived from a
    # claim status. We cannot read intent, but we can refuse the shape that
    # makes it possible: a finding carrying a claim status where a severity
    # belongs.
    for finding in out.get("findings", []) or []:
        sev = str(finding.get("severity", "")).upper()
        if sev and sev not in _SEVERITIES:
            raise BrickIntegrityError(
                f"finding severity {sev!r} is not a scanner severity "
                f"{_SEVERITIES}; evidential strength is a different axis and "
                f"must not be rendered as severity"
            )

    permitted = offer_permitted(receipt, business)

    out["verdict"] = receipt.verdict
    out["claims"] = _claims_payload(receipt)
    out["beneficiary"] = receipt.beneficiary
    out["reentry_condition"] = receipt.reentry_condition
    out["offer_permitted"] = permitted
    out["offer"] = offer_content if permitted else None
    out["offer_status"] = receipt.offer_status()

    # The value line already carries its own source state from the value
    # model (e.g. "NOT MEASURED", or "24800 AUD [ESTIMATED] under stated
    # assumptions: ..."). It is passed as that rendered string and never as
    # a bare number, so a template cannot print a figure without its state.
    if business is not None:
        impact = business.financial_impact
        if impact and not any(ch.isalpha() for ch in str(impact)):
            raise BrickIntegrityError(
                f"financial impact {impact!r} is a bare figure with no state; "
                f"a number without its source state must never reach a customer"
            )
        out["value_line"] = impact
        out["value_state"] = business.value_state
    else:
        out["value_line"] = None
        out["value_state"] = "NOT_MEASURED"

    return out
