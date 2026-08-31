"""Where a run stood, sealed durably enough to resume it after a crash.

WHY THIS EXISTS, AFTER GREPPING FOR IT AND FINDING NOTHING

Multiple governing documents in this repository assume a run can be
interrupted and picked back up: restart, recover, multi-cycle. None of
that is possible without something that answers "what was the last known
good state of task X, and can I trust it?" A grep for checkpoint/resume
machinery across the repo turned up nothing -- receipts, ledgers and
manifests all record what already happened, but nothing records where a
run WAS, in a form a later process can load and continue from. Phases
4-6 of the autonomy ramp (restart, recover, multi-cycle) are blocked on
exactly this gap.

WHAT THIS REUSES RATHER THAN INVENTING

- The atomic-write discipline of `kpm/source-vault/registry.py
  ::_ensure_archived`: write to a temp file in the SAME directory,
  fsync, then `os.replace`. `os.replace` is a single filesystem
  rename -- a crash at any point before it completes leaves the
  original file untouched; a crash after it completes leaves the new
  file complete. There is no window in which a reader can observe a
  half-written checkpoint file, because the path readers open never
  points at the temp file.
- The durable-JSONL-with-replay shape of `foundation/outcome_ledger.py`:
  history lives as one record per line, a truncated trailing line from a
  killed process is skipped rather than fatal, and content is
  content-addressed so tampering is a distinct, detectable fact rather
  than a silent load.
- The computed-not-stored posture of `foundation/system_manifest.py`:
  `latest()`/`resume()` are derived from the loaded history on every
  call, never cached state that could go stale.

WHAT IS DELIBERATELY DIFFERENT FROM OUTCOME_LEDGER

`OutcomeLedger` appends one line per record and never rewrites earlier
bytes -- that is safe there because each line only needs to be
individually well-formed. A checkpoint file has a stronger requirement:
the REQUIREMENT here (see task) is that `save()` itself be atomic, i.e.
a crash mid-save must never leave a half-written checkpoint that a later
read accepts. Pure O_APPEND cannot promise that on all filesystems (a
partial write can still land, and a concurrent reader has no signal that
the line is incomplete beyond "does it parse"). So `save()` here writes
the FULL history (all prior checkpoints plus the new one) to a fresh
temp file and swaps it in with `os.replace`. This costs O(history size)
per save, which is the right trade for a mechanism whose whole job is
"never hand back a corrupt or partial state" over one whose job is raw
append throughput. History is still append-only in effect -- every prior
record that was successfully saved is still in the file after the next
save -- there is just no separate append fast path to reason about.

SUPERSEDE, NEVER MUTATE

A new checkpoint for a `task_id` does not replace or edit the previous
one on disk. It is simply a later record with the same `task_id`;
`latest()`/`resume()` return the last one written. Every earlier
checkpoint for that task is still in the file and still loadable by
anyone who wants the history, not just the tip. There is no delete
method and no update method -- correcting a checkpoint means writing a
new one, exactly like `OutcomeLedger` and `CrystalStore` correct by
superseding.

WHAT VERIFY() CAN AND CANNOT TELL YOU

`verify()` recomputes a checkpoint's content hash from its own fields
and compares it to the hash stored on the object. That proves (or
disproves) internal self-consistency -- it is the same class of check as
`PreActionContext.is_intact()` in outcome_ledger.py. It CANNOT prove a
checkpoint file was not truncated, reordered, or had a middle line
deleted; outcome_ledger's hash-chain solves that different problem for a
different reason (an append-only audit trail where line order is
itself evidence). A checkpoint's job is narrower -- "give me the last
trustworthy state for this task" -- so `save()`'s atomicity (never
publish a half state) plus `verify()`'s self-consistency check (never
silently accept an edited one) is the complete answer this module needs.
Extending it with a hash chain would be solving a problem this module
does not have.

WHAT THIS CANNOT DO

It cannot tell you whether `next_action` is still the RIGHT next action
by the time you resume -- the world may have moved on since the
checkpoint was written. It only tells you, honestly, what the run
believed at the moment it saved. It also cannot recover a checkpoint
that was never saved: if a process crashes between deciding to
checkpoint and calling `save()`, there is nothing here to reconstruct
that decision from. And in-memory mode (`path=None`) cannot survive a
process exit at all -- that is not a bug, it is what "in-memory" means;
callers that need cross-process resume must pass a path.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

__all__ = [
    "CheckpointIntegrityError",
    "Checkpoint",
    "CheckpointStore",
    "CHECKPOINT_INTACT",
    "CHECKPOINT_TAMPERED",
    "CHECKPOINT_ABSENT",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CheckpointIntegrityError(ValueError):
    """A checkpoint claimed an identity its own content does not support."""


# verify() outcomes. Three genuinely different facts -- a missing
# checkpoint, an unaltered one, and one whose content no longer matches
# its own hash -- collapsed to one signal ("truthy"/"falsy") would let a
# caller mistake "nothing to resume from" for "resume, but distrust it".
CHECKPOINT_INTACT = "INTACT"
CHECKPOINT_TAMPERED = "TAMPERED"
CHECKPOINT_ABSENT = "ABSENT"


def _content_hash(task_id: str, phase: str, repo_revision: str,
                   config_digest: str, receipt_head: str, next_action: str,
                   payload: Mapping[str, Any], created_at: str) -> str:
    import hashlib
    blob = json.dumps({
        "task_id": task_id, "phase": phase, "repo_revision": repo_revision,
        "config_digest": config_digest, "receipt_head": receipt_head,
        "next_action": next_action, "payload": dict(payload),
        "created_at": created_at,
    }, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Checkpoint:
    """One saved statement of "here is where task_id stood".

    `checkpoint_id` and `content_hash` are content-derived: leave them as
    the default empty string and the constructor computes and fills them
    in from every other field, INCLUDING `created_at`. That means two
    checkpoints with identical fields written at different instants get
    different ids -- correct, because the timestamp is genuinely part of
    what was saved, not incidental metadata. It also means the id is
    reproducible: given the same field values (timestamp included), the
    same id is recomputed every time, which is what makes `verify()`
    meaningful -- it recomputes the hash and compares, rather than
    trusting whatever id happens to be attached.

    Loading a checkpoint back off disk passes `checkpoint_id` and
    `content_hash` through EXPLICITLY (whatever bytes were actually on
    disk), which skips recomputation. That is deliberate: it is the only
    way a tampered on-disk record can be loaded as an object whose stored
    hash no longer matches its own content, so `verify()` has something
    to catch.
    """

    task_id: str
    phase: str
    repo_revision: str = ""
    config_digest: str = ""
    receipt_head: str = ""
    next_action: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    checkpoint_id: str = ""
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not str(self.task_id).strip():
            raise CheckpointIntegrityError(
                "a checkpoint must name the task it belongs to; an "
                "unattached checkpoint cannot be resumed by anything")
        if not str(self.phase).strip():
            raise CheckpointIntegrityError(
                "a checkpoint must name the phase it was saved in; "
                "resuming needs to know not just IF but WHERE")
        object.__setattr__(self, "payload", dict(self.payload))
        if not self.checkpoint_id or not self.content_hash:
            h = self._recompute_hash()
            object.__setattr__(self, "content_hash", h)
            object.__setattr__(self, "checkpoint_id", f"CKPT-{h[:16]}")

    def _recompute_hash(self) -> str:
        return _content_hash(
            self.task_id, self.phase, self.repo_revision,
            self.config_digest, self.receipt_head, self.next_action,
            self.payload, self.created_at)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "phase": self.phase,
            "repo_revision": self.repo_revision,
            "config_digest": self.config_digest,
            "receipt_head": self.receipt_head,
            "next_action": self.next_action,
            "payload": dict(self.payload),
            "created_at": self.created_at,
            "checkpoint_id": self.checkpoint_id,
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, obj: Mapping[str, Any]) -> "Checkpoint":
        """Reconstruct exactly what was on disk, hash and id included --
        never recomputed here. A tampered record must come back AS the
        tampered record, so `verify()` is the thing that notices, not
        this loader silently repairing it on the way in."""
        return cls(
            task_id=obj["task_id"], phase=obj["phase"],
            repo_revision=obj.get("repo_revision", ""),
            config_digest=obj.get("config_digest", ""),
            receipt_head=obj.get("receipt_head", ""),
            next_action=obj.get("next_action", ""),
            payload=obj.get("payload", {}),
            created_at=obj.get("created_at", ""),
            checkpoint_id=obj.get("checkpoint_id", ""),
            content_hash=obj.get("content_hash", ""))


class CheckpointStore:
    """Holds every checkpoint ever saved, in the order it was saved.

    `path=None` (the default) means in-memory only: nothing is ever
    written to disk, which is what test isolation needs -- this repo has
    previously been bitten by test pollution writing into shared repo
    paths, so in-memory mode is not an afterthought, it is the safe
    default a caller gets without asking for anything.

    A `path` means every `save()` durably rewrites the WHOLE history
    (see module docstring for why this, not append-only, is what makes
    `save()` atomic) to that file via temp-file + fsync + `os.replace`.
    On construction, an existing file at `path` is replayed: each line is
    one JSON checkpoint record; a line that fails to parse is skipped,
    which is what a truncated trailing write from a killed process looks
    like, and is not treated as fatal.
    """

    def __init__(self, path: "str | Path | None" = None) -> None:
        self._path = Path(path) if path else None
        self._checkpoints: list[Checkpoint] = []
        if self._path and self._path.exists():
            self._replay()

    # -- durability --------------------------------------------------
    def _replay(self) -> None:
        with open(self._path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    # A truncated trailing line from a killed process.
                    # Not fatal -- a crash can only ever cost the last
                    # unflushed rewrite, never force manual recovery of
                    # everything written before it.
                    continue
                try:
                    self._checkpoints.append(Checkpoint.from_dict(obj))
                except (KeyError, CheckpointIntegrityError):
                    continue

    def save(self, cp: Checkpoint) -> Checkpoint:
        """Append `cp` to history and, if a path is configured, durably
        publish the whole history atomically.

        Never mutates or removes an earlier record -- this only ever
        grows the in-memory list and, on disk, rewrites the FULL set of
        prior records plus this one. A crash between opening the temp
        file and the `os.replace` call leaves the previously-published
        file exactly as it was: the temp file is either absent, partial,
        or complete-but-never-renamed, and none of those states is ever
        the path a reader opens.
        """
        self._checkpoints.append(cp)
        if self._path is None:
            return cp
        self._path.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(
            json.dumps(c.to_dict(), sort_keys=True, default=str) + "\n"
            for c in self._checkpoints)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=".tmp-checkpoint-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                tmp.write(content)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_name, self._path)
        except Exception:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
            raise
        return cp

    # -- reads --------------------------------------------------------
    def history(self, task_id: str) -> tuple[Checkpoint, ...]:
        """Every checkpoint ever saved for `task_id`, oldest first. The
        supersede-not-mutate guarantee made visible: nothing here is ever
        pruned by a later save."""
        return tuple(c for c in self._checkpoints if c.task_id == task_id)

    def latest(self, task_id: str) -> Optional[Checkpoint]:
        """The most recently saved checkpoint for `task_id`, or None.

        None is a normal, expected answer -- a task's first run has no
        checkpoint yet, and that is not an error condition.
        """
        matches = self.history(task_id)
        return matches[-1] if matches else None

    def resume(self, task_id: str) -> Optional[Checkpoint]:
        """Alias for `latest()` under the name a resuming caller reaches
        for. Kept as a distinct method (not just documentation) because
        "give me the checkpoint to resume from" is the actual call site
        this module exists to serve."""
        return self.latest(task_id)

    def verify(self, cp: Optional[Checkpoint]) -> str:
        """CHECKPOINT_ABSENT if `cp` is None (e.g. the result of a
        `resume()` that found nothing -- not an error, just nothing to
        verify). Otherwise recomputes the content hash from `cp`'s own
        fields and compares it to `cp.content_hash`: CHECKPOINT_INTACT on
        a match, CHECKPOINT_TAMPERED on a mismatch. Never collapses these
        three into a single true/false -- a caller deciding whether to
        trust a resume point needs to tell "nothing here" from "this was
        edited" from "this is exactly what was saved".
        """
        if cp is None:
            return CHECKPOINT_ABSENT
        recomputed = cp._recompute_hash()
        return CHECKPOINT_INTACT if recomputed == cp.content_hash else CHECKPOINT_TAMPERED
