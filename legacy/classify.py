"""
§Phase 9, 10 — Safe Legacy Classification Tool.

Scans the real, on-disk YAML corpus (not a simulated one) and produces a
derived classification manifest. This module NEVER touches the originals:
no write, no rename, no delete, anywhere in this file. Every finding is a
row in a manifest file elsewhere.

DEFAULT: UNKNOWN

A file gets anything other than UNKNOWN only because an OBJECTIVE,
MACHINE-VERIFIABLE criterion in schema/validator.py or firewall/gate.py
established it. "This file looks like the others" is not such a criterion.

TWO TRACKS

  TRACK A — every file defaults to UNKNOWN. Zero automated classification.
  TRACK B — files run through validate_artifact(); anything that isn't a
            clean, fully-schema-conformant TitanOS artifact YAML is
            REVIEW_REQUIRED, not silently promoted.

Both tracks are computed and reported. Neither is applied to production.
Nothing here wires into an ingest path — that remains the standing human
decision documented in legacy/DECISION_PACKET.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schema.validator import validate_artifact  # noqa: E402

__all__ = ["FileRecord", "scan_corpus", "classify_track_a", "classify_track_b"]

EXCLUDE_DIR_MARKERS = ("/.git/", "/node_modules/", "/cosmic-library/")


@dataclass
class FileRecord:
    path: str
    artifact_hash: str
    size_bytes: int
    schema_detection: str          # "TITANOS_ARTIFACT" | "UNRECOGNISED_YAML" | "UNPARSEABLE"
    validation_status: str         # from validate_artifact(), or "N/A"
    validation_issue_count: int
    unknown_field_count: int
    classification: str            # final track classification
    reason: str
    confidence: str                # "NONE" | "LOW" | "STRUCTURAL_ONLY"
    review_required: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hash_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return "sha256:" + h.hexdigest()


def scan_corpus(root: str = "/home/tech2", max_bytes: int = 5_000_000) -> list[Path]:
    """Find the real on-disk corpus. Read-only — no file is opened for
    writing anywhere in this function or anything it calls."""
    root_path = Path(root)
    files: list[Path] = []
    for ext in ("*.yaml", "*.yml"):
        for p in root_path.rglob(ext):
            sp = str(p)
            if any(marker in sp for marker in EXCLUDE_DIR_MARKERS):
                continue
            files.append(p)
    return sorted(files)


def classify_track_a(files: list[Path]) -> list[FileRecord]:
    """Track A: everything is UNKNOWN. No file content is even read for
    classification purposes (hash is still computed, since identity is not
    the same claim as classification)."""
    out = []
    for p in files:
        try:
            size = p.stat().st_size
            ah = _hash_file(p)
        except OSError as e:
            out.append(FileRecord(
                path=str(p), artifact_hash="N/A", size_bytes=-1,
                schema_detection="UNPARSEABLE", validation_status="N/A",
                validation_issue_count=0, unknown_field_count=0,
                classification="UNKNOWN", reason=f"unreadable: {e}",
                confidence="NONE", review_required=True,
            ))
            continue
        out.append(FileRecord(
            path=str(p), artifact_hash=ah, size_bytes=size,
            schema_detection="NOT_EVALUATED", validation_status="N/A",
            validation_issue_count=0, unknown_field_count=0,
            classification="UNKNOWN",
            reason="Track A: default classification, no automated evaluation performed",
            confidence="NONE", review_required=True,
        ))
    return out


def classify_track_b(files: list[Path], max_bytes: int = 5_000_000) -> list[FileRecord]:
    """Track B: run the real validator. Still defaults to UNKNOWN unless a
    machine-verifiable criterion says otherwise — 'parsed as YAML' is never
    treated as 'is a trustworthy TitanOS artifact'."""
    out = []
    for p in files:
        try:
            size = p.stat().st_size
            ah = _hash_file(p)
        except OSError as e:
            out.append(FileRecord(
                path=str(p), artifact_hash="N/A", size_bytes=-1,
                schema_detection="UNPARSEABLE", validation_status="N/A",
                validation_issue_count=0, unknown_field_count=0,
                classification="UNKNOWN", reason=f"unreadable: {e}",
                confidence="NONE", review_required=True,
            ))
            continue

        if size > max_bytes:
            out.append(FileRecord(
                path=str(p), artifact_hash=ah, size_bytes=size,
                schema_detection="UNPARSEABLE", validation_status="N/A",
                validation_issue_count=0, unknown_field_count=0,
                classification="UNKNOWN",
                reason=f"exceeds {max_bytes} byte scan ceiling; not evaluated",
                confidence="NONE", review_required=True,
            ))
            continue

        try:
            text = p.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeDecodeError) as e:
            out.append(FileRecord(
                path=str(p), artifact_hash=ah, size_bytes=size,
                schema_detection="UNPARSEABLE", validation_status="N/A",
                validation_issue_count=0, unknown_field_count=0,
                classification="UNKNOWN", reason=f"unreadable: {e}",
                confidence="NONE", review_required=True,
            ))
            continue

        result = validate_artifact(text)

        # Even a fully schema-VALID legacy file is not auto-promoted past
        # REVIEW_REQUIRED here — schema conformance to the TitanOS artifact
        # schema proves structure, not that the file was ever INTENDED as a
        # TitanOS artifact (near-certainly none of the 3,058 pre-existing
        # files were authored against this schema, since the schema is new).
        if result.status == "VALID":
            cls = "REVIEW_REQUIRED"
            reason = ("structurally conforms to the TitanOS artifact schema; "
                      "requires human confirmation this was the file's actual "
                      "intent before any status upgrade")
            conf = "STRUCTURAL_ONLY"
        elif result.status == "INVALID":
            cls = "UNRECOGNISED_YAML"
            reason = (f"valid YAML, does not conform to TitanOS artifact schema "
                      f"({result.issues[0].what if result.issues else 'see issues'}); "
                      f"this is the expected, correct outcome for legacy YAML that "
                      f"predates this schema — NOT evidence of contamination")
            conf = "LOW"
        else:
            cls = "UNKNOWN"
            reason = "could not be evaluated"
            conf = "NONE"

        out.append(FileRecord(
            path=str(p), artifact_hash=ah, size_bytes=size,
            schema_detection=("TITANOS_ARTIFACT_SHAPED" if result.status == "VALID"
                              else "UNRECOGNISED_YAML"),
            validation_status=result.status,
            validation_issue_count=len(result.issues),
            unknown_field_count=len(result.unknown_fields),
            classification=cls, reason=reason, confidence=conf,
            review_required=True,  # every legacy file, no exceptions (§Phase 9)
        ))
    return out


def write_manifest(records: list[FileRecord], out_path: str) -> None:
    payload = {
        "manifest_type": "LEGACY_CLASSIFICATION_MANIFEST",
        "record_count": len(records),
        "note": "Derived data only. No source file was modified, renamed, or deleted.",
        "records": [r.to_dict() for r in records],
    }
    Path(out_path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    files = scan_corpus()
    print(f"corpus size: {len(files)} files", file=sys.stderr)
    a = classify_track_a(files)
    b = classify_track_b(files)
    Path("legacy/manifests").mkdir(parents=True, exist_ok=True)
    write_manifest(a, "legacy/manifests/track_a.json")
    write_manifest(b, "legacy/manifests/track_b.json")
    print("wrote legacy/manifests/track_a.json and track_b.json", file=sys.stderr)
