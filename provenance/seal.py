"""Seal the cosmic library: hash every artifact, emit a release manifest.

Uses the TitanOS provenance layer. Every hash here is independently
reproducible with sha256 and canonical JSON — no TitanOS tooling required
to verify.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, "/home/tech2/titanos-provenance")
from provenance import build_manifest, hash_file, new_session_id, content_hash, verify_lineage

LIB = Path(__file__).resolve().parents[1]
REV = "cosmic-library-gen-001"
PIPE = "cosmic-library-1"
SESSION = new_session_id()

doctrine = LIB / "doctrine" / "doctrine-001.yaml"
doctrine_hash = hash_file(doctrine)

artifacts, manifests = [], {}
for p in sorted(LIB.rglob("*")):
    if not p.is_file() or ".git" in p.parts or p.suffix == ".pyc":
        continue
    if p.name.startswith("RELEASE-"):
        continue
    m = build_manifest(
        artifact_type=p.parent.name or "root",
        content_hash_value=hash_file(p),
        source_revision=REV, pipeline_version=PIPE,
        doctrine_version="1", doctrine_hash=doctrine_hash,
        agent_session_id=SESSION,
        parent_artifacts=() if p == doctrine else (content_hash({"doctrine": doctrine_hash}),),
        status="CANDIDATE",
    )
    artifacts.append((str(p.relative_to(LIB)), m))
    manifests[m.artifact_id] = m.to_dict()

release = {
    "release_id": "TITANOS-COSMIC-LIBRARY-001",
    "generation": 1,
    "parent_release": None,
    "source_revision": REV,
    "pipeline_version": PIPE,
    "doctrine_version": "1",
    "doctrine_hash": doctrine_hash,
    "artifact_count": len(artifacts),
    "artifacts": [{"path": path, "artifact_id": m.artifact_id,
                   "content_hash": m.content_hash} for path, m in artifacts],
    "signature": None,
    "signature_status": "UNSIGNED",
    "human_release_authorization": "NOT_GRANTED",
    "publication_status": "CANDIDATE_ONLY_DO_NOT_PUBLISH",
    "known_open_defects": ["F-006 upsert accepts fabricated authority",
                           "F-007 git history contaminated"],
}
release["release_hash"] = content_hash(
    {k: v for k, v in release.items() if k != "release_hash"})

out = LIB / "releases" / "RELEASE-001.json"
out.write_text(json.dumps(release, indent=2, sort_keys=True), encoding="utf-8")

print(f"artifacts sealed : {len(artifacts)}")
print(f"doctrine hash    : {doctrine_hash}")
print(f"release hash     : {release['release_hash']}")
print(f"authorization    : {release['human_release_authorization']}")
lin = verify_lineage(manifests)
print(f"lineage          : {lin.overall}  {lin.checks}")
