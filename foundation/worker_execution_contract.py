"""Bounded execution envelope for TitanOS workers.

The contract describes what a worker may attempt and what it must return.
It does not itself grant consequential authority.
"""

from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class WorkerExecutionContract:
    worker_id: str
    opportunity_id: str
    objective: str
    allowed_tools: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    forbidden_actions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    stop_conditions: tuple[str, ...] = ()
    escalation_conditions: tuple[str, ...] = ()
    authority_ceiling: str = "O1"
    receipt_schema: str = "default"

    def __post_init__(self) -> None:
        if not self.worker_id.strip() or not self.opportunity_id.strip():
            raise ValueError("worker_id and opportunity_id are required")
        if self.authority_ceiling not in {"O0", "O1", "O2", "O3", "O4"}:
            raise ValueError("invalid authority ceiling")

__all__ = ["WorkerExecutionContract"]
