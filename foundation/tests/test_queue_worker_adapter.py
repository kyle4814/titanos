import unittest
from typing import Any

from foundation.layer0_worker import CycleRecord, Layer0Worker
from foundation.queue_worker_adapter import make_worker_perform, make_worker_verify
from foundation.task_queue import RunBudget, Task, TaskQueue, run


class _SucceedingWorker(Layer0Worker):
    """A minimal, fully-compliant worker that always succeeds."""
    worker_id = "succeeding"

    def __init__(self, task: Task):
        self.task = task
        self.received_observation: Any = None

    def observe(self) -> Any:
        self.received_observation = self.task
        return self.task

    def check_existing(self, observation: Any) -> Any:
        return None

    def execute_minimum(self, lever: Any) -> Any:
        return f"did {self.task.task_id}"

    def verify(self, result: Any) -> bool:
        return True

    def preserve_provenance(self, result: Any, *, verified: bool) -> None:
        pass

    def update_state(self, result: Any, yield_signal: Any) -> None:
        pass


class _VerificationFailingWorker(_SucceedingWorker):
    worker_id = "verify-failing"

    def verify(self, result: Any) -> bool:
        return False


class _PermissionDeniedWorker(_SucceedingWorker):
    worker_id = "permission-denied"

    def request_permission_if_required(self, lever: Any) -> bool:
        return False


class _ExplodingWorker(_SucceedingWorker):
    worker_id = "exploding"

    def execute_minimum(self, lever: Any) -> Any:
        raise RuntimeError("worker blew up")


class TestSeamMatrix(unittest.TestCase):
    """T1-T10, per MAGL_FND_003's seam test matrix."""

    def _single_task_queue(self, task_id="T1") -> TaskQueue:
        q = TaskQueue()
        q.load(Task(task_id=task_id, description="do a thing"))
        return q

    def test_t1_t2_eligible_task_invokes_worker_with_task_derived_input(self):
        q = self._single_task_queue()
        records: dict = {}
        seen_tasks = []

        def factory(task: Task) -> _SucceedingWorker:
            seen_tasks.append(task)
            return _SucceedingWorker(task)

        run(q, RunBudget(max_tasks=5, max_failures=5),
            perform=make_worker_perform(factory, records),
            verify=make_worker_verify(records))

        self.assertEqual(len(seen_tasks), 1)
        self.assertEqual(seen_tasks[0].task_id, "T1")

    def test_t3_t4_successful_result_reaches_verification_and_completes(self):
        q = self._single_task_queue()
        records: dict = {}
        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=make_worker_perform(_SucceedingWorker, records),
            verify=make_worker_verify(records),
        )
        self.assertEqual(report.completed, ("T1",))
        self.assertEqual(q.get("T1").state, "DONE")
        self.assertIn("UPDATE_STATE", records["T1"].steps_completed)

    def test_t5_worker_exception_produces_explicit_non_success_state(self):
        q = self._single_task_queue()
        records: dict = {}
        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=make_worker_perform(_ExplodingWorker, records),
            verify=make_worker_verify(records),
        )
        self.assertEqual(report.completed, ())
        self.assertEqual(len(report.failed), 1)
        self.assertEqual(q.get("T1").state, "FAILED")
        self.assertIn("worker blew up", q.get("T1").failure_reason)
        # G4: an exception must never leave a CycleRecord behind claiming success.
        self.assertNotIn("T1", records)

    def test_t6_worker_verification_failure_does_not_produce_completion(self):
        q = self._single_task_queue()
        records: dict = {}
        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=make_worker_perform(_VerificationFailingWorker, records),
            verify=make_worker_verify(records),
        )
        self.assertEqual(report.completed, ())
        self.assertEqual(q.get("T1").state, "FAILED")
        self.assertNotIn("UPDATE_STATE", records["T1"].steps_completed)

    def test_permission_denied_never_reaches_update_state(self):
        q = self._single_task_queue()
        records: dict = {}
        run(q, RunBudget(max_tasks=5, max_failures=5),
            perform=make_worker_perform(_PermissionDeniedWorker, records),
            verify=make_worker_verify(records))
        self.assertEqual(q.get("T1").state, "FAILED")
        self.assertNotIn("UPDATE_STATE", records["T1"].steps_completed)

    def test_t7_arbitrary_callable_path_still_works_unchanged(self):
        # No worker, no adapter — the original perform/verify contract
        # from foundation/task_queue.py's own test suite, unmodified.
        q = self._single_task_queue()
        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=lambda t: "plain result", verify=lambda t, r: True,
        )
        self.assertEqual(report.completed, ("T1",))

    def test_t8_ineligible_task_never_reaches_worker_execution(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x", dependencies=("MISSING_DEP",)))
        records: dict = {}
        invoked = []

        def factory(task: Task) -> _SucceedingWorker:
            invoked.append(task.task_id)
            return _SucceedingWorker(task)

        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=make_worker_perform(factory, records),
            verify=make_worker_verify(records),
        )
        self.assertEqual(invoked, [])
        self.assertEqual(report.stopped_reason, "no eligible tasks remain")

    def test_t9_missing_record_never_silently_marked_complete(self):
        q = self._single_task_queue()
        # verify() invoked with no corresponding perform() having run —
        # simulates an ambiguous/interrupted state.
        records: dict = {}
        verify_fn = make_worker_verify(records)
        task = q.get("T1")
        self.assertFalse(verify_fn(task, "some result"))

    def test_t10_multiple_compatible_tasks_run_sequentially_with_per_task_verification(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x"))
        q.load(Task(task_id="B", description="x", dependencies=("A",)))
        q.load(Task(task_id="C", description="x"))
        records: dict = {}
        report = run(
            q, RunBudget(max_tasks=10, max_failures=5),
            perform=make_worker_perform(_SucceedingWorker, records),
            verify=make_worker_verify(records),
        )
        self.assertEqual(set(report.completed), {"A", "B", "C"})
        for task_id in ("A", "B", "C"):
            self.assertIn("UPDATE_STATE", records[task_id].steps_completed)
            self.assertEqual(q.get(task_id).state, "DONE")

    def test_mixed_success_and_failure_tasks_each_verified_independently(self):
        q = TaskQueue()
        q.load(Task(task_id="GOOD", description="x"))
        q.load(Task(task_id="BAD", description="x"))
        records: dict = {}

        def factory(task: Task):
            if task.task_id == "BAD":
                return _VerificationFailingWorker(task)
            return _SucceedingWorker(task)

        report = run(
            q, RunBudget(max_tasks=10, max_failures=5),
            perform=make_worker_perform(factory, records),
            verify=make_worker_verify(records),
        )
        self.assertEqual(report.completed, ("GOOD",))
        self.assertEqual(q.get("BAD").state, "FAILED")
        self.assertEqual(q.get("GOOD").state, "DONE")


if __name__ == "__main__":
    unittest.main()
