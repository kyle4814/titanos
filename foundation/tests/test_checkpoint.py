"""A checkpoint that lies about its own content, or that vanishes on a
crash mid-write, is worse than no checkpoint at all: it lets a resuming
run act on a state that never actually held. Every test here tries to
make that happen.
"""

import json
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from foundation.checkpoint import (
    CHECKPOINT_ABSENT,
    CHECKPOINT_INTACT,
    CHECKPOINT_TAMPERED,
    Checkpoint,
    CheckpointIntegrityError,
    CheckpointStore,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _cp(**kw):
    base = dict(task_id="T-1", phase="BUILD", repo_revision="abc123",
                config_digest="cfg-1", receipt_head="RCPT-1",
                next_action="run tests", payload={"attempt": 1})
    base.update(kw)
    return Checkpoint(**base)


class TestCheckpointIdentity(unittest.TestCase):
    def test_checkpoint_id_is_content_derived_and_stable(self):
        a = _cp(created_at="2026-01-01T00:00:00+00:00")
        b = _cp(created_at="2026-01-01T00:00:00+00:00")
        self.assertEqual(a.checkpoint_id, b.checkpoint_id)
        self.assertEqual(a.content_hash, b.content_hash)

    def test_different_content_gives_different_id(self):
        a = _cp(created_at="2026-01-01T00:00:00+00:00")
        b = _cp(created_at="2026-01-01T00:00:00+00:00", phase="RECOVER")
        self.assertNotEqual(a.checkpoint_id, b.checkpoint_id)

    def test_task_id_required(self):
        with self.assertRaises(CheckpointIntegrityError):
            _cp(task_id="")

    def test_phase_required(self):
        with self.assertRaises(CheckpointIntegrityError):
            _cp(phase="  ")


class TestInMemoryStoreIsolation(unittest.TestCase):
    def test_path_none_writes_nothing_to_disk_anywhere(self):
        before = set(REPO_ROOT.rglob("*"))
        store = CheckpointStore(path=None)
        for i in range(5):
            store.save(_cp(task_id="T-mem", payload={"i": i}))
        after = set(REPO_ROOT.rglob("*"))
        self.assertEqual(before, after,
                         "in-memory store must never touch the filesystem")

    def test_in_memory_resume_still_works(self):
        store = CheckpointStore(path=None)
        store.save(_cp(task_id="T-mem", phase="A"))
        cp2 = store.save(_cp(task_id="T-mem", phase="B"))
        self.assertEqual(store.resume("T-mem").checkpoint_id, cp2.checkpoint_id)


class TestDurableSaveAndResume(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.path = Path(self._tmpdir) / "checkpoints.jsonl"

    def test_save_then_new_store_resumes_intact(self):
        store = CheckpointStore(path=self.path)
        saved = store.save(_cp(task_id="T-durable", phase="BUILD"))
        del store

        reloaded = CheckpointStore(path=self.path)
        resumed = reloaded.resume("T-durable")
        self.assertIsNotNone(resumed)
        self.assertEqual(resumed.checkpoint_id, saved.checkpoint_id)
        self.assertEqual(resumed.next_action, saved.next_action)
        self.assertEqual(reloaded.verify(resumed), CHECKPOINT_INTACT)

    def test_crash_mid_write_leaves_previous_checkpoint_readable(self):
        store = CheckpointStore(path=self.path)
        good = store.save(_cp(task_id="T-crash", phase="BUILD"))

        # Simulate a crash BETWEEN writing the temp file and the
        # os.replace() that would publish it: leave a stray, possibly
        # garbage, temp file in the same directory without ever
        # replacing the real path.
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.path.parent), prefix=".tmp-checkpoint-")
        with os.fdopen(fd, "w") as tmp:
            tmp.write('{"task_id": "T-crash", "phase": "RECOVER truncat')
        # Deliberately do NOT os.replace(tmp_name, self.path).

        reloaded = CheckpointStore(path=self.path)
        resumed = reloaded.resume("T-crash")
        self.assertIsNotNone(resumed)
        self.assertEqual(resumed.checkpoint_id, good.checkpoint_id)
        self.assertEqual(resumed.phase, "BUILD")
        os.remove(tmp_name)

    def test_truncated_trailing_line_does_not_prevent_construction(self):
        store = CheckpointStore(path=self.path)
        good = store.save(_cp(task_id="T-trunc", phase="BUILD"))

        # Directly corrupt the file the way a killed process would:
        # append a half-written trailing line.
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write('{"task_id": "T-trunc", "phase": "unterminat')

        reloaded = CheckpointStore(path=self.path)  # must not raise
        resumed = reloaded.resume("T-trunc")
        self.assertEqual(resumed.checkpoint_id, good.checkpoint_id)

    def test_resume_on_unknown_task_id_returns_none(self):
        store = CheckpointStore(path=self.path)
        store.save(_cp(task_id="T-known"))
        self.assertIsNone(store.resume("T-does-not-exist"))
        self.assertIsNone(store.latest("T-does-not-exist"))

    def test_resume_on_fresh_store_with_no_file_returns_none(self):
        fresh_path = Path(self._tmpdir) / "never-written.jsonl"
        store = CheckpointStore(path=fresh_path)
        self.assertIsNone(store.resume("anything"))
        self.assertFalse(fresh_path.exists())


class TestSupersedeNeverMutate(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.path = Path(self._tmpdir) / "checkpoints.jsonl"

    def test_superseding_preserves_full_history(self):
        store = CheckpointStore(path=self.path)
        first = store.save(_cp(task_id="T-hist", phase="A", payload={"n": 1}))
        second = store.save(_cp(task_id="T-hist", phase="B", payload={"n": 2}))
        third = store.save(_cp(task_id="T-hist", phase="C", payload={"n": 3}))

        self.assertEqual(store.resume("T-hist").checkpoint_id, third.checkpoint_id)

        history = store.history("T-hist")
        self.assertEqual(len(history), 3)
        self.assertEqual([c.checkpoint_id for c in history],
                         [first.checkpoint_id, second.checkpoint_id,
                          third.checkpoint_id])

        # And it survives a reload from disk too -- history is not just
        # an in-memory convenience.
        reloaded = CheckpointStore(path=self.path)
        self.assertEqual(len(reloaded.history("T-hist")), 3)
        self.assertEqual(reloaded.resume("T-hist").checkpoint_id,
                         third.checkpoint_id)

    def test_no_delete_surface_on_the_public_api(self):
        public_names = {name for name in dir(CheckpointStore)
                        if not name.startswith("_")}
        forbidden = {"delete", "remove", "purge", "clear", "erase",
                    "drop", "truncate"}
        self.assertFalse(public_names & forbidden,
                         f"CheckpointStore exposes a delete-shaped method: "
                         f"{public_names & forbidden}")


class TestTamperDetection(unittest.TestCase):
    def test_verify_intact_checkpoint(self):
        store = CheckpointStore(path=None)
        cp = store.save(_cp(task_id="T-verify"))
        self.assertEqual(store.verify(cp), CHECKPOINT_INTACT)

    def test_verify_absent_on_none(self):
        store = CheckpointStore(path=None)
        self.assertIsNone(store.resume("nothing-here"))
        self.assertEqual(store.verify(store.resume("nothing-here")),
                         CHECKPOINT_ABSENT)

    def test_verify_detects_in_memory_tampering(self):
        cp = _cp(task_id="T-tamper")
        # Mutate a field on the frozen dataclass without touching the
        # hash it was sealed with -- exactly what an in-place edit of a
        # stored record would produce.
        tampered = replace(cp, next_action="do something else entirely")
        object.__setattr__(tampered, "content_hash", cp.content_hash)
        object.__setattr__(tampered, "checkpoint_id", cp.checkpoint_id)

        store = CheckpointStore(path=None)
        self.assertEqual(store.verify(tampered), CHECKPOINT_TAMPERED)

    def test_verify_detects_on_disk_tampering(self):
        tmpdir = tempfile.mkdtemp()
        path = Path(tmpdir) / "checkpoints.jsonl"
        store = CheckpointStore(path=path)
        store.save(_cp(task_id="T-disk-tamper", next_action="original"))

        # Edit the file directly, as an external actor would, without
        # updating content_hash to match.
        with open(path, "r", encoding="utf-8") as fh:
            lines = [json.loads(l) for l in fh if l.strip()]
        lines[-1]["next_action"] = "attacker-supplied action"
        with open(path, "w", encoding="utf-8") as fh:
            for obj in lines:
                fh.write(json.dumps(obj, sort_keys=True) + "\n")

        reloaded = CheckpointStore(path=path)
        resumed = reloaded.resume("T-disk-tamper")
        self.assertEqual(resumed.next_action, "attacker-supplied action")
        self.assertEqual(reloaded.verify(resumed), CHECKPOINT_TAMPERED)


if __name__ == "__main__":
    unittest.main()
