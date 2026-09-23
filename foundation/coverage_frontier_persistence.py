"""Persistence port for the coverage frontier.

GitHub inspection found no indexed OpportunityStore implementation to bind to
on the current default branch. This port prevents us from inventing that API.
A concrete adapter can implement it once the canonical store location/API is
available.

The port is intentionally narrow: load/save snapshots only. It cannot commit
work, manufacture evidence, or bypass authority gates.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from foundation.coverage_frontier_snapshot import FrontierSnapshot


class FrontierPersistencePort(ABC):
    """Minimal persistence boundary for durable frontier state."""

    @abstractmethod
    def load(self) -> FrontierSnapshot | None:
        raise NotImplementedError

    @abstractmethod
    def save(self, snapshot: FrontierSnapshot) -> None:
        raise NotImplementedError


class InMemoryFrontierPersistence(FrontierPersistencePort):
    """Reference implementation for tests and local orchestration."""

    def __init__(self) -> None:
        self._snapshot: FrontierSnapshot | None = None

    def load(self) -> FrontierSnapshot | None:
        return self._snapshot

    def save(self, snapshot: FrontierSnapshot) -> None:
        self._snapshot = snapshot


__all__ = ["FrontierPersistencePort", "InMemoryFrontierPersistence"]
