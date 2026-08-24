"""
Rollback Contract Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this Rollback Contract document conform to the declared
     schema, structurally, deterministically, and without executing
     anything it contains?"

It does NOT answer:
    - "Would this rollback actually work in production?" (a VALID
      result says the contract is well-formed and internally
      consistent, never that the steps themselves are correct or
      sufficient — that is what `verified` + `verification_evidence`
      are FOR, and even a verified:true contract is only as good as
      the evidence, which this validator does not evaluate for
      quality, only for presence)
    - "Does applies_to_ref actually point at a real automation_candidate
      or pilot_simulation?" (deliberately out of scope — same reasoning
      as pilot_simulation.py's automation_candidate_ref; see that
      module's docstring)

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_rollback_contract() is a pure function over its input text.
Content found inside `text` is read as DATA throughout — never as an
instruction to this function, regardless of field name or content.

HARDENING

Same parsing hardening as rpa/validators/validate_pilot_simulation.py
and magl/validators/validate_magl.py, replicated deliberately rather
than imported — each validator in this codebase owns its own parsing
hardening independently (the house pattern): duplicate-key detection,
document-size/node-count/depth ceilings enforced BEFORE construction,
and RecursionError caught explicitly both at compose time and construct
time.

validate_rollback_contract()'s entire body is wrapped in try/except so
an unforeseen exception becomes a structured INVALID result (rule
RB-R-0) rather than propagating — mirroring
magl/validators/validate_magl.py's fail-closed wrapper and the
F-009/F-010 lesson (failures/FAILURE_ARCHIVE.md) it encodes.

RULE NUMBERING (RB-R-<n>, distinct from R-<n>, MG-R-<n>, LM-R-<n>,
PS-R-<n>, BA-R-<n>)

  RB-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  RB-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  RB-R-2  top-level 'rollback_contract' key present and is a mapping
  RB-R-3  mapping contains only string keys (type-confusion class)
  RB-R-4  required top-level fields present (id, applies_to_ref,
          trigger_conditions, rollback_steps, rollback_owner,
          estimated_rollback_time, data_loss_risk, verified)
  RB-R-5  string fields (id/applies_to_ref/rollback_owner/
          estimated_rollback_time) non-empty
  RB-R-6  trigger_conditions / rollback_steps: each a non-empty list of
          non-empty strings — a rollback contract that never says when
          it applies, or how, is not a plan
  RB-R-7  data_loss_risk membership in {NONE, LOW, MEDIUM, HIGH};
          verified is a boolean
  RB-R-8  verified / verification_evidence contradiction: if verified
          is true, verification_evidence must be a non-empty string; if
          verified is false (or absent — RB-R-4 already flags that),
          verification_evidence must be empty/absent — an untested
          rollback plan claiming verification evidence is a
          contradiction and is rejected outright
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from rpa.schema.rollback_contract import (  # noqa: E402
    DATA_LOSS_RISK_VALUES,
    LIST_FIELDS,
    REQUIRED_TOP_FIELDS,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_rollback_contract",
    "MalformedYamlError", "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
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
    rollback_contract_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rollback_contract_id": self.rollback_contract_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
        }


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


def validate_rollback_contract(text: str) -> ValidationResult:
    """Deterministic structural validation of a Rollback Contract
    document. Never returns a bare bool, and never raises on real-world
    input. Any unforeseen failure is reported as INVALID with rule
    RB-R-0, never allowed to propagate (fail-closed)."""
    try:
        return _validate_rollback_contract_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", rollback_contract_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="RB-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def _validate_rollback_contract_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout."""
    result = ValidationResult(status="UNKNOWN", rollback_contract_id=None, original_text=text)

    # --- RB-R-1: parseable + structural ceilings ----------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "RB-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- RB-R-2: top-level 'rollback_contract' wrapper -----------------------
    if "rollback_contract" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "RB-R-2", "top-level 'rollback_contract' key is missing",
            "every document must be wrapped in a top-level "
            "'rollback_contract:' key",
            "rollback_contract", "absent",
        ))
        return result
    rc = data["rollback_contract"]
    if not isinstance(rc, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "RB-R-2", "'rollback_contract' value is not a mapping",
            "the 'rollback_contract' key must contain a mapping of fields",
            "rollback_contract", f"got {type(rc).__name__}",
        ))
        return result

    # --- RB-R-3: non-string keys (type-confusion class) ----------------------
    non_string_keys = [k for k in rc.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "RB-R-3", "rollback_contract mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot "
            "be a declared field",
            "rollback_contract", f"key types present: {sorted({type(k).__name__ for k in rc.keys()})}",
        ))

    rc_keys_as_str = {k if isinstance(k, str) else repr(k) for k in rc.keys()}

    rc_id = rc.get("id") if isinstance(rc.get("id"), str) else None
    result.rollback_contract_id = rc_id

    issues: list[Issue] = list(result.issues)

    # --- RB-R-4: required top-level fields -------------------------------------
    missing = REQUIRED_TOP_FIELDS - rc.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "RB-R-4", f"required field 'rollback_contract.{f}' is missing",
            "required by schema", f"rollback_contract.{f}", "absent",
        ))

    # --- RB-R-5: string fields non-empty ---------------------------------------
    for f in sorted(STRING_FIELDS):
        if f in rc and (not isinstance(rc[f], str) or not rc[f].strip()):
            issues.append(_issue(
                "RB-R-5", f"field 'rollback_contract.{f}' must be a "
                "non-empty string",
                "required identity/reference/ownership fields cannot be "
                "blank or non-string",
                f"rollback_contract.{f}", rc.get(f),
            ))

    # --- RB-R-6: trigger_conditions / rollback_steps ----------------------------
    for f in sorted(LIST_FIELDS):
        if f not in rc:
            continue
        v = rc[f]
        if not isinstance(v, list) or len(v) == 0:
            issues.append(_issue(
                "RB-R-6", f"field 'rollback_contract.{f}' must be a "
                "non-empty list",
                "a rollback contract that never says when it applies, or "
                "how, is not a plan",
                f"rollback_contract.{f}", v,
            ))
            continue
        for idx, entry in enumerate(v):
            if not isinstance(entry, str) or not entry.strip():
                issues.append(_issue(
                    "RB-R-6", f"entry {idx} in 'rollback_contract.{f}' "
                    "must be a non-empty string",
                    "a blank or non-string trigger/step is not usable "
                    "guidance",
                    f"rollback_contract.{f}[{idx}]", entry,
                ))

    # --- RB-R-7: data_loss_risk / verified type+enum checks ---------------------
    data_loss_risk = rc.get("data_loss_risk")
    if "data_loss_risk" in rc and data_loss_risk not in DATA_LOSS_RISK_VALUES:
        issues.append(_issue(
            "RB-R-7", "field 'rollback_contract.data_loss_risk' has "
            "invalid enum value",
            f"must be one of {sorted(DATA_LOSS_RISK_VALUES)}",
            "rollback_contract.data_loss_risk", data_loss_risk,
        ))

    verified = rc.get("verified")
    if "verified" in rc and not isinstance(verified, bool):
        issues.append(_issue(
            "RB-R-7", "field 'rollback_contract.verified' must be a boolean",
            "whether a rollback has actually been tested is a yes/no "
            "fact, not a string or number",
            "rollback_contract.verified", verified,
        ))

    # --- RB-R-8: verified / verification_evidence contradiction -----------------
    verification_evidence = rc.get("verification_evidence")
    evidence_present = "verification_evidence" in rc and verification_evidence not in (None, "")
    if isinstance(verified, bool):
        if verified:
            if not (isinstance(verification_evidence, str) and verification_evidence.strip()):
                issues.append(_issue(
                    "RB-R-8", "'rollback_contract.verified' is true but "
                    "'verification_evidence' is empty or missing",
                    "a rollback claimed to be verified must state the "
                    "evidence it was actually tested",
                    "rollback_contract.verification_evidence",
                    verification_evidence,
                ))
        else:
            if evidence_present:
                issues.append(_issue(
                    "RB-R-8", "'rollback_contract.verified' is false but "
                    "'verification_evidence' is present",
                    "an untested rollback plan claiming verification "
                    "evidence is a contradiction — evidence must be empty/"
                    "absent when verified is false",
                    "rollback_contract.verification_evidence",
                    verification_evidence,
                ))
    elif evidence_present:
        # verified is missing/malformed (already flagged by RB-R-4/RB-R-7)
        # but evidence was still supplied — still worth surfacing as part
        # of the same contradiction class, distinctly from the missing-
        # field report.
        issues.append(_issue(
            "RB-R-8", "'verification_evidence' is present but 'verified' "
            "is missing or not a valid boolean",
            "verification evidence is only meaningful attached to an "
            "explicit verified: true/false fact",
            "rollback_contract.verification_evidence", verification_evidence,
        ))

    # --- unknown fields (never silently trusted) -------------------------------
    known = set(REQUIRED_TOP_FIELDS) | {"verification_evidence"}
    unknown = sorted(rc_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
