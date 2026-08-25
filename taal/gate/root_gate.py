"""
TAAL Root Gate — the decision engine.

THE ONE JOB

Decide, for exactly one declared permission_request, whether it may be
AUTHORIZED, AUTHORIZED_WITH_CONSTRAINTS, sent to REQUIRES_HUMAN_REVIEW,
QUARANTINED, or REFUSED — by walking the governing directive's exact
12-question sequence (§6), in order, as deterministic Python. Same shape
as firewall/gate.py::evaluate(): ordered simple predicate checks, a
frozen-verdict-shaped output, and refusal treated as a SUCCESS state, not
a failure of the gate.

WHAT THIS CANNOT DO — stated, not buried

It evaluates DECLARED facts about a request (identity_verified,
authority_asserted, provenance_status, and so on — the fields on
GateInput). It cannot detect a request that lies about itself. A hostile
requester who sets identity_verified=True without having actually been
verified defeats this gate entirely; only whatever upstream system
populates GateInput (identity verification, authority attestation,
provenance checking) can catch that, and none of it lives in this file.
A green result from evaluate_request() means "cleared this gate on the
facts as declared", never "definitely legitimate" — the identical
limitation firewall/gate.py's module docstring states about artifact
metadata, restated here honestly for request metadata.

WHY THE 12 QUESTIONS ARE WALKED IN ORDER, NOT AS INDEPENDENT SWITCHES

The governing directive's root-gate sequence is a decision PROCEDURE, not
a checklist scored independently. Later questions (Q7 reversibility, Q8
consequence-of-wrongness) only matter once identity/authority/scope have
already cleared; a fully-clean high-impact-but-reversible request is
treated differently than a fully-clean high-impact-and-irreversible one,
and that distinction is only reachable once the earlier questions have
already passed. Walking them in order, each annotated with the literal
question it answers, means a reviewer can read this function top to
bottom and see exactly which question first produced a non-AUTHORIZED
result — the same auditability property firewall/gate.py's ordered
switches give for artifact classification.

JUDGMENT CALLS DOCUMENTED WHERE MADE (rules 2 and 5 of the task brief)

  RULE 2 (no asserted authority / no authority evidence):
    - authority_asserted=False -> REFUSED. A request that does not even
      CLAIM authority to act is not an ambiguous case needing a human —
      there is nothing for a human to adjudicate. Refusal is the correct
      terminal state, mirroring firewall/gate.py's "unrecognised
      classification -> REFUSED, never defaulted" pattern: an absent
      claim is not evidence needing review, it is simply absent.
    - authority_asserted=True but authority_evidence=() -> REQUIRES_
      HUMAN_REVIEW, not REFUSED. Here the requester DID make a claim —
      the claim might be true and simply under-evidenced in this
      particular submission (a real authority who forgot to attach proof,
      versus a requester with no authority at all). That ambiguity is
      exactly what a human reviewer, not an automatic refusal, exists to
      resolve. Automatically refusing every under-evidenced-but-asserted
      claim would punish legitimate requesters for a paperwork gap
      identically to punishing an attacker for having no claim at all —
      collapsing two different failure modes into one response loses
      the signal a human needs to tell them apart.

  RULE 5 (contradictory_evidence non-empty):
    - Any contradictory_evidence at all caps the verdict at REQUIRES_
      HUMAN_REVIEW, never AUTHORIZED_WITH_CONSTRAINTS and never
      AUTHORIZED. A named, specific contradiction in the request's own
      supporting material is not a "constrain and proceed" situation —
      constraining scope does not resolve a factual contradiction, it
      just narrows the blast radius of a decision made without actually
      resolving the conflict. Handing that to a human, with the specific
      contradiction quoted into `reasons`, mirrors firewall/gate.py's
      corroborating-artifacts ancestry-collapse rule: when the evidence
      set contradicts itself, the machine's job is to surface the
      conflict for review, not to average it away into a partial grant.
      (AUTHORIZED_WITH_CONSTRAINTS was considered and rejected as the
      default here — see the "no default softer path" note in
      evaluate_request's Q5 block for why.)

RULE NUMBERING

This file does not define its own rule-numbering scheme (VD-R-<n>,
MG-R-<n>) because it is not a structural validator — it is a decision
procedure. Instead each branch below is commented with the literal
directive question it answers (Q1..Q12), which is the auditable unit
here, the same way firewall/gate.py names each check after the
directive section it enforces (§10, §11, §12, §14).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["GateInput", "GateDecision", "evaluate_request", "VERDICTS"]

# Verdicts this engine may return. REFUSED, QUARANTINED and REQUIRES_
# HUMAN_REVIEW are SUCCESS states: the system correctly declined to grant
# unearned authority. UNKNOWN is reserved for a genuinely unresolvable
# input shape (see the fail-closed note in evaluate_request) rather than
# ever being produced by ordinary decision logic — the 12-question walk
# always terminates in one of the other five states.
VERDICTS = (
    "AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS", "REQUIRES_HUMAN_REVIEW",
    "QUARANTINED", "REFUSED", "UNKNOWN",
)

_PROVENANCE_STATES = frozenset({"VERIFIED", "CLAIMED", "UNKNOWN", "UNVERIFIABLE"})


@dataclass(frozen=True)
class GateInput:
    """One permission_request's declared facts, as plain fields.

    Deliberately NOT built against taal/schema/permission_request.py —
    that schema is owned by a different agent running in parallel and may
    not exist in a stable shape yet. This is root_gate's own minimal input
    contract; a future integration layer is responsible for mapping a
    validated permission_request document onto a GateInput, not this
    file.
    """
    request_id: str
    requester: str
    action: str
    resource: str
    scope: str
    duration: str
    delegation: bool = False
    identity_verified: bool = False
    authority_asserted: bool = False
    authority_evidence: tuple[str, ...] = ()
    scope_declared_necessary: bool = False
    # A narrower scope that would still satisfy the justification, if one
    # exists. Non-empty here is what makes Q4 ("can authority be
    # reduced?") concrete and actionable rather than rhetorical.
    reducible_scope: tuple[str, ...] = ()
    reversible: bool = False
    provenance_status: str = "UNKNOWN"  # VERIFIED | CLAIMED | UNKNOWN | UNVERIFIABLE
    supporting_evidence: tuple[str, ...] = ()
    contradictory_evidence: tuple[str, ...] = ()
    # Caller-declared: would getting this wrong be high-consequence.
    high_impact: bool = False


@dataclass
class GateDecision:
    verdict: str
    request_id: str
    reasons: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "request_id": self.request_id,
            "reasons": list(self.reasons),
            "constraints": list(self.constraints),
        }


def _cap(current: str, ceiling: str, order: tuple[str, ...]) -> str:
    """Return whichever of (current, ceiling) is LESS permissive, per the
    supplied permissiveness ordering (most permissive first). Used
    throughout to enforce "this check can only make the verdict more
    conservative, never more permissive" — the same one-directional
    ratchet firewall/gate.py's ordered switches embody implicitly by
    returning early on any failing check.
    """
    return current if order.index(current) >= order.index(ceiling) else ceiling


# Most permissive first. AUTHORIZED_WITH_CONSTRAINTS sits between
# AUTHORIZED and REQUIRES_HUMAN_REVIEW: it grants something, but less than
# an unconditional AUTHORIZED, and it is reachable without human
# intervention where REQUIRES_HUMAN_REVIEW is not.
_PERMISSIVENESS_ORDER = (
    "AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS", "REQUIRES_HUMAN_REVIEW",
    "QUARANTINED", "REFUSED",
)


def evaluate_request(inp: GateInput) -> GateDecision:
    """Walk the governing directive's 12 questions, in order, over one
    declared permission_request. Deterministic; no scoring, no learned
    classifier. Refusal, quarantine and human-review are success states.
    """
    reasons: list[str] = []
    constraints: list[str] = []
    # Start at the most permissive state and let each question only ever
    # move the verdict DOWN the permissiveness order (never back up) —
    # the ratchet described in `_cap`.
    verdict = "AUTHORIZED"

    def descend(new_verdict: str, reason: str) -> None:
        nonlocal verdict
        verdict = _cap(verdict, new_verdict, _PERMISSIVENESS_ORDER)
        reasons.append(reason)

    # --- Q1: "Who is asking, and is that identity verified?" -------------
    # Unverified identity caps the verdict at REQUIRES_HUMAN_REVIEW no
    # matter what else is true. This is deliberately evaluated FIRST and
    # unconditionally — see TestSelfAuthorization: an otherwise-perfect
    # request cannot buy its way past this with a strong showing on every
    # other question.
    if not inp.identity_verified:
        descend(
            "REQUIRES_HUMAN_REVIEW",
            "Q1 (identity verified?): identity_verified=False. Unverified "
            "identity can never reach AUTHORIZED regardless of any other "
            "field's strength.",
        )

    # --- Q2: "Is authority to make this request asserted, and evidenced?" -
    # Judgment call documented in the module docstring above.
    if not inp.authority_asserted:
        descend(
            "REFUSED",
            "Q2 (authority asserted?): authority_asserted=False. A "
            "request that does not even claim authority to act is "
            "refused outright — there is no ambiguous claim for a human "
            "to adjudicate.",
        )
    elif not inp.authority_evidence:
        descend(
            "REQUIRES_HUMAN_REVIEW",
            "Q2 (authority evidenced?): authority is asserted but "
            "authority_evidence is empty. The claim may be true and "
            "simply under-evidenced in this submission — that is a "
            "human-adjudication case, distinct from asserting no "
            "authority at all.",
        )

    # --- Q3: "Is the requested scope declared necessary for the stated
    #          purpose?" / Q4: "Can authority be reduced?" ---------------
    # scope_declared_necessary=False with a reducible_scope on offer is
    # the directive's "can authority be reduced?" question made concrete:
    # the gate does not refuse outright, it narrows.
    if not inp.scope_declared_necessary:
        if inp.reducible_scope:
            descend(
                "AUTHORIZED_WITH_CONSTRAINTS",
                "Q3/Q4 (scope necessary? can authority be reduced?): "
                "scope_declared_necessary=False, but a reducible_scope "
                "was offered. Authorization, if it happens at all, is "
                "constrained to that narrower scope — never granted at "
                "the originally requested (unjustified) breadth.",
            )
            constraints.append(
                f"scope constrained to: {', '.join(inp.reducible_scope)}"
            )
        else:
            descend(
                "REQUIRES_HUMAN_REVIEW",
                "Q3/Q4 (scope necessary? can authority be reduced?): "
                "scope_declared_necessary=False and no reducible_scope "
                "was offered — there is no narrower grant available to "
                "fall back to, so this is routed to a human rather than "
                "refused outright (the requester may simply need to "
                "resubmit with a justified or reduced scope).",
            )

    # --- Q5: "Does any evidence contradict this request?" ----------------
    # Judgment call documented in the module docstring above. No default
    # softer path (AUTHORIZED_WITH_CONSTRAINTS) is used here on purpose:
    # a named contradiction is a factual conflict, not a breadth-of-grant
    # problem, so narrowing scope does not address it.
    if inp.contradictory_evidence:
        descend(
            "REQUIRES_HUMAN_REVIEW",
            "Q5 (contradictory evidence?): contradictory_evidence is "
            "non-empty: " + "; ".join(inp.contradictory_evidence) + ". "
            "A named contradiction is a factual conflict a human must "
            "resolve — it is never averaged away into a partial grant.",
        )

    # --- Q6: "Is there any supporting evidence for this request at all?" -
    # Mirrors the verdict schema's own evidence-required rule (VD-R-11)
    # at the point of decision, not just at the point of recording it
    # afterward.
    if not inp.supporting_evidence:
        descend(
            "REQUIRES_HUMAN_REVIEW",
            "Q6 (any supporting evidence?): supporting_evidence is "
            "empty. A verdict of AUTHORIZED or AUTHORIZED_WITH_"
            "CONSTRAINTS can never rest on zero supporting evidence — "
            "same rule as the verdict schema's VD-R-11, enforced here at "
            "decision time.",
        )

    # --- Q7: "What is this request's provenance status?" -----------------
    # UNKNOWN/UNVERIFIABLE caps at REQUIRES_HUMAN_REVIEW (not QUARANTINED
    # — provenance UNKNOWN is "we have not yet established it", a weaker
    # claim than provenance actively found INVALID/contaminated, which is
    # firewall/gate.py's QUARANTINED case for artifacts).
    if inp.provenance_status not in _PROVENANCE_STATES:
        # An unrecognised provenance_status value is refused outright,
        # mirroring firewall/gate.py's "unrecognised classification is
        # refused, never defaulted" rule — never silently treated as
        # UNKNOWN.
        descend(
            "REFUSED",
            f"Q7 (provenance status?): unrecognised provenance_status "
            f"{inp.provenance_status!r}. Unrecognised values are refused, "
            f"never defaulted to a permissive interpretation.",
        )
    elif inp.provenance_status in ("UNKNOWN", "UNVERIFIABLE"):
        descend(
            "REQUIRES_HUMAN_REVIEW",
            f"Q7 (provenance status?): provenance_status="
            f"{inp.provenance_status!r} caps the best possible verdict at "
            f"REQUIRES_HUMAN_REVIEW even if every other check passes.",
        )

    # --- Q8: "Is delegation involved, and if so, on what identity?" ------
    # Delegated requests inherit every constraint identity/authority
    # already impose; delegation itself adds no new permissiveness. This
    # question exists to make explicit that delegation is not a bypass —
    # it is evaluated over the SAME identity_verified/authority fields
    # already checked in Q1/Q2, so no additional branch is needed beyond
    # naming the fact for the audit trail.
    if inp.delegation:
        reasons.append(
            "Q8 (delegation involved?): delegation=True. Delegation does "
            "not grant any authority beyond what Q1/Q2 already "
            "established for the underlying identity — a delegated "
            "request with unverified identity is still capped at "
            "REQUIRES_HUMAN_REVIEW by Q1, not bypassed by delegation."
        )

    # --- Q9: "Is this request reversible if it turns out to be wrong?" ---
    # Recorded for the record and consumed by Q10 below; reversibility on
    # its own does not increase permissiveness (it is not a basis for
    # granting authority, only a mitigating factor once other checks have
    # already passed).
    reasons.append(
        f"Q9 (reversible if wrong?): reversible={inp.reversible}."
    )

    # --- Q10: "Is this high-impact, and if so, is there ANY uncertainty
    #           about identity/authority/provenance?" --------------------
    # The directive's final doctrine, made literal: when in doubt about
    # high-impact authority, do not escalate past REQUIRES_HUMAN_REVIEW —
    # constrain, preserve, explain, return the decision to a human.
    if inp.high_impact:
        uncertain_about: list[str] = []
        if not inp.identity_verified:
            uncertain_about.append("identity")
        if not inp.authority_asserted or not inp.authority_evidence:
            uncertain_about.append("authority")
        if inp.provenance_status in ("UNKNOWN", "UNVERIFIABLE"):
            uncertain_about.append("provenance")
        if uncertain_about:
            descend(
                "REQUIRES_HUMAN_REVIEW",
                "Q10 (high-impact + any uncertainty?): high_impact=True "
                "and uncertainty exists about: " + ", ".join(uncertain_about) +
                ". A high-impact request under any such uncertainty is "
                "capped at REQUIRES_HUMAN_REVIEW at most — never "
                "escalated past it on the strength of other fields.",
            )
        elif not inp.reversible:
            # High-impact, fully certain on identity/authority/provenance,
            # but irreversible if wrong: still not a blank AUTHORIZED —
            # constrained at most, so a human-legible record of the
            # irreversibility exists even on the successful path.
            descend(
                "AUTHORIZED_WITH_CONSTRAINTS",
                "Q10 (high-impact + reversible?): high_impact=True and "
                "reversible=False, but no uncertainty about identity/"
                "authority/provenance. Authorization proceeds but is "
                "constrained — an irreversible high-impact action is "
                "never granted unconditionally even when everything else "
                "checks out.",
            )
            constraints.append(
                "high-impact and irreversible: proceed only with "
                "additional monitoring/rollback-preparation in place"
            )

    # --- Q11: "Is the requested duration bounded?" ------------------------
    # An unbounded or empty duration on an otherwise-authorizable request
    # is treated the same way as an unjustified scope (Q3/Q4): it does
    # not refuse the request, but it cannot be granted unconditionally.
    if not inp.duration or not inp.duration.strip():
        descend(
            "AUTHORIZED_WITH_CONSTRAINTS",
            "Q11 (duration bounded?): duration is empty/unbounded. An "
            "unbounded grant is never issued unconditionally — a default "
            "bound is imposed as a constraint.",
        )
        constraints.append("duration bounded to system default (unspecified duration)")

    # --- Q12: "Given everything above, what is the single best-supported
    #           verdict, and can it be stated with a reversal and review
    #           path?" ----------------------------------------------------
    # This is the terminal synthesis question — by this point `verdict`
    # already reflects every prior cap. Q12 exists to record that the
    # gate reasoned to a stated conclusion rather than merely accumulating
    # flags, mirroring firewall/gate.py's final "AUTHORIZED" block noting
    # explicitly what did and did not contribute.
    if verdict == "AUTHORIZED":
        reasons.append(
            "Q12 (final verdict): identity verified, authority asserted "
            "and evidenced, scope declared necessary, no contradictory "
            "evidence, supporting evidence present, provenance verified "
            "or claimed, duration bounded — AUTHORIZED without "
            "constraints."
        )
    else:
        reasons.append(f"Q12 (final verdict): {verdict}.")

    return GateDecision(verdict=verdict, request_id=inp.request_id,
                         reasons=reasons, constraints=constraints)
