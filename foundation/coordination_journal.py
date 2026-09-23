"""Crash-recoverable two-phase coordination journal for NEXT + swarm state."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
from foundation.next_kernel import OpportunityStore
from foundation.swarm_state import SwarmState, SwarmStateStore

@dataclass(frozen=True)
class CoordinationRecord:
    operation_id: str
    swarm_id: str
    phase: str  # PREPARED | COMMITTED
    state: SwarmState

class CoordinationJournal:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def prepare(self, record: CoordinationRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps({
            "operation_id":record.operation_id,
            "swarm_id":record.swarm_id,
            "phase":record.phase,
            "state":record.state.__dict__,
        },sort_keys=True),encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> CoordinationRecord | None:
        if not self.path.exists(): return None
        d=json.loads(self.path.read_text(encoding="utf-8"))
        s=d["state"]
        return CoordinationRecord(d["operation_id"],d["swarm_id"],d["phase"],
            SwarmState(d["swarm_id"],tuple(s["active"]),tuple(s["queued"]),tuple(s["completed"]),tuple(s["failed"])))

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

class CrashRecoverableCoordinator:
    def __init__(self,next_store:OpportunityStore,swarm_store:SwarmStateStore,journal:CoordinationJournal):
        self.next_store=next_store; self.swarm_store=swarm_store; self.journal=journal

    def commit(self, operation_id:str, state:SwarmState)->CoordinationRecord:
        record=CoordinationRecord(operation_id,state.swarm_id,"PREPARED",state)
        self.journal.prepare(record)
        self.swarm_store.save(state)
        committed=CoordinationRecord(operation_id,state.swarm_id,"COMMITTED",state)
        self.journal.prepare(committed)
        self.journal.clear()
        return committed

    def recover(self)->CoordinationRecord|None:
        record=self.journal.load()
        if not record: return None
        if record.phase=="COMMITTED":
            self.journal.clear()
            return record
        # PREPARED means swarm persistence may or may not have happened.
        # Re-publishing the same deterministic snapshot is idempotent.
        self.swarm_store.save(record.state)
        committed=CoordinationRecord(record.operation_id,record.swarm_id,"COMMITTED",record.state)
        self.journal.prepare(committed); self.journal.clear()
        return committed

__all__=["CoordinationRecord","CoordinationJournal","CrashRecoverableCoordinator"]
