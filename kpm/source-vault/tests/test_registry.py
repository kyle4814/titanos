"""
Tests for kpm/source-vault/registry.py.

NOTE ON IMPORT PATH: the parent directory is named "source-vault" (hyphen),
which is not a legal Python package identifier, so `registry` cannot be
reached via a dotted `kpm.source_vault...` import. This file adds the
source-vault directory itself to sys.path and imports `registry` directly
by module name — the standard workaround for a hyphenated directory that
still needs to hold real, unittest-discoverable tests. Run with either:

    python3 kpm/source-vault/tests/test_registry.py -v
    python3 -m unittest discover -s kpm/source-vault/tests -p 'test_*.py' -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_SOURCE_VAULT_DIR = Path(__file__).resolve().parent.parent
if str(_SOURCE_VAULT_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_VAULT_DIR))

import registry as reg  # noqa: E402


class SourceRegistryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.archive_dir = Path(self._tmpdir.name) / "archive"
        self.registry_path = Path(self._tmpdir.name) / "registry.jsonl"
        self.reg = reg.SourceRegistry(
            archive_dir=self.archive_dir, registry_path=self.registry_path
        )

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- basic ingestion ----------------------------------------------------

    def test_ingest_returns_source_record_with_all_required_fields(self):
        rec = self.reg.ingest_source(
            b"hello world", "text", "unit-test://inline", "kyle"
        )
        required = {
            "artifact_id", "content_hash", "ingestion_timestamp",
            "source_type", "source_location", "author_or_origin",
            "license_status", "confidentiality_status", "provenance_status",
            "integrity_status", "original_content_reference",
            "immutable_archive_reference",
        }
        d = rec.to_dict()
        for f in required:
            self.assertIn(f, d, f"missing required field {f!r}")
        self.assertTrue(rec.content_hash.startswith("sha256:"))
        self.assertEqual(len(rec.content_hash), len("sha256:") + 64)

    def test_ingest_from_path(self):
        p = Path(self._tmpdir.name) / "source.txt"
        p.write_bytes(b"content from a real file")
        rec = self.reg.ingest_source(p, "text", str(p), "kyle")
        self.assertEqual(rec.original_content_reference, str(p))
        archived = self.archive_dir.parent / rec.immutable_archive_reference
        self.assertTrue(archived.exists())
        self.assertEqual(archived.read_bytes(), b"content from a real file")

    # -- source_type enum -----------------------------------------------------

    def test_invalid_source_type_is_structured_rejection_not_crash(self):
        with self.assertRaises(reg.InvalidSourceType):
            self.reg.ingest_source(b"data", "not_a_real_type", "loc", "kyle")
        self.assertIsInstance(reg.InvalidSourceType(), reg.SourceVaultError)

    def test_all_declared_source_types_are_accepted(self):
        for st in sorted(reg.SOURCE_TYPES):
            rec = self.reg.ingest_source(
                f"content for {st}".encode(), st, "loc", "kyle"
            )
            self.assertEqual(rec.source_type, st)

    # -- get_source -----------------------------------------------------------

    def test_get_source_roundtrip(self):
        rec = self.reg.ingest_source(b"abc", "note", "loc", "kyle")
        fetched = self.reg.get_source(rec.artifact_id)
        self.assertEqual(fetched, rec)

    def test_get_source_unknown_id_returns_none(self):
        self.assertIsNone(self.reg.get_source("SRC-does-not-exist"))

    # -- verify_integrity -----------------------------------------------------

    def test_verify_integrity_true_for_untouched_archive(self):
        rec = self.reg.ingest_source(b"integral bytes", "note", "loc", "kyle")
        self.assertTrue(self.reg.verify_integrity(rec.artifact_id))
        self.assertEqual(rec.integrity_status, "VERIFIED")

    def test_verify_integrity_false_and_recorded_on_tamper(self):
        rec = self.reg.ingest_source(b"original bytes", "note", "loc", "kyle")
        archived = self.archive_dir.parent / rec.immutable_archive_reference
        # Simulate corruption/tamper directly on disk.
        archived.write_bytes(b"TAMPERED")
        result = self.reg.verify_integrity(rec.artifact_id)
        self.assertFalse(result)
        self.assertEqual(rec.integrity_status, "PROVENANCE_FAILURE")
        self.assertTrue(rec.integrity_history)
        self.assertEqual(rec.integrity_history[-1]["result"], "PROVENANCE_FAILURE")

    def test_verify_integrity_false_when_blob_missing(self):
        rec = self.reg.ingest_source(b"will be deleted", "note", "loc", "kyle")
        archived = self.archive_dir.parent / rec.immutable_archive_reference
        archived.unlink()
        self.assertFalse(self.reg.verify_integrity(rec.artifact_id))
        self.assertEqual(rec.integrity_status, "PROVENANCE_FAILURE")

    def test_verify_integrity_unknown_id_raises(self):
        with self.assertRaises(KeyError):
            self.reg.verify_integrity("SRC-nope")

    # -- no update/delete surface (house style: hasattr, not "refused") -----

    def test_no_mutating_methods_exist_on_registry(self):
        for forbidden in ("update", "delete", "overwrite", "purge", "clear",
                           "remove", "edit", "rewrite"):
            self.assertFalse(
                hasattr(self.reg, forbidden),
                f"SourceRegistry must not expose a '{forbidden}' method",
            )

    def test_no_mutating_methods_exist_on_record(self):
        rec = self.reg.ingest_source(b"x", "note", "loc", "kyle")
        for forbidden in ("update", "delete", "overwrite", "purge", "clear",
                           "remove"):
            self.assertFalse(
                hasattr(rec, forbidden),
                f"SourceRecord must not expose a '{forbidden}' method",
            )

    # -- re-ingestion of identical bytes: two records, one blob -------------

    def test_same_bytes_different_calls_produce_two_records(self):
        rec1 = self.reg.ingest_source(b"shared bytes", "text", "loc-a", "kyle")
        rec2 = self.reg.ingest_source(b"shared bytes", "text", "loc-b", "someone-else")
        self.assertNotEqual(rec1.artifact_id, rec2.artifact_id)
        self.assertEqual(rec1.content_hash, rec2.content_hash)
        self.assertEqual(len(self.reg.all_records()), 2)
        # Both point at the identical archive location.
        self.assertEqual(
            rec1.immutable_archive_reference, rec2.immutable_archive_reference
        )

    def test_reingest_same_bytes_does_not_touch_archived_file(self):
        rec1 = self.reg.ingest_source(b"do not touch me", "text", "loc", "kyle")
        archived = self.archive_dir.parent / rec1.immutable_archive_reference
        before_mtime = archived.stat().st_mtime_ns
        before_content = archived.read_bytes()

        rec2 = self.reg.ingest_source(b"do not touch me", "text", "loc2", "someone-else")

        after_mtime = archived.stat().st_mtime_ns
        after_content = archived.read_bytes()
        self.assertEqual(before_mtime, after_mtime,
                          "archived blob mtime changed on re-ingest of same bytes")
        self.assertEqual(before_content, after_content)
        self.assertNotEqual(rec1.artifact_id, rec2.artifact_id)

        # Only one blob file exists in the archive directory.
        blobs = list(self.archive_dir.glob("*.blob"))
        self.assertEqual(len(blobs), 1)

    # -- persistence across a fresh SourceRegistry instance -------------------

    def test_records_survive_reload_from_ledger(self):
        rec = self.reg.ingest_source(b"persisted", "note", "loc", "kyle")
        reloaded = reg.SourceRegistry(
            archive_dir=self.archive_dir, registry_path=self.registry_path
        )
        fetched = reloaded.get_source(rec.artifact_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.content_hash, rec.content_hash)

    # -- unrecognised input type is a structured rejection -------------------

    def test_ingest_wrong_type_raises_structured_error(self):
        with self.assertRaises(reg.SourceVaultError):
            self.reg.ingest_source(12345, "note", "loc", "kyle")

    # -- get_by_hash / get_content (added to close the RPA derivation-binding
    # finding: authorization needs to recover exact bytes by content hash,
    # not just look up a record by artifact_id) ------------------------------

    def test_get_by_hash_resolves_to_the_ingested_record(self):
        rec = self.reg.ingest_source(b"pinned content", "note", "loc", "kyle")
        matches = self.reg.get_by_hash(rec.content_hash)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].artifact_id, rec.artifact_id)

    def test_get_by_hash_returns_all_records_sharing_identical_bytes(self):
        rec1 = self.reg.ingest_source(b"same bytes", "note", "loc-a", "alice")
        rec2 = self.reg.ingest_source(b"same bytes", "note", "loc-b", "bob")
        self.assertNotEqual(rec1.artifact_id, rec2.artifact_id)
        self.assertEqual(rec1.content_hash, rec2.content_hash)
        matches = self.reg.get_by_hash(rec1.content_hash)
        self.assertEqual({m.artifact_id for m in matches},
                         {rec1.artifact_id, rec2.artifact_id})

    def test_get_by_hash_unknown_hash_returns_empty_tuple(self):
        self.assertEqual(self.reg.get_by_hash("sha256:doesnotexist"), ())

    def test_get_content_recovers_exact_bytes(self):
        rec = self.reg.ingest_source(b"exact bytes to recover", "note", "loc", "kyle")
        self.assertEqual(self.reg.get_content(rec.artifact_id), b"exact bytes to recover")

    def test_get_content_unknown_artifact_id_raises_keyerror(self):
        with self.assertRaises(KeyError):
            self.reg.get_content("SRC-nonexistent")

    def test_get_content_missing_blob_raises_no_such_content_hash(self):
        rec = self.reg.ingest_source(b"will be deleted", "note", "loc", "kyle")
        archived_path = self.archive_dir / f"{rec.content_hash.split(':', 1)[1]}.blob"
        archived_path.unlink()
        with self.assertRaises(reg.NoSuchContentHash):
            self.reg.get_content(rec.artifact_id)


if __name__ == "__main__":
    unittest.main()
