"""Conflict-aware batch swarm planner.

Plans a bounded set of opportunities without assigning one worker to multiple
simultaneous jobs. Ordering is deterministic; eligibility remains mandatory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from foundation.swarm_planner import PlannedAssignment, plan_assignment
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
from foundation.workforce_registry import WorkforceRegistry

@dataclass(frozen=True)
class BatchPlan:
    assignments: tuple[PlannedAssignment, ...]
    deferred: tuple[str, ...]

@dataclass
class ActiveBatch:
    """In-memory capacity lease for a planned batch; completion releases slots."""
    plan: BatchPlan
    active: dict[str, str] = field(default_factory=dict)

    def start(self, opportunity_id: str) -> str:
        for a in self.plan.assignments:
            if a.opportunity_id == opportunity_id:
                if opportunity_id in self.active:
                    raise ValueError("opportunity already active")
                worker = a.workers[0]
                if worker in self.active.values():
                    raise ValueError("worker already active")
                self.active[opportunity_id] = worker
                return worker
        raise KeyError(opportunity_id)

    def complete(self, opportunity_id: str) -> str:
        try:
            return self.active.pop(opportunity_id)
        except KeyError as exc:
            raise KeyError(f"opportunity is not active: {opportunity_id}") from exc


    def heartbeat(self, opportunity_id: str, worker_id: str) -> bool:
        if self.active.get(opportunity_id) != worker_id:
            raise ValueError("heartbeat does not match active worker")
        return True

    def timeout(self, opportunity_id: str, health: WorkerHealthBook, *, retry: bool = True) -> str:
        worker = self.complete(opportunity_id)
        if retry:
            health.record_retry_failure(worker)
        else:
            health.record(worker, status="FAILED")
        return worker


    def schedule_timeout(self, opportunity_id: str, retry_queue: RetryQueue, now: int, *, quarantine_after: int = 3) -> tuple[str, bool]:
        worker = self.active.get(opportunity_id)
        if worker is None:
            raise KeyError(f"opportunity is not active: {opportunity_id}")
        worker = self.complete(opportunity_id)
        accepted = retry_queue.schedule(opportunity_id, now, worker)
        return worker, accepted

    def ready_retries(self, retry_queue: RetryQueue, now: int, health: WorkerHealthBook) -> tuple[str, ...]:
        return tuple(
            oid for oid in retry_queue.ready(now)
            if retry_queue.workers.get(oid) is None
            or not health.workers[retry_queue.workers[oid]].quarantined
        )

    def reassign_retry(self, opportunity_id: str, worker_id: str, retry_queue: "RetryQueue", health: WorkerHealthBook, now: int) -> str:
        """Consume a ready retry and lease it to a healthy alternative worker."""
        if opportunity_id not in retry_queue.ready(now):
            raise ValueError("retry is not ready")
        if health.workers.get(worker_id) and health.workers[worker_id].quarantined:
            raise ValueError("worker is quarantined")
        if opportunity_id in self.active:
            raise ValueError("opportunity already active")
        if worker_id in self.active.values():
            raise ValueError("worker already active")
        self.active[opportunity_id] = worker_id
        retry_queue.release(opportunity_id)
        return worker_id

    @property
    def capacity_used(self) -> int:
        return len(self.active)


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_backoff: int = 1
    max_backoff: int = 16

    def delay(self, attempt: int) -> int:
        if attempt < 1 or self.max_attempts < 1 or self.base_backoff < 1 or self.max_backoff < 1:
            raise ValueError("invalid retry policy")
        if attempt > self.max_attempts:
            return 0
        return min(self.max_backoff, self.base_backoff * (2 ** (attempt - 1)))

@dataclass
class RetryQueue:
    policy: RetryPolicy = field(default_factory=RetryPolicy)
    attempts: dict[str, int] = field(default_factory=dict)
    ready_at: dict[str, int] = field(default_factory=dict)
    workers: dict[str, str] = field(default_factory=dict)

    def schedule(self, opportunity_id: str, now: int, worker_id: str | None = None) -> bool:
        attempt = self.attempts.get(opportunity_id, 0) + 1
        if attempt > self.policy.max_attempts:
            return False
        self.attempts[opportunity_id] = attempt
        self.ready_at[opportunity_id] = now + self.policy.delay(attempt)
        if worker_id is not None:
            self.workers[opportunity_id] = worker_id
        return True

    def ready(self, now: int) -> tuple[str, ...]:
        return tuple(sorted(oid for oid, tick in self.ready_at.items() if tick <= now))

    def release(self, opportunity_id: str) -> None:
        self.ready_at.pop(opportunity_id, None)
        self.workers.pop(opportunity_id, None)


def plan_batch(registry: WorkforceRegistry, health: WorkerHealthBook,
               specialization: SpecializationBook,
               opportunities: tuple[tuple[str,str,set[str]], ...],
               max_active: int) -> BatchPlan:
    if max_active < 0: raise ValueError("max_active must be non-negative")
    used: set[str] = set()
    planned: list[PlannedAssignment] = []
    deferred: list[str] = []
    for oid, domain, caps in opportunities:
        try:
            assignment=plan_assignment(registry,health,specialization,oid,domain,caps)
        except LookupError:
            deferred.append(oid); continue
        available=tuple(w for w in assignment.workers if w not in used)
        if not available or len(planned) >= max_active:
            deferred.append(oid); continue
        selected=PlannedAssignment(oid,domain,available)
        planned.append(selected)
        used.add(available[0])
    return BatchPlan(tuple(planned),tuple(deferred))

__all__=["BatchPlan","ActiveBatch","RetryPolicy","RetryQueue","plan_batch"]
