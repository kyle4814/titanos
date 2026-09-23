"""Persistent frontier selection for TitanOS coverage work.

This module is deliberately storage-backend agnostic. It provides stable
identity, deterministic ordering, dependency-aware eligibility, and a
snapshot/restore contract so an external store can persist the frontier.
It does not execute work or bypass authority gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from foundation.coverage_work_queue import CoverageWorkItem, WORK_STATES


FRONTIER_STATES = frozenset({"DISCOVERED", "PREPARED", "READY"})


@dataclass(frozen=True)
class FrontierItem:
    work_id: str
    score: int
    state: str
    next_action: str
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.state not in WORK_STATES:
            raise ValueError(f"invalid frontier state: {self.state}")

    def to_dict(self) -> dict[str, object]:
        return {
            "work_id": self.work_id,
            "score": self.score,
            "state": self.state,
            "next_action": self.next_action,
            "blockers": self.blockers,
        }


def select_frontier(
    items: Iterable[CoverageWorkItem],
    *,
    limit: int = 1,
) -> tuple[FrontierItem, ...]:
    """Select resumable work deterministically.

    Only non-terminal, unblocked work is eligible. Higher score wins; ties
    resolve by work_id so two agents produce the same frontier.
    """
    eligible = [
        FrontierItem(
            work_id=item.work_id,
            score=item.score,
            state=item.state,
            next_action=item.next_action,
            blockers=item.blockers,
        )
        for item in items
        if item.state in FRONTIER_STATES and not item.blockers
    ]
    eligible.sort(key=lambda x: (-x.score, x.work_id))
    return tuple(eligible[:max(0, limit)])


def snapshot_frontier(items: Iterable[CoverageWorkItem]) -> tuple[dict[str, object], ...]:
    return tuple(x.to_dict() for x in select_frontier(items, limit=10_000))


__all__ = ["FrontierItem", "FRONTIER_STATES", "select_frontier", "snapshot_frontier"]
