"""Worker health telemetry and deterministic scheduling signals."""
from __future__ import annotations
from dataclasses import dataclass, field
from time import monotonic

@dataclass(frozen=True)
class WorkerHealth:
    worker_id: str
    completed: int = 0
    failed: int = 0
    escalated: int = 0
    total_latency_ms: float = 0.0
    heartbeats: int = 0
    missed_heartbeats: int = 0
    retries: int = 0

    @property
    def throughput(self) -> float:
        total = self.completed + self.failed
        return total / (self.total_latency_ms / 1000.0) if total and self.total_latency_ms > 0 else 0.0

    @property
    def failure_rate(self) -> float:
        total = self.completed + self.failed
        return self.failed / total if total else 0.0

    @property
    def heartbeat_reliability(self) -> float:
        total = self.heartbeats + self.missed_heartbeats
        return self.heartbeats / total if total else 1.0

@dataclass
class WorkerHealthBook:
    workers: dict[str, WorkerHealth] = field(default_factory=dict)

    def record(self, worker_id: str, *, status: str, latency_ms: float = 0.0,
               heartbeat: bool = False, missed_heartbeat: bool = False,
               retry: bool = False) -> WorkerHealth:
        h=self.workers.get(worker_id, WorkerHealth(worker_id))
        h=WorkerHealth(
            worker_id, h.completed + (status=="COMPLETED"),
            h.failed + (status=="FAILED"), h.escalated + (status=="ESCALATED"),
            h.total_latency_ms + max(0.0, latency_ms),
            h.heartbeats + heartbeat, h.missed_heartbeats + missed_heartbeat,
            h.retries + retry)
        self.workers[worker_id]=h
        return h

    def rank(self, worker_ids: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(worker_ids, key=lambda wid: (
            -self.workers.get(wid, WorkerHealth(wid)).throughput,
            self.workers.get(wid, WorkerHealth(wid)).failure_rate,
            wid)))

__all__=["WorkerHealth","WorkerHealthBook"]
