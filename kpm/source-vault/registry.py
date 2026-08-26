"""
Immutable Source Registry (KPM Phase 2 — Knowledge Production Machine).

WHAT THIS FILE ANSWERS, AND ONLY THIS

    "What did we actually receive, exactly as we received it, and can we
     still prove that later?"

It does NOT answer:
    - "Is this source true, licensed, or safe to use?" (that's provenance/
      dissent/quarantine layers downstream of this one)
    - "What does this source mean?" (that's distillation, not ingestion)

THE SINGLE HARD RULE THIS FILE ENFORCES ON ITSELF

Once bytes are archived under their content hash, nothing in this module
ever opens that archived file for writing again. Ingesting the same bytes
a second time (under a new artifact_id, from a new context) must reuse the
existing archive entry byte-for-byte — never re-copy, never touch mtime,
never overwrite. The archive is the ground truth; the registry is a set of
FACTS ABOUT INGESTION EVENTS pointing at that ground truth. Two ingestion
events over identical bytes are two different facts (different actors,
times, or claimed origins might attach to each) and therefore produce two
SourceRecords — deduplicating them into one would silently discard which
event actually happened.

ARCHIVE LAYOUT (documented here because there is no other spec for it)

    kpm/source-vault/archive/<sha256-hex>.blob

    Content-addressed, flat, one file per distinct content hash. The
    "sha256:" prefix used inside SourceRecord.content_hash is stripped for
    the filename (colons are not a safe filename character on all
    filesystems); the archive filename is always the bare 64-hex-char
    digest plus ".blob".

REGISTRY BACKING STORE (documented here — this was a judgment call)

    In-memory dict, keyed by artifact_id, mirrored to an append-only JSONL
    file (kpm/source-vault/registry.jsonl by default) — one JSON object per
    line, one line per ingestion event, appended and never rewritten. This
    follows the same shape as firewall/quarantine.py's QuarantineStore: the
    in-memory dict is the fast-path source of truth for a running process,
    the JSONL file is what makes ingestion survive a restart and gives an
    auditor a append-only paper trail without needing a database. On
    construction, existing lines are replayed into memory; nothing is ever
    deleted from or rewritten in that file by this module.

FAIL-CLOSED

Any unforeseen exception during ingest_source is never allowed to produce
a SourceRecord that silently claims success. Known-bad inputs (unrecognised
source_type) raise a structured InvalidSourceType — a caught, documented
exception, not a crash and not a bare False.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "SOURCE_TYPES", "SourceRecord", "SourceRegistry",
    "InvalidSourceType", "SourceVaultError", "NoSuchContentHash",
]

# ─────────────────────────────────────────────────────────────
# Constrained vocabulary — a source_type outside this set is a
# structural rejection, never an implicit new category.
# ─────────────────────────────────────────────────────────────
SOURCE_TYPES: frozenset[str] = frozenset({
    "yaml", "markdown", "text", "image", "diagram", "screenshot",
    "audio_transcript", "video_transcript", "code", "repository",
    "research", "conversation", "note", "simulation",
    "external_reference",
})

_DEFAULT_ARCHIVE_DIR = Path(__file__).resolve().parent / "archive"
_DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.jsonl"


class SourceVaultError(Exception):
    """Base for structured rejections raised by this module. Never raised
    for "we merely disagree with the content" — only for inputs that
    cannot be safely or meaningfully registered at all."""


class InvalidSourceType(SourceVaultError):
    """Raised when source_type is outside SOURCE_TYPES. The caller gets a
    named, catchable exception — never a silent False, never a crash with
    an unrelated traceback."""


class NoSuchContentHash(SourceVaultError):
    """Raised by `get_content_by_hash` when no archived blob exists for the
    given hash. Distinct from an empty result: a caller asking "give me the
    bytes for H" deserves a loud, named failure if H was never archived,
    not a None that could be mistaken for "empty content"."""


# ─────────────────────────────────────────────────────────────
# Structured result — never a bare identifier or bool (house style)
# ─────────────────────────────────────────────────────────────

@dataclass
class SourceRecord:
    artifact_id: str
    content_hash: str                 # "sha256:<64 hex>"
    ingestion_timestamp: str          # RFC3339 UTC
    source_type: str
    source_location: str
    author_or_origin: str
    license_status: str
    confidentiality_status: str
    provenance_status: str
    integrity_status: str
    original_content_reference: str
    immutable_archive_reference: str
    integrity_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceRegistry:
    """Append-only ledger of ingestion events over an immutable,
    content-addressed archive.

    There is no `update`, no `overwrite`, no `delete`, no `purge`, no
    `clear`. Not by convention — the methods do not exist. A SourceRecord,
    once appended, can only ever be re-read or have its integrity_status
    re-checked (verify_integrity), which records a fresh finding — it never
    edits history, it appends to `integrity_history`.
    """

    def __init__(
        self,
        archive_dir: str | Path = _DEFAULT_ARCHIVE_DIR,
        registry_path: str | Path | None = _DEFAULT_REGISTRY_PATH,
    ) -> None:
        self._archive_dir = Path(archive_dir)
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        self._registry_path = Path(registry_path) if registry_path else None
        self._records: dict[str, SourceRecord] = {}
        if self._registry_path and self._registry_path.exists():
            self._replay()

    # -- internal helpers -------------------------------------------------

    def _replay(self) -> None:
        """Reload prior ingestion events from the append-only JSONL file.
        Read-only over that file — never writes here."""
        with open(self._registry_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                self._records[obj["artifact_id"]] = SourceRecord(**obj)

    def _append_to_ledger(self, rec: SourceRecord) -> None:
        if not self._registry_path:
            return
        with open(self._registry_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec.to_dict(), sort_keys=True))
            fh.write("\n")

    @staticmethod
    def _hash_bytes(content: bytes) -> str:
        return "sha256:" + hashlib.sha256(content).hexdigest()

    def _archive_path_for_hash(self, content_hash: str) -> Path:
        bare = content_hash.split(":", 1)[-1]
        return self._archive_dir / f"{bare}.blob"

    def _ensure_archived(self, content: bytes, content_hash: str) -> Path:
        """Content-addressed, idempotent copy. If a blob for this hash
        already exists, it is never opened for writing, never truncated,
        never touched — we just point the new record at it."""
        dest = self._archive_path_for_hash(content_hash)
        if dest.exists():
            return dest
        # Write to a temp file in the same directory, then atomically
        # rename into place, so a concurrent/second ingest of the same
        # bytes can never observe (or race into) a partially-written blob.
        fd, tmp_name = tempfile.mkstemp(dir=self._archive_dir, prefix=".tmp-")
        try:
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(content)
            # If another ingest already landed the file first, keep the
            # existing one untouched and discard our temp copy.
            if dest.exists():
                os.remove(tmp_name)
            else:
                os.replace(tmp_name, dest)
        except Exception:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
            raise
        return dest

    # -- public API ---------------------------------------------------------

    def ingest_source(
        self,
        path_or_bytes: "str | Path | bytes",
        source_type: str,
        source_location: str,
        author_or_origin: str,
        license_status: str = "UNKNOWN",
        confidentiality_status: str = "UNKNOWN",
    ) -> SourceRecord:
        """Hash the original bytes, archive them (idempotent by content),
        and append a new SourceRecord describing THIS ingestion event.

        Raises InvalidSourceType (a structured, catchable rejection) if
        source_type is outside SOURCE_TYPES. Never returns a record for a
        rejected type, and never silently substitutes a default.
        """
        if source_type not in SOURCE_TYPES:
            raise InvalidSourceType(
                f"source_type {source_type!r} is not in the constrained "
                f"vocabulary. Allowed: {sorted(SOURCE_TYPES)}"
            )

        if isinstance(path_or_bytes, (str, Path)):
            content = Path(path_or_bytes).read_bytes()
            original_ref = str(path_or_bytes)
        elif isinstance(path_or_bytes, (bytes, bytearray)):
            content = bytes(path_or_bytes)
            original_ref = "<in-memory bytes>"
        else:
            raise SourceVaultError(
                f"path_or_bytes must be a path or bytes, got "
                f"{type(path_or_bytes).__name__}"
            )

        content_hash = self._hash_bytes(content)
        archived_path = self._ensure_archived(content, content_hash)

        now = datetime.now(timezone.utc).isoformat()
        rec = SourceRecord(
            artifact_id=f"SRC-{uuid.uuid4().hex}",
            content_hash=content_hash,
            ingestion_timestamp=now,
            source_type=source_type,
            source_location=source_location,
            author_or_origin=author_or_origin,
            license_status=license_status,
            confidentiality_status=confidentiality_status,
            provenance_status="UNVERIFIED",
            integrity_status="VERIFIED_AT_INGEST",
            original_content_reference=original_ref,
            immutable_archive_reference=str(
                archived_path.relative_to(self._archive_dir.parent)
            ),
        )
        self._records[rec.artifact_id] = rec
        self._append_to_ledger(rec)
        return rec

    def get_source(self, artifact_id: str) -> SourceRecord | None:
        return self._records.get(artifact_id)

    def verify_integrity(self, artifact_id: str) -> bool:
        """Recompute the archived blob's hash and compare it against the
        recorded content_hash. Never a silent pass: mismatch, a missing
        blob, or a missing record all resolve to a truthful, recorded
        outcome, and the record's integrity_status is updated to match.
        """
        rec = self._records.get(artifact_id)
        if rec is None:
            raise KeyError(f"no source record for '{artifact_id}'")

        archived_path = self._archive_dir.parent / rec.immutable_archive_reference
        checked_at = datetime.now(timezone.utc).isoformat()

        if not archived_path.exists():
            rec.integrity_status = "PROVENANCE_FAILURE"
            rec.integrity_history.append({
                "checked_at": checked_at, "result": "PROVENANCE_FAILURE",
                "reason": "archived blob is missing",
            })
            return False

        actual_hash = self._hash_bytes(archived_path.read_bytes())
        if actual_hash != rec.content_hash:
            rec.integrity_status = "PROVENANCE_FAILURE"
            rec.integrity_history.append({
                "checked_at": checked_at, "result": "PROVENANCE_FAILURE",
                "reason": "archived content hash does not match recorded "
                          "content_hash",
                "expected": rec.content_hash, "actual": actual_hash,
            })
            return False

        rec.integrity_status = "VERIFIED"
        rec.integrity_history.append({
            "checked_at": checked_at, "result": "VERIFIED",
        })
        return True

    def all_records(self) -> tuple[SourceRecord, ...]:
        return tuple(self._records.values())

    def get_by_hash(self, content_hash: str) -> tuple[SourceRecord, ...]:
        """Resolve a content hash back to every SourceRecord that claims it.

        Deliberately returns a tuple, not a single record: `ingest_source()`
        always mints a fresh artifact_id even for byte-identical content
        (two ingestion events over the same bytes are two different FACTS
        about ingestion, per this module's own house rule above — see
        the module docstring's "two SourceRecords" paragraph), so more than
        one record can legitimately share a hash. A caller that only cares
        about the content itself (not which ingestion event) can safely use
        any returned record's artifact_id with `get_content()` below, since
        they all resolve to the identical archived bytes by construction.
        """
        return tuple(r for r in self._records.values() if r.content_hash == content_hash)

    def get_content(self, artifact_id: str) -> bytes:
        """Return the exact archived bytes for a registered SourceRecord.

        Raises KeyError for an unknown artifact_id (same convention as
        `get_source()`'s sibling lookups elsewhere in this codebase) and
        NoSuchContentHash if the record exists but its archived blob is
        missing — the same failure `verify_integrity()` detects, surfaced
        here as a loud exception rather than silently returning nothing,
        since a caller of this method wants the bytes, not a status report.
        """
        rec = self._records.get(artifact_id)
        if rec is None:
            raise KeyError(f"no source record for '{artifact_id}'")
        archived_path = self._archive_dir.parent / rec.immutable_archive_reference
        if not archived_path.exists():
            raise NoSuchContentHash(
                f"'{artifact_id}' is registered but its archived blob is "
                f"missing at '{archived_path}' — run verify_integrity() to "
                f"record this as a provenance failure."
            )
        return archived_path.read_bytes()
