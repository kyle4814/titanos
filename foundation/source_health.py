"""Source-adapter health and fetch telemetry."""

from __future__ import annotations

from dataclasses import dataclass

@dataclass
class SourceHealth:
    fetches: int = 0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        return self.successes / self.fetches if self.fetches else 0.0

    @property
    def healthy(self) -> bool:
        return self.consecutive_failures < 3

class SourceHealthBook:
    def __init__(self) -> None:
        self.sources: dict[str, SourceHealth] = {}

    def record(self, source_id: str, *, success: bool) -> SourceHealth:
        health = self.sources.setdefault(source_id, SourceHealth())
        health.fetches += 1
        if success:
            health.successes += 1
            health.consecutive_failures = 0
        else:
            health.failures += 1
            health.consecutive_failures += 1
        return health

__all__ = ["SourceHealth", "SourceHealthBook"]
