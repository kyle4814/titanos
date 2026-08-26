"""
Situation Analysis — the Monk/Demonblade vertical slice.

WHAT THIS FILE IS

The smallest real composition proving one full cycle can run in code:

    situation (declared facts)
        -> monk_pass()        structure/classify, never guess a gap
        -> demonblade_pass()  attack for unsupported premises / equivalence
                              fraud, produce SURVIVED or KILLED
        -> build_magl_candidate()   only a SURVIVED analysis may become one
        -> caller drives it through the EXISTING, UNCHANGED gates:
             magl.registry.catalogue.MAGLCatalogue.register_checked()
             kpm.promotion.state_machine.PromotionStore
             rpa.gates.human_jurisdiction.authorize_pilot() /
                                          confirm_pilot_authorized()
        -> record_situation_crystal()   one Crystal closing the cycle

WHAT THIS FILE IS NOT

Not a new store, not a new gate, not a new authority. `monk_pass` and
`demonblade_pass` are pure functions over plain data — no I/O, no
registry writes, no calls into ContradictionRegistry/CrystalStore/
PromotionStore/MAGLCatalogue. `demonblade_pass` only *proposes*
contradiction candidates as data (`DemonbladeVerdict.contradiction_
candidates`) — a separate, explicit caller decides whether to actually
call `ContradictionRegistry.record()` with them. Per this repository's
Monk/Demonblade doctrine (`TITANOS_MONK_DEMONBLADE_PRINCIPLE.md`):
capability(A) != authority(A). Nothing in this file can authorize or
execute anything — `build_magl_candidate()` produces a `MAGLEntry`/
`MAGLSummary` pair, never registers it; registration, composition
checking, promotion, and pilot authorization all still go through the
existing, unmodified gates in `magl/` and `rpa/`/`kpm/`.

WHY EPISTEMIC CLASSIFICATION IS REUSED, NOT REINVENTED

`SituationAnalysis.known_information` is a tuple of
`kpm.schemas.epistemic_types.Claim` — the exact same closed vocabulary
`Crystal.epistemic_status` already uses. No parallel OBSERVED/INFERRED/
UNKNOWN/PROPOSED enum was invented; `ALL_CLASSIFICATIONS` already makes
that distinction (VERIFIED_FACT/EVIDENCE_SUPPORTED_MODEL/IMPLEMENTED_
SYSTEM as the evidenced tier vs. SPECULATIVE_HYPOTHESIS/UNKNOWN/etc. as
the unevidenced tier) and `demonblade_pass` reasons directly over it.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Sequence

from kpm.schemas.epistemic_types import ALL_CLASSIFICATIONS, Claim, classify_claim

__all__ = [
    "CandidateAction",
    "SituationAnalysis",
    "DemonbladeVerdict",
    "AnalysisNotSurvived",
    "monk_pass",
    "demonblade_pass",
    "build_magl_candidate",
    "record_situation_crystal",
    "BOTTLENECK_DECISIONS",
    "BottleneckCandidate",
    "BottleneckReport",
    "find_bottleneck_hypotheses",
    "TENSION_DECISIONS",
    "TensionCandidate",
    "TensionReport",
    "find_tension_hypotheses",
    "OFFRAMP_CATEGORIES",
    "OFFRAMP_DECISIONS",
    "OffRampCandidate",
    "OffRampReport",
    "evaluate_off_ramp_candidates",
]

# The one evidence-backed tier of ALL_CLASSIFICATIONS. Mirrors
# kpm.schemas.epistemic_types._REQUIRES_EVIDENCE_TO_ENTER exactly —
# not redefined independently, just re-imported by value since that
# frozenset is not itself exported.
_EVIDENCED_TIER = frozenset({
    "VERIFIED_FACT", "EVIDENCE_SUPPORTED_MODEL", "IMPLEMENTED_SYSTEM",
})


@dataclass(frozen=True)
class CandidateAction:
    """One proposed action, with an explicit, checkable justification —
    never a bare description. `depends_on_claim_ids` names exactly which
    known_information claims (or, if it names something else, exactly
    which assumption or nothing at all) the action's justification
    rests on; demonblade_pass() checks this, it is not decorative."""

    action_id: str
    description: str
    depends_on_claim_ids: tuple[str, ...] = ()
    predicted_consequences: tuple[str, ...] = ()


@dataclass(frozen=True)
class SituationAnalysis:
    """One structured situation. Produced only by monk_pass() — never
    constructed directly by a caller trying to skip normalization."""

    situation_id: str
    framing: str
    actors: tuple[str, ...]
    goals: tuple[str, ...]
    constraints: tuple[str, ...]
    known_information: tuple[Claim, ...]
    unknowns: tuple[str, ...]
    assumptions: tuple[str, ...]
    candidate_actions: tuple[CandidateAction, ...]
    evidence_refs: tuple[str, ...]
    analyzed_by: str

    def claim_ids(self) -> frozenset[str]:
        return frozenset(c.claim_id for c in self.known_information)


def monk_pass(
    situation_id: str,
    framing: str,
    *,
    actors: Sequence[str],
    goals: Sequence[str],
    constraints: Sequence[str],
    known_information: Sequence[Claim],
    unknowns: Sequence[str],
    assumptions: Sequence[str],
    candidate_actions: Sequence[CandidateAction],
    evidence_refs: Sequence[str],
    analyzed_by: str,
) -> SituationAnalysis:
    """Structure a situation's declared facts. Pure function: no I/O, no
    registry writes, no filling in of a missing field with a guess — a
    caller who doesn't supply a field gets an empty tuple, never an
    invented value.
    """
    if not situation_id.strip():
        raise ValueError("situation_id must be non-empty")
    if not framing.strip():
        raise ValueError("framing must be non-empty")
    if not analyzed_by.strip():
        raise ValueError(
            "analyzed_by must be non-empty — an unattributed analysis "
            "cannot be audited"
        )
    for claim in known_information:
        if claim.classification not in ALL_CLASSIFICATIONS:
            raise ValueError(
                f"claim '{claim.claim_id}' has unrecognised classification "
                f"{claim.classification!r}"
            )
    return SituationAnalysis(
        situation_id=situation_id,
        framing=framing,
        actors=tuple(actors),
        goals=tuple(goals),
        constraints=tuple(constraints),
        known_information=tuple(known_information),
        unknowns=tuple(unknowns),
        assumptions=tuple(assumptions),
        candidate_actions=tuple(candidate_actions),
        evidence_refs=tuple(evidence_refs),
        analyzed_by=analyzed_by,
    )


@dataclass(frozen=True)
class DemonbladeVerdict:
    """The result of attacking one SituationAnalysis. Analysis/proposal
    only — no field here means or implies "authorized". A SURVIVED
    verdict means exactly one thing: no unsupported dependency, category
    error, or authority inflation was found in the declared candidate
    actions' justifications. It never means the action may proceed."""

    verdict: str  # "SURVIVED" | "KILLED"
    findings: tuple[str, ...]
    contradiction_candidates: tuple[tuple[str, tuple[str, ...]], ...]
    reason: str
    attacked_by: str


def demonblade_pass(
    analysis: SituationAnalysis, *, attacked_by: str,
) -> DemonbladeVerdict:
    """Adversarially attack `analysis`. Pure function: never mutates the
    analysis, never calls ContradictionRegistry.record()/CrystalStore.
    record()/any gate itself — it only proposes contradiction candidates
    as plain data (`contradiction_candidates`); a separate, explicit
    caller decides whether to actually record them.

    KILL RULE (equivalence fraud / authority inflation): a candidate
    action is flagged if any `depends_on_claim_ids` entry does not
    resolve to a real `known_information` claim in the evidence-backed
    tier (VERIFIED_FACT / EVIDENCE_SUPPORTED_MODEL / IMPLEMENTED_SYSTEM).
    Depending on an `assumptions` entry, or on nothing declared at all,
    while the action's justification implies verified support, is
    exactly the reviewer-diversity-mistaken-for-content-validation shape
    this session's RPA finding already closed once in real code — this
    is the same check, generalised to any situation's candidate actions.
    """
    if not attacked_by.strip():
        raise ValueError("attacked_by must be non-empty")

    known_by_id = {c.claim_id: c for c in analysis.known_information}
    findings: list[str] = []
    contradiction_candidates: list[tuple[str, tuple[str, ...]]] = []

    if not analysis.candidate_actions:
        findings.append("no candidate_actions to evaluate")

    for action in analysis.candidate_actions:
        for dep_id in action.depends_on_claim_ids:
            claim = known_by_id.get(dep_id)
            if claim is None:
                if dep_id in analysis.assumptions:
                    findings.append(
                        f"action '{action.action_id}' depends on assumption "
                        f"'{dep_id}', not a verified claim — unsupported premise"
                    )
                    contradiction_candidates.append((
                        f"action '{action.action_id}' treats assumption "
                        f"'{dep_id}' as if it were verified support",
                        (action.action_id, dep_id),
                    ))
                else:
                    findings.append(
                        f"action '{action.action_id}' depends on undeclared "
                        f"reference '{dep_id}' — not in known_information or "
                        f"assumptions"
                    )
                    contradiction_candidates.append((
                        f"action '{action.action_id}' cites '{dep_id}' which "
                        f"is neither a known claim nor a declared assumption",
                        (action.action_id, dep_id),
                    ))
            elif claim.classification not in _EVIDENCED_TIER:
                findings.append(
                    f"action '{action.action_id}' depends on claim '{dep_id}' "
                    f"classified {claim.classification} — not evidence-backed, "
                    f"equivalence-fraud risk if treated as sufficient support"
                )
                contradiction_candidates.append((
                    f"action '{action.action_id}' relies on claim '{dep_id}' "
                    f"({claim.classification}) as if it were evidence-backed",
                    (action.action_id, dep_id),
                ))

    if analysis.known_information and not analysis.unknowns and not analysis.assumptions:
        findings.append(
            "situation declares zero unknowns and zero assumptions while "
            "asserting known_information — overconfident self-scrutiny"
        )

    verdict = "KILLED" if contradiction_candidates else "SURVIVED"
    reason = (
        "; ".join(findings) if findings else
        "no unsupported dependency, category error, or authority inflation "
        "found in any candidate action's declared justification"
    )

    return DemonbladeVerdict(
        verdict=verdict,
        findings=tuple(findings),
        contradiction_candidates=tuple(contradiction_candidates),
        reason=reason,
        attacked_by=attacked_by,
    )


class AnalysisNotSurvived(Exception):
    """Raised by build_magl_candidate() when the supplied verdict is not
    SURVIVED. A killed or unresolved analysis has no path to becoming a
    MAGL candidate at all — checked structurally here, not left to
    caller discipline, so a caller cannot accidentally (or deliberately)
    skip straight from a KILLED verdict to a registrable candidate."""


def build_magl_candidate(
    analysis: SituationAnalysis,
    verdict: DemonbladeVerdict,
    *,
    version: str,
    name: str,
    domain: Sequence[str],
    capability_type: Sequence[str],
    maturity: str,
    license: str,
    content_hash: str,
    may_read: Sequence[str] = (),
    may_write: Sequence[str] = (),
    may_execute: Sequence[str] = (),
    may_call: Sequence[str] = (),
    may_modify: Sequence[str] = (),
    may_publish: Sequence[str] = (),
    prohibited_actions: Sequence[str] = (),
    provides: Sequence[str] = (),
    requires: Sequence[str] = (),
    compatible_interfaces: Sequence[str] = (),
    dependencies_required: Sequence[str] = (),
    dependencies_incompatible: Sequence[str] = (),
):
    """Derive a (MAGLEntry, MAGLSummary) pair from a SURVIVED analysis.

    Raises AnalysisNotSurvived if verdict.verdict != "SURVIVED" — this is
    the one structural control this module adds: capability to analyse
    is unconditional, but capability to become a MAGL candidate is not.

    Returns plain data only. Does NOT call MAGLCatalogue.register() or
    .register_checked() — the caller must do that explicitly, through
    the existing, unmodified catalogue, so composition checking
    (check_composition) and any future REFUSED verdict still apply in
    full. This function never uses plain register() itself and does not
    expose a path to it — only register_checked() can ever admit
    something this function produces into a real catalogue.
    """
    if verdict.verdict != "SURVIVED":
        raise AnalysisNotSurvived(
            f"analysis '{analysis.situation_id}' verdict is "
            f"'{verdict.verdict}', not SURVIVED — a killed or unresolved "
            f"analysis cannot be operationalized into a MAGL candidate. "
            f"reason: {verdict.reason}"
        )

    # Imported locally: this module must not become the place MAGL's own
    # types are re-exported from — a caller wanting MAGLEntry/MAGLSummary
    # directly should still import them from magl.registry.catalogue /
    # magl.composition.engine, same as any other caller.
    from magl.composition.engine import MAGLSummary
    from magl.registry.catalogue import MAGLEntry

    entry = MAGLEntry(
        magl_id=analysis.situation_id,
        version=version,
        name=name,
        domain=tuple(domain),
        capability_type=tuple(capability_type),
        # A candidate derived from analysis is a design, never a fact —
        # TECHNICAL_DESIGN is the only classification this function will
        # ever stamp; it cannot be overridden by a caller argument,
        # structurally preventing an analysis from self-certifying as
        # VERIFIED_FACT/IMPLEMENTED_SYSTEM on its way into the catalogue.
        epistemic_status="TECHNICAL_DESIGN",
        maturity=maturity,
        dependencies_required=tuple(dependencies_required),
        dependencies_incompatible=tuple(dependencies_incompatible),
        lifecycle_status="CANDIDATE",
        license=license,
        content_hash=content_hash,
    )
    summary = MAGLSummary(
        magl_id=analysis.situation_id,
        version=version,
        may_read=tuple(may_read),
        may_write=tuple(may_write),
        may_execute=tuple(may_execute),
        may_call=tuple(may_call),
        may_modify=tuple(may_modify),
        may_publish=tuple(may_publish),
        prohibited_actions=tuple(prohibited_actions),
        provides=tuple(provides),
        requires=tuple(requires),
        compatible_interfaces=tuple(compatible_interfaces),
        dependencies_required=tuple(dependencies_required),
        dependencies_incompatible=tuple(dependencies_incompatible),
    )
    return entry, summary


def record_situation_crystal(
    crystal_store,
    analysis: SituationAnalysis,
    verdict: DemonbladeVerdict,
    *,
    crystal_id: str,
    hypothesis: str,
    provenance: str,
    epistemic_status: str,
    recorded_by: str,
    regression_test_ref: str = "",
    supersedes: str | None = None,
):
    """Record one completed Monk/Demonblade cycle as a Crystal, using
    `foundation.crystal.CrystalStore` exactly as it already exists — no
    new field, no new store. `provenance` should be a content hash (or
    other verifiable reference) identifying exactly what was analysed,
    e.g. the content_hash a SourceRegistry produced for the ingested
    candidate action text — never a bare description, so a future reader
    can verify what this crystal is actually about.
    """
    action_text = "; ".join(
        f"{a.action_id}: {a.description}" for a in analysis.candidate_actions
    ) or "(no candidate actions declared)"
    return crystal_store.record(
        crystal_id,
        problem=analysis.framing,
        context="; ".join(analysis.constraints) or "(no constraints declared)",
        hypothesis=hypothesis,
        action=action_text,
        evidence="; ".join(analysis.evidence_refs) or "(no evidence_refs declared)",
        result=verdict.verdict,
        failure_mode="; ".join(verdict.findings) if verdict.verdict == "KILLED" else "",
        limitation="; ".join(analysis.unknowns) or "(no unknowns declared)",
        provenance=provenance,
        reusable_abstraction=verdict.reason,
        regression_test_ref=regression_test_ref,
        epistemic_status=epistemic_status,
        recorded_by=recorded_by,
        supersedes=supersedes,
    )


# ─────────────────────────────────────────────────────────────
# Bottleneck hypotheses — the external-world-ping extension
# ─────────────────────────────────────────────────────────────
#
# WHY A BOTTLENECK IS A Claim, NEVER A BARE NUMBER
#
# A leverage/impact score is a value judgment, not a fact. Reusing
# `kpm.schemas.epistemic_types.classify_claim` for `hypothesis_claim`
# means a bottleneck hypothesis is structurally barred from ever
# claiming VERIFIED_FACT/EVIDENCE_SUPPORTED_MODEL/IMPLEMENTED_SYSTEM
# status via HIGH confidence (`ConfidenceNotEarned` — a hypothesis is,
# by definition, SPECULATIVE_HYPOTHESIS, and that classification can
# never carry HIGH confidence per `_CANNOT_BE_HIGH_CONFIDENCE`). There
# is deliberately no separate float/score field anywhere on
# `BottleneckCandidate` — `leverage_estimate` is one of three ordinal
# labels, never a number, so nothing here can be mistaken for a
# precise, objective measurement (the "score laundering" failure mode).
#
# WHY THIS NEVER FORCES A SINGLE WINNER
#
# `BottleneckReport.candidates` is always a tuple — one entry for
# SINGLE_CANDIDATE, two-or-more for AMBIGUOUS_MULTIPLE, zero for HOLD
# or INSUFFICIENT_EVIDENCE. Nothing here ever truncates a tied result
# down to "the" bottleneck; ties are surfaced, not resolved by
# arbitrary tie-breaking.
#
# WHAT THIS DOES NOT DO (named honestly, not silently skipped)
#
# `_mentions()` below is a plain keyword-overlap heuristic connecting a
# declared `constraint` string to `known_information` claim text — it
# has no semantic/causal understanding, and does not distinguish a
# claim that merely CORRELATES with a constraint from one that
# CAUSALLY explains it. This is a real, named limitation (see
# `foundation/BUILD_REPORT.md`), not solved here — a caller should not
# read "supporting_claim_ids is non-empty" as "causation proven."

BOTTLENECK_DECISIONS = frozenset({
    "INSUFFICIENT_EVIDENCE", "HOLD", "SINGLE_CANDIDATE", "AMBIGUOUS_MULTIPLE",
})

_LEVERAGE_LEVELS = ("LOW", "MEDIUM", "HIGH")
_LEVEL_RANK = {level: i for i, level in enumerate(_LEVERAGE_LEVELS)}


def _mentions(claim_text: str, constraint_text: str) -> bool:
    """Heuristic keyword-overlap check — NOT semantic or causal
    understanding. Words of length > 3 shared between the two texts
    count as a mention. Named limitation, not a hidden one."""
    claim_words = set(claim_text.lower().split())
    constraint_words = {w for w in constraint_text.lower().split() if len(w) > 3}
    return bool(claim_words & constraint_words)


@dataclass(frozen=True)
class BottleneckCandidate:
    """One proposed bottleneck. `hypothesis_claim` is a real `Claim`
    (classification SPECULATIVE_HYPOTHESIS — never higher, see module
    note above) — this object never asserts the bottleneck as fact.
    `leverage_estimate` is an ordinal label, never a float score."""

    constraint_ref: str
    hypothesis_claim: Claim
    supporting_claim_ids: tuple[str, ...]
    leverage_estimate: str
    dimensions_scored: tuple[tuple[str, str], ...]
    rationale: str


@dataclass(frozen=True)
class BottleneckReport:
    """Analysis/proposal only. No field on this object, or on
    `BottleneckCandidate`, is named or shaped so it could be consumed as
    authorization — nothing here is a valid argument to
    `build_magl_candidate`, `PromotionStore.promote`, or
    `authorize_pilot`; a caller must separately construct a
    `DemonbladeVerdict`/`SituationAnalysis` pair to proceed toward any
    of those, same as this module's original slice."""

    situation_id: str
    decision: str
    candidates: tuple[BottleneckCandidate, ...]
    reason: str
    evaluated_by: str


def find_bottleneck_hypotheses(
    analysis: SituationAnalysis, *, evaluated_by: str, min_observation_count: int = 2,
) -> BottleneckReport:
    """Propose 0, 1, or 2+ bottleneck hypotheses from an already-built
    `SituationAnalysis`. Pure function: no I/O, no store writes, no
    calls into any gate. Returns HOLD or INSUFFICIENT_EVIDENCE rather
    than inventing a bottleneck when evidence is thin; returns
    AMBIGUOUS_MULTIPLE rather than forcing a fake single winner when
    two or more constraints tie on leverage.

    `min_observation_count` is the minimum number of evidence-backed
    (`_EVIDENCED_TIER`) claims required anywhere in `known_information`
    before ANY bottleneck hypothesis may be proposed — below that, this
    always returns INSUFFICIENT_EVIDENCE regardless of what
    `constraints`/`candidate_actions` declare.
    """
    if not evaluated_by.strip():
        raise ValueError("evaluated_by must be non-empty")

    evidenced = [c for c in analysis.known_information if c.classification in _EVIDENCED_TIER]
    if len(evidenced) < min_observation_count:
        return BottleneckReport(
            situation_id=analysis.situation_id, decision="INSUFFICIENT_EVIDENCE",
            candidates=(),
            reason=(
                f"only {len(evidenced)} evidence-backed claim(s) in "
                f"known_information, need at least {min_observation_count} "
                f"before proposing a bottleneck hypothesis"
            ),
            evaluated_by=evaluated_by,
        )

    candidates: list[BottleneckCandidate] = []
    for i, constraint in enumerate(analysis.constraints):
        supporting = tuple(c.claim_id for c in evidenced if _mentions(c.text, constraint))
        if not supporting:
            continue
        dependency_centrality = sum(
            1 for a in analysis.candidate_actions
            if set(a.depends_on_claim_ids) & set(supporting)
        )
        if dependency_centrality == 0:
            continue
        level = "HIGH" if dependency_centrality >= 2 else "MEDIUM"
        evidence_quality = "HIGH" if len(supporting) >= 2 else "MEDIUM"
        hypothesis_claim = classify_claim(
            f"bottleneck-{analysis.situation_id}-{i}", constraint,
            "SPECULATIVE_HYPOTHESIS", evaluated_by,
            confidence="MEDIUM" if level == "HIGH" else "LOW",
            evidence_refs=supporting,
        )
        candidates.append(BottleneckCandidate(
            constraint_ref=constraint, hypothesis_claim=hypothesis_claim,
            supporting_claim_ids=supporting, leverage_estimate=level,
            dimensions_scored=(
                ("dependency_centrality", level),
                ("evidence_quality", evidence_quality),
            ),
            rationale=(
                f"{dependency_centrality} candidate action(s) depend on "
                f"evidence supporting this constraint"
            ),
        ))

    if not candidates:
        return BottleneckReport(
            situation_id=analysis.situation_id, decision="HOLD", candidates=(),
            reason=(
                "evidence exists but no declared constraint clears the "
                "minimum dependency bar for a bottleneck hypothesis — "
                "refusing to invent one"
            ),
            evaluated_by=evaluated_by,
        )

    top_rank = max(_LEVEL_RANK[c.leverage_estimate] for c in candidates)
    top = tuple(c for c in candidates if _LEVEL_RANK[c.leverage_estimate] == top_rank)

    if len(top) > 1:
        return BottleneckReport(
            situation_id=analysis.situation_id, decision="AMBIGUOUS_MULTIPLE",
            candidates=top,
            reason=(
                f"{len(top)} constraints tie at leverage level "
                f"{top[0].leverage_estimate} — preserved as ambiguous rather "
                f"than forcing a single winner"
            ),
            evaluated_by=evaluated_by,
        )

    return BottleneckReport(
        situation_id=analysis.situation_id, decision="SINGLE_CANDIDATE",
        candidates=top,
        reason=f"'{top[0].constraint_ref}' dominates on dependency_centrality/evidence_quality",
        evaluated_by=evaluated_by,
    )


# ─────────────────────────────────────────────────────────────
# Tension hypotheses — structural conflict, distinct from a bottleneck
# ─────────────────────────────────────────────────────────────
#
# WHY THIS IS A SEPARATE FUNCTION, NOT A REUSE OF find_bottleneck_hypotheses
#
# A bottleneck is single-sided: one constraint blocking one or more
# candidate_actions, all pointing the same direction. A tension is
# structurally two-sided: two named actors whose evidence-backed
# positions may both be legitimate and still be in genuine, unresolved
# opposition. `BottleneckCandidate` has no second-claim slot and forcing
# one in would corrupt its existing single-actor meaning — this is a
# parallel, not a modification.
#
# NOT EVERY TENSION IS A DEFECT
#
# `STRUCTURAL_TENSION` never means "inevitable." It means: evidence
# supports both sides' competing positions, and no declared
# relaxing_condition is itself evidence-backed under the CURRENT
# analysis. A future SituationAnalysis with different evidence can
# reach a different state — this is a claim about present evidence,
# never a prediction about the future (the same discipline
# `_CANNOT_BE_HIGH_CONFIDENCE` already enforces for any
# SPECULATIVE_HYPOTHESIS). "ACTIVE_CLASH" (an already-manifested,
# observed conflict, stronger than mere unresolved incompatibility) is
# deliberately NOT implemented here — distinguishing "this has already
# happened" from "this is merely unresolved" would require causal/
# temporal understanding this module's keyword-overlap heuristic cannot
# honestly provide. Naming a state this code cannot back with evidence
# would be worse than omitting it.

TENSION_DECISIONS = frozenset({
    "INSUFFICIENT_EVIDENCE",
    "NO_TENSION_IDENTIFIED",
    "STRUCTURAL_TENSION",
    "CONTINGENT_TENSION",
    "AMBIGUOUS_MULTIPLE",
})


@dataclass(frozen=True)
class TensionCandidate:
    """One proposed two-sided tension. `tension_claim` is a real `Claim`
    (classification SPECULATIVE_HYPOTHESIS, never higher) — this object
    never asserts the tension as settled fact, and never as permanent."""

    actor_a: str
    actor_b: str
    relationship_ref: str
    tension_claim: Claim
    supporting_claim_ids_a: tuple[str, ...]
    supporting_claim_ids_b: tuple[str, ...]
    objective_compatibility: str  # "COMPATIBLE" | "COMPETING" | "UNKNOWN"
    intensifying_conditions: tuple[str, ...]
    relaxing_conditions: tuple[str, ...]
    state: str
    rationale: str


@dataclass(frozen=True)
class TensionReport:
    """Analysis/proposal only — same non-authority guarantee as
    `BottleneckReport`. No field here is a valid argument to
    `build_magl_candidate`/`PromotionStore.promote`/`authorize_pilot`;
    a `TensionReport` is not a `DemonbladeVerdict` and has no path into
    that signature at all."""

    situation_id: str
    decision: str
    candidates: tuple[TensionCandidate, ...]
    reason: str
    evaluated_by: str


def find_tension_hypotheses(
    analysis: SituationAnalysis, *, evaluated_by: str, min_observation_count: int = 2,
) -> TensionReport:
    """Propose 0, 1, or 2+ two-sided tension hypotheses between pairs of
    `analysis.actors`. Pure function — no I/O, no store writes, no gate
    calls. Refuses to invent a tension when evidence is thin
    (INSUFFICIENT_EVIDENCE) or when no actor pair shows a genuinely
    competing pattern (NO_TENSION_IDENTIFIED) — these are honest,
    reachable non-findings, not degraded results.

    A tension candidate requires: (a) evidence-backed claims mentioning
    each actor separately, and (b) at least one declared constraint
    mentioning BOTH actors (the shared point of friction). Without (b),
    two actors merely coexisting in a situation is not a tension —
    NO_TENSION_IDENTIFIED, not a manufactured conflict.
    """
    if not evaluated_by.strip():
        raise ValueError("evaluated_by must be non-empty")

    evidenced = [c for c in analysis.known_information if c.classification in _EVIDENCED_TIER]
    if len(evidenced) < min_observation_count:
        return TensionReport(
            situation_id=analysis.situation_id, decision="INSUFFICIENT_EVIDENCE",
            candidates=(),
            reason=(
                f"only {len(evidenced)} evidence-backed claim(s) in "
                f"known_information, need at least {min_observation_count} "
                f"before proposing a tension hypothesis"
            ),
            evaluated_by=evaluated_by,
        )

    candidates: list[TensionCandidate] = []
    for i, (actor_a, actor_b) in enumerate(itertools.combinations(analysis.actors, 2)):
        claims_a = tuple(c.claim_id for c in evidenced if _mentions(c.text, actor_a))
        claims_b = tuple(c.claim_id for c in evidenced if _mentions(c.text, actor_b))
        if not claims_a or not claims_b:
            continue

        shared_constraint = next(
            (c for c in analysis.constraints if _mentions(c, actor_a) and _mentions(c, actor_b)),
            None,
        )
        if shared_constraint is None:
            continue

        relaxing = tuple(
            a.description for a in analysis.candidate_actions
            if _mentions(a.description, actor_a) and _mentions(a.description, actor_b)
        )
        intensifying = tuple(
            a for a in analysis.assumptions if _mentions(a, actor_a) or _mentions(a, actor_b)
        )
        state = "CONTINGENT_TENSION" if relaxing else "STRUCTURAL_TENSION"

        tension_claim = classify_claim(
            f"tension-{analysis.situation_id}-{i}", shared_constraint,
            "SPECULATIVE_HYPOTHESIS", evaluated_by, confidence="LOW",
            evidence_refs=claims_a + claims_b,
        )
        candidates.append(TensionCandidate(
            actor_a=actor_a, actor_b=actor_b, relationship_ref=shared_constraint,
            tension_claim=tension_claim,
            supporting_claim_ids_a=claims_a, supporting_claim_ids_b=claims_b,
            objective_compatibility="COMPETING",
            intensifying_conditions=intensifying, relaxing_conditions=relaxing,
            state=state,
            rationale=(
                f"'{actor_a}' and '{actor_b}' both have evidence-backed claims "
                f"and share the constraint '{shared_constraint}'"
                + (f"; a declared candidate action already addresses both — "
                   f"treated as contingent, not structural" if relaxing else
                   f"; no declared candidate action addresses both under "
                   f"current evidence")
            ),
        ))

    if not candidates:
        return TensionReport(
            situation_id=analysis.situation_id, decision="NO_TENSION_IDENTIFIED",
            candidates=(),
            reason=(
                "evidence exists for declared actors but no shared constraint "
                "was found linking any two of them — refusing to manufacture "
                "a tension"
            ),
            evaluated_by=evaluated_by,
        )

    if len(candidates) > 1:
        return TensionReport(
            situation_id=analysis.situation_id, decision="AMBIGUOUS_MULTIPLE",
            candidates=tuple(candidates),
            reason=(
                f"{len(candidates)} actor-pair tensions found — preserved as "
                f"multiple, not collapsed into a single 'the' tension"
            ),
            evaluated_by=evaluated_by,
        )

    return TensionReport(
        situation_id=analysis.situation_id, decision=candidates[0].state,
        candidates=tuple(candidates),
        reason=candidates[0].rationale,
        evaluated_by=evaluated_by,
    )


# ─────────────────────────────────────────────────────────────
# Off-ramp hypotheses — possible stabilisation pathways, never orders
# ─────────────────────────────────────────────────────────────
#
# THIS FUNCTION NEVER GENERATES AN OFF-RAMP — ONLY VETS ONE A CALLER
# ALREADY PROPOSED
#
# A generator that invents stabilisation pathways would be exactly the
# "recommendation engine" this layer must never become — it would be
# TitanOS silently substituting its own values for a human's. Instead,
# `evaluate_off_ramp_candidates` applies the same Monk discipline
# `monk_pass()` applies to a raw situation: structure and classify a
# caller-supplied candidate against the evidence already in `analysis`,
# never invent one on the caller's behalf.
#
# WHY THERE IS NO STRUCTURAL BLOCK LIKE AnalysisNotSurvived HERE
#
# `build_magl_candidate()` only accepts `(SituationAnalysis,
# DemonbladeVerdict)` — an `OffRampCandidate`/`OffRampReport` is a
# different type entirely and has no path into that signature. The
# absence of a bridge IS the guard, the same pattern Hell's Gate uses by
# never having "TRUSTED" anywhere in its vocabulary: nothing needed to
# be forbidden, because nothing was ever built that could do it.

OFFRAMP_CATEGORIES = frozenset({
    "SEQUENCING", "BUFFER", "BOUNDARY", "INFORMATION_CORRECTION",
    "REVERSIBLE_TRIAL", "RESOURCE_EXPANSION", "SCOPE_REDUCTION",
    "SEPARATION", "HANDOFF", "PHASED_TRANSITION", "EXPLICIT_ARBITRATION",
    "WAIT", "ACCEPT_IRREDUCIBLE_CONFLICT",
})

OFFRAMP_DECISIONS = frozenset({
    "NO_CREDIBLE_OFF_RAMP_IDENTIFIED",
    "PRECONDITIONS_UNMET",
    "SINGLE_CANDIDATE",
    "MULTIPLE_CANDIDATES",
})

_REVERSIBILITY_LEVELS = ("REVERSIBLE", "PARTIALLY_REVERSIBLE", "IRREVERSIBLE")
_TRANSITION_COST_LEVELS = ("LOW", "MEDIUM", "HIGH")


@dataclass(frozen=True)
class OffRampCandidate:
    """One caller-proposed stabilisation option. Never itself an order:
    no field here is named or shaped as an imperative (no `execute`,
    `apply`, `approved`, `recommended`). `affected_relationships` is
    mandatory — pass `("NONE_IDENTIFIED_UNDER_CURRENT_EVIDENCE",)`
    rather than an empty tuple if genuinely none were found; an empty
    tuple would be indistinguishable from "not considered" (K5/K7).
    `interim_cost_if_reversible` is required whenever `reversibility !=
    "IRREVERSIBLE"` — reversible is not the same as consequence-free
    during the trial itself (K7)."""

    offramp_id: str
    tension_ref: str
    category: str
    description: str
    preconditions: tuple[str, ...]
    mechanism_claim: Claim
    supporting_evidence_refs: tuple[str, ...]
    limitations: tuple[str, ...]
    reversibility: str
    interim_cost_if_reversible: str
    affected_relationships: tuple[str, ...]
    transition_cost: str
    proposed_by: str

    def __post_init__(self) -> None:
        if self.category not in OFFRAMP_CATEGORIES:
            raise ValueError(
                f"'{self.category}' is not one of {sorted(OFFRAMP_CATEGORIES)}"
            )
        if self.reversibility not in _REVERSIBILITY_LEVELS:
            raise ValueError(
                f"reversibility must be one of {_REVERSIBILITY_LEVELS}"
            )
        if self.transition_cost not in _TRANSITION_COST_LEVELS:
            raise ValueError(
                f"transition_cost must be one of {_TRANSITION_COST_LEVELS}"
            )
        if not self.affected_relationships:
            raise ValueError(
                f"off-ramp '{self.offramp_id}' must declare "
                f"affected_relationships explicitly — pass "
                f"('NONE_IDENTIFIED_UNDER_CURRENT_EVIDENCE',) if genuinely "
                f"none were found, never leave this silently empty"
            )
        if self.reversibility != "IRREVERSIBLE" and not self.interim_cost_if_reversible.strip():
            raise ValueError(
                f"off-ramp '{self.offramp_id}' declares "
                f"reversibility={self.reversibility!r} but no "
                f"interim_cost_if_reversible — reversible is not "
                f"consequence-free during the trial itself"
            )
        if self.mechanism_claim.classification != "SPECULATIVE_HYPOTHESIS":
            raise ValueError(
                f"off-ramp '{self.offramp_id}' mechanism_claim must be "
                f"classified SPECULATIVE_HYPOTHESIS — an off-ramp's proposed "
                f"mechanism is never a verified fact"
            )


@dataclass(frozen=True)
class OffRampReport:
    """Analysis/proposal only. `decision` is never consumed by
    `build_magl_candidate`/`PromotionStore.promote`/`authorize_pilot` —
    those require a `SituationAnalysis`+`DemonbladeVerdict` pair, a
    shape this object cannot produce."""

    situation_id: str
    decision: str
    candidates: tuple[OffRampCandidate, ...]
    unmet_precondition_candidates: tuple[OffRampCandidate, ...]
    reason: str
    evaluated_by: str


def evaluate_off_ramp_candidates(
    analysis: SituationAnalysis,
    candidates: Sequence[OffRampCandidate],
    *,
    evaluated_by: str,
) -> OffRampReport:
    """Classify caller-proposed off-ramp candidates against `analysis`'s
    own `known_information` — never generate one. A precondition is
    "supported" only if some evidence-backed claim's text mentions it
    (same heuristic, same named limitation, as `find_bottleneck_
    hypotheses`'s `_mentions()`); an unsupported precondition routes the
    candidate to `unmet_precondition_candidates`, never silently into
    the credible list (closes the "declared but not re-checked"
    precondition gap for whatever evidence THIS analysis currently
    carries — re-running this function against a fresh SituationAnalysis
    is how a precondition gets re-verified against new evidence; nothing
    here caches or trusts a prior verification).
    """
    if not evaluated_by.strip():
        raise ValueError("evaluated_by must be non-empty")

    if not candidates:
        return OffRampReport(
            situation_id=analysis.situation_id,
            decision="NO_CREDIBLE_OFF_RAMP_IDENTIFIED",
            candidates=(), unmet_precondition_candidates=(),
            reason="no off-ramp candidate was proposed for evaluation",
            evaluated_by=evaluated_by,
        )

    evidenced_texts = tuple(
        c.text for c in analysis.known_information if c.classification in _EVIDENCED_TIER
    )
    credible: list[OffRampCandidate] = []
    unmet: list[OffRampCandidate] = []
    for candidate in candidates:
        if not candidate.preconditions:
            unmet.append(candidate)
            continue
        all_supported = all(
            any(_mentions(text, pre) for text in evidenced_texts)
            for pre in candidate.preconditions
        )
        (credible if all_supported else unmet).append(candidate)

    if not credible:
        return OffRampReport(
            situation_id=analysis.situation_id,
            decision="PRECONDITIONS_UNMET" if unmet else "NO_CREDIBLE_OFF_RAMP_IDENTIFIED",
            candidates=(), unmet_precondition_candidates=tuple(unmet),
            reason=(
                "no proposed off-ramp's preconditions are currently "
                "supported by evidence in this analysis"
            ),
            evaluated_by=evaluated_by,
        )

    if len(credible) > 1:
        return OffRampReport(
            situation_id=analysis.situation_id, decision="MULTIPLE_CANDIDATES",
            candidates=tuple(credible), unmet_precondition_candidates=tuple(unmet),
            reason=(
                f"{len(credible)} off-ramp candidates have evidence-supported "
                f"preconditions — preserved as multiple options, never "
                f"collapsed into a single recommendation"
            ),
            evaluated_by=evaluated_by,
        )

    return OffRampReport(
        situation_id=analysis.situation_id, decision="SINGLE_CANDIDATE",
        candidates=tuple(credible), unmet_precondition_candidates=tuple(unmet),
        reason=(
            f"'{credible[0].offramp_id}' is the one candidate whose "
            f"preconditions are currently evidence-supported"
        ),
        evaluated_by=evaluated_by,
    )
