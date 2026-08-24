"""
Legacy System Map Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this Legacy System Map conform to the declared schema,
     structurally, deterministically, and without executing anything it
     contains?"

It does NOT answer:
    - "Is this an accurate map of the real organisation?" (that is a
      question about the world, not about YAML shape — no validator can
      check ground truth)
    - "Does this organisation's epistemic_status claim deserve
      VERIFIED_FACT / EVIDENCE_SUPPORTED_MODEL / etc?" (a human judgment
      call made by whoever classified the map; this validator only
      checks that the declared value is a LEGAL member of the shared
      kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS vocabulary)
    - "What should this organisation change?" (this schema has no field
      for that opinion and never will — see LM-R-16 below)

A VALID result means "structurally conformant, and free of any
prescriptive content this schema forbids". It is never upgraded to
"accurate", "complete", or "approved for use in a transformation plan" —
those are other systems' vocabulary, if they exist at all.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_legacy_system_map() is a pure function over its input text.
Content found inside `text` is read as DATA throughout — never as an
instruction to this function, regardless of field name or content. No
field value changes control flow; every field is looked up by NAME
against the fixed schema.

HARDENING

Same parsing hardening as schema/validator.py, magl/validators/
validate_magl.py, and kpm/validators/validate_blueprint.py, replicated
deliberately rather than imported — each validator in this codebase owns
its own parsing hardening independently (the house pattern): duplicate-
key detection, document-size/node-count/depth ceilings enforced BEFORE
construction (to defeat alias/anchor expansion), and RecursionError
caught explicitly both at compose time and construct time, because
PyYAML's composer is itself recursive and can blow the Python call stack
before our own ceiling check gets a turn.

validate_legacy_system_map()'s entire body is wrapped in try/except so an
unforeseen exception becomes a structured INVALID result (rule LM-R-0)
rather than propagating — mirroring schema/validator.py's fail-closed
wrapper and the F-009/F-010 lesson (failures/FAILURE_ARCHIVE.md) it
encodes: an uncaught exception here would be a fail-OPEN bug in whatever
calls this validator.

RULE NUMBERING (LM-R-<n>, distinct from R-<n>, MG-R-<n>, BP-R-<n>)

  LM-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  LM-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  LM-R-2  top-level 'legacy_system_map' key present and is a mapping
  LM-R-3  mapping contains only string keys (type-confusion class)
  LM-R-4  required top-level fields present
  LM-R-5  identity string fields (id/organisation_name) non-empty
  LM-R-6  version is semver-shaped (N.N.N)
  LM-R-7  scanned_at is a valid RFC3339 timestamp
  LM-R-8  scan_method is a member of the declared enum
  LM-R-9  epistemic_status is a member of the imported
          kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS
  LM-R-10 nodes: non-empty list; each entry is a mapping with required
          fields, type/criticality enum membership, authority/
          known_failure_history list-shape, and node ids unique within
          the document
  LM-R-11 edges: list-shape; each entry is a mapping with required
          fields, relationship enum membership, is_manual boolean-shape,
          and from_node/to_node each reference a declared node id
  LM-R-12 boundaries: list-shape; each entry is a mapping with required
          fields, and every id in contains_node_ids references a
          declared node id
  LM-R-13 jurisdictions: list-shape; each entry is a mapping with
          required fields, basis non-empty, and authority_node_id /
          every id in scope_node_ids reference a declared node id
  LM-R-14 single_points_of_failure: list-shape; every entry references a
          declared node id
  LM-R-15 unknowns: required list present (may be empty), list-shape
  LM-R-16 no forbidden prescriptive field is present at the top level
          (automation_recommendation, proposed_change, suggested_fix,
          recommended_action, transformation_plan) — this map is
          descriptive only; presence of any of these is a structural
          rejection, not merely an unrecognised field, because letting a
          "what should change" opinion ride alongside "what was observed"
          is exactly the collapse the governing directive's
          map-before-transform sequencing exists to prevent
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

from rpa.schema.legacy_system_map import (  # noqa: E402
    CRITICALITY_LEVELS,
    EDGE_RELATIONSHIPS,
    EPISTEMIC_CLASSIFICATIONS,
    FORBIDDEN_PRESCRIPTIVE_FIELDS,
    LIST_FIELDS_TOP,
    NODE_TYPES,
    REQUIRED_BOUNDARY_FIELDS,
    REQUIRED_EDGE_FIELDS,
    REQUIRED_JURISDICTION_FIELDS,
    REQUIRED_NODE_FIELDS,
    REQUIRED_TOP_FIELDS,
    SCAN_METHODS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_legacy_system_map",
    "MalformedYamlError", "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

# Structural ceilings — same rationale and same values as
# schema/validator.py / magl/validators/validate_magl.py.
MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64

_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
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
    rule: str       # which rule ("LM-R-<n>") was violated
    evidence: str   # the observed value or condition, as a string

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    map_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    # Preservation invariant: original input is carried through untouched.
    # validate_legacy_system_map() never mutates its input.
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "map_id": self.map_id,
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


def validate_legacy_system_map(text: str) -> ValidationResult:
    """Deterministic structural validation of a Legacy System Map
    document. Never returns a bare bool, and never raises on real-world
    input — an uncaught exception here would be a fail-OPEN bug in
    whatever calls this. Any unforeseen failure is reported as INVALID
    with rule LM-R-0, never allowed to propagate (fail-closed, mirroring
    schema/validator.py's outer wrapper and the F-009/F-010 lesson it
    encodes)."""
    try:
        return _validate_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", map_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="LM-R-0", evidence=f"{type(e).__name__}: {e}",
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


def _validate_inner(text: str) -> ValidationResult:
    """Content found inside `text` is read as DATA throughout. No field
    value is ever interpreted as an instruction to this function."""
    result = ValidationResult(status="UNKNOWN", map_id=None, original_text=text)

    # --- LM-R-1: parseable + structural ceilings ----------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "LM-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- LM-R-2: top-level 'legacy_system_map' wrapper present and a mapping -
    if "legacy_system_map" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "LM-R-2", "top-level 'legacy_system_map' key is missing",
            "every Legacy System Map document must be wrapped in a "
            "top-level 'legacy_system_map:' key",
            "legacy_system_map", "absent",
        ))
        return result
    lm = data["legacy_system_map"]
    if not isinstance(lm, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "LM-R-2", "'legacy_system_map' value is not a mapping",
            "the 'legacy_system_map' key must contain a mapping of fields",
            "legacy_system_map", f"got {type(lm).__name__}",
        ))
        return result

    # --- LM-R-3: non-string keys (type-confusion class) ----------------------
    # Content found inside `lm` — including a key literally named
    # "epistemic_status" or "criticality" — is read as DATA below. Field
    # lookups are always by literal string name against the fixed schema; a
    # forged/self-declared field never changes control flow.
    non_string_keys = [k for k in lm.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "LM-R-3", "legacy_system_map mapping contains non-string keys",
            "fields must be string-named; a boolean/int/null key cannot be "
            "a declared field",
            "legacy_system_map", f"key types present: {sorted({type(k).__name__ for k in lm.keys()})}",
        ))

    lm_keys_as_str = {k if isinstance(k, str) else repr(k) for k in lm.keys()}

    map_id = lm.get("id") if isinstance(lm.get("id"), str) else None
    result.map_id = map_id

    issues: list[Issue] = list(result.issues)

    # --- LM-R-4: required top-level fields ------------------------------------
    missing = REQUIRED_TOP_FIELDS - lm.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "LM-R-4", f"required field 'legacy_system_map.{f}' is missing",
            "required by schema", f"legacy_system_map.{f}", "absent",
        ))

    # --- LM-R-5: identity string fields non-empty -----------------------------
    for f in ("id", "organisation_name"):
        if f in lm and (not isinstance(lm[f], str) or not lm[f].strip()):
            issues.append(_issue(
                "LM-R-5", f"field 'legacy_system_map.{f}' must be a "
                "non-empty string",
                "identity fields cannot be blank or non-string",
                f"legacy_system_map.{f}", lm.get(f),
            ))

    # --- LM-R-6: version is semver-shaped -------------------------------------
    version = lm.get("version")
    if isinstance(version, str) and version.strip() and not _VERSION_RE.match(version):
        issues.append(_issue(
            "LM-R-6", "field 'legacy_system_map.version' is not semver-shaped",
            "version must match N.N.N exactly — values like 'latest' or "
            "'v1' cannot be compared or resolved deterministically",
            "legacy_system_map.version", version,
        ))
    elif "version" in lm and not isinstance(version, str):
        issues.append(_issue(
            "LM-R-6", "field 'legacy_system_map.version' has wrong type",
            "expected string", "legacy_system_map.version",
            f"got {type(version).__name__}",
        ))

    # --- LM-R-7: scanned_at is a valid RFC3339 timestamp ----------------------
    scanned_at = lm.get("scanned_at")
    if "scanned_at" in lm and not _is_valid_timestamp(scanned_at):
        issues.append(_issue(
            "LM-R-7", "field 'legacy_system_map.scanned_at' is not a valid "
            "RFC3339 timestamp",
            "malformed or ambiguous timestamps break the map's evidential "
            "chain — a reader must be able to tell exactly when this "
            "organisation was observed",
            "legacy_system_map.scanned_at", scanned_at,
        ))

    # --- LM-R-8: scan_method enum membership ----------------------------------
    scan_method = lm.get("scan_method")
    if "scan_method" in lm and scan_method not in SCAN_METHODS:
        issues.append(_issue(
            "LM-R-8", "field 'legacy_system_map.scan_method' has invalid "
            "enum value",
            f"must be one of {sorted(SCAN_METHODS)}",
            "legacy_system_map.scan_method", scan_method,
        ))

    # --- LM-R-9: epistemic_status membership ----------------------------------
    epistemic_status = lm.get("epistemic_status")
    if "epistemic_status" in lm and epistemic_status not in EPISTEMIC_CLASSIFICATIONS:
        issues.append(_issue(
            "LM-R-9", "field 'legacy_system_map.epistemic_status' has "
            "invalid enum value",
            "must be a member of kpm.schemas.epistemic_types."
            "ALL_CLASSIFICATIONS — the same closed vocabulary every other "
            "claim in this codebase uses; a system map cannot invent its "
            "own confidence vocabulary, and a map built from one rushed "
            "interview is never entitled to VERIFIED_FACT merely by "
            "asserting it",
            "legacy_system_map.epistemic_status", epistemic_status,
        ))

    # --- LM-R-10: nodes ---------------------------------------------------------
    nodes = lm.get("nodes")
    known_node_ids: set[str] = set()
    if "nodes" in lm:
        if not isinstance(nodes, list):
            issues.append(_issue(
                "LM-R-10", "field 'legacy_system_map.nodes' has wrong type",
                "expected list", "legacy_system_map.nodes",
                f"got {type(nodes).__name__}",
            ))
            nodes = []
        elif len(nodes) == 0:
            issues.append(_issue(
                "LM-R-10", "field 'legacy_system_map.nodes' is empty",
                "a map with zero nodes describes nothing — at least one "
                "node is required for this to be a system map at all",
                "legacy_system_map.nodes", nodes,
            ))
        seen_ids: dict[str, int] = {}
        for idx, node in enumerate(nodes):
            where = f"legacy_system_map.nodes[{idx}]"
            if not isinstance(node, dict):
                issues.append(_issue(
                    "LM-R-10", f"entry {idx} of 'legacy_system_map.nodes' "
                    "is not a mapping",
                    "each node must be a mapping of node fields",
                    where, f"got {type(node).__name__}",
                ))
                continue
            missing_node = REQUIRED_NODE_FIELDS - node.keys()
            for f in sorted(missing_node):
                issues.append(_issue(
                    "LM-R-10", f"required field '{f}' missing on node {idx}",
                    "required by schema", f"{where}.{f}", "absent",
                ))
            node_id = node.get("id")
            if "id" in node:
                if not isinstance(node_id, str) or not node_id.strip():
                    issues.append(_issue(
                        "LM-R-10", f"node {idx} 'id' must be a non-empty string",
                        "a node with no stable id cannot be referenced by "
                        "edges/boundaries/jurisdictions",
                        f"{where}.id", node_id,
                    ))
                else:
                    if node_id in seen_ids:
                        issues.append(_issue(
                            "LM-R-10", f"duplicate node id {node_id!r} "
                            f"(also at index {seen_ids[node_id]})",
                            "node ids must be unique within the document — "
                            "duplicates make every reference to this id "
                            "ambiguous",
                            f"{where}.id", node_id,
                        ))
                    else:
                        seen_ids[node_id] = idx
                        known_node_ids.add(node_id)
            node_type = node.get("type")
            if "type" in node and node_type not in NODE_TYPES:
                issues.append(_issue(
                    "LM-R-10", f"node {idx} 'type' has invalid enum value",
                    f"must be one of {sorted(NODE_TYPES)}",
                    f"{where}.type", node_type,
                ))
            name = node.get("name")
            if "name" in node and (not isinstance(name, str) or not name.strip()):
                issues.append(_issue(
                    "LM-R-10", f"node {idx} 'name' must be a non-empty string",
                    "an unnamed node cannot be understood by a human reader",
                    f"{where}.name", name,
                ))
            for f in ("authority", "known_failure_history"):
                if f in node and not isinstance(node[f], list):
                    issues.append(_issue(
                        "LM-R-10", f"node {idx} '{f}' has wrong type",
                        "expected list", f"{where}.{f}",
                        f"got {type(node[f]).__name__}",
                    ))
            criticality = node.get("criticality")
            if "criticality" in node and criticality not in CRITICALITY_LEVELS:
                issues.append(_issue(
                    "LM-R-10", f"node {idx} 'criticality' has invalid "
                    "enum value",
                    f"must be one of {sorted(CRITICALITY_LEVELS)}",
                    f"{where}.criticality", criticality,
                ))
    else:
        nodes = []

    def _check_node_ref(rule: str, ref: Any, where: str, label: str) -> None:
        """A dangling reference to a node id that doesn't exist in
        nodes[] is a structural defect — reject with the missing id
        named explicitly."""
        if not isinstance(ref, str):
            issues.append(_issue(
                rule, f"{label} has wrong type", "expected string",
                where, f"got {type(ref).__name__}",
            ))
            return
        if ref not in known_node_ids:
            issues.append(_issue(
                rule, f"{label} references an unknown node id",
                "every reference must point to a node declared in "
                "legacy_system_map.nodes — a dangling reference describes "
                "a relationship to nothing",
                where, f"unknown node id {ref!r}",
            ))

    # --- LM-R-11: edges -----------------------------------------------------------
    edges = lm.get("edges")
    if "edges" in lm:
        if not isinstance(edges, list):
            issues.append(_issue(
                "LM-R-11", "field 'legacy_system_map.edges' has wrong type",
                "expected list", "legacy_system_map.edges",
                f"got {type(edges).__name__}",
            ))
            edges = []
        for idx, edge in enumerate(edges):
            where = f"legacy_system_map.edges[{idx}]"
            if not isinstance(edge, dict):
                issues.append(_issue(
                    "LM-R-11", f"entry {idx} of 'legacy_system_map.edges' "
                    "is not a mapping",
                    "each edge must be a mapping of edge fields",
                    where, f"got {type(edge).__name__}",
                ))
                continue
            missing_edge = REQUIRED_EDGE_FIELDS - edge.keys()
            for f in sorted(missing_edge):
                issues.append(_issue(
                    "LM-R-11", f"required field '{f}' missing on edge {idx}",
                    "required by schema", f"{where}.{f}", "absent",
                ))
            if "from_node" in edge:
                _check_node_ref("LM-R-11", edge.get("from_node"),
                                 f"{where}.from_node", f"edge {idx} 'from_node'")
            if "to_node" in edge:
                _check_node_ref("LM-R-11", edge.get("to_node"),
                                 f"{where}.to_node", f"edge {idx} 'to_node'")
            relationship = edge.get("relationship")
            if "relationship" in edge and relationship not in EDGE_RELATIONSHIPS:
                issues.append(_issue(
                    "LM-R-11", f"edge {idx} 'relationship' has invalid "
                    "enum value",
                    f"must be one of {sorted(EDGE_RELATIONSHIPS)}",
                    f"{where}.relationship", relationship,
                ))
            if "is_manual" in edge and not isinstance(edge.get("is_manual"), bool):
                issues.append(_issue(
                    "LM-R-11", f"edge {idx} 'is_manual' has wrong type",
                    "expected boolean — a manual handoff is a different "
                    "risk class than an automated one, and that fact must "
                    "be unambiguous",
                    f"{where}.is_manual", f"got {type(edge.get('is_manual')).__name__}",
                ))
            if "typical_delay" in edge and edge.get("typical_delay") is not None \
                    and not isinstance(edge.get("typical_delay"), str):
                issues.append(_issue(
                    "LM-R-11", f"edge {idx} 'typical_delay' has wrong type",
                    "expected string", f"{where}.typical_delay",
                    f"got {type(edge.get('typical_delay')).__name__}",
                ))
    else:
        edges = []

    # --- LM-R-12: boundaries -------------------------------------------------------
    boundaries = lm.get("boundaries")
    if "boundaries" in lm:
        if not isinstance(boundaries, list):
            issues.append(_issue(
                "LM-R-12", "field 'legacy_system_map.boundaries' has wrong type",
                "expected list", "legacy_system_map.boundaries",
                f"got {type(boundaries).__name__}",
            ))
            boundaries = []
        for idx, b in enumerate(boundaries):
            where = f"legacy_system_map.boundaries[{idx}]"
            if not isinstance(b, dict):
                issues.append(_issue(
                    "LM-R-12", f"entry {idx} of 'legacy_system_map.boundaries' "
                    "is not a mapping",
                    "each boundary must be a mapping of boundary fields",
                    where, f"got {type(b).__name__}",
                ))
                continue
            missing_b = REQUIRED_BOUNDARY_FIELDS - b.keys()
            for f in sorted(missing_b):
                issues.append(_issue(
                    "LM-R-12", f"required field '{f}' missing on boundary {idx}",
                    "required by schema", f"{where}.{f}", "absent",
                ))
            desc = b.get("description")
            if "description" in b and (not isinstance(desc, str) or not desc.strip()):
                issues.append(_issue(
                    "LM-R-12", f"boundary {idx} 'description' must be a "
                    "non-empty string",
                    "an undescribed boundary cannot be understood by a "
                    "human reader",
                    f"{where}.description", desc,
                ))
            contains = b.get("contains_node_ids")
            if "contains_node_ids" in b:
                if not isinstance(contains, list):
                    issues.append(_issue(
                        "LM-R-12", f"boundary {idx} 'contains_node_ids' "
                        "has wrong type",
                        "expected list", f"{where}.contains_node_ids",
                        f"got {type(contains).__name__}",
                    ))
                else:
                    for j, nid in enumerate(contains):
                        _check_node_ref(
                            "LM-R-12", nid, f"{where}.contains_node_ids[{j}]",
                            f"boundary {idx} 'contains_node_ids[{j}]'",
                        )
    else:
        boundaries = []

    # --- LM-R-13: jurisdictions -----------------------------------------------------
    jurisdictions = lm.get("jurisdictions")
    if "jurisdictions" in lm:
        if not isinstance(jurisdictions, list):
            issues.append(_issue(
                "LM-R-13", "field 'legacy_system_map.jurisdictions' has "
                "wrong type",
                "expected list", "legacy_system_map.jurisdictions",
                f"got {type(jurisdictions).__name__}",
            ))
            jurisdictions = []
        for idx, j in enumerate(jurisdictions):
            where = f"legacy_system_map.jurisdictions[{idx}]"
            if not isinstance(j, dict):
                issues.append(_issue(
                    "LM-R-13", f"entry {idx} of 'legacy_system_map.jurisdictions' "
                    "is not a mapping",
                    "each jurisdiction claim must be a mapping of "
                    "jurisdiction fields",
                    where, f"got {type(j).__name__}",
                ))
                continue
            missing_j = REQUIRED_JURISDICTION_FIELDS - j.keys()
            for f in sorted(missing_j):
                issues.append(_issue(
                    "LM-R-13", f"required field '{f}' missing on "
                    f"jurisdiction claim {idx}",
                    "required by schema", f"{where}.{f}", "absent",
                ))
            if "authority_node_id" in j:
                _check_node_ref(
                    "LM-R-13", j.get("authority_node_id"),
                    f"{where}.authority_node_id",
                    f"jurisdiction {idx} 'authority_node_id'",
                )
            scope = j.get("scope_node_ids")
            if "scope_node_ids" in j:
                if not isinstance(scope, list):
                    issues.append(_issue(
                        "LM-R-13", f"jurisdiction {idx} 'scope_node_ids' "
                        "has wrong type",
                        "expected list", f"{where}.scope_node_ids",
                        f"got {type(scope).__name__}",
                    ))
                else:
                    for k, nid in enumerate(scope):
                        _check_node_ref(
                            "LM-R-13", nid, f"{where}.scope_node_ids[{k}]",
                            f"jurisdiction {idx} 'scope_node_ids[{k}]'",
                        )
            basis = j.get("basis")
            if "basis" in j and (not isinstance(basis, str) or not basis.strip()):
                issues.append(_issue(
                    "LM-R-13", f"jurisdiction {idx} 'basis' must be a "
                    "non-empty string",
                    "a jurisdiction claim with no stated basis is exactly "
                    "the unaccountable-authority pattern forbidden "
                    "elsewhere in this codebase — authority must always "
                    "point to a reason it exists",
                    f"{where}.basis", basis,
                ))
    else:
        jurisdictions = []

    # --- LM-R-14: single_points_of_failure --------------------------------------------
    spof = lm.get("single_points_of_failure")
    if "single_points_of_failure" in lm:
        if not isinstance(spof, list):
            issues.append(_issue(
                "LM-R-14", "field 'legacy_system_map.single_points_of_failure' "
                "has wrong type",
                "expected list", "legacy_system_map.single_points_of_failure",
                f"got {type(spof).__name__}",
            ))
        else:
            for idx, nid in enumerate(spof):
                _check_node_ref(
                    "LM-R-14", nid,
                    f"legacy_system_map.single_points_of_failure[{idx}]",
                    f"single_points_of_failure[{idx}]",
                )

    # --- LM-R-15: unknowns (required, may be empty) -------------------------------------
    unknowns = lm.get("unknowns")
    if "unknowns" in lm and not isinstance(unknowns, list):
        issues.append(_issue(
            "LM-R-15", "field 'legacy_system_map.unknowns' has wrong type",
            "expected list — gaps in the map must be explicitly "
            "preserved, never silently omitted",
            "legacy_system_map.unknowns", f"got {type(unknowns).__name__}",
        ))

    # --- LM-R-16: forbidden prescriptive fields ---------------------------------------
    # This map is descriptive only. Presence of any of these is a
    # structural rejection, not merely an unrecognised field — see module
    # docstring for why "what we found" and "what we should do" must
    # never share a record.
    present_forbidden = sorted(FORBIDDEN_PRESCRIPTIVE_FIELDS & lm.keys())
    for f in present_forbidden:
        issues.append(_issue(
            "LM-R-16", f"forbidden prescriptive field 'legacy_system_map.{f}' "
            "is present",
            "a Legacy System Map is strictly descriptive — it records "
            "what was observed, never what should change; an "
            "automation/transformation opinion riding alongside the "
            "observation collapses the map-before-transform sequencing "
            "the governing directive requires",
            f"legacy_system_map.{f}", lm.get(f),
        ))

    # --- unknown fields (never silently trusted) ------------------------------------
    known = set(REQUIRED_TOP_FIELDS)
    unknown = sorted(lm_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
