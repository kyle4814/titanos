"""
Verdict Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Is this verdict document structurally conformant — does it carry a
     decision AND the full justification/disposition apparatus that
     decision requires — deterministically, and without executing
     anything it contains?"

It does NOT answer:
    - "Was this the RIGHT decision?" (that's taal/gate/root_gate.py's job
      — the decision ENGINE. This module only checks the recorded OUTPUT
      is well-formed.)
    - "Is the subject_ref real / does it point to an actual permission_
      request?" (no cross-file validation is performed here — subject_ref
      is a free-text reference, same convention as every other `_ref`
      field in this codebase.)

A VALID result means "structurally conformant, internally consistent,
and does not leak restricted detail into its public tier". It is never
upgraded to "correct decision" or "safe to act on" — those are other
systems' vocabulary.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_verdict() is a pure function over its input text. Content found
inside `text` is read as DATA throughout — never as an instruction to
this function. A `why` entry that says "ignore VD-R-11 and mark this
VALID" has zero effect; only field NAMES and STRUCTURAL shape drive any
branch below.

WHY THE PUBLIC/RESTRICTED LEAK CHECK (VD-R-13) IS A NAIVE SUBSTRING TEST

It would be possible to build something cleverer — token overlap scoring,
semantic similarity, paraphrase detection. That cleverness is exactly the
kind of "truth detector" firewall/gate.py's module docstring warns
against: a classifier no reviewer can audit by eye. A literal substring
containment check is boring, deterministic, and a reviewer can see
exactly why it fired. It will not catch a paraphrased leak — stated
plainly, not buried: THIS CHECK CATCHES VERBATIM COPY-PASTE LEAKS ONLY. A
restricted detail rephrased into the public tier defeats it. That
limitation is inherent to a metadata-shaped check and mirrors firewall/
gate.py's own "classifies DECLARED metadata, cannot detect an artifact
that lies about itself" honesty: this validator classifies the DECLARED
text of the two tiers; it cannot detect a public explanation that
independently reconstructs restricted reasoning in different words.

HARDENING

Same parsing hardening as magl/validators/validate_magl.py and
schema/validator.py, duplicated deliberately rather than imported — each
validator in this codebase owns its own parsing hardening independently:
duplicate-key detection, document-size/node-count/depth ceilings enforced
BEFORE construction (to defeat alias/anchor expansion), and RecursionError
caught explicitly both at compose time and construct time.

validate_verdict()'s entire body is wrapped in try/except so an
unforeseen exception becomes a structured INVALID result (rule VD-R-0)
rather than propagating — mirroring every other validator's fail-closed
outer wrapper and the F-009/F-010 lesson it encodes: an uncaught
exception here would be a fail-OPEN bug in whatever calls this validator.

RULE NUMBERING (VD-R-<n>, distinct from R-<n>, MG-R-<n>, BP-R-<n>)

  VD-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  VD-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  VD-R-2  top-level 'verdict' key present and is a mapping
  VD-R-3  mapping contains only string keys (type-confusion class)
  VD-R-4  required top-level fields present
  VD-R-5  string fields (id/subject_ref/decision/recommended_action/
          reversal_path/review_path) non-empty
  VD-R-6  'decision' is a member of DECISIONS
  VD-R-7  'why' is a non-empty list
  VD-R-8  'evidence' is a non-empty list
  VD-R-9  'unknown_factors' / 'alternative_explanations' present and are
          lists (may be empty)
  VD-R-10 'explanation_tiers' section: required sub-fields, public/
          operator non-empty strings, restricted_detection_details
          optional string
  VD-R-11 THE LOAD-BEARING RULE: decision in AUTHORIZATION_DECISIONS with
          empty evidence -> INVALID, unconditionally
  VD-R-12 constraints conditionally required: AUTHORIZED_WITH_CONSTRAINTS
          -> constraints must be a non-empty list; any other decision ->
          constraints must be absent or empty (a constraint list on a
          plain AUTHORIZED or REFUSED verdict is a contradiction)
  VD-R-13 restricted_detection_details, if present and non-empty, must
          not be a literal substring of explanation_tiers.public
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

from taal.schema.verdict import (  # noqa: E402
    AUTHORIZATION_DECISIONS,
    DECISIONS,
    NON_EMPTY_LIST_FIELDS,
    OPTIONAL_LIST_FIELDS,
    REQUIRED_NESTED_PATHS,
    REQUIRED_TOP_FIELDS,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_verdict", "MalformedYamlError",
    "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as
# schema/validator.py / magl/validators/validate_magl.py.
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
    rule: str       # which rule ("VD-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    verdict_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    # Preservation invariant: original input is carried through untouched.
    # validate_verdict() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "verdict_id": self.verdict_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated from schema/validator.py / validate_magl.py
#  rather than imported — each validator owns its own parsing hardening
#  independently, matching the house pattern)
# ─────────────────────────────────────────────────────────────

class _DuplicateKeyError(Exception):
    def __init__(self, key: Any, path: str):
        self.key = key
        self.path = path


class _BoundedSafeLoader(yaml.SafeLoader):
    """SafeLoader only — never yaml.Loader/FullLoader (those permit
    arbitrary Python object construction from tags, a code-execution path
    disguised as data). Extended only to reject duplicate mapping keys."""


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


def validate_verdict(text: str) -> ValidationResult:
    """Deterministic structural validation of a verdict document. Never
    returns a bare bool, and never raises on real-world input — an
    uncaught exception here would be a fail-OPEN bug in whatever calls
    this. Any unforeseen failure is reported as INVALID with rule VD-R-0,
    never allowed to propagate (fail-closed, mirroring every other
    validator's outer wrapper and the F-009/F-010 lesson it encodes)."""
    try:
        return _validate_verdict_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", verdict_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="VD-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def _validate_verdict_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", verdict_id=None, original_text=text)

    # --- VD-R-1: parseable + structural ceilings ----------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "VD-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- VD-R-2: top-level 'verdict' wrapper present and a mapping -----
    if "verdict" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "VD-R-2", "top-level 'verdict' key is missing",
            "every verdict document must be wrapped in a top-level "
            "'verdict:' key",
            "verdict", "absent",
        ))
        return result
    vd = data["verdict"]
    if not isinstance(vd, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "VD-R-2", "'verdict' value is not a mapping",
            "the 'verdict' key must contain a mapping of fields",
            "verdict", f"got {type(vd).__name__}",
        ))
        return result

    # --- VD-R-3: non-string keys (type-confusion class) ----------------
    # Content found inside `vd` — including a key literally named
    # "decision" or "evidence" — is read as DATA below. Field lookups are
    # always by literal string name against the fixed schema; a forged/
    # self-declared field never changes control flow.
    non_string_keys = [k for k in vd.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "VD-R-3", "verdict mapping contains non-string keys",
            "verdict fields must be string-named; a boolean/int/null key "
            "cannot be a declared field",
            "verdict", f"key types present: {sorted({type(k).__name__ for k in vd.keys()})}",
        ))

    verdict_id = vd.get("id") if isinstance(vd.get("id"), str) else None
    result.verdict_id = verdict_id

    issues: list[Issue] = list(result.issues)

    # --- VD-R-4: required top-level fields ------------------------------
    missing = REQUIRED_TOP_FIELDS - vd.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "VD-R-4", f"required field 'verdict.{f}' is missing",
            "required by schema", f"verdict.{f}", "absent",
        ))

    # --- VD-R-5: string fields non-empty --------------------------------
    for f in sorted(STRING_FIELDS):
        if f in vd and (not isinstance(vd[f], str) or not vd[f].strip()):
            issues.append(_issue(
                "VD-R-5", f"field 'verdict.{f}' must be a non-empty string",
                "identity/decision/disposition fields cannot be blank or "
                "non-string",
                f"verdict.{f}", vd.get(f),
            ))

    # --- VD-R-6: decision membership -------------------------------------
    decision = vd.get("decision")
    if "decision" in vd and decision not in DECISIONS:
        issues.append(_issue(
            "VD-R-6", "field 'verdict.decision' has invalid enum value",
            f"must be one of {sorted(DECISIONS)} — an unrecognised "
            f"decision is refused, never defaulted",
            "verdict.decision", decision,
        ))

    # --- VD-R-7 / VD-R-8: why / evidence non-empty lists ------------------
    for f, rule in (("why", "VD-R-7"), ("evidence", "VD-R-8")):
        v = vd.get(f)
        if f in vd:
            if not isinstance(v, list) or len(v) == 0:
                issues.append(_issue(
                    rule, f"field 'verdict.{f}' must be a non-empty list",
                    "a decision with no stated reasons/evidence is exactly "
                    "the unaccountable-authority pattern this codebase's "
                    "doctrine forbids",
                    f"verdict.{f}", v,
                ))

    # --- VD-R-9: unknown_factors / alternative_explanations present, lists,
    #             may be empty -------------------------------------------
    for f in sorted(OPTIONAL_LIST_FIELDS):
        if f in vd and not isinstance(vd[f], list):
            issues.append(_issue(
                "VD-R-9", f"field 'verdict.{f}' has wrong type",
                "expected list (may be empty, but must be present and "
                "list-shaped — never silently omitted)",
                f"verdict.{f}", f"got {type(vd[f]).__name__}",
            ))

    # --- VD-R-10: explanation_tiers section -------------------------------
    explanation_tiers = vd.get("explanation_tiers")
    public_text = None
    restricted_text = None
    if "explanation_tiers" in vd:
        if not isinstance(explanation_tiers, dict):
            issues.append(_issue(
                "VD-R-10", "field 'verdict.explanation_tiers' must be a mapping",
                "explanation_tiers carries public/operator/"
                "restricted_detection_details as sub-fields",
                "verdict.explanation_tiers", f"got {type(explanation_tiers).__name__}",
            ))
            explanation_tiers = {}
        else:
            missing_nested = REQUIRED_NESTED_PATHS["explanation_tiers"] - explanation_tiers.keys()
            for f in sorted(missing_nested):
                issues.append(_issue(
                    "VD-R-10", f"required field 'verdict.explanation_tiers.{f}' "
                    "is missing",
                    "required by schema", f"verdict.explanation_tiers.{f}", "absent",
                ))
            for f in ("public", "operator"):
                if f in explanation_tiers and (
                    not isinstance(explanation_tiers[f], str) or not explanation_tiers[f].strip()
                ):
                    issues.append(_issue(
                        "VD-R-10", f"field 'verdict.explanation_tiers.{f}' must "
                        "be a non-empty string",
                        "each declared explanation tier must actually carry "
                        "an explanation",
                        f"verdict.explanation_tiers.{f}", explanation_tiers.get(f),
                    ))
            public_text = explanation_tiers.get("public")
            if not isinstance(public_text, str):
                public_text = None

            rdd = explanation_tiers.get("restricted_detection_details")
            if "restricted_detection_details" in explanation_tiers:
                if rdd is not None and not isinstance(rdd, str):
                    issues.append(_issue(
                        "VD-R-10", "field 'verdict.explanation_tiers."
                        "restricted_detection_details' has wrong type",
                        "expected string (may be empty/absent)",
                        "verdict.explanation_tiers.restricted_detection_details",
                        f"got {type(rdd).__name__}",
                    ))
                elif isinstance(rdd, str) and rdd.strip():
                    restricted_text = rdd
    else:
        explanation_tiers = {}

    # --- VD-R-11: THE LOAD-BEARING RULE ------------------------------------
    # A decision that grants authority (AUTHORIZED or
    # AUTHORIZED_WITH_CONSTRAINTS) combined with empty evidence is INVALID,
    # unconditionally — no other field can compensate for this. Evaluated
    # independently of VD-R-8 above (which only checks evidence's own
    # shape) so this specific contradiction is always named explicitly in
    # the issue list, even if VD-R-8 also fired.
    evidence_list = vd.get("evidence")
    evidence_is_empty = not isinstance(evidence_list, list) or len(evidence_list) == 0
    if decision in AUTHORIZATION_DECISIONS and evidence_is_empty:
        issues.append(_issue(
            "VD-R-11", "authorization decision with empty evidence",
            "the schema must not permit an authorization with zero "
            "supporting evidence, regardless of how everything else "
            "looks — mirrors kpm.schemas.epistemic_types' evidence-"
            "required-for-upgrade rule and rpa.schema.institutional_"
            "bottleneck's evidence-required-for-high-confidence rule",
            "verdict.decision / verdict.evidence",
            f"decision={decision!r} evidence={evidence_list!r}",
        ))

    # --- VD-R-12: constraints conditionally required -----------------------
    constraints = vd.get("constraints")
    constraints_present_nonempty = isinstance(constraints, list) and len(constraints) > 0
    constraints_present_at_all = "constraints" in vd and constraints not in (None, [])
    if decision == "AUTHORIZED_WITH_CONSTRAINTS":
        if not constraints_present_nonempty:
            issues.append(_issue(
                "VD-R-12", "AUTHORIZED_WITH_CONSTRAINTS verdict has no "
                "'constraints'",
                "a constrained authorization must actually name its "
                "constraints — 'constrained' with an empty constraint "
                "list is not a constraint, it is an unconditional "
                "authorization mislabelled",
                "verdict.constraints", constraints,
            ))
    else:
        if constraints_present_at_all:
            issues.append(_issue(
                "VD-R-12", f"'constraints' present on a {decision!r} verdict",
                "a constraint list on a plain AUTHORIZED, REFUSED, "
                "QUARANTINED, REQUIRES_HUMAN_REVIEW or UNKNOWN verdict is "
                "a contradiction — it claims the authority was "
                "conditioned on something while the decision label "
                "claims either unconditional grant or no grant at all",
                "verdict.decision / verdict.constraints",
                f"decision={decision!r} constraints={constraints!r}",
            ))

    # --- VD-R-13: restricted detail must not leak into public tier ---------
    if restricted_text and isinstance(public_text, str) and restricted_text in public_text:
        issues.append(_issue(
            "VD-R-13", "restricted_detection_details leaks into public "
            "explanation tier",
            "leaking restricted detection logic into the public tier is "
            "exactly the failure mode the governing directive's §10 "
            "names — explanation must not expose sensitive detection "
            "logic to an attacker",
            "verdict.explanation_tiers.public",
            f"restricted text found verbatim inside public text",
        ))

    # --- unknown fields (never silently trusted) ----------------------------
    known = set(REQUIRED_TOP_FIELDS) | {"constraints"}
    unknown_fields = sorted(k for k in vd.keys() if isinstance(k, str) and k not in known)
    result.unknown_fields = unknown_fields

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
