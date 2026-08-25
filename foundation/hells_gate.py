"""
Hell's Gate — the general admission boundary (TITANOS_HELLS_GATE.md).

WHAT THIS FILE IS

The front door. Anything entering this repository's canonical
core — code, blueprints, prompts, agent instructions, documents,
external knowledge, contributions, automation proposals, governance
rules, self-modification proposals, agent outputs — passes through
`evaluate()` first. It answers exactly one question per artifact: ADMIT,
QUARANTINE, REJECT, or HUMAN_REVIEW_REQUIRED. It never answers "is this
true," "is this good," or "is this trusted" — those are different
questions this module structurally refuses to answer (see Gate 5 and the
final-decision vocabulary below).

DEFAULT IS QUARANTINE, NOT ADMIT

Every gate that cannot positively establish safety pushes the outcome
away from ADMIT, never toward it. An artifact with every field left at
its default (unknown purpose, no provenance, no beneficiary) evaluates to
QUARANTINE, not ADMIT — proven by test, not asserted.

WHAT THIS FILE REUSES, NOT DUPLICATES

- CT_141 (Gate 6): imports `foundation.flow_switch.detect_panic` rather
  than re-deriving the panic axiom a second time.
- Containment: an artifact resolving to QUARANTINE is actually contained
  via `firewall.quarantine.QuarantineStore` — the same append-only,
  no-delete, reviewed-by-required mechanism already built and tested.
  This module does not build a second quarantine store.
- Publication specifically remains `foundation.publication_gate`'s
  authority — Hell's Gate is the general front door an artifact passes
  through first; a publication-shaped artifact that reaches ADMIT here
  still has to separately clear `publication_gate.authorize_publish()`
  before an actual push happens. Hell's Gate does not shortcut that.

WHY "ADMITTED_UNDER_CURRENT_EVIDENCE" AND NEVER "TRUSTED"

The doctrine is explicit: this gate must never output the word "TRUSTED."
Every admission stays challengeable, versioned, auditable — "trusted" is
a closed, static claim; "admitted under current evidence" is an open,
revisable one. `HellsGateState.ADMIT`'s string value is literally
`"ADMITTED_UNDER_CURRENT_EVIDENCE"`, not `"ADMIT"` alone, so the word
itself is unavoidable in any serialized output.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from foundation.flow_switch import PanicSample, detect_panic  # noqa: E402

__all__ = [
    "HellsGateArtifact", "GateFinding", "HellsGateDecision", "DeltaVeto",
    "evaluate", "quarantine_artifact", "TRUSTED_FORBIDDEN_STRING",
]

TRUSTED_FORBIDDEN_STRING = "TRUSTED"

STATE_ADMIT = "ADMITTED_UNDER_CURRENT_EVIDENCE"
STATE_QUARANTINE = "QUARANTINE"
STATE_REJECT = "REJECT"
STATE_HUMAN_REVIEW = "HUMAN_REVIEW_REQUIRED"

# Severity order — the final state is the MOST severe finding, never the
# least. REJECT beats HUMAN_REVIEW_REQUIRED beats QUARANTINE beats ADMIT.
_SEVERITY = {STATE_REJECT: 3, STATE_HUMAN_REVIEW: 2, STATE_QUARANTINE: 1, STATE_ADMIT: 0}


@dataclass(frozen=True)
class HellsGateArtifact:
    """Declared facts about one artifact seeking admission. Every field
    is caller-declared, same boundary every gate in this codebase holds:
    this module checks consistency of declared evidence, it does not go
    verify the artifact's actual behaviour itself."""

    artifact_id: str
    artifact_type: str = "UNKNOWN"  # code | blueprint | prompt | document | ...

    # Gate 1 — intent
    stated_purpose: str = ""
    concealed_objective_signals: tuple[str, ...] = ()

    # Gate 2 — harm screen
    harm_confirmed: tuple[str, ...] = ()   # credible, confirmed harm categories
    harm_suspected: tuple[str, ...] = ()   # uncertain but non-trivial risk signals

    # Gate 3 — reversibility
    reversible: bool = False
    independently_verified: bool = False

    # Gate 4 — provenance
    source: str = ""
    provenance_chain: tuple[str, ...] = ()

    # Gate 5 — capability vs claim
    claimed_capabilities: tuple[str, ...] = ()
    verified_capabilities: tuple[str, ...] = ()

    # Gate 6 — CT_141
    information_velocity: float = 0.0
    verification_velocity: float = 0.0

    # Gate 7 — privilege
    requested_privileges: tuple[str, ...] = ()
    minimum_required_privileges: tuple[str, ...] = ()

    # Gate 8 — Black Ice reflection
    counterarguments_considered: tuple[str, ...] = ()
    criticism_prohibited: bool = False

    # Gate 9 — three-rail (only meaningful for action-proposing artifacts)
    proposes_action: bool = False
    verification_method_stated: bool = False

    # Gate 10 — human beneficiary
    beneficiary: str = ""
    measurable_benefit: str = ""


@dataclass
class GateFinding:
    gate: str
    passed: bool
    severity_if_failed: str  # which state this failure pushes toward
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"gate": self.gate, "passed": self.passed,
                "severity_if_failed": self.severity_if_failed, "detail": self.detail}


@dataclass
class HellsGateDecision:
    artifact_id: str
    state: str = STATE_QUARANTINE  # fail-closed default
    findings: list[GateFinding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"artifact_id": self.artifact_id, "state": self.state,
                "findings": [f.to_dict() for f in self.findings]}


@dataclass(frozen=True)
class DeltaVeto:
    """The four-part structure §"FOUR-AGENT CROSS-EXAMINATION" requires
    for any Delta veto — no vague 'no'. All four fields are required
    non-empty; constructing one with any blank raises."""
    rejection_reason: str
    evidence: str
    counterexample: str
    remediation_path: str

    def __post_init__(self):
        for name, value in (("rejection_reason", self.rejection_reason),
                            ("evidence", self.evidence),
                            ("counterexample", self.counterexample),
                            ("remediation_path", self.remediation_path)):
            if not value.strip():
                raise ValueError(
                    f"DeltaVeto requires a non-empty '{name}' — a veto "
                    f"without this is a vague 'no', which this doctrine "
                    f"forbids: 'NO -> BECAUSE -> HERE IS WHAT MUST CHANGE.'"
                )


def _finding(gate: str, passed: bool, severity: str, detail: str) -> GateFinding:
    return GateFinding(gate=gate, passed=passed, severity_if_failed=severity, detail=detail)


def evaluate(artifact: HellsGateArtifact) -> HellsGateDecision:
    """Run all ten gates. Collects every finding (never stops at the
    first failure, matching magl/composition/engine.py's convention —
    an operator deciding how to fix an artifact needs every reason, not
    just the first the engine happened to trip over). Final state is the
    single most severe finding across all ten gates."""
    findings: list[GateFinding] = []

    # --- Gate 1: INTENT ---------------------------------------------------
    if artifact.concealed_objective_signals:
        findings.append(_finding("INTENT", False, STATE_REJECT,
            f"concealed objective signals present: {artifact.concealed_objective_signals}"))
    elif not artifact.stated_purpose.strip():
        findings.append(_finding("INTENT", False, STATE_QUARANTINE,
            "no stated purpose — unknown intent fails closed to quarantine, "
            "per doctrine Gate 1"))
    else:
        findings.append(_finding("INTENT", True, STATE_ADMIT, "purpose stated, no concealment signals"))

    # --- Gate 2: HARM SCREEN ----------------------------------------------
    if artifact.harm_confirmed:
        findings.append(_finding("HARM_SCREEN", False, STATE_REJECT,
            f"confirmed harm categories: {artifact.harm_confirmed}"))
    elif artifact.harm_suspected:
        findings.append(_finding("HARM_SCREEN", False, STATE_HUMAN_REVIEW,
            f"suspected but unconfirmed harm categories: {artifact.harm_suspected}"))
    else:
        findings.append(_finding("HARM_SCREEN", True, STATE_ADMIT, "no harm signals declared"))

    # --- Gate 3: REVERSIBILITY ---------------------------------------------
    if not artifact.reversible and not artifact.independently_verified:
        findings.append(_finding("REVERSIBILITY", False, STATE_HUMAN_REVIEW,
            "unverified AND irreversible = no admission (doctrine Gate 3, "
            "verbatim) — routed to human review, not auto-rejected, since "
            "this reflects insufficient evidence rather than confirmed harm"))
    else:
        findings.append(_finding("REVERSIBILITY", True, STATE_ADMIT,
            "reversible, or irreversible-but-independently-verified"))

    # --- Gate 4: PROVENANCE -------------------------------------------------
    if not artifact.source.strip() and not artifact.provenance_chain:
        findings.append(_finding("PROVENANCE", False, STATE_QUARANTINE,
            "no source and no provenance chain — 'no provenance does not "
            "mean false, it means unverified' (doctrine Gate 4, verbatim)"))
    else:
        findings.append(_finding("PROVENANCE", True, STATE_ADMIT, "source or provenance chain present"))

    # --- Gate 5: CAPABILITY VS CLAIM ----------------------------------------
    overclaimed = set(artifact.claimed_capabilities) - set(artifact.verified_capabilities)
    if overclaimed:
        findings.append(_finding("CAPABILITY_VS_CLAIM", False, STATE_QUARANTINE,
            f"claimed but unverified capabilities: {sorted(overclaimed)} — "
            f"promises are never promoted into capabilities"))
    else:
        findings.append(_finding("CAPABILITY_VS_CLAIM", True, STATE_ADMIT,
            "no claim exceeds verified capability"))

    # --- Gate 6: CT_141 ------------------------------------------------------
    panic = detect_panic(PanicSample(
        information_velocity=artifact.information_velocity,
        verification_velocity=artifact.verification_velocity,
        timestamp="",
    ))
    if panic:
        findings.append(_finding("CT_141", False, STATE_QUARANTINE,
            f"information_velocity ({artifact.information_velocity}) exceeds "
            f"verification_velocity ({artifact.verification_velocity}) — "
            f"throttle, do not expand the attack surface"))
    else:
        findings.append(_finding("CT_141", True, STATE_ADMIT, "verification keeping pace"))

    # --- Gate 7: PRIVILEGE ----------------------------------------------------
    excess = set(artifact.requested_privileges) - set(artifact.minimum_required_privileges)
    if excess:
        findings.append(_finding("PRIVILEGE", False, STATE_HUMAN_REVIEW,
            f"requests privileges beyond declared minimum: {sorted(excess)} — "
            f"no agent receives authority merely because it is useful"))
    else:
        findings.append(_finding("PRIVILEGE", True, STATE_ADMIT,
            "requested privileges do not exceed declared minimum"))

    # --- Gate 8: BLACK ICE REFLECTION ------------------------------------------
    if artifact.criticism_prohibited:
        findings.append(_finding("BLACK_ICE_REFLECTION", False, STATE_REJECT,
            "artifact survives only because criticism is prohibited — "
            "doctrine Gate 8 requires REJECT in this case, verbatim"))
    elif not artifact.counterarguments_considered:
        findings.append(_finding("BLACK_ICE_REFLECTION", False, STATE_QUARANTINE,
            "no counterarguments/alternative hypotheses recorded — "
            "reflection was not performed"))
    else:
        findings.append(_finding("BLACK_ICE_REFLECTION", True, STATE_ADMIT,
            "counterarguments considered, criticism not prohibited"))

    # --- Gate 9: THREE-RAIL DOCTRINE --------------------------------------------
    if artifact.proposes_action and not artifact.verification_method_stated:
        findings.append(_finding("THREE_RAIL", False, STATE_HUMAN_REVIEW,
            "artifact proposes action without a stated verification method "
            "— action without verification is cascade risk"))
    else:
        findings.append(_finding("THREE_RAIL", True, STATE_ADMIT,
            "not an action proposal, or verification method stated"))

    # --- Gate 10: HUMAN BENEFICIARY -----------------------------------------------
    if not artifact.beneficiary.strip() or not artifact.measurable_benefit.strip():
        findings.append(_finding("HUMAN_BENEFICIARY", False, STATE_QUARANTINE,
            "no identifiable beneficiary or measurable benefit — do not promote"))
    else:
        findings.append(_finding("HUMAN_BENEFICIARY", True, STATE_ADMIT,
            "beneficiary and measurable benefit both stated"))

    # --- combine: most severe finding wins, never the least ------------------
    worst = STATE_ADMIT
    for f in findings:
        if not f.passed and _SEVERITY[f.severity_if_failed] > _SEVERITY[worst]:
            worst = f.severity_if_failed

    return HellsGateDecision(artifact_id=artifact.artifact_id, state=worst, findings=findings)


def quarantine_artifact(store: Any, decision: HellsGateDecision, *, content: str) -> Any:
    """Actually contain a QUARANTINE-state decision via the real
    firewall.quarantine.QuarantineStore — not a second store. `store` is
    typed Any here rather than imported directly to avoid a hard import
    cycle risk; callers pass a real QuarantineStore instance."""
    if decision.state != STATE_QUARANTINE:
        raise ValueError(
            f"quarantine_artifact() called on a decision with state "
            f"'{decision.state}', not QUARANTINE — only genuinely "
            f"quarantined decisions route through this function."
        )
    reasons = "; ".join(f.detail for f in decision.findings if not f.passed)
    return store.quarantine(
        artifact_id=decision.artifact_id, content=content,
        reason=f"Hell's Gate: {reasons}",
        provenance={"gate": "hells_gate", "findings": [f.to_dict() for f in decision.findings]},
    )
