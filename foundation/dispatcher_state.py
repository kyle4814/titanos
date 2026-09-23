"""Persistent execution-pool state for the bounded TitanOS dispatcher."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json

@dataclass(frozen=True)
class DispatcherState:
    pool_id: str
    active: tuple[str, ...] = ()
    queued: tuple[str, ...] = ()
    completed: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()

class DispatcherStateStore:
    def __init__(self, path: str | Path):
        self.path=Path(path)

    def save(self,state:DispatcherState)->None:
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(asdict(state),sort_keys=True),encoding="utf-8")
        tmp.replace(self.path)

    def load(self,pool_id:str)->DispatcherState:
        if not self.path.exists(): return DispatcherState(pool_id)
        d=json.loads(self.path.read_text(encoding="utf-8"))
        if d.get("pool_id")!=pool_id: raise ValueError("dispatcher pool identity mismatch")
        return DispatcherState(pool_id,tuple(d.get("active",())),tuple(d.get("queued",())),tuple(d.get("completed",())),tuple(d.get("failed",())))

__all__=["DispatcherState","DispatcherStateStore"]
