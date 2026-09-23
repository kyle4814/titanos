"""Unified persistent institutional memory kernel.

Coordinates opportunity learning with workforce health/specialization so restart
recovery restores one coherent learning state.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from foundation.learning_store import OpportunityLearningStore
from foundation.opportunity_feedback import OpportunityFeedbackBook
from foundation.workforce_memory import WorkforceMemoryStore
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook

class InstitutionalMemory:
    def __init__(self, opportunity_learning: OpportunityFeedbackBook | None = None,
                 worker_health: WorkerHealthBook | None = None,
                 specialization: SpecializationBook | None = None):
        self.opportunity_learning=opportunity_learning or OpportunityFeedbackBook()
        self.worker_health=worker_health or WorkerHealthBook()
        self.specialization=specialization or SpecializationBook()

class InstitutionalMemoryStore:
    """Atomic persistence of the complete learning state."""
    def __init__(self, path: str | Path): self.path=Path(path)

    def save(self, memory: InstitutionalMemory) -> None:
        self.path.parent.mkdir(parents=True,exist_ok=True)
        payload={"opportunities": memory.opportunity_learning.records,
                 "health": memory.worker_health.workers,
                 "specialization": memory.specialization.records}
        # Normalize dataclasses through the existing store serializers.
        import dataclasses
        def norm(x):
            if dataclasses.is_dataclass(x): return {k:norm(v) for k,v in dataclasses.asdict(x).items()}
            if isinstance(x,tuple): return [norm(v) for v in x]
            if isinstance(x,dict): return {str(k):norm(v) for k,v in x.items()}
            return x
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(norm(payload),sort_keys=True,separators=(",",":"))+"\n")
        os.replace(tmp,self.path)

    def load(self) -> InstitutionalMemory:
        if not self.path.exists(): return InstitutionalMemory()
        raw=json.loads(self.path.read_text())
        if not isinstance(raw,dict): raise ValueError("invalid institutional memory")
        # Rehydrate using the canonical domain stores by writing/reading only in memory.
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            op=OpportunityLearningStore(root/"op.json")
            op.path.write_text(json.dumps(raw.get("opportunities",{}),sort_keys=True))
            wb=WorkforceMemoryStore(root/"wf.json")
            wb.path.write_text(json.dumps({"health":raw.get("health",{}),
                                           "specialization":raw.get("specialization",[])},sort_keys=True))
            learning=op.load(); health,spec=wb.load()
        return InstitutionalMemory(learning,health,spec)

__all__=["InstitutionalMemory","InstitutionalMemoryStore"]
