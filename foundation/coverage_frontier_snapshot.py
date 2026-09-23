"""Durable frontier snapshot contract.

The existing OpportunityStore remains the persistence authority. This module
defines a narrow serialization envelope for coverage-frontier recovery, so a
future store adapter can persist/reload it without coupling the planner to a
specific database or filesystem.

A snapshot is descriptive state, not proof that work completed.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable

from foundation.coverage_frontier import FrontierItem


@dataclass(frozen=True)
class FrontierSnapshot:
    version: int
    items: tuple[FrontierItem, ...]
    source: str = "coverage_frontier"

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source": self.source,
            "items": [item.to_dict() for item in self.items],
        }

    def fingerprint(self) -> str:
        raw = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        payload = self.canonical_payload()
        payload["fingerprint"] = self.fingerprint()
        return payload


def make_snapshot(
    items: Iterable[FrontierItem],
    *,
    version: int = 1,
) -> FrontierSnapshot:
    ordered = tuple(sorted(items, key=lambda x: (-x.score, x.work_id)))
    return FrontierSnapshot(version=version, items=ordered)


def validate_snapshot(snapshot: FrontierSnapshot) -> None:
    if snapshot.version < 1:
        raise ValueError("snapshot version must be positive")
    if snapshot.fingerprint() == "":
        raise ValueError("snapshot fingerprint cannot be empty")


__all__ = ["FrontierSnapshot", "make_snapshot", "validate_snapshot"]
