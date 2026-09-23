"""Append-only hash-chained receipt ledger with atomic staged commits."""
from __future__ import annotations
from dataclasses import asdict
import hashlib,json,os
from pathlib import Path
from foundation.learning_receipt import LearningReceipt
class ReceiptLedger:
    def __init__(self,path:str|Path): self.path=Path(path)
    @staticmethod
    def _canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":")).encode()
    @classmethod
    def _hash(cls,x): return "sha256:"+hashlib.sha256(cls._canonical(x)).hexdigest()
    def _entry(self,receipt,previous):
        body={"receipt":asdict(receipt),"previous_hash":previous}
        return {**body,"entry_hash":self._hash(body)}
    def prepare(self,receipt):
        if not isinstance(receipt,LearningReceipt): raise TypeError("LearningReceipt required")
        rows=self.read()
        if any(row.get("receipt",{}).get("receipt_id")==receipt.receipt_id for row in rows):
            raise ValueError("duplicate receipt id")
        previous=rows[-1]["entry_hash"] if rows else "GENESIS"
        return self._entry(receipt,previous)
    def append(self,receipt): self.commit(self.prepare(receipt))
    def commit(self,entry):
        rows=self.read(); previous=rows[-1]["entry_hash"] if rows else "GENESIS"
        if entry.get("previous_hash")!=previous: raise ValueError("ledger head changed")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        with tmp.open("w",encoding="utf-8") as f:
            if self.path.exists(): f.write(self.path.read_text())
            f.write(json.dumps(entry,sort_keys=True,separators=(",",":"))+"\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,self.path)
    def read(self):
        if not self.path.exists(): return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]
    def verify(self):
        rows=self.read(); previous="GENESIS"
        for row in rows:
            if row.get("previous_hash")!=previous:return False
            body={"receipt":row.get("receipt"),"previous_hash":row.get("previous_hash")}
            if row.get("entry_hash")!=self._hash(body):return False
            previous=row["entry_hash"]
        return True
__all__=["ReceiptLedger"]
