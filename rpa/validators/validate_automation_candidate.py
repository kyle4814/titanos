"""
Automation Candidate Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this automation_candidate document conform to the declared
     schema, structurally, deterministically, and without executing
     anything it contains?"

It does NOT answer:
    - "Should this automation be built?" (human judgment)
    - "Is bottleneck_ref/system_map_ref a real, existing record?" (no
      cross-file validation — see rpa/schema/automation_candidate.py's
      docstring; this validator treats both as opaque strings)
    - "Is this candidate authorized to pilot?" (that is
      rpa/gates/human_jurisdiction.py's job, built on top of
      kpm.promotion.state_machine — a structurally VALID candidate is not
      an authorized one)

A VALID result means "structurally conformant". It is never upgraded to
"approved", "authorized to pilot", or "safe to run" — those are other
systems' vocabulary.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_automation_candidate() is a pure function over its input text.
Content found inside `text` is read as DATA throughout — never as an
instruction to this function, regardless of field name or content. No
field value changes control flow; every field is looked up by NAME
against the fixed schema.

HARDENING

Same parsing hardening as magl/validators/validate_magl.py and
kpm/validators/validate_blueprint.py, replicated deliberately rather than
imported — each validator in this codebase owns its own parsing
hardening independently (the house pattern): duplicate-key detection,
document-size/node-count/depth ceilings enforced BEFORE construction (to
defeat alias/anchor expansion), and RecursionError caught explicitly both
at compose time and construct time.

validate_automation_candidate()'s entire body is wrapped in try/except so
an unforeseen exception becomes a structured INVALID result (rule AC-R-0)
rather than propagating — mirroring the other validators' fail-closed
outer wrapper and the F-009/F-010 lesson (failures/FAILURE_ARCHIVE.md) it
encodes.

RULE NUMBERING (AC-R-<n>, distinct from R-<n>, BP-R-<n>, MG-R-<n>, BN-R-<n>)

  AC-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  AC-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  AC-R-2  top-level 'automation_candidate' key present and is a mapping
  AC-R-3  mapping contains only string keys (type-confusion class)
  AC-R-4  required top-level fields present
  AC-R-5  identity/scope string fields non-empty
  AC-R-6  epistemic_status membership (imported from
          kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS)
  AC-R-7  proposed_jurisdiction section: mapping shape, list-shape of all
          sub-fields (mirrors MG-R-10)
  AC-R-8  automation_scope <-> proposed_jurisdiction breadth contradiction:
          OBSERVATION_ONLY with any non-empty may_write/may_execute/
          may_call/may_modify, OR FULL_WORKFLOW_AUTOMATION with zero
          non-empty acting jurisdiction fields (mirrors magl's MG-R-11)
  AC-R-9  requires_human_approval / reversible / irreversibility_acknowledged
          boolean shape
  AC-R-10 requires_human_approval must be true when automation_scope is
          SMALL_BOUNDED_AUTOMATION or FULL_WORKFLOW_AUTOMATION — a
          candidate proposing real write/execute/modify jurisdiction
          cannot self-authorize past the human gate
  AC-R-11 rollback_plan required non-empty when reversible is true;
          irreversibility_acknowledged required true when reversible is
          false (mirrors kpm/validators/validate_blueprint.py's
          rollback.reversible pattern)
  AC-R-12 known_risks must be a non-empty list — a candidate with zero
          acknowledged risks is exactly the "beautiful proposal, no
          evidence of self-scrutiny" pattern this codebase's doctrine
          warns against elsewhere (mirrors MG-R-15's non-empty
          limitations rule)
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

from rpa.schema.automation_candidate import (  # noqa: E402
    ACTING_JURISDICTION_FIELDS,
    ACTING_SCOPES,
    AUTOMATION_SCOPES,
    BOOL_FIELDS,
    EPISTEMIC_CLASSIFICATIONS,
    JURISDICTION_LIST_FIELDS,
    LIST_FIELDS,
    OBSERVATION_ONLY_SCOPE,
    REQUIRED_TOP_FIELDS,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_automation_candidate",
    "MalformedYamlError", "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as
# magl/validators/validate_magl.py / kpm/validators/validate_blueprint.py.
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
    rule: str       # which rule ("AC-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    candidate_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    # Preservation invariant: original input is carried through untouched.
    # validate_automation_candidate() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "candidate_id": self.candidate_id,
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


def validate_automation_candidate(text: str) -> ValidationResult:
    """Deterministic structural validation of an automation_candidate
    document. Never returns a bare bool, and never raises on real-world
    input — an uncaught exception here would be a fail-OPEN bug in
    whatever calls this. Any unforeseen failure is reported as INVALID
    with rule AC-R-0, never allowed to propagate (fail-closed, mirroring
    the other validators' outer wrapper and the F-009/F-010 lesson it
    encodes)."""
    try:
        return _validate_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", candidate_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="AC-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def _validate_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", candidate_id=None, original_text=text)

    # --- AC-R-1: parseable + structural ceilings ----------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "AC-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- AC-R-2: top-level 'automation_candidate' wrapper present -----------
    if "automation_candidate" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "AC-R-2", "top-level 'automation_candidate' key is missing",
            "every automation candidate document must be wrapped in a "
            "top-level 'automation_candidate:' key",
            "automation_candidate", "absent",
        ))
        return result
    ac = data["automation_candidate"]
    if not isinstance(ac, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "AC-R-2", "'automation_candidate' value is not a mapping",
            "the 'automation_candidate' key must contain a mapping of fields",
            "automation_candidate", f"got {type(ac).__name__}",
        ))
        return result

    # --- AC-R-3: non-string keys (type-confusion class) ----------------------
    # Content found inside `ac` — including a key literally named
    # "epistemic_status" or "automation_scope" — is read as DATA below.
    # Field lookups are always by literal string name against the fixed
    # schema; a forged/self-declared field never changes control flow.
    non_string_keys = [k for k in ac.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "AC-R-3", "automation_candidate mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot be "
            "a declared field",
            "automation_candidate",
            f"key types present: {sorted({type(k).__name__ for k in ac.keys()})}",
        ))

    ac_keys_as_str = {k if isinstance(k, str) else repr(k) for k in ac.keys()}

    candidate_id = ac.get("id") if isinstance(ac.get("id"), str) else None
    result.candidate_id = candidate_id

    issues: list[Issue] = list(result.issues)

    # --- AC-R-4: required top-level fields ------------------------------------
    missing = REQUIRED_TOP_FIELDS - ac.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "AC-R-4", f"required field 'automation_candidate.{f}' is missing",
            "required by schema", f"automation_candidate.{f}", "absent",
        ))

    # --- AC-R-5: identity/scope string fields non-empty -----------------------
    for f in sorted(STRING_FIELDS):
        if f in ac and (not isinstance(ac[f], str) or not ac[f].strip()):
            issues.append(_issue(
                "AC-R-5", f"field 'automation_candidate.{f}' must be a "
                "non-empty string",
                "identity/scope fields cannot be blank or non-string",
                f"automation_candidate.{f}", ac.get(f),
            ))

    automation_scope = ac.get("automation_scope")
    if "automation_scope" in ac and isinstance(automation_scope, str) and \
            automation_scope.strip() and automation_scope not in AUTOMATION_SCOPES:
        issues.append(_issue(
            "AC-R-5", "field 'automation_candidate.automation_scope' has "
            "invalid enum value",
            f"must be one of {sorted(AUTOMATION_SCOPES)}",
            "automation_candidate.automation_scope", automation_scope,
        ))

    # --- AC-R-6: epistemic_status membership ----------------------------------
    epistemic_status = ac.get("epistemic_status")
    if "epistemic_status" in ac and isinstance(epistemic_status, str) and \
            epistemic_status.strip() and epistemic_status not in EPISTEMIC_CLASSIFICATIONS:
        issues.append(_issue(
            "AC-R-6", "field 'automation_candidate.epistemic_status' has "
            "invalid enum value",
            "must be a member of kpm.schemas.epistemic_types."
            "ALL_CLASSIFICATIONS — the same closed vocabulary every other "
            "claim in this codebase uses; an automation candidate cannot "
            "invent its own epistemic status",
            "automation_candidate.epistemic_status", epistemic_status,
        ))

    # --- AC-R-7: proposed_jurisdiction section (shape) -------------------------
    jurisdiction = ac.get("proposed_jurisdiction")
    if "proposed_jurisdiction" in ac:
        if not isinstance(jurisdiction, dict):
            issues.append(_issue(
                "AC-R-7", "field 'automation_candidate.proposed_jurisdiction' "
                "must be a mapping",
                "proposed_jurisdiction carries may_read/may_write/etc as "
                "sub-fields",
                "automation_candidate.proposed_jurisdiction",
                f"got {type(jurisdiction).__name__}",
            ))
            jurisdiction = {}
        else:
            for f in JURISDICTION_LIST_FIELDS:
                if f in jurisdiction and not isinstance(jurisdiction[f], list):
                    issues.append(_issue(
                        "AC-R-7", f"field 'automation_candidate."
                        f"proposed_jurisdiction.{f}' has wrong type",
                        "expected list",
                        f"automation_candidate.proposed_jurisdiction.{f}",
                        f"got {type(jurisdiction[f]).__name__}",
                    ))
    else:
        jurisdiction = {}

    # --- AC-R-8: automation_scope <-> jurisdiction breadth contradiction -------
    # Only evaluated when automation_scope itself is well-formed (a
    # recognised enum member) and proposed_jurisdiction is a mapping — an
    # already-broken scope/jurisdiction is reported once, under AC-R-5/
    # AC-R-7, not doubled here.
    scope_ok = isinstance(automation_scope, str) and automation_scope in AUTOMATION_SCOPES
    if scope_ok and isinstance(jurisdiction, dict):
        acting_fields_present = any(
            isinstance(jurisdiction.get(f), list) and len(jurisdiction.get(f)) > 0
            for f in ACTING_JURISDICTION_FIELDS
        )
        if automation_scope == OBSERVATION_ONLY_SCOPE and acting_fields_present:
            issues.append(_issue(
                "AC-R-8", "OBSERVATION_ONLY automation_scope declares "
                "acting jurisdiction",
                "a candidate declaring automation_scope: OBSERVATION_ONLY "
                "but also declaring may_write/may_execute/may_call/"
                "may_modify entries is a structural contradiction — it "
                "claims to only observe while also claiming write/execute "
                "scope",
                "automation_candidate.proposed_jurisdiction",
                {"automation_scope": automation_scope, "jurisdiction": jurisdiction},
            ))
        if automation_scope == "FULL_WORKFLOW_AUTOMATION" and not acting_fields_present:
            issues.append(_issue(
                "AC-R-8", "FULL_WORKFLOW_AUTOMATION automation_scope "
                "declares no acting jurisdiction",
                "a candidate that claims to fully automate a workflow but "
                "declares no scope in may_write/may_execute/may_call/"
                "may_modify is a structural contradiction — it claims to "
                "act while claiming no scope to act within",
                "automation_candidate.proposed_jurisdiction",
                {"automation_scope": automation_scope, "jurisdiction": jurisdiction},
            ))

    # --- AC-R-9: boolean fields ------------------------------------------------
    for f in sorted(BOOL_FIELDS):
        if f in ac and not isinstance(ac[f], bool):
            issues.append(_issue(
                "AC-R-9", f"field 'automation_candidate.{f}' must be a boolean",
                "expected boolean", f"automation_candidate.{f}",
                f"got {type(ac[f]).__name__}",
            ))

    # --- AC-R-10: requires_human_approval required true for acting scopes ------
    requires_human_approval = ac.get("requires_human_approval")
    if scope_ok and automation_scope in ACTING_SCOPES and \
            isinstance(requires_human_approval, bool) and not requires_human_approval:
        issues.append(_issue(
            "AC-R-10", "requires_human_approval is false for an acting "
            "automation_scope",
            "a candidate proposing SMALL_BOUNDED_AUTOMATION or "
            "FULL_WORKFLOW_AUTOMATION (real write/execute/modify "
            "jurisdiction) cannot skip human approval — that would let a "
            "proposal assert its own way past the human gate this "
            "component exists to enforce",
            "automation_candidate.requires_human_approval",
            {"automation_scope": automation_scope,
             "requires_human_approval": requires_human_approval},
        ))

    # --- AC-R-11: reversible <-> rollback_plan / irreversibility_acknowledged --
    reversible = ac.get("reversible")
    rollback_plan = ac.get("rollback_plan")
    irreversibility_ack = ac.get("irreversibility_acknowledged")
    if isinstance(reversible, bool):
        if reversible is True:
            if not isinstance(rollback_plan, str) or not rollback_plan.strip():
                issues.append(_issue(
                    "AC-R-11", "field 'automation_candidate.rollback_plan' "
                    "is required when reversible is true",
                    "a candidate claiming reversibility must state how to "
                    "reverse it — an unstated rollback plan makes the "
                    "reversibility claim unverifiable",
                    "automation_candidate.rollback_plan", rollback_plan,
                ))
        else:
            # reversible is False: require the explicit sentinel field
            # (mirrors kpm/validators/validate_blueprint.py's
            # rollback.irreversibility_acknowledged pattern) — an
            # irreversible candidate cannot pass through silently.
            if irreversibility_ack is not True:
                issues.append(_issue(
                    "AC-R-11", "irreversible candidate lacks explicit "
                    "acknowledgment",
                    "reversible: false must be paired with "
                    "irreversibility_acknowledged: true — an irreversible "
                    "candidate cannot pass through silently",
                    "automation_candidate.irreversibility_acknowledged",
                    irreversibility_ack,
                ))

    # --- AC-R-12: known_risks non-empty list ------------------------------------
    known_risks = ac.get("known_risks")
    if "known_risks" in ac:
        if not isinstance(known_risks, list) or len(known_risks) == 0:
            issues.append(_issue(
                "AC-R-12", "field 'automation_candidate.known_risks' must "
                "be a non-empty list",
                "a candidate declaring zero known risks is exactly the "
                "'beautiful proposal, no evidence of self-scrutiny' "
                "pattern this codebase's doctrine warns against elsewhere "
                "— every real automation candidate has at least one known "
                "risk, and omitting all of them is a structural defect, "
                "not a stylistic gap (mirrors magl's non-empty "
                "documentation.limitations rule)",
                "automation_candidate.known_risks", known_risks,
            ))

    for f in sorted(LIST_FIELDS - {"known_risks"}):
        if f in ac and not isinstance(ac[f], list):
            issues.append(_issue(
                "AC-R-12", f"field 'automation_candidate.{f}' has wrong type",
                "expected list", f"automation_candidate.{f}",
                f"got {type(ac[f]).__name__}",
            ))

    # --- unknown fields (never silently trusted) --------------------------------
    known = set(REQUIRED_TOP_FIELDS) | {"irreversibility_acknowledged"}
    unknown = sorted(ac_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
