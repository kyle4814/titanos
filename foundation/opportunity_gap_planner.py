"""Dependency-aware coverage-gap prioritization for TitanOS.

Scores are engineering-planning heuristics. They never assert that a gap is
economically superior; they estimate leverage from reuse, breadth, freshness,
and build friction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from foundation.opportunity_coverage_gaps import CoverageGap
from foundation.source_adapter_contract import SourceAdapterContract


DEFAULT_WEIGHTS: Final[dict[str, int]] = {
    "reuse": 5,
    "breadth": 4,
    "freshness": 2,
    "evidence": 3,
    "friction": 3,
}


@dataclass(frozen=True)
class GapPlan:
    gap: CoverageGap
    score: int
    reusable_adapters: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "gap": self.gap.to_dict(),
            "score": self.score,
            "reusable_adapters": self.reusable_adapters,
            "blockers": self.blockers,
            "rationale": self.rationale,
        }


def _overlap(a: SourceAdapterContract, gap: CoverageGap) -> int:
    score = 0
    if not a.opportunity_types or gap.opportunity_type in a.opportunity_types:
        score += 2
    if not a.regions or gap.region in a.regions or "GLOBAL" in a.regions:
        score += 2
    if not a.jurisdictions or gap.jurisdiction in a.jurisdictions:
        score += 2
    return score


def plan_gap(
    gap: CoverageGap,
    adapters: tuple[SourceAdapterContract, ...] = (),
    *,
    weights: dict[str, int] | None = None,
) -> GapPlan:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    reusable: list[tuple[int, str]] = []
    blockers: list[str] = []

    for adapter in adapters:
        if adapter.status in {"DISABLED", "RETIRED"}:
            continue
        overlap = _overlap(adapter, gap)
        if overlap:
            reusable.append((overlap, adapter.adapter_id))

    if reusable:
        reusable.sort(key=lambda item: (-item[0], item[1]))
        reuse_score = min(10, reusable[0][0] + len(reusable))
        rationale = ("existing adapter overlap",)
    else:
        reuse_score = 0
        rationale = ("no existing adapter overlap",)

    if gap.source_class in {"PUBLIC_PROCUREMENT", "PUBLIC_GRANTS", "REGULATOR"}:
        breadth_score = 8
    elif gap.source_class in {"GITHUB", "OPEN_SOURCE_HOSTING", "BUG_BOUNTY_PLATFORM"}:
        breadth_score = 7
    else:
        breadth_score = 5

    evidence_score = 2 if gap.source_class == "OTHER_WEB" else 5
    freshness_score = 5
    friction_score = 2 if reusable else 5

    score = (
        w["reuse"] * reuse_score
        + w["breadth"] * breadth_score
        + w["freshness"] * freshness_score
        + w["evidence"] * evidence_score
        - w["friction"] * friction_score
    )

    if not reusable and gap.source_class in {"PUBLIC_PROCUREMENT", "REGULATOR"}:
        blockers.append("source adapter must be discovered and validated")

    return GapPlan(
        gap=gap,
        score=score,
        reusable_adapters=tuple(x[1] for x in reusable),
        blockers=tuple(blockers),
        rationale=rationale + ("score is an engineering heuristic",),
    )


def prioritize_gaps(
    gaps: tuple[CoverageGap, ...],
    adapters: tuple[SourceAdapterContract, ...] = (),
    *,
    limit: int | None = 100,
) -> tuple[GapPlan, ...]:
    plans = tuple(plan_gap(gap, adapters) for gap in gaps)
    ranked = tuple(sorted(
        plans,
        key=lambda p: (-p.score, p.gap.key),
    ))
    return ranked if limit is None else ranked[:limit]


__all__ = ["GapPlan", "plan_gap", "prioritize_gaps", "DEFAULT_WEIGHTS"]
