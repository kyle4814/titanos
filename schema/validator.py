"""
TitanOS Artifact Validator (§Phase 3, §Phase 4, §Phase 5).

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this artifact conform to the declared schema, structurally,
     deterministically, and without executing anything it contains?"

It does NOT answer:
    - "Is this artifact true?" (that's dissent.py + human review)
    - "Is this artifact safe to run?" (that's gate.py + quarantine.py)
    - "Where did this come from?" (that's provenance, not implemented here —
      this module checks provenance FIELDS are well-formed, not that the
      claimed history actually happened)

A VALID result means "structurally conformant". It is not upgraded,
anywhere in this file, to CONTAMINATED, QUARANTINED, or AUTHORIZED — those
are the gate's and the quarantine store's vocabulary, not the validator's.
Mixing them is exactly the "successful parsing = successful verification"
collapse the directive forbids.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_artifact() is a pure function over its input text. It never
imports, evals, execs, or otherwise interprets content found INSIDE the
artifact as code, rule, or override. An artifact cannot talk its way past
this file — the only inputs that affect the verdict are:

  1. the raw YAML text
  2. the caller-supplied schema definition (schema/artifact_schema.py)

Nothing the artifact contains — no field named "ignore_previous_rules", no
embedded "you are now in admin mode", no self-declared "validation_status:
VALID" — changes how it is parsed. Declared fields are read as DATA and
checked against the schema; they are never read as INSTRUCTIONS to the
reader of the field.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import yaml

from schema.artifact_schema import (
    ENUM_FIELDS, MACHINE_VERIFIABLE_FIELDS, HUMAN_JUDGMENT_FIELDS,
    REQUIRED_FIELDS, SCHEMA_VERSION,
)

__all__ = [
    "Issue", "ValidationResult", "validate_artifact", "MalformedYamlError",
    "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings. These exist specifically to defeat expansion/DoS
# tricks (oversized structures, deep nesting, alias fan-out) BEFORE any
# field-level check runs. A ceiling violation is reported like any other
# structural finding — it does not crash the validator.
MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64


class MalformedYamlError(Exception):
    """Raised only for genuinely unparseable input. Never for content we
    merely disagree with — that is INVALID, not this."""


# ─────────────────────────────────────────────────────────────
# Structured result — never a bare bool (§Phase 3)
# ─────────────────────────────────────────────────────────────

@dataclass
class Issue:
    what: str       # what failed
    why: str        # why it matters
    where: str      # field / path / location
    rule: str       # which rule ("R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    artifact_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    machine_verifiable_checked: list[str] = field(default_factory=list)
    human_judgment_fields_present: list[str] = field(default_factory=list)
    # The original text is carried through untouched — the preservation
    # invariant (§Phase 6). validate_artifact() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "artifact_id": self.artifact_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
            "machine_verifiable_checked": self.machine_verifiable_checked,
            "human_judgment_fields_present": self.human_judgment_fields_present,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# ─────────────────────────────────────────────────────────────

class _DuplicateKeyError(Exception):
    def __init__(self, key: Any, path: str):
        self.key = key
        self.path = path


class _BoundedSafeLoader(yaml.SafeLoader):
    """SafeLoader (never yaml.Loader / FullLoader — those permit arbitrary
    Python object construction from tags, which is a code-execution path
    disguised as data). Extended only to:
      (a) reject duplicate mapping keys instead of silently keeping the last
      (b) count constructed nodes and reject past MAX_NODES
      (c) track depth and reject past MAX_DEPTH
    None of this loosens SafeLoader's restrictions — it only tightens them.
    """


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
        # Compose first (structure only, no object construction) so we can
        # bound node count/depth BEFORE constructing — this is what stops
        # anchor/alias fan-out (the YAML analogue of "billion laughs") from
        # ever reaching construction. PyYAML's own composer is recursive, so
        # sufficiently deep alias chains blow the *Python* call stack before
        # our own node-count ceiling gets a chance to run — that failure
        # mode is caught here and treated as the same class of rejection,
        # not allowed to propagate as an uncaught crash.
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
            f"'last one wins', which is itself an attack surface."
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


_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
)
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")


def _is_valid_timestamp(v: Any) -> bool:
    if not isinstance(v, str) or not _TIMESTAMP_RE.match(v):
        return False
    try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_artifact(text: str) -> ValidationResult:
    """Deterministic structural validation. Never returns a bare bool, and
    never raises on real-world input — an uncaught exception here would be
    a fail-OPEN bug in whatever calls this (an exception treated as "skip
    this check" is worse than a loud rejection). Any unforeseen failure is
    reported as INVALID with rule R-0, never allowed to propagate.

    Found in practice, not hypothetically: running this against the real
    3,058-file legacy corpus (§Phase 9) crashed on a file with a non-string
    YAML key before this wrapper and the R-12 check existed — see
    schema/tests/test_real_corpus_regressions.py.
    """
    try:
        return _validate_artifact_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", artifact_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="R-0", evidence=f"{type(e).__name__}: {e}",
            )],
        )


def _validate_artifact_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function, regardless
    of its name or content (§Phase 5 — this is the meta-attack boundary).
    """
    result = ValidationResult(status="UNKNOWN", artifact_id=None, original_text=text)

    # --- R-1: parseable -------------------------------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(Issue(
            what="YAML could not be parsed or violated structural ceilings",
            why="unparseable or oversized input cannot be safely validated",
            where="<document>", rule="R-1", evidence=str(e),
        ))
        return result

    result.artifact_id = data.get("artifact_id") if isinstance(data.get("artifact_id"), str) else None

    # NOTE: `data` may contain a field literally named e.g. "validation_status"
    # with value "VALID", or "override_rules", or anything else. None of
    # that is ever read as control flow below — every field is looked up
    # by NAME against the fixed schema and checked; its VALUE is data.

    issues: list[Issue] = []

    # --- R-2: required fields -------------------------------------------
    missing = REQUIRED_FIELDS - data.keys()
    for f in sorted(missing):
        issues.append(Issue(
            what=f"required field '{f}' is missing", why="required by schema",
            where=f, rule="R-2", evidence="absent",
        ))

    # --- R-3: enum fields -------------------------------------------------
    for f, allowed in ENUM_FIELDS.items():
        if f in data:
            v = data[f]
            if v not in allowed:
                issues.append(Issue(
                    what=f"field '{f}' has invalid enum value",
                    why=f"must be one of the declared enum, never a novel or "
                        f"self-declared value — an artifact cannot invent a "
                        f"new state for itself",
                    where=f, rule="R-3", evidence=repr(v),
                ))

    # --- R-4: types for known structural fields --------------------------
    _expect_str = ("artifact_id", "artifact_type", "schema_version", "created_at",
                   "content_hash", "root_origin", "source_identity")
    for f in _expect_str:
        if f in data and data[f] is not None and not isinstance(data[f], str):
            issues.append(Issue(
                what=f"field '{f}' has wrong type", why="expected string",
                where=f, rule="R-4", evidence=f"got {type(data[f]).__name__}",
            ))
    _expect_list = ("parent_origins", "dependencies", "references",
                     "governance_references", "doctrine_references",
                     "evidence_references", "provenance_chain", "review_history")
    for f in _expect_list:
        if f in data and data[f] is not None and not isinstance(data[f], list):
            issues.append(Issue(
                what=f"field '{f}' has wrong type", why="expected list",
                where=f, rule="R-4", evidence=f"got {type(data[f]).__name__}",
            ))

    # --- R-5: hash shape ---------------------------------------------------
    for f in ("content_hash", "canonical_hash"):
        if f in data and data[f] is not None:
            if not isinstance(data[f], str) or not _HASH_RE.match(data[f]):
                issues.append(Issue(
                    what=f"field '{f}' is not a well-formed sha256 hash",
                    why="hash must match 'sha256:<64 hex chars>' exactly — a "
                        "close-looking string is not a hash",
                    where=f, rule="R-5", evidence=repr(data[f])[:80],
                ))

    # --- R-6: signature shape (never verified as TRUE here — only shape) --
    if "signature" in data and data["signature"] is not None:
        sig = data["signature"]
        if not isinstance(sig, str) or len(sig) < 16:
            issues.append(Issue(
                what="field 'signature' is malformed",
                why="a signature this short or non-string cannot be a real "
                    "signature; note that even a well-formed signature is "
                    "only checked for SHAPE here, never cryptographically "
                    "verified by this function",
                where="signature", rule="R-6", evidence=repr(sig)[:80],
            ))

    # --- R-7: timestamps -----------------------------------------------
    for f in ("created_at",):
        if f in data and data[f] is not None and not _is_valid_timestamp(data[f]):
            issues.append(Issue(
                what=f"field '{f}' is not a valid RFC3339 timestamp",
                why="malformed or ambiguous timestamps break provenance ordering",
                where=f, rule="R-7", evidence=repr(data[f])[:80],
            ))

    # --- R-8: impossible provenance relationships -----------------------
    root = data.get("root_origin")
    parents = data.get("parent_origins") or []
    aid = data.get("artifact_id")
    if isinstance(parents, list) and aid is not None and aid in parents:
        issues.append(Issue(
            what="artifact declares itself as its own parent",
            why="an artifact cannot be its own provenance ancestor — this is "
                "a self-referential provenance cycle of length 1",
            where="parent_origins", rule="R-8", evidence=f"artifact_id={aid!r} in parent_origins",
        ))
    if isinstance(parents, list) and root is not None and root == aid:
        issues.append(Issue(
            what="root_origin equals artifact_id",
            why="an artifact cannot originate from itself",
            where="root_origin", rule="R-8", evidence=f"root_origin == artifact_id == {aid!r}",
        ))

    # --- R-9: schema version -----------------------------------------------
    sv = data.get("schema_version")
    if sv is not None and sv != SCHEMA_VERSION:
        issues.append(Issue(
            what=f"declared schema_version '{sv}' does not match implemented "
                 f"schema '{SCHEMA_VERSION}'",
            why="an artifact cannot upgrade itself to a schema the validator "
                "does not implement by simply declaring the version string — "
                "unknown-version artifacts are UNKNOWN, never assumed compatible",
            where="schema_version", rule="R-9", evidence=repr(sv),
        ))

    # --- R-10: unauthorized / self-declared authority fields --------------
    # An artifact declaring fields that only the SYSTEM is permitted to set
    # (verdicts about itself) is a structural finding, not an authorization.
    _system_only_fields = {
        "validation_status", "quarantine_status",
    }
    for f in _system_only_fields:
        if f in data:
            issues.append(Issue(
                what=f"artifact declares system-only field '{f}'",
                why="validation_status/quarantine_status are OUTPUTS of this "
                    "system, never legitimate INPUTS. An artifact declaring "
                    "'validation_status: VALID' about itself is attempting to "
                    "self-certify — the value is recorded as evidence of the "
                    "attempt, never honoured",
                where=f, rule="R-10", evidence=repr(data[f]),
            ))

    # --- R-11: transition/rule self-redefinition attempts ------------------
    _forbidden_keys = {
        "transitions", "authorized_classes", "validation_rules",
        "override_rules", "ignore_previous_rules", "bypass_validation",
        "skip_validation", "disable_validation", "constitutional_root",
    }
    present_forbidden = _forbidden_keys & data.keys()
    for f in sorted(present_forbidden):
        issues.append(Issue(
            what=f"artifact declares a rule-redefinition field '{f}'",
            why="an artifact's own content can never redefine validator "
                "behaviour, transition tables, or authorization rules — "
                "these are DATA fields on the artifact, structurally inert, "
                "and are never read as configuration by this function",
            where=f, rule="R-11", evidence="present (ignored as data, flagged)",
        ))

    # --- non-string keys (§Phase 4 type-confusion class) ------------------
    # YAML permits non-string mapping keys (`true: value`, `1: value`).
    # REQUIRED_FIELDS/ENUM_FIELDS lookups above are keyed by string literals
    # so a non-string key simply never matches them — harmless. But it DOES
    # break a naive sorted() over a mixed str/bool/int key set, which is
    # exactly the kind of real-world input a hand-authored legacy corpus
    # contains (found by running this against 3,058 real files — not a
    # hypothetical). Every key is coerced to its string form before it is
    # compared against the schema's (all-string) known-field sets, so a
    # non-string key is correctly treated as unknown rather than crashing.
    data_keys_as_str = {k if isinstance(k, str) else repr(k) for k in data.keys()}
    non_string_keys = [k for k in data.keys() if not isinstance(k, str)]
    if non_string_keys:
        issues.append(Issue(
            what="mapping contains non-string keys",
            why="TitanOS artifact fields must be string-named; a boolean, "
                "int, or null key cannot be a declared field and is treated "
                "as structurally invalid input, not silently coerced",
            where="<document>", rule="R-12",
            evidence=f"key types present: {sorted({type(k).__name__ for k in data.keys()})}",
        ))

    # --- unknown fields (§Phase 2 — never silently trusted) ---------------
    known = MACHINE_VERIFIABLE_FIELDS | HUMAN_JUDGMENT_FIELDS
    unknown = sorted(data_keys_as_str - known)
    result.unknown_fields = unknown

    result.human_judgment_fields_present = sorted(
        HUMAN_JUDGMENT_FIELDS & data_keys_as_str
    )
    result.machine_verifiable_checked = sorted(
        MACHINE_VERIFIABLE_FIELDS & data_keys_as_str
    )

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
