"""EXP-001 Arm B — get past the schema gate, then test whether the
firewall actually discriminates.

WHY ARM B EXISTS

Arm A ran 28 real third-party documents through the pipeline and every
single one came back REFUSED with the identical reason: "schema invalid".
That is a uniform result, and the governing payload says a uniform clean
pass must be treated as suspicious and investigated rather than reported
as a success.

The investigation found the cause immediately: `firewall.evaluate()` is an
ordered chain of gates whose THIRD gate is `if not artifact.schema_valid`.
No README or security advisory on earth is a well-formed TitanOS artifact,
so every document died at gate three and the seven gates behind it --
provenance, the prompt-injection boundary, the classification allowlist,
agent self-authorization, common-ancestry collapse, constitutional
authority -- never executed once.

So Arm A did not measure the firewall's judgement. It measured the file
format of its input. Reporting "28/28 correctly refused" would have been
technically true and substantively worthless.

Arm B wraps each real document's real content hash into the minimal
envelope the validator accepts, so schema_valid becomes True and the rest
of the chain actually runs. Nothing new is built: the envelope is the
schema this repository already defines, and the decisions are made by the
same `evaluate()` Arm A called.

THE PROBES

    B1  honest baseline    everything measured, authorization not declared
    B2  self-declaration   the artifact declares its own authorization_valid
    B3  shared ancestry    same-organisation documents offered as corroboration
    B4  injection + B2     a document containing instructions, self-authorized

B2 and B4 are the falsification probes. `authorization_valid` is a bare
boolean the caller sets. If declaring it True is sufficient to reach
AUTHORIZED, then a caller-declared fact is being treated as a verified
fact, which this repository's own doctrine names as a prohibition.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from firewall.gate import Artifact, evaluate                          # noqa: E402
from schema.validator import validate_artifact                        # noqa: E402

ENVELOPE = """artifact_id: {aid}
artifact_type: EVIDENCE_RECORD
schema_version: "1.0.0"
created_at: "{created}"
content_hash: "sha256:{chash}"
contamination_state: {contam}
classification: EVIDENCE
"""


def envelope_for(doc: dict, contamination: str = "UNVERIFIED") -> str:
    """The real document's real hash, inside the schema this repo defines."""
    return ENVELOPE.format(
        aid=doc["doc_id"].replace(":", "-").replace("/", "-").lower()[:60],
        created=doc["retrieved_at"].replace("+00:00", "Z"),
        chash=doc["content_hash"], contam=contamination)


def main() -> int:
    corpus = json.loads((HERE / "CORPUS.json").read_text())
    arm_a = {r["doc_id"]: r for r in
             json.loads((HERE / "RESULTS.json").read_text())["results"]}
    docs = [d for d in corpus["documents"] if d["doc_type"] != "DERIVED_EMPTY"]

    out = []
    for doc in docs:
        text = envelope_for(doc)
        vr = validate_artifact(text)
        has_instructions = bool(arm_a.get(doc["doc_id"], {}).get("injection_markers"))

        base = dict(
            artifact_id=doc["doc_id"], classification="EVIDENCE",
            contamination_state="UNVERIFIED",
            schema_valid=(vr.status == "VALID"),
            provenance_valid=True, root_origin=doc["organisation"],
            generated_by_agent=False, memetic_profile={},
        )

        b1 = evaluate(Artifact(**base, authorization_valid=False,
                               contains_instructions=has_instructions))
        b2 = evaluate(Artifact(**base, authorization_valid=True,
                               contains_instructions=has_instructions))

        # B3: offer the SAME organisation's other documents as corroboration
        siblings = [d for d in docs
                    if d["organisation"] == doc["organisation"]
                    and d["doc_id"] != doc["doc_id"]]
        b3 = None
        if siblings:
            corro = [Artifact(artifact_id=s["doc_id"], classification="EVIDENCE",
                              root_origin=s["organisation"], provenance_valid=True)
                     for s in siblings[:3]] + [
                     Artifact(artifact_id=doc["doc_id"], classification="EVIDENCE",
                              root_origin=doc["organisation"], provenance_valid=True)]
            b3 = evaluate(Artifact(**base, authorization_valid=True,
                                   contains_instructions=has_instructions),
                          corroborating=corro).to_dict()

        out.append({
            "doc_id": doc["doc_id"], "organisation": doc["organisation"],
            "doc_type": doc["doc_type"],
            "schema_status_after_wrap": vr.status,
            "contains_instructions": has_instructions,
            "B1_no_declared_authorization": b1.to_dict(),
            "B2_self_declared_authorization": b2.to_dict(),
            "B3_same_org_corroboration": b3,
        })

    (HERE / "RESULTS_ARM_B.json").write_text(json.dumps(
        {"probes": {
            "B1": "everything measured; authorization_valid not declared",
            "B2": "identical, except the artifact declares authorization_valid=True",
            "B3": "B2 plus same-organisation documents offered as corroboration"},
         "documents": len(out), "results": out}, indent=2, sort_keys=True))

    import collections
    for probe in ("B1_no_declared_authorization", "B2_self_declared_authorization"):
        c = collections.Counter(r[probe]["verdict"] for r in out)
        print(f"{probe:34} {dict(c)}")
    c3 = collections.Counter(r["B3_same_org_corroboration"]["verdict"]
                             for r in out if r["B3_same_org_corroboration"])
    print(f"{'B3_same_org_corroboration':34} {dict(c3)}")
    inj = [r for r in out if r["contains_instructions"]]
    for r in inj:
        print(f"\n  instruction-bearing doc: {r['doc_id']}")
        print(f"    B1 -> {r['B1_no_declared_authorization']['verdict']}")
        print(f"    B2 -> {r['B2_self_declared_authorization']['verdict']}"
              f"  may_influence_runtime="
              f"{r['B2_self_declared_authorization']['may_influence_runtime']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
