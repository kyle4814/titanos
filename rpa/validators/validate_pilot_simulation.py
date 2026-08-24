"""
Pilot Simulation Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this Pilot Simulation document conform to the declared schema,
     structurally, deterministically, and without executing anything it
     contains?"

It does NOT answer:
    - "Is this pilot a good idea?" (human/organisational judgment — the
      quality of proposed_change/expected_benefit is never scored here)
    - "Does automation_candidate_ref/rollback_plan_ref/measurement_plan_ref
      actually point at a real, valid document?" (deliberately out of
      scope — see pilot_simulation.py's module docstring; this is a
      pure, single-document structural validator, not a cross-file
      resolver)
    - "Has this pilot actually run, and did it work?" (that's
      before_after_measurement's job, not this one)

A VALID result means "structurally conformant". It is never upgraded to
"approved", "safe to pilot", or "will work" — those are other systems'
vocabulary, and even within this schema, VALID and status ==
APPROVED_FOR_PILOT are two different claims (see PS-R-9).

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_pilot_simulation() is a pure function over its input text.
Content found inside `text` is read as DATA throughout — never as an
instruction to this function, regardless of field name or content. No
field value changes control flow; every field is looked up by NAME
against the fixed schema.

HARDENING

Same parsing hardening as magl/validators/validate_magl.py and
rpa/validators/validate_legacy_system_map.py, replicated deliberately
rather than imported — each validator in this codebase owns its own
parsing hardening independently (the house pattern): duplicate-key
detection, document-size/node-count/depth ceilings enforced BEFORE
construction (to defeat alias/anchor expansion), and RecursionError
caught explicitly both at compose time and construct time, because
PyYAML's composer is itself recursive and can blow the Python call
stack before our own ceiling check gets a turn.

validate_pilot_simulation()'s entire body is wrapped in try/except so an
unforeseen exception becomes a structured INVALID result (rule PS-R-0)
rather than propagating — mirroring magl/validators/validate_magl.py's
fail-closed wrapper and the F-009/F-010 lesson
(failures/FAILURE_ARCHIVE.md) it encodes: an uncaught exception here
would be a fail-OPEN bug in whatever calls this validator.

RULE NUMBERING (PS-R-<n>, distinct from R-<n>, MG-R-<n>, LM-R-<n>)

  PS-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  PS-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  PS-R-2  top-level 'pilot_simulation' key present and is a mapping
  PS-R-3  mapping contains only string keys (type-confusion class)
  PS-R-4  required top-level fields present
  PS-R-5  string fields (id/automation_candidate_ref/proposed_change/
          expected_benefit/rollback_plan_ref/measurement_plan_ref)
          non-empty
  PS-R-6  baseline section: description non-empty, metrics[] shape and
          per-entry required fields (name, current_value)
  PS-R-7  known_risks: non-empty list ("cannot claim zero risks" — same
          reasoning as automation_candidate)
  PS-R-8  failure_scenarios: non-empty list; each entry has scenario/
          likelihood/impact/detection_method, likelihood in
          {LOW,MEDIUM,HIGH,UNKNOWN}, impact in
          {LOW,MEDIUM,HIGH,SEVERE}, detection_method non-empty
  PS-R-9  status membership AND, when status == APPROVED_FOR_PILOT, the
          explicit completeness check: failure_scenarios non-empty with
          every entry's detection_method non-empty, AND
          rollback_plan_ref non-empty, AND measurement_plan_ref
          non-empty. Written as its own explicit check (not merely
          relied upon via PS-R-4/PS-R-8's field-level requirements) so
          that a human reading this validator sees "APPROVED_FOR_PILOT
          has extra teeth" stated directly.
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

from rpa.schema.pilot_simulation import (  # noqa: E402
    IMPACT_VALUES,
    LIKELIHOOD_VALUES,
    LIST_FIELDS,
    REQUIRED_BASELINE_FIELDS,
    REQUIRED_FAILURE_SCENARIO_FIELDS,
    REQUIRED_METRIC_FIELDS,
    REQUIRED_TOP_FIELDS,
    STATUS_VALUES,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_pilot_simulation",
    "MalformedYamlError", "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as
# magl/validators/validate_magl.py / rpa/validators/validate_legacy_system_map.py.
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
    rule: str       # which rule ("PS-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    pilot_simulation_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    # Preservation invariant: original input is carried through untouched.
    # validate_pilot_simulation() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "pilot_simulation_id": self.pilot_simulation_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated from magl/validators/validate_magl.py rather
#  than imported — each validator owns its own parsing hardening
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


def validate_pilot_simulation(text: str) -> ValidationResult:
    """Deterministic structural validation of a Pilot Simulation document.
    Never returns a bare bool, and never raises on real-world input — an
    uncaught exception here would be a fail-OPEN bug in whatever calls
    this. Any unforeseen failure is reported as INVALID with rule PS-R-0,
    never allowed to propagate (fail-closed, mirroring
    magl/validators/validate_magl.py's outer wrapper and the F-009/F-010
    lesson it encodes)."""
    try:
        return _validate_pilot_simulation_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", pilot_simulation_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="PS-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def _validate_pilot_simulation_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", pilot_simulation_id=None, original_text=text)

    # --- PS-R-1: parseable + structural ceilings ---------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "PS-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- PS-R-2: top-level 'pilot_simulation' wrapper present and a mapping --
    if "pilot_simulation" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "PS-R-2", "top-level 'pilot_simulation' key is missing",
            "every Pilot Simulation document must be wrapped in a "
            "top-level 'pilot_simulation:' key",
            "pilot_simulation", "absent",
        ))
        return result
    ps = data["pilot_simulation"]
    if not isinstance(ps, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "PS-R-2", "'pilot_simulation' value is not a mapping",
            "the 'pilot_simulation' key must contain a mapping of fields",
            "pilot_simulation", f"got {type(ps).__name__}",
        ))
        return result

    # --- PS-R-3: non-string keys (type-confusion class) --------------------
    non_string_keys = [k for k in ps.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "PS-R-3", "pilot_simulation mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot "
            "be a declared field",
            "pilot_simulation", f"key types present: {sorted({type(k).__name__ for k in ps.keys()})}",
        ))

    ps_keys_as_str = {k if isinstance(k, str) else repr(k) for k in ps.keys()}

    ps_id = ps.get("id") if isinstance(ps.get("id"), str) else None
    result.pilot_simulation_id = ps_id

    issues: list[Issue] = list(result.issues)

    # --- PS-R-4: required top-level fields ----------------------------------
    missing = REQUIRED_TOP_FIELDS - ps.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "PS-R-4", f"required field 'pilot_simulation.{f}' is missing",
            "required by schema", f"pilot_simulation.{f}", "absent",
        ))

    # --- PS-R-5: string fields non-empty ------------------------------------
    for f in sorted(STRING_FIELDS):
        if f in ps and (not isinstance(ps[f], str) or not ps[f].strip()):
            issues.append(_issue(
                "PS-R-5", f"field 'pilot_simulation.{f}' must be a non-empty string",
                "required identity/reference fields cannot be blank or "
                "non-string",
                f"pilot_simulation.{f}", ps.get(f),
            ))

    # --- PS-R-6: baseline section --------------------------------------------
    baseline = ps.get("baseline")
    if "baseline" in ps:
        if not isinstance(baseline, dict):
            issues.append(_issue(
                "PS-R-6", "field 'pilot_simulation.baseline' must be a mapping",
                "baseline carries description/metrics as sub-fields",
                "pilot_simulation.baseline", f"got {type(baseline).__name__}",
            ))
            baseline = {}
        else:
            missing_nested = REQUIRED_BASELINE_FIELDS - baseline.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "PS-R-6", f"required field 'pilot_simulation.baseline.{f}' is missing",
                    "the current-state performance/behaviour must be "
                    "described before any change is proposed",
                    f"pilot_simulation.baseline.{f}", "absent",
                ))
            description = baseline.get("description")
            if "description" in baseline and (not isinstance(description, str) or not description.strip()):
                issues.append(_issue(
                    "PS-R-6", "field 'pilot_simulation.baseline.description' "
                    "must be a non-empty string",
                    "a pilot with no stated baseline has nothing to compare "
                    "results against",
                    "pilot_simulation.baseline.description", description,
                ))
            metrics = baseline.get("metrics")
            if "metrics" in baseline:
                if not isinstance(metrics, list):
                    issues.append(_issue(
                        "PS-R-6", "field 'pilot_simulation.baseline.metrics' has wrong type",
                        "expected list", "pilot_simulation.baseline.metrics",
                        f"got {type(metrics).__name__}",
                    ))
                else:
                    for idx, m in enumerate(metrics):
                        if not isinstance(m, dict):
                            issues.append(_issue(
                                "PS-R-6", f"entry {idx} in "
                                "'pilot_simulation.baseline.metrics' is not a mapping",
                                "each metric must be a mapping of name/current_value",
                                f"pilot_simulation.baseline.metrics[{idx}]",
                                f"got {type(m).__name__}",
                            ))
                            continue
                        missing_m = REQUIRED_METRIC_FIELDS - m.keys()
                        for f in sorted(missing_m):
                            issues.append(_issue(
                                "PS-R-6", f"required field '{f}' missing in "
                                f"'pilot_simulation.baseline.metrics[{idx}]'",
                                "required by schema",
                                f"pilot_simulation.baseline.metrics[{idx}].{f}",
                                "absent",
                            ))
                        for f in ("name", "current_value"):
                            if f in m and (not isinstance(m[f], str) or not m[f].strip()):
                                issues.append(_issue(
                                    "PS-R-6", f"field '{f}' in "
                                    f"'pilot_simulation.baseline.metrics[{idx}]' "
                                    "must be a non-empty string",
                                    "a named metric with no current value "
                                    "measures nothing",
                                    f"pilot_simulation.baseline.metrics[{idx}].{f}",
                                    m.get(f),
                                ))

    # --- PS-R-7: known_risks non-empty ---------------------------------------
    known_risks = ps.get("known_risks")
    if "known_risks" in ps:
        if not isinstance(known_risks, list) or len(known_risks) == 0:
            issues.append(_issue(
                "PS-R-7", "field 'pilot_simulation.known_risks' must be a "
                "non-empty list",
                "a pilot claiming zero risks is not a credible simulation "
                "— every real change carries at least one known risk",
                "pilot_simulation.known_risks", known_risks,
            ))

    # --- PS-R-8: failure_scenarios -------------------------------------------
    failure_scenarios = ps.get("failure_scenarios")
    all_detection_methods_present = False
    if "failure_scenarios" in ps:
        if not isinstance(failure_scenarios, list) or len(failure_scenarios) == 0:
            issues.append(_issue(
                "PS-R-8", "field 'pilot_simulation.failure_scenarios' must "
                "be a non-empty list",
                "a pilot with no enumerated failure scenarios has not "
                "actually simulated anything",
                "pilot_simulation.failure_scenarios", failure_scenarios,
            ))
            failure_scenarios = []
        else:
            all_detection_methods_present = True
            for idx, fs in enumerate(failure_scenarios):
                if not isinstance(fs, dict):
                    issues.append(_issue(
                        "PS-R-8", f"entry {idx} in "
                        "'pilot_simulation.failure_scenarios' is not a mapping",
                        "each failure scenario must be a mapping of "
                        "scenario/likelihood/impact/detection_method",
                        f"pilot_simulation.failure_scenarios[{idx}]",
                        f"got {type(fs).__name__}",
                    ))
                    all_detection_methods_present = False
                    continue
                missing_fs = REQUIRED_FAILURE_SCENARIO_FIELDS - fs.keys()
                for f in sorted(missing_fs):
                    issues.append(_issue(
                        "PS-R-8", f"required field '{f}' missing in "
                        f"'pilot_simulation.failure_scenarios[{idx}]'",
                        "required by schema",
                        f"pilot_simulation.failure_scenarios[{idx}].{f}",
                        "absent",
                    ))
                    all_detection_methods_present = False
                scenario = fs.get("scenario")
                if "scenario" in fs and (not isinstance(scenario, str) or not scenario.strip()):
                    issues.append(_issue(
                        "PS-R-8", f"field 'scenario' in "
                        f"'pilot_simulation.failure_scenarios[{idx}]' must "
                        "be a non-empty string",
                        "an unnamed failure scenario cannot be reasoned about",
                        f"pilot_simulation.failure_scenarios[{idx}].scenario",
                        scenario,
                    ))
                likelihood = fs.get("likelihood")
                if "likelihood" in fs and likelihood not in LIKELIHOOD_VALUES:
                    issues.append(_issue(
                        "PS-R-8", f"field 'likelihood' in "
                        f"'pilot_simulation.failure_scenarios[{idx}]' has "
                        "invalid enum value",
                        f"must be one of {sorted(LIKELIHOOD_VALUES)}",
                        f"pilot_simulation.failure_scenarios[{idx}].likelihood",
                        likelihood,
                    ))
                impact = fs.get("impact")
                if "impact" in fs and impact not in IMPACT_VALUES:
                    issues.append(_issue(
                        "PS-R-8", f"field 'impact' in "
                        f"'pilot_simulation.failure_scenarios[{idx}]' has "
                        "invalid enum value",
                        f"must be one of {sorted(IMPACT_VALUES)}",
                        f"pilot_simulation.failure_scenarios[{idx}].impact",
                        impact,
                    ))
                detection_method = fs.get("detection_method")
                if not isinstance(detection_method, str) or not detection_method.strip():
                    all_detection_methods_present = False
                    if "detection_method" in fs:
                        issues.append(_issue(
                            "PS-R-8", f"field 'detection_method' in "
                            f"'pilot_simulation.failure_scenarios[{idx}]' "
                            "must be a non-empty string",
                            "a failure scenario with no stated detection "
                            "method describes a failure nobody would "
                            "notice happened",
                            f"pilot_simulation.failure_scenarios[{idx}].detection_method",
                            detection_method,
                        ))

    # --- PS-R-9: status membership + APPROVED_FOR_PILOT completeness --------
    status = ps.get("status")
    if "status" in ps and status not in STATUS_VALUES:
        issues.append(_issue(
            "PS-R-9", "field 'pilot_simulation.status' has invalid enum value",
            f"must be one of {sorted(STATUS_VALUES)}",
            "pilot_simulation.status", status,
        ))

    # Explicit, standalone completeness check — deliberately NOT merely
    # inferred from the field-level requirements enforced above (PS-R-4,
    # PS-R-8), so a human reading this validator sees "APPROVED_FOR_PILOT
    # has extra teeth" stated directly, not merely implied by other rules
    # happening to have already fired.
    if status == "APPROVED_FOR_PILOT":
        rollback_ref = ps.get("rollback_plan_ref")
        measurement_ref = ps.get("measurement_plan_ref")
        completeness_failures: list[str] = []
        if not (isinstance(failure_scenarios, list) and len(failure_scenarios) > 0):
            completeness_failures.append("failure_scenarios is empty or missing")
        elif not all_detection_methods_present:
            completeness_failures.append(
                "one or more failure_scenarios entries lack a non-empty "
                "detection_method"
            )
        if not (isinstance(rollback_ref, str) and rollback_ref.strip()):
            completeness_failures.append("rollback_plan_ref is empty or missing")
        if not (isinstance(measurement_ref, str) and measurement_ref.strip()):
            completeness_failures.append("measurement_plan_ref is empty or missing")
        if completeness_failures:
            issues.append(_issue(
                "PS-R-9", "status 'APPROVED_FOR_PILOT' declared without "
                "meeting its completeness requirements",
                "a pilot cannot be approved for real-world execution "
                "unless every failure scenario has a stated detection "
                "method AND a rollback plan AND a measurement plan are "
                "both referenced — this is checked explicitly here, not "
                "left implicit",
                "pilot_simulation.status", "; ".join(completeness_failures),
            ))

    # --- unknown fields (never silently trusted) ---------------------------
    known = set(REQUIRED_TOP_FIELDS)
    unknown = sorted(ps_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
