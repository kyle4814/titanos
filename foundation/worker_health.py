"""Worker health telemetry, quarantine, and deterministic scheduling signals."""
from __future__ import annotations
from dataclasses import dataclass, field

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
    quarantined: bool = False

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
        h = self.workers.get(worker_id, WorkerHealth(worker_id))
        h = WorkerHealth(
            worker_id, h.completed + (status == "COMPLETED"),
            h.failed + (status == "FAILED"), h.escalated + (status == "ESCALATED"),
            h.total_latency_ms + max(0.0, latency_ms),
            h.heartbeats + heartbeat, h.missed_heartbeats + missed_heartbeat,
            h.retries + retry, h.quarantined)
        self.workers[worker_id] = h
        return h

    def record_retry_failure(self, worker_id: str, *, quarantine_after: int = 3,
                             latency_ms: float = 0.0) -> WorkerHealth:
        if quarantine_after < 1:
            raise ValueError("quarantine_after must be positive")
        h = self.record(worker_id, status="FAILED", latency_ms=latency_ms, retry=True)
        if h.retries >= quarantine_after:
            return self.quarantine(worker_id)
        return h

    def record_success(self, worker_id: str, *, latency_ms: float = 0.0) -> WorkerHealth:
        h = self.record(worker_id, status="COMPLETED", latency_ms=latency_ms)
        if h.quarantined:
            return self.recover(worker_id)
        return h

    def quarantine(self, worker_id: str) -> WorkerHealth:
        h = self.workers.get(worker_id, WorkerHealth(worker_id))
        updated = WorkerHealth(h.worker_id, h.completed, h.failed, h.escalated,
                               h.total_latency_ms, h.heartbeats,
                               h.missed_heartbeats, h.retries, True)
        self.workers[worker_id] = updated
        return updated

    def recover(self, worker_id: str) -> WorkerHealth:
        h = self.workers.get(worker_id, WorkerHealth(worker_id))
        updated = WorkerHealth(h.worker_id, h.completed, h.failed, h.escalated,
                               h.total_latency_ms, h.heartbeats,
                               h.missed_heartbeats, h.retries, False)
        self.workers[worker_id] = updated
        return updated

    def rank(self, worker_ids: tuple[str, ...]) -> tuple[str, ...]:
        eligible = tuple(wid for wid in worker_ids if not self.workers.get(wid, WorkerHealth(wid)).quarantined)
        return tuple(sorted(eligible, key=lambda wid: (
            -self.workers[wid].throughput if wid in self.workers else 0.0,
            self.workers.get(wid, WorkerHealth(wid)).failure_rate, wid)))

__all__ = ["WorkerHealth", "WorkerHealthBook"]