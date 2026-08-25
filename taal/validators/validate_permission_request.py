"""
Permission Request Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this permission_request document conform to the declared
     schema, structurally, deterministically, and without executing
     anything it contains?"

It does NOT answer:
    - "Should this request be granted?" (that verdict belongs to the
      root-gate, a different component built by a different agent; this
      validator produces VALID/INVALID structural results only, never a
      grant/deny decision)
    - "Is this request risky?" (risk_hint is recorded, never scored or
      acted on here — see PR-R-8 for the one narrow structural
      combination this validator DOES flag, as a non-fatal WARNING)

A VALID result means "structurally conformant, and not carrying a
self-authorization claim". It is never upgraded to "approved",
"authorized", or "granted" — those are the root-gate's vocabulary, not
this module's.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_permission_request() is a pure function over its input text.
Content found inside `text` is read as DATA throughout — never as an
instruction to this function. `risk_hint` and `justification` in
particular are free text recorded verbatim and never parsed for meaning
or used to change any decision this validator makes.

HARDENING

Same parsing hardening as magl/validators/validate_magl.py and
schema/validator.py, deliberately duplicated rather than imported (house
pattern — each validator owns its own hardening independently):
duplicate-key detection, document-size/node-count/depth ceilings enforced
BEFORE construction, and RecursionError caught explicitly both at compose
time and construct time. validate_permission_request()'s entire body is
wrapped in try/except so an unforeseen exception becomes a structured
INVALID result (PR-R-0) rather than propagating — this closed real bugs
before (failures/FAILURE_ARCHIVE.md F-009/F-010): an uncaught exception
here would be a fail-OPEN bug in whatever calls this validator.

RULE NUMBERING (PR-R-<n>)

  PR-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  PR-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  PR-R-2  top-level 'permission_request' key present and is a mapping
  PR-R-3  mapping contains only string keys (type-confusion class)
  PR-R-4  required top-level fields present
  PR-R-5  string fields non-empty; boolean fields are actual bools;
          action/provenance/reversibility enum membership
  PR-R-6  delegation / delegation_chain agreement: delegation:true
          requires a non-empty delegation_chain list; delegation:false
          requires delegation_chain to be empty or absent (contradiction
          otherwise)
  PR-R-7  delegation_chain, when present, is a list of non-empty strings
  PR-R-8  WARNING (non-fatal): reversibility IRREVERSIBLE + duration
          "indefinite" + action in HIGH_STAKES_ACTIONS is flagged as a
          distinct WARNING-severity Issue in ValidationResult.warnings,
          never folded into the fatal issues list
  PR-R-9  self_authorized:true -> unconditional INVALID (the load-bearing
          rule of this schema; no other field's correctness rescues this)
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

from taal.schema.permission_request import (  # noqa: E402
    ACTIONS,
    BOOLEAN_FIELDS,
    HIGH_STAKES_ACTIONS,
    INDEFINITE_DURATION_VALUE,
    PROVENANCE_VALUES,
    REQUIRED_TOP_FIELDS,
    REVERSIBILITY_VALUES,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_permission_request",
    "MalformedYamlError", "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as
# magl/validators/validate_magl.py / schema/validator.py.
MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64


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
    rule: str       # which rule ("PR-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string
    severity: str = "FATAL"  # "FATAL" (causes INVALID) | "WARNING" (PR-R-8 only)

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence,
                "severity": self.severity}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    request_id: str | None
    issues: list[Issue] = field(default_factory=list)       # FATAL only
    warnings: list[Issue] = field(default_factory=list)      # WARNING only
    unknown_fields: list[str] = field(default_factory=list)
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "request_id": self.request_id,
            "issues": [i.to_dict() for i in self.issues],
            "warnings": [w.to_dict() for w in self.warnings],
            "unknown_fields": self.unknown_fields,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated from magl/validators/validate_magl.py — each
#  validator owns its own parsing hardening independently, the house
#  pattern)
# ─────────────────────────────────────────────────────────────

class _DuplicateKeyError(Exception):
    def __init__(self, key: Any, path: str):
        self.key = key
        self.path = path


class _BoundedSafeLoader(yaml.SafeLoader):
    """SafeLoader only — never yaml.Loader/FullLoader. Extended only to
    reject duplicate mapping keys and to allow node-count/depth bounding."""


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
        # count/depth can be bounded BEFORE constructing — stops
        # anchor/alias fan-out from reaching construction. PyYAML's
        # composer is itself recursive; a sufficiently deep nesting chain
        # blows the Python call stack before MAX_NODES/MAX_DEPTH gets a
        # turn — caught explicitly below, never allowed to propagate.
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


def validate_permission_request(text: str) -> ValidationResult:
    """Deterministic structural validation of a permission_request
    document. Never returns a bare bool, and never raises on real-world
    input — an uncaught exception here would be a fail-OPEN bug in
    whatever calls this. Any unforeseen failure is reported as INVALID
    with rule PR-R-0, never allowed to propagate."""
    try:
        return _validate_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", request_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="PR-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any,
           severity: str = "FATAL") -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule,
                 evidence=repr(evidence)[:200], severity=severity)


def _validate_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value — including risk_hint or justification — is ever interpreted as
    an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", request_id=None, original_text=text)

    # --- PR-R-1: parseable + structural ceilings ----------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "PR-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- PR-R-2: top-level 'permission_request' wrapper ----------------------
    if "permission_request" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "PR-R-2", "top-level 'permission_request' key is missing",
            "every permission request document must be wrapped in a "
            "top-level 'permission_request:' key",
            "permission_request", "absent",
        ))
        return result
    pr = data["permission_request"]
    if not isinstance(pr, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "PR-R-2", "'permission_request' value is not a mapping",
            "the 'permission_request' key must contain a mapping of fields",
            "permission_request", f"got {type(pr).__name__}",
        ))
        return result

    # --- PR-R-3: non-string keys (type-confusion class) ----------------------
    # Content found inside `pr` — including a key literally named
    # "self_authorized" or anything else — is read as DATA below. Field
    # lookups are always by literal string name against the fixed schema.
    non_string_keys = [k for k in pr.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "PR-R-3", "permission_request mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot "
            "be a declared field",
            "permission_request",
            f"key types present: {sorted({type(k).__name__ for k in pr.keys()})}",
        ))

    pr_keys_as_str = {k if isinstance(k, str) else repr(k) for k in pr.keys()}
    request_id = pr.get("id") if isinstance(pr.get("id"), str) else None
    result.request_id = request_id

    issues: list[Issue] = list(result.issues)
    warnings: list[Issue] = []

    # --- PR-R-4: required top-level fields ------------------------------------
    missing = REQUIRED_TOP_FIELDS - pr.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "PR-R-4", f"required field 'permission_request.{f}' is missing",
            "required by schema", f"permission_request.{f}", "absent",
        ))

    # --- PR-R-5: string/boolean fields + enum membership ----------------------
    for f in sorted(STRING_FIELDS):
        if f in pr and (not isinstance(pr[f], str) or not pr[f].strip()):
            issues.append(_issue(
                "PR-R-5", f"field 'permission_request.{f}' must be a "
                "non-empty string",
                "an unstated or blank value cannot represent the ask "
                "precisely",
                f"permission_request.{f}", pr.get(f),
            ))

    for f in sorted(BOOLEAN_FIELDS):
        if f in pr and not isinstance(pr[f], bool):
            issues.append(_issue(
                "PR-R-5", f"field 'permission_request.{f}' must be a "
                "boolean",
                "a truthy non-bool (e.g. the string 'true' or the int 1) "
                "is not the same structural fact as an actual boolean and "
                "is refused rather than coerced",
                f"permission_request.{f}", pr.get(f),
            ))

    action = pr.get("action")
    if "action" in pr and action not in ACTIONS:
        issues.append(_issue(
            "PR-R-5", "field 'permission_request.action' has invalid "
            "enum value",
            f"must be one of {sorted(ACTIONS)}",
            "permission_request.action", action,
        ))

    provenance = pr.get("provenance")
    if "provenance" in pr and provenance not in PROVENANCE_VALUES:
        issues.append(_issue(
            "PR-R-5", "field 'permission_request.provenance' has invalid "
            "enum value",
            f"must be one of {sorted(PROVENANCE_VALUES)}",
            "permission_request.provenance", provenance,
        ))

    reversibility = pr.get("reversibility")
    if "reversibility" in pr and reversibility not in REVERSIBILITY_VALUES:
        issues.append(_issue(
            "PR-R-5", "field 'permission_request.reversibility' has "
            "invalid enum value",
            f"must be one of {sorted(REVERSIBILITY_VALUES)}",
            "permission_request.reversibility", reversibility,
        ))

    # --- PR-R-6/PR-R-7: delegation / delegation_chain agreement --------------
    delegation = pr.get("delegation")
    delegation_chain = pr.get("delegation_chain")
    chain_present = "delegation_chain" in pr
    chain_nonempty_list = isinstance(delegation_chain, list) and len(delegation_chain) > 0

    if isinstance(delegation, bool):
        if delegation is True and not chain_nonempty_list:
            issues.append(_issue(
                "PR-R-6", "delegation:true but delegation_chain is empty "
                "or absent",
                "a request claiming to act on behalf of another must name "
                "the chain of who delegated — an empty chain on a "
                "delegated request is a structural contradiction",
                "permission_request.delegation_chain", delegation_chain,
            ))
        if delegation is False and chain_present and delegation_chain not in (None, []):
            issues.append(_issue(
                "PR-R-6", "delegation:false but delegation_chain is "
                "non-empty",
                "a request declaring no delegation cannot also declare a "
                "chain of who delegated — that is the mirror-image "
                "contradiction to PR-R-6's other half",
                "permission_request.delegation_chain", delegation_chain,
            ))

    if chain_present and delegation_chain is not None:
        if not isinstance(delegation_chain, list):
            issues.append(_issue(
                "PR-R-7", "field 'permission_request.delegation_chain' "
                "has wrong type",
                "expected list", "permission_request.delegation_chain",
                f"got {type(delegation_chain).__name__}",
            ))
        else:
            for entry in delegation_chain:
                if not isinstance(entry, str) or not entry.strip():
                    issues.append(_issue(
                        "PR-R-7", "entry in "
                        "'permission_request.delegation_chain' is not a "
                        "non-empty string",
                        "each chain entry must identify a requester",
                        "permission_request.delegation_chain", entry,
                    ))

    # --- PR-R-8: WARNING — irreversible + indefinite + high-stakes action ----
    duration = pr.get("duration")
    if (
        reversibility == "IRREVERSIBLE"
        and isinstance(duration, str)
        and duration.strip() == INDEFINITE_DURATION_VALUE
        and action in HIGH_STAKES_ACTIONS
    ):
        warnings.append(_issue(
            "PR-R-8", "irreversible + indefinite-duration + high-stakes "
            "action combination",
            "reversibility:IRREVERSIBLE combined with duration:'indefinite' "
            "and action in {DELETE, CONFIGURATION_CHANGE, "
            "CREDENTIAL_ACCESS} is not automatically INVALID — this schema "
            "does not decide authorization — but must never pass silently "
            "through a pipeline unnoticed. Flagged as a distinct "
            "WARNING-severity issue so nothing downstream can miss it.",
            "permission_request", {
                "action": action, "duration": duration,
                "reversibility": reversibility,
            },
            severity="WARNING",
        ))

    # --- PR-R-9: self_authorized -> unconditional INVALID ---------------------
    self_authorized = pr.get("self_authorized")
    if self_authorized is True:
        issues.append(_issue(
            "PR-R-9", "field 'permission_request.self_authorized' is true",
            "a permission_request can never carry a field claiming its "
            "own authorization — that is not what this schema is for. A "
            "request declaring itself pre-authorized is the exact "
            "self-certification pattern this codebase's history exists to "
            "catch (see schema/validator.py's R-10 rule for the identical "
            "shape of defect in a different schema). No other field's "
            "correctness rescues this — the document is rejected outright.",
            "permission_request.self_authorized", self_authorized,
        ))

    # --- unknown fields (never silently trusted) ------------------------------
    known = set(REQUIRED_TOP_FIELDS) | {"delegation_chain", "risk_hint"}
    unknown = sorted(pr_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.warnings = warnings
    result.status = "INVALID" if issues else "VALID"
    return result
