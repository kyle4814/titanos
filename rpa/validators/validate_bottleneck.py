"""
Institutional Bottleneck Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this institutional_bottleneck document conform to the declared
     schema, structurally, deterministically, and without executing
     anything it contains?"

It does NOT answer:
    - "Is this actually a bottleneck?" (a human/investigative judgment —
      the epistemic_status field carries how confident the author is,
      this validator only checks that the field is a member of the
      shared closed vocabulary and that evidence accompanies
      high-confidence claims; it never assesses whether the claim is
      TRUE)
    - "Do involved_node_ids actually exist in the referenced system map?"
      (referential integrity against rpa/schema/legacy_system_map.py is a
      deliberately separate concern, owned by a cross-schema linking
      layer this validator does not implement — see the schema module's
      docstring)
    - "Is the recommended_next_step a GOOD investigation?" (only that it
      is not an automation instruction — see BN-R-9)

HARDENING

Same parsing hardening as magl/validators/validate_magl.py, replicated
deliberately rather than imported — each validator in this codebase owns
its own parsing hardening independently (the house pattern): duplicate-
key detection, document-size/node-count/depth ceilings checked BEFORE
full construction, RecursionError caught explicitly during both compose
and construct stages, and a fail-closed outer wrapper converting any
unforeseen exception to a structured INVALID result rather than letting
it propagate. This replicates the fix for failures/FAILURE_ARCHIVE.md
F-009 (uncaught RecursionError on deep alias chains failing OPEN past the
validator) and F-010 (uncaught TypeError on non-string YAML keys found
against real corpus data) — both were real crashes found by adversarial
testing and real-data runs respectively, not by review.

RULE NUMBERING (BN-R-<n>)

  BN-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  BN-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  BN-R-2  top-level 'institutional_bottleneck' key present and a mapping
  BN-R-3  mapping contains only string keys (type-confusion class)
  BN-R-4  required top-level fields present
  BN-R-5  identity string fields (id/system_map_ref/bottleneck_type/
          epistemic_status/recommended_next_step) non-empty where present
  BN-R-6  involved_node_ids is a non-empty list of non-empty strings
  BN-R-7  bottleneck_type is a member of BOTTLENECK_TYPES
  BN-R-8  epistemic_status is a member of
          kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS
  BN-R-9  recommended_next_step contains none of ACTION_VERB_BLOCKLIST
          (case-insensitive whole-word match) — a bottleneck record
          proposes how to learn more, never a direct fix
  BN-R-10 evidence required (non-empty) when epistemic_status is
          VERIFIED_FACT or EVIDENCE_SUPPORTED_MODEL; evidence, if present,
          must be a list of non-empty strings
  BN-R-11 estimated_impact section: required sub-fields present,
          value_at_risk/delay_contribution non-empty strings if present,
          failure_propagation_scope is a list if present
  BN-R-12 assumptions/unknowns are lists (may be empty) when present
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rpa.schema.institutional_bottleneck import (  # noqa: E402
    ACTION_VERB_BLOCKLIST,
    BOTTLENECK_TYPES,
    EPISTEMIC_CLASSIFICATIONS,
    EVIDENCE_REQUIRED_CLASSIFICATIONS,
    REQUIRED_NESTED_PATHS,
    REQUIRED_TOP_FIELDS,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_bottleneck", "MalformedYamlError",
    "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64


class MalformedYamlError(Exception):
    """Raised only for genuinely unparseable (or structurally-over-ceiling)
    input. Never for content we merely disagree with — that is INVALID."""


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
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    bottleneck_id: str | None
    issues: list[Issue] = field(default_factory=list)
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "bottleneck_id": self.bottleneck_id,
            "issues": [i.to_dict() for i in self.issues],
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated from magl/validators/validate_magl.py — house
#  pattern: each validator owns its own parsing hardening independently)
# ─────────────────────────────────────────────────────────────

class _DuplicateKeyError(Exception):
    def __init__(self, key: Any, path: str):
        self.key = key
        self.path = path


class _BoundedSafeLoader(yaml.SafeLoader):
    """SafeLoader only — never yaml.Loader/FullLoader (arbitrary Python
    object construction from tags is a code-execution path disguised as
    data). Extended only to reject duplicate mapping keys and support
    node-count/depth bounding via _count_and_bound below."""


def _construct_mapping_strict(loader: _BoundedSafeLoader, node, deep=False):
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise _DuplicateKeyError(key, getattr(node, "start_mark", "?"))
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
        raise MalformedYamlError(
            f"document exceeds MAX_NODES ({MAX_NODES}) — refused before "
            f"full construction to defeat alias/anchor expansion attacks."
        )
    if depth > MAX_DEPTH:
        raise MalformedYamlError(f"document exceeds MAX_DEPTH ({MAX_DEPTH}) — refused.")
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
        raise MalformedYamlError(
            f"document exceeds MAX_DOCUMENT_BYTES ({MAX_DOCUMENT_BYTES})."
        )
    try:
        # Compose first (structure only) so node count/depth can be bounded
        # BEFORE constructing — this is what stops anchor/alias fan-out
        # ("billion laughs") from ever reaching construction. PyYAML's
        # composer is itself recursive, so a sufficiently deep chain blows
        # the Python call stack before MAX_NODES/MAX_DEPTH gets a chance to
        # run — caught explicitly below, per F-009.
        raw_node = yaml.compose(text, Loader=_BoundedSafeLoader)
    except RecursionError as e:
        raise MalformedYamlError(
            "document exceeds safe recursion depth during composition — "
            "refused before construction (alias/anchor or nesting fan-out)."
        ) from e
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
        raise MalformedYamlError(
            f"duplicate mapping key {e.key!r} at {e.path} — the same field "
            f"declared twice is refused rather than silently resolved by "
            f"'last one wins'."
        ) from e
    except RecursionError as e:
        raise MalformedYamlError(
            "document exceeds safe recursion depth during construction — refused."
        ) from e
    except yaml.YAMLError as e:
        raise MalformedYamlError(f"YAML failed to parse: {e}") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise MalformedYamlError(
            f"top-level YAML document must be a mapping, got {type(data).__name__}."
        )
    return data


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def validate_bottleneck(text: str) -> ValidationResult:
    """Deterministic structural validation of an institutional_bottleneck
    document. Never returns a bare bool, and never raises on real-world
    input — an uncaught exception here would be a fail-OPEN bug in
    whatever calls this. Any unforeseen failure is reported as INVALID
    with rule BN-R-0, never allowed to propagate (fail-closed, mirroring
    magl/validators/validate_magl.py's outer wrapper and the F-009/F-010
    lesson it encodes)."""
    try:
        return _validate_bottleneck_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", bottleneck_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="BN-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


_WORD_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _contains_action_verb(text_value: str) -> list[str]:
    """Case-insensitive whole-word match against ACTION_VERB_BLOCKLIST.
    Content is read as DATA — the field value is scanned for these
    literal words, never executed or otherwise interpreted."""
    hits = []
    lowered = text_value.lower()
    for verb in sorted(ACTION_VERB_BLOCKLIST):
        pattern = _WORD_RE_CACHE.get(verb)
        if pattern is None:
            pattern = re.compile(r"\b" + re.escape(verb) + r"\b")
            _WORD_RE_CACHE[verb] = pattern
        if pattern.search(lowered):
            hits.append(verb)
    return hits


def _validate_bottleneck_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", bottleneck_id=None, original_text=text)

    # --- BN-R-1: parseable + structural ceilings ----------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "BN-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- BN-R-2: top-level wrapper present and a mapping --------------------
    if "institutional_bottleneck" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "BN-R-2", "top-level 'institutional_bottleneck' key is missing",
            "every bottleneck document must be wrapped in a top-level "
            "'institutional_bottleneck:' key",
            "institutional_bottleneck", "absent",
        ))
        return result
    bn = data["institutional_bottleneck"]
    if not isinstance(bn, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "BN-R-2", "'institutional_bottleneck' value is not a mapping",
            "the key must contain a mapping of fields",
            "institutional_bottleneck", f"got {type(bn).__name__}",
        ))
        return result

    # --- BN-R-3: non-string keys (type-confusion class) ----------------------
    non_string_keys = [k for k in bn.keys() if not isinstance(k, str)]
    issues: list[Issue] = []
    if non_string_keys:
        issues.append(_issue(
            "BN-R-3", "institutional_bottleneck mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot be "
            "a declared field",
            "institutional_bottleneck",
            f"key types present: {sorted({type(k).__name__ for k in bn.keys()})}",
        ))

    bottleneck_id = bn.get("id") if isinstance(bn.get("id"), str) else None
    result.bottleneck_id = bottleneck_id

    # --- BN-R-4: required top-level fields ------------------------------------
    missing = REQUIRED_TOP_FIELDS - bn.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "BN-R-4", f"required field 'institutional_bottleneck.{f}' is missing",
            "required by schema", f"institutional_bottleneck.{f}", "absent",
        ))

    # --- BN-R-5: identity string fields non-empty -----------------------------
    for f in sorted(STRING_FIELDS):
        if f in bn and (not isinstance(bn[f], str) or not bn[f].strip()):
            issues.append(_issue(
                "BN-R-5", f"field 'institutional_bottleneck.{f}' must be a "
                "non-empty string",
                "identity/classification fields cannot be blank or non-string",
                f"institutional_bottleneck.{f}", bn.get(f),
            ))

    # --- BN-R-6: involved_node_ids non-empty list of non-empty strings -------
    involved = bn.get("involved_node_ids")
    if "involved_node_ids" in bn:
        if not isinstance(involved, list) or not involved:
            issues.append(_issue(
                "BN-R-6", "field 'institutional_bottleneck.involved_node_ids' "
                "must be a non-empty list",
                "a bottleneck claim naming zero architecture points is "
                "structurally empty — referential integrity against the "
                "system map is a separate concern this validator does not "
                "check, but list-shape and non-emptiness are",
                "institutional_bottleneck.involved_node_ids", involved,
            ))
        else:
            bad = [n for n in involved if not isinstance(n, str) or not n.strip()]
            if bad:
                issues.append(_issue(
                    "BN-R-6", "entry in 'involved_node_ids' is not a "
                    "non-empty string",
                    "each entry is a plain node id reference; a blank or "
                    "non-string entry cannot be a reference to anything",
                    "institutional_bottleneck.involved_node_ids", bad,
                ))

    # --- BN-R-7: bottleneck_type enum -----------------------------------------
    bottleneck_type = bn.get("bottleneck_type")
    if "bottleneck_type" in bn and bottleneck_type not in BOTTLENECK_TYPES:
        issues.append(_issue(
            "BN-R-7", "field 'institutional_bottleneck.bottleneck_type' has "
            "invalid enum value",
            f"must be one of {sorted(BOTTLENECK_TYPES)}",
            "institutional_bottleneck.bottleneck_type", bottleneck_type,
        ))

    # --- BN-R-8: epistemic_status membership ----------------------------------
    epistemic_status = bn.get("epistemic_status")
    if "epistemic_status" in bn and epistemic_status not in EPISTEMIC_CLASSIFICATIONS:
        issues.append(_issue(
            "BN-R-8", "field 'institutional_bottleneck.epistemic_status' has "
            "invalid enum value",
            "must be a member of kpm.schemas.epistemic_types."
            "ALL_CLASSIFICATIONS — the same closed vocabulary every other "
            "claim in this codebase uses; a bottleneck claim cannot invent "
            "its own epistemic status",
            "institutional_bottleneck.epistemic_status", epistemic_status,
        ))

    # --- BN-R-9: recommended_next_step must not be an automation instruction -
    next_step = bn.get("recommended_next_step")
    if "recommended_next_step" in bn and isinstance(next_step, str) and next_step.strip():
        hits = _contains_action_verb(next_step)
        if hits:
            issues.append(_issue(
                "BN-R-9", "field 'institutional_bottleneck.recommended_next_step' "
                "contains a direct-automation action verb",
                "a bottleneck record's job is to describe a problem and "
                "propose how to learn more about it — never to prescribe a "
                "fix; fixes belong in a separate automation-candidate "
                f"artefact. Blocked verb(s): {hits}",
                "institutional_bottleneck.recommended_next_step", next_step,
            ))

    # --- BN-R-10: evidence required for high-confidence classes --------------
    evidence = bn.get("evidence")
    if "evidence" in bn:
        if not isinstance(evidence, list):
            issues.append(_issue(
                "BN-R-10", "field 'institutional_bottleneck.evidence' has wrong type",
                "expected list", "institutional_bottleneck.evidence",
                f"got {type(evidence).__name__}",
            ))
        else:
            bad = [e for e in evidence if not isinstance(e, str) or not e.strip()]
            if bad:
                issues.append(_issue(
                    "BN-R-10", "entry in 'evidence' is not a non-empty string",
                    "each evidence entry must be a concrete, non-blank "
                    "reference",
                    "institutional_bottleneck.evidence", bad,
                ))
    if epistemic_status in EVIDENCE_REQUIRED_CLASSIFICATIONS:
        if not evidence or not isinstance(evidence, list) or all(
            not (isinstance(e, str) and e.strip()) for e in evidence
        ):
            issues.append(_issue(
                "BN-R-10", "field 'institutional_bottleneck.evidence' is "
                "required and must be non-empty when epistemic_status is "
                f"{epistemic_status!r}",
                "mirrors kpm.schemas.epistemic_types' rule that entering a "
                "high-confidence evidentiary classification requires "
                "non-empty evidence_refs — an unevidenced VERIFIED_FACT or "
                "EVIDENCE_SUPPORTED_MODEL claim is exactly the collapse "
                "that vocabulary exists to prevent",
                "institutional_bottleneck.evidence", evidence,
            ))

    # --- BN-R-11: estimated_impact section ------------------------------------
    estimated_impact = bn.get("estimated_impact")
    if "estimated_impact" in bn:
        if not isinstance(estimated_impact, dict):
            issues.append(_issue(
                "BN-R-11", "field 'institutional_bottleneck.estimated_impact' "
                "must be a mapping",
                "estimated_impact carries value_at_risk/delay_contribution/"
                "failure_propagation_scope as sub-fields",
                "institutional_bottleneck.estimated_impact",
                f"got {type(estimated_impact).__name__}",
            ))
            estimated_impact = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["estimated_impact"] - estimated_impact.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "BN-R-11", f"required field "
                    f"'institutional_bottleneck.estimated_impact.{f}' is missing",
                    "required by schema",
                    f"institutional_bottleneck.estimated_impact.{f}", "absent",
                ))
            for f in ("value_at_risk", "delay_contribution"):
                if f in estimated_impact and (
                    not isinstance(estimated_impact[f], str) or not estimated_impact[f].strip()
                ):
                    issues.append(_issue(
                        "BN-R-11", f"field "
                        f"'institutional_bottleneck.estimated_impact.{f}' "
                        "must be a non-empty string",
                        "free-text human estimate, but cannot be blank if "
                        "declared",
                        f"institutional_bottleneck.estimated_impact.{f}",
                        estimated_impact.get(f),
                    ))
            scope = estimated_impact.get("failure_propagation_scope")
            if "failure_propagation_scope" in estimated_impact and not isinstance(scope, list):
                issues.append(_issue(
                    "BN-R-11", "field "
                    "'institutional_bottleneck.estimated_impact."
                    "failure_propagation_scope' has wrong type",
                    "expected list",
                    "institutional_bottleneck.estimated_impact."
                    "failure_propagation_scope",
                    f"got {type(scope).__name__}",
                ))

    # --- BN-R-12: assumptions/unknowns are lists (may be empty) --------------
    for f in ("assumptions", "unknowns"):
        v = bn.get(f)
        if f in bn and not isinstance(v, list):
            issues.append(_issue(
                "BN-R-12", f"field 'institutional_bottleneck.{f}' has wrong type",
                "expected list (may be empty, but must be a list — never "
                "silently omitted)",
                f"institutional_bottleneck.{f}", f"got {type(v).__name__}",
            ))

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
