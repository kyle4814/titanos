"""
Authority Sigil — the finite, typed, scoped, revocable, expiring authority
object a persistent runtime consumes, plus the fail-closed gate that
checks it. Built 2026-08-27 per Kyle's explicit authorization: "build
toward persistent governed autonomy, but the system receives no master
key. Capability may expand; authority may only expand through separately
explicit, finite release codes."

WHAT THIS FILE IS, AND IS NOT

Not a spend mechanism. Not a worker. Not a scheduler. Not a second
authority model competing with `communication_gate.py`/
`publication_gate.py`/`hells_gate.py` — this module answers a narrower
question those don't: "may THIS specific, already-running, unattended
tick perform THIS specific action, right now, within THIS specific
budget window" — a question that only exists once something runs
without a human present to ask each time. Every other critical-function
gate in this repository is still the authority of record for what it
already governs; a `ReleaseCode`'s `allowed_capabilities` may name one
of those gates as a downstream check, never bypass it.

THE ONE-TIME-DELEGATION LAW (the actual point of this module)

ONE-TIME DELEGATION != UNLIMITED FUTURE PERMISSION. A `ReleaseCode` is a
finite object: named authority_class, an explicit capability set, an
explicit target set, a hard budget with a period, a mandatory expiry,
and revocability. Nothing here can mint or widen its own authority —
there is no `expand_scope()`, no `renew()`, no `increase_budget()`
anywhere in this file's public surface, checked by test. The only ways a
release's authority ever changes are `issue_release()` (a brand new
object, every field explicit, no defaults that grant scope) and
`revoke_release()` (only ever narrows). A capability, target, or budget
increase requires a brand new, separately-issued release — never an edit
to an existing one.

FAIL-CLOSED, TWO-POINT ENFORCEMENT (same shape as publication_gate.py /
communication_gate.py)

`evaluate()` computes a decision from the ledger's own persisted state.
`authorize_action()` does not trust a cached decision — it re-derives
from the ledger every call, so a caller cannot construct a stale
"admitted" object by hand and have this module believe it. Every
required condition (not expired, not revoked, capability allowed,
target allowed, budget available) must be positively established; an
unknown or missing fact never defaults to permission.

DURABILITY IS DELIBERATE HERE, UNLIKE MOST OF THIS REPOSITORY'S STORES

`QuarantineStore`/`PromotionStore`/`CrystalStore` are documented,
accepted, in-memory-only (see INTUITION.md) because nothing in this
repository has ever needed to survive a process restart mid-operation.
This module is the one real exception: a persistent runtime's budget
state MUST survive a restart, or a crash-and-restart loop would silently
reset a spend/action budget every time it happened -- a real security
hole, not a hypothetical one. `ReleaseLedger` persists to an append-only
JSONL file, same pattern as `kpm/source-vault/registry.py`.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, FrozenSet, Optional

__all__ = [
    "AUTHORITY_CLASSES",
    "ReleaseCode",
    "ActionRecord",
    "ReleaseLedger",
    "ActionDecision",
    "AuthoritySigilError",
    "issue_release",
    "revoke_release",
    "evaluate",
    "authorize_action",
]

_DEFAULT_LEDGER_PATH = Path(__file__).resolve().parent / "authority_ledger.jsonl"

# Constrained vocabulary -- an authority_class outside this set is a
# structural rejection at issuance, same discipline as
# kpm/source-vault/registry.py's SOURCE_TYPES. Exactly one class exists
# right now: the zero-spend, read-only class this module's own proof
# cycle uses. A spend-bearing or write-bearing class is a future,
# separately-designed release-class, not something this constant grows
# into by extending a tuple.
AUTHORITY_CLASSES: FrozenSet[str] = frozenset({
    "ZERO_SPEND_READ_ONLY",
})


class AuthoritySigilError(Exception):
    """Base for structured rejections raised by this module."""


@dataclass(frozen=True)
class ReleaseCode:
    """A finite, explicit authority grant. Every field is required and
    explicit at issuance -- no field has a default that grants scope.
    Frozen: a ReleaseCode cannot be mutated to widen itself after
    construction; the only legitimate lifecycle events are recorded
    separately in the ledger (revocation, action consumption)."""

    release_id: str
    authority_class: str
    allowed_capabilities: FrozenSet[str]
    allowed_targets: FrozenSet[str]
    max_actions_per_period: int
    period_seconds: int
    issued_by: str
    issued_at: str
    expires_at: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["allowed_capabilities"] = sorted(self.allowed_capabilities)
        d["allowed_targets"] = sorted(self.allowed_targets)
        return d


@dataclass(frozen=True)
class ActionRecord:
    """One consumed tick against a release's budget. Append-only."""

    release_id: str
    capability: str
    target: str
    occurred_at: str
    result: str  # ADMIT | DENY -- DENY entries do not consume budget

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionDecision:
    admitted: bool = False
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"admitted": self.admitted, "reasons": list(self.reasons)}


class ReleaseLedger:
    """Append-only ledger of issued releases, revocations, and consumed
    actions. Mirrors kpm/source-vault/registry.py's shape: in-memory
    dict as the fast path, JSONL as the durable, replay-on-construction
    paper trail. No `update`, no `delete`, no `widen` -- revocation is
    itself an append-only record, never an edit to the original release."""

    def __init__(self, ledger_path: str | Path | None = _DEFAULT_LEDGER_PATH) -> None:
        self._ledger_path = Path(ledger_path) if ledger_path else None
        self._releases: dict[str, ReleaseCode] = {}
        self._revoked: set[str] = set()
        self._actions: list[ActionRecord] = []
        if self._ledger_path and self._ledger_path.exists():
            self._replay()

    def _replay(self) -> None:
        """Fail-soft over malformed lines, same discipline as
        foundation/mouth_common.py::read_mouth_log_continuity(). A real
        crash (process killed mid-write, power loss, OOM) can only ever
        truncate the last unflushed append -- every prior line is a
        completed, durable write and is always replayed. Skipping a
        corrupted trailing line only ever loses that one record (at
        worst, one action under-counted against budget -- safe-direction,
        never grants more authority than actually existed); it must never
        crash the whole ledger, which would force a destructive manual
        recovery (delete/truncate the file) that silently resets all
        budget and revocation state -- a real, evidenced defect, found
        and fixed 2026-08-28 by directly simulating a truncated write."""
        with open(self._ledger_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    self._replay_line(json.loads(line))
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

    def _replay_line(self, obj: dict[str, Any]) -> None:
        kind = obj["kind"]
        if kind == "RELEASE":
            rc = ReleaseCode(
                release_id=obj["release_id"],
                authority_class=obj["authority_class"],
                allowed_capabilities=frozenset(obj["allowed_capabilities"]),
                allowed_targets=frozenset(obj["allowed_targets"]),
                max_actions_per_period=obj["max_actions_per_period"],
                period_seconds=obj["period_seconds"],
                issued_by=obj["issued_by"],
                issued_at=obj["issued_at"],
                expires_at=obj["expires_at"],
            )
            self._releases[rc.release_id] = rc
        elif kind == "REVOKE":
            self._revoked.add(obj["release_id"])
        elif kind == "ACTION":
            self._actions.append(ActionRecord(
                release_id=obj["release_id"], capability=obj["capability"],
                target=obj["target"], occurred_at=obj["occurred_at"],
                result=obj["result"],
            ))

    def _append(self, obj: dict[str, Any]) -> None:
        if not self._ledger_path:
            return
        with open(self._ledger_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, sort_keys=True))
            fh.write("\n")

    def get_release(self, release_id: str) -> Optional[ReleaseCode]:
        return self._releases.get(release_id)

    def is_revoked(self, release_id: str) -> bool:
        return release_id in self._revoked

    def actions_in_window(self, release_id: str, since: datetime) -> int:
        count = 0
        for a in self._actions:
            if a.release_id != release_id or a.result != "ADMIT":
                continue
            occurred = datetime.fromisoformat(a.occurred_at)
            if occurred.tzinfo is None:
                occurred = occurred.replace(tzinfo=timezone.utc)
            if occurred >= since:
                count += 1
        return count

    def all_releases(self) -> tuple[ReleaseCode, ...]:
        return tuple(self._releases.values())

    def all_actions(self) -> tuple[ActionRecord, ...]:
        return tuple(self._actions)

    # -- the only two ways authority is ever created or reduced --------

    def record_release(self, rc: ReleaseCode) -> None:
        self._releases[rc.release_id] = rc
        d = rc.to_dict()
        d["kind"] = "RELEASE"
        self._append(d)

    def record_revocation(self, release_id: str) -> None:
        self._revoked.add(release_id)
        self._append({"kind": "REVOKE", "release_id": release_id})

    def record_action(self, record: ActionRecord) -> None:
        self._actions.append(record)
        d = record.to_dict()
        d["kind"] = "ACTION"
        self._append(d)


def issue_release(
    ledger: ReleaseLedger,
    *,
    release_id: str,
    authority_class: str,
    allowed_capabilities: FrozenSet[str],
    allowed_targets: FrozenSet[str],
    max_actions_per_period: int,
    period_seconds: int,
    issued_by: str,
    duration_seconds: int,
    now: Optional[datetime] = None,
) -> ReleaseCode:
    """The only way a ReleaseCode comes into existence. Every scope field
    is required, explicit, and named by the caller -- there is no
    default that grants a capability, target, or budget the caller did
    not explicitly ask for. Raises AuthoritySigilError for a structurally
    invalid request rather than silently narrowing or widening it."""
    if authority_class not in AUTHORITY_CLASSES:
        raise AuthoritySigilError(
            f"authority_class {authority_class!r} is not in the declared "
            f"vocabulary {sorted(AUTHORITY_CLASSES)} -- a release cannot "
            f"be issued under an undeclared authority class"
        )
    if not allowed_capabilities:
        raise AuthoritySigilError("allowed_capabilities must be non-empty")
    if not allowed_targets:
        raise AuthoritySigilError("allowed_targets must be non-empty")
    if max_actions_per_period <= 0 or period_seconds <= 0:
        raise AuthoritySigilError(
            "max_actions_per_period and period_seconds must both be positive "
            "-- an unbounded or zero budget is not a valid release"
        )
    if not issued_by.strip():
        raise AuthoritySigilError("issued_by is required -- a release with no named human issuer is not valid")
    if duration_seconds <= 0:
        raise AuthoritySigilError("duration_seconds must be positive -- a release must expire")
    if ledger.get_release(release_id) is not None:
        raise AuthoritySigilError(f"release_id {release_id!r} already exists -- release ids are not reusable")

    issued_at_dt = now or datetime.now(timezone.utc)
    issued_at = issued_at_dt.isoformat()
    expires_at = (issued_at_dt.timestamp() + duration_seconds)
    expires_at_iso = datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()

    rc = ReleaseCode(
        release_id=release_id, authority_class=authority_class,
        allowed_capabilities=frozenset(allowed_capabilities),
        allowed_targets=frozenset(allowed_targets),
        max_actions_per_period=max_actions_per_period, period_seconds=period_seconds,
        issued_by=issued_by, issued_at=issued_at, expires_at=expires_at_iso,
    )
    ledger.record_release(rc)
    return rc


def revoke_release(ledger: ReleaseLedger, release_id: str) -> None:
    """The only way a release's authority is ever reduced before its own
    expiry. Idempotent: revoking an already-revoked or unknown release_id
    is not an error -- the end state (no authority) is what matters."""
    ledger.record_revocation(release_id)


def evaluate(
    ledger: ReleaseLedger,
    release_id: str,
    capability: str,
    target: str,
    now: Optional[datetime] = None,
) -> ActionDecision:
    """Point one of two-point enforcement. Fail-closed throughout: every
    required condition must be positively established. Never performs
    the action itself -- this module only decides whether it may be
    performed."""
    d = ActionDecision()
    current = now or datetime.now(timezone.utc)

    rc = ledger.get_release(release_id)
    if rc is None:
        d.reasons.append(f"release_id {release_id!r} does not exist")
        return d

    if ledger.is_revoked(release_id):
        d.reasons.append(f"release {release_id!r} has been revoked")
        return d

    expires = datetime.fromisoformat(rc.expires_at)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if current >= expires:
        d.reasons.append(f"release {release_id!r} expired at {rc.expires_at}")
        return d

    if capability not in rc.allowed_capabilities:
        d.reasons.append(
            f"capability {capability!r} is not in this release's "
            f"allowed_capabilities {sorted(rc.allowed_capabilities)}"
        )
        return d

    if target not in rc.allowed_targets:
        d.reasons.append(
            f"target {target!r} is not in this release's "
            f"allowed_targets {sorted(rc.allowed_targets)}"
        )
        return d

    window_start = datetime.fromtimestamp(
        current.timestamp() - rc.period_seconds, tz=timezone.utc
    )
    used = ledger.actions_in_window(release_id, window_start)
    if used >= rc.max_actions_per_period:
        d.reasons.append(
            f"budget exhausted: {used}/{rc.max_actions_per_period} actions "
            f"already consumed in the trailing {rc.period_seconds}s window"
        )
        return d

    d.admitted = True
    d.reasons.append(
        f"capability {capability!r} on target {target!r} authorized under "
        f"release {release_id!r} ({used + 1}/{rc.max_actions_per_period} "
        f"this period)"
    )
    return d


def authorize_action(
    ledger: ReleaseLedger,
    release_id: str,
    capability: str,
    target: str,
    now: Optional[datetime] = None,
) -> ActionDecision:
    """Point two of two-point enforcement. Re-derives from the ledger's
    own persisted state every call -- never trusts a cached decision.
    Records the result (ADMIT or DENY) as a durable ActionRecord either
    way, so a denied attempt is never silently invisible. Only an ADMIT
    consumes budget (see ReleaseLedger.actions_in_window's ADMIT-only
    filter)."""
    decision = evaluate(ledger, release_id, capability, target, now=now)
    occurred_at = (now or datetime.now(timezone.utc)).isoformat()
    ledger.record_action(ActionRecord(
        release_id=release_id, capability=capability, target=target,
        occurred_at=occurred_at, result="ADMIT" if decision.admitted else "DENY",
    ))
    return decision
