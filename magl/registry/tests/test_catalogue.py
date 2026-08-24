"""Tests for magl/registry/catalogue.py."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from magl.registry.catalogue import (  # noqa: E402
    MAGLEntry,
    MAGLCatalogue,
    MAGLRelationshipGraph,
    RelationshipType,
    transitive_dependencies,
)


def make_entry(magl_id="magl.example", version="1.0.0", **overrides) -> MAGLEntry:
    fields = dict(
        magl_id=magl_id,
        version=version,
        name="Example MAGL",
        domain=("finance", "risk"),
        capability_type=("analysis",),
        epistemic_status="VERIFIED",
        maturity="STABLE",
        dependencies_required=(),
        dependencies_incompatible=(),
        lifecycle_status="ACTIVE",
        license="MIT",
        content_hash="sha256:deadbeef",
    )
    fields.update(overrides)
    return MAGLEntry(**fields)


class TestRegisterAndGet(unittest.TestCase):
    def test_register_then_get_exact_version(self):
        cat = MAGLCatalogue()
        entry = make_entry()
        cat.register(entry)
        got = cat.get("magl.example", version="1.0.0")
        self.assertEqual(got.magl_id, "magl.example")
        self.assertEqual(got.version, "1.0.0")

    def test_get_unknown_id_returns_none(self):
        cat = MAGLCatalogue()
        self.assertIsNone(cat.get("nope"))

    def test_get_unknown_version_returns_none(self):
        cat = MAGLCatalogue()
        cat.register(make_entry())
        self.assertIsNone(cat.get("magl.example", version="9.9.9"))

    def test_reregister_same_id_and_version_raises(self):
        cat = MAGLCatalogue()
        cat.register(make_entry())
        with self.assertRaises(ValueError):
            cat.register(make_entry())

    def test_different_version_of_same_id_is_fine(self):
        cat = MAGLCatalogue()
        cat.register(make_entry(version="1.0.0"))
        cat.register(make_entry(version="2.0.0"))
        self.assertEqual(len(cat.all_versions("magl.example")), 2)

    def test_get_with_no_version_single_version_is_unambiguous(self):
        cat = MAGLCatalogue()
        cat.register(make_entry(version="1.0.0"))
        got = cat.get("magl.example")
        self.assertEqual(got.version, "1.0.0")

    def test_get_with_no_version_multiple_versions_raises(self):
        cat = MAGLCatalogue()
        cat.register(make_entry(version="1.0.0"))
        cat.register(make_entry(version="2.0.0"))
        with self.assertRaises(ValueError):
            cat.get("magl.example")

    def test_all_versions_preserves_registration_order(self):
        cat = MAGLCatalogue()
        cat.register(make_entry(version="1.0.0"))
        cat.register(make_entry(version="1.1.0"))
        cat.register(make_entry(version="2.0.0"))
        versions = [e.version for e in cat.all_versions("magl.example")]
        self.assertEqual(versions, ["1.0.0", "1.1.0", "2.0.0"])

    def test_all_versions_unknown_id_is_empty_tuple(self):
        cat = MAGLCatalogue()
        self.assertEqual(cat.all_versions("nope"), ())

    def test_registered_at_is_stamped_when_not_given(self):
        cat = MAGLCatalogue()
        cat.register(make_entry())
        got = cat.get("magl.example", version="1.0.0")
        self.assertNotEqual(got.registered_at, "")


class TestAppendOnlyDiscipline(unittest.TestCase):
    """Mirrors kpm/contradictions/registry.py and firewall/quarantine.py:
    no delete surface exists on the catalogue or the relationship graph."""

    def test_catalogue_has_no_delete_surface(self):
        cat = MAGLCatalogue()
        for method in ("delete", "purge", "clear", "remove", "drop"):
            self.assertFalse(hasattr(cat, method), f"MAGLCatalogue must not expose '{method}'")

    def test_relationship_graph_has_no_delete_surface(self):
        graph = MAGLRelationshipGraph()
        for method in ("delete", "purge", "clear", "remove", "drop"):
            self.assertFalse(hasattr(graph, method), f"MAGLRelationshipGraph must not expose '{method}'")


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.cat = MAGLCatalogue()
        self.cat.register(make_entry(
            magl_id="magl.a", domain=("finance",), capability_type=("analysis",),
            epistemic_status="VERIFIED", maturity="STABLE", license="MIT",
            lifecycle_status="ACTIVE",
        ))
        self.cat.register(make_entry(
            magl_id="magl.b", domain=("healthcare", "risk"), capability_type=("generation",),
            epistemic_status="UNVERIFIED", maturity="EXPERIMENTAL", license="Apache-2.0",
            lifecycle_status="ACTIVE",
        ))
        self.cat.register(make_entry(
            magl_id="magl.c", domain=("finance", "risk"), capability_type=("analysis", "generation"),
            epistemic_status="VERIFIED", maturity="STABLE", license="MIT",
            lifecycle_status="DEPRECATED",
        ))

    def test_search_no_filters_returns_all(self):
        self.assertEqual(len(self.cat.search()), 3)

    def test_search_single_filter_domain(self):
        results = self.cat.search(domain=("healthcare",))
        self.assertEqual({e.magl_id for e in results}, {"magl.b"})

    def test_search_single_filter_domain_intersection_semantics(self):
        # "risk" is present on magl.b and magl.c only.
        results = self.cat.search(domain=("risk",))
        self.assertEqual({e.magl_id for e in results}, {"magl.b", "magl.c"})

    def test_search_single_filter_capability_type(self):
        results = self.cat.search(capability_type=("generation",))
        self.assertEqual({e.magl_id for e in results}, {"magl.b", "magl.c"})

    def test_search_single_filter_scalar_field(self):
        results = self.cat.search(lifecycle_status="DEPRECATED")
        self.assertEqual({e.magl_id for e in results}, {"magl.c"})

    def test_search_combined_filters_and_semantics(self):
        results = self.cat.search(domain=("finance",), maturity="STABLE", license="MIT")
        self.assertEqual({e.magl_id for e in results}, {"magl.a", "magl.c"})

    def test_search_combined_filters_narrows_to_none(self):
        results = self.cat.search(domain=("finance",), epistemic_status="UNVERIFIED")
        self.assertEqual(results, ())

    def test_search_domain_or_capability_no_match_returns_empty(self):
        results = self.cat.search(domain=("nonexistent-domain",))
        self.assertEqual(results, ())


class TestRelationshipGraph(unittest.TestCase):
    def test_add_relationship_valid_type(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("magl.a", "DEPENDS_ON", "magl.b", reason="needs core primitives")
        edges = graph.relationships_from("magl.a")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].relationship_type, "DEPENDS_ON")
        self.assertEqual(edges[0].to_id, "magl.b")

    def test_add_relationship_accepts_enum_member(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("magl.a", RelationshipType.EXTENDS, "magl.b")
        self.assertEqual(graph.relationships_from("magl.a")[0].relationship_type, "EXTENDS")

    def test_add_relationship_invalid_type_raises(self):
        graph = MAGLRelationshipGraph()
        with self.assertRaises(ValueError):
            graph.add_relationship("magl.a", "FRIENDS_WITH", "magl.b")

    def test_relationships_from_and_to(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("magl.a", "DEPENDS_ON", "magl.b")
        graph.add_relationship("magl.c", "DEPENDS_ON", "magl.b")
        self.assertEqual(len(graph.relationships_from("magl.a")), 1)
        self.assertEqual(len(graph.relationships_to("magl.b")), 2)

    def test_all_six_relationship_types_accepted(self):
        graph = MAGLRelationshipGraph()
        for rt in RelationshipType:
            graph.add_relationship("x", rt, "y")
        self.assertEqual(len(graph.relationships_from("x")), 6)


class TestCycleDetection(unittest.TestCase):
    def test_three_node_depends_on_cycle_detected(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "DEPENDS_ON", "B")
        graph.add_relationship("B", "DEPENDS_ON", "C")
        graph.add_relationship("C", "DEPENDS_ON", "A")
        cycles = graph.detect_cycles("DEPENDS_ON")
        self.assertEqual(len(cycles), 1)
        cycle = cycles[0]
        self.assertEqual({"A", "B", "C"}, set(cycle))
        # First and last node of the reported path must be the same (closed loop).
        self.assertEqual(cycle[0], cycle[-1])

    def test_conflicts_with_edge_not_flagged_when_scoped_to_depends_on(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "CONFLICTS_WITH", "B")
        graph.add_relationship("B", "CONFLICTS_WITH", "A")
        cycles = graph.detect_cycles("DEPENDS_ON")
        self.assertEqual(cycles, [])

    def test_no_cycle_in_acyclic_depends_on_graph(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "DEPENDS_ON", "B")
        graph.add_relationship("B", "DEPENDS_ON", "C")
        self.assertEqual(graph.detect_cycles("DEPENDS_ON"), [])

    def test_mixed_relationship_types_only_scoped_type_considered(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "DEPENDS_ON", "B")
        graph.add_relationship("B", "EXTENDS", "A")  # would close a cycle if types were mixed
        self.assertEqual(graph.detect_cycles("DEPENDS_ON"), [])
        self.assertEqual(graph.detect_cycles("EXTENDS"), [])


class TestTransitiveDependencies(unittest.TestCase):
    def test_three_hop_chain_full_closure(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "DEPENDS_ON", "B")
        graph.add_relationship("B", "DEPENDS_ON", "C")
        graph.add_relationship("C", "DEPENDS_ON", "D")
        self.assertEqual(transitive_dependencies(graph, "A"), frozenset({"B", "C", "D"}))

    def test_leaf_node_has_empty_closure(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "DEPENDS_ON", "B")
        self.assertEqual(transitive_dependencies(graph, "B"), frozenset())

    def test_diamond_dependency_deduplicated(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "DEPENDS_ON", "B")
        graph.add_relationship("A", "DEPENDS_ON", "C")
        graph.add_relationship("B", "DEPENDS_ON", "D")
        graph.add_relationship("C", "DEPENDS_ON", "D")
        self.assertEqual(transitive_dependencies(graph, "A"), frozenset({"B", "C", "D"}))

    def test_non_depends_on_edges_ignored(self):
        graph = MAGLRelationshipGraph()
        graph.add_relationship("A", "DEPENDS_ON", "B")
        graph.add_relationship("B", "EXTENDS", "C")
        self.assertEqual(transitive_dependencies(graph, "A"), frozenset({"B"}))


if __name__ == "__main__":
    unittest.main()
