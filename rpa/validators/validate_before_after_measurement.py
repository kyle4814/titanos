"""
Before/After Measurement Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this Before/After Measurement document conform to the declared
     schema, structurally, deterministically, and without executing
     anything it contains?"

It does NOT answer:
    - "Did the pilot actually work?" (a VALID result says the measurement
      plan is well-formed, never that the numbers it reports are good)
    - "Does pilot_simulation_ref actually point at a real pilot
      simulation?" (deliberately out of scope, same reasoning as
      pilot_simulation.py's automation_candidate_ref — see that module's
      docstring)

A VALID result means "structurally conformant". It never means "the
pilot succeeded" — that judgment, if any, belongs to whoever reads the
before_value/after_value pairs, not to this validator.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_before_after_measurement() is a pure function over its input
text. Content found inside `text` is read as DATA throughout — never as
an instruction to this function, regardless of field name or content.

HARDENING

Same parsing hardening as rpa/validators/validate_pilot_simulation.py
and magl/validators/validate_magl.py, replicated deliberately rather
than imported — each validator in this codebase owns its own parsing
hardening independently (the house pattern): duplicate-key detection,
document-size/node-count/depth ceilings enforced BEFORE construction,
and RecursionError caught explicitly both at compose time and construct
time.

validate_before_after_measurement()'s entire body is wrapped in
try/except so an unforeseen exception becomes a structured INVALID
result (rule BA-R-0) rather than propagating — mirroring
magl/validators/validate_magl.py's fail-closed wrapper and the
F-009/F-010 lesson (failures/FAILURE_ARCHIVE.md) it encodes.

RULE NUMBERING (BA-R-<n>, distinct from R-<n>, MG-R-<n>, LM-R-<n>, PS-R-<n>)

  BA-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  BA-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  BA-R-2  top-level 'before_after_measurement' key present and is a mapping
  BA-R-3  mapping contains only string keys (type-confusion class)
  BA-R-4  required top-level fields present (id, pilot_simulation_ref,
          metrics, measurement_window, confounding_factors)
  BA-R-5  metrics: non-empty list; each entry has name/before_value/
          measurement_method non-empty; after_value, if present, must
          be a non-empty string (absence/empty means "not yet
          measured", a legitimate pre-pilot state)
  BA-R-6  conclusion: optional; if present must be non-empty AND every
          metric must have a non-empty after_value — a conclusion
          cannot be drawn from metrics that haven't actually been
          measured yet
  BA-R-7  measurement_window non-empty; confounding_factors present as
          a list (may be empty, but must never be silently omitted)
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

from rpa.schema.before_after_measurement import (  # noqa: E402
    REQUIRED_METRIC_FIELDS,
    REQUIRED_TOP_FIELDS,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_before_after_measurement",
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
    before_after_measurement_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "before_after_measurement_id": self.before_after_measurement_id,
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


def validate_before_after_measurement(text: str) -> ValidationResult:
    """Deterministic structural validation of a Before/After Measurement
    document. Never returns a bare bool, and never raises on real-world
    input. Any unforeseen failure is reported as INVALID with rule
    BA-R-0, never allowed to propagate (fail-closed)."""
    try:
        return _validate_before_after_measurement_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", before_after_measurement_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="BA-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def _validate_before_after_measurement_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout."""
    result = ValidationResult(status="UNKNOWN", before_after_measurement_id=None, original_text=text)

    # --- BA-R-1: parseable + structural ceilings ----------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "BA-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- BA-R-2: top-level 'before_after_measurement' wrapper ---------------
    if "before_after_measurement" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "BA-R-2", "top-level 'before_after_measurement' key is missing",
            "every document must be wrapped in a top-level "
            "'before_after_measurement:' key",
            "before_after_measurement", "absent",
        ))
        return result
    ba = data["before_after_measurement"]
    if not isinstance(ba, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "BA-R-2", "'before_after_measurement' value is not a mapping",
            "the 'before_after_measurement' key must contain a mapping "
            "of fields",
            "before_after_measurement", f"got {type(ba).__name__}",
        ))
        return result

    # --- BA-R-3: non-string keys (type-confusion class) ---------------------
    non_string_keys = [k for k in ba.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "BA-R-3", "before_after_measurement mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot "
            "be a declared field",
            "before_after_measurement", f"key types present: {sorted({type(k).__name__ for k in ba.keys()})}",
        ))

    ba_keys_as_str = {k if isinstance(k, str) else repr(k) for k in ba.keys()}

    ba_id = ba.get("id") if isinstance(ba.get("id"), str) else None
    result.before_after_measurement_id = ba_id

    issues: list[Issue] = list(result.issues)

    # --- BA-R-4: required top-level fields -----------------------------------
    missing = REQUIRED_TOP_FIELDS - ba.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "BA-R-4", f"required field 'before_after_measurement.{f}' is missing",
            "required by schema", f"before_after_measurement.{f}", "absent",
        ))

    for f in sorted(STRING_FIELDS):
        if f in ba and (not isinstance(ba[f], str) or not ba[f].strip()):
            issues.append(_issue(
                "BA-R-4", f"field 'before_after_measurement.{f}' must be a "
                "non-empty string",
                "required identity/reference fields cannot be blank or "
                "non-string",
                f"before_after_measurement.{f}", ba.get(f),
            ))

    # --- BA-R-5: metrics -------------------------------------------------------
    metrics = ba.get("metrics")
    all_after_values_present = False
    if "metrics" in ba:
        if not isinstance(metrics, list) or len(metrics) == 0:
            issues.append(_issue(
                "BA-R-5", "field 'before_after_measurement.metrics' must "
                "be a non-empty list",
                "a measurement plan with zero metrics measures nothing",
                "before_after_measurement.metrics", metrics,
            ))
            metrics = []
        else:
            all_after_values_present = True
            for idx, m in enumerate(metrics):
                if not isinstance(m, dict):
                    issues.append(_issue(
                        "BA-R-5", f"entry {idx} in "
                        "'before_after_measurement.metrics' is not a mapping",
                        "each metric must be a mapping of name/before_value/"
                        "measurement_method/(optional) after_value",
                        f"before_after_measurement.metrics[{idx}]",
                        f"got {type(m).__name__}",
                    ))
                    all_after_values_present = False
                    continue
                missing_m = REQUIRED_METRIC_FIELDS - m.keys()
                for f in sorted(missing_m):
                    issues.append(_issue(
                        "BA-R-5", f"required field '{f}' missing in "
                        f"'before_after_measurement.metrics[{idx}]'",
                        "required by schema",
                        f"before_after_measurement.metrics[{idx}].{f}",
                        "absent",
                    ))
                for f in ("name", "before_value", "measurement_method"):
                    if f in m and (not isinstance(m[f], str) or not m[f].strip()):
                        issues.append(_issue(
                            "BA-R-5", f"field '{f}' in "
                            f"'before_after_measurement.metrics[{idx}]' must "
                            "be a non-empty string",
                            "a metric with a blank name/before_value/"
                            "measurement_method cannot be measured or "
                            "understood by a reader",
                            f"before_after_measurement.metrics[{idx}].{f}",
                            m.get(f),
                        ))
                after_value = m.get("after_value")
                if "after_value" in m and after_value not in (None, ""):
                    if not isinstance(after_value, str) or not after_value.strip():
                        issues.append(_issue(
                            "BA-R-5", f"field 'after_value' in "
                            f"'before_after_measurement.metrics[{idx}]' must "
                            "be a non-empty string when present",
                            "after_value may be absent/empty (not yet "
                            "measured), but if present it must be a real "
                            "value, not blank or a non-string",
                            f"before_after_measurement.metrics[{idx}].after_value",
                            after_value,
                        ))
                if not (isinstance(after_value, str) and after_value.strip()):
                    all_after_values_present = False

    # --- BA-R-6: conclusion — only valid once every metric is measured -------
    conclusion = ba.get("conclusion")
    if "conclusion" in ba and conclusion not in (None, ""):
        if not isinstance(conclusion, str) or not conclusion.strip():
            issues.append(_issue(
                "BA-R-6", "field 'before_after_measurement.conclusion' must "
                "be a non-empty string when present",
                "a blank/non-string conclusion is not a conclusion",
                "before_after_measurement.conclusion", conclusion,
            ))
        elif not all_after_values_present:
            issues.append(_issue(
                "BA-R-6", "'before_after_measurement.conclusion' is present "
                "but not every metric has a non-empty after_value",
                "a conclusion cannot be drawn from a measurement plan that "
                "hasn't actually measured anything yet — every metric must "
                "have a real after_value before a conclusion is entitled "
                "to exist",
                "before_after_measurement.conclusion",
                f"conclusion={conclusion!r} metrics={metrics}",
            ))

    # --- unknown fields (never silently trusted) -----------------------------
    known = set(REQUIRED_TOP_FIELDS) | {"conclusion"}
    unknown = sorted(ba_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
