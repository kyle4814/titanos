"""
Historical findings — the one honest bridge from a real, already-fixed
repository finding into ContradictionRegistry.

WHY THIS FILE EXISTS, AND WHY IT DOES NOT TOUCH situation_analysis.py

Three independent recon passes (2026-08-26, this session) converged on
the same finding: `demonblade_pass()`'s `contradiction_candidates`
(foundation/situation_analysis.py) are single-sided "action depends on
an unsupported/unevidenced claim" findings — never two claims that
CANNOT BOTH BE TRUE, which is `ContradictionRegistry`'s own documented
definition of a contradiction (kpm/contradictions/registry.py's module
docstring). Wiring `demonblade_pass()`'s raw output directly into
`ContradictionRegistry.record()` would misuse the registry's own
semantics — semantic laundering, not a real bridge. That composition
was explicitly attacked and rejected; `demonblade_pass()` remains
completely unmodified and unwired to this file.

`ContradictionRegistry.record()` genuinely has zero real non-test
callers anywhere in this repository (confirmed by repeated grep). The
one real subject this repository actually has that DOES fit the
registry's own definition — two claims that cannot both be true, with
real evidence, not fabricated — is this session's own already-fixed RPA
validation-transfer finding:

  CLAIM A (the design intent `authorize_pilot()` was built to satisfy):
    a candidate queued for pilot review is backed by real, structurally
    validated automation-candidate content.

  CLAIM B (the observed pre-fix behaviour, real and reproduced):
    before 2026-08-26, `authorize_pilot()` accepted any `candidate_id`
    string with zero connection to validated content — see
    `rpa/ADOPT.md`'s Threat Model and Changelog, and the real regression
    test `test_arbitrary_magl_id_with_no_validated_source_is_refused`
    (rpa/tests/test_end_to_end.py) which proves the bypass this
    contradiction records is now closed.

These two claims cannot both be true of the same shipped design — which
is exactly what `ContradictionRegistry` means by "contradiction." The
`evidence_refs` passed to `resolve()` below cite the real commit
history, file, and test name — nothing here is invented to make a test
pass.

WHAT THIS FILE DOES NOT DO

Does not call `PromotionStore.promote()` — recording and resolving this
contradiction changes only `ContradictionRegistry` state. Whether the
pre-fix design's tracked blueprint (if one is registered in a
`PromotionStore`) gets downgraded is a separate, explicit decision left
entirely to `foundation.regression_engine.check_for_regression()` and
whatever caller acts on its proposal — this file never makes that call
itself.
"""

from __future__ import annotations

from kpm.contradictions.registry import ContradictionRecord, ContradictionRegistry

__all__ = [
    "RPA_PRE_FIX_BLUEPRINT_ID",
    "RPA_DESIGN_INTENT_CLAIM_ID",
    "RPA_VALIDATION_BYPASS_CONTRADICTION_ID",
    "record_rpa_validation_bypass_finding",
]

# Two distinct identifiers, per ContradictionRegistry.record()'s own
# >=2 involved_ids requirement — not two names for the same thing.
RPA_PRE_FIX_BLUEPRINT_ID = "rpa-human-jurisdiction-authorize-pilot-pre-fix-design"
RPA_DESIGN_INTENT_CLAIM_ID = "rpa-human-jurisdiction-authorize-pilot-design-intent"
RPA_VALIDATION_BYPASS_CONTRADICTION_ID = "rpa-validation-transfer-bypass-2026-08-26"


def record_rpa_validation_bypass_finding(
    registry: ContradictionRegistry, *, resolved_by: str,
) -> ContradictionRecord:
    """Record, then immediately resolve with real evidence, the one
    genuine two-claim contradiction this repository's own history
    actually contains. Never automatic, never invoked by
    `demonblade_pass()` or any analysis pipeline — an explicit,
    one-time, caller-invoked historical record.

    Raises `ValueError` if called twice (the underlying `record()`
    rejects a duplicate `contradiction_id`) — this finding happened
    once and is recorded once, not re-derived per call.
    """
    registry.record(
        RPA_VALIDATION_BYPASS_CONTRADICTION_ID,
        "authorize_pilot()'s pre-fix behaviour (any candidate_id queued "
        "for review with zero connection to validated content) "
        "contradicts its own design intent (only structurally validated "
        "candidate content may be queued for pilot review) — both "
        "cannot be true of the same shipped design.",
        (RPA_PRE_FIX_BLUEPRINT_ID, RPA_DESIGN_INTENT_CLAIM_ID),
    )
    return registry.resolve(
        RPA_VALIDATION_BYPASS_CONTRADICTION_ID,
        "fixed 2026-08-26: authorize_pilot() now requires "
        "source_registry/source_hashes and revalidates fresh via "
        "validate_automation_candidate() before queueing anything, "
        "closing the gap this contradiction records.",
        evidence_refs=(
            "rpa/gates/human_jurisdiction.py::authorize_pilot",
            "rpa/tests/test_end_to_end.py::TestHumanAuthorizationGate::"
            "test_arbitrary_magl_id_with_no_validated_source_is_refused",
            "rpa/ADOPT.md#changelog",
        ),
        resolved_by=resolved_by,
    )
