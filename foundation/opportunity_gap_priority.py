"""Dependency-aware engineering prioritization for opportunity coverage gaps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from foundation.opportunity_coverage_gaps import CoverageGap
from foundation.source_adapter_contract import SourceAdapterContract


DEFAULT_WEIGHTS: Final[dict[str, int]] = {
    "reuse": 5,
    "breadth": 4,
    "evidence": 3,
    "freshness": 2,
    "effort": 3,
}


@dataclass(frozen=True)
class GapPriority:
    gap: CoverageGap
    score: int
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "gap": self.gap.to_dict(),
            "score": self.score,
            "reasons": self.reasons,
        }


def _overlap(adapter: SourceAdapterContract, gap: CoverageGap) -> int:
    if adapter.status in {"DISABLED", "RETIRED"}:
        return 0
    score = 0
    if not adapter.opportunity_types or gap.opportunity_type in adapter.opportunity_types:
        score += 1
    if not adapter.regions or gap.region in adapter.regions or "GLOBAL" in adapter.regions:
        score += 1
    if not adapter.jurisdictions or gap.jurisdiction in adapter.jurisdictions:
        score += 1
    if adapter.source_class == gap.source_class:
        score += 2
    return score


def prioritize_gaps(
    gaps: tuple[CoverageGap, ...],
    adapters: tuple[SourceAdapterContract, ...] = (),
    *,
    weights: dict[str, int] | None = None,
) -> tuple[GapPriority, ...]:
    """Rank engineering gaps by reusable infrastructure and explicit heuristics.

    This is not an economic or political ranking. It is a deterministic
    engineering queue signal and must not be presented as expected opportunity
    value.
    """
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    results: list[GapPriority] = []
    for gap in gaps:
        reusable = max((_overlap(a, gap) for a in adapters), default=0)
        breadth = sum(
            1 for a in adapters
            if a.status == "AVAILABLE"
            and (not a.opportunity_types or gap.opportunity_type in a.opportunity_types)
        )
        evidence = sum(
            1 for a in adapters
            if a.status == "AVAILABLE" and bool(a.evidence_fields)
        )
        freshness = sum(
            1 for a in adapters
            if a.status == "AVAILABLE" and a.update_cadence != "unknown"
        )
        effort_proxy = 1 if reusable >= 3 else 0

        score = (
            w["reuse"] * reusable
            + w["breadth"] * breadth
            + w["evidence"] * evidence
            + w["freshness"] * freshness
            + w["effort"] * effort_proxy
        )
        reasons = (
            f"reusable_adapter_overlap={reusable}",
            f"available_breadth={breadth}",
            f"evidence_ready_adapters={evidence}",
            f"freshness_declared_adapters={freshness}",
            f"effort_proxy={effort_proxy}",
        )
        results.append(GapPriority(gap=gap, score=score, reasons=reasons))

    return tuple(sorted(
        results,
        key=lambda item: (-item.score, item.gap.key),
    ))


__all__ = ["DEFAULT_WEIGHTS", "GapPriority", "prioritize_gaps"]
