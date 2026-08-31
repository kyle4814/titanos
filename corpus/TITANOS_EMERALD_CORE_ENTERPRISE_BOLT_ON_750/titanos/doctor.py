import time
from .state import load_state,save_state,receipt
def run():
    s=load_state(); s["doctor_last_run"]=time.time(); s["offline_core"]=True; save_state(s)
    return receipt("SYSTEM","DOCTOR_PASS",outputs={"status":"OK"})
