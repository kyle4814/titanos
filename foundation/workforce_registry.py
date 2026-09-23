"""Declarative TitanOS workforce registry.

Worker definitions are capability contracts, not live processes. They can be
materialized into Claude Code/subagent jobs by a higher-level dispatcher.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

@dataclass(frozen=True)
class WorkerSpec:
    worker_id: str
    domain: str
    capabilities: tuple[str, ...] = ()
    preferred_model: str = "sonnet"
    fallback_model: str = "haiku"
    tools: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    authority_ceiling: str = "O1"
    description: str = ""

    def __post_init__(self) -> None:
        if not self.worker_id.strip():
            raise ValueError("worker_id is required")
        if self.authority_ceiling not in {"O0", "O1", "O2", "O3", "O4"}:
            raise ValueError("invalid authority ceiling")

@dataclass(frozen=True)
class WorkforceRegistry:
    workers: Mapping[str, WorkerSpec] = field(default_factory=dict)

    def register(self, spec: WorkerSpec) -> "WorkforceRegistry":
        if spec.worker_id in self.workers:
            raise ValueError(f"worker already registered: {spec.worker_id}")
        updated = dict(self.workers)
        updated[spec.worker_id] = spec
        return WorkforceRegistry(updated)

    def get(self, worker_id: str) -> WorkerSpec:
        try:
            return self.workers[worker_id]
        except KeyError as exc:
            raise KeyError(f"unknown worker: {worker_id}") from exc

    def match(self, capabilities: set[str], *, domain: str | None = None) -> tuple[WorkerSpec, ...]:
        matches = [
            w for w in self.workers.values()
            if (domain is None or w.domain == domain)
            and capabilities.issubset(set(w.capabilities))
        ]
        return tuple(sorted(matches, key=lambda w: (w.preferred_model, w.worker_id)))

__all__ = ["WorkerSpec", "WorkforceRegistry"]
