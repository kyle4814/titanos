"""Canonical contract for TitanOS opportunity-source adapters.

Adapters are discovery components, not authorization bypasses. They describe
how an external source can be observed, what it can emit, and what evidence
it can produce. Consequential submissions/actions remain behind authorization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


ADAPTER_STATUSES: Final[tuple[str, ...]] = (
    "PLANNED", "AVAILABLE", "DEGRADED", "DISABLED", "RETIRED",
)

AUTH_MODES: Final[tuple[str, ...]] = (
    "PUBLIC", "API_KEY", "OAUTH", "SESSION", "MANUAL_HANDOFF",
    "PERMISSIONED", "UNKNOWN",
)

RETRIEVAL_METHODS: Final[tuple[str, ...]] = (
    "API", "RSS", "WEB", "SITEMAP", "GIT", "FILE", "MANUAL",
    "WEBHOOK", "CONNECTOR", "UNKNOWN",
)


@dataclass(frozen=True)
class SourceAdapterContract:
    adapter_id: str
    name: str
    status: str
    source_class: str
    source_family: str
    regions: tuple[str, ...] = ()
    jurisdictions: tuple[str, ...] = ()
    opportunity_types: tuple[str, ...] = ()
    auth_mode: str = "UNKNOWN"
    retrieval_methods: tuple[str, ...] = ()
    update_cadence: str = "unknown"
    rate_limit: str = "unknown"
    terms_reference: str = ""
    authorization_required: bool = False
    evidence_fields: tuple[str, ...] = ()
    parser_version: str = ""
    last_verified_at: str = ""

    def __post_init__(self) -> None:
        if self.status not in ADAPTER_STATUSES:
            raise ValueError(f"invalid adapter status: {self.status}")
        if self.auth_mode not in AUTH_MODES:
            raise ValueError(f"invalid auth mode: {self.auth_mode}")
        invalid = [m for m in self.retrieval_methods if m not in RETRIEVAL_METHODS]
        if invalid:
            raise ValueError(f"invalid retrieval methods: {invalid}")

    def coverage_key(self) -> str:
        return f"{self.source_class}:{self.source_family}:{self.adapter_id}"

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "name": self.name,
            "status": self.status,
            "source_class": self.source_class,
            "source_family": self.source_family,
            "regions": self.regions,
            "jurisdictions": self.jurisdictions,
            "opportunity_types": self.opportunity_types,
            "auth_mode": self.auth_mode,
            "retrieval_methods": self.retrieval_methods,
            "update_cadence": self.update_cadence,
            "rate_limit": self.rate_limit,
            "terms_reference": self.terms_reference,
            "authorization_required": self.authorization_required,
            "evidence_fields": self.evidence_fields,
            "parser_version": self.parser_version,
            "last_verified_at": self.last_verified_at,
        }


@dataclass
class AdapterRegistry:
    adapters: dict[str, SourceAdapterContract] = field(default_factory=dict)

    def register(self, adapter: SourceAdapterContract) -> None:
        existing = self.adapters.get(adapter.adapter_id)
        if existing is not None and existing != adapter:
            raise ValueError(f"adapter id already registered: {adapter.adapter_id}")
        self.adapters[adapter.adapter_id] = adapter

    def by_status(self, status: str) -> tuple[SourceAdapterContract, ...]:
        return tuple(a for a in self.adapters.values() if a.status == status)

    def coverage(self) -> dict[str, int]:
        return {
            "adapters": len(self.adapters),
            "available": len(self.by_status("AVAILABLE")),
            "planned": len(self.by_status("PLANNED")),
            "degraded": len(self.by_status("DEGRADED")),
            "disabled": len(self.by_status("DISABLED")),
            "retired": len(self.by_status("RETIRED")),
        }


__all__ = [
    "ADAPTER_STATUSES",
    "AUTH_MODES",
    "RETRIEVAL_METHODS",
    "SourceAdapterContract",
    "AdapterRegistry",
]
