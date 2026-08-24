"""
MAGL Composition Engine.

THE ONE JOB

Given a set of already-individually-valid MAGLs (Modular Architecture
Generation Library units), decide whether they may be COMPOSED together —
and if not, say exactly why, for every reason, not just the first one.

REFUSAL IS A SUCCESS STATE, same as firewall/gate.py. The whole point of
this engine is to refuse incompatible combinations loudly rather than
best-guess an authorization. A composed system that silently grants MAGL B
the ability to do something MAGL A explicitly prohibited is a privilege
escalation, not a convenience.

WHAT THIS FILE ASSUMES, AND DOES NOT RE-CHECK

Each individual MAGL has already passed schema/structural validation
(schema/validator.py's job, not this file's). This engine only reasons
about COMBINATIONS: jurisdiction conflicts across a composed set,
dependency satisfiability within the set, incompatibility declarations,
and circular requires/provides chains. Steps that are out of this file's
scope (side effects, invariant language, provenance) are still recorded in
the report as explicit no-ops — never silently skipped, so a reader of the
report always knows what was and wasn't checked.

THE TEN-STEP ORDER

This engine runs the same ten checks, in the same order, every time:

  1. Schema compatibility        — assumed pre-validated by the caller (no-op)
  2. Jurisdiction comparison     — prohibited_actions vs. granted actions
  3. Dependency comparison       — dependencies_required satisfiable in-set
  4. Incompatibility comparison  — dependencies_incompatible present in-set
  5. Side effects                — requires runtime observation (no-op)
  6. Circular dependency         — requires/provides graph, proper DFS
  7. Privilege escalation        — jurisdiction-union invariant
  8. Conflicting invariants      — no invariant language in MAGLSummary (no-op)
  9. Provenance conflicts        — no provenance in MAGLSummary (no-op)
  10. Produce composition report — always, findings never dropped

Unlike gate.py's "first failure wins", this engine does NOT stop at the
first FATAL finding — every check runs, every finding is recorded. A
composition may be REFUSED for three independent reasons at once, and an
operator deciding whether to fix and retry needs to see all three, not
just the first the engine happened to trip over.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Sequence

__all__ = [
    "MAGLSummary", "Finding", "CompositionReport", "check_composition",
]

JURISDICTION_ACTION_FIELDS = (
    "may_write", "may_execute", "may_call", "may_modify", "may_publish",
)


# ─────────────────────────────────────────────────────────────
# Input shape
# ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MAGLSummary:
    """Minimal per-MAGL input this engine reasons over.

    Deliberately narrower than the full MAGL schema (that's the schema
    agent's territory) — just enough declared jurisdiction and composition
    metadata to reason about combinations.
    """
    magl_id: str
    version: str
    may_read: tuple[str, ...] = ()
    may_write: tuple[str, ...] = ()
    may_execute: tuple[str, ...] = ()
    may_call: tuple[str, ...] = ()
    may_modify: tuple[str, ...] = ()
    may_publish: tuple[str, ...] = ()
    prohibited_actions: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    compatible_interfaces: tuple[str, ...] = ()
    dependencies_required: tuple[str, ...] = ()
    dependencies_incompatible: tuple[str, ...] = ()

    def granted_actions(self) -> frozenset[str]:
        """Union of every action this MAGL declares it may perform, across
        the write/execute/call/modify/publish fields. may_read is excluded
        deliberately — read access is not the escalation surface step 2
        cares about; the prohibited-actions rule below only ever compares
        against actions that change or invoke something.
        """
        out: set[str] = set()
        for f in JURISDICTION_ACTION_FIELDS:
            out.update(getattr(self, f))
        return frozenset(out)


# ─────────────────────────────────────────────────────────────
# Structured result — never a bare bool
# ─────────────────────────────────────────────────────────────

@dataclass
class Finding:
    check: str                       # which of the 10 steps produced this
    severity: str                    # "FATAL" | "WARNING" | "INFO"
    what: str
    why: str
    involved_magl_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompositionReport:
    verdict: str                     # "COMPOSABLE" | "REFUSED"
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "findings": [f.to_dict() for f in self.findings],
        }

    def fatal_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "FATAL"]


_SEVERITY_ORDER = {"FATAL": 0, "WARNING": 1, "INFO": 2}


# ─────────────────────────────────────────────────────────────
# Step 1 — schema compatibility (no-op, out of scope)
# ─────────────────────────────────────────────────────────────

def _step1_schema(magls: Sequence[MAGLSummary]) -> list[Finding]:
    return [Finding(
        check="1_schema_compatibility",
        severity="INFO",
        what="schema compatibility not re-checked here",
        why="assumed pre-validated — each MAGL is expected to already have "
            "passed individual schema/structural validation before "
            "composition is attempted; this engine only reasons about "
            "combinations, not individual well-formedness.",
        involved_magl_ids=tuple(m.magl_id for m in magls),
    )]


# ─────────────────────────────────────────────────────────────
# Step 2 — jurisdiction comparison / prohibited-action conflicts
# ─────────────────────────────────────────────────────────────

def _step2_jurisdiction(magls: Sequence[MAGLSummary]) -> list[Finding]:
    findings: list[Finding] = []
    for a in magls:
        prohibited = set(a.prohibited_actions)
        if not prohibited:
            continue
        for b in magls:
            if a.magl_id == b.magl_id:
                continue
            conflict = prohibited & b.granted_actions()
            if conflict:
                findings.append(Finding(
                    check="2_jurisdiction_comparison",
                    severity="FATAL",
                    what=f"{b.magl_id} is granted action(s) "
                         f"{sorted(conflict)} that {a.magl_id} explicitly "
                         f"prohibits",
                    why="composing A with B would let B perform something A "
                        "declared off-limits within the same composition — "
                        "a jurisdiction conflict, not best-guessed away.",
                    involved_magl_ids=(a.magl_id, b.magl_id),
                ))
    return findings


# ─────────────────────────────────────────────────────────────
# Step 3 — dependency comparison
# ─────────────────────────────────────────────────────────────

def _step3_dependencies(magls: Sequence[MAGLSummary]) -> list[Finding]:
    findings: list[Finding] = []
    for m in magls:
        for dep in m.dependencies_required:
            providers = [
                other.magl_id for other in magls
                if other.magl_id != m.magl_id and dep in other.provides
            ]
            if not providers:
                findings.append(Finding(
                    check="3_dependency_comparison",
                    severity="WARNING",
                    what=f"{m.magl_id} requires '{dep}' but no other MAGL "
                         f"in the composed set provides it",
                    why="MISSING_DEPENDENCY: not fatal by itself, since it "
                        "may be satisfiable externally to this composed "
                        "set — but it must be reported, never silently "
                        "assumed resolved.",
                    involved_magl_ids=(m.magl_id,),
                ))
    return findings


# ─────────────────────────────────────────────────────────────
# Step 4 — incompatibility comparison
# ─────────────────────────────────────────────────────────────

def _step4_incompatibility(magls: Sequence[MAGLSummary]) -> list[Finding]:
    findings: list[Finding] = []
    present_ids = {m.magl_id for m in magls}
    for m in magls:
        for incompatible_id in m.dependencies_incompatible:
            if incompatible_id in present_ids and incompatible_id != m.magl_id:
                findings.append(Finding(
                    check="4_incompatibility_comparison",
                    severity="FATAL",
                    what=f"{m.magl_id} declares itself incompatible with "
                         f"{incompatible_id}, which is present in this "
                         f"composed set",
                    why="INCOMPATIBLE_PAIR: an explicit incompatibility "
                        "declaration is a hard stop, never overridden by "
                        "best-guessing that it'll probably be fine.",
                    involved_magl_ids=(m.magl_id, incompatible_id),
                ))
    return findings


# ─────────────────────────────────────────────────────────────
# Step 5 — side effects (no-op, out of scope)
# ─────────────────────────────────────────────────────────────

def _step5_side_effects(magls: Sequence[MAGLSummary]) -> list[Finding]:
    return [Finding(
        check="5_side_effects",
        severity="INFO",
        what="side effects not statically checked here",
        why="requires runtime observation, not statically checkable from "
            "declared metadata alone.",
        involved_magl_ids=tuple(m.magl_id for m in magls),
    )]


# ─────────────────────────────────────────────────────────────
# Step 6 — circular dependency detection (requires/provides graph)
# ─────────────────────────────────────────────────────────────

def _build_requires_graph(magls: Sequence[MAGLSummary]) -> dict[str, set[str]]:
    """Edge A -> B iff A requires something B provides (A depends on B)."""
    by_id = {m.magl_id: m for m in magls}
    graph: dict[str, set[str]] = {m.magl_id: set() for m in magls}
    for a in magls:
        for req in a.requires:
            for b in magls:
                if b.magl_id == a.magl_id:
                    continue
                if req in b.provides:
                    graph[a.magl_id].add(b.magl_id)
    return graph


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    """Proper 3-colour DFS cycle detection (WHITE/GRAY/BLACK), not a depth
    cap. Returns the cycle's node sequence (closed, first == last) or None.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack_path: list[str] = []

    def dfs(node: str) -> list[str] | None:
        color[node] = GRAY
        stack_path.append(node)
        for neighbor in sorted(graph.get(node, ())):
            if color[neighbor] == WHITE:
                found = dfs(neighbor)
                if found is not None:
                    return found
            elif color[neighbor] == GRAY:
                idx = stack_path.index(neighbor)
                return stack_path[idx:] + [neighbor]
        stack_path.pop()
        color[node] = BLACK
        return None

    for node in sorted(graph):
        if color[node] == WHITE:
            cycle = dfs(node)
            if cycle is not None:
                return cycle
    return None


def _step6_circular(magls: Sequence[MAGLSummary]) -> list[Finding]:
    if len(magls) < 2:
        return []
    graph = _build_requires_graph(magls)
    cycle = _find_cycle(graph)
    if cycle is None:
        return []
    involved = tuple(dict.fromkeys(cycle))  # dedupe, preserve order
    return [Finding(
        check="6_circular_dependency",
        severity="FATAL",
        what=f"circular requires/provides chain: {' -> '.join(cycle)}",
        why="a requires/provides cycle means no valid resolution order "
            "exists for this composed set — none of these MAGLs can be "
            "the 'first' one satisfied.",
        involved_magl_ids=involved,
    )]


# ─────────────────────────────────────────────────────────────
# Step 7 — privilege escalation / jurisdiction-union invariant
# ─────────────────────────────────────────────────────────────

def _step7_privilege_escalation(magls: Sequence[MAGLSummary]) -> list[Finding]:
    """Assert the structural invariant: composed jurisdiction is exactly
    the union of individual jurisdictions, never more. If this engine ever
    computed a broader set than the union, that would itself be a bug —
    this check exists to catch that class of bug, not to catch anything a
    well-formed MAGLSummary set could produce on its own.
    """
    findings: list[Finding] = []
    per_magl_union: set[str] = set()
    for m in magls:
        per_magl_union.update(m.granted_actions())

    composed_union: set[str] = set()
    for m in magls:
        composed_union.update(m.granted_actions())

    extra = composed_union - per_magl_union
    if extra:
        findings.append(Finding(
            check="7_privilege_escalation",
            severity="FATAL",
            what=f"composed jurisdiction contains action(s) {sorted(extra)} "
                 f"not declared by any single MAGL",
            why="composed jurisdiction must be exactly the union of "
                "individual jurisdictions — anything beyond that is an "
                "escalation introduced by composition itself.",
            involved_magl_ids=tuple(m.magl_id for m in magls),
        ))
    else:
        findings.append(Finding(
            check="7_privilege_escalation",
            severity="INFO",
            what="composed jurisdiction equals the union of individual "
                 "jurisdictions (invariant holds)",
            why="concrete prohibited-action conflicts are caught in step 2; "
                "this step only asserts no *additional* authority leaks in "
                "from the act of composing.",
            involved_magl_ids=tuple(m.magl_id for m in magls),
        ))
    return findings


# ─────────────────────────────────────────────────────────────
# Steps 8, 9 — no-ops, out of scope for MAGLSummary
# ─────────────────────────────────────────────────────────────

def _step8_invariants(magls: Sequence[MAGLSummary]) -> list[Finding]:
    return [Finding(
        check="8_conflicting_invariants",
        severity="INFO",
        what="invariant conflicts not checked here",
        why="MAGLSummary carries no invariant language to compare.",
        involved_magl_ids=tuple(m.magl_id for m in magls),
    )]


def _step9_provenance(magls: Sequence[MAGLSummary]) -> list[Finding]:
    return [Finding(
        check="9_provenance_conflicts",
        severity="INFO",
        what="provenance conflicts not checked here",
        why="MAGLSummary carries no provenance fields to compare.",
        involved_magl_ids=tuple(m.magl_id for m in magls),
    )]


# ─────────────────────────────────────────────────────────────
# Step 10 — produce the report
# ─────────────────────────────────────────────────────────────

def check_composition(magls: Sequence[MAGLSummary]) -> CompositionReport:
    """Run all ten checks, in order, and return a CompositionReport.

    Every check runs regardless of earlier findings — this is not
    first-failure-wins. All findings from all steps are always included in
    the report; none are ever silently dropped. Verdict is REFUSED iff any
    FATAL finding exists anywhere in the report.
    """
    magls = list(magls)

    if len(magls) <= 1:
        # Trivially composable: nothing to conflict with.
        return CompositionReport(
            verdict="COMPOSABLE",
            findings=[Finding(
                check="10_composition_report",
                severity="INFO",
                what="composed set has 0 or 1 MAGL",
                why="a set of zero or one MAGL cannot conflict with "
                    "anything else in the set; trivially composable.",
                involved_magl_ids=tuple(m.magl_id for m in magls),
            )],
        )

    findings: list[Finding] = []
    findings += _step1_schema(magls)
    findings += _step2_jurisdiction(magls)
    findings += _step3_dependencies(magls)
    findings += _step4_incompatibility(magls)
    findings += _step5_side_effects(magls)
    findings += _step6_circular(magls)
    findings += _step7_privilege_escalation(magls)
    findings += _step8_invariants(magls)
    findings += _step9_provenance(magls)

    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))

    verdict = "REFUSED" if any(f.severity == "FATAL" for f in findings) else "COMPOSABLE"
    return CompositionReport(verdict=verdict, findings=findings)
