"""Approval bridge for canonical ExecutionIntent envelopes.

This module deliberately stops at human approval. It does not execute the
intent and it does not create authority. The approval request binds the exact
ExecutionIntent fingerprint into the visible action text AND the Telegram
request identity so a callback cannot be ambiguously associated with another
intent.
"""

from __future__ import annotations

from foundation.execution_intent import ExecutionIntent
from foundation.telegram_approval import ApprovalRequest, Decision, request_approval

__all__ = ["approval_request_for_intent", "request_intent_approval"]


def approval_request_for_intent(intent: ExecutionIntent) -> ApprovalRequest:
    """Render an exact ExecutionIntent into the existing Telegram gate."""
    params = ", ".join(
        f"{key}={value!r}" for key, value in sorted(intent.parameters.items())
    )
    action = (
        f"{intent.action} on {intent.target}; "
        f"intent={intent.intent_id}; fingerprint={intent.fingerprint()}; "
        f"expires={intent.expires_at}"
    )
    evidence = ", ".join(intent.evidence_refs)
    why = (
        f"Evidence: {evidence}. "
        f"Expected effect: {intent.expected_effect}. "
        f"Parameters: {params or '(none)'}.")
    cost = f"Authority required: {intent.authority_required}; policy={intent.policy_version}"
    reversible = "yes" if intent.reversible else "NO — irreversible action"
    return ApprovalRequest(
        action=action,
        why=why,
        cost=cost,
        reversible=reversible,
    )


def request_intent_approval(intent: ExecutionIntent, **kwargs) -> Decision:
    """Submit an exact intent to the existing Telegram approval gate.

    The approval request id is bound to the canonical intent fingerprint by
    default. This prevents concurrent approval cards from sharing the
    generic titan-approval callback identity. A caller may still supply
    an explicit request_id for an externally coordinated workflow.
    """
    kwargs.setdefault("request_id", f"intent:{intent.fingerprint()}")
    return request_approval(approval_request_for_intent(intent), **kwargs)
