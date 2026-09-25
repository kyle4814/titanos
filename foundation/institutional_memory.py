"""Cross-process locked institutional memory transactions."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from foundation.opportunity_feedback import OpportunityFeedbackBook
from foundation.learning_store import OpportunityLearningStore
from foundation.learning_receipt import LearningReceipt
from foundation.receipt_ledger import ReceiptLedger
from foundation.transaction_journal import MemoryTransactionJournal
from foundation.workforce_memory import WorkforceMemoryStore
from foundation.worker_health import WorkerHealthBook
from foundation.specialization import SpecializationBook
CURRENT_SCHEMA=4
class InstitutionalMemory:
    def __init__(self,opportunity_learning=None,worker_health=None,specialization=None):
        self.opportunity_learning=opportunity_learning or OpportunityFeedbackBook(); self.worker_health=worker_health or WorkerHealthBook(); self.specialization=specialization or SpecializationBook()
class InstitutionalMemoryStore:
    def __init__(self,path:str|Path,ledger_path=None,journal_path=None):
        self.path=Path(path); self.ledger=ReceiptLedger(ledger_path or self.path.with_suffix(".receipts.jsonl")); self.journal=MemoryTransactionJournal(journal_path or self.path.with_suffix(".tx.json")); self.lock_path=self.path.with_suffix(".lock")
    def _lock(self):
        self.lock_path.parent.mkdir(parents=True,exist_ok=True); f=self.lock_path.open("a+")
        try:
            import fcntl; fcntl.flock(f.fileno(),fcntl.LOCK_EX)
        except ImportError: pass
        return f
    def _unlock(self,f):
        try:
            import fcntl; fcntl.flock(f.fileno(),fcntl.LOCK_UN)
        except ImportError: pass
        f.close()
    def _normalize(self,x):
        import dataclasses
        if dataclasses.is_dataclass(x): return {k:self._normalize(v) for k,v in dataclasses.asdict(x).items()}
        if isinstance(x,tuple): return [self._normalize(v) for v in x]
        if isinstance(x,dict): return {str(k):self._normalize(v) for k,v in x.items()}
        return x
    @staticmethod
    def _canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
    @classmethod
    def _checksum(cls,x): return "sha256:"+hashlib.sha256(cls._canonical(x)).hexdigest()
    def _payload(self,m): return self._normalize({"schema_version":CURRENT_SCHEMA,"opportunities":m.opportunity_learning.records,"health":m.worker_health.workers,"specialization":tuple(v for _,v in sorted(m.specialization.records.items()))})
    def _write_memory(self,payload,receipt):
        envelope={**payload,"checksum":self._checksum(payload),"receipt":self._normalize(receipt)}; self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp"); tmp.write_text(json.dumps(envelope,sort_keys=True,separators=(",",":"))+"\n"); os.replace(tmp,self.path)
    def _raw_payload(self):
        # An absent store IS the empty memory. load() returns
        # InstitutionalMemory() for a missing file, so every producer derives
        # a receipt's `before` from _payload(load()); the persisted-state view
        # must be that same canonical, schema-versioned payload -- never {},
        # which is not a payload at all. Two encodings of one state made the
        # first write into a fresh store impossible (14 identical binding
        # errors, CI run 36188217313; EXP-002 left this open).
        if not self.path.exists(): return self._payload(InstitutionalMemory())
        raw=json.loads(self.path.read_text()); return {k:v for k,v in raw.items() if k not in ("checksum","receipt")}
    def reconcile(self):
        tx=self.journal.load()
        if not tx:return "CLEAN"
        if tx["status"]=="COMMITTED":
            if not self.ledger.verify():raise ValueError("receipt ledger integrity failure")
            self.journal.clear();return "COMMITTED_CLEARED"
        memory_hash=self._checksum(self._raw_payload())
        ledger=self.ledger.read(); head=ledger[-1]["entry_hash"] if ledger else "GENESIS"
        if memory_hash==tx["new_memory_hash"] and head==tx["ledger_entry_hash"]:
            self.journal.mark_committed();self.journal.clear();return "FINALIZED"
        if memory_hash==tx["previous_memory_hash"] and head!=tx["ledger_entry_hash"]:
            self.journal.clear();return "ROLLED_BACK"
        if memory_hash==tx["new_memory_hash"] and head!=tx["ledger_entry_hash"]:
            # Crash after the memory write, before the ledger commit. The
            # previous payload is retained nowhere, so rollback is impossible;
            # but the receipt was persisted verbatim in the memory envelope and
            # the journal holds the staged entry's hash, so the entry can be
            # rebuilt against the current head and is committed only if it
            # reproduces that hash exactly. Anything else stays unresolved.
            entry=self._staged_entry_from_memory(tx)
            if entry is not None:
                self.ledger.commit(entry);self.journal.mark_committed();self.journal.clear();return "FINALIZED"
        raise ValueError("unresolved institutional memory transaction")
    def _staged_entry_from_memory(self,tx):
        """Rebuild the ledger entry a PREPARED transaction staged, from the
        receipt persisted beside the memory payload. Returns None unless the
        rebuilt entry's hash equals the journal's ledger_entry_hash."""
        if not self.path.exists():return None
        rec=json.loads(self.path.read_text()).get("receipt")
        if not isinstance(rec,dict) or rec.get("receipt_id")!=tx["receipt_id"]:return None
        try:
            receipt=LearningReceipt(**{**rec,"input_evidence":tuple(rec.get("input_evidence",()))})
            entry=self.ledger.prepare(receipt)
        except (TypeError,ValueError):return None
        return entry if entry["entry_hash"]==tx["ledger_entry_hash"] else None
    def save(self,memory,receipt):
        lock=self._lock()
        try:
            if not isinstance(receipt,LearningReceipt):raise TypeError("learning receipt required")
            self.reconcile()
            if not self.ledger.verify():raise ValueError("receipt ledger integrity failure")
            payload=self._payload(memory);before=self._raw_payload()
            if not receipt.verify_transition(before,payload):raise ValueError("learning receipt does not bind this memory transition")
            staged=self.ledger.prepare(receipt);new_hash=self._checksum(payload);previous_hash=self._checksum(before)
            self.journal.begin(receipt.receipt_id,receipt.receipt_id,previous_hash,new_hash,staged["entry_hash"])
            self._write_memory(payload,receipt);self.ledger.commit(staged);self.journal.mark_committed();self.journal.clear()
        finally:self._unlock(lock)
    def load(self):
        lock=self._lock()
        try:
            self.reconcile()
            if not self.path.exists():return InstitutionalMemory()
            if not self.ledger.verify():raise ValueError("receipt ledger integrity failure")
            raw=json.loads(self.path.read_text());raw=self._verify(raw);raw=self._migrate(raw)
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);op=OpportunityLearningStore(root/"op.json");op.path.write_text(json.dumps(raw.get("opportunities",{}),sort_keys=True))
                wb=WorkforceMemoryStore(root/"wf.json");wb.path.write_text(json.dumps({"health":raw.get("health",{}),"specialization":raw.get("specialization",[])},sort_keys=True))
                learning=op.load();health,spec=wb.load()
            return InstitutionalMemory(learning,health,spec)
        finally:self._unlock(lock)
    @classmethod
    def _migrate(cls,raw):
        version=raw.get("schema_version",1)
        while version<CURRENT_SCHEMA:version+=1;raw=dict(raw);raw["schema_version"]=version
        if version!=CURRENT_SCHEMA:raise ValueError(f"unsupported institutional memory schema: {version}")
        return raw
    @classmethod
    def _verify(cls,raw):
        supplied=raw.pop("checksum",None)
        # The checksum covers the memory payload only; the binding receipt is
        # stored beside it (see _write_memory / _raw_payload), not inside it.
        raw.pop("receipt",None)
        if not supplied or supplied!=cls._checksum(raw):raise ValueError("institutional memory checksum mismatch")
        return raw
__all__=["CURRENT_SCHEMA","InstitutionalMemory","InstitutionalMemoryStore"]
