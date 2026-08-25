"""
Closed-loop reality proof: TASK -> QUEUE -> ELIGIBILITY -> CANONICAL
WORKER -> RESULT -> VERIFICATION -> STATE -> EVIDENCE -> BOUNDED STOP.

Unlike foundation/tests/test_queue_worker_adapter.py (which proves the
seam's *wiring* with synthetic test-double workers), every test in this
file drives the loop through `SentinelSweepWorker` — a real worker whose
unit of work is the real, already-existing `foundation.sentinel.
pulse_sweep()` running against the real repository, and whose state
update writes a real `foundation.crystal.Crystal` into a real
`CrystalStore`. No mocked success is presented as genuine end-to-end
execution (G1).
"""

import unittest
from pathlib import Path

from foundation.crystal import CrystalStore
from foundation.queue_worker_adapter import make_worker_perform, make_worker_verify
from foundation.sentinel_worker import SentinelSweepWorker
from foundation.task_queue import RunBudget, Task, TaskQueue, run

REPO_ROOT = Path(__file__).resolve().parents[2]


def _worker_factory(crystal_store: CrystalStore):
    def factory(task: Task) -> SentinelSweepWorker:
        return SentinelSweepWorker(
            repo_root=REPO_ROOT,
            crystal_store=crystal_store,
            recorded_by="closed-loop-reality-test",
            crystal_id=f"sentinel-sweep-{task.task_id}",
        )
    return factory


class TestClosedLoopRealityPass(unittest.TestCase):
    def test_single_real_task_traverses_full_loop_and_produces_real_evidence(self):
        # TASK -> QUEUE
        q = TaskQueue()
        q.load(Task(task_id="SWEEP-1", description="run a real sentinel pulse sweep"))
        crystal_store = CrystalStore()
        records: dict = {}

        # QUEUE -> ELIGIBILITY -> WORKER -> RESULT -> VERIFY -> STATE
        report = run(
            q, RunBudget(max_tasks=5, max_failures=1),
            perform=make_worker_perform(_worker_factory(crystal_store), records),
            verify=make_worker_verify(records),
        )

        # RESULT/VERIFY/STATE: task completed for real, not simulated.
        self.assertEqual(report.completed, ("SWEEP-1",))
        self.assertEqual(q.get("SWEEP-1").state, "DONE")

        # EVIDENCE: a real Crystal was written, derived from a real sweep.
        crystal = crystal_store.get("sentinel-sweep-SWEEP-1")
        self.assertIsNotNone(crystal)
        self.assertEqual(crystal.epistemic_status, "VERIFIED_FACT")
        self.assertIn("finding", crystal.evidence)
        # The crystal's evidence must match what a fresh, independent
        # pulse_sweep() call finds right now — proof this is real
        # output, not a canned string.
        from foundation.sentinel import pulse_sweep
        independent_check = pulse_sweep(REPO_ROOT)
        self.assertIn(str(independent_check.raw_finding_count), crystal.evidence)

        # STOP: bounded run ends cleanly with an explicit reason.
        self.assertEqual(report.stopped_reason, "no eligible tasks remain")

    def test_g3_ineligible_dependent_task_never_reaches_the_real_worker(self):
        q = TaskQueue()
        q.load(Task(task_id="SWEEP-1", description="first"))
        q.load(Task(task_id="SWEEP-2", description="second", dependencies=("SWEEP-1",)))
        crystal_store = CrystalStore()
        records: dict = {}

        report = run(
            q, RunBudget(max_tasks=1, max_failures=1),  # budget for exactly one task
            perform=make_worker_perform(_worker_factory(crystal_store), records),
            verify=make_worker_verify(records),
        )

        # G3/T2/T8: only the independent task ran; the dependent one is
        # untouched — no worker was ever constructed for it, no Crystal
        # was written for it.
        self.assertEqual(report.completed, ("SWEEP-1",))
        self.assertEqual(q.get("SWEEP-2").state, "PENDING")
        self.assertIsNone(crystal_store.get("sentinel-sweep-SWEEP-2"))

    def test_t11_two_independent_tasks_each_independently_verified(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="independent sweep A"))
        q.load(Task(task_id="B", description="independent sweep B"))
        crystal_store = CrystalStore()
        records: dict = {}

        report = run(
            q, RunBudget(max_tasks=5, max_failures=1),
            perform=make_worker_perform(_worker_factory(crystal_store), records),
            verify=make_worker_verify(records),
        )

        self.assertEqual(set(report.completed), {"A", "B"})
        for task_id in ("A", "B"):
            self.assertEqual(q.get(task_id).state, "DONE")
            self.assertIsNotNone(crystal_store.get(f"sentinel-sweep-{task_id}"))
            self.assertIn("UPDATE_STATE", records[task_id].steps_completed)

    def test_t12_bounded_stop_leaves_unstarted_task_untouched(self):
        q = TaskQueue()
        q.load(Task(task_id="A", description="x"))
        q.load(Task(task_id="B", description="x"))
        q.load(Task(task_id="C", description="x"))
        crystal_store = CrystalStore()
        records: dict = {}

        report = run(
            q, RunBudget(max_tasks=2, max_failures=1),  # deliberately less than 3
            perform=make_worker_perform(_worker_factory(crystal_store), records),
            verify=make_worker_verify(records),
        )

        self.assertEqual(len(report.completed), 2)
        self.assertIn("max_tasks reached", report.stopped_reason)
        # The task never reached is genuinely untouched: still PENDING,
        # no worker constructed, no Crystal recorded for it.
        remaining = [t for t in q.all_tasks() if t.state == "PENDING"]
        self.assertEqual(len(remaining), 1)
        self.assertIsNone(crystal_store.get(f"sentinel-sweep-{remaining[0].task_id}"))

    def test_g9_no_duplicate_orchestration_loop_two_runs_are_independent(self):
        # Calling run() twice must not silently continue a hidden shared
        # loop state — each call is bounded and independent.
        q = TaskQueue()
        q.load(Task(task_id="A", description="x"))
        crystal_store = CrystalStore()
        records: dict = {}
        budget = RunBudget(max_tasks=5, max_failures=1)

        first = run(q, budget, perform=make_worker_perform(_worker_factory(crystal_store), records),
                    verify=make_worker_verify(records))
        second = run(q, budget, perform=make_worker_perform(_worker_factory(crystal_store), records),
                     verify=make_worker_verify(records))

        self.assertEqual(first.completed, ("A",))
        # Second run finds nothing eligible — A is already DONE, not
        # re-executed, no second Crystal written under a fresh id clash.
        self.assertEqual(second.completed, ())
        self.assertEqual(second.stopped_reason, "no eligible tasks remain")


if __name__ == "__main__":
    unittest.main()
