"""Durable transaction journal for institutional memory recovery."""
from __future__ import annotations
import json, os
from pathlib import Path

class MemoryTransactionJournal:
    def __init__(self,path:str|Path): self.path=Path(path)
    def begin(self,tx_id:str,receipt_id:str,previous_memory_hash:str,new_memory_hash:str,ledger_entry_hash:str)->None:
        payload={"tx_id":tx_id,"receipt_id":receipt_id,"previous_memory_hash":previous_memory_hash,
                 "new_memory_hash":new_memory_hash,"ledger_entry_hash":ledger_entry_hash,"status":"PREPARED"}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(payload,sort_keys=True)+"\n")
        os.replace(tmp,self.path)
    def mark_committed(self)->None:
        if not self.path.exists(): raise ValueError("transaction journal missing")
        raw=json.loads(self.path.read_text()); raw["status"]="COMMITTED"
        tmp=self.path.with_suffix(".tmp"); tmp.write_text(json.dumps(raw,sort_keys=True)+"\n"); os.replace(tmp,self.path)
    def load(self)->dict|None:
        if not self.path.exists(): return None
        raw=json.loads(self.path.read_text())
        if raw.get("status") not in {"PREPARED","COMMITTED"}: raise ValueError("invalid transaction journal")
        return raw
    def clear(self)->None:
        if self.path.exists(): self.path.unlink()

    def abort(self, tx_id:str)->None:
        tx=self.load()
        if tx is None:return
        if tx["tx_id"] != tx_id: raise ValueError("transaction id mismatch")
        if tx["status"] != "PREPARED": raise ValueError("cannot abort committed transaction")
        self.clear()
__all__=["MemoryTransactionJournal"]
