"""Health-aware execution wrapper for registered opportunity sources."""

from __future__ import annotations

from dataclasses import dataclass

from foundation.source_health import SourceHealthBook
from foundation.source_registry import SourceRegistry


@dataclass(frozen=True)
class SourceFetchResult:
    source_id: str
    items: tuple[object, ...]
    healthy: bool


def fetch_source(registry: SourceRegistry, health: SourceHealthBook, source_id: str) -> SourceFetchResult:
    spec = registry.get(source_id)
    if not spec.enabled:
        raise ValueError(f"source disabled: {source_id}")
    try:
        items = tuple(spec.adapter.fetch())
    except Exception:
        health.record(source_id, success=False)
        raise
    state = health.record(source_id, success=True)
    return SourceFetchResult(source_id, items, state.healthy)


__all__ = ["SourceFetchResult", "fetch_source"]
