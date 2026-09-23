"""Deterministic persistent kernel for the NEXT opportunity queue.

This module is deliberately small: policy lives in the command layer; repeatable
state transitions live here. It never performs outbound actions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


STATES = {
    "DISCOVERED", "QUALIFIED", "PREPARED", "READY", "COMMITTED", "OUTCOME",
    "REJECTED", "EXPIRED", "BLOCKED", "STALE", "DUPLICATE",
    "HUMAN-GATED", "ALREADY-ACTIONED", "FAILED", "SUCCEEDED",
    "AWAITING-OUTCOME",
}

FORWARD = {
    "DISCOVERED": {"QUALIFIED", "REJECTED", "DUPLICATE", "STALE", "BLOCKED"},
    "QUALIFIED": {"PREPARED", "REJECTED", "EXPIRED", "STALE", "BLOCKED"},
    "PREPARED": {"READY", "HUMAN-GATED", "REJECTED", "STALE", "BLOCKED"},
    "READY": {"COMMITTED", "HUMAN-GATED", "REJECTED", "EXPIRED", "STALE"},
    "COMMITTED": {"OUTCOME", "AWAITING-OUTCOME", "FAILED"},
    "AWAITING-OUTCOME": {"OUTCOME", "SUCCEEDED", "FAILED", "STALE"},
    "OUTCOME": {"SUCCEEDED", "FAILED"},
}

TERMINAL = {"REJECTED", "EXPIRED", "DUPLICATE", "ALREADY-ACTIONED", "SUCCEEDED", "FAILED"}


def fingerprint(source: str, external_id: str = "", url: str = "") -> str:
    """Stable identity from source + external identity, with URL as fallback."""
    key = "|".join(part.strip().lower() for part in (source, external_id or url))
    if not source.strip() or not (external_id.strip() or url.strip()):
        raise ValueError("source and external_id/url are required")
    return sha256(key.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Opportunity:
    id: str
    source: str
    title: str
    status: str = "DISCOVERED"
    value: float | None = None
    deadline: str | None = None
    evidence_refs: tuple[str, ...] = ()
    authority: str = "O0"
    next_action: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("id is required")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("source is required")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title is required")
        if self.status not in STATES:
            raise ValueError(f"invalid state: {self.status}")
        if self.authority not in {"O0", "O1", "O2", "O3", "O4"}:
            raise ValueError(f"invalid authority: {self.authority}")
        if self.value is not None and (isinstance(self.value, bool) or not isinstance(self.value, (int, float))):
            raise ValueError("value must be numeric or None")
        if not isinstance(self.evidence_refs, (tuple, list)) or not all(isinstance(x, str) for x in self.evidence_refs):
            raise ValueError("evidence_refs must be a sequence of strings")


class OpportunityStore:
    """Tiny JSON store with atomic replacement and forward-only transitions."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict[str, Opportunity]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid persisted NEXT state") from exc
        if not isinstance(raw, dict):
            raise ValueError("persisted NEXT state must be an object")
        items = {k: Opportunity(**v) for k, v in raw.items()}
        for key, item in items.items():
            if not isinstance(key, str) or key != item.id:
                raise ValueError("persisted opportunity key/id mismatch")
        return items

    def save(self, items: dict[str, Opportunity]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {k: asdict(v) for k, v in sorted(items.items())}
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def upsert(self, item: Opportunity) -> str:
        """Insert or merge an observation without regressing lifecycle state.

        Repeated discovery is not a duplicate *fact* when it carries new
        evidence. The durable queue therefore keeps the existing lifecycle
        state/authority while unioning newly observed evidence references.
        This makes repeated NEXT cycles compound evidence instead of either
        double-counting or silently discarding it.
        """
        items = self.load()
        if item.id in items:
            existing = items[item.id]
            if existing.source != item.source:
                raise ValueError("opportunity identity collision")
            merged_refs = tuple(sorted(set(existing.evidence_refs) | set(item.evidence_refs)))
            if merged_refs == existing.evidence_refs:
                return "DUPLICATE"
            items[item.id] = Opportunity(
                **{
                    **asdict(existing),
                    "evidence_refs": merged_refs,
                }
            )
            self.save(items)
            return "UPDATED"
        items[item.id] = item
        self.save(items)
        return "NEW"

    def advance(self, opportunity_id: str, new_status: str) -> Opportunity:
        items = self.load()
        if opportunity_id not in items:
            raise KeyError(opportunity_id)
        if new_status not in STATES:
            raise ValueError(f"invalid state: {new_status}")
        current = items[opportunity_id]
        allowed = FORWARD.get(current.status, set())
        if new_status not in allowed:
            raise ValueError(f"invalid transition: {current.status} -> {new_status}")
        updated = Opportunity(**{**asdict(current), "status": new_status})
        items[opportunity_id] = updated
        self.save(items)
        return updated

    def actionable(self) -> list[Opportunity]:
        """Return durable work candidates; terminal and stale states stay visible."""
        return sorted(
            (x for x in self.load().values()
             if x.status in {"DISCOVERED", "QUALIFIED", "PREPARED", "READY", "HUMAN-GATED", "AWAITING-OUTCOME"}),
            key=lambda x: (x.deadline is None, x.deadline or "", -(x.value or 0.0), x.id),
        )

def ingest_pipeline_opportunities(
    store: OpportunityStore,
    opportunities: Any,
) -> tuple[str, ...]:
    """Persist observed pipeline opportunities into the NEXT queue.

    This is an observation adapter only. It deliberately assigns O0 and
    DISCOVERED: a signal is not qualification, commitment, money, or
    authority. The adapter reads the pipeline's existing opportunity shape
    without importing it, avoiding a dependency cycle.
    """
    results: list[str] = []
    for observed in opportunities:
        party = str(observed.controlling_party).strip()
        if not party:
            continue
        refs = sorted({
            ref
            for signal in observed.signals
            for ref in (str(signal.source_ref).strip(), f"signal:{signal.signal_id}")
            if ref
        })
        item = Opportunity(
            id=str(observed.opportunity_id),
            source="opportunity_pipeline",
            title=f"Observed demand: {party}",
            status="DISCOVERED",
            evidence_refs=tuple(refs),
            authority="O0",
            next_action=(
                "QUALIFY: verify eligibility, value, deadline, and actionability "
                "from primary evidence"
            ),
        )
        results.append(store.upsert(item))
    return tuple(results)
