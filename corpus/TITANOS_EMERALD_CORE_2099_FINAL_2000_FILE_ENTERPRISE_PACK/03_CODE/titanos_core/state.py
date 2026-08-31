from pathlib import Path
import hashlib, json, os, time, uuid

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
RUNTIME.mkdir(exist_ok=True)
STATE = RUNTIME / "state.json"
RECEIPTS = RUNTIME / "receipts.jsonl"

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()

def atomic_write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}

def save_state(state):
    atomic_write(STATE, canonical(state))

def receipt_head():
    if not RECEIPTS.exists():
        return ""
    rows = [r for r in RECEIPTS.read_text(encoding="utf-8").splitlines() if r.strip()]
    return json.loads(rows[-1])["hash"] if rows else ""

def write_receipt(task_id, action, **payload):
    record = {
        "receipt_id": str(uuid.uuid4()),
        "task_id": task_id,
        "action": action,
        "timestamp": time.time(),
        "previous_hash": receipt_head(),
        **payload,
    }
    record["hash"] = digest(record)
    with RECEIPTS.open("a", encoding="utf-8") as fh:
        fh.write(canonical(record) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return record
