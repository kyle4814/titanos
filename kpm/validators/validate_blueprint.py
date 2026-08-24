"""
Blueprint Atom Validator (§Phase 3, §Phase 5, §Phase 6 of the Knowledge
Production Machine directive).

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this blueprint atom conform to the declared schema, structurally,
     deterministically, and without executing anything it contains?"

It does NOT answer:
    - "Is this blueprint a good idea?" (human judgment, purpose/problem/
      threat_model/dissent quality is never scored here)
    - "Do the source_artifacts it cites actually exist?" (that's the source
      registry another component owns — this validator checks SHAPE only)
    - "Has this blueprint actually earned its promotion state?" (that's the
      promotion state machine another component owns — this validator only
      catches the STRUCTURAL contradiction of status != promotion.current_gate
      and the STRUCTURAL rule that interpretive classifications can never be
      declared STABLE; it does not implement the full gate logic)

A VALID result means "structurally conformant". It is never upgraded to
"approved", "safe to build", or "promoted" — those are other systems'
vocabulary.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_blueprint() is a pure function over its input text. Content found
inside `text` is read as DATA throughout — never as an instruction to this
function, regardless of field name or content. No field value changes
control flow; every field is looked up by NAME against the fixed schema.

HARDENING

Same parsing hardening as schema/validator.py, replicated deliberately
rather than referenced: duplicate-key detection, document-size/node-count/
depth ceilings enforced BEFORE construction (to defeat alias/anchor
expansion), and RecursionError caught explicitly both at compose time and
construct time, because PyYAML's composer is itself recursive and can blow
the Python call stack before our own ceiling check gets a turn. See
schema/validator.py's comments for the incident this pattern traces back to.

validate_blueprint()'s entire body is wrapped in try/except so an unforeseen
exception becomes a structured INVALID result (rule BP-R-0) rather than
propagating, mirroring schema/validator.py's fail-closed wrapper (see
failures/FAILURE_ARCHIVE.md F-009, F-010 for why this is not optional).

RULE NUMBERING

Rules here are prefixed BP-R-<n> (Blueprint Rule) to stay distinct from
schema/validator.py's R-<n> numbering, since both modules may be referenced
in the same later documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from kpm.schemas.blueprint_atom import (
    CONFIDENCE_VALUES,
    EPISTEMIC_CLASSIFICATIONS,
    LIST_FIELDS,
    NON_STABLE_PROMOTABLE_CLASSIFICATIONS,
    REQUIRED_NESTED_PATHS,
    REQUIRED_TOP_FIELDS,
    STATUS_VALUES,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_blueprint", "MalformedYamlError",
    "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as schema/validator.py:
# defeat expansion/DoS tricks before any field-level check runs.
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
    rule: str       # which rule ("BP-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    blueprint_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    machine_verifiable_checked: list[str] = field(default_factory=list)
    human_judgment_fields_present: list[str] = field(default_factory=list)
    # Preservation invariant: original input is carried through untouched.
    # validate_blueprint() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blueprint_id": self.blueprint_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
            "machine_verifiable_checked": self.machine_verifiable_checked,
            "human_judgment_fields_present": self.human_judgment_fields_present,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated from schema/validator.py rather than imported —
#  each validator owns its own parsing hardening independently, matching the
#  house pattern of the reference module)
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


def validate_blueprint(text: str) -> ValidationResult:
    """Deterministic structural validation of a blueprint atom document.
    Never returns a bare bool, and never raises on real-world input — an
    uncaught exception here would be a fail-OPEN bug in whatever calls this.
    Any unforeseen failure is reported as INVALID with rule BP-R-0, never
    allowed to propagate (fail-closed, mirroring schema/validator.py's
    outer wrapper and the F-009/F-010 lesson it encodes)."""
    try:
        return _validate_blueprint_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", blueprint_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="BP-R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _issue(rule: str, what: str, why: str, where: str, evidence: Any) -> Issue:
    return Issue(what=what, why=why, where=where, rule=rule, evidence=repr(evidence)[:200])


def _validate_blueprint_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", blueprint_id=None, original_text=text)

    # --- BP-R-1: parseable ------------------------------------------------
    try:
        doc = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(Issue(
            what="YAML could not be parsed or violated structural ceilings",
            why="unparseable or oversized input cannot be safely validated",
            where="<document>", rule="BP-R-1", evidence=str(e),
        ))
        return result

    issues: list[Issue] = []

    # --- BP-R-2: top-level `blueprint:` wrapper present and a mapping -----
    if "blueprint" not in doc:
        issues.append(_issue(
            "BP-R-2", "top-level 'blueprint' key is missing",
            "the entire document must be nested under a top-level "
            "'blueprint:' key by schema", "blueprint", "absent",
        ))
        result.issues = issues
        result.status = "INVALID"
        return result

    bp = doc["blueprint"]
    if not isinstance(bp, dict):
        issues.append(_issue(
            "BP-R-2", "'blueprint' value is not a mapping",
            "the blueprint body must be a mapping of fields",
            "blueprint", f"got {type(bp).__name__}",
        ))
        result.issues = issues
        result.status = "INVALID"
        return result

    result.blueprint_id = bp.get("id") if isinstance(bp.get("id"), str) else None

    # Non-string keys inside blueprint mapping — treat like schema/validator's
    # R-12 type-confusion class: coerce to str form for comparison, never
    # crash a sorted()/set comparison on mixed key types.
    bp_keys_as_str = {k if isinstance(k, str) else repr(k) for k in bp.keys()}
    non_string_keys = [k for k in bp.keys() if not isinstance(k, str)]
    if non_string_keys:
        issues.append(_issue(
            "BP-R-12", "blueprint mapping contains non-string keys",
            "blueprint fields must be string-named; a boolean, int, or null "
            "key cannot be a declared field",
            "blueprint", f"key types present: {sorted({type(k).__name__ for k in bp.keys()})}",
        ))

    # NOTE: `bp` may contain a field literally named e.g. "promotion" with a
    # forged current_gate, or any other content. None of that is ever read
    # as control flow — every field is looked up by NAME against the fixed
    # schema and checked; its VALUE is data.

    # --- BP-R-3: required top-level fields ---------------------------------
    missing_top = REQUIRED_TOP_FIELDS - bp.keys()
    for f in sorted(missing_top):
        issues.append(_issue(
            "BP-R-3", f"required field 'blueprint.{f}' is missing",
            "required by schema", f"blueprint.{f}", "absent",
        ))

    # --- BP-R-4: string fields must be non-empty strings when present -----
    for f in STRING_FIELDS:
        if f in bp:
            v = bp[f]
            if not isinstance(v, str) or v.strip() == "":
                issues.append(_issue(
                    "BP-R-4", f"field 'blueprint.{f}' must be a non-empty string",
                    "empty or wrongly-typed required text fields are a "
                    "structural defect, not a stylistic gap",
                    f"blueprint.{f}", v,
                ))

    # --- BP-R-5: list fields must be lists when present --------------------
    for f in LIST_FIELDS:
        if f in bp and bp[f] is not None and not isinstance(bp[f], list):
            issues.append(_issue(
                "BP-R-5", f"field 'blueprint.{f}' has wrong type",
                "expected list", f"blueprint.{f}", f"got {type(bp[f]).__name__}",
            ))

    # --- BP-R-6: status enum -------------------------------------------
    status = bp.get("status")
    if "status" in bp and status not in STATUS_VALUES:
        issues.append(_issue(
            "BP-R-6", "field 'blueprint.status' has invalid enum value",
            f"must be one of {sorted(STATUS_VALUES)}",
            "blueprint.status", status,
        ))

    # --- BP-R-7: classification section ------------------------------------
    classification = bp.get("classification")
    primary = None
    if "classification" in bp:
        if not isinstance(classification, dict):
            issues.append(_issue(
                "BP-R-7", "field 'blueprint.classification' must be a mapping",
                "classification.primary/confidence are required sub-fields",
                "blueprint.classification", f"got {type(classification).__name__}",
            ))
            classification = {}
        missing_nested = REQUIRED_NESTED_PATHS["classification"] - classification.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "BP-R-7", f"required field 'blueprint.classification.{f}' is missing",
                "required by schema", f"blueprint.classification.{f}", "absent",
            ))
        primary = classification.get("primary")
        if "primary" in classification and primary not in EPISTEMIC_CLASSIFICATIONS:
            issues.append(_issue(
                "BP-R-7", "field 'blueprint.classification.primary' has invalid enum value",
                f"must be one of the 15 declared epistemic classifications",
                "blueprint.classification.primary", primary,
            ))
        confidence = classification.get("confidence")
        if "confidence" in classification and confidence not in CONFIDENCE_VALUES:
            issues.append(_issue(
                "BP-R-7", "field 'blueprint.classification.confidence' has invalid enum value",
                f"must be one of {sorted(CONFIDENCE_VALUES)}",
                "blueprint.classification.confidence", confidence,
            ))
    else:
        classification = {}

    # --- BP-R-8: implementation section -------------------------------
    implementation = bp.get("implementation")
    if "implementation" in bp:
        if not isinstance(implementation, dict):
            issues.append(_issue(
                "BP-R-8", "field 'blueprint.implementation' must be a mapping",
                "smallest_next_step/acceptance_criteria are required sub-fields",
                "blueprint.implementation", f"got {type(implementation).__name__}",
            ))
            implementation = {}
        missing_nested = REQUIRED_NESTED_PATHS["implementation"] - implementation.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "BP-R-8", f"required field 'blueprint.implementation.{f}' is missing",
                "required by schema", f"blueprint.implementation.{f}", "absent",
            ))
        step = implementation.get("smallest_next_step")
        if "smallest_next_step" in implementation and (
            not isinstance(step, str) or step.strip() == ""
        ):
            issues.append(_issue(
                "BP-R-8", "field 'blueprint.implementation.smallest_next_step' must be a non-empty string",
                "a blueprint with no defined next step cannot move forward",
                "blueprint.implementation.smallest_next_step", step,
            ))
        criteria = implementation.get("acceptance_criteria")
        if "acceptance_criteria" in implementation:
            if not isinstance(criteria, list) or len(criteria) == 0:
                issues.append(_issue(
                    "BP-R-8", "field 'blueprint.implementation.acceptance_criteria' must be a non-empty list",
                    "a blueprint with no way to check it's done is an "
                    "unfalsifiable 'done' state — a structural defect this "
                    "validator must catch, not a nicety",
                    "blueprint.implementation.acceptance_criteria", criteria,
                ))
    else:
        implementation = {}

    # --- BP-R-9: promotion section + status agreement ----------------------
    promotion = bp.get("promotion")
    current_gate = None
    if "promotion" in bp:
        if not isinstance(promotion, dict):
            issues.append(_issue(
                "BP-R-9", "field 'blueprint.promotion' must be a mapping",
                "current_gate is a required sub-field",
                "blueprint.promotion", f"got {type(promotion).__name__}",
            ))
            promotion = {}
        missing_nested = REQUIRED_NESTED_PATHS["promotion"] - promotion.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "BP-R-9", f"required field 'blueprint.promotion.{f}' is missing",
                "required by schema", f"blueprint.promotion.{f}", "absent",
            ))
        current_gate = promotion.get("current_gate")
        if "current_gate" in promotion and current_gate not in STATUS_VALUES:
            issues.append(_issue(
                "BP-R-9", "field 'blueprint.promotion.current_gate' has invalid enum value",
                f"must be one of {sorted(STATUS_VALUES)}",
                "blueprint.promotion.current_gate", current_gate,
            ))
        preq = promotion.get("promotion_requirements")
        if preq is not None and not isinstance(preq, list):
            issues.append(_issue(
                "BP-R-9", "field 'blueprint.promotion.promotion_requirements' has wrong type",
                "expected list", "blueprint.promotion.promotion_requirements",
                f"got {type(preq).__name__}",
            ))
    else:
        promotion = {}

    # --- BP-R-10: status vs promotion.current_gate agreement ---------------
    # A blueprint claiming two different promotion states is a contradiction,
    # not a typo to shrug off. Checked whenever BOTH fields are present and
    # well-formed enough to compare; missing-field cases are already caught
    # by BP-R-3/BP-R-9 above.
    if "status" in bp and "current_gate" in promotion and status != current_gate:
        issues.append(_issue(
            "BP-R-10", "'blueprint.status' and 'blueprint.promotion.current_gate' disagree",
            "a blueprint cannot simultaneously claim two different "
            "promotion states — this is a structural contradiction, "
            "not a cosmetic mismatch",
            "blueprint.status / blueprint.promotion.current_gate",
            f"status={status!r} current_gate={current_gate!r}",
        ))

    # --- BP-R-11: interpretive classification cannot be STABLE-promoted ---
    # Belt-and-suspenders enforcement of the forbidden-classification-
    # transition rule at the schema layer: CREATIVE_CONCEPT,
    # SPECULATIVE_HYPOTHESIS, and SYMBOLIC_DOCTRINE classifications are
    # inherently interpretive/unfalsifiable and can never be declared
    # STABLE, regardless of what the (separately-built) promotion state
    # machine would otherwise permit.
    if primary in NON_STABLE_PROMOTABLE_CLASSIFICATIONS:
        if status == "STABLE":
            issues.append(_issue(
                "BP-R-11", "interpretive classification declared STABLE via 'status'",
                f"{primary} is an interpretive/unfalsifiable classification "
                f"and can never be STABLE-promoted",
                "blueprint.status", f"classification.primary={primary!r} status=STABLE",
            ))
        if current_gate == "STABLE":
            issues.append(_issue(
                "BP-R-11", "interpretive classification declared STABLE via 'promotion.current_gate'",
                f"{primary} is an interpretive/unfalsifiable classification "
                f"and can never be STABLE-promoted",
                "blueprint.promotion.current_gate",
                f"classification.primary={primary!r} current_gate=STABLE",
            ))

    # --- BP-R-13: rollback section ------------------------------------------
    rollback = bp.get("rollback")
    if "rollback" in bp:
        if not isinstance(rollback, dict):
            issues.append(_issue(
                "BP-R-13", "field 'blueprint.rollback' must be a mapping",
                "reversible is a required sub-field",
                "blueprint.rollback", f"got {type(rollback).__name__}",
            ))
            rollback = {}
        missing_nested = REQUIRED_NESTED_PATHS["rollback"] - rollback.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "BP-R-13", f"required field 'blueprint.rollback.{f}' is missing",
                "required by schema", f"blueprint.rollback.{f}", "absent",
            ))
        reversible = rollback.get("reversible")
        if "reversible" in rollback and not isinstance(reversible, bool):
            issues.append(_issue(
                "BP-R-13", "field 'blueprint.rollback.reversible' has wrong type",
                "expected boolean", "blueprint.rollback.reversible",
                f"got {type(reversible).__name__}",
            ))
        recovery = rollback.get("recovery_procedure")
        if reversible is True:
            if not isinstance(recovery, str) or recovery.strip() == "":
                issues.append(_issue(
                    "BP-R-13", "field 'blueprint.rollback.recovery_procedure' is required when reversible is true",
                    "a blueprint claiming reversibility without stating how "
                    "to reverse it is an unfulfillable promise",
                    "blueprint.rollback.recovery_procedure", recovery,
                ))
        elif reversible is False:
            # Judgment call: irreversibility must be explicitly acknowledged
            # rather than merely implied by an absent recovery_procedure —
            # a caller could otherwise leave the field out by oversight and
            # have it silently pass as "irreversible, no big deal". We
            # require SOME explicit acknowledgment token; we accept either a
            # non-empty recovery_procedure describing why none exists, or a
            # literal acknowledgment sentinel. This is documented, not
            # silently inferred from absence.
            irreversibility_ack = rollback.get("irreversibility_acknowledged")
            has_explanatory_text = isinstance(recovery, str) and recovery.strip() != ""
            if irreversibility_ack is not True and not has_explanatory_text:
                issues.append(_issue(
                    "BP-R-13", "irreversible blueprint lacks explicit acknowledgment",
                    "reversible: false must be paired with either a "
                    "recovery_procedure explaining why none exists, or "
                    "rollback.irreversibility_acknowledged: true — an "
                    "irreversible blueprint cannot pass through silently",
                    "blueprint.rollback", f"reversible=False recovery_procedure={recovery!r} "
                    f"irreversibility_acknowledged={irreversibility_ack!r}",
                ))
    else:
        rollback = {}

    # --- BP-R-14: audit section ----------------------------------------------
    audit = bp.get("audit")
    if "audit" in bp:
        if not isinstance(audit, dict):
            issues.append(_issue(
                "BP-R-14", "field 'blueprint.audit' must be a mapping",
                "created_by is a required sub-field",
                "blueprint.audit", f"got {type(audit).__name__}",
            ))
            audit = {}
        missing_nested = REQUIRED_NESTED_PATHS["audit"] - audit.keys()
        for f in sorted(missing_nested):
            issues.append(_issue(
                "BP-R-14", f"required field 'blueprint.audit.{f}' is missing",
                "required by schema", f"blueprint.audit.{f}", "absent",
            ))
        created_by = audit.get("created_by")
        if "created_by" in audit and (not isinstance(created_by, str) or created_by.strip() == ""):
            issues.append(_issue(
                "BP-R-14", "field 'blueprint.audit.created_by' must be a non-empty string",
                "provenance of who authored the blueprint must be recorded",
                "blueprint.audit.created_by", created_by,
            ))
        for f, expect in (("reviewed_by", list), ("timestamps", dict), ("hashes", dict)):
            if f in audit and audit[f] is not None and not isinstance(audit[f], expect):
                issues.append(_issue(
                    "BP-R-14", f"field 'blueprint.audit.{f}' has wrong type",
                    f"expected {expect.__name__}", f"blueprint.audit.{f}",
                    f"got {type(audit[f]).__name__}",
                ))
    else:
        audit = {}

    # --- BP-R-15: provenance section (shape only) ---------------------------
    provenance = bp.get("provenance")
    if provenance is not None:
        if not isinstance(provenance, dict):
            issues.append(_issue(
                "BP-R-15", "field 'blueprint.provenance' must be a mapping",
                "immutable_source_refs/interpretations are expected sub-fields",
                "blueprint.provenance", f"got {type(provenance).__name__}",
            ))
        else:
            for f in ("immutable_source_refs", "interpretations"):
                if f in provenance and provenance[f] is not None and not isinstance(provenance[f], list):
                    issues.append(_issue(
                        "BP-R-15", f"field 'blueprint.provenance.{f}' has wrong type",
                        "expected list", f"blueprint.provenance.{f}",
                        f"got {type(provenance[f]).__name__}",
                    ))

    # --- BP-R-16: verification section (shape only) -------------------------
    verification = bp.get("verification")
    if verification is not None:
        if not isinstance(verification, dict):
            issues.append(_issue(
                "BP-R-16", "field 'blueprint.verification' must be a mapping",
                "tests/evidence_required are expected sub-fields",
                "blueprint.verification", f"got {type(verification).__name__}",
            ))
        else:
            for f in ("tests", "evidence_required"):
                if f in verification and verification[f] is not None and not isinstance(verification[f], list):
                    issues.append(_issue(
                        "BP-R-16", f"field 'blueprint.verification.{f}' has wrong type",
                        "expected list", f"blueprint.verification.{f}",
                        f"got {type(verification[f]).__name__}",
                    ))

    # --- BP-R-17: dissent section (shape only) -------------------------------
    dissent = bp.get("dissent")
    if dissent is not None:
        if not isinstance(dissent, dict):
            issues.append(_issue(
                "BP-R-17", "field 'blueprint.dissent' must be a mapping",
                "alternative_models/unresolved_objections are expected sub-fields",
                "blueprint.dissent", f"got {type(dissent).__name__}",
            ))
        else:
            for f in ("alternative_models", "unresolved_objections"):
                if f in dissent and dissent[f] is not None and not isinstance(dissent[f], list):
                    issues.append(_issue(
                        "BP-R-17", f"field 'blueprint.dissent.{f}' has wrong type",
                        "expected list", f"blueprint.dissent.{f}",
                        f"got {type(dissent[f]).__name__}",
                    ))

    # --- unknown fields (never silently trusted) ---------------------------
    known = {
        "id", "title", "version", "status", "domain", "source_artifacts",
        "provenance", "classification", "purpose", "problem", "constraints",
        "assumptions", "unknowns", "non_goals", "inputs", "outputs",
        "invariants", "threat_model", "failure_modes", "controls",
        "interfaces", "dependencies", "implementation", "verification",
        "dissent", "promotion", "rollback", "audit",
    }
    unknown = sorted(bp_keys_as_str - known)
    result.unknown_fields = unknown

    from kpm.schemas.blueprint_atom import HUMAN_JUDGMENT_FIELDS, MACHINE_VERIFIABLE_FIELDS
    result.human_judgment_fields_present = sorted(HUMAN_JUDGMENT_FIELDS & bp_keys_as_str)
    result.machine_verifiable_checked = sorted(MACHINE_VERIFIABLE_FIELDS & bp_keys_as_str)

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
