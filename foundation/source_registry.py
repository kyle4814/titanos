"""Deterministic registry for modular opportunity source adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SourceAdapter(Protocol):
    def fetch(self) -> tuple[object, ...]:
        ...


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    category: str
    adapter: SourceAdapter
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.category.strip():
            raise ValueError("source_id and category are required")


class SourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, SourceSpec] = {}

    def register(self, source: SourceSpec) -> "SourceRegistry":
        if source.source_id in self._sources:
            raise ValueError(f"source already registered: {source.source_id}")
        self._sources[source.source_id] = source
        return self

    def enable(self, source_id: str) -> "SourceRegistry":
        self._sources[source_id] = SourceSpec(
            source_id, self._sources[source_id].category,
            self._sources[source_id].adapter, True
        )
        return self

    def disable(self, source_id: str) -> "SourceRegistry":
        source = self._sources[source_id]
        self._sources[source_id] = SourceSpec(
            source.source_id, source.category, source.adapter, False
        )
        return self

    def active(self) -> tuple[SourceSpec, ...]:
        return tuple(self._sources[key] for key in sorted(self._sources) if self._sources[key].enabled)

    def get(self, source_id: str) -> SourceSpec:
        return self._sources[source_id]

__all__ = ["SourceAdapter", "SourceSpec", "SourceRegistry"]
