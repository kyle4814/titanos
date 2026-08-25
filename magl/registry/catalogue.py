"""
MAGL registry — catalogue and relationship graph.

WHY THIS IS A SEPARATE MODULE FROM THE SCHEMA/VALIDATOR

This module does not parse or validate a MAGL document. It assumes another
component (magl/validators/) has already done that and handed over a
summary record (`MAGLEntry`) worth cataloguing. All this module knows about
a MAGL's internals is: it has a `magl_id` (string) and a `version`
(string). Everything else on `MAGLEntry` is metadata the catalogue needs
to search and cross-reference, not structure it interprets.

APPEND-ONLY, LIKE THE OTHER REGISTERS IN THIS CODEBASE

Mirrors kpm/contradictions/registry.py and firewall/quarantine.py: no
`delete`, `purge`, `clear`, `remove` or `drop` method exists anywhere in
this file, on either `MAGLCatalogue` or `MAGLRelationshipGraph`. A
specific (magl_id, version) pair, once registered, is immutable — an
update is a NEW version registered alongside it, never an edit of an
existing entry. Multiple versions of the same magl_id coexist in the
catalogue; nothing here decides which one is "current" except the caller.

ILLEGAL TRANSITIONS BY ABSENCE, NOT BY IF-CHECK

Mirrors firewall/quarantine.py's `TRANSITIONS` table: relationship types
are restricted to a fixed frozenset (`RELATIONSHIP_TYPES`), not validated
by a chain of `if` statements scattered through the code. An unknown
relationship type has no entry in that set, so `add_relationship` rejects
it structurally.

CYCLE DETECTION IS SCOPED TO ONE RELATIONSHIP TYPE AT A TIME

A DEPENDS_ON cycle is a real problem (A cannot be built until B, which
cannot be built until A). An EXTENDS or CONFLICTS_WITH "cycle" over the
same two nodes is not the same kind of defect — two MAGLs can quite
sensibly CONFLICT_WITH each other in both directions. Mixing relationship
types into one graph for cycle detection would flag structurally
meaningless cycles and drown the real ones, so `detect_cycles` always
operates over edges of exactly one relationship type.

Cycle detection uses full WHITE/GREY/BLACK-coloured DFS with no depth cap.
A depth-capped search silently misses cycles longer than the cap — that is
a documented anti-pattern in this codebase's history, not a stylistic
choice; it is not repeated here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable

from magl.composition.engine import MAGLSummary, check_composition

__all__ = [
    "MAGLEntry",
    "MAGLCatalogue",
    "CompositionRefusedAtRegistration",
    "RelationshipType",
    "Relationship",
    "MAGLRelationshipGraph",
    "transitive_dependencies",
]


class CompositionRefusedAtRegistration(Exception):
    """Raised by register_checked() when the incoming MAGL would conflict
    with something already catalogued. Carries the full CompositionReport
    so a caller sees every reason, not just that it failed."""

    def __init__(self, magl_id: str, version: str, report: Any):
        self.magl_id = magl_id
        self.version = version
        self.report = report
        fatal = [f.what for f in report.findings if f.severity == "FATAL"]
        super().__init__(
            f"registering '{magl_id}' v{version} refused — would conflict "
            f"with an already-catalogued MAGL: {'; '.join(fatal)}"
        )


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MAGLEntry:
    """Summary record for one registered MAGL version.

    This is deliberately NOT a parsed MAGL document. It is the set of
    fields a catalogue needs to search and cross-reference; the real
    document structure/validation lives in magl/schema/ and
    magl/validators/, owned elsewhere.
    """

    magl_id: str
    version: str
    name: str
    domain: tuple[str, ...]
    capability_type: tuple[str, ...]
    epistemic_status: str
    maturity: str
    dependencies_required: tuple[str, ...]
    dependencies_incompatible: tuple[str, ...]
    lifecycle_status: str
    license: str
    content_hash: str
    registered_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MAGLCatalogue:
    """Append-only catalogue of registered MAGL entries.

    No `delete`, `purge`, `clear`, `remove` or `drop` method exists on this
    class. A (magl_id, version) pair is immutable once registered — trying
    to register the same pair again raises `ValueError`. A *different*
    version of the same magl_id is expected and welcome: multiple versions
    of a MAGL coexist in the catalogue, and it is the caller's job (not
    this class's) to decide which one is "current" for a given purpose.
    """

    def __init__(self) -> None:
        # magl_id -> version -> entry, plus insertion order per magl_id.
        self._entries: dict[str, dict[str, MAGLEntry]] = {}
        self._order: dict[str, list[str]] = {}
        # magl_id -> version -> summary, ONLY populated by register_checked().
        # register() never touches this — a caller using the plain path has
        # no jurisdiction data to compose against, and this dict staying
        # empty for them is correct, not a gap.
        self._summaries: dict[str, dict[str, "MAGLSummary"]] = {}

    def register(self, entry: MAGLEntry) -> None:
        versions = self._entries.setdefault(entry.magl_id, {})
        if entry.version in versions:
            raise ValueError(
                f"MAGL '{entry.magl_id}' version '{entry.version}' is "
                f"already registered. A specific version is immutable once "
                f"catalogued — register a new version instead of "
                f"re-registering this one."
            )
        stamped = entry
        if not entry.registered_at:
            stamped = MAGLEntry(
                **{**entry.to_dict(),
                   "registered_at": datetime.now(timezone.utc).isoformat()},
            )
        versions[stamped.version] = stamped
        self._order.setdefault(entry.magl_id, []).append(stamped.version)

    def register_checked(self, entry: MAGLEntry, summary: MAGLSummary) -> None:
        """Register, but only after checking the incoming MAGL against
        every summary already catalogued via THIS method.

        WHY THIS IS A SEPARATE METHOD, NOT A CHANGE TO register()

        register() is a pure catalogue write — it has no jurisdiction data
        to reason about and must stay usable for callers who only have an
        MAGLEntry (e.g. re-cataloguing something already known-composable
        by other means). register_checked() is the connected version named
        as the next work cell in magl/BUILD_REPORT.md: "a MAGL that would
        conflict with an already-catalogued one can still be registered
        today, because these are two components with a proven seam, not
        yet a connected pipeline." This closes that gap without changing
        register()'s contract for existing callers.

        THE CHECK SET

        `summary` is checked via check_composition() against every summary
        previously registered through register_checked() (never against
        entries added via plain register(), which carry no summary). If
        the report's verdict is REFUSED, this raises
        CompositionRefusedAtRegistration BEFORE anything is written —
        catalogue state and the summary store are unchanged on refusal, so
        a caller retrying with a fixed MAGL sees a clean slate, not a
        partial write to clean up.
        """
        existing = [s for by_version in self._summaries.values()
                   for s in by_version.values()]
        report = check_composition([*existing, summary])
        if report.verdict == "REFUSED":
            raise CompositionRefusedAtRegistration(entry.magl_id, entry.version, report)

        self.register(entry)
        self._summaries.setdefault(entry.magl_id, {})[entry.version] = summary

    def get(self, magl_id: str, version: str | None = None) -> MAGLEntry | None:
        """Look up one entry.

        If `version` is given, return exactly that version (or None if not
        registered).

        If `version` is None, this is ambiguous UNLESS exactly one version
        of `magl_id` has ever been registered — in that single-version
        case, returning it is unambiguous and convenient. With two or more
        versions registered, this raises `ValueError` rather than
        guessing which one is "current" (this catalogue has no concept of
        a superseding version; that is a decision for a caller or a
        higher-level component, not for a lookup method to invent
        silently).
        """
        versions = self._entries.get(magl_id)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        if len(versions) == 1:
            return next(iter(versions.values()))
        raise ValueError(
            f"MAGL '{magl_id}' has {len(versions)} registered versions "
            f"({sorted(versions)}); specify `version` explicitly."
        )

    def all_versions(self, magl_id: str) -> tuple[MAGLEntry, ...]:
        versions = self._entries.get(magl_id)
        order = self._order.get(magl_id, [])
        if not versions:
            return ()
        return tuple(versions[v] for v in order)

    def search(
        self,
        *,
        domain: Iterable[str] | None = None,
        capability_type: Iterable[str] | None = None,
        epistemic_status: str | None = None,
        maturity: str | None = None,
        license: str | None = None,
        lifecycle_status: str | None = None,
    ) -> tuple[MAGLEntry, ...]:
        """AND-combine whichever filters are given; None = don't filter.

        `domain` and `capability_type` use list-intersection semantics:
        an entry matches if ANY of its values intersects ANY of the
        requested values. All other filters are exact-match on a scalar
        field.
        """
        domain_set = set(domain) if domain is not None else None
        cap_set = set(capability_type) if capability_type is not None else None

        results: list[MAGLEntry] = []
        for versions in self._entries.values():
            for entry in versions.values():
                if domain_set is not None and not (domain_set & set(entry.domain)):
                    continue
                if cap_set is not None and not (cap_set & set(entry.capability_type)):
                    continue
                if epistemic_status is not None and entry.epistemic_status != epistemic_status:
                    continue
                if maturity is not None and entry.maturity != maturity:
                    continue
                if license is not None and entry.license != license:
                    continue
                if lifecycle_status is not None and entry.lifecycle_status != lifecycle_status:
                    continue
                results.append(entry)
        return tuple(results)


# ---------------------------------------------------------------------------
# Relationship graph
# ---------------------------------------------------------------------------


class RelationshipType(str, Enum):
    DEPENDS_ON = "DEPENDS_ON"
    EXTENDS = "EXTENDS"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    IMPLEMENTS = "IMPLEMENTS"
    REPLACES = "REPLACES"
    REQUIRES_HUMAN_REVIEW_FOR = "REQUIRES_HUMAN_REVIEW_FOR"


RELATIONSHIP_TYPES: frozenset[str] = frozenset(t.value for t in RelationshipType)


@dataclass(frozen=True)
class Relationship:
    from_id: str
    relationship_type: str
    to_id: str
    reason: str = ""
    recorded_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MAGLRelationshipGraph:
    """Append-only, typed graph of relationships between MAGLs.

    Edges are stored as a flat append-only list — no `delete`, `purge`,
    `clear`, `remove` or `drop` method exists here either. A relationship,
    once recorded, is part of the audit trail even if later superseded by
    a new relationship (e.g. REPLACES); nothing is ever retracted.
    """

    def __init__(self) -> None:
        self._edges: list[Relationship] = []

    def add_relationship(
        self, from_id: str, relationship_type: str, to_id: str, reason: str = "",
    ) -> None:
        rt = relationship_type.value if isinstance(relationship_type, RelationshipType) else relationship_type
        if rt not in RELATIONSHIP_TYPES:
            raise ValueError(
                f"'{relationship_type}' is not a recognised relationship "
                f"type. Must be one of: {sorted(RELATIONSHIP_TYPES)}."
            )
        self._edges.append(Relationship(
            from_id=from_id,
            relationship_type=rt,
            to_id=to_id,
            reason=reason,
            recorded_at=datetime.now(timezone.utc).isoformat(),
        ))

    def relationships_from(self, magl_id: str) -> tuple[Relationship, ...]:
        return tuple(e for e in self._edges if e.from_id == magl_id)

    def relationships_to(self, magl_id: str) -> tuple[Relationship, ...]:
        return tuple(e for e in self._edges if e.to_id == magl_id)

    def _adjacency(self, relationship_type: str) -> dict[str, list[str]]:
        rt = relationship_type.value if isinstance(relationship_type, RelationshipType) else relationship_type
        adj: dict[str, list[str]] = {}
        for e in self._edges:
            if e.relationship_type != rt:
                continue
            adj.setdefault(e.from_id, []).append(e.to_id)
            adj.setdefault(e.to_id, [])  # ensure sink nodes are visited too
        return adj

    def detect_cycles(self, relationship_type: str = "DEPENDS_ON") -> list[list[str]]:
        """Find all cycles among edges of exactly `relationship_type`.

        WHITE/GREY/BLACK-coloured DFS, no depth cap — a depth-capped scan
        silently misses cycles longer than the cap, which is a documented
        anti-pattern in this codebase's history and is not repeated here.

        Returns the actual cycle paths found (each a list of node ids,
        starting and ending on the repeated node), not merely a boolean.
        A given cycle is reported once, from its lowest-indexed entry
        point in DFS traversal order.
        """
        adj = self._adjacency(relationship_type)

        WHITE, GREY, BLACK = 0, 1, 2
        color: dict[str, int] = {node: WHITE for node in adj}
        stack: list[str] = []
        stack_set: set[str] = set()
        cycles: list[list[str]] = []

        def dfs(node: str) -> None:
            color[node] = GREY
            stack.append(node)
            stack_set.add(node)
            for neighbour in adj.get(node, []):
                if color.get(neighbour, WHITE) == WHITE:
                    dfs(neighbour)
                elif neighbour in stack_set:
                    # Found a back-edge into the current DFS stack: the
                    # cycle is the stack slice from neighbour's first
                    # occurrence through to node, closed back on neighbour.
                    idx = stack.index(neighbour)
                    cycles.append(stack[idx:] + [neighbour])
            stack.pop()
            stack_set.discard(node)
            color[node] = BLACK

        for node in adj:
            if color[node] == WHITE:
                dfs(node)

        return cycles


def transitive_dependencies(graph: MAGLRelationshipGraph, magl_id: str) -> frozenset[str]:
    """Full closure of everything `magl_id` ultimately DEPENDS_ON.

    Walks DEPENDS_ON edges transitively (BFS/DFS over the whole reachable
    set) so a caller can always ask "everything this ultimately depends
    on", not just the one-hop neighbours — no hidden dependency chains.
    `magl_id` itself is not included in the result.
    """
    seen: set[str] = set()
    frontier = [magl_id]
    while frontier:
        current = frontier.pop()
        for edge in graph.relationships_from(current):
            if edge.relationship_type != RelationshipType.DEPENDS_ON.value:
                continue
            if edge.to_id not in seen:
                seen.add(edge.to_id)
                frontier.append(edge.to_id)
    return frozenset(seen)
