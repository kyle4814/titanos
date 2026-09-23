"""Persistent opportunity learning memory.

Atomic JSON persistence for feedback records. Unknown/malformed records are
rejected rather than silently converted, preserving evidence integrity.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from foundation.opportunity_feedback import OutcomeFeedback, OpportunityFeedbackBook

class OpportunityLearningStore:
    def __init__(self, path: str | Path):
        self.path=Path(path)

    def save(self, book: OpportunityFeedbackBook) -> None:
        payload={}
        for oid, rows in book.records.items():
            payload[oid]=[{
                "opportunity_id": x.opportunity_id,
                "expected_value": x.expected_value,
                "realized_value": x.realized_value,
                "completed": x.completed,
                "evidence_strength": x.evidence_strength,
                "observed_at": x.observed_at,
            } for x in rows]
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix(self.path.suffix+".tmp")
        tmp.write_text(json.dumps(payload,sort_keys=True,separators=(",",":"))+"\n")
        os.replace(tmp,self.path)

    def load(self) -> OpportunityFeedbackBook:
        if not self.path.exists(): return OpportunityFeedbackBook()
        raw=json.loads(self.path.read_text())
        if not isinstance(raw,dict): raise ValueError("learning store root must be an object")
        book=OpportunityFeedbackBook()
        for oid, rows in raw.items():
            if not isinstance(rows,list): raise ValueError(f"invalid records for {oid}")
            for row in rows:
                if row.get("opportunity_id") != oid: raise ValueError("opportunity id mismatch")
                book.record(OutcomeFeedback(
                    opportunity_id=oid,
                    expected_value=float(row["expected_value"]),
                    realized_value=float(row["realized_value"]),
                    completed=bool(row["completed"]),
                    evidence_strength=float(row.get("evidence_strength",0.0)),
                    observed_at=row.get("observed_at")))
        return book

__all__=["OpportunityLearningStore"]
