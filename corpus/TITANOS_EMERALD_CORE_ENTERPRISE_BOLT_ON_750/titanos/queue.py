import json, uuid, time
from .state import ROOT, receipt
QUEUE=ROOT/"runtime"/"queue.jsonl"
def enqueue(mission,priority=0):
    t={"task_id":str(uuid.uuid4()),"mission":mission,"priority":float(priority),
       "status":"QUEUED","created_at":time.time()}
    with QUEUE.open("a") as f: f.write(json.dumps(t,sort_keys=True)+"\n")
    receipt(t["task_id"],"TASK_CREATED",outputs=t); return t
def pending():
    if not QUEUE.exists(): return []
    return [json.loads(x) for x in QUEUE.read_text().splitlines() if x.strip()]
