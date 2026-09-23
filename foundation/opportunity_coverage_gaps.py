"""Coverage-gap engine for TitanOS opportunity discovery.

The engine does not pretend every Cartesian cell needs a scraper. It emits
declared gaps from the dimensions we actually model, while allowing adapters
to cover multiple types/regions/jurisdictions/surfaces. Scoring is a planning
heuristic for engineering prioritization, not a claim about economic value.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Final

from foundation.opportunity_discovery_scope import (
    DISCOVERY_SURFACE_CLASSES,
    GLOBAL_REGION_GROUPS,
    JURISDICTION_TIERS,
)
from foundation.opportunity_scope import OPPORTUNITY_TYPES
from foundation.source_adapter_contract import SourceAdapterContract


DEFAULT_GAP_SCORE: Final[int] = 1


@dataclass(frozen=True)
class CoverageGap:
    opportunity_type: str
    region: str
    jurisdiction: str
    source_class: str
    score: int = DEFAULT_GAP_SCORE

    @property
    def key(self) -> str:
        return ":".join((
            self.opportunity_type,
            self.region,
            self.jurisdiction,
            self.source_class,
        ))

    def to_dict(self) -> dict[str, object]:
        return {
            "opportunity_type": self.opportunity_type,
            "region": self.region,
            "jurisdiction": self.jurisdiction,
            "source_class": self.source_class,
            "score": self.score,
            "key": self.key,
        }


def _covers(adapter: SourceAdapterContract, gap: CoverageGap) -> bool:
    if adapter.status in {"DISABLED", "RETIRED"}:
        return False
    type_ok = not adapter.opportunity_types or gap.opportunity_type in adapter.opportunity_types
    region_ok = not adapter.regions or gap.region in adapter.regions or "GLOBAL" in adapter.regions
    jurisdiction_ok = not adapter.jurisdictions or gap.jurisdiction in adapter.jurisdictions
    source_ok = adapter.source_class == gap.source_class
    return type_ok and region_ok and jurisdiction_ok and source_ok


def find_gaps(
    adapters: tuple[SourceAdapterContract, ...] = (),
    *,
    opportunity_types: tuple[str, ...] = OPPORTUNITY_TYPES,
    regions: tuple[str, ...] = GLOBAL_REGION_GROUPS,
    jurisdictions: tuple[str, ...] = JURISDICTION_TIERS,
    source_classes: tuple[str, ...] = DISCOVERY_SURFACE_CLASSES,
    limit: int | None = 500,
) -> tuple[CoverageGap, ...]:
    """Return uncovered declared cells without making economic claims."""
    gaps: list[CoverageGap] = []
    for opportunity_type, region, jurisdiction, source_class in product(
        opportunity_types, regions, jurisdictions, source_classes
    ):
        gap = CoverageGap(opportunity_type, region, jurisdiction, source_class)
        if not any(_covers(adapter, gap) for adapter in adapters):
            gaps.append(gap)
            if limit is not None and len(gaps) >= limit:
                break
    return tuple(gaps)


def rank_gaps(gaps: tuple[CoverageGap, ...]) -> tuple[CoverageGap, ...]:
    """Deterministically order gaps for engineering triage."""
    return tuple(sorted(
        gaps,
        key=lambda g: (-g.score, g.opportunity_type, g.region, g.jurisdiction, g.source_class),
    ))


__all__ = ["CoverageGap", "find_gaps", "rank_gaps"]
