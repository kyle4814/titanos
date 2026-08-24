"""
Pilot Simulation Schema.

WHAT THIS FILE IS

The canonical, versioned definition of what fields a Pilot Simulation
YAML document may declare — the rpa/ package's counterpart to
rpa/schema/legacy_system_map.py, magl/schema/magl_schema.py, and
kpm/schemas/blueprint_atom.py. Same discipline: this module is data
(field names, enum universes, required-path tables), never behaviour.
All behaviour lives in rpa/validators/validate_pilot_simulation.py.

WHAT A PILOT SIMULATION IS

The governing directive's "Executive Sandbox" (§XII) requires that
before any real-world pilot of an automation candidate is run, a
structured "here's what we expect, here's what could go wrong" contract
exists: the current-state baseline, the proposed change, the expected
benefit, the known risks, an enumerated set of failure scenarios (each
with a stated detection method — HOW you'd know it happened, not just
that it might), a reference to a separately-owned rollback contract, and
a reference to a separately-owned before/after measurement plan. Only
once all of that is present and internally consistent may a pilot
simulation's status legitimately become APPROVED_FOR_PILOT — see
PS-R-9 in the validator.

WHY THIS SCHEMA REFERENCES OTHER DOCUMENTS BY ID RATHER THAN EMBEDDING
THEM

automation_candidate_ref, rollback_plan_ref, and measurement_plan_ref
are free-text string references to documents owned by other schemas
(automation_candidate, rollback_contract, before_after_measurement).
This schema does not, and will not, embed those documents inline or
perform cross-file existence validation — that would require this
validator to load and trust arbitrary other files at validation time,
which is out of scope for a pure, deterministic, single-document
structural validator. Cross-file existence/consistency checking, if
ever needed, belongs to a separate composition-layer tool, not here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import FrozenSet, Mapping

__all__ = [
    "SCHEMA_VERSION", "SCHEMA_ID",
    "LIKELIHOOD_VALUES", "IMPACT_VALUES", "STATUS_VALUES",
    "REQUIRED_TOP_FIELDS", "REQUIRED_BASELINE_FIELDS",
    "REQUIRED_FAILURE_SCENARIO_FIELDS", "REQUIRED_METRIC_FIELDS",
    "STRING_FIELDS", "LIST_FIELDS",
    "FieldGroup", "schema_hash",
]

SCHEMA_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

LIKELIHOOD_VALUES: FrozenSet[str] = frozenset({
    "LOW", "MEDIUM", "HIGH", "UNKNOWN",
})

IMPACT_VALUES: FrozenSet[str] = frozenset({
    "LOW", "MEDIUM", "HIGH", "SEVERE",
})

STATUS_VALUES: FrozenSet[str] = frozenset({
    "PROPOSED", "SIMULATED", "REJECTED", "APPROVED_FOR_PILOT",
})

# ─────────────────────────────────────────────────────────────
# Field groups / required-field tables
# ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FieldGroup:
    name: str
    fields: FrozenSet[str]


IDENTITY = FieldGroup("identity", frozenset({
    "id", "automation_candidate_ref",
}))
BASELINE = FieldGroup("baseline", frozenset({"baseline"}))
PROPOSAL = FieldGroup("proposal", frozenset({
    "proposed_change", "expected_benefit",
}))
RISK = FieldGroup("risk", frozenset({
    "known_risks", "failure_scenarios",
}))
PLANS = FieldGroup("plans", frozenset({
    "rollback_plan_ref", "measurement_plan_ref",
}))
LIFECYCLE = FieldGroup("lifecycle", frozenset({"status"}))

ALL_GROUPS = (IDENTITY, BASELINE, PROPOSAL, RISK, PLANS, LIFECYCLE)

# Top-level keys required directly under `pilot_simulation:`.
REQUIRED_TOP_FIELDS: FrozenSet[str] = frozenset({
    "id", "automation_candidate_ref", "baseline", "proposed_change",
    "expected_benefit", "known_risks", "failure_scenarios",
    "rollback_plan_ref", "measurement_plan_ref", "status",
})

# Required sub-fields within `baseline:` (a mapping).
REQUIRED_BASELINE_FIELDS: FrozenSet[str] = frozenset({"description"})

# Required per-entry fields within `failure_scenarios[]`.
REQUIRED_FAILURE_SCENARIO_FIELDS: FrozenSet[str] = frozenset({
    "scenario", "likelihood", "impact", "detection_method",
})

# Required per-entry fields within `baseline.metrics[]`.
REQUIRED_METRIC_FIELDS: FrozenSet[str] = frozenset({
    "name", "current_value",
})

# Top-level fields whose value, if present, must be a non-empty string.
STRING_FIELDS: FrozenSet[str] = frozenset({
    "id", "automation_candidate_ref", "proposed_change",
    "expected_benefit", "rollback_plan_ref", "measurement_plan_ref",
})

# Top-level fields whose value must be a list.
LIST_FIELDS: FrozenSet[str] = frozenset({
    "known_risks", "failure_scenarios",
})


def schema_hash() -> str:
    """Integrity-address the schema itself (same rationale as
    magl_schema.schema_hash / legacy_system_map.schema_hash): a claimed
    Pilot Simulation schema version should be checkable against what this
    validator actually implements."""
    payload = {
        "version": SCHEMA_VERSION,
        "required_top_fields": sorted(REQUIRED_TOP_FIELDS),
        "required_baseline_fields": sorted(REQUIRED_BASELINE_FIELDS),
        "required_failure_scenario_fields": sorted(REQUIRED_FAILURE_SCENARIO_FIELDS),
        "required_metric_fields": sorted(REQUIRED_METRIC_FIELDS),
        "likelihood_values": sorted(LIKELIHOOD_VALUES),
        "impact_values": sorted(IMPACT_VALUES),
        "status_values": sorted(STATUS_VALUES),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


SCHEMA_ID = f"pilot-simulation-schema-v{SCHEMA_VERSION}"
