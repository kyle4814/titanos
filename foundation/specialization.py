"""Domain-specialization telemetry for worker routing."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Specialization:
    worker_id: str
    domain: str
    completed: int = 0
    failed: int = 0
    evidence_count: int = 0

    @property
    def success_rate(self) -> float:
        total=self.completed+self.failed
        return self.completed/total if total else 0.0

@dataclass
class SpecializationBook:
    records: dict[tuple[str,str], Specialization] = field(default_factory=dict)

    def record(self, worker_id:str, domain:str, *, completed:bool, evidence_count:int=0)->Specialization:
        key=(worker_id,domain); old=self.records.get(key,Specialization(worker_id,domain))
        new=Specialization(worker_id,domain,old.completed+int(completed),old.failed+int(not completed),old.evidence_count+max(0,evidence_count))
        self.records[key]=new; return new

    def rank(self, worker_ids:tuple[str,...], domain:str)->tuple[str,...]:
        return tuple(sorted(worker_ids,key=lambda w:(-self.records.get((w,domain),Specialization(w,domain)).success_rate,
            -self.records.get((w,domain),Specialization(w,domain)).evidence_count,w)))

__all__=["Specialization","SpecializationBook"]
