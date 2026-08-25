"""
Queue <-> Layer0Worker Adapter (MAGL_FND_003 — Canonical Execution Seam).

WHAT THIS FILE IS

The thinnest possible bridge between `foundation/task_queue.py::run()`'s
`perform`/`verify` callable contract and `foundation/layer0_worker.py::
Layer0Worker.run()`'s zero-argument template method. **Neither file is
modified.** Both keep their existing, independently-tested contracts
exactly as they were (task_queue: 32 tests; layer0_worker: 18 tests) —
this module only wires them together from the outside.

WHY AN ADAPTER RATHER THAN A CHANGE TO EITHER FILE

`task_queue.run()`'s `perform` signature is `Callable[[Task], str]` —
one argument in, a string out. `Layer0Worker.run()` takes no arguments
and returns a `CycleRecord`, not a string. These are genuinely
incompatible shapes, not a naming mismatch that could be papered over —
per the directive's own rule ("if the seam cannot be implemented without
changing established contracts, stop at the boundary, document the
exact mismatch, and do not invent a large abstraction"), the correct
move is a small explicit bridge, not a redesign of either module.

HOW A WORKER RECEIVES ITS TASK-DERIVED INPUT

This adapter does not reach into a worker's internals to hand it a task
— that is the worker subclass's own concern (via its constructor or its
`observe()` override), exactly as `layer0_worker.py`'s own docstring
already establishes: "how a worker receives its task-derived input" is a
subclass decision. `worker_factory(task)` is the seam's actual contract:
given a `Task`, produce a `Layer0Worker` instance already configured to
operate on it.

WHY SUCCESS IS DETECTED VIA `"UPDATE_STATE" in record.steps_completed`,
NOT VIA `record.halted`

`Layer0Worker.run()` sets `halted=True` in two structurally different
situations: (a) permission denied or its own `verify()` failed — a real
failure, before or without ever reaching `update_state()`; and (b) the
formal stop condition was met *after* a fully successful cycle (`update_
state()` already ran) — the worker recommending it stop future
recursion, not reporting failure. Checking `record.halted` alone would
misclassify case (b) as a queue-level failure. `update_state()` only
ever executes on the worker's success path (see `Layer0Worker.run()`'s
own step sequence) — its presence in `steps_completed` is therefore the
one precise, contract-guaranteed signal, not a fragile string match on
`halt_reason` text.

STATE LAW COMPLIANCE

No successful Python return automatically means verified/completed
(directive's own rule) — `make_worker_verify()`'s `verify` callable is a
real check against the recorded `CycleRecord`, not a pass-through. A
missing record (perform() never ran for this task_id, or was never
invoked) is treated as unverified, never as success — "if the result is
ambiguous, preserve evidence and stop that task's promotion."
"""

from __future__ import annotations

from typing import Callable

from foundation.layer0_worker import CycleRecord, Layer0Worker
from foundation.task_queue import Task

__all__ = ["make_worker_perform", "make_worker_verify"]


def make_worker_perform(
    worker_factory: Callable[[Task], Layer0Worker],
    records: dict[str, CycleRecord],
) -> Callable[[Task], str]:
    """`perform` callable, compatible with `task_queue.run()`.

    `records` is a caller-owned dict this function writes into, keyed by
    `task.task_id` — the explicit, inspectable hand-off to the paired
    `verify` callable from `make_worker_verify()`. A worker that raises
    during `run()` propagates the exception unchanged; `task_queue.run()`
    already catches it and records an explicit task failure (its
    existing, unmodified behaviour — G4).
    """
    def perform(task: Task) -> str:
        worker = worker_factory(task)
        record = worker.run()
        records[task.task_id] = record
        return record.halt_reason or "completed"
    return perform


def make_worker_verify(records: dict[str, CycleRecord]) -> Callable[[Task, str], bool]:
    """`verify` callable, compatible with `task_queue.run()`.

    Completion requires the worker's CycleRecord to show `UPDATE_STATE`
    among its completed steps — the one step that only ever runs after
    `execute_minimum` succeeded AND the worker's own `verify()` passed.
    A record that halted before reaching it (permission denied, worker
    verification failed) or an absent record both return False.
    """
    def verify(task: Task, result: str) -> bool:
        record = records.get(task.task_id)
        if record is None:
            return False
        return "UPDATE_STATE" in record.steps_completed
    return verify
