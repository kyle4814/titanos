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
    "TaskValue", "SCORING_MODEL_VERSION", "select_next",
    "RecoveryHandoff", "recovery_handoff",
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


SCORING_MODEL_VERSION = "1"


@dataclass(frozen=True)
class TaskValue:
    """Why one task should be done before another.

    THE LAW THIS EXISTS FOR: "the scheduler selects the highest-value
    sufficiently-verifiable task, NOT MERELY THE OLDEST TASK." Before this,
    `run()` took `eligible[0]` in load order and `Task` had no value axis
    at all, so highest-value selection was not merely unimplemented -- it
    was structurally impossible.

    EVERY FACTOR IS OPTIONAL AND NONE DEFAULTS TO ZERO. An unestimated
    factor is `None`, and a task with any `None` factor is UNSCORED rather
    than scored low -- the same rule `foundation/value_model.py` already
    enforces for money: UNKNOWN is not ZERO. A queue that silently ranked
    unestimated work at the bottom would bury exactly the tasks nobody has
    looked at yet.

    The score is a NAVIGATION AID, not a truth. It is versioned
    (`SCORING_MODEL_VERSION`) precisely because it will be wrong and will
    need to change, and `assumptions` records what the estimate rests on.
    """

    value: Optional[float] = None
    dependency_unlock: Optional[float] = None
    reuse: Optional[float] = None
    risk_reduction: Optional[float] = None
    execution_cost: Optional[float] = None
    verification_cost: Optional[float] = None
    assumptions: tuple[str, ...] = ()
    model_version: str = SCORING_MODEL_VERSION

    _FACTORS = ("value", "dependency_unlock", "reuse", "risk_reduction",
                "execution_cost", "verification_cost")

    def unestimated(self) -> tuple[str, ...]:
        return tuple(f for f in self._FACTORS if getattr(self, f) is None)

    def is_scoreable(self) -> bool:
        return not self.unestimated()

    def score(self) -> Optional[float]:
        """Benefit over cost. None when any factor was never estimated.

        Deliberately returns None rather than a number: a caller that wants
        to rank must decide what to do about unestimated work, and cannot
        be handed a fabricated zero to sort by.
        """
        if not self.is_scoreable():
            return None
        benefit = (self.value + self.dependency_unlock + self.reuse
                   + self.risk_reduction)
        cost = self.execution_cost + self.verification_cost
        # Cost floors at 1 so a zero-cost claim cannot produce infinity --
        # a task asserting it is free is not thereby infinitely valuable.
        return benefit / max(cost, 1.0)

    def show_the_math(self) -> str:
        if not self.is_scoreable():
            return (f"UNSCORED -- never estimated: "
                    f"{', '.join(self.unestimated())}")
        lines = [f"SCORE {self.score():.3f}  (model v{self.model_version})",
                 f"  + value             {self.value}",
                 f"  + dependency_unlock {self.dependency_unlock}",
                 f"  + reuse             {self.reuse}",
                 f"  + risk_reduction    {self.risk_reduction}",
                 f"  / execution_cost    {self.execution_cost}",
                 f"  / verification_cost {self.verification_cost}"]
        for a in self.assumptions:
            lines.append(f"  assumption: {a}")
        return "\n".join(lines)


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
    task_value: Optional[TaskValue] = None

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
        """PENDING tasks whose every dependency is DONE, in load order.

        Load order is the ENUMERATION order, not the selection order --
        `select_next()` decides what runs. Kept separate so that "what is
        eligible" stays a fact about dependencies and "what runs next"
        stays a judgement about value.
        """
        eligible = []
        for task in self.all_tasks():
            if task.state != "PENDING":
                continue
            # Fail-closed: a dependency on an unknown task_id must never
            # be silently skipped as vacuously satisfied — that would
            # make an ineligible task (per validate()'s own "unknown
            # dependency" finding) eligible anyway. Found by
            # foundation/tests/test_queue_worker_adapter.py's T8 case.
            if all(d in self._tasks and self._tasks[d].state == "DONE" for d in task.dependencies):
                eligible.append(task)
        return tuple(eligible)


def select_next(eligible: "tuple[Task, ...]") -> Optional[Task]:
    """Highest-value scoreable task, load order only as a tie-break.

    UNSCORED WORK IS NOT RANKED LAST. If nothing eligible carries an
    estimate, the oldest is returned -- FIFO remains the honest fallback
    when there is no value information, rather than the default when
    there is. If SOME tasks are scored, an unscored one is not silently
    outranked by a low-scoring estimate either: unscored tasks are
    returned only when no scored task is eligible, and `unscored_eligible`
    lets a caller see them rather than lose them.

    A scheduler that invents a zero for unestimated work would bury
    exactly the tasks nobody has assessed yet.
    """
    if not eligible:
        return None
    scored = [t for t in eligible
              if t.task_value is not None and t.task_value.is_scoreable()]
    if scored:
        best = max(scored, key=lambda t: t.task_value.score())
        top = best.task_value.score()
        # Ties resolve by load order, preserving the old behaviour exactly
        # where value genuinely cannot discriminate.
        for t in eligible:
            if (t.task_value is not None and t.task_value.is_scoreable()
                    and t.task_value.score() == top):
                return t
        return best
    return eligible[0]


def unscored_eligible(eligible: "tuple[Task, ...]") -> tuple[Task, ...]:
    """Eligible work carrying no usable estimate. Visible, not buried."""
    return tuple(t for t in eligible
                 if t.task_value is None or not t.task_value.is_scoreable())


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
    # Eligible-but-not-started task_ids at the moment this run stopped —
    # explicit deferral (MAGL_CAP_002), not a new task state. A deferred
    # task's own `state` stays exactly what it already was (PENDING) —
    # pressure reduces how much work a run STARTS, it never touches a
    # task's own state machine.
    deferred: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RecoveryHandoff:
    """The minimum durable information a fresh session/model needs to
    resume this queue without any prior chat context — built entirely
    from `TaskQueue`/`RunReport`, no second memory system. Per MAGL_
    CAP_002's Recovery Contract: current run state, next atomic action,
    relevant task ids, what still needs verification, and any known
    blocker — nothing else.
    """
    run_state: str
    next_atomic_action: Optional[str]  # a task_id, or None if nothing is pending
    relevant_task_ids: tuple[str, ...]
    verification_required: tuple[str, ...]  # task_ids left IN_PROGRESS
    known_blockers: tuple[tuple[str, str], ...]  # (task_id, failure_reason) for FAILED tasks


def recovery_handoff(queue: TaskQueue, report: RunReport) -> RecoveryHandoff:
    """Build a `RecoveryHandoff` from the queue's actual current state and
    the just-completed run's report. Read-only — inspects, does not
    mutate, and does not guess: an IN_PROGRESS task found here still
    requires `reconcile_in_progress()` before a future run may trust it,
    exactly as before this function existed.
    """
    in_progress = tuple(t.task_id for t in queue.all_tasks() if t.state == "IN_PROGRESS")
    known_blockers = tuple(
        (t.task_id, t.failure_reason) for t in queue.all_tasks() if t.state == "FAILED"
    )
    failed_ids = tuple(tid for tid, _ in known_blockers)
    next_action = report.deferred[0] if report.deferred else None
    # Order preserved, duplicates removed — a task can appear in at most
    # one of deferred/in_progress/failed at a time (mutually exclusive
    # states), but dedup defensively rather than assuming that forever.
    relevant = tuple(dict.fromkeys(report.deferred + in_progress + failed_ids))
    return RecoveryHandoff(
        run_state=report.stopped_reason,
        next_atomic_action=next_action,
        relevant_task_ids=relevant,
        verification_required=in_progress,
        known_blockers=known_blockers,
    )


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

    def _stop(reason: str) -> RunReport:
        # Explicit deferral (MAGL_CAP_002): whatever is still eligible
        # at the moment we stop is reported, not silently left for a
        # future caller to rediscover by re-querying the queue. The
        # tasks themselves are untouched — still PENDING, nothing here
        # transitions or claims them.
        deferred = tuple(t.task_id for t in queue.eligible_tasks())
        return RunReport(tuple(completed), tuple(failed), reason, deferred)

    while True:
        if task_count >= effective_max_tasks:
            return _stop("max_tasks reached (after verification_reserve)")
        if len(failed) >= budget.max_failures:
            return _stop("max_failures reached")
        if budget.time_budget_seconds is not None and (
            time.monotonic() - started
        ) >= budget.time_budget_seconds:
            return _stop("time_budget_seconds reached")

        eligible = queue.eligible_tasks()
        if not eligible:
            return _stop("no eligible tasks remain")

        task = select_next(eligible)
        if task is None:                      # pragma: no cover - guarded above
            return _stop("no eligible tasks remain")
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
