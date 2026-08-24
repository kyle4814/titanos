"""
TitanOS Epistemic Firewall — the rejection engine.

THE ONE JOB

Prevent unverified ideas from silently acquiring machine authority.

Not: decide which ideas are true. Not: decide which ideas anyone may
believe. The gate is narrower and therefore stronger — it governs what may
reach RUNTIME POLICY, and nothing else. An artifact refused here is still
readable, still archived, still arguable. It simply cannot govern.

WHY IT IS BORING ON PURPOSE

Every decision below is a deterministic predicate over declared metadata.
There is no model, no scoring function, no learned classifier anywhere in
this file. A reviewer must be able to read a refusal and see exactly which
predicate failed. A "truth detector" that cannot be audited is a worse
authority than the narratives it screens.

THE INVERSION THAT MATTERS

Persuasiveness, repetition, emotional force and agent agreement do not
increase authority. In this engine they are RISK SIGNALS: the more
compelling an artifact is, the more separation it gets from executable
power, because compelling material is exactly what bypasses review. That
is deliberately the opposite of how attention economies work.

WHAT THIS CANNOT DO — stated, not buried

It classifies DECLARED metadata. It cannot detect an artifact that lies
about itself. A hostile author who marks narrative as EVIDENCE and forges
provenance defeats the metadata layer entirely; only provenance
verification and independent corroboration catch that, and both live
outside this file. This gate is one layer, not a guarantee, and a green
result from it means "cleared this gate", never "true".
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "Classification", "ContaminationState", "Decision", "Artifact",
    "AUTHORIZED_RUNTIME_CLASSES", "evaluate", "collapse_ancestry",
]

# ─────────────────────────────────────────────────────────────
# Vocabulary
# ─────────────────────────────────────────────────────────────

Classification = str
ALL_CLASSIFICATIONS = frozenset({
    "FACTUAL_CLAIM", "EVIDENCE", "INFERENCE", "HYPOTHESIS", "SPECULATION",
    "PHILOSOPHY", "METAPHOR", "MYTH", "NARRATIVE", "VALUE_JUDGMENT",
    "GOVERNANCE_RULE", "CONSTITUTIONAL_RULE", "EXECUTABLE_POLICY",
    "UNKNOWN", "CONTAMINATED",
})

# The allowlist. Deliberately tiny.
#
# NARRATIVE, MYTH, METAPHOR, PHILOSOPHY and VALUE_JUDGMENT are absent by
# design — not because they are worthless (they are often the most
# valuable material in the library) but because their value is
# interpretive, and interpretation must not execute. SPECULATION and
# HYPOTHESIS are absent because they are explicitly unverified. UNKNOWN is
# absent because uncertainty must never be resolved in favour of action.
AUTHORIZED_RUNTIME_CLASSES = frozenset({
    "CONSTITUTIONAL_RULE", "GOVERNANCE_RULE", "EXECUTABLE_POLICY", "EVIDENCE",
})

ContaminationState = str
TERMINAL_BLOCKING_STATES = frozenset({
    "CONTAMINATED", "QUARANTINED", "REJECTED", "SUSPICIOUS",
})

# Verdicts this engine may return. REFUSED and QUARANTINED are SUCCESS
# states: the system correctly declined to grant authority.
VERDICTS = ("AUTHORIZED", "REFUSED", "QUARANTINED", "REQUIRES_HUMAN_REVIEW")


@dataclass(frozen=True)
class Artifact:
    """An inbound artifact and the metadata it declares about itself."""
    artifact_id: str
    classification: Classification
    contamination_state: ContaminationState = "UNVERIFIED"
    schema_valid: bool = False
    provenance_valid: bool = False
    authorization_valid: bool = False
    # Origin lineage — used to collapse common ancestry (see §12).
    root_origin: str | None = None
    parent_origins: tuple[str, ...] = ()
    # AI-generated artifacts can never self-authorize (see §11).
    generated_by_agent: bool = False
    independently_confirmed_by: tuple[str, ...] = ()
    # Risk indicators, NOT truth measurements (see §7).
    memetic_profile: Mapping[str, int] = field(default_factory=dict)
    # Instructions arriving as content are DATA until authorized (see §14).
    contains_instructions: bool = False


@dataclass
class Decision:
    verdict: str
    artifact_id: str
    reasons: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    may_influence_runtime: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────
# Ancestry collapse (§12)
# ─────────────────────────────────────────────────────────────

def collapse_ancestry(artifacts: Sequence[Artifact]) -> int:
    """Count DISTINCT epistemic origins, not artifacts.

    Five agents restating one contaminated specification are five
    artifacts and ONE origin. Counting artifacts is how a system talks
    itself into false corroboration, so independence is measured by root
    origin and nothing else.

    An artifact declaring no root_origin counts as its own origin — the
    conservative reading, since an unknown origin might be shared.
    """
    origins = {a.root_origin or a.artifact_id for a in artifacts}
    return len(origins)


# ─────────────────────────────────────────────────────────────
# The gate
# ─────────────────────────────────────────────────────────────

def _memetic_flags(p: Mapping[str, int]) -> list[str]:
    """Surface high-risk rhetorical signatures. These NEVER authorize.

    They exist to route compelling material toward review, and to make the
    reason legible in the record. A high score is not a claim of falsehood —
    persuasive things are often true — it is a claim that this artifact
    should not slip past a human on momentum alone.
    """
    flags: list[str] = []
    def hi(k: str, t: int = 70) -> bool:
        return int(p.get(k, 0)) >= t
    if hi("authority_claim"):
        flags.append("asserts its own authority")
    if hi("inevitability_claim"):
        flags.append("asserts inevitability or destiny")
    if hi("self_reference"):
        flags.append("high self-reference (possible system mythology)")
    if hi("identity_binding"):
        flags.append("binds identity to belief")
    if hi("dissent_suppression_signal", 50):
        flags.append("signals suppression of dissent")
    if hi("dehumanization_signal", 30):
        flags.append("dehumanization signal")
    if hi("emotional_intensity", 80):
        flags.append("very high emotional intensity")
    if hi("persuasion_intensity", 80):
        flags.append("very high persuasive intensity")
    return flags


def evaluate(artifact: Artifact, *, corroborating: Iterable[Artifact] = ()) -> Decision:
    """Decide whether an artifact may influence runtime policy.

    Ordered simple switches. First failure wins, and the reason is
    recorded. Refusal is a success state.
    """
    d = Decision(verdict="REFUSED", artifact_id=artifact.artifact_id)
    d.risk_flags = _memetic_flags(artifact.memetic_profile)

    # --- structural gates ---------------------------------------------
    if artifact.classification not in ALL_CLASSIFICATIONS:
        d.reasons.append(
            f"unrecognised classification '{artifact.classification}'. Unknown "
            f"classes are refused, never defaulted — defaulting is how "
            f"unclassified material acquires authority."
        )
        return d

    if artifact.contamination_state in TERMINAL_BLOCKING_STATES:
        d.verdict = "QUARANTINED"
        d.reasons.append(
            f"contamination_state is {artifact.contamination_state}. No "
            f"automatic transition to AUTHORIZED exists. Artifact preserved, "
            f"not deleted."
        )
        return d

    if not artifact.schema_valid:
        d.reasons.append("schema invalid — malformed input never executes.")
        return d

    if not artifact.provenance_valid:
        d.verdict = "QUARANTINED"
        d.reasons.append(
            "provenance could not be established. Unverifiable origin is "
            "quarantined for review, not discarded and not trusted."
        )
        return d

    # --- prompt-injection boundary (§14) ------------------------------
    # Parsing an instruction is not authorization to execute it. Content
    # arriving from READMEs, issues, datasets, comments or model output is
    # DATA. This is the single most common real-world path from "text the
    # system read" to "behaviour the system performed".
    if artifact.contains_instructions and not artifact.authorization_valid:
        d.verdict = "REQUIRES_HUMAN_REVIEW"
        d.reasons.append(
            "artifact contains instructions but carries no authorization. "
            "Imported instructions are DATA until explicitly authorized; "
            "parsing is not permission."
        )
        return d

    # --- classification allowlist (§10) -------------------------------
    if artifact.classification not in AUTHORIZED_RUNTIME_CLASSES:
        d.reasons.append(
            f"classification '{artifact.classification}' is not runtime-"
            f"authorized. It may be read, cited, archived and argued with — "
            f"it may not govern. Interpretation does not execute."
        )
        return d

    # --- agents cannot self-authorize (§11) ---------------------------
    if artifact.generated_by_agent and not artifact.independently_confirmed_by:
        d.verdict = "REQUIRES_HUMAN_REVIEW"
        d.reasons.append(
            "agent-generated artifact with no independent confirmation. An "
            "agent cannot validate its own output; more agents restating it "
            "would not help, since repetition is not independence."
        )
        return d

    # --- common-ancestry collapse (§12) -------------------------------
    corro = list(corroborating)
    if corro:
        distinct = collapse_ancestry(corro)
        if distinct < 2 and len(corro) > 1:
            d.verdict = "REQUIRES_HUMAN_REVIEW"
            d.reasons.append(
                f"{len(corro)} corroborating artifacts collapse to {distinct} "
                f"epistemic origin. Shared ancestry is not corroboration."
            )
            return d

    # --- constitutional authority -------------------------------------
    if not artifact.authorization_valid:
        d.verdict = "REQUIRES_HUMAN_REVIEW"
        d.reasons.append(
            "no valid constitutional authorization. Capability to act is not "
            "permission to act."
        )
        return d

    # --- authorized ----------------------------------------------------
    #
    # Note what did NOT contribute: persuasiveness, repetition count,
    # emotional force, agent agreement, popularity, or rhetorical quality.
    # Every one of those is recorded in risk_flags and weighted at zero.
    d.verdict = "AUTHORIZED"
    d.may_influence_runtime = True
    d.reasons.append(
        "schema valid, provenance valid, classification runtime-authorized, "
        "constitutional authorization present."
    )
    if d.risk_flags:
        d.reasons.append(
            "risk flags present and recorded; they did not contribute to the "
            "decision in either direction."
        )
    return d
