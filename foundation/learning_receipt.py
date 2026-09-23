"""Auditable provenance receipts for learning mutations."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json, uuid

@dataclass(frozen=True)
class LearningReceipt:
    receipt_id: str
    actor: str
    mutation: str
    input_evidence: tuple[str, ...]
    before_hash: str
    after_hash: str
    observed_at: str

    @classmethod
    def create(cls, actor:str, mutation:str, input_evidence:tuple[str,...],
               before:object, after:object, observed_at:str|None=None):
        def digest(x):
            raw=json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()
            return "sha256:"+hashlib.sha256(raw).hexdigest()
        return cls(str(uuid.uuid4()),actor,mutation,tuple(input_evidence),
                   digest(before),digest(after),
                   observed_at or datetime.now(timezone.utc).isoformat())

    def verify_transition(self,before:object,after:object)->bool:
        def digest(x):
            raw=json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()
            return "sha256:"+hashlib.sha256(raw).hexdigest()
        return self.before_hash==digest(before) and self.after_hash==digest(after)

__all__=["LearningReceipt"]
