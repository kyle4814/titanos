"""
Normalized Security Event Validator.

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "Does this normalized_security_event document conform to the
     declared schema, structurally, deterministically, and without
     executing anything it contains?"

It does NOT answer:
    - "Is this event a real threat?" (that is a VERDICT — a different
      schema, owned by a different agent, built on top of events like
      this one. This validator's entire job on that question is to
      REJECT the document if it tries to answer it itself — see SE-R-9)
    - "Does related_permission_request_ref point at a real
      permission_request?" (no cross-file validation is performed here —
      documented boundary, same as every other `_ref` field in this
      codebase's history)

A VALID result means "structurally conformant observation record,
carrying no verdict fields". It is never upgraded to "investigated",
"triaged", or "resolved" — those are other systems' vocabulary.

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

validate_normalized_security_event() is a pure function over its input
text. Content found inside `text` is read as DATA throughout — never as
an instruction to this function. `signals` entries are read and checked
against a small literal blocklist (see SE-R-8), never parsed for meaning
beyond that literal substring check.

HARDENING

Same parsing hardening as magl/validators/validate_magl.py and
taal/validators/validate_permission_request.py, deliberately duplicated
rather than imported (house pattern — each validator owns its own
hardening independently): duplicate-key detection, document-size/
node-count/depth ceilings enforced BEFORE construction, and
RecursionError caught explicitly both at compose time and construct
time. validate_normalized_security_event()'s entire body is wrapped in
try/except so an unforeseen exception becomes a structured INVALID
result (SE-R-0) rather than propagating — an uncaught exception here
would be a fail-OPEN bug in whatever calls this validator.

RULE NUMBERING (SE-R-<n>)

  SE-R-0  fail-closed outer wrapper (unforeseen exception -> INVALID)
  SE-R-1  YAML parseable + structural ceilings (size/nodes/depth)
  SE-R-2  top-level 'normalized_security_event' key present and is a mapping
  SE-R-3  mapping contains only string keys (type-confusion class)
  SE-R-4  required top-level fields present
  SE-R-5  string fields non-empty; observed_at is RFC3339-shaped;
          source_type / confidence enum membership (confidence drawn
          from kpm.schemas.epistemic_types.ALL_CLASSIFICATIONS)
  SE-R-6  signals: non-empty list of non-empty strings
  SE-R-7  related_permission_request_ref, if present, is a non-empty
          string (free-text pointer, no cross-file resolution attempted)
  SE-R-8  JUDGMENT-CALL rule: a signals entry containing a word from
          CONCLUSORY_WORD_BLOCKLIST ("malicious", "attack", "compromised",
          "confirmed") is rejected as a structural violation — a signal
          must record what was observed, never what it is concluded to
          mean
  SE-R-9  any FORBIDDEN_VERDICT_FIELDS key present (verdict, threat_label,
          attack_confirmed, is_malicious, recommended_action) ->
          unconditional INVALID; these belong to a separate VERDICT
          schema and must never appear on an observation record
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

from taal.schema.normalized_security_event import (  # noqa: E402
    CONCLUSORY_WORD_BLOCKLIST,
    EPISTEMIC_CLASSIFICATIONS,
    FORBIDDEN_VERDICT_FIELDS,
    REQUIRED_TOP_FIELDS,
    SOURCE_TYPES,
    STRING_FIELDS,
)

__all__ = [
    "Issue", "ValidationResult", "validate_normalized_security_event",
    "MalformedYamlError", "MAX_DOCUMENT_BYTES", "MAX_NODES", "MAX_DEPTH",
]

MAX_DOCUMENT_BYTES = 2_000_000
MAX_NODES = 50_000
MAX_DEPTH = 64

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
    what: str
    why: str
    where: str
    rule: str       # "SE-R-<n>"
    evidence: str
    severity: str = "FATAL"  # this schema has no non-fatal rule class today

    def to_dict(self) -> dict[str, str]:
        return {"what": self.what, "why": self.why, "where": self.where,
                "rule": self.rule, "evidence": self.evidence,
                "severity": self.severity}


@dataclass
class ValidationResult:
    status: str  # "VALID" | "INVALID" | "UNKNOWN"
    event_id: str | None
    issues: list[Issue] = field(default_factory=list)
    unknown_fields: list[str] = field(default_factory=list)
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "event_id": self.event_id,
            "issues": [i.to_dict() for i in self.issues],
            "unknown_fields": self.unknown_fields,
        }


# ─────────────────────────────────────────────────────────────
# Duplicate-key-detecting, alias-bounded safe loader
# (deliberately duplicated — house pattern, see validate_permission_request.py)
# ─────────────────────────────────────────────────────────────

class _DuplicateKeyError(Exception):
    def __init__(self, key: Any, path: str):
        self.key = key
        self.path = path


class _BoundedSafeLoader(yaml.SafeLoader):
    """SafeLoader only — never yaml.Loader/FullLoader."""


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


def validate_normalized_security_event(text: str) -> ValidationResult:
    """Deterministic structural validation of a normalized_security_event
    document. Never returns a bare bool, and never raises on real-world
    input. Any unforeseen failure is reported as INVALID with rule
    SE-R-0, never allowed to propagate (fail-closed)."""
    try:
        return _validate_inner(text)
    except Exception as e:  # noqa: BLE001 — deliberate: never fail open
        return ValidationResult(
            status="INVALID", event_id=None, original_text=text,
            issues=[Issue(
                what="internal validation error",
                why="an unforeseen input shape broke a structural check; "
                    "treated as a rejection rather than propagated, so a "
                    "caller can never mistake a crash for a pass",
                where="<validator>", rule="SE-R-0", evidence=f"{type(e).__name__}: {e}",
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
    """Content found inside `text` is read as DATA throughout. `signals`
    entries are checked against a small literal blocklist (SE-R-8) and
    otherwise never parsed for meaning."""
    result = ValidationResult(status="UNKNOWN", event_id=None, original_text=text)

    # --- SE-R-1: parseable + structural ceilings ------------------------------
    try:
        data = _safe_parse(text)
    except MalformedYamlError as e:
        result.status = "INVALID"
        result.issues.append(_issue(
            "SE-R-1", "YAML could not be parsed or violated structural ceilings",
            "unparseable or oversized input cannot be safely validated",
            "<document>", str(e),
        ))
        return result

    # --- SE-R-2: top-level 'normalized_security_event' wrapper ----------------
    if "normalized_security_event" not in data:
        result.status = "INVALID"
        result.issues.append(_issue(
            "SE-R-2", "top-level 'normalized_security_event' key is missing",
            "every normalized security event document must be wrapped in "
            "a top-level 'normalized_security_event:' key",
            "normalized_security_event", "absent",
        ))
        return result
    ev = data["normalized_security_event"]
    if not isinstance(ev, dict):
        result.status = "INVALID"
        result.issues.append(_issue(
            "SE-R-2", "'normalized_security_event' value is not a mapping",
            "the 'normalized_security_event' key must contain a mapping "
            "of fields",
            "normalized_security_event", f"got {type(ev).__name__}",
        ))
        return result

    # --- SE-R-3: non-string keys (type-confusion class) ------------------------
    non_string_keys = [k for k in ev.keys() if not isinstance(k, str)]
    if non_string_keys:
        result.issues.append(_issue(
            "SE-R-3", "normalized_security_event mapping contains "
            "non-string keys",
            "fields must be string-named; a boolean/int/null key cannot "
            "be a declared field",
            "normalized_security_event",
            f"key types present: {sorted({type(k).__name__ for k in ev.keys()})}",
        ))

    ev_keys_as_str = {k if isinstance(k, str) else repr(k) for k in ev.keys()}
    event_id = ev.get("id") if isinstance(ev.get("id"), str) else None
    result.event_id = event_id

    issues: list[Issue] = list(result.issues)

    # --- SE-R-4: required top-level fields --------------------------------------
    missing = REQUIRED_TOP_FIELDS - ev.keys()
    for f in sorted(missing):
        issues.append(_issue(
            "SE-R-4", f"required field 'normalized_security_event.{f}' is missing",
            "required by schema", f"normalized_security_event.{f}", "absent",
        ))

    # --- SE-R-5: string fields, observed_at timestamp shape, enum membership ---
    for f in sorted(STRING_FIELDS):
        if f in ev and (not isinstance(ev[f], str) or not ev[f].strip()):
            issues.append(_issue(
                "SE-R-5", f"field 'normalized_security_event.{f}' must be "
                "a non-empty string",
                "an unstated or blank value cannot represent the "
                "observation precisely",
                f"normalized_security_event.{f}", ev.get(f),
            ))

    observed_at = ev.get("observed_at")
    if "observed_at" in ev and isinstance(observed_at, str) and observed_at.strip() and not _is_valid_timestamp(observed_at):
        issues.append(_issue(
            "SE-R-5", "field 'normalized_security_event.observed_at' is "
            "not a valid RFC3339 timestamp",
            "malformed or ambiguous timestamps break event ordering and "
            "correlation",
            "normalized_security_event.observed_at", observed_at,
        ))

    source_type = ev.get("source_type")
    if "source_type" in ev and source_type not in SOURCE_TYPES:
        issues.append(_issue(
            "SE-R-5", "field 'normalized_security_event.source_type' has "
            "invalid enum value",
            f"must be one of {sorted(SOURCE_TYPES)}",
            "normalized_security_event.source_type", source_type,
        ))

    confidence = ev.get("confidence")
    if "confidence" in ev and confidence not in EPISTEMIC_CLASSIFICATIONS:
        issues.append(_issue(
            "SE-R-5", "field 'normalized_security_event.confidence' has "
            "invalid enum value",
            "must be a member of kpm.schemas.epistemic_types."
            "ALL_CLASSIFICATIONS — the same closed vocabulary every other "
            "claim in this codebase uses; a normalized event cannot "
            "invent its own confidence vocabulary",
            "normalized_security_event.confidence", confidence,
        ))

    # --- SE-R-6: signals — non-empty list of non-empty strings -----------------
    signals = ev.get("signals")
    if "signals" in ev:
        if not isinstance(signals, list) or len(signals) == 0:
            issues.append(_issue(
                "SE-R-6", "field 'normalized_security_event.signals' "
                "must be a non-empty list",
                "an observation record with zero observable facts is not "
                "structurally an observation",
                "normalized_security_event.signals", signals,
            ))
            signals = []
        else:
            for s in signals:
                if not isinstance(s, str) or not s.strip():
                    issues.append(_issue(
                        "SE-R-6", "entry in "
                        "'normalized_security_event.signals' is not a "
                        "non-empty string",
                        "each signal must be a factual, string-described "
                        "observation",
                        "normalized_security_event.signals", s,
                    ))
    else:
        signals = []

    # --- SE-R-7: related_permission_request_ref (optional, free-text) ----------
    ref = ev.get("related_permission_request_ref")
    if "related_permission_request_ref" in ev and ref is not None:
        if not isinstance(ref, str) or not ref.strip():
            issues.append(_issue(
                "SE-R-7", "field "
                "'normalized_security_event.related_permission_request_ref' "
                "must be a non-empty string when present",
                "a blank reference is not a usable pointer; no "
                "cross-file resolution is attempted here — this is a "
                "free-text reference boundary, same as every other "
                "'_ref' field in this codebase",
                "normalized_security_event.related_permission_request_ref", ref,
            ))

    # --- SE-R-8: JUDGMENT-CALL — conclusory-word blocklist in signals ----------
    if isinstance(signals, list):
        for s in signals:
            if not isinstance(s, str):
                continue
            lowered = s.lower()
            hit_words = sorted(
                w for w in CONCLUSORY_WORD_BLOCKLIST if w in lowered
            )
            if hit_words:
                issues.append(_issue(
                    "SE-R-8", "signals entry contains a conclusory word",
                    "a signal must record what was observed, never what "
                    "it is concluded to mean — e.g. '3 failed auth "
                    "attempts in 10s' is a fine signal, 'looks like brute "
                    "force' is not. This narrow literal blocklist "
                    f"({sorted(CONCLUSORY_WORD_BLOCKLIST)}) cannot catch "
                    "every conclusory phrasing, only the small set of "
                    "words that are almost never legitimate inside a "
                    "factual observation string",
                    "normalized_security_event.signals",
                    {"entry": s, "blocklist_hits": hit_words},
                ))

    # --- SE-R-9: forbidden verdict fields -> unconditional INVALID -------------
    present_forbidden = sorted(FORBIDDEN_VERDICT_FIELDS & ev.keys())
    for f in present_forbidden:
        issues.append(_issue(
            "SE-R-9", f"field 'normalized_security_event.{f}' is a "
            "forbidden verdict field",
            "this schema is an OBSERVATION record and must never contain "
            "a conclusion — verdict/threat_label/attack_confirmed/"
            "is_malicious/recommended_action all belong to a separate "
            "VERDICT schema owned by a different component. This is the "
            "load-bearing separation of this schema (observation vs. "
            "conclusion), mirroring "
            "rpa/schema/legacy_system_map.py's "
            "FORBIDDEN_PRESCRIPTIVE_FIELDS pattern",
            f"normalized_security_event.{f}", ev.get(f),
        ))

    # --- unknown fields (never silently trusted) --------------------------------
    known = set(REQUIRED_TOP_FIELDS) | {"related_permission_request_ref"}
    unknown = sorted(ev_keys_as_str - known)
    result.unknown_fields = unknown

    result.issues = issues
    result.status = "INVALID" if issues else "VALID"
    return result
