"""Tests for `foundation/telegram_notify.py`.

Offline throughout — the real network opener is always injected. These
pin the two locks (authorization + credentials), the fail-open/fail-closed
split, and the one rule that matters most: the bot token never leaks into
a file, a log, or an exception.
"""

import io
import json
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from foundation.communication_gate import CommunicationDenied
from foundation.telegram_notify import (
    SendResult,
    TelegramNotifyError,
    operator_switch,
    send_card,
    send_messages,
)
import urllib.parse as _urlparse
from foundation import communication_gate


NOW = datetime(2026, 9, 4, 6, 0, tzinfo=timezone.utc)
TOKEN = "123456:FAKE-not-a-real-token"
CHAT = "999"


class _FakeResp:
    def __init__(self, ok=True, description=""):
        body = {"ok": ok}
        if description:
            body["description"] = description
        self._raw = json.dumps(body).encode("utf-8")
    def read(self):
        return self._raw


class _RecordingOpener:
    """Captures every Request the sender builds, returns ok responses."""
    def __init__(self, ok=True, description=""):
        self.calls = []
        self._ok, self._desc = ok, description
    def __call__(self, req):
        self.calls.append(req)
        return _FakeResp(ok=self._ok, description=self._desc)


class TestAuthorizationIsRealAndFirst(unittest.TestCase):
    def test_operator_switch_is_authorized(self):
        # The named authorization Kyle actually gave passes the gate.
        self.assertTrue(
            communication_gate.authorize_communication(operator_switch(now=NOW)))

    def test_authorization_checked_before_credentials(self):
        # If the gate ever denies, no send/dry-run happens at all — even
        # with a token present. Patch the gate to deny for this test.
        orig = communication_gate.authorize_communication
        def deny(_switch):
            raise CommunicationDenied("denied for test")
        # send_messages imported the symbol directly; patch there.
        import foundation.telegram_notify as tn
        tn.authorize_communication = deny
        try:
            with self.assertRaises(CommunicationDenied):
                send_messages(("hi",), token=TOKEN, chat_id=CHAT,
                              opener=_RecordingOpener(), now=NOW)
        finally:
            tn.authorize_communication = orig


class TestDryRunWhenNoCredentials(unittest.TestCase):
    def test_no_token_writes_a_file_and_does_not_call_the_network(self):
        opener = _RecordingOpener()
        with TemporaryDirectory() as d:
            res = send_messages(("card one", "card two"), token=None,
                                chat_id=None, dry_run_dir=Path(d),
                                opener=opener, now=NOW)
            self.assertEqual(res.mode, "DRY_RUN")
            self.assertEqual(res.total, 2)
            self.assertEqual(opener.calls, [])  # network never touched
            self.assertTrue(Path(res.dry_run_path).exists())

    def test_dry_run_file_contains_the_messages(self):
        with TemporaryDirectory() as d:
            res = send_messages(("ALPHA_CARD", "BETA_CARD"),
                                dry_run_dir=Path(d), now=NOW)
            text = Path(res.dry_run_path).read_text(encoding="utf-8")
        self.assertIn("ALPHA_CARD", text)
        self.assertIn("BETA_CARD", text)


class TestSendPath(unittest.TestCase):
    def test_all_messages_are_posted(self):
        opener = _RecordingOpener(ok=True)
        res = send_messages(("a", "b", "c"), token=TOKEN, chat_id=CHAT,
                            opener=opener, now=NOW)
        self.assertEqual(res.mode, "SENT")
        self.assertEqual(res.delivered, 3)
        self.assertEqual(len(opener.calls), 3)

    def test_a_rejected_message_is_recorded_not_swallowed(self):
        opener = _RecordingOpener(ok=False, description="chat not found")
        res = send_messages(("a",), token=TOKEN, chat_id=CHAT,
                            opener=opener, now=NOW)
        self.assertEqual(res.delivered, 0)
        self.assertTrue(res.errors)
        self.assertIn("chat not found", res.errors[0])

    def test_an_oversized_message_raises(self):
        opener = _RecordingOpener()
        res = send_messages(("A" * 5000,), token=TOKEN, chat_id=CHAT,
                            opener=opener, now=NOW)
        # captured as a per-message error, not a crash of the whole batch
        self.assertEqual(res.delivered, 0)
        self.assertTrue(any("4096" in e for e in res.errors))


class TestSecretsFileAndAliases(unittest.TestCase):
    def test_dm_id_alias_resolves_as_chat_id(self):
        import foundation.telegram_notify as tn
        with mock.patch.dict("os.environ",
                             {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_DM_ID": "42"},
                             clear=True):
            tok, chat = tn._resolve_credentials(None, None)
        self.assertEqual(tok, "t")
        self.assertEqual(chat, "42")

    def test_read_secrets_file_is_pure_and_telegram_only(self):
        import foundation.telegram_notify as tn
        with TemporaryDirectory() as d:
            f = Path(d) / ".titanos_env"
            f.write_text("export TELEGRAM_BOT_TOKEN='filetok'\n"
                         "TELEGRAM_DM_ID=\"99\"\n"
                         "CLOUDFLARE_SECRET=should_not_load\n"
                         "# comment\n", encoding="utf-8")
            secrets = tn._read_secrets_file(str(f))
        self.assertEqual(secrets.get("TELEGRAM_BOT_TOKEN"), "filetok")
        self.assertEqual(secrets.get("TELEGRAM_DM_ID"), "99")
        # non-Telegram secrets are NOT read, and os.environ is untouched
        self.assertNotIn("CLOUDFLARE_SECRET", secrets)

    def test_missing_secrets_file_returns_empty(self):
        import foundation.telegram_notify as tn
        self.assertEqual(tn._read_secrets_file("/no/such/file"), {})

    def test_app_resolver_prefers_env_then_file_no_mutation(self):
        import os
        import foundation.telegram_notify as tn
        with TemporaryDirectory() as d:
            f = Path(d) / ".titanos_env"
            f.write_text("TELEGRAM_BOT_TOKEN=filetok\nTELEGRAM_DM_ID=77\n",
                         encoding="utf-8")
            # env empty -> falls back to the file, WITHOUT mutating os.environ
            with mock.patch.dict("os.environ", {}, clear=True), \
                 mock.patch.object(tn, "SECRETS_FILE", str(f)):
                tok, chat = tn.resolve_operator_credentials()
                self.assertEqual((tok, chat), ("filetok", "77"))
                self.assertIsNone(os.environ.get("TELEGRAM_BOT_TOKEN"))  # untouched
            # env present -> env wins, file not needed
            with mock.patch.dict("os.environ",
                                 {"TELEGRAM_BOT_TOKEN": "envtok",
                                  "TELEGRAM_CHAT_ID": "55"}, clear=True), \
                 mock.patch.object(tn, "SECRETS_FILE", "/no/such/file"):
                self.assertEqual(tn.resolve_operator_credentials(),
                                 ("envtok", "55"))


class TestSendCard(unittest.TestCase):
    def test_card_sends_with_inline_keyboard_through_the_socket(self):
        opener = _RecordingOpener()
        markup = {"inline_keyboard": [[{"text": "✅ Approve",
                                        "callback_data": "approve:x"}]]}
        ok = send_card("decide this", markup, token=TOKEN, chat_id=CHAT,
                       opener=opener, now=NOW)
        self.assertTrue(ok)
        self.assertEqual(len(opener.calls), 1)
        # the reply_markup actually rode along in the POST body
        body = _urlparse.parse_qs(opener.calls[0].data.decode("utf-8"))
        self.assertIn("reply_markup", body)
        self.assertIn("approve:x", body["reply_markup"][0])

    def test_card_without_credentials_returns_false_and_no_network(self):
        opener = _RecordingOpener()
        ok = send_card("x", {"inline_keyboard": []}, token=None, chat_id=None,
                       opener=opener, now=NOW)
        self.assertFalse(ok)
        self.assertEqual(opener.calls, [])


class TestTokenNeverLeaks(unittest.TestCase):
    def test_token_not_in_dry_run_file(self):
        with TemporaryDirectory() as d:
            res = send_messages(("card",), token=None, chat_id=None,
                                dry_run_dir=Path(d), now=NOW)
            text = Path(res.dry_run_path).read_text(encoding="utf-8")
        self.assertNotIn(TOKEN, text)

    def test_token_not_in_api_rejection_error(self):
        opener = _RecordingOpener(ok=False, description="unauthorized")
        res = send_messages(("card",), token=TOKEN, chat_id=CHAT,
                            opener=opener, now=NOW)
        for e in res.errors:
            self.assertNotIn(TOKEN, e)

    def test_token_not_in_send_result_dict(self):
        opener = _RecordingOpener(ok=True)
        res = send_messages(("card",), token=TOKEN, chat_id=CHAT,
                            opener=opener, now=NOW)
        self.assertNotIn(TOKEN, json.dumps(res.to_dict()))


if __name__ == "__main__":
    unittest.main()
