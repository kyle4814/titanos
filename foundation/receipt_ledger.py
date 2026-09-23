"""Append-only, hash-chained ledger for learning receipts."""
from __future__ import annotations
from dataclasses import asdict
import hashlib,json,os
from pathlib import Path
from foundation.learning_receipt import LearningReceipt

class ReceiptLedger:
    def __init__(self,path:str|Path): self.path=Path(path)

    @staticmethod
    def _canonical(x:dict)->bytes:
        return json.dumps(x,sort_keys=True,separators=(",",":")).encode()

    @classmethod
    def _hash(cls,x:dict)->str:
        return "sha256:"+hashlib.sha256(cls._canonical(x)).hexdigest()

    def append(self,receipt:LearningReceipt)->None:
        if not isinstance(receipt,LearningReceipt): raise TypeError("LearningReceipt required")
        rows=self.read()
        previous=rows[-1]["entry_hash"] if rows else "GENESIS"
        body={"receipt":asdict(receipt),"previous_hash":previous}
        entry={"previous_hash":previous,"receipt":asdict(receipt),
               "entry_hash":self._hash(body)}
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.open("a",encoding="utf-8") as f:
            f.write(json.dumps(entry,sort_keys=True,separators=(",",":"))+"\n")

    def read(self)->list[dict]:
        if not self.path.exists(): return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def verify(self)->bool:
        rows=self.read()
        previous="GENESIS"
        for row in rows:
            if row.get("previous_hash")!=previous: return False
            body={"receipt":row.get("receipt"),"previous_hash":row.get("previous_hash")}
            if row.get("entry_hash")!=self._hash(body): return False
            previous=row["entry_hash"]
        return True

__all__=["ReceiptLedger"]
