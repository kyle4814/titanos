"""Minimal durable offline-first TitanOS kernel."""
from __future__ import annotations
import hashlib, json, os, time, uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "runtime"
STATE.mkdir(exist_ok=True)
QUEUE = STATE / "queue.jsonl"
RECEIPTS = STATE / "receipts.jsonl"
CHECKPOINTS = STATE / "checkpoints"
CHECKPOINTS.mkdir(exist_ok=True)

def _json(x: Any) -> str:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_text(x: str) -> str:
    return hashlib.sha256(x.encode("utf-8")).hexdigest()

def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(_json(obj) + "\n")
        f.flush()
        os.fsync(f.fileno())

def receipt(action: str, task_id: str, actor: str, **payload) -> dict:
    previous = ""
    if RECEIPTS.exists():
        lines = RECEIPTS.read_text(encoding="utf-8").splitlines()
        if lines:
            previous = json.loads(lines[-1]).get("receipt_hash", "")
    body = {
        "receipt_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "task_id": task_id,
        "run_id": os.environ.get("TITANOS_RUN_ID", "local"),
        "actor": actor,
        "action": action,
        "inputs": payload.get("inputs", {}),
        "outputs": payload.get("outputs", {}),
        "evidence": payload.get("evidence", []),
        "files_changed": payload.get("files_changed", []),
        "tests": payload.get("tests", []),
        "provenance": payload.get("provenance", []),
        "value_class": payload.get("value_class", "MODELLED"),
        "outcome": payload.get("outcome", "RECORDED"),
        "config_hash": payload.get("config_hash", ""),
        "code_revision": payload.get("code_revision", ""),
        "previous_receipt_hash": previous,
    }
    body["receipt_hash"] = sha256_text(_json(body))
    append_jsonl(RECEIPTS, body)
    return body

@dataclass
class Task:
    task_id: str
    mission: str
    priority: float = 0.0
    scope: list[str] | None = None
    status: str = "QUEUED"

def enqueue(mission: str, priority: float = 0.0, scope=None) -> Task:
    task = Task(str(uuid.uuid4()), mission, priority, scope or [])
    append_jsonl(QUEUE, asdict(task))
    receipt("TASK_CREATED", task.task_id, "kernel",
            outputs={"mission": mission, "priority": priority})
    return task

def load_queue() -> list[dict]:
    if not QUEUE.exists():
        return []
    return [json.loads(x) for x in QUEUE.read_text(encoding="utf-8").splitlines() if x.strip()]

def pareto(tasks: list[dict]) -> list[dict]:
    return sorted(tasks, key=lambda t: (-float(t.get("priority", 0)), t["task_id"]))

def checkpoint(task: dict, next_action: str) -> None:
    p = CHECKPOINTS / f"{task['task_id']}.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(_json({"task": task, "next_action": next_action}), encoding="utf-8")
    os.replace(tmp, p)

def execute_local(task: dict) -> dict:
    """Execute only the built-in safe local mission types."""
    mission = task["mission"]
    checkpoint(task, "EXECUTE")
    if mission == "health":
        result = {"status": "ok", "mode": "offline"}
    elif mission == "receipt_integrity":
        result = {"status": "ok", "receipts": str(RECEIPTS)}
    else:
        result = {"status": "accepted_for_worker", "mission": mission}
    receipt("TASK_EXECUTED", task["task_id"], "kernel",
            outputs=result, outcome=result["status"])
    checkpoint(task, "COMPLETE")
    return result

def boot() -> dict:
    STATE.mkdir(exist_ok=True)
    receipt("SYSTEM_BOOT", "SYSTEM", "kernel",
            outputs={"state": str(STATE), "offline": True})
    return {"status": "BOOTED", "state": str(STATE)}
