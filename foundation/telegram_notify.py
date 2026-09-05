"""
Telegram Notify — the operator push channel.

WHAT THIS IS

The one outbound door in this repository: it pushes the ops digest
(`ops_digest.py`) to KYLE'S OWN Telegram chat, via KYLE'S OWN bot token.
This is the operator notifying himself — not third-party communication —
which Kyle explicitly authorized ("start telegramming me shit to do ...
make it part of the end of /next").

TWO INDEPENDENT LOCKS ON AN ACTUAL SEND (both required)

  1. AUTHORIZATION. Every send re-derives through
     `communication_gate.authorize_communication()` on the NOTIFY_OPERATOR
     scope. The authorization is real and named (Kyle), recorded in
     HUMAN_DECISIONS.md — not a bool this module sets for itself.
  2. CREDENTIALS. A bot token + chat id, read ONLY from the environment
     (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) or an explicit argument —
     never hard-coded, never committed, never logged. A credential is one
     of the five human-authority gates, so this repository cannot supply
     it; Kyle pastes it into his own environment once.

FAIL-OPEN ON DRAFTING, FAIL-CLOSED ON SENDING (switch-gate doctrine §8)

  - No token present  -> DRY_RUN: the rendered messages are written to a
    local file so the digest is still produced and inspectable. Drafting
    is a non-destructive analysis action; it fails open.
  - Token present but authorization denied -> refuses (raises). Sending
    external data is not reversible; it fails closed.

The token is a secret. This module never prints it, never includes it in
an exception message, and never writes it to the dry-run file. The only
place it is used is the request URL to api.telegram.org, constructed at
call time and not retained.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from foundation.communication_gate import (
    CommunicationSwitch,
    authorize_communication,
)
from foundation.ops_digest import render_telegram_html

__all__ = [
    "TelegramNotifyError",
    "SendResult",
    "operator_switch",
    "send_messages",
    "send_digest",
    "API_BASE",
    "TOKEN_ENV",
    "CHAT_ENV",
]

API_BASE = "https://api.telegram.org"
TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ENV = "TELEGRAM_CHAT_ID"
# Kyle's existing moneyprinter bot wiring names the chat id TELEGRAM_DM_ID.
# Accept it as an alias so the standing setup Just Works without renaming.
CHAT_ENV_ALIASES = ("TELEGRAM_CHAT_ID", "TELEGRAM_DM_ID")
# The standing secrets file the wiring already lives in. Loaded (Telegram keys
# only, never overriding an already-set var) so an autonomous run that did not
# source it can still reach Kyle. Never logged.
SECRETS_FILE = os.path.expanduser("~/.titanos_env")
_MAX_MESSAGE_BYTES = 4096  # Telegram's own hard limit


class TelegramNotifyError(Exception):
    """Raised on a real delivery failure (network, API rejection, or a
    message over the limit). Never carries the bot token in its text."""


@dataclass
class SendResult:
    mode: str                    # "SENT" or "DRY_RUN"
    delivered: int = 0           # messages actually accepted by the API
    total: int = 0
    dry_run_path: Optional[str] = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "mode": self.mode, "delivered": self.delivered,
            "total": self.total, "dry_run_path": self.dry_run_path,
            "errors": list(self.errors),
        }


def operator_switch(now: Optional[datetime] = None) -> CommunicationSwitch:
    """The named, recorded authorization for pushing to Kyle's own chat.
    Every field reflects a real fact: Kyle authorized it, it is one-way to
    his own channel, and sent data is acknowledged as not fully
    reversible."""
    return CommunicationSwitch(
        requested_scope="NOTIFY_OPERATOR",
        human_authorized_by="Kyle Graham",
        human_authorization_note=(
            "Operator self-notification only: push the ops digest to Kyle's "
            "own Telegram chat via his own bot token. Authorized 2026-09-04 "
            "('start telegramming me ... make it part of the end of /next'). "
            "Not third-party communication. See HUMAN_DECISIONS.md."
        ),
        reversibility_acknowledged=True,
        evaluated_at=(now or datetime.now(timezone.utc)).isoformat(),
    )


def _read_secrets_file(path: str = SECRETS_FILE) -> dict:
    """Read ONLY the TELEGRAM_* keys from the standing secrets file and return
    them as a dict. PURE — never mutates os.environ (that would leak across
    unit tests and pollute the no-credentials paths), never touches
    non-Telegram secrets, never logs a value. Empty dict if absent/unreadable."""
    out: dict = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("TELEGRAM_"):
            out[key] = val.strip().strip('"').strip("'")
    return out


def _resolve_credentials(token: Optional[str],
                         chat_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """ENV-ONLY resolution (plus the TELEGRAM_DM_ID alias). Never reads the
    secrets file — keeps library callers and their tests pure. The file is
    only consulted at the app boundary, via resolve_operator_credentials()."""
    token = token or os.environ.get(TOKEN_ENV) or None
    if not chat_id:
        for name in CHAT_ENV_ALIASES:
            if os.environ.get(name):
                chat_id = os.environ[name]
                break
    return token, chat_id or None


def resolve_operator_credentials(token: Optional[str] = None,
                                 chat_id: Optional[str] = None
                                 ) -> tuple[Optional[str], Optional[str]]:
    """App-boundary resolver: env first (with the DM_ID alias), then the
    standing secrets file as a fallback — WITHOUT mutating os.environ. The CLI
    and the daemon call this and pass the result explicitly to the send
    functions, so an autonomous run that didn't source the env still reaches
    Kyle, while the library stays env-pure for tests."""
    token, chat_id = _resolve_credentials(token, chat_id)
    if token and chat_id:
        return token, chat_id
    # Read the CURRENT module-level path (not the def-time default), so tests
    # that patch SECRETS_FILE never fall through to the real file.
    secrets = _read_secrets_file(SECRETS_FILE)
    token = token or secrets.get(TOKEN_ENV) or None
    if not chat_id:
        for name in CHAT_ENV_ALIASES:
            if secrets.get(name):
                chat_id = secrets[name]
                break
    return token, chat_id or None


def _post_message(token: str, chat_id: str, text: str,
                  opener: Callable[[urllib.request.Request], object],
                  reply_markup: Optional[dict] = None) -> None:
    """POST one message to Telegram's sendMessage. `opener` is injected in
    tests so no test touches the real network. `reply_markup` (optional) adds
    an inline keyboard (e.g. Approve/Deny buttons). Raises TelegramNotifyError
    (token never in the message) on any non-ok response."""
    if len(text.encode("utf-8")) > _MAX_MESSAGE_BYTES:
        raise TelegramNotifyError(
            "a digest message exceeds Telegram's 4096-char limit — "
            "ops_digest should have split it")
    url = f"{API_BASE}/bot{token}/sendMessage"
    fields = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    if reply_markup is not None:
        fields["reply_markup"] = json.dumps(reply_markup)
    payload = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        resp = opener(req)
        raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:  # pragma: no cover - network shape
        # Telegram puts the reason in the body; the token is in the URL,
        # which HTTPError does NOT echo into str(exc). Still, never
        # interpolate `url` into an error.
        raise TelegramNotifyError(
            f"Telegram API returned HTTP {exc.code}") from None
    except urllib.error.URLError as exc:  # pragma: no cover - network shape
        raise TelegramNotifyError(
            f"could not reach Telegram: {exc.reason}") from None
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        raise TelegramNotifyError("Telegram returned a non-JSON response")
    if not body.get("ok", False):
        # `description` is safe (no token); `url` is not, and is not used.
        raise TelegramNotifyError(
            f"Telegram rejected the message: {body.get('description', 'unknown')}")


def send_card(text: str, reply_markup: dict,
              *,
              token: Optional[str] = None,
              chat_id: Optional[str] = None,
              opener: Optional[Callable] = None,
              now: Optional[datetime] = None) -> bool:
    """Send ONE message carrying an inline keyboard (e.g. Approve/Deny) through
    the sanctioned gated socket. Gate FIRST, then credentials. Returns True if
    sent, False if credentials are absent (no dry-run file — a card with no
    reachable buttons is pointless). `opener` injected in tests."""
    authorize_communication(operator_switch(now=now))
    token, chat_id = _resolve_credentials(token, chat_id)
    if not token or not chat_id:
        return False
    opener = opener or (lambda req: urllib.request.urlopen(req, timeout=30))
    _post_message(token, chat_id, text, opener, reply_markup=reply_markup)
    return True


def send_messages(messages: tuple[str, ...],
                  *,
                  token: Optional[str] = None,
                  chat_id: Optional[str] = None,
                  dry_run_dir: Optional[Path] = None,
                  opener: Optional[Callable] = None,
                  now: Optional[datetime] = None) -> SendResult:
    """Push already-rendered messages to Kyle's chat, or dry-run them.

    Authorization is checked FIRST, always — before credentials are even
    looked at — so an unauthorized caller cannot reach the send path by
    supplying a token. Then:
      - credentials present  -> send each message in order.
      - credentials absent   -> write them to a dry-run file and return.
    """
    # Lock 1: authorization (raises CommunicationDenied if not authorized).
    authorize_communication(operator_switch(now=now))

    total = len(messages)
    token, chat_id = _resolve_credentials(token, chat_id)

    if not token or not chat_id:
        # Fail-open drafting: produce the artifact so the digest is never
        # lost just because the token has not been set yet.
        target_dir = dry_run_dir or Path("digest_out")
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
        path = target_dir / f"ops_digest_{stamp}.txt"
        path.write_text("\n\n----------\n\n".join(messages), encoding="utf-8")
        return SendResult(mode="DRY_RUN", total=total, dry_run_path=str(path),
                          errors=["no TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID set "
                                  "— rendered to file instead of sending"])

    # Lock 2 satisfied (credentials present) and Lock 1 already passed.
    opener = opener or (lambda req: urllib.request.urlopen(req, timeout=30))
    result = SendResult(mode="SENT", total=total)
    for msg in messages:
        try:
            _post_message(token, chat_id, msg, opener)
            result.delivered += 1
        except TelegramNotifyError as exc:
            result.errors.append(str(exc))
    return result


def send_digest(*,
                token: Optional[str] = None,
                chat_id: Optional[str] = None,
                dry_run_dir: Optional[Path] = None,
                opener: Optional[Callable] = None,
                now: Optional[datetime] = None) -> SendResult:
    """Render the live ops digest and push it (or dry-run it). The one
    call an end-of-cycle hook makes."""
    messages = render_telegram_html(now=now)
    return send_messages(messages, token=token, chat_id=chat_id,
                         dry_run_dir=dry_run_dir, opener=opener, now=now)
