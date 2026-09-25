"""Machine-readable human approval envelope for consequential execution.

An approval is bound to one exact ExecutionIntent fingerprint. It is not a
generic permission and cannot be reused for a materially different action.

AUTHENTICITY (2026-09-25). A dataclass anyone can construct proves nothing,
so an envelope now carries an HMAC-SHA256 `mac` over its canonical fields
(including a single-use `nonce`, the intent id and a parameter hash) under a
key held by the approving side. `AuthorizationGate` verifies that MAC before
it mints a permit. The key is always passed in explicitly; this module never
stores, derives or defaults one, and refuses keys shorter than 32 bytes.
HMAC is symmetric: whoever holds the key can also sign, so the key must stay
with the approver and the gate only.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Optional

from foundation.execution_intent import ExecutionIntent, ExecutionIntentError

__all__ = [
    "AlreadyConsumedError", "ApprovalDecision", "ApprovalEnvelope",
    "ApprovalError", "ConsumedIds", "ConsumptionUnavailable",
    "RING0_SECRET_ENV", "Ring0SecretError", "compute_mac", "load_ring0_key",
    "parameter_hash",
]

MIN_KEY_BYTES = 32


ApprovalDecision = Literal["APPROVE", "DECLINE", "REVIEW"]


class ApprovalError(ExecutionIntentError):
    """Raised when an approval envelope is invalid or does not bind."""


def _check_key(key: Any) -> bytes:
    if not isinstance(key, (bytes, bytearray)) or len(key) < MIN_KEY_BYTES:
        raise ApprovalError(
            f"approval key missing or shorter than {MIN_KEY_BYTES} bytes; refusing")
    return bytes(key)


def compute_mac(key: bytes, label: str, payload: Mapping[str, Any]) -> str:
    """HMAC-SHA256 over `label` + canonical JSON (same canonical form as
    ExecutionIntent.fingerprint). The label separates approval MACs from
    permit MACs so one can never be replayed as the other."""
    body = json.dumps({"kind": label, **payload}, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    return hmac.new(_check_key(key), body, hashlib.sha256).hexdigest()


def parameter_hash(intent: ExecutionIntent) -> str:
    raw = json.dumps(dict(intent.parameters), sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class AlreadyConsumedError(ApprovalError):
    """The single-use id was consumed before: a replay. A domain result,
    never an infrastructure error."""


class ConsumptionUnavailable(ApprovalError):
    """The ledger could not be reached or stayed locked past every retry.
    Fails closed like a replay, but is reported as infrastructure, so a
    lock is never mistaken for (or disguised as) a security outcome."""


class ConsumedIds:
    """Single-use identifiers (approval nonces, permit ids) in a SQLite file.

    `id` is the PRIMARY KEY, so the database itself decides the one winner:
    each consume() is BEGIN IMMEDIATE -> INSERT -> COMMIT on its own
    connection. A duplicate raises AlreadyConsumedError; lock contention is
    retried with backoff and, if it never clears, raises
    ConsumptionUnavailable. There is no in-memory cache, so the answer is
    the same across threads, processes and restarts."""

    SCHEMA = ("CREATE TABLE IF NOT EXISTS consumed_ids ("
              "id TEXT PRIMARY KEY NOT NULL, consumed_at TEXT NOT NULL)")
    BUSY_TIMEOUT_S = 10.0
    MAX_ATTEMPTS = 20

    def __init__(self, path: Path) -> None:
        if path is None or str(path) in ("", ":memory:"):
            raise ApprovalError("ConsumedIds needs a database file path; "
                                "process-local replay protection is refused")
        self._path = Path(path)
        self._run(lambda c: c.execute(self.SCHEMA))

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self._path), timeout=self.BUSY_TIMEOUT_S,
                               isolation_level=None)

    def _run(self, work):
        last: Exception | None = None
        for attempt in range(self.MAX_ATTEMPTS):
            conn = None
            try:
                conn = self._connect()
                conn.execute("BEGIN IMMEDIATE")
                result = work(conn)
                conn.execute("COMMIT")
                return result
            except sqlite3.IntegrityError:
                if conn is not None:
                    conn.execute("ROLLBACK")
                raise
            except sqlite3.OperationalError as exc:
                if conn is not None and conn.in_transaction:
                    conn.execute("ROLLBACK")
                msg = str(exc).lower()
                if "locked" not in msg and "busy" not in msg:
                    raise ConsumptionUnavailable(f"consumption ledger error: {exc}") from exc
                last = exc
                time.sleep(min(0.05 * (2 ** attempt), 1.0))
            finally:
                if conn is not None:
                    conn.close()
        raise ConsumptionUnavailable(
            f"consumption ledger stayed locked after {self.MAX_ATTEMPTS} attempts: {last}")

    def consume(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ApprovalError("single-use id is missing")
        stamp = datetime.now(timezone.utc).isoformat()
        try:
            self._run(lambda c: c.execute(
                "INSERT INTO consumed_ids (id, consumed_at) VALUES (?, ?)", (value, stamp)))
        except sqlite3.IntegrityError as exc:
            raise AlreadyConsumedError(
                f"id {value!r} was already used; replay refused") from exc

    def count(self, value: str) -> int:
        conn = self._connect()
        try:
            return conn.execute("SELECT COUNT(*) FROM consumed_ids WHERE id = ?",
                                (value,)).fetchone()[0]
        finally:
            conn.close()

    def __contains__(self, value: object) -> bool:
        return isinstance(value, str) and self.count(value) > 0


# ── Ring 0 secret: boot fail-closed ──────────────────────────────────────
RING0_SECRET_ENV = "TITANOS_RING0_SECRET"

# Values that must never sign anything, however long they are.
KNOWN_DEV_SECRETS = frozenset({
    "dev", "development", "test", "testing", "secret", "changeme", "change-me",
    "password", "default", "titanos", "titanos-dev", "titanos-dev-secret",
    "ring0", "ring0-dev", "insecure", "example",
})


class Ring0SecretError(ApprovalError):
    """Raised at boot when the Ring 0 approval secret is unusable."""


def load_ring0_key(environ: Optional[Mapping[str, str]] = None) -> bytes:
    """Read TITANOS_RING0_SECRET and return it as the approval key. There is
    no fallback: missing, empty, a known development value, shorter than
    MIN_KEY_BYTES, or a single repeated character all raise Ring0SecretError."""
    env = os.environ if environ is None else environ
    raw = env.get(RING0_SECRET_ENV)
    if raw is None or not raw.strip():
        raise Ring0SecretError(f"{RING0_SECRET_ENV} is not set; refusing to boot")
    value = raw.strip()
    if value.lower() in KNOWN_DEV_SECRETS:
        raise Ring0SecretError(f"{RING0_SECRET_ENV} is a known development value; refusing to boot")
    if len(value.encode("utf-8")) < MIN_KEY_BYTES:
        raise Ring0SecretError(
            f"{RING0_SECRET_ENV} is shorter than {MIN_KEY_BYTES} bytes; refusing to boot")
    if len(set(value)) == 1:
        raise Ring0SecretError(f"{RING0_SECRET_ENV} is one repeated character; refusing to boot")
    return value.encode("utf-8")


@dataclass(frozen=True)
class ApprovalEnvelope:
    proposal_id: str
    intent_fingerprint: str
    decision: ApprovalDecision
    authority: str
    policy_version: str
    expires_at: str
    target: str
    action: str
    expected_effect: str
    decided_at: str
    reviewer: str
    intent_id: str = ""
    parameter_hash: str = ""
    nonce: str = ""
    mac: str = ""

    @classmethod
    def decide(
        cls,
        *,
        proposal_id: str,
        intent: ExecutionIntent,
        decision: ApprovalDecision,
        authority: str,
        reviewer: str,
        decided_at: str | None = None,
        nonce: str | None = None,
    ) -> "ApprovalEnvelope":
        if decision not in ("APPROVE", "DECLINE", "REVIEW"):
            raise ApprovalError("decision must be APPROVE, DECLINE, or REVIEW")
        if not authority.strip() or not reviewer.strip():
            raise ApprovalError("authority and reviewer must be non-empty")
        return cls(
            proposal_id=proposal_id,
            intent_fingerprint=intent.fingerprint(),
            decision=decision,
            authority=authority,
            policy_version=intent.policy_version,
            expires_at=intent.expires_at,
            target=intent.target,
            action=intent.action,
            expected_effect=intent.expected_effect,
            decided_at=decided_at or datetime.now(timezone.utc).isoformat(),
            reviewer=reviewer,
            intent_id=intent.intent_id,
            parameter_hash=parameter_hash(intent),
            nonce=nonce if nonce is not None else secrets.token_hex(16),
        )

    def validate_for(self, intent: ExecutionIntent, now: datetime | None = None) -> None:
        if self.intent_fingerprint != intent.fingerprint():
            raise ApprovalError("approval does not bind to the exact intent fingerprint")
        if self.target != intent.target or self.action != intent.action:
            raise ApprovalError("approval target/action mismatch")
        if self.policy_version != intent.policy_version:
            raise ApprovalError("approval policy version mismatch")
        if self.expires_at != intent.expires_at:
            raise ApprovalError("approval expiry mismatch")
        if self.expected_effect != intent.expected_effect:
            raise ApprovalError("approval expected-effect mismatch")
        if self.authority != intent.authority_required:
            raise ApprovalError("approval authority does not satisfy intent requirement")
        expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        current = now or datetime.now(timezone.utc)
        if expiry <= current:
            raise ApprovalError("approval is expired")

    def is_authorized_for(self, intent: ExecutionIntent, now: datetime | None = None) -> bool:
        self.validate_for(intent, now)
        return self.decision == "APPROVE"

    def signing_payload(self) -> dict[str, object]:
        """Every field except `mac` -- the exact bytes the MAC binds."""
        payload = self.to_dict()
        payload.pop("mac")
        return payload

    def signed(self, key: bytes) -> "ApprovalEnvelope":
        """Ring 0: the approving side seals this envelope with its key."""
        if not self.nonce.strip():
            raise ApprovalError("an envelope must carry a nonce before signing")
        return replace(self, mac=compute_mac(key, "approval-v1", self.signing_payload()))

    def verify_mac(self, key: bytes) -> None:
        expected = compute_mac(key, "approval-v1", self.signing_payload())
        if not isinstance(self.mac, str) or not hmac.compare_digest(self.mac, expected):
            raise ApprovalError("approval MAC is missing or invalid")

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "intent_fingerprint": self.intent_fingerprint,
            "decision": self.decision,
            "authority": self.authority,
            "policy_version": self.policy_version,
            "expires_at": self.expires_at,
            "target": self.target,
            "action": self.action,
            "expected_effect": self.expected_effect,
            "decided_at": self.decided_at,
            "reviewer": self.reviewer,
            "intent_id": self.intent_id,
            "parameter_hash": self.parameter_hash,
            "nonce": self.nonce,
            "mac": self.mac,
        }
