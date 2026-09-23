"""Versioned, checksummed institutional memory with mandatory mutation receipts."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from foundation.opportunity_feedback import OpportunityFeedbackBook
from foundation.learning_receipt import LearningReceipt
from foundation.workforce_memory import WorkforceMemoryStore
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook

CURRENT_SCHEMA=3

class InstitutionalMemory:
    def __init__(self,opportunity_learning=None,worker_health=None,specialization=None):
        self.opportunity_learning=opportunity_learning or OpportunityFeedbackBook()
        self.worker_health=worker_health or WorkerHealthBook()
        self.specialization=specialization or SpecializationBook()

class InstitutionalMemoryStore:
    def __init__(self,path:str|Path): self.path=Path(path)
    def _normalize(self,x):
        import dataclasses
        if dataclasses.is_dataclass(x): return {k:self._normalize(v) for k,v in dataclasses.asdict(x).items()}
        if isinstance(x,tuple): return [self._normalize(v) for v in x]
        if isinstance(x,dict): return {str(k):self._normalize(v) for k,v in x.items()}
        return x
    @staticmethod
    def _canonical(payload:dict)->bytes: return json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    @classmethod
    def _checksum(cls,payload:dict)->str: return "sha256:"+hashlib.sha256(cls._canonical(payload)).hexdigest()
    def _payload(self,memory):
        return self._normalize({"schema_version":CURRENT_SCHEMA,"opportunities":memory.opportunity_learning.records,
                                "health":memory.worker_health.workers,"specialization":memory.specialization.records})
    def save(self,memory:InstitutionalMemory,receipt:LearningReceipt)->None:
        if not isinstance(receipt,LearningReceipt): raise TypeError("learning receipt required")
        payload=self._payload(memory)
        current_before={}
        if self.path.exists():
            raw=json.loads(self.path.read_text()); current_before={k:v for k,v in raw.items() if k not in ("checksum","receipt")}
        if not receipt.verify_transition(current_before,payload):
            raise ValueError("learning receipt does not bind this memory transition")
        envelope={**payload,"checksum":self._checksum(payload),"receipt":self._normalize(receipt)}
        self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(envelope,sort_keys=True,separators=(",",":"))+"\n"); os.replace(tmp,self.path)
    @staticmethod
    def _migrate(raw:dict)->dict:
        version=raw.get("schema_version",1)
        if version==1:
            raw=dict(raw); raw["schema_version"]=2
            raw.setdefault("opportunities",{}); raw.setdefault("health",{}); raw.setdefault("specialization",[])
            version=2
        if version==2:
            raw=dict(raw); raw["schema_version"]=3
            version=3
        if version==CURRENT_SCHEMA:return raw
        raise ValueError(f"unsupported institutional memory schema: {version}")
    @classmethod
    def _verify(cls,raw:dict)->dict:
        supplied=raw.pop("checksum",None)
        if not supplied: raise ValueError("institutional memory checksum missing")
        if supplied!=cls._checksum(raw): raise ValueError("institutional memory checksum mismatch")
        return raw
    def load(self)->InstitutionalMemory:
        if not self.path.exists(): return InstitutionalMemory()
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
