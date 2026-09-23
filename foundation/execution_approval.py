"""Approval bridge for canonical ExecutionIntent envelopes.

This module deliberately stops at human approval. It does not execute the
intent and it does not create authority. The approval request binds the exact
ExecutionIntent fingerprint into the visible action text so the downstream
executor can require the same fingerprint before acting.
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
    why = (
        f"Evidence: {', '.join(intent.evidence_refs)}. "
        f"Expected effect: {intent.expected_effect}. "
        f"Parameters: {params or '(none)'}."
    )
    cost = f"Authority required: {intent.authority_required}; policy={intent.policy_version}"
    reversible = "yes" if intent.reversible else "NO — irreversible action"
    return ApprovalRequest(
        action=action,
        why=why,
        cost=cost,
        reversible=reversible,
    )


def request_intent_approval(intent: ExecutionIntent, **kwargs) -> Decision:
    """Submit an exact intent to the existing Telegram approval gate."""
    return request_approval(approval_request_for_intent(intent), **kwargs)
