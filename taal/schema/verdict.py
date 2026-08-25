"""
Verdict Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a `verdict` YAML
document may declare — taal/'s counterpart to
taal/schema/permission_request.py and magl/schema/magl_schema.py. Same
discipline: this module is data (field names, enum universes,
required-field tables), never behaviour. All behaviour lives in
taal/validators/validate_verdict.py.

WHAT A VERDICT IS, AND WHAT IT IS NOT

A `permission_request` is the ASK. A `verdict` is the ANSWER — the
structured output of a root-gate decision (taal/gate/root_gate.py) about
either a permission_request or a normalized_security_event. It is never a
bare label. `decision: AUTHORIZED` on its own, with nothing else, is
exactly the unaccountable-authority pattern this codebase's doctrine
exists to forbid — an authority that says yes or no without saying why,
without saying how it could be wrong, and without saying how to undo it.

Every verdict this schema accepts carries, structurally, not just what
was decided but WHY (`why`), WHAT WAS SEEN (`evidence`), WHAT WASN'T KNOWN
(`unknown_factors`), WHAT ELSE COULD EXPLAIN IT (`alternative_explanations`),
WHAT TO DO NEXT (`recommended_action`), HOW TO UNDO IT IF WRONG
(`reversal_path`), and HOW TO CHALLENGE IT (`review_path`). A verdict
missing any of these is not a lesser verdict — it is a structurally
invalid one, rejected the same way an artifact_schema document missing
required fields is rejected.

THE LOAD-BEARING RULE (VD-R-11)

A `decision` of AUTHORIZED or AUTHORIZED_WITH_CONSTRAINTS combined with an
empty `evidence` list is INVALID, full stop, regardless of how well-formed
every other field is. This mirrors kpm/schemas/epistemic_types.py's
evidence-required-for-upgrade rule (_REQUIRES_EVIDENCE_TO_ENTER) and
rpa/schema/institutional_bottleneck.py's evidence-required-for-
high-confidence-classification rule — same shape of defect (an
unevidenced escalation of authority), applied here at the point where
authority is actually granted rather than merely classified.

WHY `decision: UNKNOWN` IS NOT A DEFECT

UNKNOWN is a legitimate terminal state, not a failure to decide. A
root-gate that genuinely cannot resolve a request should be ABLE to say
so, structurally, exactly as cleanly as it says AUTHORIZED — that is what
lets the rest of the system distinguish "we looked and don't know" from
"we didn't look". A verdict with `decision: UNKNOWN` and every other
required field present and non-empty validates as VALID. Nothing in this
schema, or in the validator built on top of it, ever treats
`decision: UNKNOWN` as equivalent to, or a stepping-stone toward,
AUTHORIZED — see the validator's TestUnknownIsNeverAuthorized test.

WHY `constraints` IS CONDITIONALLY REQUIRED (VD-R-12)

`constraints` exists to carry the actual narrowed scope/duration/etc a
AUTHORIZED_WITH_CONSTRAINTS verdict imposes. A `constraints` list on a
plain AUTHORIZED verdict, or on a REFUSED/QUARANTINED/REQUIRES_HUMAN_
REVIEW/UNKNOWN verdict, is a structural contradiction: it claims the
authority was conditioned on something, while the decision label itself
claims either unconditional grant or no grant at all. Mirrors
magl_schema.py's capability_type/jurisdiction contradiction pattern
(MG-R-11) — the same shape of defect (two fields making incompatible
claims about the same fact), applied here to decision/constraints.

WHY `explanation_tiers.restricted_detection_details` MUST NOT LEAK INTO
`explanation_tiers.public` (VD-R-13)

The governing directive (§10) is explicit: explanation must not expose
sensitive detection logic to an attacker. A verdict that states its
restricted detection reasoning verbatim inside the tier meant for broad
disclosure has defeated the entire purpose of having tiers in the first
place. The validator's check is deliberately naive (literal substring
containment) — see the validator module docstring for why that is the
right amount of cleverness here, not a shortcut.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import FrozenSet, Mapping

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "DECISIONS", "AUTHORIZATION_DECISIONS",
    "REQUIRED_TOP_FIELDS", "REQUIRED_NESTED_PATHS",
    "STRING_FIELDS", "NON_EMPTY_LIST_FIELDS", "OPTIONAL_LIST_FIELDS",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

# The closed universe of verdicts a root-gate may return. Locally
# authored — this is taal's own decision vocabulary, distinct from
# kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS (which classifies
# CLAIMS, not authorization decisions) and from firewall.gate.VERDICTS
# (which classifies ARTIFACTS' runtime eligibility, a narrower and
# differently-shaped question). No redefinition of either — a verdict
# and a claim classification are not the same kind of fact.
DECISIONS: FrozenSet[str] = frozenset({
    "AUTHORIZED",
    "AUTHORIZED_WITH_CONSTRAINTS",
    "REQUIRES_HUMAN_REVIEW",
    "QUARANTINED",
    "REFUSED",
    "UNKNOWN",
})

# Decisions that grant SOME degree of authority. Used by both the
# evidence-required rule (VD-R-11) and the constraints-conditional rule
# (VD-R-12).
AUTHORIZATION_DECISIONS: FrozenSet[str] = frozenset({
    "AUTHORIZED", "AUTHORIZED_WITH_CONSTRAINTS",
})

# ─────────────────────────────────────────────────────────────
# Field groups (top-level `verdict.*` keys)
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({"id", "subject_ref"}))
DECISION = FieldGroup("decision", frozenset({"decision"}))
JUSTIFICATION = FieldGroup("justification", frozenset({
    "why", "evidence", "unknown_factors", "alternative_explanations",
}))
DISPOSITION = FieldGroup("disposition", frozenset({
    "recommended_action", "reversal_path", "review_path",
}))
CONSTRAINTS = FieldGroup("constraints", frozenset({"constraints"}))
EXPLANATION_TIERS = FieldGroup("explanation_tiers", frozenset({"explanation_tiers"}))

ALL_GROUPS = (
    IDENTITY, DECISION, JUSTIFICATION, DISPOSITION, CONSTRAINTS,
    EXPLANATION_TIERS,
)

ALL_TOP_FIELDS: FrozenSet[str] = frozenset(f for g in ALL_GROUPS for f in g.fields)

# Top-level keys required directly under `verdict:`. `constraints` is
# deliberately absent from this set — it is conditionally required (only
# when decision == AUTHORIZED_WITH_CONSTRAINTS), enforced by the
# validator's VD-R-12, not by unconditional presence here.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "subject_ref", "decision", "why", "evidence", "unknown_factors",
    "alternative_explanations", "recommended_action", "reversal_path",
    "review_path", "explanation_tiers",
})

# Dotted paths required within nested sections (checked once the parent
# section itself is confirmed present and is a mapping).
REQUIRED_NESTED_PATHS: Mapping[str, FrozenSet[str]] = {
    "explanation_tiers": frozenset({"public", "operator"}),
}

# Fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "subject_ref", "decision", "recommended_action",
    "reversal_path", "review_path",
})

# List fields required to be present AND non-empty.
NON_EMPTY_LIST_FIELDS: FrozenSet[str] = frozenset({"why", "evidence"})

# List fields required to be present but may be empty.
OPTIONAL_LIST_FIELDS: FrozenSet[str] = frozenset({
    "unknown_factors", "alternative_explanations",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    magl_schema.schema_hash / artifact_schema.schema_hash): a claimed
    verdict schema version should be checkable against what this
    validator actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_nested_paths": {
            k: sorted(v) for k, v in sorted(REQUIRED_NESTED_PATHS.items())
        },
        "decisions": sorted(DECISIONS),
        "authorization_decisions": sorted(AUTHORIZATION_DECISIONS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"verdict-schema-v{SCHEMA_VERSION}"
