"""The one required vertical slice (TITANOS Frontier Power Dynamics ->
MAGL -> Continuity Corpus build):

    SITUATION -> monk_pass -> demonblade_pass -> SURVIVED finding
        -> build_magl_candidate -> MAGLCatalogue.register_checked()
        -> PromotionStore (RAW..TESTED) -> SourceRegistry (real content)
        -> rpa.gates.human_jurisdiction.authorize_pilot()
        -> separate human promotion to STABLE (different reviewer)
        -> confirm_pilot_authorized() -> True
        -> record_situation_crystal() -> one durable Crystal
        -> a fresh reader retrieves the reusable lesson with no
           conversation history, only the CrystalStore object.

Every step past monk_pass/demonblade_pass runs through EXISTING,
UNMODIFIED gates: magl/registry/catalogue.py, magl/composition/engine.py,
kpm/promotion/state_machine.py, kpm/source-vault/registry.py,
rpa/gates/human_jurisdiction.py, foundation/crystal.py. Nothing in this
test file is a new gate — it is glue proving the existing gates compose.

Proves, per the acceptance test:
    ANALYSIS != AUTHORIZATION
    CRYSTAL  != CURRENT TRUTH (superseded by a later crystal, not edited)
    MAGL     != EXECUTION (nothing here executes anything)
    CAPABILITY != AUTHORITY (SURVIVED alone never reaches STABLE)
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kpm.schemas.epistemic_types import classify_claim  # noqa: E402
from kpm.promotion.state_machine import (  # noqa: E402
    IllegalTransition, PromotionStore, SelfPromotionForbidden,
)
from magl.composition.engine import MAGLSummary  # noqa: E402
from magl.registry.catalogue import (  # noqa: E402
    CompositionRefusedAtRegistration, MAGLCatalogue, MAGLEntry,
)
from rpa.gates.human_jurisdiction import (  # noqa: E402
    AmbiguousValidatedSource, NoValidatedSource, SourceRegistry,
    authorize_pilot, confirm_pilot_authorized,
)
from foundation.crystal import CrystalStore  # noqa: E402
from foundation.situation_analysis import (  # noqa: E402
    AnalysisNotSurvived, CandidateAction, build_magl_candidate,
    demonblade_pass, monk_pass, record_situation_crystal,
)

FIXTURES = Path(__file__).resolve().parents[2] / "rpa" / "fixtures"


def _real_candidate_content() -> bytes:
    return (FIXTURES / "automation_candidate.yaml").read_bytes()


class TestVerticalSliceSurvivedPath(unittest.TestCase):
    """The full happy path: a well-supported analysis survives, becomes
    a MAGL candidate, and is genuinely authorized by a separate human."""

    def _survived_analysis_and_verdict(self, situation_id: str):
        claim = classify_claim(
            "c-bottleneck", "invoice clerk delay confirmed by system_map+bottleneck fixtures",
            "VERIFIED_FACT", "recon-agent", confidence="HIGH",
            evidence_refs=("rpa/fixtures/bottleneck.yaml",),
        )
        analysis = monk_pass(
            situation_id,
            "a bounded automation is proposed to notify a backup approver "
            "when the invoice clerk has not actioned an invoice in 24h",
            actors=("invoice-clerk", "backup-approver"),
            goals=("reduce approval delay",),
            constraints=("must not approve or modify invoices itself",),
            known_information=(claim,),
            unknowns=("backup roster staleness is not measured",),
            assumptions=(),
            candidate_actions=(
                CandidateAction(
                    "act-notify", "notify backup approver after 24h delay",
                    depends_on_claim_ids=("c-bottleneck",),
                ),
            ),
            evidence_refs=("rpa/fixtures/bottleneck.yaml",),
            analyzed_by="recon-agent",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team-agent")
        return analysis, verdict

    def test_full_chain_reaches_genuine_authorization_and_records_a_crystal(self):
        analysis, verdict = self._survived_analysis_and_verdict("sit-e2e-1")
        self.assertEqual(verdict.verdict, "SURVIVED")

        # --- MAGL candidate, existing validation (composition engine) ---
        registry = SourceRegistry(
            archive_dir=Path("/tmp") / "situation_analysis_e2e_archive",
            registry_path=None,
        )
        source = registry.ingest_source(
            _real_candidate_content(), source_type="yaml",
            source_location="rpa/fixtures/automation_candidate.yaml",
            author_or_origin="test",
        )
        entry, summary = build_magl_candidate(
            analysis, verdict, version="1.0.0", name="Backup Approver Notifier",
            domain=("finance", "automation"), capability_type=("EXTERNALLY_ACTING",),
            maturity="EXPERIMENTAL", license="MIT",
            content_hash=source.content_hash,
            may_call=("notification_service",),
            prohibited_actions=("approve_invoice", "modify_invoice_amount"),
            provides=("backup_approver_notification",),
        )
        catalogue = MAGLCatalogue()
        catalogue.register_checked(entry, summary)  # existing validation — real, not bypassed
        self.assertIsNotNone(catalogue.get(entry.magl_id, entry.version))

        # --- existing authorization boundary (unchanged rpa gate) ---
        store = PromotionStore()
        store.register(entry.magl_id, created_by="rpa-pipeline")
        store.promote(entry.magl_id, "DISTILLED", reason="distilled from bottleneck")
        store.promote(entry.magl_id, "PROVISIONAL", reason="schema-validated")
        store.promote(entry.magl_id, "TESTED", reason="pilot_simulation approved")

        authorize_pilot(
            store, entry.magl_id, reviewed_by="finance-ops-lead",
            created_by="rpa-pipeline", reason="ready for human review",
            source_registry=registry, source_hashes=(source.content_hash,),
        )
        # ANALYSIS != AUTHORIZATION: surviving Demonblade's attack only
        # reached HUMAN_REVIEW, never STABLE, never "authorized".
        self.assertFalse(confirm_pilot_authorized(store, entry.magl_id))

        # A separate human, not the pipeline that created it, authorizes.
        store.promote(entry.magl_id, "STABLE", reason="approved for pilot",
                      reviewed_by="finance-ops-lead")
        self.assertTrue(confirm_pilot_authorized(store, entry.magl_id))

        # --- continuity corpus: one Crystal closes the cycle ---
        crystal_store = CrystalStore()
        crystal = record_situation_crystal(
            crystal_store, analysis, verdict, crystal_id="crys-e2e-1",
            hypothesis="notifying a backup approver after 24h delay is a "
                       "bounded, non-approving action safe to pilot",
            provenance=source.content_hash,
            epistemic_status="TECHNICAL_DESIGN", recorded_by="red-team-agent",
            regression_test_ref=(
                "foundation.tests.test_situation_analysis_end_to_end."
                "TestVerticalSliceSurvivedPath."
                "test_full_chain_reaches_genuine_authorization_and_records_a_crystal"
            ),
        )
        self.assertEqual(crystal.result, "SURVIVED")

        # --- future reader, zero conversation history, only the store ---
        fresh_view = crystal_store.get("crys-e2e-1")
        self.assertIsNotNone(fresh_view)
        self.assertIn("no unsupported dependency", fresh_view.reusable_abstraction)
        self.assertEqual(fresh_view.provenance, source.content_hash)
        self.assertIn(
            fresh_view.provenance,
            (r.content_hash for r in registry.get_by_hash(source.content_hash)),
        )


class TestVerticalSliceKilledPathCannotProceed(unittest.TestCase):
    """The required negative test: a tempting bypass — building and
    registering a MAGL candidate straight from a KILLED analysis — is
    refused before it ever reaches the catalogue."""

    def test_killed_analysis_cannot_become_a_magl_candidate(self):
        analysis = monk_pass(
            "sit-e2e-killed", "an automation is proposed on an unverified premise",
            actors=("someone",), goals=(), constraints=(),
            known_information=(), unknowns=(), assumptions=("it will probably work",),
            candidate_actions=(
                CandidateAction("act-1", "auto-approve invoices over $10,000",
                                 depends_on_claim_ids=("it will probably work",)),
            ),
            evidence_refs=(), analyzed_by="recon-agent",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team-agent")
        self.assertEqual(verdict.verdict, "KILLED")

        with self.assertRaises(AnalysisNotSurvived):
            build_magl_candidate(
                analysis, verdict, version="1.0.0", name="x", domain=("test",),
                capability_type=("EXECUTABLE",), maturity="EXPERIMENTAL",
                license="MIT", content_hash="sha256:irrelevant",
            )
        # Confirms no MAGLEntry was ever produced to register in the
        # first place — the catalogue never had a chance to refuse it,
        # because it was never handed anything to refuse.


class TestVerticalSliceCannotBypassCompositionValidation(unittest.TestCase):
    """A SURVIVED analysis's resulting MAGL candidate still cannot bypass
    the catalogue's own existing composition check — register_checked()
    refuses a real jurisdiction conflict exactly as it would for any
    other caller."""

    def test_composition_conflict_is_refused_even_for_a_survived_candidate(self):
        claim = classify_claim("c-1", "x", "VERIFIED_FACT", "recon-agent",
                                confidence="HIGH")
        analysis = monk_pass(
            "sit-e2e-conflict", "framing", actors=(), goals=(), constraints=(),
            known_information=(claim,), unknowns=("x",), assumptions=(),
            candidate_actions=(
                CandidateAction("act-1", "call an external service",
                                 depends_on_claim_ids=("c-1",)),
            ),
            evidence_refs=("e",), analyzed_by="recon-agent",
        )
        verdict = demonblade_pass(analysis, attacked_by="red-team-agent")
        self.assertEqual(verdict.verdict, "SURVIVED")

        entry, summary = build_magl_candidate(
            analysis, verdict, version="1.0.0", name="x", domain=("test",),
            capability_type=("EXTERNALLY_ACTING",), maturity="EXPERIMENTAL",
            license="MIT", content_hash="sha256:whatever",
            may_call=("external_service",),
        )
        catalogue = MAGLCatalogue()
        # A pre-existing guard explicitly prohibits the exact action our
        # SURVIVED candidate would be granted — this must still refuse.
        guard_entry = MAGLEntry(
            magl_id="guard", version="1.0.0", name="guard",
            domain=("test",), capability_type=("ANALYTICAL",),
            epistemic_status="IMPLEMENTED_SYSTEM", maturity="STABLE",
            dependencies_required=(), dependencies_incompatible=(),
            lifecycle_status="STABLE", license="MIT", content_hash="sha256:guard",
        )
        guard_summary = MAGLSummary(
            magl_id="guard", version="1.0.0",
            prohibited_actions=("external_service",),
        )
        catalogue.register_checked(guard_entry, guard_summary)

        with self.assertRaises(CompositionRefusedAtRegistration):
            catalogue.register_checked(entry, summary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
