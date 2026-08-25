"""
TAAL — TITANOS THREAT INTEGRATOR (directive §9).

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Given a disparate raw signal, what is its canonical shape, and which
     threat_archetype categories might plausibly apply to it?"

It does NOT answer:
    - "Is this an attack?" (that's the root-gate + human review, not built
      here)
    - "What should happen to this entity?" (that's the gate's verdict)
    - "Is this candidate correct?" (a candidate is a hypothesis for
      downstream review, never a finding)

WHY "CANDIDATES", NEVER A CONCLUSION

§9 of the governing directive is explicit: "The integrator must never
claim 'attack detected' without preserving the signals supporting that
conclusion." This module goes one step further and never claims "attack
detected" at all — full stop. `propose_archetype_candidates` returns a
tuple of threat_class CATEGORY NAMES (the same closed vocabulary
taal/schema/threat_archetype.py's THREAT_CLASSES draws from, reproduced
here literally rather than imported — this component and that schema are
a deliberate seam, same pattern as rpa/schema/*.py's free-text _ref
fields). A category name like "PRIVILEGE_ESCALATION_ATTEMPTS" is a
classification bucket, not an assertion that escalation happened. No
conclusory word ("detected", "confirmed", "malicious", "attack") appears
anywhere in this module's return values or log strings — enforced by
taal/integrator/tests/test_integrator.py::TestNeverConclusory, which greps
the actual returned/logged string content.

NEVER SUMMARIZE AWAY raw_facts

`raw_facts` are observations, not conclusions (per RawSignal's own
docstring below). `normalize()` copies every entry into
`NormalizedEvent.signals` verbatim — no truncation, no "top 3", no
deduplication that would drop an entry. Silently dropping an observed
fact is exactly the kind of narrative-collapse §9's sibling files
(firewall/dissent.py, firewall/quarantine.py) exist to prevent one layer
over.

DETERMINISTIC ONLY

`propose_archetype_candidates` is simple keyword/substring matching
against `observed_action`, `affected_resource`, and `signals` — no ML, no
fuzzy scoring, no probability. This mirrors the "simple switches win"
convention used throughout this codebase (see schema/validator.py,
magl/composition/engine.py). An empty tuple is a legitimate output: "no
candidate archetype fits this signal" is normal, not an error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Tuple

__all__ = [
    "RawSignal", "NormalizedEvent", "SOURCE_TYPES", "THREAT_CLASSES",
    "normalize", "propose_archetype_candidates",
]

# ---------------------------------------------------------------------------
# Input shape. Deliberately minimal and locally owned — see module docstring
# on the schema seam. Another agent's normalized_security_event schema may
# validate a superset/variant of this; this module does not import it.
# ---------------------------------------------------------------------------

SOURCE_TYPES = frozenset({
    "APPLICATION_EVENT", "ACCESS_REQUEST", "AI_TOOL_REQUEST",
    "POLICY_VIOLATION", "ANOMALY", "AUDIT_LOG", "HUMAN_REPORT",
    "SECURITY_TELEMETRY",
})


@dataclass(frozen=True)
class RawSignal:
    """A single disparate input to the integrator.

    `raw_facts` must be OBSERVABLE FACTS ONLY — e.g. "3 failed logins in
    10s" — never a conclusion such as "brute force attack". Enforcing the
    wording of caller-supplied strings is out of scope for this dataclass;
    what this module guarantees is that whatever facts arrive here are
    never dropped or rephrased into a conclusion downstream (see
    `normalize`).
    """
    signal_id: str
    source_type: str
    entity: str
    observed_action: str
    affected_resource: str
    raw_facts: Tuple[str, ...] = ()
    timestamp: str = ""


@dataclass(frozen=True)
class NormalizedEvent:
    """Canonical shape produced by `normalize()`.

    Field names loosely mirror what a `normalized_security_event` schema
    would validate, by convention, not by import — see module docstring.
    """
    event_id: str
    source_type: str
    entity: str
    action: str
    resource: str
    signals: Tuple[str, ...] = field(default_factory=tuple)
    normalized_at: str = ""
    original_timestamp: str = ""


def normalize(signal: RawSignal) -> NormalizedEvent:
    """Produce a NormalizedEvent from a RawSignal.

    Hard guarantee: `len(result.signals) == len(signal.raw_facts)` and
    every entry is preserved verbatim, in order. No fact is summarized,
    deduplicated, or dropped. See TestRawFactsNeverDropped.
    """
    return NormalizedEvent(
        event_id=signal.signal_id,
        source_type=signal.source_type,
        entity=signal.entity,
        action=signal.observed_action,
        resource=signal.affected_resource,
        signals=tuple(signal.raw_facts),
        normalized_at=datetime.now(timezone.utc).isoformat(),
        original_timestamp=signal.timestamp,
    )


# ---------------------------------------------------------------------------
# Candidate archetype classes. Reproduced literally from the fixed set the
# directive specifies (matches taal/schema/threat_archetype.py's
# THREAT_CLASSES enum) — not imported, per the deliberate cross-component
# seam described in the module docstring.
# ---------------------------------------------------------------------------

THREAT_CLASSES = frozenset({
    "IDENTITY_DECEPTION",
    "AUTHORIZATION_ABUSE",
    "PRIVILEGE_ESCALATION_ATTEMPTS",
    "DATA_EXFILTRATION_PATTERNS",
    "INTEGRITY_MANIPULATION",
    "UNAUTHORIZED_EXECUTION",
    "PERSISTENCE_RISK",
    "RESOURCE_ABUSE",
    "DEPENDENCY_COMPROMISE",
    "SUPPLY_CHAIN_RISK",
    "SOCIAL_ENGINEERING_RISK",
    "AUTOMATION_ABUSE",
    "AGENT_PERMISSION_DRIFT",
    "CONTEXT_MANIPULATION",
    "PROMPT_INJECTION_RISK",
    "INSIDER_THREAT",
    "AVAILABILITY_DISRUPTION",
    "OBSERVABILITY_EVASION_RISK",
    "TRUST_BOUNDARY_CONFUSION",
    "THIRD_PARTY_DELEGATION_RISK",
})

# Deterministic keyword -> candidate class table. Each rule is a simple
# substring match against the lower-cased haystack (action + resource +
# joined signals). Multiple rules may fire; order in THREAT_CLASSES-sorted
# output is stable (see propose_archetype_candidates).
#
# These are intentionally coarse and over-inclusive on the "candidate"
# side — false positives here cost a human a look; false negatives cost
# nothing being flagged at all. The root-gate (owned by another component)
# is where actual adjudication happens, not here.
_KEYWORD_RULES: tuple[tuple[str, str], ...] = (
    ("impersonat", "IDENTITY_DECEPTION"),
    ("spoof", "IDENTITY_DECEPTION"),
    ("forged credential", "IDENTITY_DECEPTION"),
    ("unauthorized access", "AUTHORIZATION_ABUSE"),
    ("access denied", "AUTHORIZATION_ABUSE"),
    ("without permission", "AUTHORIZATION_ABUSE"),
    ("privilege escalat", "PRIVILEGE_ESCALATION_ATTEMPTS"),
    ("sudo", "PRIVILEGE_ESCALATION_ATTEMPTS"),
    ("elevate", "PRIVILEGE_ESCALATION_ATTEMPTS"),
    ("root access", "PRIVILEGE_ESCALATION_ATTEMPTS"),
    ("exfiltrat", "DATA_EXFILTRATION_PATTERNS"),
    ("bulk download", "DATA_EXFILTRATION_PATTERNS"),
    ("large outbound transfer", "DATA_EXFILTRATION_PATTERNS"),
    ("tamper", "INTEGRITY_MANIPULATION"),
    ("checksum mismatch", "INTEGRITY_MANIPULATION"),
    ("modified without authorization", "INTEGRITY_MANIPULATION"),
    ("unauthorized execution", "UNAUTHORIZED_EXECUTION"),
    ("arbitrary code", "UNAUTHORIZED_EXECUTION"),
    ("remote code execution", "UNAUTHORIZED_EXECUTION"),
    ("cron job added", "PERSISTENCE_RISK"),
    ("startup script", "PERSISTENCE_RISK"),
    ("scheduled task created", "PERSISTENCE_RISK"),
    ("resource exhaustion", "RESOURCE_ABUSE"),
    ("excessive requests", "RESOURCE_ABUSE"),
    ("quota abuse", "RESOURCE_ABUSE"),
    ("dependency compromise", "DEPENDENCY_COMPROMISE"),
    ("malicious package", "DEPENDENCY_COMPROMISE"),
    ("typosquat", "DEPENDENCY_COMPROMISE"),
    ("supply chain", "SUPPLY_CHAIN_RISK"),
    ("build pipeline modified", "SUPPLY_CHAIN_RISK"),
    ("phishing", "SOCIAL_ENGINEERING_RISK"),
    ("pretext", "SOCIAL_ENGINEERING_RISK"),
    ("social engineering", "SOCIAL_ENGINEERING_RISK"),
    ("automation abuse", "AUTOMATION_ABUSE"),
    ("bot loop", "AUTOMATION_ABUSE"),
    ("scripted abuse", "AUTOMATION_ABUSE"),
    ("agent permission drift", "AGENT_PERMISSION_DRIFT"),
    ("scope creep", "AGENT_PERMISSION_DRIFT"),
    ("permission drift", "AGENT_PERMISSION_DRIFT"),
    ("context manipulation", "CONTEXT_MANIPULATION"),
    ("context poison", "CONTEXT_MANIPULATION"),
    ("prompt injection", "PROMPT_INJECTION_RISK"),
    ("ignore previous instructions", "PROMPT_INJECTION_RISK"),
    ("jailbreak", "PROMPT_INJECTION_RISK"),
    ("insider", "INSIDER_THREAT"),
    ("disgruntled employee", "INSIDER_THREAT"),
    ("denial of service", "AVAILABILITY_DISRUPTION"),
    ("service unavailable", "AVAILABILITY_DISRUPTION"),
    ("outage caused by", "AVAILABILITY_DISRUPTION"),
    ("log tampering", "OBSERVABILITY_EVASION_RISK"),
    ("disabled logging", "OBSERVABILITY_EVASION_RISK"),
    ("cleared audit trail", "OBSERVABILITY_EVASION_RISK"),
    ("trust boundary", "TRUST_BOUNDARY_CONFUSION"),
    ("cross-tenant", "TRUST_BOUNDARY_CONFUSION"),
    ("third-party delegation", "THIRD_PARTY_DELEGATION_RISK"),
    ("delegated to external", "THIRD_PARTY_DELEGATION_RISK"),
    ("subcontractor access", "THIRD_PARTY_DELEGATION_RISK"),
)


def propose_archetype_candidates(event: NormalizedEvent) -> Tuple[str, ...]:
    """Deterministic keyword match producing candidate threat_class labels.

    Returns a tuple of category names from THREAT_CLASSES, sorted for
    stable output, possibly EMPTY. This is a proposal for human/root-gate
    review, never a verdict. Never returns or logs a conclusory word
    ("detected", "confirmed", "malicious", "attack") — only classification
    category names, which are labels, not claims.
    """
    haystack = " ".join(
        [event.action, event.resource, *event.signals]
    ).lower()

    hits: set[str] = set()
    for keyword, threat_class in _KEYWORD_RULES:
        if keyword in haystack:
            hits.add(threat_class)

    return tuple(sorted(hits))
