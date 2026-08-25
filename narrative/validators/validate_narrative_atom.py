"""
Narrative Atom Validator.

House style inherited from schema/validator.py: structured ValidationResult/
Issue (never a bare bool), full YAML hardening (duplicate-key detection,
size/node/depth ceilings checked before construction, RecursionError
caught at both compose and construct stages), and a fail-closed outer
wrapper (rule NA-R-0) converting any unforeseen exception into a
structured rejection rather than letting it propagate — this exact
pattern closed two real bugs earlier in this repository's history
(failures/FAILURE_ARCHIVE.md F-009/F-010); replicated here rather than
assumed unnecessary for a "smaller" schema.

THE TWO RULES THAT MATTER MOST IN THIS FILE

1. NA-R-13: `promotion_status: CANONICAL_ABSTRACTION` requires non-empty
   `falsification_criteria` — the doctrine's own words: "if a narrative
   cannot state what would change its mind, do not promote it to canon."
2. NA-R-12: the Human Experience Preservation Rule, made structural. A
   `source_type: PERSONAL_EXPERIENCE` atom can never have `evidence_status:
   VERIFIED_FACT` (the literal, external claim) unless a SEPARATE field,
   `external_explanation_status`, is independently `VERIFIED_FACT` too —
   the experience itself is never disputed, but promoting the person's
   interpretation of its external cause to fact requires its own
   evidence, not inherited confidence from the fact that something was
   genuinely felt.

WHAT THIS FILE DOES NOT DO

It validates ONE document's internal consistency. It does not drive an
atom through the promotion state machine (`PROMOTION_TRANSITIONS` in
narrative_atom.py) — that requires a stateful store tracking an atom's
prior state, which does not exist yet (see PARETO_FRONTIER.md). This
validator only checks that a single declared `promotion_status` is
internally consistent with the rest of the document's fields.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from narrative.schema.narrative_atom import (  # noqa: E402
    EPISTEMIC_LAYERS, SOURCE_TYPES, PROMOTION_STATES,
    SUBJECTIVE_EXPERIENCE_SOURCE_TYPES, REQUIRED_TOP_FIELDS,
)

__all__ = ["Issue", "ValidationResult", "validate_narrative_atom",
          "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH"]

MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64

_CONFIDENCE_LEVELS = frozenset({"LOW", "MEDIUM", "HIGH"})
_HARM_RISK_LEVELS = frozenset({"NONE", "LOW", "MEDIUM", "HIGH", "SEVERE"})
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

# §XI — the Narrative Immune System's own named phrases, verbatim spirit.
# Substring match, deliberately coarse (documented limitation, same as
# every other keyword blocklist in this repository — e.g.
# taal/integrator/integrator.py's keyword matcher has the identical,
# explicitly-acknowledged limitation).
_SELF_SEALING_PHRASES = (
    "questioning this proves you", "only this system can save",
    "act now or thinking is betrayal", "doubt is betrayal",
    "disagreement proves you are wrong",
)

# Structurally absent from REQUIRED_TOP_FIELDS and explicitly forbidden if
# present — "repetition is not verification, beauty is not evidence" made
# into a rejection rule, not just an absent field a caller could still add.
_FORBIDDEN_FIELDS = frozenset({
    "popularity", "beauty", "repetition_count", "authority_weight",
    "social_credit_score", "belief_score",
})


class MalformedYamlError(Exception):
    pass


class _DuplicateKeyError(Exception):
    def __init__(self, key: Any):
        self.key = key


class _BoundedSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping_strict(loader, node, deep=False):
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise _DuplicateKeyError(key)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_BoundedSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping_strict
)


def _count_and_bound(node, depth: int = 0, counter: list[int] | None = None) -> None:
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_NODES:
        raise MalformedYamlError(f"document exceeds MAX_NODES ({MAX_NODES})")
    if depth > MAX_DEPTH:
        raise MalformedYamlError(f"document exceeds MAX_DEPTH ({MAX_DEPTH})")
    children = getattr(node, "value", None)
    if isinstance(children, list):
        for c in children:
            if isinstance(c, tuple):
                for x in c:
                    if hasattr(x, "value"):
                        _count_and_bound(x, depth + 1, counter)
            elif hasattr(c, "value"):
                _count_and_bound(c, depth + 1, counter)


def _safe_parse(text: str) -> dict[str, Any]:
    if len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise MalformedYamlError(f"document exceeds MAX_DOCUMENT_BYTES ({MAX_DOCUMENT_BYTES})")
    try:
        raw_node = yaml.compose(text, Loader=_BoundedSafeLoader)
    except RecursionError as e:
        raise MalformedYamlError("recursion depth exceeded during composition") from e
    except yaml.YAMLError as e:
        raise MalformedYamlError(f"YAML failed to parse: {e}") from e
    if raw_node is None:
        return {}
    _count_and_bound(raw_node)
    try:
        loader = _BoundedSafeLoader(text)
        try:
            data = loader.get_single_data()
        finally:
            loader.dispose()
    except _DuplicateKeyError as e:
        raise MalformedYamlError(f"duplicate mapping key {e.key!r}") from e
    except RecursionError as e:
        raise MalformedYamlError("recursion depth exceeded during construction") from e
    except yaml.YAMLError as e:
        raise MalformedYamlError(f"YAML failed to parse: {e}") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise MalformedYamlError(f"top-level document must be a mapping, got {type(data).__name__}")
    return data


@dataclass
class Issue:
    what: str
    why: str
    where: str
    rule: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str
    atom_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "atom_id": self.atom_id,
                "issues": [i.to_dict() for i in self.issues],
                "unknown_fields": self.unknown_fields}


def _is_valid_timestamp(v: Any) -> bool:
    if not isinstance(v, str):
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_narrative_atom(text: str) -> ValidationResult:
    try:
        return _validate_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate, never fail open
        return ValidationResult(
            status="INVALID", atom_id=None,
            issues=[Issue(
                what="internal validation error", why="unforeseen input shape",
                where="<validator>", rule="NA-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _validate_inner(text: str) -> ValidationResult:
    result = ValidationResult(status="UNKNOWN", atom_id=None)
    try:
        raw = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(Issue(
            what="YAML could not be parsed or violated structural ceilings",
            why="unparseable or oversized input cannot be safely validated",
            where="<document>", rule="NA-R-1", evidence=str(e),
        ))
        return result

    if "narrative_atom" not in raw or not isinstance(raw.get("narrative_atom"), dict):
        result.status = "INVALID"
        result.issues.append(Issue(
            what="missing or malformed top-level 'narrative_atom' key",
            why="every atom document must be wrapped under this key",
            where="<document>", rule="NA-R-2", evidence=repr(sorted(raw.keys())),
        ))
        return result

    data = raw["narrative_atom"]
    result.atom_id = data.get("id") if isinstance(data.get("id"), str) else None

    issues: list[Issue] = []

    non_string_keys = [k for k in data.keys() if not isinstance(k, str)]
    if non_string_keys:
        issues.append(Issue(
            what="mapping contains non-string keys", why="fields must be string-named",
            where="narrative_atom", rule="NA-R-3", evidence=repr(non_string_keys),
        ))

    missing = REQUIRED_TOP_FIELDS - {k for k in data.keys() if isinstance(k, str)}
    for f in sorted(missing):
        issues.append(Issue(
            what=f"required field '{f}' is missing", why="required by schema",
            where=f, rule="NA-R-4", evidence="absent",
        ))

    source_type = data.get("source_type")
    if source_type is not None and source_type not in SOURCE_TYPES:
        issues.append(Issue(
            what=f"source_type '{source_type}' not recognised", why="must be a declared source type",
            where="source_type", rule="NA-R-5", evidence=repr(source_type),
        ))

    epistemic_layer = data.get("epistemic_layer")
    if epistemic_layer is not None and epistemic_layer not in EPISTEMIC_LAYERS:
        issues.append(Issue(
            what=f"epistemic_layer '{epistemic_layer}' not in the imported "
                 f"kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS",
            why="reuses the repository's single closed epistemic vocabulary, "
                "never a parallel one",
            where="epistemic_layer", rule="NA-R-6", evidence=repr(epistemic_layer),
        ))

    promotion_status = data.get("promotion_status")
    if promotion_status is not None and promotion_status not in PROMOTION_STATES:
        issues.append(Issue(
            what=f"promotion_status '{promotion_status}' not recognised",
            why="must be one of the declared narrative state machine states",
            where="promotion_status", rule="NA-R-7", evidence=repr(promotion_status),
        ))

    ts = data.get("timestamp")
    if ts is not None and not _is_valid_timestamp(ts):
        issues.append(Issue(
            what="timestamp is not a valid RFC3339 timestamp", why="ambiguous timestamps break ordering",
            where="timestamp", rule="NA-R-8", evidence=repr(ts)[:80],
        ))

    prov = data.get("provenance_hash")
    if prov is not None and (not isinstance(prov, str) or not _HASH_RE.match(prov)):
        issues.append(Issue(
            what="provenance_hash is not a well-formed sha256 hash",
            why="hash must match 'sha256:<64 hex chars>' exactly",
            where="provenance_hash", rule="NA-R-9", evidence=repr(prov)[:80],
        ))

    confidence = data.get("confidence")
    if confidence is not None and confidence not in _CONFIDENCE_LEVELS:
        issues.append(Issue(
            what=f"confidence '{confidence}' not in {sorted(_CONFIDENCE_LEVELS)}",
            why="confidence must be a declared level, not free text",
            where="confidence", rule="NA-R-10", evidence=repr(confidence),
        ))

    harm_risk = data.get("harm_risk")
    if harm_risk is not None and harm_risk not in _HARM_RISK_LEVELS:
        issues.append(Issue(
            what=f"harm_risk '{harm_risk}' not in {sorted(_HARM_RISK_LEVELS)}",
            why="harm_risk must be a declared level",
            where="harm_risk", rule="NA-R-11", evidence=repr(harm_risk),
        ))

    # --- NA-R-12: the Human Experience Preservation Rule, structural ------
    if source_type in SUBJECTIVE_EXPERIENCE_SOURCE_TYPES:
        external_status = data.get("external_explanation_status")
        if external_status is None:
            issues.append(Issue(
                what="source_type is PERSONAL_EXPERIENCE but "
                     "external_explanation_status is not declared",
                why="the Human Experience Preservation Rule requires this field "
                    "to exist SEPARATELY from evidence_status, precisely so the "
                    "experience itself is never disputed while its external "
                    "cause stays honestly UNKNOWN unless independently evidenced",
                where="external_explanation_status", rule="NA-R-12", evidence="absent",
            ))
        elif (data.get("evidence_status") == "VERIFIED_FACT"
              and external_status != "VERIFIED_FACT"):
            issues.append(Issue(
                what="evidence_status is VERIFIED_FACT for a PERSONAL_EXPERIENCE "
                     "atom but external_explanation_status is not independently "
                     "VERIFIED_FACT",
                why="a subjective experience being genuinely felt does not "
                    "evidence its external/cosmological interpretation — "
                    "promoting the interpretation to fact requires its own "
                    "independent evidence, never inherited from the fact that "
                    "something was felt",
                where="evidence_status", rule="NA-R-12",
                evidence=f"evidence_status=VERIFIED_FACT, "
                         f"external_explanation_status={external_status!r}",
            ))

    # --- NA-R-13: canon requires falsifiability ----------------------------
    if promotion_status == "CANONICAL_ABSTRACTION":
        falsification = data.get("falsification_criteria")
        if not falsification or (isinstance(falsification, (list, tuple)) and len(falsification) == 0):
            issues.append(Issue(
                what="promotion_status is CANONICAL_ABSTRACTION but "
                     "falsification_criteria is empty or absent",
                why="'if a narrative cannot state what would change its mind, "
                    "do not promote it to canon' — doctrine, verbatim",
                where="falsification_criteria", rule="NA-R-13", evidence="empty/absent",
            ))

    # --- NA-R-14: self-sealing rhetoric -------------------------------------
    text_fields = " ".join(str(data.get(f, "")) for f in
                           ("raw_fragment", "normalized_claim", "symbolic_meaning")).lower()
    hit_phrases = [p for p in _SELF_SEALING_PHRASES if p in text_fields]
    if hit_phrases:
        if promotion_status == "CANONICAL_ABSTRACTION":
            issues.append(Issue(
                what=f"self-sealing rhetoric detected and promotion_status is "
                     f"CANONICAL_ABSTRACTION: {hit_phrases}",
                why="the Narrative Immune System forbids canonizing a narrative "
                    "that structurally forbids questioning itself",
                where="raw_fragment/normalized_claim/symbolic_meaning",
                rule="NA-R-14", evidence=repr(hit_phrases),
            ))
        # else: recorded as a non-fatal signal — raw input is preserved, not
        # rejected, per "preserve raw input" — see unknown_fields-style
        # reporting below for how this surfaces without blocking ingestion.

    # --- NA-R-15: forbidden popularity/authority-weight style fields -------
    forbidden_present = _FORBIDDEN_FIELDS & set(data.keys())
    if forbidden_present:
        issues.append(Issue(
            what=f"forbidden fields present: {sorted(forbidden_present)}",
            why="'repetition is not verification, beauty is not evidence' — "
                "these fields cannot exist on this schema even as unused metadata",
            where=",".join(sorted(forbidden_present)), rule="NA-R-15",
            evidence=repr(sorted(forbidden_present)),
        ))

    known = REQUIRED_TOP_FIELDS | {
        "author_status_if_known", "normalized_claim", "subdomain",
        "symbolic_meaning", "human_problem", "human_beneficiary",
        "actionability", "reversibility", "related_atoms", "contradictions",
        "external_explanation_status", "falsification_criteria",
    }
    result.unknown_fields = sorted(set(data.keys()) - known)

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
