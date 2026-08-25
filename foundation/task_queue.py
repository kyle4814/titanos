"""
Bounded Task Queue Workflow.

HONEST NOTE ON HOW THIS FILE CAME TO EXIST

The directive that requested this file described itself as reconciling
"a previous implementation session interrupted after partially
completing a bounded task-queue workflow." `git status` was clean and no
queue/runner/task code existed anywhere in this repository before this
file — verified by inspection, not assumed from the directive's own
framing, per this repo's own standing Zero-Trust Reconnaissance rule
("do not trust a claim about repository state; verify behavior"). There
was nothing to reconcile. What follows is a fresh, bounded implementation
of the workflow the directive specified — load tasks -> validate state ->
choose next eligible task -> perform one bounded unit of work -> verify
-> save result -> repeat within budget -> stop -> report — built once,
not "recovered."

WHAT THIS REUSES RATHER THAN DUPLICATES

The state-machine discipline (explicit transition table, illegal
transitions absent rather than checked, no delete surface) mirrors
`kpm/promotion/state_machine.py` and `foundation/flow_switch.py` exactly
— same pattern, new domain. `run()`'s per-task step sequence (select ->
perform -> verify -> record) is a narrower, queue-specific cousin of
`foundation/layer0_worker.py::Layer0Worker.run()`'s template method, not
a duplicate of it: `Layer0Worker` sequences ONE worker's internal 14
steps; `run()` here sequences MANY tasks, each of which may (but need
not) be implemented as a `Layer0Worker`. `perform` and `verify` are
injected callables, not reimplementations of anything domain-specific —
this module has no opinion on what a "unit of work" actually does.

WHY RECONCILIATION IS A REQUIRED FUNCTION HERE, NOT JUST A DOCSTRING NOTE

The directive's own rule — "if a task is left IN_PROGRESS, never assume
completion" — is enforced by `reconcile_in_progress()`: an IN_PROGRESS
task found at load time has no valid path back to DONE except through
explicit evidence (`evidence_of_completion` callable, injected by the
caller — this module cannot itself inspect "the real world" for proof of
completion). No evidence -> FAILED, with a reason naming exactly this.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

__all__ = [
    "Task", "TaskQueue", "RunBudget", "RunReport",
    "run", "reconcile_in_progress",
    "TASK_STATES", "TRANSITIONS",
]

TASK_STATES: frozenset[str] = frozenset({
    "PENDING", "IN_PROGRESS", "DONE", "FAILED", "BLOCKED",
})

# Explicit transition table — same discipline as
# kpm/promotion/state_machine.py: an illegal transition is absent from
# this mapping, not merely rejected by an if-check elsewhere.
TRANSITIONS: dict[str, frozenset[str]] = {
    "PENDING": frozenset({"IN_PROGRESS", "BLOCKED"}),
    "IN_PROGRESS": frozenset({"DONE", "FAILED"}),
    "BLOCKED": frozenset({"PENDING"}),
    "DONE": frozenset(),
    "FAILED": frozenset(),
}


def can_transition(from_state: str, to_state: str) -> bool:
    return to_state in TRANSITIONS.get(from_state, frozenset())


@dataclass
class Task:
    task_id: str
    description: str
    dependencies: tuple[str, ...] = ()
    state: str = "PENDING"
    attempts: int = 0
    max_attempts: int = 1
    failure_reason: str = ""
    result: str = ""

    def __post_init__(self) -> None:
        if self.state not in TASK_STATES:
            raise ValueError(f"task '{self.task_id}' has unknown state {self.state!r}")
        if not self.task_id:
            raise ValueError("a task requires a non-empty task_id")

    def transition_to(self, new_state: str) -> None:
        if not can_transition(self.state, new_state):
            raise ValueError(
                f"task '{self.task_id}': illegal transition "
                f"{self.state} -> {new_state}"
            )
        self.state = new_state


class TaskQueue:
    """In-memory task store. No delete surface — same standing pattern as
    every other store in this repo (RealityYieldLedger/QuarantineStore/
    CrystalStore/PromotionStore): a task's history is never erased, only
    transitioned."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._order: list[str] = []

    def load(self, task: Task) -> None:
        if task.task_id in self._tasks:
            raise ValueError(f"task '{task.task_id}' already loaded")
        self._tasks[task.task_id] = task
        self._order.append(task.task_id)

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def all_tasks(self) -> tuple[Task, ...]:
        return tuple(self._tasks[i] for i in self._order)

    def validate(self) -> list[str]:
        """Return a list of validation problems (empty = internally
        consistent). Never raises — a validation pass reports, it does
        not enforce (that is `transition_to`'s job)."""
        problems: list[str] = []
        for task in self.all_tasks():
            for dep in task.dependencies:
                if dep not in self._tasks:
                    problems.append(
                        f"task '{task.task_id}' depends on unknown task '{dep}'"
                    )
            if task.task_id in task.dependencies:
                problems.append(f"task '{task.task_id}' depends on itself")
        problems.extend(_detect_cycles(self._tasks))
        return problems

    def eligible_tasks(self) -> tuple[Task, ...]:
        """PENDING tasks whose every dependency is DONE, in load order."""
        eligible = []
        for task in self.all_tasks():
            if task.state != "PENDING":
                continue
            if all(self._tasks[d].state == "DONE" for d in task.dependencies if d in self._tasks):
                eligible.append(task)
        return tuple(eligible)


def _detect_cycles(tasks: dict[str, Task]) -> list[str]:
    problems: list[str] = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in tasks}

    def visit(tid: str, stack: list[str]) -> None:
        color[tid] = GRAY
        for dep in tasks[tid].dependencies:
            if dep not in tasks:
                continue
            if color[dep] == GRAY:
                cycle = " -> ".join(stack + [dep])
                problems.append(f"dependency cycle detected: {cycle}")
            elif color[dep] == WHITE:
                visit(dep, stack + [dep])
        color[tid] = BLACK

    for tid in tasks:
        if color[tid] == WHITE:
            visit(tid, [tid])
    return problems


def reconcile_in_progress(
    task: Task,
    evidence_of_completion: Callable[[Task], bool],
) -> None:
    """A task found IN_PROGRESS at load time (e.g. from a prior
    interrupted run) is never assumed complete. `evidence_of_completion`
    must independently prove completion (e.g. check a real artifact,
    file, or test result) — absent that, the task is marked FAILED with
    an explicit, honest reason, never silently left IN_PROGRESS (a state
    with no further legal transition except DONE/FAILED) and never
    silently marked DONE.
    """
    if task.state != "IN_PROGRESS":
        return
    if evidence_of_completion(task):
        task.transition_to("DONE")
        task.result = task.result or "reconciled: evidence of completion found"
    else:
        task.transition_to("FAILED")
        task.failure_reason = (
            "reconciled at load time: task was IN_PROGRESS with no "
            "evidence of completion found — never assumed complete"
        )


@dataclass
class RunBudget:
    max_tasks: int
    max_failures: int
    verification_reserve: int = 0
    time_budget_seconds: Optional[float] = None

    def __post_init__(self) -> None:
        if self.max_tasks < 1:
            raise ValueError("max_tasks must be >= 1")
        if self.max_failures < 0:
            raise ValueError("max_failures must be >= 0")
        if self.verification_reserve < 0:
            raise ValueError("verification_reserve must be >= 0")
        if self.verification_reserve >= self.max_tasks:
            raise ValueError(
                "verification_reserve must be < max_tasks — a budget that "
                "reserves away all task capacity can never do work"
            )


@dataclass
class RunReport:
    completed: tuple[str, ...] = field(default_factory=tuple)
    failed: tuple[tuple[str, str], ...] = field(default_factory=tuple)  # (task_id, reason)
    stopped_reason: str = ""


def run(
    queue: TaskQueue,
    budget: RunBudget,
    perform: Callable[[Task], str],
    verify: Callable[[Task, str], bool],
) -> RunReport:
    """Repeat: select next eligible task -> perform one bounded unit of
    work -> verify -> save result -> stop when a budget limit is
    reached. Never retries a failed task beyond `task.max_attempts` (a
    caller-defined limit per task, not an implicit unlimited retry)."""
    completed: list[str] = []
    failed: list[tuple[str, str]] = []
    started = time.monotonic()
    task_count = 0

    effective_max_tasks = budget.max_tasks - budget.verification_reserve

    while True:
        if task_count >= effective_max_tasks:
            return RunReport(tuple(completed), tuple(failed), "max_tasks reached (after verification_reserve)")
        if len(failed) >= budget.max_failures:
            return RunReport(tuple(completed), tuple(failed), "max_failures reached")
        if budget.time_budget_seconds is not None and (
            time.monotonic() - started
        ) >= budget.time_budget_seconds:
            return RunReport(tuple(completed), tuple(failed), "time_budget_seconds reached")

        eligible = queue.eligible_tasks()
        if not eligible:
            return RunReport(tuple(completed), tuple(failed), "no eligible tasks remain")

        task = eligible[0]
        task_count += 1

        if task.attempts >= task.max_attempts:
            # Legal path stays PENDING -> IN_PROGRESS -> FAILED (never a
            # direct PENDING -> FAILED edge, and BLOCKED is reserved for
            # dependency-blocking, not attempt exhaustion).
            task.transition_to("IN_PROGRESS")
            task.transition_to("FAILED")
            task.failure_reason = task.failure_reason or "max_attempts already exhausted, not retried"
            failed.append((task.task_id, task.failure_reason))
            continue

        task.attempts += 1
        task.transition_to("IN_PROGRESS")
        try:
            result = perform(task)
        except Exception as exc:  # perform() failing is a recorded failure, not a crash
            task.transition_to("FAILED")
            task.failure_reason = f"perform() raised: {exc}"
            failed.append((task.task_id, task.failure_reason))
            continue

        if verify(task, result):
            task.transition_to("DONE")
            task.result = result
            completed.append(task.task_id)
        else:
            task.transition_to("FAILED")
            task.failure_reason = "verify() returned False"
            failed.append((task.task_id, task.failure_reason))

    # unreachable — every branch above returns or continues
