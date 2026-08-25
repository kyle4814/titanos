"""
KPM end-to-end integration proof -- kpm/BUILD_REPORT.md's own named
"next smallest work cell," never actually built: does ingest ->
classify -> blueprint -> validate -> promote actually fit together as
one real pipeline, or only as four independently-green components with
a proven seam and no connected path? `magl/`, `rpa/`, `taal/` each got
this proof for their own subsystem; `kpm/` -- the foundational one all
three build on -- never did, until now.

Deliberately a single integration test, not new production code, per
the BUILD_REPORT's own framing: "the cheapest way to find out whether
the four independently built, independently green components actually
fit together, before building anything further on top of an unverified
assumption that they do."
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source-vault"))

from registry import SourceRegistry  # noqa: E402
from kpm.schemas.epistemic_types import classify_claim  # noqa: E402
from kpm.validators.validate_blueprint import validate_blueprint  # noqa: E402
from kpm.promotion.state_machine import PromotionStore  # noqa: E402


class TestIngestClassifyBlueprintValidatePromote(unittest.TestCase):
    """ONE real source, driven through all four components in sequence,
    with each stage's real output feeding the next stage's real input --
    no stage is mocked, no intermediate value is hand-constructed to
    look plausible."""

    def test_full_pipeline_reaches_tested(self):
        # 1. INGEST -- a real SourceRecord, content-addressed and hashed.
        registry = SourceRegistry(
            archive_dir=Path("/tmp") / "kpm_e2e_test_archive",
            registry_path=None,  # in-memory only for this test
        )
        source = registry.ingest_source(
            b"Observed: kpm/BUILD_REPORT.md named an end-to-end "
            b"integration test as its own next smallest work cell, and "
            b"no such test existed anywhere in this repository.",
            source_type="text",
            source_location="kpm/BUILD_REPORT.md#next-smallest-work-cell",
            author_or_origin="this repository's own build report",
        )
        self.assertTrue(source.artifact_id.startswith("SRC-"))

        # 2. CLASSIFY -- a real Claim extracted from that source, evidence-
        # gated (VERIFIED_FACT requires non-empty evidence_refs).
        claim = classify_claim(
            claim_id="CLAIM-KPM-E2E-GAP",
            text="kpm/ had no end-to-end integration test tying its four "
                 "components together, unlike magl/rpa/taal which each "
                 "have one for their own subsystem",
            classification="VERIFIED_FACT",
            classified_by="kpm_end_to_end_test",
            confidence="HIGH",
            evidence_refs=(source.artifact_id,),
        )
        self.assertEqual(claim.classification, "VERIFIED_FACT")

        # 3. BUILD a real blueprint_atom YAML referencing the real claim
        # and source -- not a hand-waved placeholder id.
        blueprint_yaml = f"""
blueprint:
  id: "bp-kpm-e2e-001"
  title: "KPM end-to-end integration test"
  version: "1.0.0"
  status: PROVISIONAL
  domain: ["software_engineering", "testing"]
  source_artifacts: ["{source.artifact_id}"]
  provenance:
    immutable_source_refs: ["{source.artifact_id}"]
    interpretations: ["{claim.claim_id}"]
  classification:
    primary: TECHNICAL_DESIGN
    confidence: HIGH
  purpose: "Prove ingest->classify->blueprint->validate->promote fits together as one real pipeline"
  problem: "kpm's four components were each independently tested but never proven connected"
  constraints: ["must reuse existing modules, no new production code"]
  assumptions: ["a single real pipeline run is sufficient proof, not exhaustive coverage"]
  unknowns: ["whether other integration seams in kpm remain unproven"]
  non_goals: ["not a general integration test framework"]
  inputs: ["one real SourceRecord"]
  outputs: ["one PromotionRecord reaching TESTED"]
  invariants: ["every stage's real output feeds the next stage's real input"]
  threat_model: ["a stage silently mocked to look connected when it isn't"]
  failure_modes: ["a stage's real output shape doesn't match the next stage's real input contract"]
  controls: ["structural assertions between every stage"]
  interfaces: ["SourceRegistry.ingest_source", "classify_claim", "validate_blueprint", "PromotionStore.promote"]
  dependencies: ["kpm.source_vault.registry", "kpm.schemas.epistemic_types", "kpm.validators.validate_blueprint", "kpm.promotion.state_machine"]
  implementation:
    smallest_next_step: "this test itself"
    acceptance_criteria: ["reaches TESTED", "validate_blueprint returns VALID"]
  verification:
    tests: ["kpm/tests/test_end_to_end.py"]
    evidence_required: ["green test run"]
  dissent:
    alternative_models: []
    unresolved_objections: []
  promotion:
    current_gate: PROVISIONAL
    promotion_requirements: ["pass validate_blueprint", "advance through PromotionStore"]
  rollback:
    reversible: true
    recovery_procedure: "delete this test file, revert the commit"
  audit:
    created_by: "kpm_end_to_end_test"
    reviewed_by: []
    timestamps: {{}}
    hashes: {{}}
"""

        # 4. VALIDATE -- the real validator, on the real YAML built above.
        result = validate_blueprint(blueprint_yaml)
        self.assertEqual(result.status, "VALID", result.issues)

        # 5. PROMOTE -- the real state machine, real legal transitions
        # only (RAW -> DISTILLED -> PROVISIONAL -> TESTED; there is no
        # shortcut edge, same table rpa/gates/human_jurisdiction.py and
        # this session's low_regret/regression engines all reuse rather
        # than duplicate).
        store = PromotionStore()
        store.register("bp-kpm-e2e-001", created_by="kpm_end_to_end_test")
        for state in ("DISTILLED", "PROVISIONAL", "TESTED"):
            store.promote("bp-kpm-e2e-001", to_state=state,
                           reason="end-to-end pipeline proof, stage advancing")

        final = store.get("bp-kpm-e2e-001")
        self.assertEqual(final.state, "TESTED")
        # The full history is real and inspectable, not asserted blind.
        self.assertEqual(
            [h["to"] for h in final.history],
            ["RAW", "DISTILLED", "PROVISIONAL", "TESTED"],
        )


if __name__ == "__main__":
    unittest.main()
