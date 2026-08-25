"""
RPA cross-file referential integrity checker.

WHY THIS FILE EXISTS

rpa/BUILD_REPORT.md named this gap explicitly: every _ref field across the
legacy_system_map -> institutional_bottleneck -> automation_candidate ->
pilot_simulation chain is free text, checked for shape only by each
schema's own validator, never checked against what actually exists. Each
agent that built one of those schemas made the same documented judgment
call — a single-document validator must not load and trust arbitrary
other files, that breaks the "pure function over one document's text"
invariant every validator in this codebase holds. This file is the
SEPARATE composition-layer tool that judgment call always pointed at,
mirroring magl/composition/engine.py exactly: individual documents are
assumed already schema-valid (that's each validator's job, not this
file's); this file only reasons about the SET.

WHAT THIS DOES NOT DO

It does not re-validate schema. It does not re-run rule R-0..R-N for any
document. It takes already-parsed dicts (the caller's job to
yaml.safe_load them, ideally through each document's own validator first)
and checks that the promises they make to each other are kept: every
_ref actually resolves, every node id a bottleneck/map cites actually
exists in the map.

REFUSAL IS A SUCCESS STATE, same as magl/composition/engine.py and
firewall/gate.py — a chain with a dangling reference is refused loudly,
with every broken reference listed, not silently accepted with one
missing link.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping, Sequence

__all__ = ["Finding", "ChainIntegrityReport", "check_chain_integrity"]


@dataclass
class Finding:
    check: str
    severity: str  # "FATAL" | "WARNING" | "INFO"
    what: str
    why: str
    involved_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChainIntegrityReport:
    verdict: str  # "INTACT" | "REFUSED"
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"verdict": self.verdict, "findings": [f.to_dict() for f in self.findings]}


def _node_ids(map_doc: Mapping[str, Any]) -> set[str]:
    m = map_doc.get("legacy_system_map", {})
    return {n.get("id") for n in m.get("nodes", []) if isinstance(n, dict)}


def check_chain_integrity(
    *,
    map_doc: Mapping[str, Any] | None = None,
    bottleneck_docs: Sequence[Mapping[str, Any]] = (),
    candidate_docs: Sequence[Mapping[str, Any]] = (),
    pilot_docs: Sequence[Mapping[str, Any]] = (),
    rollback_docs: Sequence[Mapping[str, Any]] = (),
    measurement_docs: Sequence[Mapping[str, Any]] = (),
) -> ChainIntegrityReport:
    """Check that every cross-document reference in the chain resolves.

    Every argument is an already-parsed document dict (top-level key
    included, e.g. {"legacy_system_map": {...}}) — this function performs
    no YAML parsing and no schema validation of its own.
    """
    findings: list[Finding] = []

    map_id = None
    node_ids: set[str] = set()
    if map_doc is not None:
        map_id = map_doc.get("legacy_system_map", {}).get("id")
        node_ids = _node_ids(map_doc)

    bottleneck_ids: set[str] = set()
    for doc in bottleneck_docs:
        b = doc.get("institutional_bottleneck", {})
        bid = b.get("id")
        if bid:
            bottleneck_ids.add(bid)

        ref = b.get("system_map_ref")
        if map_id is not None and ref != map_id:
            findings.append(Finding(
                check="bottleneck_system_map_ref", severity="FATAL",
                what=f"bottleneck '{bid}' references system_map_ref "
                     f"'{ref}' but the supplied map's id is '{map_id}'",
                why="a bottleneck describing a map that isn't the one "
                    "actually being reasoned about is not describing "
                    "anything real",
                involved_ids=(bid, ref, map_id),
            ))

        if map_doc is not None:
            for nid in b.get("involved_node_ids", []):
                if nid not in node_ids:
                    findings.append(Finding(
                        check="bottleneck_involved_node_ids", severity="FATAL",
                        what=f"bottleneck '{bid}' cites node '{nid}' which "
                             f"does not exist in the supplied map",
                        why="a bottleneck cannot involve a node the map "
                            "never declared — this is a dangling reference, "
                            "the same class of defect the schema validators "
                            "individually cannot catch by design",
                        involved_ids=(bid, nid),
                    ))

    candidate_ids: set[str] = set()
    for doc in candidate_docs:
        c = doc.get("automation_candidate", {})
        cid = c.get("id")
        if cid:
            candidate_ids.add(cid)

        bref = c.get("bottleneck_ref")
        if bottleneck_docs and bref not in bottleneck_ids:
            findings.append(Finding(
                check="candidate_bottleneck_ref", severity="FATAL",
                what=f"candidate '{cid}' references bottleneck_ref "
                     f"'{bref}' which is not among the supplied bottlenecks",
                why="an automation candidate proposing to fix a bottleneck "
                    "that cannot be found has no verifiable justification",
                involved_ids=(cid, bref),
            ))

        mref = c.get("system_map_ref")
        if map_id is not None and mref != map_id:
            findings.append(Finding(
                check="candidate_system_map_ref", severity="FATAL",
                what=f"candidate '{cid}' references system_map_ref "
                     f"'{mref}' but the supplied map's id is '{map_id}'",
                why="the candidate must be scoped to the same map its "
                    "bottleneck was found in",
                involved_ids=(cid, mref, map_id),
            ))

    rollback_ids = {doc.get("rollback_contract", {}).get("id")
                    for doc in rollback_docs}
    measurement_ids = {doc.get("before_after_measurement", {}).get("id")
                       for doc in measurement_docs}

    for doc in rollback_docs:
        rb = doc.get("rollback_contract", {})
        rid = rb.get("id")

        aref = rb.get("applies_to_ref")
        if candidate_docs and aref not in candidate_ids:
            findings.append(Finding(
                check="rollback_candidate_ref", severity="FATAL",
                what=f"rollback contract '{rid}' references applies_to_ref "
                     f"'{aref}' which is not among the supplied automation "
                     f"candidates",
                why="validate_rollback_contract.py's own docstring names "
                    "this resolution as deliberately deferred to the "
                    "composition layer — a rollback contract citing a "
                    "candidate that cannot be found is not a rollback "
                    "target the architecture can trust",
                involved_ids=(rid, aref),
            ))
    pilot_ids: set[str] = set()
    for doc in pilot_docs:
        p = doc.get("pilot_simulation", {})
        if p.get("id"):
            pilot_ids.add(p["id"])

    for doc in measurement_docs:
        ba = doc.get("before_after_measurement", {})
        bid = ba.get("id")

        pref = ba.get("pilot_simulation_ref")
        if pilot_docs and pref not in pilot_ids:
            findings.append(Finding(
                check="measurement_pilot_ref", severity="FATAL",
                what=f"measurement '{bid}' references pilot_simulation_ref "
                     f"'{pref}' which is not among the supplied pilot "
                     f"simulations",
                why="validate_before_after_measurement.py's own docstring "
                    "names this resolution as deliberately deferred to the "
                    "composition layer — a measurement plan citing a pilot "
                    "that cannot be found is not measuring anything real",
                involved_ids=(bid, pref),
            ))

    for doc in pilot_docs:
        p = doc.get("pilot_simulation", {})
        pid = p.get("id")

        cref = p.get("automation_candidate_ref")
        if candidate_docs and cref not in candidate_ids:
            findings.append(Finding(
                check="pilot_candidate_ref", severity="FATAL",
                what=f"pilot '{pid}' references automation_candidate_ref "
                     f"'{cref}' which is not among the supplied candidates",
                why="a pilot simulating a candidate that cannot be found "
                    "is simulating nothing verifiable",
                involved_ids=(pid, cref),
            ))

        rref = p.get("rollback_plan_ref")
        if rollback_docs and rref not in rollback_ids:
            findings.append(Finding(
                check="pilot_rollback_ref", severity="FATAL",
                what=f"pilot '{pid}' references rollback_plan_ref '{rref}' "
                     f"which is not among the supplied rollback contracts",
                why="a pilot cannot be APPROVED_FOR_PILOT on the strength "
                    "of a rollback plan that does not actually exist",
                involved_ids=(pid, rref),
            ))

        mref = p.get("measurement_plan_ref")
        if measurement_docs and mref not in measurement_ids:
            findings.append(Finding(
                check="pilot_measurement_ref", severity="FATAL",
                what=f"pilot '{pid}' references measurement_plan_ref "
                     f"'{mref}' which is not among the supplied measurement "
                     f"plans",
                why="a pilot with no real measurement plan behind it cannot "
                    "learn anything, regardless of what its status field says",
                involved_ids=(pid, mref),
            ))

    verdict = "REFUSED" if any(f.severity == "FATAL" for f in findings) else "INTACT"
    return ChainIntegrityReport(verdict=verdict, findings=findings)
