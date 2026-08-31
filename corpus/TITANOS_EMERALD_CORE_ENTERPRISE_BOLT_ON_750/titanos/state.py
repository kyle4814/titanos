from pathlib import Path
import hashlib, json, os, time, uuid
ROOT=Path(__file__).resolve().parents[1]; RUNTIME=ROOT/"runtime"; RUNTIME.mkdir(exist_ok=True)
STATE=RUNTIME/"state.json"; RECEIPTS=RUNTIME/"receipts.jsonl"
def canonical(x): return json.dumps(x, sort_keys=True, separators=(",",":"), ensure_ascii=False)
def sha(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def atomic_write(p,t):
    q=p.with_suffix(p.suffix+".tmp"); q.write_text(t,encoding="utf-8"); os.replace(q,p)
def load_state(): return json.loads(STATE.read_text()) if STATE.exists() else {}
def save_state(x): atomic_write(STATE,canonical(x))
def last_hash():
    if not RECEIPTS.exists(): return ""
    rows=[x for x in RECEIPTS.read_text().splitlines() if x.strip()]
    return json.loads(rows[-1])["hash"] if rows else ""
def receipt(task_id, action, **data):
    b={"receipt_id":str(uuid.uuid4()),"task_id":task_id,"action":action,
       "timestamp":time.time(),"previous_hash":last_hash(),**data}; b["hash"]=sha(b)
    with RECEIPTS.open("a",encoding="utf-8") as f: f.write(canonical(b)+"\n"); f.flush(); os.fsync(f.fileno())
    return b
