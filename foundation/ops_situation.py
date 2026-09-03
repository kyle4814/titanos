"""
Ops Situation — wire the bottleneck engine to the real income situation.

`foundation/situation_analysis.py` is the largest capability in this
repository (bottleneck / tension / off-ramp analysis) and, until now, was
reachable from nothing — one of the 21 tested-but-uninvocable modules the
reachability report flags. Kyle's operating profile §6 is explicit:
"a capability nobody can invoke is not a capability ... wiring is part of
building." This module is the real caller.

It builds a `SituationAnalysis` from FACTS THAT ARE ACTUALLY TRUE — the
operator profile is empty (verified: every identity field in
operator_profile.json is null), and each live deal depends on those facts
to close — then runs `find_bottleneck_hypotheses` over it. The engine
computes, from dependency structure alone, what the close pack already
asserts by hand: the single highest-leverage bottleneck is the unstated
operator identity. Computing it two independent ways is the point — the
engine is not told the answer, it derives it.

Nothing here fabricates a fact: every claim is VERIFIED_FACT only because
the profile and board genuinely record it. Pure functions, no I/O.
"""

from __future__ import annotations

from foundation.close_pack import CLOSE_PLANS
from foundation.ops_digest import live_opportunities
from foundation.situation_analysis import (
    CandidateAction,
    SituationAnalysis,
    BottleneckReport,
    find_bottleneck_hypotheses,
    monk_pass,
)
from kpm.schemas.epistemic_types import classify_claim

__all__ = ["build_ops_situation", "analyse_ops_bottleneck", "render_bottleneck"]

_BY = "autonomous-ops-cycle"

# The verified facts about the operator, each tied to a constraint by
# shared keywords (situation_analysis._mentions is word-overlap). Every
# one is VERIFIED_FACT because operator_profile.json / OPS_BOARD.md
# genuinely record it — nothing here is asserted beyond the evidence.
def _facts(by: str):
    return [
        classify_claim(
            "c_identity",
            "operator identity is unstated: legal name, ABN number, business "
            "address and contact are all null in the operator profile",
            "VERIFIED_FACT", by, confidence="HIGH",
            evidence_refs=("operator_profile.json",)),
        classify_claim(
            "c_experience",
            "operator has declared no pen-test or ICT skills, no turnover "
            "figures and no referees in the operator profile",
            "VERIFIED_FACT", by, confidence="HIGH",
            evidence_refs=("operator_profile.json",)),
        classify_claim(
            "c_insurance",
            "operator holds no professional indemnity or public liability "
            "insurance cover",
            "VERIFIED_FACT", by, confidence="HIGH",
            evidence_refs=("OPS_BOARD.md",)),
        classify_claim(
            "c_certs",
            "operator holds no security certifications such as OSCP CREST "
            "GIAC or CISSP",
            "VERIFIED_FACT", by, confidence="HIGH",
            evidence_refs=("OPS_BOARD.md",)),
        classify_claim(
            "c_refs",
            "operator has no corporate reference contracts to cite",
            "VERIFIED_FACT", by, confidence="HIGH",
            evidence_refs=("OPS_BOARD.md",)),
    ]

# Constraints deliberately AVOID the shared word "operator": the
# situation_analysis._mentions linker is word-overlap, so a common word
# would link every claim to every constraint and drown the signal (it did,
# on the first run). Each constraint here shares only its own distinctive
# term with exactly one fact claim.
_CONSTRAINTS = (
    "identity credentials unstated: name ABN address contact",
    "experience turnover skills referees undeclared",
    "insurance cover absent",
    "certifications absent",
    "corporate reference contracts absent",
)


def _needs_experience(opp_id: str) -> bool:
    """Does this deal's own close plan require declared skills/turnover?"""
    plan = CLOSE_PLANS[opp_id]
    blob = " ".join(plan.needs).lower()
    return ("skill" in blob or "turnover" in blob or "experience" in blob
            or "project idea" in blob)


def build_ops_situation(by: str = _BY) -> SituationAnalysis:
    """The current income situation as a structured SituationAnalysis.

    candidate_actions are the live (non-expired) deals; each depends on
    `c_identity` (no registration, inquiry or application can be completed
    without the operator's name and ABN) and, where its own close plan
    demands skills/turnover, on `c_experience`. This dependency structure
    is real, not arranged — it mirrors what each deal actually needs."""
    opps = [o for o in live_opportunities() if not o.is_expired()]
    actions = []
    for o in opps:
        deps = ["c_identity"]
        if _needs_experience(o.opp_id):
            deps.append("c_experience")
        actions.append(CandidateAction(
            action_id=o.opp_id,
            description=o.title,
            depends_on_claim_ids=tuple(deps),
            predicted_consequences=("reaches its submit line once its "
                                    "dependencies are satisfied",)))
    return monk_pass(
        "ops-current",
        "Current live income opportunities and what blocks closing each",
        actors=("operator (Kyle)",),
        goals=("close a first real deal",),
        constraints=_CONSTRAINTS,
        known_information=_facts(by),
        unknowns=("which deals survive their portal-gated documents",),
        assumptions=(),
        candidate_actions=actions,
        evidence_refs=("OPS_BOARD.md", "operator_profile.json"),
        analyzed_by=by,
    )


def analyse_ops_bottleneck(by: str = _BY) -> BottleneckReport:
    """Run the bottleneck engine over the real situation."""
    return find_bottleneck_hypotheses(build_ops_situation(by), evaluated_by=by)


def render_bottleneck(report: BottleneckReport) -> str:
    out = [
        "=" * 72,
        "OPS BOTTLENECK ANALYSIS  (computed by situation_analysis, not asserted)",
        "=" * 72,
        f"decision : {report.decision}",
        f"reason   : {report.reason}",
        "",
    ]
    if not report.candidates:
        out.append("No bottleneck hypothesis met the evidence bar.")
        return "\n".join(out)
    out.append("bottleneck hypotheses (most-leverage first):")
    ranked = sorted(report.candidates,
                    key=lambda c: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(
                        c.leverage_estimate, 3))
    for c in ranked:
        out += [
            "",
            f"  • {c.constraint_ref}",
            f"    leverage   : {c.leverage_estimate}",
            f"    rationale  : {c.rationale}",
            f"    supported  : {len(c.supporting_claim_ids)} evidenced claim(s)",
        ]
    out += [
        "",
        "This is a SPECULATIVE_HYPOTHESIS the engine derived from dependency "
        "structure — it is not authority to act.",
    ]
    return "\n".join(out)
