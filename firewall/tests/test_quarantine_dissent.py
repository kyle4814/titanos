"""
Adversarial tests for quarantine (§15, §16, §19) and dissent (§8, §9).

The two failure modes under test are mirror images:
  - too permissive: contaminated material reaches execution
  - too aggressive: disagreement gets filtered as contamination
Both must fail.
"""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from firewall.quarantine import (  # noqa: E402
    QuarantineStore, IllegalTransition, TRANSITIONS, can_transition,
)
from firewall.dissent import DissentRegister, Position  # noqa: E402


class TestNoPathToExecution(unittest.TestCase):
    """§15 — no automatic CONTAMINATED -> AUTHORIZED transition."""

    def test_no_edge_contaminated_to_authorized(self):
        """Enforced by the ABSENCE of an edge, not by a runtime check."""
        self.assertNotIn("AUTHORIZED", TRANSITIONS["CONTAMINATED"])
        self.assertFalse(can_transition("CONTAMINATED", "AUTHORIZED"))

    def test_no_edge_quarantined_to_authorized(self):
        self.assertNotIn("AUTHORIZED", TRANSITIONS["QUARANTINED"])
        self.assertFalse(can_transition("QUARANTINED", "AUTHORIZED"))

    def test_only_verified_reaches_authorized(self):
        reaching = [s for s, t in TRANSITIONS.items() if "AUTHORIZED" in t]
        self.assertEqual(reaching, ["VERIFIED"],
                         "AUTHORIZED must be reachable only from VERIFIED")

    def test_illegal_transition_raises_loudly(self):
        s = QuarantineStore()
        s.quarantine(artifact_id="a1", content="x", reason="unverified provenance")
        with self.assertRaises(IllegalTransition):
            s.transition("a1", "AUTHORIZED", reason="looks fine to me")


class TestPreservationNotDeletion(unittest.TestCase):
    """§16, §19 — a false positive must stay reviewable."""

    def test_quarantine_preserves_content_hash_and_reason(self):
        s = QuarantineStore()
        rec = s.quarantine(artifact_id="a1", content="original text",
                           reason="provenance unverifiable",
                           provenance={"source": "external"})
        self.assertEqual(rec.preserved_content, "original text")
        self.assertTrue(rec.content_hash.startswith("sha256:"))
        self.assertEqual(rec.reason, "provenance unverifiable")
        self.assertEqual(rec.provenance["source"], "external")

    def test_store_exposes_no_delete_surface(self):
        s = QuarantineStore()
        for method in ("delete", "purge", "clear", "remove", "drop"):
            self.assertFalse(hasattr(s, method),
                             f"append-only store must not expose {method}()")

    def test_unexplained_quarantine_is_refused(self):
        """An unreviewable hold is censorship, not safety."""
        s = QuarantineStore()
        with self.assertRaises(ValueError):
            s.quarantine(artifact_id="a1", content="x", reason="   ")

    def test_release_requires_a_human(self):
        s = QuarantineStore()
        s.quarantine(artifact_id="a1", content="x", reason="needs review")
        with self.assertRaises(IllegalTransition):
            s.transition("a1", "VERIFIED", reason="rechecked")  # no reviewed_by
        rec = s.transition("a1", "VERIFIED", reason="rechecked",
                           reviewed_by="kyle")
        self.assertEqual(rec.state, "VERIFIED")
        self.assertIn("REVIEWED_BY:kyle", rec.human_review_status)

    def test_history_is_append_only_and_complete(self):
        s = QuarantineStore()
        s.quarantine(artifact_id="a1", content="x", reason="r1")
        s.transition("a1", "VERIFIED", reason="r2", reviewed_by="kyle")
        s.transition("a1", "AUTHORIZED", reason="r3")
        rec = s.get("a1")
        self.assertEqual(len(rec.history), 3)
        self.assertEqual([h["to"] for h in rec.history],
                         ["QUARANTINED", "VERIFIED", "AUTHORIZED"])

    def test_pending_review_is_visible(self):
        s = QuarantineStore()
        s.quarantine(artifact_id="a1", content="x", reason="held")
        self.assertEqual(len(s.pending_review()), 1)


class TestDissentIsNotContamination(unittest.TestCase):
    """§8, §9 — the filter guards process, not opinion."""

    def test_disagreement_records_as_DISPUTED_not_FALSE(self):
        r = DissentRegister()
        rec = r.record("d1", "scoring weights are calibrated", [
            Position("p1", "weights are sound", "agent-a", root_origin="O1"),
            Position("p2", "weights are uncalibrated guesses", "kyle",
                     root_origin="O2", is_minority=True),
        ])
        self.assertEqual(rec.status, "DISPUTED")

    def test_majority_cannot_resolve_without_evidence(self):
        """The safeguard: a vote is not a finding."""
        r = DissentRegister()
        r.record("d1", "subject", [
            Position(f"p{i}", "X", f"agent-{i}", root_origin=f"O{i}")
            for i in range(9)
        ] + [Position("p9", "not X", "dissenter", root_origin="O9",
                      is_minority=True)])
        with self.assertRaises(ValueError):
            r.resolve("d1", status="SUPPORTED", evidence_refs=[],
                      reviewed_by="kyle")

    def test_shared_ancestry_cannot_adjudicate_itself(self):
        r = DissentRegister()
        r.record("d1", "subject", [
            Position("p1", "X", "agent-1", root_origin="SPEC-A"),
            Position("p2", "X", "agent-2", root_origin="SPEC-A"),
        ])
        with self.assertRaises(ValueError):
            r.resolve("d1", status="SUPPORTED", evidence_refs=["ev-1"],
                      reviewed_by="kyle")

    def test_resolution_preserves_the_losing_position(self):
        r = DissentRegister()
        r.record("d1", "subject", [
            Position("p1", "X", "a", root_origin="O1"),
            Position("p2", "not X", "b", root_origin="O2", is_minority=True),
        ])
        rec = r.resolve("d1", status="SUPPORTED",
                        evidence_refs=["ev-1", "ev-2"], reviewed_by="kyle")
        self.assertEqual(rec.status, "SUPPORTED")
        self.assertEqual(len(rec.positions), 2, "losing position must survive")
        self.assertTrue(any(p.is_minority for p in rec.positions))

    def test_minority_positions_survive_resolution(self):
        r = DissentRegister()
        r.record("d1", "s", [
            Position("p1", "X", "a", root_origin="O1"),
            Position("p2", "not X", "b", root_origin="O2", is_minority=True),
        ])
        r.resolve("d1", status="SUPPORTED", evidence_refs=["ev"],
                  reviewed_by="kyle")
        self.assertEqual(len(r.minority_positions()), 1,
                         "a system that forgets why it might be wrong is capturable")

    def test_register_exposes_no_delete_surface(self):
        r = DissentRegister()
        for m in ("delete", "purge", "clear", "remove"):
            self.assertFalse(hasattr(r, m))

    def test_single_position_is_not_a_dispute(self):
        r = DissentRegister()
        with self.assertRaises(ValueError):
            r.record("d1", "s", [Position("p1", "X", "a")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
