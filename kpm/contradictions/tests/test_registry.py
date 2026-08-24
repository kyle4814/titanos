import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from kpm.contradictions.registry import ContradictionRegistry


class TestNoDeleteSurface(unittest.TestCase):
    def test_no_delete_surface(self):
        reg = ContradictionRegistry()
        for name in ("delete", "purge", "clear", "remove"):
            self.assertFalse(hasattr(reg, name),
                              f"ContradictionRegistry must not expose '{name}'")


class TestRecord(unittest.TestCase):
    def test_single_involved_id_is_not_a_contradiction(self):
        reg = ContradictionRegistry()
        with self.assertRaises(ValueError):
            reg.record("c-1", "claim vs itself", ["bp-1"])

    def test_zero_involved_ids_is_not_a_contradiction(self):
        reg = ContradictionRegistry()
        with self.assertRaises(ValueError):
            reg.record("c-2", "nothing involved", [])

    def test_empty_description_refused(self):
        reg = ContradictionRegistry()
        with self.assertRaises(ValueError):
            reg.record("c-3", "   ", ["bp-1", "bp-2"])

    def test_valid_record(self):
        reg = ContradictionRegistry()
        rec = reg.record("c-4", "bp-1 says X, bp-2 says not-X", ["bp-1", "bp-2"])
        self.assertEqual(rec.status, "OPEN")
        self.assertEqual(rec.involved_ids, ("bp-1", "bp-2"))

    def test_duplicate_id_refused(self):
        reg = ContradictionRegistry()
        reg.record("c-5", "first", ["bp-1", "bp-2"])
        with self.assertRaises(ValueError):
            reg.record("c-5", "dup", ["bp-3", "bp-4"])


class TestResolve(unittest.TestCase):
    def test_resolve_without_evidence_refused(self):
        reg = ContradictionRegistry()
        reg.record("c-6", "bp-1 vs bp-2", ["bp-1", "bp-2"])
        with self.assertRaises(ValueError):
            reg.resolve("c-6", "we think bp-1 is right", evidence_refs=(),
                        resolved_by="carol")

    def test_resolve_with_evidence_succeeds(self):
        reg = ContradictionRegistry()
        reg.record("c-7", "bp-1 vs bp-2", ["bp-1", "bp-2"])
        rec = reg.resolve("c-7", "bp-2 cites a retracted source",
                           evidence_refs=("doc://retraction-notice",),
                           resolved_by="carol")
        self.assertEqual(rec.status, "RESOLVED")
        self.assertEqual(rec.resolution["resolved_by"], "carol")
        self.assertEqual(rec.resolution["evidence_refs"], ("doc://retraction-notice",))

    def test_wont_fix_requires_reason_and_resolver_but_not_evidence(self):
        reg = ContradictionRegistry()
        reg.record("c-8", "bp-1 vs bp-2", ["bp-1", "bp-2"])
        rec = reg.resolve("c-8", "low priority, deferred", evidence_refs=(),
                           resolved_by="carol", final_status="WONT_FIX")
        self.assertEqual(rec.status, "WONT_FIX")

    def test_wont_fix_without_reason_refused(self):
        reg = ContradictionRegistry()
        reg.record("c-9", "bp-1 vs bp-2", ["bp-1", "bp-2"])
        with self.assertRaises(ValueError):
            reg.resolve("c-9", "  ", evidence_refs=(), resolved_by="carol",
                        final_status="WONT_FIX")

    def test_resolve_without_resolved_by_refused(self):
        reg = ContradictionRegistry()
        reg.record("c-10", "bp-1 vs bp-2", ["bp-1", "bp-2"])
        with self.assertRaises(ValueError):
            reg.resolve("c-10", "evidence found", evidence_refs=("doc://x",),
                        resolved_by="")

    def test_involved_ids_survive_resolution(self):
        reg = ContradictionRegistry()
        reg.record("c-11", "bp-1 vs bp-2 vs bp-3", ["bp-1", "bp-2", "bp-3"])
        rec = reg.resolve("c-11", "bp-3 was the error",
                           evidence_refs=("doc://audit",), resolved_by="carol")
        self.assertEqual(rec.involved_ids, ("bp-1", "bp-2", "bp-3"))

    def test_cannot_resolve_to_open(self):
        reg = ContradictionRegistry()
        reg.record("c-12", "bp-1 vs bp-2", ["bp-1", "bp-2"])
        with self.assertRaises(ValueError):
            reg.resolve("c-12", "reset it", evidence_refs=("doc://x",),
                        resolved_by="carol", final_status="OPEN")

    def test_resolve_unknown_contradiction_raises_keyerror(self):
        reg = ContradictionRegistry()
        with self.assertRaises(KeyError):
            reg.resolve("nope", "reason", evidence_refs=("doc://x",),
                        resolved_by="carol")


class TestOpenContradictions(unittest.TestCase):
    def test_open_contradictions_filters_correctly(self):
        reg = ContradictionRegistry()
        reg.record("c-13", "still open", ["bp-1", "bp-2"])
        reg.record("c-14", "will resolve", ["bp-3", "bp-4"])
        reg.resolve("c-14", "resolved with evidence", evidence_refs=("doc://x",),
                    resolved_by="carol")
        open_ids = {r.contradiction_id for r in reg.open_contradictions()}
        self.assertEqual(open_ids, {"c-13"})


class TestAppendOnlyHistory(unittest.TestCase):
    def test_history_records_recorded_and_resolved_events(self):
        reg = ContradictionRegistry()
        reg.record("c-15", "bp-1 vs bp-2", ["bp-1", "bp-2"])
        reg.resolve("c-15", "found evidence", evidence_refs=("doc://x",),
                    resolved_by="carol")
        rec = reg.get("c-15")
        events = [h["event"] for h in rec.history]
        self.assertEqual(events, ["RECORDED", "RESOLVED"])


if __name__ == "__main__":
    unittest.main()
