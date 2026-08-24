"""
Value Flow Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this value_flow document conform to the declared zero-extraction
     accounting schema, structurally, deterministically, and without
     executing anything it contains?"

It does NOT answer:
    - "Is this a FAIR value flow?" (a human/policy judgment — this
      validator only checks that every extraction structurally answers
      the six required questions, never whether the answers are good
      ones)
    - "Do the amounts actually add up?" (this schema deliberately performs
      no currency math — amount_description fields are free text)
    - "Does system_map_ref point at a real map?" (referential integrity is
      a separate concern this validator does not implement)

HARDENING

Same parsing hardening as magl/validators/validate_magl.py and
rpa/validators/validate_bottleneck.py, replicated deliberately rather
than imported (house pattern: each validator owns its own parsing
hardening independently) — duplicate-key detection, document-size/node-
count/depth ceilings checked BEFORE full construction, RecursionError
caught explicitly during both compose and construct stages, and a
fail-closed outer wrapper converting any unforeseen exception to a
structured INVALID result rather than letting it propagate. This
replicates the fix for failures/FAILURE_ARCHIVE.md F-009 (uncaught
RecursionError failing OPEN past the validator) and F-010 (uncaught
TypeError on non-string YAML keys, found against real corpus data).

RULE NUMBERING (VF-R-<n>)

  VF-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  VF-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  VF-R-2  top-level 'value_flow' key present and a mapping
  VF-R-3  mapping contains only string keys (type-confusion class)
  VF-R-4  required top-level fields present
  VF-R-5  identity string fields (id/system_map_ref/period) non-empty
          where present
  VF-R-6  necessary_consumption must be a non-empty list — a value flow
          declaring zero necessary consumption is itself rejected as
          structurally suspicious (nothing real runs on zero cost)
  VF-R-7  each necessary_consumption[] entry: category/amount_description/
          basis all present and non-empty; category must be a member of
          NECESSARY_CONSUMPTION_CATEGORIES
  VF-R-8  each value_created[] entry: source/amount_description present
          and non-empty
  VF-R-9  THE CORE RULE. Each extractions[] entry missing ANY of
          recipient/reason/authority/contribution/limit/audit_mechanism
          is rejected — the literal enforcement of "every extraction must
          answer these six questions". `id` must also be a non-empty
          string and `reviewable` must be a bool.
  VF-R-10 an extractions[] entry with reviewable == False is flagged as a
          WARNING-level issue, not by itself INVALID — see
          _WARNING_RULES / judgment call documented below
  VF-R-11 each reinvestment[]/reserved[]/returned[] entry has its
          required sub-fields present and non-empty
  VF-R-12 undeclared_leakage_flag/leakage_description consistency: if the
          flag is true, leakage_description must be a non-empty string;
          if false, leakage_description must be absent or empty/blank

JUDGMENT CALL — SEVERITY OF reviewable: false (VF-R-10)

An unreviewable extraction is exactly the "uninspectable rent-seeking"
the zero-extraction model exists to forbid at the level of a single
extraction entry. But the document as a WHOLE remains structurally
well-formed and legible — the six required questions are still answered
for that entry, it merely also declares that it cannot be reviewed. That
declaration is itself useful signal (an honest "this cannot be audited"
beats a silently-omitted one), and failing the entire document would
create an incentive to omit `reviewable` truthfulness rather than admit
it. So VF-R-10 is implemented as a WARNING-severity issue attached to a
document that can otherwise still reach VALID — the validator surfaces it
loudly (via `warnings` on the result, always populated even when
`status == "VALID"`) rather than burying it inside a document-wide
INVALID a caller might triage without reading. A downstream policy layer
(not this validator) is the right place to decide whether "VALID with
unreviewable extractions" is an acceptable state to act on.
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

from rpa.schema.value_flow import (  # noqa: E402
    NECESSARY_CONSUMPTION_CATEGORIES,
    REQUIRED_EXTRACTION_FIELDS,
    REQUIRED_NECESSARY_CONSUMPTION_FIELDS,
    REQUIRED_REINVESTMENT_FIELDS,
    REQUIRED_RESERVED_FIELDS,
    REQUIRED_RETURNED_FIELDS,
    REQUIRED_TOP_FIELDS,
    REQUIRED_VALUE_CREATED_FIELDS,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_value_flow", "MalformedYamlError",
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
    severity: str = "ERROR"  # "ERROR" | "WARNING" — see VF-R-10 doc above

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence,
                "severity": self.severity}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    value_flow_id: str | None
    issues: list[Issue] = field(default_factory=list)      # ERROR-severity only
    warnings: list[Issue] = field(default_factory=list)     # WARNING-severity only
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "value_flow_id": self.value_flow_id,
            "issues": [i.to_dict() for i in self.issues],
            "warnings": [w.to_dict() for w in self.warnings],
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated — house pattern)
# ─────────────────────────────────────────────────────────────

class _DuplicateKeyError(Exception):
    def __init__(self, key: Any, path: str):
        self.key = key
        self.path = path


class _BoundedSafeLoader(yaml.SafeLoader):
    """SafeLoader only — never yaml.Loader/FullLoader. Extended only to
    reject duplicate mapping keys and support node-count/depth bounding."""


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


def _issue(rule: str, what: str, why: str, where: str, evidence: Any,
           severity: str = "ERROR") -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule,
                 evidence=repr(evidence)[:200], severity=severity)


def validate_value_flow(text: str) -> ValidationResult:
    """Deterministic structural validation of a value_flow document. Never
    returns a bare bool, and never raises on real-world input — fail-closed
    outer wrapper mirroring validate_bottleneck.py / validate_magl.py and
    the F-009/F-010 lesson."""
    try:
        return _validate_value_flow_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", value_flow_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="VF-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _check_list_of_records(
    container: Any, top_key: str, required_fields: frozenset[str], rule: str,
    id_field: str | None = None,
) -> list[Issue]:
    """Shared shape-check for value_created/necessary_consumption/
    reinvestment/reserved/returned: each entry must be a mapping with all
    required_fields present and non-empty-string (id_field, if given, is
    checked the same way as any other required string field — this helper
    does not special-case it beyond documentation)."""
    issues: list[Issue] = []
    if not isinstance(container, list):
        issues.append(_issue(
            rule, f"field '{top_key}' has wrong type", "expected list",
            top_key, f"got {type(container).__name__}",
        ))
        return issues
    for idx, entry in enumerate(container):
        where = f"{top_key}[{idx}]"
        if not isinstance(entry, dict):
            issues.append(_issue(
                rule, f"entry in '{top_key}' is not a mapping",
                "each entry must be a mapping of its required fields",
                where, f"got {type(entry).__name__}",
            ))
            continue
        missing = required_fields - entry.keys()
        for f in sorted(missing):
            issues.append(_issue(
                rule, f"required field '{f}' missing from '{where}'",
                "required by schema", f"{where}.{f}", "absent",
            ))
        for f in sorted(required_fields):
            if f in entry and (not isinstance(entry[f], str) or not entry[f].strip()):
                issues.append(_issue(
                    rule, f"field '{where}.{f}' must be a non-empty string",
                    "required field cannot be blank or non-string",
                    f"{where}.{f}", entry.get(f),
                ))
    return issues


def _validate_value_flow_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", value_flow_id=None, original_text=text)

    # --- VF-R-1: parseable + structural ceilings ------------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "VF-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- VF-R-2: top-level wrapper present and a mapping ----------------------
    if "value_flow" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "VF-R-2", "top-level 'value_flow' key is missing",
            "every value flow document must be wrapped in a top-level "
            "'value_flow:' key",
            "value_flow", "absent",
        ))
        return result
    vf = data["value_flow"]
    if not isinstance(vf, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "VF-R-2", "'value_flow' value is not a mapping",
            "the key must contain a mapping of fields",
            "value_flow", f"got {type(vf).__name__}",
        ))
        return result

    # --- VF-R-3: non-string keys (type-confusion class) ------------------------
    non_string_keys = [k for k in vf.keys() if not isinstance(k, str)]
    issues: list[Issue] = []
    warnings: list[Issue] = []
    if non_string_keys:
        issues.append(_issue(
            "VF-R-3", "value_flow mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot be "
            "a declared field",
            "value_flow", f"key types present: {sorted({type(k).__name__ for k in vf.keys()})}",
        ))

    value_flow_id = vf.get("id") if isinstance(vf.get("id"), str) else None
    result.value_flow_id = value_flow_id

    # --- VF-R-4: required top-level fields --------------------------------------
    missing = REQUIRED_TOP_FIELDS - vf.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "VF-R-4", f"required field 'value_flow.{f}' is missing",
            "required by schema", f"value_flow.{f}", "absent",
        ))

    # --- VF-R-5: identity string fields non-empty --------------------------------
    for f in sorted(STRING_FIELDS):
        if f in vf and (not isinstance(vf[f], str) or not vf[f].strip()):
            issues.append(_issue(
                "VF-R-5", f"field 'value_flow.{f}' must be a non-empty string",
                "identity fields cannot be blank or non-string",
                f"value_flow.{f}", vf.get(f),
            ))

    # --- VF-R-6: necessary_consumption must be non-empty ------------------------
    necessary_consumption = vf.get("necessary_consumption")
    if "necessary_consumption" in vf:
        if not isinstance(necessary_consumption, list) or not necessary_consumption:
            issues.append(_issue(
                "VF-R-6", "field 'value_flow.necessary_consumption' must be "
                "a non-empty list",
                "a value flow declaring zero necessary consumption is "
                "itself structurally suspicious — nothing real runs on "
                "zero cost; an empty list here is treated as hidden "
                "extraction, not as a legitimate zero-cost operation",
                "value_flow.necessary_consumption", necessary_consumption,
            ))
        else:
            # --- VF-R-7: necessary_consumption[] entry shape --------------------
            issues.extend(_check_list_of_records(
                necessary_consumption, "value_flow.necessary_consumption",
                REQUIRED_NECESSARY_CONSUMPTION_FIELDS, "VF-R-7",
            ))
            for idx, entry in enumerate(necessary_consumption):
                if isinstance(entry, dict) and "category" in entry:
                    cat = entry.get("category")
                    if cat not in NECESSARY_CONSUMPTION_CATEGORIES:
                        issues.append(_issue(
                            "VF-R-7", "field "
                            f"'value_flow.necessary_consumption[{idx}].category' "
                            "has invalid enum value",
                            f"must be one of {sorted(NECESSARY_CONSUMPTION_CATEGORIES)}",
                            f"value_flow.necessary_consumption[{idx}].category", cat,
                        ))

    # --- VF-R-8: value_created[] entry shape -------------------------------------
    value_created = vf.get("value_created")
    if "value_created" in vf:
        issues.extend(_check_list_of_records(
            value_created, "value_flow.value_created",
            REQUIRED_VALUE_CREATED_FIELDS, "VF-R-8",
        ))

    # --- VF-R-9: extractions[] — THE CORE RULE -----------------------------------
    extractions = vf.get("extractions")
    if "extractions" in vf:
        if not isinstance(extractions, list):
            issues.append(_issue(
                "VF-R-9", "field 'value_flow.extractions' has wrong type",
                "expected list", "value_flow.extractions",
                f"got {type(extractions).__name__}",
            ))
        else:
            for idx, entry in enumerate(extractions):
                where = f"value_flow.extractions[{idx}]"
                if not isinstance(entry, dict):
                    issues.append(_issue(
                        "VF-R-9", f"entry in 'value_flow.extractions' is not "
                        "a mapping",
                        "each extraction must be a mapping of its required "
                        "fields",
                        where, f"got {type(entry).__name__}",
                    ))
                    continue
                missing_fields = REQUIRED_EXTRACTION_FIELDS - entry.keys()
                for f in sorted(missing_fields):
                    issues.append(_issue(
                        "VF-R-9", f"required field '{f}' missing from '{where}'",
                        "every extraction must structurally answer WHO "
                        "(recipient), WHY (reason), UNDER WHAT AUTHORITY "
                        "(authority), WHAT DID THEY CONTRIBUTE "
                        "(contribution), WHAT IS THE LIMIT (limit), and HOW "
                        "IS IT AUDITED (audit_mechanism) — a missing field "
                        "here is an unanswered question, not an omission "
                        "this validator can let slide",
                        f"{where}.{f}", "absent",
                    ))
                for f in ("id", "recipient", "reason", "authority",
                          "contribution", "limit", "audit_mechanism"):
                    if f in entry and (not isinstance(entry[f], str) or not entry[f].strip()):
                        issues.append(_issue(
                            "VF-R-9", f"field '{where}.{f}' must be a "
                            "non-empty string",
                            "required field cannot be blank or non-string",
                            f"{where}.{f}", entry.get(f),
                        ))
                reviewable = entry.get("reviewable")
                if "reviewable" in entry and not isinstance(reviewable, bool):
                    issues.append(_issue(
                        "VF-R-9", f"field '{where}.reviewable' must be a boolean",
                        "reviewable is a strict yes/no answer to 'can it "
                        "be reviewed', not a free-text field",
                        f"{where}.reviewable", f"got {type(reviewable).__name__}",
                    ))
                # --- VF-R-10: reviewable == False -> WARNING, not fatal ---------
                elif reviewable is False:
                    warnings.append(_issue(
                        "VF-R-10", f"extraction '{where}' is flagged as "
                        "not reviewable",
                        "an unreviewable extraction is exactly the "
                        "uninspectable rent-seeking the zero-extraction "
                        "model forbids; flagged loudly as a WARNING rather "
                        "than invalidating the whole document — see the "
                        "judgment call documented in this validator's "
                        "module docstring",
                        f"{where}.reviewable", False, severity="WARNING",
                    ))

    # --- VF-R-11: reinvestment/reserved/returned shape ---------------------------
    if "reinvestment" in vf:
        issues.extend(_check_list_of_records(
            vf.get("reinvestment"), "value_flow.reinvestment",
            REQUIRED_REINVESTMENT_FIELDS, "VF-R-11",
        ))
    if "reserved" in vf:
        issues.extend(_check_list_of_records(
            vf.get("reserved"), "value_flow.reserved",
            REQUIRED_RESERVED_FIELDS, "VF-R-11",
        ))
    if "returned" in vf:
        issues.extend(_check_list_of_records(
            vf.get("returned"), "value_flow.returned",
            REQUIRED_RETURNED_FIELDS, "VF-R-11",
        ))

    # --- VF-R-12: undeclared_leakage_flag / leakage_description consistency ----
    leakage_flag = vf.get("undeclared_leakage_flag")
    leakage_description = vf.get("leakage_description")
    if "undeclared_leakage_flag" in vf and not isinstance(leakage_flag, bool):
        issues.append(_issue(
            "VF-R-12", "field 'value_flow.undeclared_leakage_flag' must be a boolean",
            "strict yes/no flag, not a free-text field",
            "value_flow.undeclared_leakage_flag", f"got {type(leakage_flag).__name__}",
        ))
    else:
        has_description = isinstance(leakage_description, str) and leakage_description.strip()
        if leakage_flag is True and not has_description:
            issues.append(_issue(
                "VF-R-12", "'undeclared_leakage_flag' is true but "
                "'leakage_description' is missing or empty",
                "a declared leakage flag with no description is an "
                "admission with no content — the description is required "
                "the moment the flag is raised",
                "value_flow.leakage_description", leakage_description,
            ))
        if leakage_flag is False and has_description:
            issues.append(_issue(
                "VF-R-12", "'undeclared_leakage_flag' is false but "
                "'leakage_description' is present",
                "a false flag with a leakage description attached is a "
                "contradiction — either the flag or the description is "
                "wrong, and this validator cannot silently pick one",
                "value_flow.leakage_description", leakage_description,
            ))

    result.issues = issues
    result.warnings = warnings
    result.status = "INVALID" if issues else "VALID"
    return result
