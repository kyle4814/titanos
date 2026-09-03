"""foundation/partner_network.py -- the delivery-partner layer.

WHY THIS EXISTS, AND WHAT IT DELIBERATELY IS NOT

The campaign's central finding is that almost every real opportunity is
gated on something the operator does not have: held insurance, a
certification, corporate reference contracts, a turnover figure, staff
based in a jurisdiction, a legal entity. `entry_gate.py` already computes
exactly which of those a given opportunity demands. A delivery partner is
the lawful way to supply what the operator cannot -- so the single
highest-leverage missing piece is the BRIDGE from "this opportunity has a
gate the operator cannot clear" to "a partner who could provide it,"
plus a way to hold candidate partners honestly.

That bridge is `derive_partner_needs()`. It reuses `entry_gate` and adds
no new opportunity analysis.

WHAT THIS IS NOT, THIS CYCLE (Pareto slice -- one bottleneck):

  - NO outreach. No message is drafted, addressed, or sent here. Contact
    is a human-approved action gated elsewhere; this module has no
    network import and no send verb.
  - NO invented people. The registry starts empty. Every test uses
    synthetic candidates. Nothing in this module scrapes, fetches, or
    fabricates a contact.
  - NO partner without evidence. A DISCOVERED or CONTACTED candidate is
    NEVER a partner. `is_partner()` returns True only for an ACTIVE
    relationship, and a claim never becomes VERIFIED because the
    candidate asserted it.

THE TWO DISCIPLINES CARRIED FROM ELSEWHERE IN THIS REPO

  - Forward-only lifecycle with no state-skipping, mirroring
    `deal_pipeline.Deal` -- a candidate cannot jump to ACTIVE because a
    model is confident.
  - UNKNOWN is not ZERO and self-report is not fact, mirroring
    `qualification`/`eligibility`/`value_model` -- a claim carries an
    explicit evidence tier, and the strongest tier a bare self-report
    can hold is SELF_REPORTED.

NO NETWORK. Pure data and pure functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from foundation.entry_gate import EntryAssessment, GATE_KINDS

__all__ = [
    "PartnerNetworkError",
    "RELATIONSHIP_STATES",
    "TERMINAL_STATES",
    "EVIDENCE_TIERS",
    "PARTNER_NEED_KINDS",
    "PartnerNeed",
    "EvidencedClaim",
    "PartnerCandidate",
    "derive_partner_needs",
    "advance_state",
    "is_partner",
    "format_partner_needs",
]


class PartnerNetworkError(ValueError):
    """Raised on a malformed candidate, an illegal state transition, or a
    claim that would fabricate evidence. This module refuses to represent
    a contact as a partner."""


# The lifecycle, in order. Forward-only: a candidate advances one or more
# steps but never skips backwards, and never jumps to a later state
# because a model is confident (see `advance_state`). Verbatim the
# progression the directive names.
RELATIONSHIP_STATES = (
    "DISCOVERED",        # a name found in public data. NOT a partner.
    "UNVERIFIED",        # captured, no evidence checked yet
    "EVIDENCE_CHECKED",  # public evidence assessed
    "QUALIFIED",         # meets an opportunity's partner-need on evidence
    "HUMAN_REVIEW",      # awaiting the operator's judgement
    "CONTACTED",         # outreach sent (by a human-approved action). NOT a partner.
    "RESPONDED",         # replied
    "NEGOTIATING",       # commercial discussion underway
    "AGREEMENT_PENDING",  # terms agreed, not yet signed
    "ACTIVE",            # signed agreement + a real relationship
)

# States a candidate cannot advance out of.
TERMINAL_STATES = ("DECLINED", "REJECTED", "INACTIVE")

_ALL_STATES = RELATIONSHIP_STATES + TERMINAL_STATES
_STATE_INDEX = {s: i for i, s in enumerate(RELATIONSHIP_STATES)}

# The ONLY state at which a candidate is a partner. DISCOVERED and
# CONTACTED are explicitly not, however far along the pipeline they sit.
_PARTNER_STATE = "ACTIVE"

# How strongly a claim about a candidate is supported. Ordered weakest to
# strongest. A bare self-report can never be more than SELF_REPORTED; a
# company website is PUBLICLY_EVIDENCED at most, never VERIFIED.
EVIDENCE_TIERS = (
    "UNKNOWN",
    "SELF_REPORTED",
    "PUBLICLY_EVIDENCED",
    "THIRD_PARTY_EVIDENCED",
    "VERIFIED",
)

# The tiers at or above which a claim counts as independently supported
# (i.e. not merely the candidate's own assertion).
_INDEPENDENT_TIERS = frozenset({
    "PUBLICLY_EVIDENCED", "THIRD_PARTY_EVIDENCED", "VERIFIED"})

# A partner need is exactly one entry_gate GATE_KIND -- the capability a
# partner would supply to unlock the opportunity. Reusing GATE_KINDS
# rather than inventing a parallel vocabulary keeps this bridge honest:
# a need can only be something entry_gate actually detected.
PARTNER_NEED_KINDS = GATE_KINDS


@dataclass(frozen=True)
class PartnerNeed:
    """One capability an opportunity requires that a partner could supply,
    derived from an `entry_gate` gate. `quote` is the opportunity's own
    words -- never paraphrased."""

    kind: str
    quote: str
    reason: str

    def __post_init__(self) -> None:
        if self.kind not in PARTNER_NEED_KINDS:
            raise PartnerNetworkError(
                f"unknown partner-need kind {self.kind!r} -- must be an "
                f"entry_gate GATE_KIND {PARTNER_NEED_KINDS}")
        if not self.quote.strip():
            raise PartnerNetworkError(
                "a partner need must quote the opportunity clause that "
                "created it -- an unquoted need is an assertion")


@dataclass(frozen=True)
class EvidencedClaim:
    """One assertion about a candidate, with its evidence tier and where
    that evidence came from. A VERIFIED or independently-evidenced claim
    MUST carry a source -- a claim cannot be independently supported by
    nothing."""

    field_name: str
    value: str
    tier: str
    source_url: str = ""

    def __post_init__(self) -> None:
        if self.tier not in EVIDENCE_TIERS:
            raise PartnerNetworkError(
                f"unknown evidence tier {self.tier!r} -- one of {EVIDENCE_TIERS}")
        if not self.field_name.strip():
            raise PartnerNetworkError("an evidenced claim must name its field")
        if self.tier in _INDEPENDENT_TIERS and not self.source_url.strip():
            raise PartnerNetworkError(
                f"a {self.tier} claim about {self.field_name!r} carries no "
                "source -- a claim cannot be independently evidenced by "
                "nothing; use SELF_REPORTED or provide the source")

    @property
    def is_independently_evidenced(self) -> bool:
        return self.tier in _INDEPENDENT_TIERS


@dataclass(frozen=True)
class PartnerCandidate:
    """One potential delivery partner. Starts life DISCOVERED and is NOT
    a partner until ACTIVE. Every substantive assertion is an
    `EvidencedClaim`, so nothing about the candidate is a fact merely
    because it was written down.

    The field set is deliberately the essential subset the directive's
    profile lists -- identity, where they are, what they claim to do,
    how to reach them publicly, and the provenance/relationship state.
    A thirty-field record with mostly-UNKNOWN columns is noise, not
    diligence.
    """

    candidate_id: str
    organisation_name: str
    country: str
    relationship_status: str
    claims: Tuple[EvidencedClaim, ...] = ()
    public_contact: str = ""
    discovery_method: str = ""
    source_urls: Tuple[str, ...] = ()
    opted_out: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise PartnerNetworkError("a candidate must have an id")
        if not self.organisation_name.strip():
            raise PartnerNetworkError(
                "a candidate must name the organisation or individual -- an "
                "unnamed candidate is a placeholder, not a candidate")
        if self.relationship_status not in _ALL_STATES:
            raise PartnerNetworkError(
                f"relationship_status must be one of {_ALL_STATES}, got "
                f"{self.relationship_status!r}")
        seen = set()
        for c in self.claims:
            if not isinstance(c, EvidencedClaim):
                raise PartnerNetworkError(
                    "claims must be EvidencedClaim instances -- a bare "
                    "string smuggles an unclassified assertion in as fact")

    def claim(self, field_name: str) -> Optional[EvidencedClaim]:
        for c in self.claims:
            if c.field_name == field_name:
                return c
        return None


def is_partner(candidate: PartnerCandidate) -> bool:
    """A candidate is a PARTNER only with a signed, active relationship.
    A DISCOVERED name or a CONTACTED lead is never a partner, and an
    opted-out candidate is never a partner regardless of state."""
    if not isinstance(candidate, PartnerCandidate):
        raise PartnerNetworkError("is_partner() takes a PartnerCandidate")
    return (candidate.relationship_status == _PARTNER_STATE
            and not candidate.opted_out)


def advance_state(candidate: PartnerCandidate, to_state: str) -> PartnerCandidate:
    """Move a candidate one or more steps FORWARD along the lifecycle,
    or to a terminal state. Returns a new candidate; never mutates.

    Refuses to skip -- ACTIVE cannot be reached from DISCOVERED in one
    move, because a partner cannot become active without passing through
    contact, response and agreement, however confident a caller is. A
    backwards move is refused. An opted-out candidate can only be moved
    to a terminal state.
    """
    if to_state not in _ALL_STATES:
        raise PartnerNetworkError(
            f"unknown state {to_state!r} -- one of {_ALL_STATES}")
    current = candidate.relationship_status
    if current in TERMINAL_STATES:
        raise PartnerNetworkError(
            f"{current} is terminal; the candidate cannot advance")
    if candidate.opted_out and to_state not in TERMINAL_STATES:
        raise PartnerNetworkError(
            "an opted-out candidate may only move to a terminal state -- "
            "respecting the opt-out is not optional")
    if to_state in TERMINAL_STATES:
        return _replace_status(candidate, to_state)
    # Forward-only within the ordered pipeline, no skipping.
    ci, ti = _STATE_INDEX[current], _STATE_INDEX[to_state]
    if ti <= ci:
        raise PartnerNetworkError(
            f"cannot move from {current} to {to_state}: only forward "
            "transitions are allowed, and a candidate never re-enters a "
            "state it has left")
    if ti != ci + 1:
        raise PartnerNetworkError(
            f"cannot skip from {current} to {to_state}: the lifecycle is "
            f"stepwise ({RELATIONSHIP_STATES[ci]} -> "
            f"{RELATIONSHIP_STATES[ci + 1]} next). A candidate does not "
            "become a partner because a model is confident.")
    return _replace_status(candidate, to_state)


def _replace_status(candidate: PartnerCandidate, to_state: str) -> PartnerCandidate:
    from dataclasses import replace
    return replace(candidate, relationship_status=to_state)


def derive_partner_needs(assessment: EntryAssessment) -> Tuple[PartnerNeed, ...]:
    """THE BRIDGE. Turn one opportunity's entry-gate analysis into the
    capabilities a partner would have to supply to make it winnable.

    A partner is needed for what the OPERATOR cannot clear himself:
      - operator_gates: hard walls that need the operator to hold/be
        something (held insurance, certification, legal entity, identity)
        -- a partner with those credentials can carry them.
      - work_gates: capacity the operator lacks (references, turnover,
        local presence, round-the-clock staffing) -- a partner supplies
        the capacity.

    A partner is NOT needed for:
      - declaration_gates: the operator can satisfy these himself with a
        statement (a broker letter, an ability-to-obtain).
      - deferred_gates: the document defers these past admission.
    Reusing entry_gate's own classification keeps this honest -- this
    function invents no requirement entry_gate did not find.
    """
    if not isinstance(assessment, EntryAssessment):
        raise PartnerNetworkError(
            "derive_partner_needs() takes an EntryAssessment")

    needs: list[PartnerNeed] = []
    for gate in assessment.operator_gates:
        needs.append(PartnerNeed(
            kind=gate.kind, quote=gate.quote,
            reason=("a hard admission wall the operator cannot clear "
                    "personally -- a partner holding this credential could "
                    "carry it, subject to the opportunity's own rules on "
                    "subcontracting/consortium/reliance")))
    for gate in assessment.work_gates:
        needs.append(PartnerNeed(
            kind=gate.kind, quote=gate.quote,
            reason=("capacity the operator lacks -- a partner could supply "
                    "it where the opportunity permits reliance on another "
                    "entity's resources")))
    return tuple(needs)


def format_partner_needs(needs: Tuple[PartnerNeed, ...]) -> str:
    """Operator-facing render. States plainly that a need is not a match
    and not authority to contact anyone."""
    if not needs:
        return ("NO PARTNER NEEDED -- this opportunity states no gate the "
                "operator cannot clear himself. (A gate the document did "
                "not state is UNKNOWN, not absent.)")
    lines = [f"WHAT A PARTNER WOULD HAVE TO SUPPLY ({len(needs)}):", ""]
    for n in needs:
        lines.append(f"  [{n.kind}] {n.reason}")
        lines.append(f"      opportunity's words: {n.quote}")
    lines.append("")
    lines.append(
        "This is the capability gap, NOT a matched partner and NOT "
        "authority to contact anyone. Whether this opportunity even "
        "permits a partner (subcontracting / consortium / reliance) is a "
        "separate question the tender's own rules answer -- and any "
        "outreach is a human-approved action, gated elsewhere.")
    return "\n".join(lines)
