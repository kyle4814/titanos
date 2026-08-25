"""
TAAL threat_archetype Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this threat_archetype document conform to the declared schema,
     structurally, deterministically, and without executing anything it
     contains?"

It does NOT answer:
    - "Is this a compelling or well-written archetype?" (human judgment —
      symbolic_layer.human_description quality is never scored here)
    - "Should this archetype's response.default_state actually trigger
      quarantine right now?" (that's a runtime gate/scoring system's job;
      this validator only checks that the declared value is a member of
      the closed vocabulary)
    - "Is the archetype's technical_layer content accurate to a real
      threat?" (that is a security-review/red-team judgment call, not a
      structural check)

A VALID result means "structurally conformant". It is never upgraded to
"approved", "confirmed threat", or "enforced" — those are other systems'
vocabulary.

THE STRUCTURAL SEPARATION THIS VALIDATOR GUARANTEES

This is the single most important property of this file. `symbolic_layer`
is read ONLY for its own three required fields (archetype_name non-empty,
metaphor_status == the one legal literal, human_description non-empty —
rules TA-R-6a/6b/6c below). No other rule in this file, and no field
computed from any other rule, ever reads `symbolic_layer.archetype_name`
or `symbolic_layer.human_description` content. Every enforcement-relevant
finding (threat_class validity, boundary-crossing non-emptiness, evidence
confidence membership, risk/response enum membership, detection/FP/FN
non-emptiness) is derived exclusively from `technical_layer` and its
siblings (adversarial_goal, capability_request, boundary_analysis,
evidence, behaviour, risk, controls, response, false_positive_controls,
false_negative_controls, provenance).

taal/validators/tests/test_validate_threat_archetype.py::
TestSymbolicTechnicalSeparation constructs two documents identical except
for symbolic_layer content — one deliberately mundane, one deliberately
maximal mythic/dramatic ("THE ANCIENT DEVOURER OF TRUST, HARBINGER OF THE
VOID") — and asserts the two ValidationResults' technical findings
(status, issues minus symbolic_layer-rule issues, unknown_fields) are
byte-identical. This mirrors schema/tests/test_meta_attack.py's proof that
persuasive content has zero effect on the verdict.

HARDENING

Same parsing hardening as schema/validator.py, magl/validators/
validate_magl.py, and kpm/validators/validate_blueprint.py, replicated
deliberately rather than imported — each validator in this codebase owns
its own parsing hardening independently (the house pattern): duplicate-key
detection, document-size/node-count/depth ceilings enforced BEFORE
construction (to defeat alias/anchor expansion), and RecursionError caught
explicitly both at compose time and construct time, because PyYAML's
composer is itself recursive and can blow the Python call stack before our
own ceiling check gets a turn.

validate_threat_archetype()'s entire body is wrapped in try/except so an
unforeseen exception becomes a structured INVALID result (rule TA-R-0)
rather than propagating — mirroring the other validators' fail-closed
wrapper and the F-009/F-010 lesson (failures/FAILURE_ARCHIVE.md) it
encodes: an uncaught exception here would be a fail-OPEN bug in whatever
calls this validator.

RULE NUMBERING (TA-R-<n>, distinct from R-<n>, MG-R-<n>, BP-R-<n>, LM-R-<n>)

  TA-R-0   fail-closed outer wrapper (unforeseen exception -> INVALID)
  TA-R-1   YAML parseable + structural ceilings (size/nodes/depth)
  TA-R-2   top-level 'threat_archetype' key present and is a mapping
  TA-R-3   mapping contains only string keys (type-confusion class)
  TA-R-4   required top-level fields present
  TA-R-5   identity fields (id/version/title) non-empty strings; version
           is semver-shaped
  TA-R-6a  symbolic_layer.archetype_name non-empty string
  TA-R-6b  symbolic_layer.metaphor_status is EXACTLY "SYMBOLIC_ONLY"
           (missing or any other value is rejected — the structural
           guarantee this whole component exists to enforce)
  TA-R-6c  symbolic_layer.human_description non-empty string
  TA-R-7   technical_layer: threat_class membership, behaviour_class
           non-empty, target_classes/asset_classes non-empty lists
  TA-R-8   adversarial_goal.primary non-empty string; .secondary list-shape
  TA-R-9   capability_request: list/string shape only (no required
           sub-fields — a capability_request may legitimately be empty)
  TA-R-10  boundary_analysis: list-shape of all four *_crossed fields, AND
           at least one of the four is non-empty (an archetype describing
           zero boundary crossings is normal operation, not a threat)
  TA-R-11  evidence.confidence membership in
           kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS; unknowns
           present as a list (may be empty, never omitted)
  TA-R-12  behaviour.observable_indicators non-empty list
  TA-R-13  risk: confidentiality/integrity/availability impact enum
           membership, blast_radius non-empty, reversibility enum
           membership
  TA-R-14  controls.detection non-empty list; prevention/containment/
           recovery list-shape
  TA-R-15  response.default_state enum membership; escalation_conditions/
           human_review_conditions list-shape
  TA-R-16  false_positive_controls non-empty list
  TA-R-17  false_negative_controls non-empty list
  TA-R-18  provenance.evidence_status membership in ALL_CLASSIFICATIONS;
           last_reviewed RFC3339 timestamp shape; sources list-shape
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

from taal.schema.threat_archetype import (  # noqa: E402
    BOUNDARY_CROSSED_FIELDS,
    EPISTEMIC_CLASSIFICATIONS,
    IMPACT_LEVELS,
    METAPHOR_STATUS_REQUIRED_VALUE,
    REQUIRED_NESTED_PATHS,
    REQUIRED_TOP_FIELDS,
    RESPONSE_STATES,
    REVERSIBILITY_VALUES,
    THREAT_CLASSES,
)

__all__ = [
    "Issue", "ValidationResult", "validate_threat_archetype",
    "MalformedYamlError", "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as the other
# validators in this codebase.
MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)


class MalformedYamlError(Exception):
    """Raised only for genuinely unparseable (or structurally-over-ceiling)
    input. Never for content we merely disagree with — that is INVALID."""


# ─────────────────────────────────────────────────────────────
# Structured result — never a bare bool
# ─────────────────────────────────────────────────────────────

@dataclass
class Issue:
    what: str       # what failed
    why: str        # why it matters
    where: str      # field / path / location
    rule: str       # which rule ("TA-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    archetype_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    # Preservation invariant: original input is carried through untouched.
    # validate_threat_archetype() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "archetype_id": self.archetype_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated from the other validators rather than imported —
#  each validator in this codebase owns its own parsing hardening
#  independently, matching the house pattern)
# ─────────────────────────────────────────────────────────────

class _DuplicateKeyError(Exception):
    def __init__(self, key: Any, path: str):
        self.key = key
        self.path = path


class _BoundedSafeLoader(yaml.SafeLoader):
    """SafeLoader only — never yaml.Loader/FullLoader (those permit
    arbitrary Python object construction from tags, a code-execution path
    disguised as data). Extended only to reject duplicate mapping keys and
    to allow node-count/depth bounding via _count_and_bound below."""


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
        raise MalformedYamlError(
            f"document exceeds MAX_DEPTH ({MAX_DEPTH}) — refused."
        )
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
        # Compose first (structure only, no object construction) so node
        # count/depth can be bounded BEFORE constructing — this is what
        # stops anchor/alias fan-out ("billion laughs") from ever reaching
        # construction. PyYAML's composer is itself recursive, so a
        # sufficiently deep alias/nesting chain blows the Python call stack
        # before MAX_NODES/MAX_DEPTH gets a chance to run — that failure is
        # caught explicitly below and treated as the same class of
        # rejection, never allowed to propagate as an uncaught crash.
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


def validate_threat_archetype(text: str) -> ValidationResult:
    """Deterministic structural validation of a threat_archetype document.
    Never returns a bare bool, and never raises on real-world input — an
    uncaught exception here would be a fail-OPEN bug in whatever calls
    this. Any unforeseen failure is reported as INVALID with rule TA-R-0,
    never allowed to propagate (fail-closed, mirroring the other
    validators' outer wrapper and the F-009/F-010 lesson it encodes)."""
    try:
        return _validate_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", archetype_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="TA-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def _is_valid_timestamp(v: Any) -> bool:
    if not isinstance(v, str) or not _TIMESTAMP_RE.match(v):
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _require_mapping(mg: dict, key: str, rule: str, issues: list[Issue]) -> dict:
    """Fetch mg[key], reporting a shape issue and returning {} if it is
    present but not a mapping. Absence of the key is reported separately
    by TA-R-4 and is not doubled here."""
    val = mg.get(key)
    if key in mg and not isinstance(val, dict):
        issues.append(_issue(
            rule, f"field 'threat_archetype.{key}' must be a mapping",
            f"{key} carries required sub-fields",
            f"threat_archetype.{key}", f"got {type(val).__name__}",
        ))
        return {}
    return val if isinstance(val, dict) else {}


def _check_list_shape(section: dict, section_name: str, subfields: tuple[str, ...],
                       rule: str, issues: list[Issue]) -> None:
    for f in subfields:
        if f in section and not isinstance(section[f], list):
            issues.append(_issue(
                rule, f"field 'threat_archetype.{section_name}.{f}' has wrong type",
                "expected list", f"threat_archetype.{section_name}.{f}",
                f"got {type(section[f]).__name__}",
            ))


def _non_empty_str(v: Any) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _validate_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function. In
    particular: symbolic_layer content is read ONLY for its own three
    required fields (TA-R-6a/6b/6c) — it never feeds any other rule."""
    result = ValidationResult(status="UNKNOWN", archetype_id=None, original_text=text)

    # --- TA-R-1: parseable + structural ceilings -----------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "TA-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- TA-R-2: top-level 'threat_archetype' wrapper present and a mapping --
    if "threat_archetype" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "TA-R-2", "top-level 'threat_archetype' key is missing",
            "every threat_archetype document must be wrapped in a "
            "top-level 'threat_archetype:' key",
            "threat_archetype", "absent",
        ))
        return result
    mg = data["threat_archetype"]
    if not isinstance(mg, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "TA-R-2", "'threat_archetype' value is not a mapping",
            "the 'threat_archetype' key must contain a mapping of fields",
            "threat_archetype", f"got {type(mg).__name__}",
        ))
        return result

    # --- TA-R-3: non-string keys (type-confusion class) ----------------------
    # Content found inside `mg` — including a key literally named
    # "metaphor_status" or "default_state" — is read as DATA below. Field
    # lookups are always by literal string name against the fixed schema; a
    # forged/self-declared field never changes control flow.
    non_string_keys = [k for k in mg.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "TA-R-3", "threat_archetype mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot be "
            "a declared field",
            "threat_archetype", f"key types present: {sorted({type(k).__name__ for k in mg.keys()})}",
        ))

    mg_keys_as_str = {k if isinstance(k, str) else repr(k) for k in mg.keys()}

    archetype_id = mg.get("id") if isinstance(mg.get("id"), str) else None
    result.archetype_id = archetype_id

    issues: list[Issue] = list(result.issues)

    # --- TA-R-4: required top-level fields ------------------------------------
    missing = REQUIRED_TOP_FIELDS - mg.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "TA-R-4", f"required field 'threat_archetype.{f}' is missing",
            "required by schema", f"threat_archetype.{f}", "absent",
        ))

    # --- TA-R-5: identity fields ------------------------------------------------
    for f in ("id", "version", "title"):
        if f in mg and not _non_empty_str(mg.get(f)):
            issues.append(_issue(
                "TA-R-5", f"field 'threat_archetype.{f}' must be a non-empty string",
                "identity fields cannot be blank or non-string",
                f"threat_archetype.{f}", mg.get(f),
            ))
    version = mg.get("version")
    if isinstance(version, str) and version.strip() and not _VERSION_RE.match(version):
        issues.append(_issue(
            "TA-R-5", "field 'threat_archetype.version' is not semver-shaped",
            "version must match N.N.N exactly — values like 'latest' or "
            "'v1' cannot be compared or resolved deterministically",
            "threat_archetype.version", version,
        ))

    # --- TA-R-6a/6b/6c: symbolic_layer -----------------------------------------
    # STRUCTURAL FIREWALL: this is the ONLY place in this function that
    # reads symbolic_layer. Its content is checked for its own three
    # required fields and NOTHING ELSE — it is never consulted by any rule
    # below this block, and no downstream variable is derived from it.
    symbolic = _require_mapping(mg, "symbolic_layer", "TA-R-6a", issues)
    if "symbolic_layer" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["symbolic_layer"] - symbolic.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-6a", f"required field 'threat_archetype.symbolic_layer.{f}' is missing",
                "required by schema", f"threat_archetype.symbolic_layer.{f}", "absent",
            ))
        if "archetype_name" in symbolic and not _non_empty_str(symbolic.get("archetype_name")):
            issues.append(_issue(
                "TA-R-6a", "field 'threat_archetype.symbolic_layer.archetype_name' "
                "must be a non-empty string",
                "the memory-aid name must exist even though it is never "
                "read by enforcement logic",
                "threat_archetype.symbolic_layer.archetype_name",
                symbolic.get("archetype_name"),
            ))
        metaphor_status = symbolic.get("metaphor_status")
        if "metaphor_status" in symbolic and metaphor_status != METAPHOR_STATUS_REQUIRED_VALUE:
            issues.append(_issue(
                "TA-R-6b", "field 'threat_archetype.symbolic_layer.metaphor_status' "
                "must be exactly the literal 'SYMBOLIC_ONLY'",
                "this is the structural guarantee that the symbolic layer "
                "can never claim to be technical evidence — any other "
                "value (including a plausible-sounding one) is rejected",
                "threat_archetype.symbolic_layer.metaphor_status", metaphor_status,
            ))
        if "human_description" in symbolic and not _non_empty_str(symbolic.get("human_description")):
            issues.append(_issue(
                "TA-R-6c", "field 'threat_archetype.symbolic_layer.human_description' "
                "must be a non-empty string",
                "an archetype with no human-readable memory aid fails its "
                "one purpose for this section",
                "threat_archetype.symbolic_layer.human_description",
                symbolic.get("human_description"),
            ))

    # --- TA-R-7: technical_layer -------------------------------------------------
    technical = _require_mapping(mg, "technical_layer", "TA-R-7", issues)
    if "technical_layer" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["technical_layer"] - technical.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-7", f"required field 'threat_archetype.technical_layer.{f}' is missing",
                "required by schema", f"threat_archetype.technical_layer.{f}", "absent",
            ))
        threat_class = technical.get("threat_class")
        if "threat_class" in technical and threat_class not in THREAT_CLASSES:
            issues.append(_issue(
                "TA-R-7", "field 'threat_archetype.technical_layer.threat_class' "
                "has invalid enum value",
                f"must be one of {sorted(THREAT_CLASSES)}",
                "threat_archetype.technical_layer.threat_class", threat_class,
            ))
        if "behaviour_class" in technical and not _non_empty_str(technical.get("behaviour_class")):
            issues.append(_issue(
                "TA-R-7", "field 'threat_archetype.technical_layer.behaviour_class' "
                "must be a non-empty string",
                "required by schema", "threat_archetype.technical_layer.behaviour_class",
                technical.get("behaviour_class"),
            ))
        for f in ("target_classes", "asset_classes"):
            v = technical.get(f)
            if f in technical and (not isinstance(v, list) or len(v) == 0):
                issues.append(_issue(
                    "TA-R-7", f"field 'threat_archetype.technical_layer.{f}' "
                    "must be a non-empty list",
                    "an archetype with no declared target/asset classes "
                    "cannot be scoped",
                    f"threat_archetype.technical_layer.{f}", v,
                ))

    # --- TA-R-8: adversarial_goal ------------------------------------------------
    adv_goal = _require_mapping(mg, "adversarial_goal", "TA-R-8", issues)
    if "adversarial_goal" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["adversarial_goal"] - adv_goal.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-8", f"required field 'threat_archetype.adversarial_goal.{f}' is missing",
                "required by schema", f"threat_archetype.adversarial_goal.{f}", "absent",
            ))
        if "primary" in adv_goal and not _non_empty_str(adv_goal.get("primary")):
            issues.append(_issue(
                "TA-R-8", "field 'threat_archetype.adversarial_goal.primary' "
                "must be a non-empty string",
                "required by schema", "threat_archetype.adversarial_goal.primary",
                adv_goal.get("primary"),
            ))
        _check_list_shape(adv_goal, "adversarial_goal", ("secondary",), "TA-R-8", issues)

    # --- TA-R-9: capability_request (shape only) ----------------------------------
    cap_req = _require_mapping(mg, "capability_request", "TA-R-9", issues)
    if "capability_request" in mg:
        _check_list_shape(cap_req, "capability_request", (
            "requested_permissions", "requested_resources",
            "requested_external_access",
        ), "TA-R-9", issues)
        for f in ("requested_scope", "requested_duration", "requested_persistence"):
            if f in cap_req and cap_req.get(f) is not None and not isinstance(cap_req.get(f), str):
                issues.append(_issue(
                    "TA-R-9", f"field 'threat_archetype.capability_request.{f}' has wrong type",
                    "expected string", f"threat_archetype.capability_request.{f}",
                    f"got {type(cap_req[f]).__name__}",
                ))

    # --- TA-R-10: boundary_analysis -----------------------------------------------
    boundary = _require_mapping(mg, "boundary_analysis", "TA-R-10", issues)
    if "boundary_analysis" in mg:
        _check_list_shape(boundary, "boundary_analysis", BOUNDARY_CROSSED_FIELDS,
                           "TA-R-10", issues)
        any_non_empty = any(
            isinstance(boundary.get(f), list) and len(boundary.get(f)) > 0
            for f in BOUNDARY_CROSSED_FIELDS
        )
        if not any_non_empty:
            issues.append(_issue(
                "TA-R-10", "all four boundary_analysis.*_crossed lists are empty",
                "an archetype describing zero boundary crossings isn't "
                "describing a threat, it's describing normal operation — "
                "at least one of trust_boundary_crossed / "
                "privilege_boundary_crossed / data_boundary_crossed / "
                "execution_boundary_crossed must be non-empty",
                "threat_archetype.boundary_analysis",
                {f: boundary.get(f) for f in BOUNDARY_CROSSED_FIELDS},
            ))

    # --- TA-R-11: evidence -----------------------------------------------------------
    evidence = _require_mapping(mg, "evidence", "TA-R-11", issues)
    if "evidence" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["evidence"] - evidence.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-11", f"required field 'threat_archetype.evidence.{f}' is missing",
                "required by schema", f"threat_archetype.evidence.{f}", "absent",
            ))
        confidence = evidence.get("confidence")
        if "confidence" in evidence and confidence not in EPISTEMIC_CLASSIFICATIONS:
            issues.append(_issue(
                "TA-R-11", "field 'threat_archetype.evidence.confidence' "
                "has invalid enum value",
                "must be a member of kpm.schemas.epistemic_types."
                "ALL_CLASSIFICATIONS — the same closed vocabulary every "
                "other claim in this codebase uses; a threat archetype "
                "cannot invent its own confidence scale",
                "threat_archetype.evidence.confidence", confidence,
            ))
        unknowns = evidence.get("unknowns")
        if "unknowns" in evidence and not isinstance(unknowns, list):
            issues.append(_issue(
                "TA-R-11", "field 'threat_archetype.evidence.unknowns' has wrong type",
                "expected list (may be empty, but must be present as a list)",
                "threat_archetype.evidence.unknowns", f"got {type(unknowns).__name__}",
            ))
        _check_list_shape(evidence, "evidence",
                           ("supporting_signals", "contradictory_signals"),
                           "TA-R-11", issues)

    # --- TA-R-12: behaviour -----------------------------------------------------------
    behaviour = _require_mapping(mg, "behaviour", "TA-R-12", issues)
    if "behaviour" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["behaviour"] - behaviour.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-12", f"required field 'threat_archetype.behaviour.{f}' is missing",
                "required by schema", f"threat_archetype.behaviour.{f}", "absent",
            ))
        obs = behaviour.get("observable_indicators")
        if "observable_indicators" in behaviour and (not isinstance(obs, list) or len(obs) == 0):
            issues.append(_issue(
                "TA-R-12", "field 'threat_archetype.behaviour.observable_indicators' "
                "must be a non-empty list",
                "an archetype with no observable indicators cannot be "
                "detected, only imagined",
                "threat_archetype.behaviour.observable_indicators", obs,
            ))
        _check_list_shape(behaviour, "behaviour",
                           ("temporal_patterns", "dependency_patterns", "anomalous_requests"),
                           "TA-R-12", issues)

    # --- TA-R-13: risk -----------------------------------------------------------------
    risk = _require_mapping(mg, "risk", "TA-R-13", issues)
    if "risk" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["risk"] - risk.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-13", f"required field 'threat_archetype.risk.{f}' is missing",
                "required by schema", f"threat_archetype.risk.{f}", "absent",
            ))
        for f in ("confidentiality_impact", "integrity_impact", "availability_impact"):
            v = risk.get(f)
            if f in risk and v not in IMPACT_LEVELS:
                issues.append(_issue(
                    "TA-R-13", f"field 'threat_archetype.risk.{f}' has invalid enum value",
                    f"must be one of {sorted(IMPACT_LEVELS)}",
                    f"threat_archetype.risk.{f}", v,
                ))
        if "blast_radius" in risk and not _non_empty_str(risk.get("blast_radius")):
            issues.append(_issue(
                "TA-R-13", "field 'threat_archetype.risk.blast_radius' must be "
                "a non-empty string",
                "required by schema", "threat_archetype.risk.blast_radius",
                risk.get("blast_radius"),
            ))
        reversibility = risk.get("reversibility")
        if "reversibility" in risk and reversibility not in REVERSIBILITY_VALUES:
            issues.append(_issue(
                "TA-R-13", "field 'threat_archetype.risk.reversibility' has "
                "invalid enum value",
                f"must be one of {sorted(REVERSIBILITY_VALUES)}",
                "threat_archetype.risk.reversibility", reversibility,
            ))

    # --- TA-R-14: controls -----------------------------------------------------------
    controls = _require_mapping(mg, "controls", "TA-R-14", issues)
    if "controls" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["controls"] - controls.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-14", f"required field 'threat_archetype.controls.{f}' is missing",
                "required by schema", f"threat_archetype.controls.{f}", "absent",
            ))
        detection = controls.get("detection")
        if "detection" in controls and (not isinstance(detection, list) or len(detection) == 0):
            issues.append(_issue(
                "TA-R-14", "field 'threat_archetype.controls.detection' must "
                "be a non-empty list",
                "a threat archetype the system has no way to detect is not "
                "actionable",
                "threat_archetype.controls.detection", detection,
            ))
        _check_list_shape(controls, "controls",
                           ("prevention", "containment", "recovery"),
                           "TA-R-14", issues)

    # --- TA-R-15: response -----------------------------------------------------------
    response = _require_mapping(mg, "response", "TA-R-15", issues)
    if "response" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["response"] - response.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-15", f"required field 'threat_archetype.response.{f}' is missing",
                "required by schema", f"threat_archetype.response.{f}", "absent",
            ))
        default_state = response.get("default_state")
        if "default_state" in response and default_state not in RESPONSE_STATES:
            issues.append(_issue(
                "TA-R-15", "field 'threat_archetype.response.default_state' "
                "has invalid enum value",
                f"must be one of {sorted(RESPONSE_STATES)}",
                "threat_archetype.response.default_state", default_state,
            ))
        _check_list_shape(response, "response",
                           ("escalation_conditions", "human_review_conditions"),
                           "TA-R-15", issues)

    # --- TA-R-16: false_positive_controls ---------------------------------------------
    fp_controls = mg.get("false_positive_controls")
    if "false_positive_controls" in mg and (not isinstance(fp_controls, list) or len(fp_controls) == 0):
        issues.append(_issue(
            "TA-R-16", "field 'threat_archetype.false_positive_controls' "
            "must be a non-empty list",
            "a detector claiming zero false-positive risk is not to be "
            "trusted",
            "threat_archetype.false_positive_controls", fp_controls,
        ))

    # --- TA-R-17: false_negative_controls ---------------------------------------------
    fn_controls = mg.get("false_negative_controls")
    if "false_negative_controls" in mg and (not isinstance(fn_controls, list) or len(fn_controls) == 0):
        issues.append(_issue(
            "TA-R-17", "field 'threat_archetype.false_negative_controls' "
            "must be a non-empty list",
            "a detector claiming zero false-negative risk is not to be "
            "trusted",
            "threat_archetype.false_negative_controls", fn_controls,
        ))

    # --- TA-R-18: provenance ---------------------------------------------------------
    provenance = _require_mapping(mg, "provenance", "TA-R-18", issues)
    if "provenance" in mg:
        missing_nested = REQUIRED_NESTED_PATHS["provenance"] - provenance.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "TA-R-18", f"required field 'threat_archetype.provenance.{f}' is missing",
                "required by schema", f"threat_archetype.provenance.{f}", "absent",
            ))
        evidence_status = provenance.get("evidence_status")
        if "evidence_status" in provenance and evidence_status not in EPISTEMIC_CLASSIFICATIONS:
            issues.append(_issue(
                "TA-R-18", "field 'threat_archetype.provenance.evidence_status' "
                "has invalid enum value",
                "must be a member of kpm.schemas.epistemic_types."
                "ALL_CLASSIFICATIONS",
                "threat_archetype.provenance.evidence_status", evidence_status,
            ))
        last_reviewed = provenance.get("last_reviewed")
        if "last_reviewed" in provenance and not _is_valid_timestamp(last_reviewed):
            issues.append(_issue(
                "TA-R-18", "field 'threat_archetype.provenance.last_reviewed' "
                "is not a valid RFC3339 timestamp",
                "malformed or ambiguous timestamps break provenance "
                "ordering", "threat_archetype.provenance.last_reviewed",
                last_reviewed,
            ))
        _check_list_shape(provenance, "provenance", ("sources",), "TA-R-18", issues)

    # --- unknown fields (never silently trusted) ---------------------------------
    unknown = sorted(mg_keys_as_str - set(REQUIRED_TOP_FIELDS))
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
