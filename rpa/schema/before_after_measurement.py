"""
Before/After Measurement Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a Before/After
Measurement YAML document may declare — the rpa/ package's counterpart
to rpa/schema/pilot_simulation.py and rpa/schema/legacy_system_map.py.
Same discipline: this module is data (field names, enum universes,
required-path tables), never behaviour. All behaviour lives in
rpa/validators/validate_before_after_measurement.py.

WHAT A BEFORE/AFTER MEASUREMENT IS

A measurement plan for a specific pilot_simulation (referenced by
pilot_simulation_ref, free text, no cross-file validation — see
pilot_simulation.py's rationale for the same design choice): a
non-empty list of named metrics, each with a before_value that must
already be known at plan-authoring time, a measurement_method stating
HOW the metric is captured (not just what it is), and an optional
after_value that legitimately starts empty (the pilot hasn't run yet)
and is filled in once measurement actually happens. A conclusion may
only be drawn once every metric actually has an after_value — see
BA-R-6 in the validator; a measurement plan is not entitled to
conclude anything about metrics it never actually measured.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import FrozenSet

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "REQUIRED_TOP_FIELDS", "REQUIRED_METRIC_FIELDS",
    "STRING_FIELDS", "LIST_FIELDS",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Field groups / required-field tables
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({
    "id", "pilot_simulation_ref",
}))
MEASUREMENT = FieldGroup("measurement", frozenset({
    "metrics", "measurement_window", "confounding_factors",
}))
FINDING = FieldGroup("finding", frozenset({"conclusion"}))

ALL_GROUPS = (IDENTITY, MEASUREMENT, FINDING)

# Top-level keys required directly under `before_after_measurement:`.
# `conclusion` is deliberately excluded — it is optional (see BA-R-6).
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "pilot_simulation_ref", "metrics", "measurement_window",
    "confounding_factors",
})

# Required per-entry fields within `metrics[]`. `after_value` is
# deliberately excluded — it is optional (absent/empty means "not yet
# measured", a legitimate pre-pilot state).
REQUIRED_METRIC_FIELDS: FrozenSet[str] = frozenset({
    "name", "before_value", "measurement_method",
})

# Top-level fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "pilot_simulation_ref", "measurement_window",
})

# Top-level fields whose value must be a list (may be empty for
# confounding_factors — see validator BA-R-4).
LIST_FIELDS: FrozenSet[str] = frozenset({
    "metrics", "confounding_factors",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    pilot_simulation.schema_hash): a claimed Before/After Measurement
    schema version should be checkable against what this validator
    actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_metric_fields": sorted(REQUIRED_METRIC_FIELDS),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"before-after-measurement-schema-v{SCHEMA_VERSION}"
