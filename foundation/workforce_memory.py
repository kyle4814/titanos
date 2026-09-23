"""Persistent workforce institutional memory."""
from __future__ import annotations
import json, os
from pathlib import Path
from foundation.worker_health import WorkerHealth, WorkerHealthBook
from foundation.specialization import Specialization, SpecializationBook

class WorkforceMemoryStore:
    def __init__(self,path:str|Path): self.path=Path(path)

    def save(self, health:WorkerHealthBook, specialization:SpecializationBook)->None:
        payload={"health":{wid:h.__dict__ for wid,h in health.workers.items()},
                 "specialization":[s.__dict__ for s in specialization.records.values()]}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":"))+"\n")
        os.replace(tmp,self.path)

    def load(self)->tuple[WorkerHealthBook,SpecializationBook]:
        if not self.path.exists(): return WorkerHealthBook(),SpecializationBook()
        raw=json.loads(self.path.read_text())
        if not isinstance(raw,dict) or not isinstance(raw.get("health",{}),dict) or not isinstance(raw.get("specialization",[]),list):
            raise ValueError("invalid workforce memory")
        h=WorkerHealthBook()
        for wid,row in raw["health"].items():
            h.workers[wid]=WorkerHealth(**row)
        s=SpecializationBook()
        for row in raw["specialization"]:
            item=Specialization(**row); s.records[(item.worker_id,item.domain)]=item
        return h,s

__all__=["WorkforceMemoryStore"]
