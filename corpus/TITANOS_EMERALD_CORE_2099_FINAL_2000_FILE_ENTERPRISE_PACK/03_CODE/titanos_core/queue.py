import json, time, uuid
from .state import ROOT, write_receipt

QUEUE = ROOT / "runtime" / "queue.jsonl"

def enqueue(mission, priority=0):
    item = {
        "task_id": str(uuid.uuid4()),
        "mission": mission,
        "priority": float(priority),
        "status": "QUEUED",
        "created_at": time.time(),
    }
    with QUEUE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, sort_keys=True) + "\n")
    write_receipt(item["task_id"], "TASK_CREATED", outputs=item)
    return item

def pending():
    if not QUEUE.exists():
        return []
    return [json.loads(x) for x in QUEUE.read_text(encoding="utf-8").splitlines() if x.strip()]
