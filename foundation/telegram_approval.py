"""
Telegram Approval + Alert loop — the async human-in-the-loop keystone.

Kyle's model: the machine hunts and runs the whole pipeline; the human is a
*tap*, not a halt. This is that tap. It plugs into Kyle's existing moneyprinter
Telegram bot (via TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID, the same env
`telegram_notify` already uses) and provides two primitives:

  request_approval(...) -> Decision
      Fire an Approve/Deny card for a GATED action (money, credentials, legal,
      outbound-as-Kyle, irreversible). The machine keeps working while it
      waits; Kyle taps from his phone.

  alert_operator(...) -> bool
      "I need a sword to sharpen against." Ping Kyle to come into the chat when
      the machine hits something that needs his judgment mid-op.

FAIL-CLOSED, BY CONSTRUCTION. An approval that cannot be obtained is NOT an
approval: no credentials, a timeout, or a deny all return a Decision whose
`is_approved` is False. The caller MUST check `.is_approved` and refuse the
gated action otherwise — the two-point enforcement that keeps "runs without
Kyle" safe. And the card only *gates* an action; it never *legalises* one — the
caller must only ever propose lawful, non-abusive actions (the legal rail sits
before the card, never after it).

No test touches the network: `sender` and `decision_source` are injected.

DECISION CONTRACT (2026-09-26). A decision used to be a bare string: no
nonce, no expiry, no one-time semantics (the same request_id approved
twice), no sender identity, and a constant default request_id -- so any
decision source answering "approve" approved every card. Now every card
mints a single-use nonce (`secrets.token_hex`, as ApprovalEnvelope does)
and an expiry, both printed on the card and carried in the button
callback data, and `decision_source(request_id, nonce)` must return a
mapping `{"decision": "approve"|"deny", "nonce": <echo>, "sender": <claim>}`.
The nonce must echo (constant-time compare), the decision must arrive
before expiry, and APPROVED additionally requires `expected_sender` to be
supplied by the caller and to equal the sender claim -- WHO that is stays a
human policy input; this module never infers identity from a username,
message text or the word "approve". Anything else is MALFORMED / UNBOUND /
TIMEOUT, none of which is approved. The private transport is responsible
for verifying the claim it forwards; this contract is what it must satisfy.
"""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable, Mapping, Optional, Union

from foundation import telegram_notify
from foundation.telegram_notify import _resolve_credentials, operator_switch
from foundation.communication_gate import authorize_communication

__all__ = [
    "ApprovalRequest",
    "Decision",
    "request_approval",
    "alert_operator",
    "format_card",
]


class Decision(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    TIMEOUT = "TIMEOUT"        # no tap within the window / after expiry — NOT approved
    UNAVAILABLE = "UNAVAILABLE"  # no bot credentials — treated as NOT approved
    MALFORMED = "MALFORMED"    # decision not bound to this card (nonce/shape/sender) — NOT approved
    UNBOUND = "UNBOUND"        # approve tap, but no expected_sender policy supplied — NOT approved

    @property
    def is_approved(self) -> bool:
        return self is Decision.APPROVED


@dataclass(frozen=True)
class ApprovalRequest:
    """A complete, glanceable decision surface — a thin card is fake
    governance, so every field is required and must be TRUE."""
    action: str        # WHAT will happen, exactly (incl. the content/command)
    why: str           # the opportunity / expected value
    cost: str          # money / time / risk
    reversible: str    # can it be undone? how?

    def __post_init__(self) -> None:
        for name in ("action", "why", "cost", "reversible"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"approval card field {name!r} must not be empty "
                                 "— a thin card is fake governance")


def format_card(req: ApprovalRequest, *, request_id: str = "", nonce: str = "",
                expires_at: str = "") -> str:
    """The Telegram message body. HTML-safe, glanceable. The reference line
    binds the card to one request id + single-use nonce and states when the
    decision stops being accepted."""
    def esc(s: str) -> str:
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    ref = ""
    if request_id or nonce or expires_at:
        ref = (f"<b>REF:</b> {esc(request_id)}:{esc(nonce)}\n"
               f"<b>EXPIRES:</b> {esc(expires_at)}\n\n")
    return (
        "🛡️ <b>TITAN — approval needed</b>\n\n"
        f"<b>WHAT:</b> {esc(req.action)}\n"
        f"<b>WHY:</b> {esc(req.why)}\n"
        f"<b>COST:</b> {esc(req.cost)}\n"
        f"<b>REVERSIBLE:</b> {esc(req.reversible)}\n\n"
        f"{ref}"
        "Tap ✅ Approve or ❌ Deny below."
    )


# --- production senders/pollers (injected in tests) --------------------------

def _default_sender(req_id: str, text: str,
                    token: str, chat_id: str, nonce: str = "") -> None:
    """Send the card with inline Approve/Deny buttons — through
    `telegram_notify`'s sanctioned gated socket, NOT a socket of our own (the
    control plane must stay unbypassable). The nonce rides in the callback
    data so the poller can echo it without parsing message text."""
    suffix = f"{req_id}:{nonce}" if nonce else req_id
    markup = {"inline_keyboard": [[
        {"text": "✅ Approve", "callback_data": f"approve:{suffix}"},
        {"text": "❌ Deny", "callback_data": f"deny:{suffix}"},
    ]]}
    telegram_notify.send_card(text, markup, token=token, chat_id=chat_id)


DecisionPayload = Union[Mapping[str, object], str, None]


def _bind_decision(raw: DecisionPayload, nonce: str,
                   expected_sender: Optional[str]) -> Decision:
    """Turn a transport's answer into a Decision. Everything that is not a
    mapping echoing this card's nonce with a recognised decision is
    MALFORMED; an approve with no sender policy is UNBOUND; an approve whose
    sender claim differs from the policy is MALFORMED. Never approved by
    default."""
    if raw is None:
        return Decision.TIMEOUT
    if not isinstance(raw, Mapping):
        return Decision.MALFORMED  # legacy bare string: unbound to any card
    echoed = raw.get("nonce")
    if not isinstance(echoed, str) or not hmac.compare_digest(echoed, nonce):
        return Decision.MALFORMED
    decision = raw.get("decision")
    if not isinstance(decision, str):
        return Decision.MALFORMED
    decision = decision.strip().lower()
    if decision == "deny":
        return Decision.DENIED
    if decision != "approve":
        return Decision.MALFORMED
    if expected_sender is None:
        return Decision.UNBOUND
    claim = raw.get("sender")
    if not isinstance(claim, str) or not claim or claim != expected_sender:
        return Decision.MALFORMED
    return Decision.APPROVED


DEFAULT_TTL_SECONDS = 900


def request_approval(req: ApprovalRequest,
                     *,
                     sender: Optional[Callable[[str, str], None]] = None,
                     decision_source: Optional[Callable[[str, str], DecisionPayload]] = None,
                     token: Optional[str] = None,
                     chat_id: Optional[str] = None,
                     request_id: str = "titan-approval",
                     expected_sender: Optional[str] = None,
                     ttl_seconds: int = DEFAULT_TTL_SECONDS,
                     now: Union[datetime, Callable[[], datetime], None] = None) -> Decision:
    """Fire the approval card and return the Decision.

    `sender(request_id, card_text)` posts the card;
    `decision_source(request_id, nonce)` returns None (no tap yet) or a
    mapping {"decision": "approve"|"deny", "nonce": <echo of the card's
    nonce>, "sender": <verified sender claim>}. Both are injected in tests; in
    production they are built from the bot credentials and the (private)
    poller. `expected_sender` is the operator identity policy: without it an
    approve tap is UNBOUND, never APPROVED. `now` may be a datetime or a
    clock callable (tests); the expiry check runs after the decision arrives.

    FAIL-CLOSED: no credentials -> UNAVAILABLE; no tap or late tap ->
    TIMEOUT; unbound/mis-shaped/wrong-sender -> MALFORMED; approve with no
    sender policy -> UNBOUND. Only APPROVED has is_approved == True.
    Authorization is charged on the NOTIFY_OPERATOR scope before anything is
    sent — the same gate as every other Telegram write."""
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    clock = now if callable(now) else (lambda fixed=now: fixed or datetime.now(timezone.utc))
    # Gate first (the socket discipline), exactly like telegram_notify.
    decision_switch = authorize_communication(operator_switch())
    if not decision_switch:
        return Decision.UNAVAILABLE

    nonce = secrets.token_hex(16)
    issued = clock()
    expires_at = issued + timedelta(seconds=ttl_seconds)

    if sender is None or decision_source is None:
        tok, cid = _resolve_credentials(token, chat_id)
        if not tok or not cid:
            return Decision.UNAVAILABLE
        if sender is None:
            sender = lambda rid, text: _default_sender(rid, text, tok, cid, nonce=nonce)
        if decision_source is None:
            # Real polling of getUpdates is the production path; not exercised
            # in tests (which always inject decision_source). Absent a poller,
            # fail closed rather than block forever.
            return Decision.UNAVAILABLE

    sender(request_id, format_card(req, request_id=request_id, nonce=nonce,
                                   expires_at=expires_at.isoformat()))
    raw = decision_source(request_id, nonce)
    if raw is not None and clock() >= expires_at:
        return Decision.TIMEOUT  # a late tap is no tap, however well-formed
    return _bind_decision(raw, nonce, expected_sender)


def alert_operator(headline: str, detail: str = "",
                   *,
                   opener: Optional[Callable] = None,
                   token: Optional[str] = None,
                   chat_id: Optional[str] = None) -> bool:
    """Ping Kyle to come into the chat — 'I need a sword to sharpen against.'
    Returns True if sent, False if no credentials (fail-soft: an alert that
    can't send just doesn't, it never blocks the op). Routes through
    `telegram_notify`'s sanctioned gated socket. `opener` injected in tests."""
    tok, cid = _resolve_credentials(token, chat_id)
    if not tok or not cid:
        return False
    text = ("🗡️ <b>TITAN needs you</b>\n\n" + str(headline)
            + (("\n\n" + str(detail)) if detail else "")
            + "\n\nCome sharpen swords when you get a sec.")
    try:
        result = telegram_notify.send_messages(
            (text,), token=tok, chat_id=cid, opener=opener)
    except Exception:
        return False
    return result.delivered > 0
