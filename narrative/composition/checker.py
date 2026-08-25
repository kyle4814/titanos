"""
Narrative Atom cross-atom referential integrity checker.

WHY THIS FILE EXISTS

TRANSMISSION_DIGESTION_CONTINUITY_001's own Cross-Atom Law named the
real gap: `narrative_atom.py`'s `related_atoms`/`contradictions` fields
are real, already populated in real data (`NA-INGEST-002.related_atoms
== ["NA-INGEST-001"]`, `narrative/tests/
test_real_ingestion_recursion_guard.py`), but nothing anywhere resolves
them — `validate_narrative_atom.py` only checks each is a list (shape,
not existence), and `NarrativeAtomStore` tracks promotion state, not
atom content or cross-references at all. This is the exact same class
of gap `rpa/composition/checker.py` already closed four times this
session (measurement_pilot_ref, rollback_candidate_ref,
value_flow_system_map_ref, and the original bottleneck/candidate/pilot
chain) — mirrored here, not duplicated: same pure-function-over-
already-parsed-dicts boundary, same "refusal is a success state"
discipline, same Finding/Report shape.

WHAT THIS DOES NOT DO

It does not judge WHETHER a relation is true, meaningful, or
semantically correct — only whether the id it names actually exists
among the atoms supplied. It does not resolve contradictions (that
remains `kpm/contradictions/registry.py`'s job, a separate system this
file does not duplicate or import — a narrative atom's `contradictions`
field is a list of atom ids it contradicts, a different concept from
kpm's contradiction *records*). It does not query, rank, or traverse
relations beyond one hop. It does not promote either atom in a
relation — checking that a reference resolves is not evidence the
referenced atom's content is correct.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Mapping, Sequence

__all__ = ["Finding", "RelationIntegrityReport", "check_atom_relations"]


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
class RelationIntegrityReport:
    verdict: str  # "INTACT" | "REFUSED"
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"verdict": self.verdict, "findings": [f.to_dict() for f in self.findings]}


def check_atom_relations(
    atom_docs: Sequence[Mapping[str, Any]],
) -> RelationIntegrityReport:
    """Check that every `related_atoms`/`contradictions` id in the
    supplied set of narrative atom documents resolves to another atom
    in the same set.

    Every argument entry is an already-parsed document dict (top-level
    `narrative_atom:` key included) — this function performs no YAML
    parsing and no schema validation of its own, the same boundary
    `rpa/composition/checker.py::check_chain_integrity()` holds.

    A dangling id is refused loudly (FATAL), listing every broken
    reference — never silently accepted with one missing link.
    """
    findings: list[Finding] = []

    atom_ids: set[str] = set()
    for doc in atom_docs:
        a = doc.get("narrative_atom", {})
        aid = a.get("id")
        if aid:
            atom_ids.add(aid)

    for doc in atom_docs:
        a = doc.get("narrative_atom", {})
        aid = a.get("id")

        for ref in a.get("related_atoms") or []:
            if ref == aid:
                findings.append(Finding(
                    check="related_atoms_self_reference", severity="FATAL",
                    what=f"atom '{aid}' lists itself in related_atoms",
                    why="a self-reference is not a relation to another "
                        "atom — this is a malformed reference, not a "
                        "real structural link",
                    involved_ids=(aid,),
                ))
            elif ref not in atom_ids:
                findings.append(Finding(
                    check="related_atoms_dangling_ref", severity="FATAL",
                    what=f"atom '{aid}' references related_atoms id "
                         f"'{ref}' which is not among the supplied atoms",
                    why="a relation to an atom that cannot be found is "
                        "not a verifiable structural link — the same "
                        "class of defect rpa/composition/checker.py "
                        "catches for its own _ref chain",
                    involved_ids=(aid, ref),
                ))

        for ref in a.get("contradictions") or []:
            if ref == aid:
                findings.append(Finding(
                    check="contradictions_self_reference", severity="FATAL",
                    what=f"atom '{aid}' lists itself in contradictions",
                    why="an atom cannot contradict itself — this is a "
                        "malformed reference",
                    involved_ids=(aid,),
                ))
            elif ref not in atom_ids:
                findings.append(Finding(
                    check="contradictions_dangling_ref", severity="FATAL",
                    what=f"atom '{aid}' references contradictions id "
                         f"'{ref}' which is not among the supplied atoms",
                    why="a contradiction with an atom that cannot be "
                        "found is not verifiable",
                    involved_ids=(aid, ref),
                ))

    verdict = "REFUSED" if any(f.severity == "FATAL" for f in findings) else "INTACT"
    return RelationIntegrityReport(verdict=verdict, findings=findings)
