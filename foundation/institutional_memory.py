"""Versioned persistent institutional memory kernel."""
from __future__ import annotations
import json, os
from pathlib import Path
from foundation.learning_store import OpportunityLearningStore
from foundation.opportunity_feedback import OpportunityFeedbackBook
from foundation.workforce_memory import WorkforceMemoryStore
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook

CURRENT_SCHEMA=2

class InstitutionalMemory:
    def __init__(self, opportunity_learning=None, worker_health=None, specialization=None):
        self.opportunity_learning=opportunity_learning or OpportunityFeedbackBook()
        self.worker_health=worker_health or WorkerHealthBook()
        self.specialization=specialization or SpecializationBook()

class InstitutionalMemoryStore:
    """Atomic, versioned persistence with explicit schema migration."""
    def __init__(self,path:str|Path): self.path=Path(path)

    def _normalize(self,x):
        import dataclasses
        if dataclasses.is_dataclass(x): return {k:self._normalize(v) for k,v in dataclasses.asdict(x).items()}
        if isinstance(x,tuple): return [self._normalize(v) for v in x]
        if isinstance(x,dict): return {str(k):self._normalize(v) for k,v in x.items()}
        return x

    def save(self,memory:InstitutionalMemory)->None:
        payload={"schema_version":CURRENT_SCHEMA,
                 "opportunities":memory.opportunity_learning.records,
                 "health":memory.worker_health.workers,
                 "specialization":memory.specialization.records}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(self._normalize(payload),sort_keys=True,separators=(",",":"))+"\n")
        os.replace(tmp,self.path)

    @staticmethod
    def _migrate(raw:dict)->dict:
        version=raw.get("schema_version",1)
        if version==1:
            raw=dict(raw); raw["schema_version"]=2
            raw.setdefault("opportunities",{}); raw.setdefault("health",{}); raw.setdefault("specialization",[])
            return raw
        if version==CURRENT_SCHEMA: return raw
        raise ValueError(f"unsupported institutional memory schema: {version}")

    def load(self)->InstitutionalMemory:
        if not self.path.exists(): return InstitutionalMemory()
        raw=json.loads(self.path.read_text())
        if not isinstance(raw,dict): raise ValueError("invalid institutional memory")
        raw=self._migrate(raw)
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            op=OpportunityLearningStore(root/"op.json")
            op.path.write_text(json.dumps(raw.get("opportunities",{}),sort_keys=True))
            wb=WorkforceMemoryStore(root/"wf.json")
            wb.path.write_text(json.dumps({"health":raw.get("health",{}),"specialization":raw.get("specialization",[])},sort_keys=True))
            learning=op.load(); health,spec=wb.load()
        return InstitutionalMemory(learning,health,spec)

__all__=["CURRENT_SCHEMA","InstitutionalMemory","InstitutionalMemoryStore"]
