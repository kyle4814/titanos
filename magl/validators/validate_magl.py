"""
MAGL (Modular Architecture Generation Library unit) Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this MAGL unit conform to the declared schema, structurally,
     deterministically, and without executing anything it contains?"

It does NOT answer:
    - "Is this MAGL a good design?" (human judgment — purpose/risks/
      documentation quality is never scored here)
    - "Has this MAGL actually earned its promotion state?" (that's the
      promotion state machine another component — kpm/promotion/
      state_machine.py — owns; this validator only catches the STRUCTURAL
      contradiction of lifecycle.status != promotion.current_gate and that
      both are members of the shared 10-state vocabulary, not full gate
      logic)
    - "Is this MAGL safe to run?" (that's the runtime authorization layer;
      this validator only catches the STRUCTURAL contradiction between
      capability_type and jurisdiction — see MG-R-11 below)

A VALID result means "structurally conformant". It is never upgraded to
"approved", "safe to execute", or "promoted" — those are other systems'
vocabulary.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_magl() is a pure function over its input text. Content found
inside `text` is read as DATA throughout — never as an instruction to this
function, regardless of field name or content. No field value changes
control flow; every field is looked up by NAME against the fixed schema.
A field literally named "lifecycle.status: STABLE" on a freshly-authored
MAGL is checked against the real promotion vocabulary and the real
current_gate agreement rule like any other value — it is never honoured
merely because it was asserted.

HARDENING

Same parsing hardening as schema/validator.py and
kpm/validators/validate_blueprint.py, replicated deliberately rather than
imported — each validator in this codebase owns its own parsing hardening
independently (the house pattern): duplicate-key detection, document-size/
node-count/depth ceilings enforced BEFORE construction (to defeat alias/
anchor expansion), and RecursionError caught explicitly both at compose
time and construct time, because PyYAML's composer is itself recursive and
can blow the Python call stack before our own ceiling check gets a turn.

validate_magl()'s entire body is wrapped in try/except so an unforeseen
exception becomes a structured INVALID result (rule MG-R-0) rather than
propagating — mirroring schema/validator.py's fail-closed wrapper and the
F-009/F-010 lesson (failures/FAILURE_ARCHIVE.md) it encodes: an uncaught
exception here would be a fail-OPEN bug in whatever calls this validator.

RULE NUMBERING (MG-R-<n>, distinct from R-<n> and BP-R-<n>)

  MG-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  MG-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  MG-R-2  top-level 'magl' key present and is a mapping
  MG-R-3  mapping contains only string keys (type-confusion class)
  MG-R-4  required top-level fields present
  MG-R-5  identity string fields (id/name/version/title/description) non-empty
  MG-R-6  version is semver-shaped (N.N.N)
  MG-R-7  classification section: required sub-fields, capability_type
          enum-list, epistemic_status membership (imported from
          kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS), maturity enum
  MG-R-8  provenance section: license non-empty, source_hashes/content_hash
          shape (sha256:<64 hex>)
  MG-R-9  purpose section: problem / intended_benefit non-empty
  MG-R-10 jurisdiction section: list-shape of all sub-fields
  MG-R-11 jurisdiction/capability_type contradiction (EXECUTABLE or
          EXTERNALLY_ACTING with zero acting-jurisdiction, OR
          DESCRIPTIVE-only with nonzero acting-jurisdiction)
  MG-R-12 inputs/outputs/dependencies/risks/controls/verification/
          composition sections: shape only (lists where declared)
  MG-R-13 lifecycle section: status membership (imported from
          kpm.promotion.state_machine.ALL_STATES), created_at/updated_at
          RFC3339 timestamp shape
  MG-R-14 audit section: content_hash shape
  MG-R-15 documentation section: summary non-empty, limitations non-empty
          list (an empty limitations list is rejected — "beautiful YAML
          is not evidence")
  MG-R-16 promotion section: current_gate membership AND current_gate ==
          lifecycle.status (mirrors blueprint_atom's BP-R-10 pattern)
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

from magl.schema.magl_schema import (  # noqa: E402
    ACTING_CAPABILITY_TYPES,
    CAPABILITY_TYPES,
    EPISTEMIC_CLASSIFICATIONS,
    EXECUTION_JURISDICTION_FIELDS,
    LIST_FIELDS,
    MATURITY_VALUES,
    PROMOTION_STATES,
    REQUIRED_NESTED_PATHS,
    REQUIRED_TOP_FIELDS,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_magl", "MalformedYamlError",
    "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as
# schema/validator.py / kpm/validators/validate_blueprint.py.
MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
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
    rule: str       # which rule ("MG-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    magl_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    # Preservation invariant: original input is carried through untouched.
    # validate_magl() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "magl_id": self.magl_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated from schema/validator.py rather than imported —
#  each validator owns its own parsing hardening independently, matching
#  the house pattern)
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


def validate_magl(text: str) -> ValidationResult:
    """Deterministic structural validation of a MAGL unit document. Never
    returns a bare bool, and never raises on real-world input — an
    uncaught exception here would be a fail-OPEN bug in whatever calls
    this. Any unforeseen failure is reported as INVALID with rule MG-R-0,
    never allowed to propagate (fail-closed, mirroring schema/validator.py's
    outer wrapper and the F-009/F-010 lesson it encodes)."""
    try:
        return _validate_magl_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", magl_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="MG-R-0", evidence=f"{type(e).__name__}: {e}",
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


def _validate_magl_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", magl_id=None, original_text=text)

    # --- MG-R-1: parseable + structural ceilings ---------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "MG-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- MG-R-2: top-level 'magl' wrapper present and a mapping ------------
    if "magl" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "MG-R-2", "top-level 'magl' key is missing",
            "every MAGL document must be wrapped in a top-level 'magl:' key",
            "magl", "absent",
        ))
        return result
    mg = data["magl"]
    if not isinstance(mg, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "MG-R-2", "'magl' value is not a mapping",
            "the 'magl' key must contain a mapping of fields",
            "magl", f"got {type(mg).__name__}",
        ))
        return result

    # --- MG-R-3: non-string keys (type-confusion class) --------------------
    # Content found inside `mg` — including a key literally named
    # "epistemic_status", "current_gate", or anything else — is read as
    # DATA below. Field lookups are always by literal string name against
    # the fixed schema; a forged/self-declared field never changes control
    # flow.
    non_string_keys = [k for k in mg.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "MG-R-3", "magl mapping contains non-string keys",
            "MAGL fields must be string-named; a boolean/int/null key "
            "cannot be a declared field",
            "magl", f"key types present: {sorted({type(k).__name__ for k in mg.keys()})}",
        ))

    mg_keys_as_str = {k if isinstance(k, str) else repr(k) for k in mg.keys()}

    magl_id = mg.get("id") if isinstance(mg.get("id"), str) else None
    result.magl_id = magl_id

    issues: list[Issue] = list(result.issues)

    # --- MG-R-4: required top-level fields ----------------------------------
    missing = REQUIRED_TOP_FIELDS - mg.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "MG-R-4", f"required field 'magl.{f}' is missing",
            "required by schema", f"magl.{f}", "absent",
        ))

    # --- MG-R-5: identity string fields non-empty ---------------------------
    for f in sorted(STRING_FIELDS):
        if f in mg and (not isinstance(mg[f], str) or not mg[f].strip()):
            issues.append(_issue(
                "MG-R-5", f"field 'magl.{f}' must be a non-empty string",
                "identity fields cannot be blank or non-string",
                f"magl.{f}", mg.get(f),
            ))

    # --- MG-R-6: version is semver-shaped -----------------------------------
    version = mg.get("version")
    if isinstance(version, str) and version.strip() and not _VERSION_RE.match(version):
        issues.append(_issue(
            "MG-R-6", "field 'magl.version' is not semver-shaped",
            "version must match N.N.N exactly — values like 'latest' or "
            "'v1' cannot be compared or resolved deterministically",
            "magl.version", version,
        ))

    # --- MG-R-7: classification section -------------------------------------
    classification = mg.get("classification")
    capability_types: list[Any] = []
    if "classification" in mg:
        if not isinstance(classification, dict):
            issues.append(_issue(
                "MG-R-7", "field 'magl.classification' must be a mapping",
                "classification carries domain/capability_type/"
                "epistemic_status/maturity as sub-fields",
                "magl.classification", f"got {type(classification).__name__}",
            ))
            classification = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["classification"] - classification.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "MG-R-7", f"required field 'magl.classification.{f}' is missing",
                    "required by schema", f"magl.classification.{f}", "absent",
                ))

            domain = classification.get("domain")
            if "domain" in classification and not isinstance(domain, list):
                issues.append(_issue(
                    "MG-R-7", "field 'magl.classification.domain' has wrong type",
                    "expected list", "magl.classification.domain",
                    f"got {type(domain).__name__}",
                ))

            capability_type = classification.get("capability_type")
            if "capability_type" in classification:
                if not isinstance(capability_type, list) or not capability_type:
                    issues.append(_issue(
                        "MG-R-7", "field 'magl.classification.capability_type' "
                        "must be a non-empty list",
                        "a capability with no declared type cannot be "
                        "structurally reasoned about",
                        "magl.classification.capability_type", capability_type,
                    ))
                else:
                    capability_types = capability_type
                    bad = [c for c in capability_type if c not in CAPABILITY_TYPES]
                    if bad:
                        issues.append(_issue(
                            "MG-R-7", "field 'magl.classification.capability_type' "
                            "contains invalid enum value(s)",
                            f"must each be one of {sorted(CAPABILITY_TYPES)}",
                            "magl.classification.capability_type", bad,
                        ))

            epistemic_status = classification.get("epistemic_status")
            if "epistemic_status" in classification and epistemic_status not in EPISTEMIC_CLASSIFICATIONS:
                issues.append(_issue(
                    "MG-R-7", "field 'magl.classification.epistemic_status' "
                    "has invalid enum value",
                    "must be a member of kpm.schemas.epistemic_types."
                    "ALL_CLASSIFICATIONS — the same closed vocabulary every "
                    "other claim in this codebase uses; a MAGL cannot invent "
                    "its own epistemic status",
                    "magl.classification.epistemic_status", epistemic_status,
                ))

            maturity = classification.get("maturity")
            if "maturity" in classification and maturity not in MATURITY_VALUES:
                issues.append(_issue(
                    "MG-R-7", "field 'magl.classification.maturity' has invalid enum value",
                    f"must be one of {sorted(MATURITY_VALUES)}",
                    "magl.classification.maturity", maturity,
                ))

    # --- MG-R-8: provenance section -----------------------------------------
    provenance = mg.get("provenance")
    if "provenance" in mg:
        if not isinstance(provenance, dict):
            issues.append(_issue(
                "MG-R-8", "field 'magl.provenance' must be a mapping",
                "provenance carries license/source_hashes/etc as sub-fields",
                "magl.provenance", f"got {type(provenance).__name__}",
            ))
            provenance = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["provenance"] - provenance.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "MG-R-8", f"required field 'magl.provenance.{f}' is missing",
                    "required by schema", f"magl.provenance.{f}", "absent",
                ))
            license_ = provenance.get("license")
            if "license" in provenance and (not isinstance(license_, str) or not license_.strip()):
                issues.append(_issue(
                    "MG-R-8", "field 'magl.provenance.license' must be a "
                    "non-empty string",
                    "a MAGL with an unstated license cannot legally enter "
                    "a public library",
                    "magl.provenance.license", license_,
                ))
            source_hashes = provenance.get("source_hashes")
            if "source_hashes" in provenance:
                if not isinstance(source_hashes, list):
                    issues.append(_issue(
                        "MG-R-8", "field 'magl.provenance.source_hashes' has wrong type",
                        "expected list", "magl.provenance.source_hashes",
                        f"got {type(source_hashes).__name__}",
                    ))
                else:
                    for h in source_hashes:
                        if not isinstance(h, str) or not _HASH_RE.match(h):
                            issues.append(_issue(
                                "MG-R-8", "entry in 'magl.provenance.source_hashes' "
                                "is not a well-formed sha256 hash",
                                "hash must match 'sha256:<64 hex chars>' exactly",
                                "magl.provenance.source_hashes", h,
                            ))

    # --- MG-R-9: purpose section ---------------------------------------------
    purpose = mg.get("purpose")
    if "purpose" in mg:
        if not isinstance(purpose, dict):
            issues.append(_issue(
                "MG-R-9", "field 'magl.purpose' must be a mapping",
                "purpose carries problem/intended_benefit/non_goals as "
                "sub-fields",
                "magl.purpose", f"got {type(purpose).__name__}",
            ))
            purpose = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["purpose"] - purpose.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "MG-R-9", f"required field 'magl.purpose.{f}' is missing",
                    "required by schema", f"magl.purpose.{f}", "absent",
                ))
            for f in ("problem", "intended_benefit"):
                if f in purpose and (not isinstance(purpose[f], str) or not purpose[f].strip()):
                    issues.append(_issue(
                        "MG-R-9", f"field 'magl.purpose.{f}' must be a non-empty string",
                        "a MAGL with no stated problem/benefit is not "
                        "structurally purposeful",
                        f"magl.purpose.{f}", purpose.get(f),
                    ))

    # --- MG-R-10: jurisdiction section (shape) --------------------------------
    jurisdiction = mg.get("jurisdiction")
    _JURISDICTION_LIST_FIELDS = (
        "may_read", "may_write", "may_execute", "may_call", "may_modify",
        "may_publish", "prohibited_actions",
    )
    if "jurisdiction" in mg:
        if not isinstance(jurisdiction, dict):
            issues.append(_issue(
                "MG-R-10", "field 'magl.jurisdiction' must be a mapping",
                "jurisdiction carries may_read/may_write/etc as sub-fields",
                "magl.jurisdiction", f"got {type(jurisdiction).__name__}",
            ))
            jurisdiction = {}
        else:
            for f in _JURISDICTION_LIST_FIELDS:
                if f in jurisdiction and not isinstance(jurisdiction[f], list):
                    issues.append(_issue(
                        "MG-R-10", f"field 'magl.jurisdiction.{f}' has wrong type",
                        "expected list", f"magl.jurisdiction.{f}",
                        f"got {type(jurisdiction[f]).__name__}",
                    ))
    else:
        jurisdiction = {}

    # --- MG-R-11: jurisdiction / capability_type contradiction ---------------
    # Only evaluated when capability_type was itself well-formed (a
    # non-empty list of recognised values) — an already-broken
    # capability_type is reported once, under MG-R-7, not doubled here.
    if capability_types and isinstance(jurisdiction, dict):
        acting_fields_present = any(
            isinstance(jurisdiction.get(f), list) and len(jurisdiction.get(f)) > 0
            for f in EXECUTION_JURISDICTION_FIELDS
        )
        is_acting_type = any(c in ACTING_CAPABILITY_TYPES for c in capability_types)
        is_descriptive_only = capability_types == ["DESCRIPTIVE"] or (
            set(capability_types) == {"DESCRIPTIVE"}
        )

        if is_acting_type and not acting_fields_present:
            issues.append(_issue(
                "MG-R-11", "EXECUTABLE/EXTERNALLY_ACTING capability_type "
                "declares no acting jurisdiction",
                "a capability that claims to act (EXECUTABLE or "
                "EXTERNALLY_ACTING) but declares no scope in "
                "may_execute/may_call/may_write/may_modify/may_publish is "
                "a structural contradiction — it claims to act while "
                "claiming no scope to act within",
                "magl.jurisdiction", {"capability_type": capability_types,
                                        "jurisdiction": jurisdiction},
            ))
        if is_descriptive_only and acting_fields_present:
            issues.append(_issue(
                "MG-R-11", "DESCRIPTIVE-only capability_type declares "
                "acting jurisdiction",
                "a capability declaring capability_type: [DESCRIPTIVE] "
                "only, but also declaring may_write/may_execute/may_call/"
                "may_modify/may_publish entries, is a structural "
                "contradiction — it claims to only describe while also "
                "claiming execution/modification jurisdiction",
                "magl.jurisdiction", {"capability_type": capability_types,
                                        "jurisdiction": jurisdiction},
            ))

    # --- MG-R-12: inputs/outputs/dependencies/risks/controls/verification/
    #              composition sections — shape only ---------------------------
    _mapping_sections_with_list_fields: dict[str, tuple[str, ...]] = {
        "inputs": ("required", "optional", "schemas"),
        "outputs": ("declared", "schemas"),
        "dependencies": ("required", "optional", "incompatible_with"),
        "risks": ("known", "failure_modes", "abuse_cases",
                  "false_positive_risks", "false_negative_risks"),
        "controls": ("validation", "authorization", "containment", "rollback",
                     "human_review"),
        "verification": ("schema_tests", "unit_tests", "integration_tests",
                          "simulation_tests", "evidence_requirements"),
        "composition": ("provides", "requires", "compatible_interfaces",
                         "composition_limits"),
    }
    for section, subfields in _mapping_sections_with_list_fields.items():
        if section not in mg:
            continue
        sval = mg[section]
        if not isinstance(sval, dict):
            issues.append(_issue(
                "MG-R-12", f"field 'magl.{section}' must be a mapping",
                f"{section} carries {', '.join(subfields)} as sub-fields",
                f"magl.{section}", f"got {type(sval).__name__}",
            ))
            continue
        for f in subfields:
            if f in sval and not isinstance(sval[f], list):
                issues.append(_issue(
                    "MG-R-12", f"field 'magl.{section}.{f}' has wrong type",
                    "expected list", f"magl.{section}.{f}",
                    f"got {type(sval[f]).__name__}",
                ))

    for f in sorted(LIST_FIELDS):
        if f in mg and not isinstance(mg[f], list):
            issues.append(_issue(
                "MG-R-12", f"field 'magl.{f}' has wrong type",
                "expected list", f"magl.{f}", f"got {type(mg[f]).__name__}",
            ))

    # --- MG-R-13: lifecycle section -------------------------------------------
    lifecycle = mg.get("lifecycle")
    lifecycle_status = None
    if "lifecycle" in mg:
        if not isinstance(lifecycle, dict):
            issues.append(_issue(
                "MG-R-13", "field 'magl.lifecycle' must be a mapping",
                "lifecycle carries status/created_at/etc as sub-fields",
                "magl.lifecycle", f"got {type(lifecycle).__name__}",
            ))
            lifecycle = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["lifecycle"] - lifecycle.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "MG-R-13", f"required field 'magl.lifecycle.{f}' is missing",
                    "required by schema", f"magl.lifecycle.{f}", "absent",
                ))
            lifecycle_status = lifecycle.get("status")
            if "status" in lifecycle and lifecycle_status not in PROMOTION_STATES:
                issues.append(_issue(
                    "MG-R-13", "field 'magl.lifecycle.status' has invalid enum value",
                    "must be a member of kpm.promotion.state_machine's "
                    "10-state vocabulary (RAW..SUPERSEDED) — the same "
                    "lifecycle every promotable unit in this codebase "
                    "shares",
                    "magl.lifecycle.status", lifecycle_status,
                ))
            for f in ("created_at", "updated_at"):
                if f in lifecycle and lifecycle.get(f) not in (None, "") and not _is_valid_timestamp(lifecycle.get(f)):
                    issues.append(_issue(
                        "MG-R-13", f"field 'magl.lifecycle.{f}' is not a "
                        "valid RFC3339 timestamp",
                        "malformed or ambiguous timestamps break lifecycle "
                        "ordering",
                        f"magl.lifecycle.{f}", lifecycle.get(f),
                    ))
    else:
        lifecycle = {}

    # --- MG-R-14: audit section (shape only) ------------------------------------
    audit = mg.get("audit")
    if "audit" in mg:
        if not isinstance(audit, dict):
            issues.append(_issue(
                "MG-R-14", "field 'magl.audit' must be a mapping",
                "audit carries content_hash/signatures/etc as sub-fields",
                "magl.audit", f"got {type(audit).__name__}",
            ))
            audit = {}
        else:
            content_hash = audit.get("content_hash")
            if content_hash not in (None, "") and (not isinstance(content_hash, str) or not _HASH_RE.match(content_hash)):
                issues.append(_issue(
                    "MG-R-14", "field 'magl.audit.content_hash' is not a "
                    "well-formed sha256 hash",
                    "hash must match 'sha256:<64 hex chars>' exactly",
                    "magl.audit.content_hash", content_hash,
                ))
            signatures = audit.get("signatures")
            if "signatures" in audit and not isinstance(signatures, list):
                issues.append(_issue(
                    "MG-R-14", "field 'magl.audit.signatures' has wrong type",
                    "expected list", "magl.audit.signatures",
                    f"got {type(signatures).__name__}",
                ))

    # --- MG-R-15: documentation section -----------------------------------------
    documentation = mg.get("documentation")
    if "documentation" in mg:
        if not isinstance(documentation, dict):
            issues.append(_issue(
                "MG-R-15", "field 'magl.documentation' must be a mapping",
                "documentation carries summary/examples/limitations as "
                "sub-fields",
                "magl.documentation", f"got {type(documentation).__name__}",
            ))
            documentation = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["documentation"] - documentation.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "MG-R-15", f"required field 'magl.documentation.{f}' is missing",
                    "required by schema", f"magl.documentation.{f}", "absent",
                ))
            summary = documentation.get("summary")
            if "summary" in documentation and (not isinstance(summary, str) or not summary.strip()):
                issues.append(_issue(
                    "MG-R-15", "field 'magl.documentation.summary' must be "
                    "a non-empty string",
                    "an undescribed MAGL cannot be evaluated by anyone "
                    "downstream",
                    "magl.documentation.summary", summary,
                ))
            limitations = documentation.get("limitations")
            if "limitations" in documentation:
                if not isinstance(limitations, list) or len(limitations) == 0:
                    issues.append(_issue(
                        "MG-R-15", "field 'magl.documentation.limitations' "
                        "must be a non-empty list",
                        "a MAGL declaring zero known limitations is exactly "
                        "the 'beautiful YAML is not evidence' failure mode — "
                        "every real capability has at least one known "
                        "limitation, and omitting all of them is a "
                        "structural defect, not a stylistic gap (mirrors "
                        "blueprint_atom's non-empty acceptance_criteria "
                        "rule)",
                        "magl.documentation.limitations", limitations,
                    ))
    else:
        documentation = {}

    # --- MG-R-16: promotion section + status agreement --------------------------
    promotion = mg.get("promotion")
    current_gate = None
    if "promotion" in mg:
        if not isinstance(promotion, dict):
            issues.append(_issue(
                "MG-R-16", "field 'magl.promotion' must be a mapping",
                "current_gate is a required sub-field",
                "magl.promotion", f"got {type(promotion).__name__}",
            ))
            promotion = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["promotion"] - promotion.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "MG-R-16", f"required field 'magl.promotion.{f}' is missing",
                    "required by schema", f"magl.promotion.{f}", "absent",
                ))
            current_gate = promotion.get("current_gate")
            if "current_gate" in promotion and current_gate not in PROMOTION_STATES:
                issues.append(_issue(
                    "MG-R-16", "field 'magl.promotion.current_gate' has "
                    "invalid enum value",
                    "must be a member of the shared 10-state promotion "
                    "vocabulary",
                    "magl.promotion.current_gate", current_gate,
                ))
            requirements = promotion.get("requirements_for_next_gate")
            if "requirements_for_next_gate" in promotion and not isinstance(requirements, list):
                issues.append(_issue(
                    "MG-R-16", "field 'magl.promotion.requirements_for_next_gate' "
                    "has wrong type",
                    "expected list", "magl.promotion.requirements_for_next_gate",
                    f"got {type(requirements).__name__}",
                ))
    else:
        promotion = {}

    # Agreement check: only meaningful once both sides are actually present
    # (their individual absence is already reported by MG-R-4/MG-R-13/
    # MG-R-16 above).
    if "lifecycle" in mg and "status" in lifecycle and "promotion" in mg and "current_gate" in promotion:
        if lifecycle_status != current_gate:
            issues.append(_issue(
                "MG-R-16", "'magl.lifecycle.status' and "
                "'magl.promotion.current_gate' disagree",
                "a MAGL's declared lifecycle state and its declared "
                "promotion gate must be the same fact stated twice, never "
                "two different claims",
                "magl.lifecycle.status / magl.promotion.current_gate",
                f"lifecycle.status={lifecycle_status!r} "
                f"current_gate={current_gate!r}",
            ))

    # --- unknown fields (never silently trusted) ---------------------------
    known = set(REQUIRED_TOP_FIELDS) | {
        "audit",
        "inputs", "outputs", "dependencies", "assumptions", "unknowns",
        "risks", "controls", "verification", "composition",
    }
    unknown = sorted(mg_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
