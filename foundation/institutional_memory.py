"""Versioned, checksummed institutional memory with mandatory receipt ledger."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from foundation.opportunity_feedback import OpportunityFeedbackBook
from foundation.learning_receipt import LearningReceipt
from foundation.receipt_ledger import ReceiptLedger
from foundation.workforce_memory import WorkforceMemoryStore
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
CURRENT_SCHEMA=4
class InstitutionalMemory:
    def __init__(self,opportunity_learning=None,worker_health=None,specialization=None):
        self.opportunity_learning=opportunity_learning or OpportunityFeedbackBook()
        self.worker_health=worker_health or WorkerHealthBook()
        self.specialization=specialization or SpecializationBook()
class InstitutionalMemoryStore:
    def __init__(self,path:str|Path,ledger_path:str|Path|None=None):
        self.path=Path(path); self.ledger=ReceiptLedger(ledger_path or self.path.with_suffix(".receipts.jsonl"))
    def _normalize(self,x):
        import dataclasses
        if dataclasses.is_dataclass(x): return {k:self._normalize(v) for k,v in dataclasses.asdict(x).items()}
        if isinstance(x,tuple): return [self._normalize(v) for v in x]
        if isinstance(x,dict): return {str(k):self._normalize(v) for k,v in x.items()}
        return x
    @staticmethod
    def _canonical(payload): return json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    @classmethod
    def _checksum(cls,payload): return "sha256:"+hashlib.sha256(cls._canonical(payload)).hexdigest()
    def _payload(self,memory):
        return self._normalize({"schema_version":CURRENT_SCHEMA,"opportunities":memory.opportunity_learning.records,"health":memory.worker_health.workers,"specialization":memory.specialization.records})
    def save(self,memory,receipt):
        if not isinstance(receipt,LearningReceipt): raise TypeError("learning receipt required")
        if not self.ledger.verify(): raise ValueError("receipt ledger integrity failure")
        payload=self._payload(memory); before={}
        if self.path.exists():
            raw=json.loads(self.path.read_text()); before={k:v for k,v in raw.items() if k not in ("checksum","receipt")}
        if not receipt.verify_transition(before,payload): raise ValueError("learning receipt does not bind this memory transition")
        self.ledger.append(receipt)
        envelope={**payload,"checksum":self._checksum(payload),"receipt":self._normalize(receipt)}
        self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix(self.path.suffix+".tmp")
        try:
            tmp.write_text(json.dumps(envelope,sort_keys=True,separators=(",",":"))+"\n"); os.replace(tmp,self.path)
        except Exception:
            raise
    @classmethod
    def _migrate(cls,raw):
        version=raw.get("schema_version",1)
        while version<CURRENT_SCHEMA:
            version+=1; raw=dict(raw); raw["schema_version"]=version
        if version!=CURRENT_SCHEMA: raise ValueError(f"unsupported institutional memory schema: {version}")
        return raw
    @classmethod
    def _verify(cls,raw):
        supplied=raw.pop("checksum",None)
        if not supplied: raise ValueError("institutional memory checksum missing")
        if supplied!=cls._checksum(raw): raise ValueError("institutional memory checksum mismatch")
        return raw
    def load(self):
        if not self.path.exists(): return InstitutionalMemory()
        if not self.ledger.verify(): raise ValueError("receipt ledger integrity failure")
        raw=json.loads(self.path.read_text())
        if not isinstance(raw,dict): raise ValueError("invalid institutional memory")
        raw=self._verify(raw); raw=self._migrate(raw)
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); op=OpportunityLearningStore(root/"op.json")
            op.path.write_text(json.dumps(raw.get("opportunities",{}),sort_keys=True))
            wb=WorkforceMemoryStore(root/"wf.json")
            wb.path.write_text(json.dumps({"health":raw.get("health",{}),"specialization":raw.get("specialization",[])},sort_keys=True))
            learning=op.load(); health,spec=wb.load()
        return InstitutionalMemory(learning,health,spec)
__all__=["CURRENT_SCHEMA","InstitutionalMemory","InstitutionalMemoryStore"]
