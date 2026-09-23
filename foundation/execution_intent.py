"""Canonical boundary between a verified opportunity and an executable action.

This module does NOT execute anything and does NOT grant authority. It freezes
the exact action a worker proposes so downstream approval/execution systems can
bind their decision to the same target, parameters, expected effect, policy,
and expiry. Changing any load-bearing field produces a different fingerprint.

The envelope is deliberately adapter-neutral: Stripe, GitHub, email, tenders,
Web3, contracts, or the existing private TitanOS business system can consume
it without putting their credentials or implementation into this repository.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

__all__ = ["ExecutionIntent", "ExecutionIntentError"]


class ExecutionIntentError(ValueError):
    """Raised when an execution proposal is incomplete or internally invalid."""


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda x: str(x[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ExecutionIntentError(
        f"parameters contain unsupported value type {type(value).__name__!r}"
    )


@dataclass(frozen=True)
class ExecutionIntent:
    """An exact, immutable proposal for one externally meaningful action.

    This is a proposal, not permission. A caller must still pass the relevant
    authority gate before anything leaves the system.
    """

    intent_id: str
    target: str
    action: str
    parameters: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    expected_effect: str
    authority_required: str
    reversible: bool
    expires_at: str
    policy_version: str

    def __post_init__(self) -> None:
        for name in (
            "intent_id", "target", "action", "expected_effect",
            "authority_required", "expires_at", "policy_version",
        ):
            if not str(getattr(self, name)).strip():
                raise ExecutionIntentError(f"{name} must not be empty")

        if not self.evidence_refs:
            raise ExecutionIntentError(
                "an execution intent must cite at least one evidence reference"
            )
        if any(not str(ref).strip() for ref in self.evidence_refs):
            raise ExecutionIntentError("evidence references must be non-empty")

        try:
            datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ExecutionIntentError("expires_at must be an ISO-8601 timestamp") from exc

        canonical = _canonical(dict(self.parameters))
        object.__setattr__(self, "parameters", MappingProxyType(canonical))
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))

    def binding_payload(self) -> dict[str, Any]:
        """Return the exact fields an approval/executor must bind to."""
        return {
            "intent_id": self.intent_id,
            "target": self.target,
            "action": self.action,
            "parameters": _canonical(self.parameters),
            "evidence_refs": list(self.evidence_refs),
            "expected_effect": self.expected_effect,
            "authority_required": self.authority_required,
            "reversible": self.reversible,
            "expires_at": self.expires_at,
            "policy_version": self.policy_version,
        }

    def fingerprint(self) -> str:
        """Stable SHA-256 binding for the exact proposed action."""
        raw = json.dumps(
            self.binding_payload(), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return "EI-" + hashlib.sha256(raw).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        payload = self.binding_payload()
        payload["fingerprint"] = self.fingerprint()
        return payload
