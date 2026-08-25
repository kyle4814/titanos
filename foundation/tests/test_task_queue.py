import unittest

from foundation.task_queue import (
    RunBudget, RunReport, Task, TaskQueue, can_transition, reconcile_in_progress, run,
)


class TestTaskConstruction(unittest.TestCase):
    def test_valid_task_constructs(self):
        t = Task(task_id="T1", description="do a thing")
        self.assertEqual(t.state, "PENDING")

    def test_empty_id_rejected(self):
        with self.assertRaises(ValueError):
            Task(task_id="", description="x")

    def test_bad_state_rejected(self):
        with self.assertRaises(ValueError):
            Task(task_id="T1", description="x", state="NOT_A_STATE")

    def test_transition_to_legal_state(self):
        t = Task(task_id="T1", description="x")
        t.transition_to("IN_PROGRESS")
        self.assertEqual(t.state, "IN_PROGRESS")

    def test_transition_to_illegal_state_rejected(self):
        t = Task(task_id="T1", description="x")
        with self.assertRaises(ValueError):
            t.transition_to("DONE")  # PENDING -> DONE is not a legal edge

    def test_terminal_states_have_no_outgoing_edges(self):
        self.assertFalse(can_transition("DONE", "PENDING"))
        self.assertFalse(can_transition("FAILED", "PENDING"))


class TestTaskQueue(unittest.TestCase):
    def test_load_and_get(self):
        q = TaskQueue()
        q.load(Task(task_id="T1", description="x"))
        self.assertEqual(q.get("T1").task_id, "T1")

    def test_duplicate_load_rejected(self):
        q = TaskQueue()
        q.load(Task(task_id="T1", description="x"))
        with self.assertRaises(ValueError):
            q.load(Task(task_id="T1", description="x"))

    def test_no_delete_surface(self):
        q = TaskQueue()
        for method in ("delete", "purge", "clear", "remove"):
            self.assertFalse(hasattr(q, method))

    def test_validate_detects_unknown_dependency(self):
        q = TaskQueue()
        q.load(Task(task_id="T1", description="x", dependencies=("GHOST",)))
        problems = q.validate()
        self.assertTrue(any("unknown task" in p for p in problems))

    def test_validate_detects_self_dependency(self):
        q = TaskQueue()
        q.load(Task(task_id="T1", description="x", dependencies=("T1",)))
        problems = q.validate()
        self.assertTrue(any("depends on itself" in p for p in problems))

    def test_validate_detects_cycle(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x", dependencies=("B",)))
        q.load(Task(task_id="B", description="x", dependencies=("A",)))
        problems = q.validate()
        self.assertTrue(any("cycle" in p for p in problems))

    def test_validate_clean_queue_has_no_problems(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x"))
        q.load(Task(task_id="B", description="x", dependencies=("A",)))
        self.assertEqual(q.validate(), [])

    def test_eligible_tasks_respects_dependencies(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x"))
        q.load(Task(task_id="B", description="x", dependencies=("A",)))
        eligible = [t.task_id for t in q.eligible_tasks()]
        self.assertEqual(eligible, ["A"])

    def test_eligible_tasks_unblocks_after_dependency_done(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x"))
        q.load(Task(task_id="B", description="x", dependencies=("A",)))
        q.get("A").transition_to("IN_PROGRESS")
        q.get("A").transition_to("DONE")
        eligible = [t.task_id for t in q.eligible_tasks()]
        self.assertEqual(eligible, ["B"])

    def test_unknown_dependency_never_vacuously_eligible(self):
        # Fail-closed regression: a task depending on a task_id that
        # does not exist must never be treated as eligible just because
        # there's nothing to check it against. Found via
        # test_queue_worker_adapter.py's T8 seam case.
        q = TaskQueue()
        q.load(Task(task_id="A", description="x", dependencies=("GHOST",)))
        self.assertEqual(q.eligible_tasks(), ())

    def test_non_pending_tasks_never_eligible(self):
        q = TaskQueue()
        t = Task(task_id="A", description="x")
        t.transition_to("IN_PROGRESS")
        q.load(t)
        self.assertEqual(q.eligible_tasks(), ())


class TestReconcileInProgress(unittest.TestCase):
    def test_non_in_progress_task_untouched(self):
        t = Task(task_id="A", description="x")  # PENDING
        reconcile_in_progress(t, evidence_of_completion=lambda task: True)
        self.assertEqual(t.state, "PENDING")

    def test_in_progress_with_evidence_becomes_done(self):
        t = Task(task_id="A", description="x")
        t.transition_to("IN_PROGRESS")
        reconcile_in_progress(t, evidence_of_completion=lambda task: True)
        self.assertEqual(t.state, "DONE")

    def test_in_progress_without_evidence_becomes_failed_never_done(self):
        t = Task(task_id="A", description="x")
        t.transition_to("IN_PROGRESS")
        reconcile_in_progress(t, evidence_of_completion=lambda task: False)
        self.assertEqual(t.state, "FAILED")
        self.assertIn("never assumed complete", t.failure_reason)


class TestRunBudget(unittest.TestCase):
    def test_valid_budget_constructs(self):
        b = RunBudget(max_tasks=5, max_failures=2)
        self.assertEqual(b.max_tasks, 5)

    def test_max_tasks_must_be_positive(self):
        with self.assertRaises(ValueError):
            RunBudget(max_tasks=0, max_failures=1)

    def test_negative_max_failures_rejected(self):
        with self.assertRaises(ValueError):
            RunBudget(max_tasks=1, max_failures=-1)

    def test_verification_reserve_ge_max_tasks_rejected(self):
        with self.assertRaises(ValueError):
            RunBudget(max_tasks=3, max_failures=1, verification_reserve=3)


class TestRun(unittest.TestCase):
    def _queue_of(self, n):
        q = TaskQueue()
        for i in range(n):
            q.load(Task(task_id=f"T{i}", description="x"))
        return q

    def test_all_tasks_completed_when_perform_and_verify_succeed(self):
        q = self._queue_of(3)
        report = run(
            q, RunBudget(max_tasks=10, max_failures=5),
            perform=lambda t: "ok", verify=lambda t, r: True,
        )
        self.assertEqual(set(report.completed), {"T0", "T1", "T2"})
        self.assertEqual(report.failed, ())
        self.assertEqual(report.stopped_reason, "no eligible tasks remain")

    def test_max_tasks_limit_stops_run(self):
        q = self._queue_of(5)
        report = run(
            q, RunBudget(max_tasks=2, max_failures=5),
            perform=lambda t: "ok", verify=lambda t, r: True,
        )
        self.assertEqual(len(report.completed), 2)
        self.assertIn("max_tasks reached", report.stopped_reason)

    def test_max_failures_limit_stops_run(self):
        q = self._queue_of(5)
        report = run(
            q, RunBudget(max_tasks=10, max_failures=1),
            perform=lambda t: "ok", verify=lambda t, r: False,
        )
        self.assertEqual(report.stopped_reason, "max_failures reached")
        self.assertGreaterEqual(len(report.failed), 1)

    def test_perform_exception_recorded_as_failure_not_raised(self):
        q = self._queue_of(1)

        def boom(t):
            raise RuntimeError("simulated failure")

        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=boom, verify=lambda t, r: True,
        )
        self.assertEqual(report.completed, ())
        self.assertEqual(len(report.failed), 1)
        self.assertIn("simulated failure", report.failed[0][1])
        self.assertEqual(q.get("T0").state, "FAILED")

    def test_failed_task_never_marked_done(self):
        q = self._queue_of(1)
        run(q, RunBudget(max_tasks=5, max_failures=5),
            perform=lambda t: "bad", verify=lambda t, r: False)
        self.assertEqual(q.get("T0").state, "FAILED")

    def test_task_at_max_attempts_not_retried(self):
        q = TaskQueue()
        t = Task(task_id="T0", description="x", max_attempts=1, attempts=1)
        q.load(t)
        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=lambda task: (_ for _ in ()).throw(AssertionError("perform must not run")),
            verify=lambda task, r: True,
        )
        self.assertEqual(t.state, "FAILED")
        self.assertIn("not retried", t.failure_reason)
        self.assertEqual(len(report.failed), 1)

    def test_effective_budget_respects_verification_reserve(self):
        q = self._queue_of(5)
        report = run(
            q, RunBudget(max_tasks=3, max_failures=5, verification_reserve=1),
            perform=lambda t: "ok", verify=lambda t, r: True,
        )
        self.assertEqual(len(report.completed), 2)  # 3 - 1 reserve

    def test_dependent_task_runs_after_its_dependency(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x"))
        q.load(Task(task_id="B", description="x", dependencies=("A",)))
        order: list[str] = []
        report = run(
            q, RunBudget(max_tasks=10, max_failures=5),
            perform=lambda t: order.append(t.task_id) or "ok",
            verify=lambda t, r: True,
        )
        self.assertEqual(order, ["A", "B"])
        self.assertEqual(set(report.completed), {"A", "B"})

    def test_empty_queue_stops_immediately(self):
        q = TaskQueue()
        report = run(
            q, RunBudget(max_tasks=5, max_failures=5),
            perform=lambda t: "ok", verify=lambda t, r: True,
        )
        self.assertEqual(report, RunReport((), (), "no eligible tasks remain"))


if __name__ == "__main__":
    unittest.main()
