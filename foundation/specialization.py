"""Specialization routing with outcome-driven learning."""
from __future__ import annotations
from dataclasses import dataclass, field
from foundation.worker_health import WorkerHealthBook

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
    def record_outcome(self, worker_id:str, domain:str, *, outcome:str, evidence_count:int=0)->Specialization:
        if outcome not in {"SUCCESS","FAILURE"}: raise ValueError("outcome must be SUCCESS or FAILURE")
        return self.record(worker_id,domain,completed=outcome=="SUCCESS",evidence_count=evidence_count)
    def rank(self, worker_ids:tuple[str,...], domain:str)->tuple[str,...]:
        return tuple(sorted(worker_ids,key=lambda w:(-self.records.get((w,domain),Specialization(w,domain)).success_rate,-self.records.get((w,domain),Specialization(w,domain)).evidence_count,w)))
    def rank_with_health(self, worker_ids:tuple[str,...], domain:str, health:WorkerHealthBook)->tuple[str,...]:
        eligible=tuple(w for w in worker_ids if not health.workers.get(w,__import__("foundation.worker_health",fromlist=["WorkerHealth"]).WorkerHealth(w)).quarantined)
        def key(w):
            s=self.records.get((w,domain),Specialization(w,domain)); h=health.workers.get(w)
            return (-s.success_rate,-s.evidence_count,1 if h and h.probation_remaining else 0,-(h.throughput if h else 0.0),h.failure_rate if h else 0.0,w)
        return tuple(sorted(eligible,key=key))
__all__=["Specialization","SpecializationBook"]