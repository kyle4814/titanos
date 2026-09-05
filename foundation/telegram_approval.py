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
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from foundation.telegram_notify import (
    API_BASE, TelegramNotifyError, _resolve_credentials, _post_message,
    operator_switch,
)
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
    TIMEOUT = "TIMEOUT"        # no tap within the window — treated as NOT approved
    UNAVAILABLE = "UNAVAILABLE"  # no bot credentials — treated as NOT approved

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


def format_card(req: ApprovalRequest) -> str:
    """The Telegram message body. HTML-safe, glanceable."""
    def esc(s: str) -> str:
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    return (
        "🛡️ <b>TITAN — approval needed</b>\n\n"
        f"<b>WHAT:</b> {esc(req.action)}\n"
        f"<b>WHY:</b> {esc(req.why)}\n"
        f"<b>COST:</b> {esc(req.cost)}\n"
        f"<b>REVERSIBLE:</b> {esc(req.reversible)}\n\n"
        "Tap ✅ Approve or ❌ Deny below."
    )


# --- production senders/pollers (injected in tests) --------------------------

def _default_sender(req_id: str, text: str,
                    token: str, chat_id: str) -> None:
    """Send the card with inline Approve/Deny buttons via the real bot."""
    import urllib.request
    import urllib.parse
    url = f"{API_BASE}/bot{token}/sendMessage"
    markup = {"inline_keyboard": [[
        {"text": "✅ Approve", "callback_data": f"approve:{req_id}"},
        {"text": "❌ Deny", "callback_data": f"deny:{req_id}"},
    ]]}
    payload = urllib.parse.urlencode({
        "chat_id": chat_id, "text": text, "parse_mode": "HTML",
        "reply_markup": json.dumps(markup),
    }).encode("utf-8")
    r = urllib.request.Request(url, data=payload, method="POST")
    r.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urllib.request.urlopen(r, timeout=30)  # pragma: no cover - network
    body = json.loads(resp.read().decode("utf-8", "replace"))
    if not body.get("ok", False):
        raise TelegramNotifyError(
            f"Telegram rejected the card: {body.get('description', 'unknown')}")


def request_approval(req: ApprovalRequest,
                     *,
                     sender: Optional[Callable[[str, str], None]] = None,
                     decision_source: Optional[Callable[[str], Optional[str]]] = None,
                     token: Optional[str] = None,
                     chat_id: Optional[str] = None,
                     request_id: str = "titan-approval") -> Decision:
    """Fire the approval card and return the Decision.

    `sender(request_id, card_text)` posts the card; `decision_source(request_id)`
    returns "approve"/"deny"/None (None = no tap yet / timeout). Both are
    injected in tests; in production they are built from the bot credentials.

    FAIL-CLOSED: no credentials -> UNAVAILABLE; no tap -> TIMEOUT; both have
    is_approved == False. Authorization is charged on the NOTIFY_OPERATOR scope
    before anything is sent — the same gate as every other Telegram write."""
    # Gate first (the socket discipline), exactly like telegram_notify.
    decision_switch = authorize_communication(operator_switch())
    if not decision_switch:
        return Decision.UNAVAILABLE

    if sender is None or decision_source is None:
        tok, cid = _resolve_credentials(token, chat_id)
        if not tok or not cid:
            return Decision.UNAVAILABLE
        if sender is None:
            sender = lambda rid, text: _default_sender(rid, text, tok, cid)
        if decision_source is None:
            # Real polling of getUpdates is the production path; not exercised
            # in tests (which always inject decision_source). Absent a poller,
            # fail closed rather than block forever.
            return Decision.UNAVAILABLE

    sender(request_id, format_card(req))
    raw = decision_source(request_id)
    if raw is None:
        return Decision.TIMEOUT
    raw = str(raw).strip().lower()
    if raw == "approve":
        return Decision.APPROVED
    if raw == "deny":
        return Decision.DENIED
    # Any unrecognised response is NOT an approval.
    return Decision.TIMEOUT


def alert_operator(headline: str, detail: str = "",
                   *,
                   opener: Optional[Callable] = None,
                   token: Optional[str] = None,
                   chat_id: Optional[str] = None) -> bool:
    """Ping Kyle to come into the chat — 'I need a sword to sharpen against.'
    Returns True if sent, False if no credentials / gate closed (fail-soft: an
    alert that can't send just doesn't, it never blocks the op). `opener` is
    injected in tests."""
    if not authorize_communication(operator_switch()):
        return False
    tok, cid = _resolve_credentials(token, chat_id)
    if not tok or not cid:
        return False
    text = ("🗡️ <b>TITAN needs you</b>\n\n" + str(headline)
            + (("\n\n" + str(detail)) if detail else "")
            + "\n\nCome sharpen swords when you get a sec.")
    if opener is None:
        import urllib.request
        opener = urllib.request.urlopen  # pragma: no cover - network
    try:
        _post_message(tok, cid, text, opener)
        return True
    except TelegramNotifyError:
        return False
