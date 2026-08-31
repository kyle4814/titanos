from .queue import pending
from .state import receipt
STEPS=("LOAD","CENSUS","SEARCH","PARETO","QUEUE","ROUTE","IMPLEMENT","TEST","BLUE_TEAM","RECEIPT","CHECKPOINT","CALIBRATE","PERSIST","NEXT")
def rank(ts): return sorted(ts,key=lambda x:(-x["priority"],x["created_at"],x["task_id"]))
def run_once():
    ts=rank(pending())
    if not ts: return {"status":"IDLE"}
    t=ts[0]; receipt(t["task_id"],"RAIL_OBSERVED",step="ROUTE",task=t); return {"status":"READY","task":t}
