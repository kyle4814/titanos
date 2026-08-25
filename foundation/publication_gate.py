"""
Publication Gate — the first §2 critical function hard-gated under
TITANOS_CRITICAL_FUNCTION_SWITCH_GATE.md.

WHY THIS FILE EXISTS RIGHT NOW, NOT HYPOTHETICALLY

This repository is being prepared for actual GitHub publication (see
legacy/DECISION_PACKET.md's redaction note, LICENSE, README.md). Until
this file existed, the only thing standing between "prepare the repo"
and "push it publicly" was an assistant remembering to ask first — a
reminder, not a mechanism. The Switch-Gate doctrine's own core principle
is that this is not good enough: "an instruction can be ignored, diluted,
overwritten, or lost in context." This closes that gap for the one
critical function that was actually about to matter.

THE SWITCH MODEL, LITERALLY

    {
        "armed": false,
        "trigger_verified": false,
        "gates_passed": false,
        "human_review_required": false,
        "action_permitted": false,
    }

Every field starts at the fail-closed value. `action_permitted` can only
become True if every required piece of evidence is present AND a human
has explicitly named the publication target — never inferred, never
defaulted from "looks ready."

TWO-POINT ENFORCEMENT (§5)

Point one: `evaluate()` computes the switch from declared evidence.
Point two: `authorize_publish()` does NOT trust a cached `action_permitted`
flag from a `PublicationSwitch` object a caller hands it — it re-derives
the answer from the switch's own recorded evidence fields, the same
"verify from the record, not the label" discipline used in
`taal/gate/human_jurisdiction.py::confirm_pilot_authorized()`. A caller
cannot construct a `PublicationSwitch(action_permitted=True, ...)` by
hand with everything else blank and expect `authorize_publish()` to honour
it — the flag is advisory only; the evidence fields are load-bearing.

WHAT THIS FILE DOES NOT DO

It does not run `git push`. It does not touch the network. It answers
exactly one question — "is publication currently authorized" — and
nothing calls a real push based on its answer without a human separately
executing that step. This is a decision gate, not an execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "PublicationSwitch", "PublicationDecision", "evaluate", "authorize_publish",
    "PublicationRefused",
]


class PublicationRefused(Exception):
    """Raised by authorize_publish() when re-derivation from evidence
    disagrees with the switch's own action_permitted flag, or when
    required evidence is missing. Loud on purpose — a caller that ignores
    this exception has to do so explicitly, not by accident."""


@dataclass(frozen=True)
class PublicationSwitch:
    """Declared evidence for one publication decision. Every field here
    is a CLAIM the caller makes; this module does not go verify secret
    scans or read LICENSE files itself — that boundary is the same one
    every validator in this codebase holds (checks shape/consistency of
    DECLARED fields, does not manufacture them). The honesty of the
    inputs is outside this module's power to enforce, same as
    foundation/switch_hardener.py's run_hardening_gates()."""

    target_repo: str = ""                    # e.g. "github.com/org/repo" — required
    secret_scan_passed: bool = False
    secret_scan_evidence: str = ""            # required if secret_scan_passed
    license_present: bool = False
    readme_present: bool = False
    classification: str = "UNKNOWN"           # "PUBLIC" | "PRIVATE_CORE" | "UNKNOWN"
    human_authorized_by: str = ""             # required non-empty — a name, not a bool
    human_authorization_note: str = ""        # what exactly was authorized (e.g. target+visibility)
    reversibility_acknowledged: bool = False  # public exposure is not fully reversible; must be
                                              # explicitly acknowledged, never assumed
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PublicationDecision:
    armed: bool = False
    trigger_verified: bool = False
    gates_passed: bool = False
    human_review_required: bool = True
    action_permitted: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "armed": self.armed, "trigger_verified": self.trigger_verified,
            "gates_passed": self.gates_passed,
            "human_review_required": self.human_review_required,
            "action_permitted": self.action_permitted,
            "reasons": list(self.reasons),
        }


def evaluate(switch: PublicationSwitch) -> PublicationDecision:
    """Point one of two-point enforcement (§5). Fail-closed throughout:
    every gate must be explicitly satisfied, never assumed from silence.

    IF ANY REQUIRED CONDITION IS UNKNOWN, action_permitted STAYS FALSE.
    This function never returns action_permitted=True by omission.
    """
    d = PublicationDecision()

    # --- trigger: is there actually a declared target? -------------------
    if not switch.target_repo.strip():
        d.reasons.append("no target_repo declared — publication has no "
                         "destination, there is nothing to authorize")
        return d
    d.trigger_verified = True

    # --- classification: PRIVATE_CORE or UNKNOWN blocks outright ---------
    if switch.classification == "PRIVATE_CORE":
        d.reasons.append("classification is PRIVATE_CORE — this switch "
                         "structurally cannot authorize; per §6's example "
                         "verbatim: publication_switch = LOCKED, "
                         "external_export = DENIED")
        return d
    if switch.classification != "PUBLIC":
        d.reasons.append(f"classification is '{switch.classification}', not "
                         f"PUBLIC — UNKNOWN does not equal permitted")
        return d

    # --- gates: secret scan, license, readme, reversibility ack ----------
    gate_findings: list[str] = []
    if not switch.secret_scan_passed:
        gate_findings.append("secret_scan_passed is False")
    elif not switch.secret_scan_evidence.strip():
        gate_findings.append("secret_scan_passed claimed True but no "
                             "evidence recorded — a claim without evidence "
                             "does not pass this gate")
    if not switch.license_present:
        gate_findings.append("license_present is False")
    if not switch.readme_present:
        gate_findings.append("readme_present is False")
    if not switch.reversibility_acknowledged:
        gate_findings.append("reversibility_acknowledged is False — public "
                             "exposure is not fully reversible and this "
                             "must be explicitly acknowledged, never assumed")

    if gate_findings:
        d.reasons.extend(gate_findings)
        return d
    d.gates_passed = True
    d.armed = True

    # --- human review: always required for this switch, no exception -----
    if not switch.human_authorized_by.strip():
        d.reasons.append("human_review_required is unconditionally True for "
                         "publication — no human_authorized_by name recorded")
        return d
    if not switch.human_authorization_note.strip():
        d.reasons.append("human_authorized_by is present but "
                         "human_authorization_note is empty — an unexplained "
                         "authorization is not distinguishable from a "
                         "forged one; the doctrine requires evidence, not a "
                         "name alone")
        return d
    d.human_review_required = False  # satisfied, not skipped

    d.action_permitted = True
    d.reasons.append(f"all gates passed; authorized by {switch.human_authorized_by}: "
                     f"{switch.human_authorization_note}")
    return d


def authorize_publish(switch: PublicationSwitch) -> bool:
    """Point two of two-point enforcement (§5).

    Does NOT accept a PublicationDecision as input and does NOT trust any
    action_permitted flag a caller might have cached. Re-runs evaluate()
    against the switch's own declared evidence every time, so a caller
    cannot construct a decision object by hand claiming authorization and
    have this function believe it — the only path to True is genuinely
    satisfying every gate in evaluate(), re-derived fresh.

    Raises PublicationRefused (never returns False silently) so a caller
    cannot mistake "didn't check" for "checked and it's fine" — the same
    reasoning as every fail-closed wrapper elsewhere in this codebase.
    """
    decision = evaluate(switch)
    if not decision.action_permitted:
        raise PublicationRefused(
            f"publication to '{switch.target_repo}' is NOT authorized: "
            f"{'; '.join(decision.reasons)}"
        )
    return True
