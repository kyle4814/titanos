"""EXP-001 — run a real, public, third-party document corpus through the
existing TitanOS pipeline and record what happens.

WHY THIS EXISTS

Every subsystem in this repository has been proven against fixtures
written by the same author as the subsystem. This script writes no new
capability. It only wires together what already exists:

    schema/validator.py::validate_artifact      structural validation
    firewall/gate.py::evaluate                  runtime-authority decision
    firewall/gate.py::collapse_ancestry         source multiplicity
    kpm/schemas/epistemic_types.py              classification
    foundation/untrusted_text.py                injection surface
    foundation/mouth_common.py::fetch_feed      the only socket, gated

HOW FIELDS ARE DERIVED — READ THIS BEFORE TRUSTING A RESULT

`firewall.Artifact` asks for metadata an inbound document does not carry.
Inventing plausible values would make the experiment measure this script's
imagination rather than the pipeline, so each field is either measured or
explicitly left at its least-privileged value:

    schema_valid           MEASURED  validate_artifact(text).status == VALID
    provenance_valid       TRUE      we hold url + retrieved_at + sha256
    authorization_valid    FALSE     no human authorized any of these
    generated_by_agent     FALSE     these are human-written public docs
    contains_instructions  MEASURED  untrusted_text.looks_like_injection()
    root_origin            MEASURED  the GitHub owner (org) of the document
    classification         DECLARED  "EVIDENCE" — deliberately the most
                                     favourable authorized class, so that a
                                     REFUSED verdict cannot be dismissed as
                                     an artifact of a hostile input label
    memetic_profile        EMPTY     nothing in this repository measures it

That last one is a finding in itself and is recorded as such: `memetic_
profile` is consumed by `_memetic_flags()` and referenced by the schema,
but no code anywhere in this repository derives one from text. On real
input those risk flags cannot fire, because nothing feeds them.

WRITE SCOPE

Writes only under experiments/EXP-001/. Reads the network only through
`fetch_feed`, which refuses without a DiscoveryPolicy naming a concrete
objective and a budget.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from firewall.gate import Artifact, collapse_ancestry, evaluate      # noqa: E402
from foundation.discovery_authorization import (                      # noqa: E402
    DiscoveryPolicy, reset_budgets)
from foundation.mouth_common import fetch_feed                        # noqa: E402
from foundation.untrusted_text import looks_like_injection            # noqa: E402
from kpm.schemas.epistemic_types import (                             # noqa: E402
    MissingEvidence, classify_claim, reclassify)
from schema.validator import validate_artifact                        # noqa: E402

# ── THE SELECTION RULE, FIXED BEFORE ANY CONTENT WAS FETCHED ──────────
#
# Stated here so the corpus is reproducible rather than cherry-picked. No
# repository was added or removed after its content was seen.
#
#   1. Well-known open-source projects, chosen for breadth across
#      ecosystems (JS, Python, Go, Java, C, Rust, infrastructure).
#   2. Kept only if the GitHub API reports the licence as MIT or
#      Apache-2.0. Everything else is EXCLUDED and the exclusion is
#      recorded with its actual licence -- the rule has to bite visibly,
#      or it is not a rule.
#   3. At least two organisations contribute two repositories each, so
#      `collapse_ancestry` has real common-origin material to work on.
#   4. The list below is complete. Nothing was fetched that is not here.
CANDIDATE_REPOS = [
    ("facebook", "react"), ("vuejs", "core"), ("expressjs", "express"),
    ("axios", "axios"), ("kubernetes", "kubernetes"), ("grpc", "grpc"),
    ("apache", "kafka"), ("apache", "spark"), ("google", "guava"),
    ("google", "leveldb"), ("tensorflow", "tensorflow"),
    ("pytorch", "pytorch"), ("denoland", "deno"), ("nodejs", "node"),
    ("microsoft", "TypeScript"), ("microsoft", "vscode"),
    ("elastic", "elasticsearch"), ("prometheus", "prometheus"),
    ("grafana", "grafana"), ("hashicorp", "terraform"),
    ("openssl", "openssl"), ("jekyll", "jekyll"),
    ("home-assistant", "core"), ("ansible", "ansible"),
    ("moby", "moby"),
]
ACCEPTED_LICENCES = {"MIT", "Apache-2.0"}

# Advisories are public security documents that make impact claims. One
# API request returns many, so they are cheap against the 60/hour
# unauthenticated budget. Taken in the order the API returns them.
ADVISORY_URL = ("https://api.github.com/advisories"
                "?per_page=10&sort=published&direction=desc")

USER_AGENT = "titanos-exp001/1.0 (research; +https://github.com/kyle4814/titanos)"

# Deterministic capability-claim markers. Sentences containing one of
# these are extracted as claims. This is a blunt instrument on purpose:
# a cleverer extractor would be a new capability, which this cycle forbids.
CLAIM_MARKERS = re.compile(
    r"\b(guarantee[sd]?|ensures?|never fails?|100%|fastest|most secure|"
    r"secure by default|production[- ]ready|battle[- ]tested|"
    r"industry[- ]standard|proven|reliable|scalable|zero[- ]downtime|"
    r"bullet[- ]proof|impossible to)\b", re.I)


def _sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_claims(text: str, limit: int = 5) -> list[str]:
    """Sentences carrying a capability-claim marker, in document order."""
    out: list[str] = []
    for raw in re.split(r"(?<=[.!?])\s+|\n", text):
        s = " ".join(raw.split())
        if 20 <= len(s) <= 300 and CLAIM_MARKERS.search(s):
            out.append(s)
            if len(out) >= limit:
                break
    return out


def collect(policy: DiscoveryPolicy) -> tuple[list[dict], list[dict]]:
    """Fetch the corpus. Returns (documents, exclusions)."""
    docs: list[dict] = []
    excluded: list[dict] = []

    for owner, repo in CANDIDATE_REPOS:
        meta_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            meta = json.loads(fetch_feed(meta_url, user_agent=USER_AGENT,
                                         policy=policy).decode("utf-8", "replace"))
        except Exception as exc:                                  # noqa: BLE001
            excluded.append({"repo": f"{owner}/{repo}", "reason": "METADATA_FETCH_FAILED",
                             "detail": f"{type(exc).__name__}: {exc}"})
            continue

        licence = ((meta.get("license") or {}).get("spdx_id")) or "UNKNOWN"
        if licence not in ACCEPTED_LICENCES:
            excluded.append({"repo": f"{owner}/{repo}", "reason": "LICENCE_NOT_PERMITTED",
                             "detail": f"licence is {licence}; rule admits "
                                       f"{sorted(ACCEPTED_LICENCES)}"})
            continue

        branch = meta.get("default_branch") or "main"
        body = None
        for name in ("README.md", "README.rst", "README"):
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{name}"
            try:
                body = fetch_feed(url, user_agent=USER_AGENT, policy=policy)
                break
            except Exception:                                     # noqa: BLE001
                continue
        if body is None:
            excluded.append({"repo": f"{owner}/{repo}", "reason": "NO_README_FOUND",
                             "detail": f"no README.md/.rst/plain on {branch}"})
            continue

        text = body.decode("utf-8", "replace")
        docs.append({
            "doc_id": f"README:{owner}/{repo}",
            "source_url": f"https://github.com/{owner}/{repo}/blob/{branch}/README.md",
            "retrieved_at": _now(), "content_hash": _sha256(body),
            "licence": licence, "collection_method": "GET raw.githubusercontent.com",
            "organisation": owner, "doc_type": "README",
            "bytes": len(body), "text": text,
            "why_included": "permissively-licensed project README making "
                            "capability claims; selected before content was seen",
        })

    # ── security advisories: real public docs, impact claims, one request
    try:
        advisories = json.loads(fetch_feed(ADVISORY_URL, user_agent=USER_AGENT,
                                           policy=policy).decode("utf-8", "replace"))
    except Exception as exc:                                      # noqa: BLE001
        excluded.append({"repo": "github/advisories", "reason": "ADVISORY_FETCH_FAILED",
                         "detail": f"{type(exc).__name__}: {exc}"})
        advisories = []

    for adv in advisories if isinstance(advisories, list) else []:
        text = (adv.get("description") or "").strip()
        if not text:
            excluded.append({"repo": adv.get("ghsa_id", "?"),
                             "reason": "EMPTY_ADVISORY_DESCRIPTION",
                             "detail": "no description field to analyse"})
            continue
        raw = text.encode("utf-8")
        docs.append({
            "doc_id": f"ADVISORY:{adv.get('ghsa_id')}",
            "source_url": adv.get("html_url") or ADVISORY_URL,
            "retrieved_at": _now(), "content_hash": _sha256(raw),
            "licence": "CC-BY-4.0 (GitHub Advisory Database)",
            "collection_method": "GET api.github.com/advisories",
            "organisation": "github/advisory-database", "doc_type": "SECURITY_ADVISORY",
            "bytes": len(raw), "text": text,
            "why_included": "public security advisory asserting impact and "
                            "remediation; contains imperatives aimed at a reader",
        })

    # ── deliberately malformed / truncated, DERIVED and labelled as such
    if docs:
        donor = docs[0]
        trunc = donor["text"][:180]
        docs.append({
            "doc_id": "DERIVED:truncated", "source_url": donor["source_url"],
            "retrieved_at": _now(), "content_hash": _sha256(trunc.encode()),
            "licence": donor["licence"], "collection_method": "DERIVED — truncated to 180 chars",
            "organisation": donor["organisation"], "doc_type": "DERIVED_TRUNCATED",
            "bytes": len(trunc.encode()), "text": trunc,
            "why_included": "the payload requires a malformed/truncated document. "
                            "This is a DERIVED mutation of a real document, not a "
                            "real-world artifact, and is labelled so nobody reads "
                            "it as evidence about real inputs.",
        })
    docs.append({
        "doc_id": "DERIVED:empty", "source_url": "n/a",
        "retrieved_at": _now(), "content_hash": _sha256(b""),
        "licence": "n/a", "collection_method": "DERIVED — empty document",
        "organisation": "n/a", "doc_type": "DERIVED_EMPTY", "bytes": 0, "text": "",
        "why_included": "degenerate input: does the pipeline crash or refuse cleanly?",
    })
    return docs, excluded


def run_pipeline(doc: dict) -> dict:
    """One document through parser -> validator -> firewall -> kpm."""
    text = doc["text"]
    rec: dict = {k: doc[k] for k in (
        "doc_id", "source_url", "retrieved_at", "content_hash", "licence",
        "collection_method", "organisation", "doc_type", "bytes")}
    rec["exceptions"] = []

    # ── validator ------------------------------------------------------
    try:
        vr = validate_artifact(text)
        rec["validator_result"] = {
            "status": vr.status,
            "artifact_id": vr.artifact_id,
            "issues": [{"rule": i.rule, "what": i.what, "where": i.where}
                       for i in (vr.issues or [])],
        }
    except Exception as exc:                                      # noqa: BLE001
        rec["validator_result"] = {"status": "EXCEPTION"}
        rec["exceptions"].append(f"validate_artifact: {type(exc).__name__}: {exc}")

    # ── injection surface ---------------------------------------------
    try:
        markers = looks_like_injection(text)
        rec["injection_markers"] = list(markers)
    except Exception as exc:                                      # noqa: BLE001
        rec["injection_markers"] = []
        rec["exceptions"].append(f"looks_like_injection: {type(exc).__name__}: {exc}")

    # ── firewall -------------------------------------------------------
    art = Artifact(
        artifact_id=doc["doc_id"],
        classification="EVIDENCE",          # most favourable authorized class
        contamination_state="UNVERIFIED",
        schema_valid=(rec.get("validator_result", {}).get("status") == "VALID"),
        provenance_valid=True,              # url + timestamp + sha256 held
        authorization_valid=False,          # no human authorized these
        root_origin=doc["organisation"],
        generated_by_agent=False,
        memetic_profile={},                 # nothing in this repo measures it
        contains_instructions=bool(rec.get("injection_markers")),
    )
    try:
        dec = evaluate(art)
        rec["firewall_decision"] = dec.to_dict()
    except Exception as exc:                                      # noqa: BLE001
        rec["firewall_decision"] = {"verdict": "EXCEPTION"}
        rec["exceptions"].append(f"firewall.evaluate: {type(exc).__name__}: {exc}")

    # ── kpm classification --------------------------------------------
    claims = _extract_claims(text)
    rec["claims_extracted"] = len(claims)
    rec["kpm"] = []
    for n, claim_text in enumerate(claims):
        entry: dict = {"claim": claim_text}
        try:
            c = classify_claim(f"{doc['doc_id']}#c{n}", claim_text,
                               "UNVERIFIED_EXTERNAL_CLAIM",
                               classified_by="exp-001", confidence="LOW")
            entry["classification"] = c.classification
            entry["confidence"] = c.confidence
            entry["evidence_refs"] = list(c.evidence_refs)
            entry["provenance"] = [h[0] for h in c.history]
            # Falsification probe: can this be upgraded with no evidence?
            try:
                reclassify(c, "VERIFIED_FACT",
                           reason="the document asserts it confidently",
                           by="exp-001")
                entry["unevidenced_upgrade"] = "ALLOWED"
            except MissingEvidence:
                entry["unevidenced_upgrade"] = "REFUSED"
        except Exception as exc:                                  # noqa: BLE001
            entry["classification"] = "EXCEPTION"
            rec["exceptions"].append(
                f"classify_claim({doc['doc_id']}#c{n}): {type(exc).__name__}: {exc}")
        rec["kpm"].append(entry)

    # ── final state ----------------------------------------------------
    verdict = rec.get("firewall_decision", {}).get("verdict")
    if rec["exceptions"]:
        rec["final_state"] = "CRASHED"
    elif verdict == "REFUSED":
        rec["final_state"] = "REFUSED"
    elif verdict == "QUARANTINED":
        rec["final_state"] = "QUARANTINED"
    elif verdict == "AUTHORIZED":
        rec["final_state"] = "TRUE"
    else:
        rec["final_state"] = "UNKNOWN"
    return rec


def main() -> int:
    started = _now()
    reset_budgets()
    policy = DiscoveryPolicy(
        objective=("EXP-001: retrieve permissively-licensed public README and "
                   "security-advisory documents to test the TitanOS pipeline "
                   "against third-party claims"),
        requested_scope="READ_URL",
        max_queries=140, max_wall_clock_seconds=900, max_results=80)

    docs, excluded = collect(policy)
    results = [run_pipeline(d) for d in docs]

    # ── source multiplicity vs independence ---------------------------
    by_org: dict[str, list] = {}
    for d in docs:
        by_org.setdefault(d["organisation"], []).append(d)
    ancestry = {}
    for org, group in by_org.items():
        if len(group) < 2:
            continue
        arts = [Artifact(artifact_id=g["doc_id"], classification="EVIDENCE",
                         root_origin=org, provenance_valid=True)
                for g in group]
        ancestry[org] = {"documents": len(group),
                         "independent_sources_after_collapse": collapse_ancestry(arts)}

    finished = _now()
    corpus = {"selection_rule": "see METHOD.md; fixed before any fetch",
              "candidates": len(CANDIDATE_REPOS), "collected": len(docs),
              "excluded": excluded,
              "documents": [{k: v for k, v in d.items() if k != "text"} for d in docs]}
    (HERE / "CORPUS.json").write_text(json.dumps(corpus, indent=2, sort_keys=True))
    payload = {"started_at": started, "finished_at": finished,
               "documents": len(results), "ancestry_collapse": ancestry,
               "results": results}
    (HERE / "RESULTS.json").write_text(json.dumps(payload, indent=2, sort_keys=True))

    corpus_hash = _sha256((HERE / "CORPUS.json").read_bytes())
    results_hash = _sha256((HERE / "RESULTS.json").read_bytes())
    receipt = {
        "receipt_id": f"EXP-001-{int(time.time())}",
        "run_id": f"exp001-{started}", "actor": "claude-opus-5 (agent)",
        "started_at": started, "finished_at": finished,
        "action": "EXP-001 public claim corpus through existing pipeline",
        "inputs": {"corpus_manifest_hash": corpus_hash,
                   "candidate_repos": len(CANDIDATE_REPOS)},
        "outputs": {"CORPUS.json": corpus_hash, "RESULTS.json": results_hash},
        "changed_files": ["experiments/EXP-001/CORPUS.json",
                          "experiments/EXP-001/RESULTS.json"],
        "tests_run": "./run_all_tests.sh", "tests_result": "SEE_REPORT",
        "status": "COMPLETED",
        "previous_hash": None,
        "note": "A receipt records what happened. It is not evidence that any "
                "claim in the corpus is true.",
    }
    receipt["hash"] = _sha256(json.dumps(receipt, sort_keys=True).encode())
    (HERE / "RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))

    print(f"collected {len(docs)} documents, {len(excluded)} exclusions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
