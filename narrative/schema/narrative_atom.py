"""
Narrative Atom Schema — TITANOS_AKASHIC_NARRATIVE_ENGINE.md §III.

WHY THIS IS THE FIRST THING BUILT, NOT THE FIVE-RECORD MODEL OR THE
ISOMORPHISM CONTRACT

Every other artifact this doctrine describes (the Five Records, the Gold
Ledger, the Isomorphism Engine, the Primary Narrative) operates ON
narrative atoms. Building any of those first would mean designing them
against an atom shape that doesn't exist yet. This is the primitive.

WHAT THIS FILE REUSES, NOT DUPLICATES (per the doctrine's own §XVIII
audit requirement, run before writing this file)

`epistemic_layer` is bound to `kpm.schemas.epistemic_types.
ALL_CLASSIFICATIONS` — the same 15-value closed vocabulary every other
epistemic-status field in this repository uses. The doctrine's Five
Records (Observation/Evidence/Human/Symbolic/Unknown) are a coarser,
narrative-specific grouping layered ON TOP of that finer vocabulary, not
a competing one — see `record_for_epistemic_layer()` below, which maps
one onto the other explicitly rather than requiring two separate fields
that could disagree.

THE ONE RULE THIS FILE EXISTS TO ENFORCE STRUCTURALLY

"AN ATOM NEVER BECOMES CANONICAL MERELY BECAUSE IT IS EMOTIONALLY
POWERFUL, ANCIENT, POPULAR, REPEATED, TECHNICALLY WORDED, SPIRITUALLY
MEANINGFUL, AI-GENERATED, OR AUTHORITY-ASSOCIATED." None of those are
even fields on this schema — there is no `popularity`, `beauty`,
`repetition_count`, or `authority_weight` field anywhere below, and a
test in this package proves promotion never reads unknown/extra fields.
The only path to `CANONICAL_ABSTRACTION` is the state machine in
`promotion_status`, which the validator (a separate module) will check
against the same evidence/falsifiability discipline every other
promotion mechanism in this repository already holds.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import FrozenSet, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS  # noqa: E402

__all__ = [
    "SCHEMA_VERSION", "EPISTEMIC_LAYERS", "SOURCE_TYPES",
    "PROMOTION_STATES", "PROMOTION_TRANSITIONS", "FIVE_RECORDS",
    "RECORD_FOR_EPISTEMIC_LAYER", "REQUIRED_TOP_FIELDS",
    "SUBJECTIVE_EXPERIENCE_SOURCE_TYPES", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# The narrative engine's epistemic_layer is bound to the SAME closed
# vocabulary every other classifier in this repo uses — not redefined.
EPISTEMIC_LAYERS: FrozenSet[str] = ALL_CLASSIFICATIONS

SOURCE_TYPES: FrozenSet[str] = frozenset({
    "CONVERSATION", "SCIENCE", "HISTORY", "PHILOSOPHY", "MYTHOLOGY",
    "PERSONAL_EXPERIENCE", "FAILURE_REPORT", "CONTRADICTION_REPORT",
    "DISCOVERY", "OPEN_QUESTION", "CULTURAL_MEMORY", "TECHNICAL_KNOWLEDGE",
})

SUBJECTIVE_EXPERIENCE_SOURCE_TYPES: FrozenSet[str] = frozenset({
    "PERSONAL_EXPERIENCE",
})

# §XIII — the narrative state machine. Absence of an edge is the
# enforcement, same pattern as every other state machine in this repo
# (firewall/quarantine.py, kpm/promotion/state_machine.py,
# foundation/flow_switch.py). Four terminal branches from CLASSIFIED:
# the normal evidentiary path toward CANONICAL_ABSTRACTION, or a direct
# jump to SYMBOLIC, QUARANTINED, or UNKNOWN — each a legitimate resting
# state, not a failure to be corrected.
PROMOTION_STATES: FrozenSet[str] = frozenset({
    "RAW", "OBSERVED", "CLASSIFIED", "CONNECTED", "CHALLENGED", "TESTED",
    "SUPPORTED", "CANONICAL_ABSTRACTION", "SYMBOLIC", "QUARANTINED", "UNKNOWN",
})

PROMOTION_TRANSITIONS: Mapping[str, FrozenSet[str]] = {
    "RAW":         frozenset({"OBSERVED", "CLASSIFIED"}),
    "OBSERVED":    frozenset({"CLASSIFIED"}),
    "CLASSIFIED":  frozenset({"CONNECTED", "SYMBOLIC", "QUARANTINED", "UNKNOWN"}),
    "CONNECTED":   frozenset({"CHALLENGED", "QUARANTINED", "UNKNOWN"}),
    "CHALLENGED":  frozenset({"TESTED", "QUARANTINED", "UNKNOWN"}),
    "TESTED":      frozenset({"SUPPORTED", "QUARANTINED", "UNKNOWN"}),
    "SUPPORTED":   frozenset({"CANONICAL_ABSTRACTION", "QUARANTINED", "UNKNOWN"}),
    # CANONICAL_ABSTRACTION is not eternal (doctrine, verbatim) — it can
    # be revisited if new contradicting evidence arrives, same
    # discipline as kpm's promotion states allowing STABLE -> DISPUTED.
    "CANONICAL_ABSTRACTION": frozenset({"CHALLENGED", "UNKNOWN"}),
    "SYMBOLIC":    frozenset({"UNKNOWN"}),  # a symbolic reading can be flagged unknown, never silently promoted past
    "QUARANTINED": frozenset({"UNKNOWN", "CLASSIFIED"}),  # re-classification after review, not silent release
    "UNKNOWN":     frozenset({"CLASSIFIED"}),  # the only way out of UNKNOWN is honest re-classification
}


def can_promote(src: str, dst: str) -> bool:
    return dst in PROMOTION_TRANSITIONS.get(src, frozenset())


# §IV — the Five Records. Maps the fine-grained epistemic_layer vocabulary
# onto the doctrine's coarser record grouping, so an atom's record
# membership is DERIVED, never a second field that could disagree with
# epistemic_layer.
FIVE_RECORDS: FrozenSet[str] = frozenset({
    "OBSERVATION", "EVIDENCE", "HUMAN", "SYMBOLIC", "UNKNOWN",
})

RECORD_FOR_EPISTEMIC_LAYER: Mapping[str, str] = {
    "VERIFIED_FACT": "OBSERVATION",
    "EVIDENCE_SUPPORTED_MODEL": "EVIDENCE",
    "IMPLEMENTED_SYSTEM": "EVIDENCE",
    "TECHNICAL_DESIGN": "EVIDENCE",
    "SOFTWARE_REQUIREMENT": "EVIDENCE",
    "POLICY_REQUIREMENT": "EVIDENCE",
    "SCIENTIFIC_CLAIM_REQUIRING_EVIDENCE": "EVIDENCE",
    "HISTORICAL_CLAIM_REQUIRING_EVIDENCE": "EVIDENCE",
    "PERSONAL_EXPERIENCE": "HUMAN",
    "ARCHITECTURAL_METAPHOR": "SYMBOLIC",
    "SYMBOLIC_DOCTRINE": "SYMBOLIC",
    "CREATIVE_CONCEPT": "SYMBOLIC",
    "SPECULATIVE_HYPOTHESIS": "UNKNOWN",
    "UNVERIFIED_EXTERNAL_CLAIM": "UNKNOWN",
    "UNKNOWN": "UNKNOWN",
}


def record_for_epistemic_layer(layer: str) -> str:
    return RECORD_FOR_EPISTEMIC_LAYER.get(layer, "UNKNOWN")


REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "timestamp", "source_reference", "source_type", "raw_fragment",
    "domain", "epistemic_layer", "evidence_status", "confidence",
    "uncertainty", "harm_risk", "provenance_hash", "promotion_status",
})


def schema_hash() -> str:
    payload = {
        "version": SCHEMA_VERSION,
        "epistemic_layers": sorted(EPISTEMIC_LAYERS),
        "source_types": sorted(SOURCE_TYPES),
        "promotion_states": sorted(PROMOTION_STATES),
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()
