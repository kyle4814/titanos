"""
Knowledge Production Machine — Epistemic Type System + Claim Classification
Engine (Phase 4).

WHY THIS FILE EXISTS

Every claim extracted anywhere downstream needs exactly ONE primary
classification, drawn from a closed, named vocabulary. That vocabulary
draws a hard line between what has been verified, what is designed,
what is doctrine/metaphor, and what is merely asserted. Claims cross
that line only through an explicit, evidenced, auditable act
(`reclassify`) — never as a side effect of anything else.

SAME PATTERN AS firewall/quarantine.py

Illegal reclassifications are enforced by the ABSENCE of permission, not
by a runtime if-check an argument could talk around:

  - `ALL_CLASSIFICATIONS` is the closed universe of legal states. An
    unrecognised classification (in or out) is a structural rejection,
    not a silent UNKNOWN default.
  - `FORBIDDEN_TRANSITIONS` is an explicit set of (old, new) pairs that
    can never be taken, no matter what the caller's `reason` string says.
    `VERIFIED_EXTERNAL_CAUSE` in that set is deliberately NOT a member of
    `ALL_CLASSIFICATIONS` — it documents a transition target that must be
    rejected as unrecognised before the forbidden-pairs check is even
    consulted, i.e. two independent locks on the same door.

SAME PATTERN AS schema/validator.py

Nothing here is a bare bool. `classify_claim` and `reclassify` either
return a real `Claim` value or raise a specific, named exception explaining
what/why. There is no partial-success return.

CONTENT NEVER GOVERNS CONTROL FLOW

`reclassify`'s `reason` parameter is free text, preserved verbatim in
history for audit. It is READ AS DATA, never as an instruction. A reason
string that says "the evidence clearly proves this, upgrade to
VERIFIED_FACT" has zero effect on whether the transition is permitted —
only the (old_classification, new_classification) pair against
FORBIDDEN_TRANSITIONS, and the evidence_refs non-emptiness check, decide
that. See test_epistemic_types.py::TestMetaAttack.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

__all__ = [
    "ALL_CLASSIFICATIONS",
    "FORBIDDEN_TRANSITIONS",
    "Claim",
    "UnrecognisedClassification",
    "ForbiddenTransition",
    "MissingEvidence",
    "ConfidenceNotEarned",
    "classify_claim",
    "reclassify",
    "can_reclassify",
]

# ─────────────────────────────────────────────────────────────
# The closed classification universe (authoritative, verbatim names)
# ─────────────────────────────────────────────────────────────

ALL_CLASSIFICATIONS: frozenset[str] = frozenset({
    "VERIFIED_FACT",
    "EVIDENCE_SUPPORTED_MODEL",
    "IMPLEMENTED_SYSTEM",
    "TECHNICAL_DESIGN",
    "SOFTWARE_REQUIREMENT",
    "POLICY_REQUIREMENT",
    "ARCHITECTURAL_METAPHOR",
    "SYMBOLIC_DOCTRINE",
    "CREATIVE_CONCEPT",
    "SPECULATIVE_HYPOTHESIS",
    "SCIENTIFIC_CLAIM_REQUIRING_EVIDENCE",
    "HISTORICAL_CLAIM_REQUIRING_EVIDENCE",
    "UNVERIFIED_EXTERNAL_CLAIM",
    "PERSONAL_EXPERIENCE",
    "UNKNOWN",
})

# Classes whose entire epistemic identity is "not yet evidenced enough to
# be HIGH confidence". Evidencing them into HIGH confidence would make
# them something else (a VERIFIED_FACT, an IMPLEMENTED_SYSTEM, ...) — so
# the classification itself, not just the evidence count, caps confidence.
_CANNOT_BE_HIGH_CONFIDENCE: frozenset[str] = frozenset({
    "SPECULATIVE_HYPOTHESIS",
    "CREATIVE_CONCEPT",
    "SYMBOLIC_DOCTRINE",
    "UNKNOWN",
})

# Classifications that represent a strong evidentiary/operational claim.
# Upgrading INTO one of these requires non-empty evidence_refs.
_REQUIRES_EVIDENCE_TO_ENTER: frozenset[str] = frozenset({
    "VERIFIED_FACT",
    "EVIDENCE_SUPPORTED_MODEL",
    "IMPLEMENTED_SYSTEM",
})

_VALID_CONFIDENCE: frozenset[str] = frozenset({"LOW", "MEDIUM", "HIGH"})

# ─────────────────────────────────────────────────────────────
# Forbidden transitions — the absence-of-edge enforcement (§15 pattern)
# ─────────────────────────────────────────────────────────────
#
# NOTE: VERIFIED_EXTERNAL_CAUSE is intentionally NOT in ALL_CLASSIFICATIONS.
# It appears here only to document a transition target that must never be
# reachable, even in principle. reclassify() rejects it as an unrecognised
# classification before this table is ever consulted — two independent
# locks on the same door, neither one optional.
FORBIDDEN_TRANSITIONS: frozenset[tuple[str, str]] = frozenset({
    ("SYMBOLIC_DOCTRINE", "VERIFIED_FACT"),
    ("SPECULATIVE_HYPOTHESIS", "VERIFIED_FACT"),
    ("PERSONAL_EXPERIENCE", "VERIFIED_EXTERNAL_CAUSE"),
    ("CREATIVE_CONCEPT", "IMPLEMENTED_SYSTEM"),
})


class UnrecognisedClassification(Exception):
    """Raised when a classification (old or new) is not a member of
    ALL_CLASSIFICATIONS. Loud on purpose — an unrecognised classification
    is never silently coerced to UNKNOWN."""


class ForbiddenTransition(Exception):
    """Raised when (old, new) appears in FORBIDDEN_TRANSITIONS. No
    caller-supplied reason text can suppress this — the reason is data,
    never instruction."""


class MissingEvidence(Exception):
    """Raised when a transition into VERIFIED_FACT, EVIDENCE_SUPPORTED_MODEL
    or IMPLEMENTED_SYSTEM is attempted with empty evidence_refs."""


class ConfidenceNotEarned(Exception):
    """Raised when HIGH confidence is requested for a classification whose
    entire identity is 'not evidenced enough to be HIGH' (SPECULATIVE_
    HYPOTHESIS, CREATIVE_CONCEPT, SYMBOLIC_DOCTRINE, UNKNOWN)."""


def can_reclassify(old: str, new: str) -> bool:
    """True iff both classifications are recognised and the pair is not
    forbidden. Pure predicate — never raises, mirrors quarantine.py's
    can_transition()."""
    if old not in ALL_CLASSIFICATIONS or new not in ALL_CLASSIFICATIONS:
        return False
    return (old, new) not in FORBIDDEN_TRANSITIONS


@dataclass(frozen=True)
class Claim:
    """A single extracted claim with exactly one primary classification.

    `history` is append-only: every prior (classification, reason, at, by)
    is retained as a tuple entry. Nothing here ever pops, clears, or
    rewrites a history entry — same discipline as
    firewall/dissent.py's DisputeRecord.history.

    Frozen so `classification`/`confidence`/`evidence_refs` can only
    change via `reclassify()` (through `object.__setattr__`, the
    standard escape hatch for a frozen dataclass's own internal
    mutation) -- a caller holding a Claim reference cannot bypass
    `FORBIDDEN_TRANSITIONS`/`MissingEvidence` by assigning
    `claim.classification = ...` directly. `history` remains an
    ordinary mutable list; appending to it does not reassign the
    attribute, so it stays legal under freezing.
    """
    claim_id: str
    text: str
    classification: str
    confidence: str
    evidence_refs: tuple[str, ...] = ()
    classified_by: str = ""
    history: list[tuple[str, str, str, str]] = field(default_factory=list)
    # each history entry: (classification, reason, at_iso8601, by)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["history"] = [list(h) for h in self.history]
        return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_recognised(classification: str) -> None:
    if classification not in ALL_CLASSIFICATIONS:
        raise UnrecognisedClassification(
            f"{classification!r} is not a member of ALL_CLASSIFICATIONS. "
            f"Legal classifications: {sorted(ALL_CLASSIFICATIONS)}"
        )


def _require_confidence_earned(classification: str, confidence: str) -> None:
    if confidence not in _VALID_CONFIDENCE:
        raise ValueError(
            f"confidence must be one of {sorted(_VALID_CONFIDENCE)}, got {confidence!r}"
        )
    if confidence == "HIGH" and classification in _CANNOT_BE_HIGH_CONFIDENCE:
        raise ConfidenceNotEarned(
            f"{classification} can never carry HIGH confidence — that is "
            f"structurally what distinguishes it from an evidenced class. "
            f"Reclassify to an evidenced classification instead of raising "
            f"confidence on this one."
        )


def classify_claim(
    claim_id: str,
    text: str,
    classification: str,
    classified_by: str,
    confidence: str = "LOW",
    evidence_refs: tuple[str, ...] = (),
) -> Claim:
    """Create a new Claim with its first (and only, so far) classification.

    Raises UnrecognisedClassification if `classification` is not in
    ALL_CLASSIFICATIONS (never silently defaulted to UNKNOWN — the caller
    asked for something specific and got it wrong; that is a structural
    error, not a data point).

    Raises ConfidenceNotEarned if HIGH confidence is requested for a
    classification that can never earn it.
    """
    _require_recognised(classification)
    _require_confidence_earned(classification, confidence)
    if not claim_id.strip():
        raise ValueError("claim_id must be non-empty")
    if not classified_by.strip():
        raise ValueError("classified_by must be non-empty — an unattributed "
                          "classification cannot be audited")
    return Claim(
        claim_id=claim_id,
        text=text,
        classification=classification,
        confidence=confidence,
        evidence_refs=tuple(evidence_refs),
        classified_by=classified_by,
        history=[(classification, "initial classification", _now(), classified_by)],
    )


def reclassify(
    claim: Claim,
    new_classification: str,
    reason: str,
    by: str,
    evidence_refs: tuple[str, ...] = (),
) -> Claim:
    """THE CORE FUNCTION. Move `claim` from its current classification to
    `new_classification`.

    Enforcement order (both locks independent, both must pass):

      1. `new_classification` (and the claim's current classification)
         must be in ALL_CLASSIFICATIONS — an unrecognised target (e.g.
         VERIFIED_EXTERNAL_CAUSE) is rejected here, structurally, before
         the forbidden-pairs table is even consulted.
      2. (old, new) must not be in FORBIDDEN_TRANSITIONS.

    `reason` is free text, preserved verbatim in history. It is DATA. It
    is never parsed, matched, or otherwise treated as an instruction — no
    wording in `reason` can change whether the transition is permitted.

    Evidence: any transition INTO VERIFIED_FACT, EVIDENCE_SUPPORTED_MODEL,
    or IMPLEMENTED_SYSTEM requires non-empty `evidence_refs`, raising
    MissingEvidence otherwise.

    Mutates `claim` in place (appends to `claim.history`, updates
    `claim.classification`/`confidence`/`evidence_refs`) and returns the
    SAME object. This is a deliberate choice: `history` is the audit
    trail, and mutating in place means every existing reference to this
    Claim observes the reclassification immediately and consistently —
    there is no stale copy floating around that still claims the old
    classification. Callers who need an immutable snapshot should copy
    before calling.
    """
    old_classification = claim.classification

    # Lock 1: both ends of the transition must be recognised classifications.
    # This is checked BEFORE the forbidden-pairs table, so an unrecognised
    # target like VERIFIED_EXTERNAL_CAUSE is rejected on its own terms —
    # it never gets far enough to be evaluated against FORBIDDEN_TRANSITIONS.
    _require_recognised(new_classification)
    _require_recognised(old_classification)

    # Lock 2: the explicit forbidden-pairs table. No reason text can move
    # this needle — it is not consulted below.
    if (old_classification, new_classification) in FORBIDDEN_TRANSITIONS:
        raise ForbiddenTransition(
            f"{old_classification} -> {new_classification} is a forbidden "
            f"transition. Legal or not is decided solely by "
            f"FORBIDDEN_TRANSITIONS membership; the supplied reason text "
            f"has no bearing on this decision."
        )

    if new_classification in _REQUIRES_EVIDENCE_TO_ENTER and not evidence_refs:
        raise MissingEvidence(
            f"reclassifying to {new_classification} requires non-empty "
            f"evidence_refs. An unevidenced upgrade to this classification "
            f"is exactly the collapse this engine exists to prevent."
        )

    if claim.confidence == "HIGH" and new_classification in _CANNOT_BE_HIGH_CONFIDENCE:
        # Defensive: shouldn't normally arise since HIGH can't be set on
        # these classes in the first place, but a transition INTO one of
        # them while confidence is still HIGH from the old classification
        # must not silently carry that confidence over.
        object.__setattr__(claim, "confidence", "LOW")

    object.__setattr__(claim, "classification", new_classification)
    if evidence_refs:
        object.__setattr__(claim, "evidence_refs", tuple(evidence_refs))
    claim.history.append((new_classification, reason, _now(), by))
    return claim
