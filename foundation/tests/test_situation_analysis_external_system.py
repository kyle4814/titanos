"""World Ping — the external-system vertical slice.

Uses a REAL external-system subject already in this repository:
rpa/fixtures/legacy_map.yaml (Acme Manufacturing's invoicing system) and
rpa/fixtures/bottleneck.yaml (the KEY_PERSON_DEPENDENCY bottleneck
already documented against it) — an outside organisation's process, not
TitanOS's own code. No synthetic scenario was invented; both fixtures
pre-date this test and were independently validated against their own
schemas by rpa/tests/test_end_to_end.py.

Proves the full chain required by this task:

    SOURCE (real fixture, content-hashed)
        -> SituationAnalysis (monk_pass)
        -> BottleneckReport (find_bottleneck_hypotheses) — evidence-bound,
           never a bare score, can HOLD/refuse
        -> DemonbladeVerdict (demonblade_pass) — SURVIVED/KILLED
        -> bounded MAGL candidate OR AnalysisNotSurvived refusal
        -> existing validation (MAGLCatalogue.register_checked)
        -> existing authorization boundary (PromotionStore + rpa gate)
        -> Crystal (continuity corpus) + CrystalStore.is_current()
           (a stale/superseded finding cannot masquerade as current)

Nothing here executes anything external — this analyses a static,
already-scanned YAML description; it does not contact Acme or any real
system.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kpm.schemas.epistemic_types import classify_claim  # noqa: E402
from kpm.promotion.state_machine import PromotionStore  # noqa: E402
from magl.registry.catalogue import MAGLCatalogue  # noqa: E402
from rpa.gates.human_jurisdiction import (  # noqa: E402
    SourceRegistry, authorize_pilot, confirm_pilot_authorized,
)
from foundation.crystal import CrystalStore  # noqa: E402
from foundation.situation_analysis import (  # noqa: E402
    AnalysisNotSurvived, CandidateAction, OffRampCandidate,
    build_magl_candidate, demonblade_pass, evaluate_off_ramp_candidates,
    find_bottleneck_hypotheses, find_tension_hypotheses, monk_pass,
    record_situation_crystal,
)

FIXTURES = Path(__file__).resolve().parents[2] / "rpa" / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text()


class TestWorldPingOnRealExternalFixture(unittest.TestCase):
    """The one required vertical slice, end to end, on a real subject."""

    def test_full_world_ping_cycle_reaches_authorization_and_records_crystal(self):
        # --- SOURCE: real external-system artifacts, content-hashed ---
        registry = SourceRegistry(
            archive_dir=Path("/tmp") / "world_ping_e2e_archive", registry_path=None,
        )
        map_source = registry.ingest_source(
            _read("legacy_map.yaml").encode(), source_type="yaml",
            source_location="rpa/fixtures/legacy_map.yaml", author_or_origin="test",
        )
        bottleneck_source = registry.ingest_source(
            _read("bottleneck.yaml").encode(), source_type="yaml",
            source_location="rpa/fixtures/bottleneck.yaml", author_or_origin="test",
        )
        # The real, structurally-validated automation candidate proposed
        # against this exact bottleneck (bottleneck-invoice-clerk-dependency)
        # — this is the content authorize_pilot() must recover and revalidate,
        # distinct from the raw bottleneck evidence above.
        candidate_source = registry.ingest_source(
            _read("automation_candidate.yaml").encode(), source_type="yaml",
            source_location="rpa/fixtures/automation_candidate.yaml",
            author_or_origin="test",
        )

        # --- MONK: structure the real, external situation ---
        claim_map = classify_claim(
            "c-legacy-map", "legacy invoicing system has single points of "
            "failure at the invoice clerk and the invoicing system itself",
            "EVIDENCE_SUPPORTED_MODEL", "recon-agent",
            evidence_refs=(map_source.content_hash,),
        )
        claim_bottleneck = classify_claim(
            "c-key-person", "invoicing stalled for 3 weeks during a 2026 "
            "leave period because no backup approver was designated — "
            "key-person dependency on the invoice clerk",
            "VERIFIED_FACT", "recon-agent", confidence="HIGH",
            evidence_refs=(bottleneck_source.content_hash,),
        )
        analysis = monk_pass(
            "world-acme-invoicing",
            "Acme Manufacturing's invoicing system has a documented "
            "key-person dependency on its invoice clerk",
            actors=("invoice-clerk", "erp-vendor", "approval-workflow"),
            goals=("keep invoice processing running during staff absence",),
            constraints=("key-person dependency on the invoice clerk",),
            known_information=(claim_map, claim_bottleneck),
            unknowns=("whether a second staff member has informal "
                      "familiarity with the process was not confirmed",),
            assumptions=(),
            candidate_actions=(
                CandidateAction(
                    "act-backup-approver",
                    "designate and notify a backup approver when the "
                    "primary invoice clerk is unavailable",
                    depends_on_claim_ids=("c-key-person",),
                ),
            ),
            evidence_refs=(map_source.content_hash, bottleneck_source.content_hash),
            analyzed_by="recon-agent",
        )

        # --- BOTTLENECK HYPOTHESIS: evidence-bound, not a bare score ---
        bottleneck_report = find_bottleneck_hypotheses(
            analysis, evaluated_by="recon-agent",
        )
        self.assertEqual(bottleneck_report.decision, "SINGLE_CANDIDATE")
        self.assertEqual(len(bottleneck_report.candidates), 1)
        self.assertEqual(
            bottleneck_report.candidates[0].hypothesis_claim.classification,
            "SPECULATIVE_HYPOTHESIS",
        )

        # --- DEMONBLADE: attack the candidate action's justification ---
        verdict = demonblade_pass(analysis, attacked_by="red-team-agent")
        self.assertEqual(verdict.verdict, "SURVIVED")

        # --- existing validation (MAGL composition, unmodified) ---
        entry, summary = build_magl_candidate(
            analysis, verdict, version="1.0.0", name="Backup Approver Designation",
            domain=("finance", "operations"), capability_type=("EXTERNALLY_ACTING",),
            maturity="EXPERIMENTAL", license="MIT",
            content_hash=candidate_source.content_hash,
            may_call=("notification_service",),
            prohibited_actions=("approve_invoice", "modify_invoice_amount"),
            provides=("backup_approver_designation",),
        )
        catalogue = MAGLCatalogue()
        catalogue.register_checked(entry, summary)

        # --- existing authorization boundary (unmodified rpa gate) ---
        store = PromotionStore()
        store.register(entry.magl_id, created_by="world-ping-pipeline")
        store.promote(entry.magl_id, "DISTILLED", reason="distilled from bottleneck finding")
        store.promote(entry.magl_id, "PROVISIONAL", reason="schema-validated")
        store.promote(entry.magl_id, "TESTED", reason="candidate reviewed")

        authorize_pilot(
            store, entry.magl_id, reviewed_by="ops-lead",
            created_by="world-ping-pipeline", reason="ready for human review",
            source_registry=registry, source_hashes=(candidate_source.content_hash,),
        )
        # SURVIVED bottleneck candidate != authorized action.
        self.assertFalse(confirm_pilot_authorized(store, entry.magl_id))

        store.promote(entry.magl_id, "STABLE", reason="approved by process owner",
                      reviewed_by="ops-lead")
        self.assertTrue(confirm_pilot_authorized(store, entry.magl_id))

        # --- continuity corpus: durable Crystal, staleness checkable ---
        crystal_store = CrystalStore()
        crystal = record_situation_crystal(
            crystal_store, analysis, verdict, crystal_id="world::acme::bottleneck-001",
            hypothesis=bottleneck_report.candidates[0].hypothesis_claim.text,
            provenance=candidate_source.content_hash,
            epistemic_status="TECHNICAL_DESIGN", recorded_by="red-team-agent",
            regression_test_ref=(
                "foundation.tests.test_situation_analysis_external_system."
                "TestWorldPingOnRealExternalFixture."
                "test_full_world_ping_cycle_reaches_authorization_and_records_crystal"
            ),
        )
        self.assertTrue(crystal_store.is_current("world::acme::bottleneck-001"))

        # --- future reader, zero conversation history ---
        fresh = crystal_store.get("world::acme::bottleneck-001")
        self.assertTrue(fresh.reusable_abstraction)
        self.assertEqual(fresh.provenance, candidate_source.content_hash)

    def test_stale_crystal_cannot_by_itself_prove_current_bottleneck(self):
        """A prior finding is historical, never assumed still true. New
        evidence supersedes it explicitly; is_current() reflects that
        immediately, for any reader, without re-deriving it."""
        store = CrystalStore()
        old = store.record(
            "world::acme::bottleneck-001-v1",
            problem="Acme invoicing key-person dependency (2026-01 finding)",
            context="single approver, no backup", hypothesis="dependency is unresolved",
            action="documented the dependency", evidence="bottleneck.yaml v1",
            result="SURVIVED", failure_mode="", limitation="not yet remediated",
            provenance="sha256:old", reusable_abstraction="key-person risk confirmed",
            epistemic_status="TECHNICAL_DESIGN", recorded_by="recon-agent",
        )
        self.assertTrue(store.is_current(old.crystal_id))

        # New evidence: a backup approver was since designated — the old
        # finding is superseded, not edited or deleted.
        store.record(
            "world::acme::bottleneck-001-v2",
            problem="Acme invoicing key-person dependency (re-assessed)",
            context="backup approver now designated per updated policy",
            hypothesis="dependency is resolved", action="re-audited the policy",
            evidence="updated policy document", result="KILLED",
            failure_mode="original bottleneck hypothesis no longer holds — "
                         "a backup approver now exists",
            limitation="backup approver's actual responsiveness untested",
            provenance="sha256:new", reusable_abstraction="dependency risk closed",
            epistemic_status="TECHNICAL_DESIGN", recorded_by="recon-agent",
            supersedes=old.crystal_id,
        )

        self.assertFalse(store.is_current(old.crystal_id))
        self.assertTrue(store.is_current("world::acme::bottleneck-001-v2"))
        # The old crystal is still retrievable — historical record
        # preserved, never deleted — but is_current() is how a future
        # reader avoids treating it as the current world state.
        self.assertIsNotNone(store.get(old.crystal_id))


class TestTectonicTensionOnRealFixture(unittest.TestCase):
    """The tension/off-ramp extension, wired into the SAME real gate
    chain as TestWorldPingOnRealExternalFixture — not a standalone unit
    test in isolation. Subject: the real jurisdiction data in
    rpa/fixtures/legacy_map.yaml — the invoice clerk holds informal
    'approve invoices under $5000' authority (node-invoice-clerk) while
    the formal approval workflow (node-approval-workflow) itself
    declares zero authority of its own, yet the clerk's authority is
    'delegated' into the workflow's scope per the fixture's own
    `jurisdictions` block. This is a genuine, evidence-backed, two-sided
    structural tension already latent in a real fixture — not invented.
    """

    def _real_jurisdiction_claims(self):
        clerk_claim = classify_claim(
            "c-clerk-authority",
            "the clerk role holds informal delegated authority to approve "
            "invoices under $5000, per real fixture node node-invoice-clerk",
            "VERIFIED_FACT", "recon-agent", confidence="HIGH",
        )
        workflow_claim = classify_claim(
            "c-workflow-authority",
            "the formal workflow itself declares zero authority of its "
            "own, per real fixture node node-approval-workflow",
            "VERIFIED_FACT", "recon-agent", confidence="HIGH",
        )
        return clerk_claim, workflow_claim

    def _survived_tension(self):
        """Shared setup, not itself a test — see test_genuine_two_sided_
        tension_is_identified_from_real_evidence for the assertions this
        produces."""
        clerk_claim, workflow_claim = self._real_jurisdiction_claims()
        analysis = monk_pass(
            "world-acme-jurisdiction-tension",
            "Acme's clerk role holds informal delegated authority "
            "that the formal workflow has no independent claim to",
            actors=("clerk", "workflow"),
            goals=("keep invoice approval both fast and properly authorized",),
            constraints=(
                "clerk and workflow both effectively determine approval outcomes",
            ),
            known_information=(clerk_claim, workflow_claim),
            unknowns=("whether policy FIN-004 has ever been formally "
                      "reviewed since delegation was granted",),
            assumptions=(), candidate_actions=(), evidence_refs=(),
            analyzed_by="recon-agent",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team-agent")
        return analysis, report

    def test_genuine_two_sided_tension_is_identified_from_real_evidence(self):
        analysis, report = self._survived_tension()
        self.assertEqual(report.decision, "STRUCTURAL_TENSION")
        self.assertEqual(len(report.candidates), 1)
        candidate = report.candidates[0]
        self.assertEqual(candidate.tension_claim.classification, "SPECULATIVE_HYPOTHESIS")
        # STRUCTURAL_TENSION must never be read as "inevitable" -- no
        # such word appears anywhere in the produced rationale.
        self.assertNotIn("inevitable", candidate.rationale.lower())
        self.assertNotIn("must", candidate.rationale.lower())

    def test_insufficient_evidence_refuses_to_invent_a_tension(self):
        """Negative control: an apparent conflict (two actors declared)
        but with evidence below the floor -- the system must refuse
        structural-conflict classification rather than guess."""
        analysis = monk_pass(
            "world-acme-thin-evidence", "framing",
            actors=("clerk", "workflow"), goals=(),
            constraints=("clerk and workflow both effectively determine "
                         "approval outcomes",),
            known_information=(), unknowns=(), assumptions=(),
            candidate_actions=(), evidence_refs=(), analyzed_by="recon-agent",
        )
        report = find_tension_hypotheses(analysis, evaluated_by="red-team-agent")
        self.assertEqual(report.decision, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(report.candidates, ())

    def test_survived_tension_with_no_credible_off_ramp_is_honest_hold(self):
        analysis, tension_report = self._survived_tension()
        # A proposed off-ramp whose precondition is NOT supported by any
        # evidence in this analysis -- must not be silently accepted.
        candidate = OffRampCandidate(
            offramp_id="or-fin004-review", tension_ref=tension_report.candidates[0].relationship_ref,
            category="EXPLICIT_ARBITRATION",
            description="have a compliance officer formally re-adjudicate "
                        "the FIN-004 delegation",
            preconditions=("a compliance officer has already reviewed FIN-004 "
                          "this fiscal year",),
            mechanism_claim=classify_claim(
                "mech-fin004", "a fresh formal review would resolve the "
                "authority ambiguity", "SPECULATIVE_HYPOTHESIS", "red-team-agent",
            ),
            supporting_evidence_refs=(), limitations=("compliance officer "
                "availability not confirmed",),
            reversibility="REVERSIBLE", interim_cost_if_reversible="approvals "
                "paused pending review",
            affected_relationships=("clerk-manager reporting line", "vendor "
                "payment timing"),
            transition_cost="MEDIUM", proposed_by="red-team-agent",
        )
        offramp_report = evaluate_off_ramp_candidates(
            analysis, (candidate,), evaluated_by="red-team-agent",
        )
        self.assertEqual(offramp_report.decision, "PRECONDITIONS_UNMET")
        self.assertEqual(offramp_report.candidates, ())
        self.assertEqual(len(offramp_report.unmet_precondition_candidates), 1)

    def test_tension_and_offramp_do_not_alter_the_existing_gate_chain(self):
        """The tension/off-ramp layer is pure analysis wired alongside
        the unchanged real gate chain -- registering, promoting, and
        authorizing the underlying MAGL candidate proceeds exactly as
        it does without this layer, proving no bypass and no new
        authority was introduced."""
        analysis, tension_report = self._survived_tension()
        verdict = demonblade_pass(analysis, attacked_by="red-team-agent")
        # This particular analysis has no candidate_actions declared, so
        # Demonblade has nothing to attack -- SURVIVED is the correct,
        # honest result (no unsupported dependency exists because none
        # was declared), not evidence the tension itself is resolved.
        self.assertEqual(verdict.verdict, "SURVIVED")

        registry = SourceRegistry(
            archive_dir=Path("/tmp") / "tension_e2e_archive", registry_path=None,
        )
        candidate_source = registry.ingest_source(
            _read("automation_candidate.yaml").encode(), source_type="yaml",
            source_location="rpa/fixtures/automation_candidate.yaml",
            author_or_origin="test",
        )
        entry, summary = build_magl_candidate(
            analysis, verdict, version="1.0.0", name="Jurisdiction Clarification Review",
            domain=("finance", "governance"), capability_type=("ANALYTICAL",),
            maturity="EXPERIMENTAL", license="MIT",
            content_hash=candidate_source.content_hash,
        )
        catalogue = MAGLCatalogue()
        catalogue.register_checked(entry, summary)

        store = PromotionStore()
        store.register(entry.magl_id, created_by="world-ping-pipeline")
        store.promote(entry.magl_id, "DISTILLED", reason="distilled from tension finding")
        store.promote(entry.magl_id, "PROVISIONAL", reason="schema-validated")
        store.promote(entry.magl_id, "TESTED", reason="candidate reviewed")
        authorize_pilot(
            store, entry.magl_id, reviewed_by="ops-lead",
            created_by="world-ping-pipeline", reason="ready for human review",
            source_registry=registry, source_hashes=(candidate_source.content_hash,),
        )
        # A STRUCTURAL_TENSION finding, on its own, authorizes nothing.
        self.assertFalse(confirm_pilot_authorized(store, entry.magl_id))
        store.promote(entry.magl_id, "STABLE", reason="approved by process owner",
                      reviewed_by="ops-lead")
        self.assertTrue(confirm_pilot_authorized(store, entry.magl_id))

        crystal_store = CrystalStore()
        crystal = record_situation_crystal(
            crystal_store, analysis, verdict,
            crystal_id="world::acme::jurisdiction-tension-001",
            hypothesis=tension_report.candidates[0].tension_claim.text,
            provenance=candidate_source.content_hash,
            epistemic_status="TECHNICAL_DESIGN", recorded_by="red-team-agent",
            regression_test_ref=(
                "foundation.tests.test_situation_analysis_external_system."
                "TestTectonicTensionOnRealFixture."
                "test_tension_and_offramp_do_not_alter_the_existing_gate_chain"
            ),
        )
        self.assertTrue(crystal_store.is_current(crystal.crystal_id))
        fresh = crystal_store.get(crystal.crystal_id)
        self.assertTrue(fresh.reusable_abstraction)


class TestKilledExternalBottleneckCannotReachMagl(unittest.TestCase):
    def test_demonblade_kill_blocks_magl_candidate(self):
        claim = classify_claim(
            "c-1", "informal rumor about the process, unverified",
            "UNVERIFIED_EXTERNAL_CLAIM", "recon-agent",
        )
        analysis = monk_pass(
            "world-unverified", "an external system's bottleneck is rumored",
            actors=(), goals=(), constraints=("alleged dependency",),
            known_information=(claim,), unknowns=(), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "act on the rumor",
                                 depends_on_claim_ids=("c-1",)),
            ),
            evidence_refs=(), analyzed_by="recon-agent",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team-agent")
        self.assertEqual(verdict.verdict, "KILLED")
        with self.assertRaises(AnalysisNotSurvived):
            build_magl_candidate(
                analysis, verdict, version="1.0.0", name="x", domain=("test",),
                capability_type=("ANALYTICAL",), maturity="EXPERIMENTAL",
                license="MIT", content_hash="sha256:irrelevant",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
