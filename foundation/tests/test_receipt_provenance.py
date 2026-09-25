"""Regression tests for execution-receipt provenance (2026-09-26).

Closes the confirmed hole in `AdapterExecutionGateway.execute_permitted`:
`receipt_store.get(f"exec:{fingerprint}")` used to be trusted as proof of
prior execution merely because a record existed under that key -- planted,
tampered, or legacy-unsigned JSON all passed. These tests prove the fix:
an existing receipt is now trusted only after `ExecutionReceipt.verify()`
succeeds against the gateway's own Ring 0 key, and any failure there raises
`ReceiptIntegrityError` fail-closed -- never silently accepted, never
silently re-executed.
"""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path

from foundation.adapter_execution_gateway import AdapterExecutionGateway
from foundation.approval_envelope import ApprovalEnvelope, ConsumedIds
from foundation.authorization_gate import AuthorizationGate
from foundation.execution_adapter import AdapterResult
from foundation.execution_dispatcher import AdapterDispatcher
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt import ExecutionReceipt, ReceiptIntegrityError
from foundation.execution_receipt_store import ExecutionReceiptStore

KEY = b"k" * 32
OTHER_KEY = b"z" * 32


class CountingAdapter:
    name = "stripe"

    def __init__(self):
        self.calls = 0
        self._lock = threading.Lock()

    def supports(self, intent):
        return intent.target.startswith("stripe:")

    def execute(self, intent):
        with self._lock:
            self.calls += 1
        return AdapterResult(
            status="EXECUTED", effect="payment link created",
            executed=True, evidence=("stripe:receipt:123",),
        )


def _ledger():
    tmp = Path(tempfile.mkdtemp())
    return ConsumedIds(tmp / "consumed.db")


def _intent(intent_id="EI-PROV-1"):
    return ExecutionIntent(
        intent_id=intent_id,
        target="stripe:customer_123",
        action="CREATE_PAYMENT_LINK",
        parameters={"amount": 1000, "currency": "AUD"},
        evidence_refs=("OPP-1",),
        expected_effect="create one payment link",
        authority_required="A3",
        reversible=True,
        expires_at="2099-01-01T00:00:00+00:00",
        policy_version="mothership-1",
    )


def _permit(intent, consumed, *, nonce="n0"):
    env = ApprovalEnvelope.decide(
        proposal_id="p", intent=intent, decision="APPROVE",
        authority="A3", reviewer="kyle", nonce=nonce,
    ).signed(KEY)
    return AuthorizationGate.issue(intent, env, key=KEY, consumed=consumed)


class TestValidReceiptProvenance(unittest.TestCase):
    """1. VALID AUTHENTIC RECEIPT."""

    def test_legitimately_produced_receipt_verifies_and_is_returned(self):
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]), store, KEY, consumed)
            receipt = gateway.execute_permitted(intent, _permit(intent, consumed))
            self.assertTrue(receipt.executed)
            self.assertNotEqual(receipt.mac, "")
            # The exact contract execute_permitted itself relies on.
            receipt.verify(KEY, intent.fingerprint())


class TestPlantedReceipt(unittest.TestCase):
    """2. PLANTED RECEIPT -- an attacker-crafted, unsigned exec:<fingerprint>
    entry must not be accepted as proof of prior execution, and must not
    cause a silent second real-world execution either."""

    def test_planted_unsigned_receipt_is_refused_fail_closed(self):
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.json"
            fingerprint = intent.fingerprint()
            fake = {
                f"exec:{fingerprint}": {
                    "receipt_id": f"exec:{fingerprint}",
                    "intent_id": intent.intent_id,
                    "fingerprint": fingerprint,
                    "target": intent.target,
                    "action": intent.action,
                    "status": "EXECUTED",
                    "executed": True,
                    "recorded_at": "2020-01-01T00:00:00+00:00",
                    "evidence": "planted: nothing really happened",
                    "mac": "",
                }
            }
            path.write_text(json.dumps(fake), encoding="utf-8")
            store = ExecutionReceiptStore(path)
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]), store, KEY, consumed)
            with self.assertRaises(ReceiptIntegrityError):
                gateway.execute_permitted(intent, _permit(intent, consumed))
            # Fail-closed means "refuse", not "quietly execute again" --
            # the adapter must not have been silently invoked by the fix.
            self.assertEqual(adapter.calls, 0)


class TestTamperedReceipt(unittest.TestCase):
    """3. TAMPERED RECEIPT -- a legitimately authenticated receipt, edited
    after persistence, must fail verification."""

    def test_tampered_authenticated_receipt_fails_closed(self):
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.json"
            store = ExecutionReceiptStore(path)
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]), store, KEY, consumed)
            gateway.execute_permitted(intent, _permit(intent, consumed))
            self.assertEqual(adapter.calls, 1)

            raw = json.loads(path.read_text(encoding="utf-8"))
            key = f"exec:{intent.fingerprint()}"
            raw[key]["evidence"] = "tampered: pretend it never happened"
            path.write_text(json.dumps(raw), encoding="utf-8")

            with self.assertRaises(ReceiptIntegrityError):
                gateway.execute_permitted(intent, _permit(intent, consumed, nonce="n1"))
            # Tampering after the real execution must not trigger a second
            # real adapter call either -- it fails closed, not open.
            self.assertEqual(adapter.calls, 1)


class TestWrongFingerprintBinding(unittest.TestCase):
    """4. WRONG FINGERPRINT -- a receipt authenticated for fingerprint A
    cannot satisfy a check for fingerprint B, even though its own MAC is
    perfectly valid for A."""

    def test_receipt_authentic_for_one_fingerprint_rejects_another(self):
        intent_a = _intent("EI-PROV-A")
        intent_b = _intent("EI-PROV-B")
        fp_a, fp_b = intent_a.fingerprint(), intent_b.fingerprint()
        self.assertNotEqual(fp_a, fp_b)
        receipt = ExecutionReceipt(
            receipt_id=f"exec:{fp_a}", intent_id=intent_a.intent_id,
            fingerprint=fp_a, target=intent_a.target, action=intent_a.action,
            status="EXECUTED", executed=True,
            recorded_at="2026-01-01T00:00:00+00:00", evidence="ok",
        ).sign(KEY)
        receipt.verify(KEY, fp_a)  # valid for its own fingerprint
        with self.assertRaises(ReceiptIntegrityError):
            receipt.verify(KEY, fp_b)  # refused for a different one

    def test_gateway_store_itself_refuses_a_relabeled_receipt(self):
        # Belt-and-suspenders: even before reaching ExecutionReceipt.verify,
        # ExecutionReceiptStore's own key/id binding check refuses a receipt
        # authenticated for A that is filed under B's key.
        consumed = _ledger()
        intent_a = _intent("EI-PROV-A2")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.json"
            fp_a = intent_a.fingerprint()
            receipt = ExecutionReceipt(
                receipt_id=f"exec:{fp_a}", intent_id=intent_a.intent_id,
                fingerprint=fp_a, target=intent_a.target, action=intent_a.action,
                status="EXECUTED", executed=True,
                recorded_at="2026-01-01T00:00:00+00:00", evidence="ok",
            ).sign(KEY)
            path.write_text(
                json.dumps({"exec:RELABELED": receipt.to_dict()}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "key/id mismatch"):
                ExecutionReceiptStore(path).load()


def _signed(intent, **overrides):
    fields = dict(
        receipt_id=f"exec:{intent.fingerprint()}", intent_id=intent.intent_id,
        fingerprint=intent.fingerprint(), target=intent.target, action=intent.action,
        status="EXECUTED", executed=True,
        recorded_at="2026-01-01T00:00:00+00:00", evidence="ok",
    )
    fields.update(overrides)
    return ExecutionReceipt(**fields).sign(KEY)


class TestReceiptIdBinding(unittest.TestCase):
    """RECEIPT-ID MISMATCH -- a receipt whose MAC is valid over its own
    fields but whose receipt_id is not `exec:<its fingerprint>` is refused
    by verify() independently of the MAC (and by the store, independently
    of verify())."""

    def test_valid_mac_with_wrong_receipt_id_is_refused_by_verify(self):
        intent = _intent()
        receipt = _signed(intent, receipt_id="exec:SOMETHING_ELSE")
        # The MAC genuinely covers this (wrong) receipt_id, so the MAC check
        # alone would pass; the explicit binding check must still refuse.
        with self.assertRaisesRegex(ReceiptIntegrityError, "id/fingerprint binding"):
            receipt.verify(KEY, intent.fingerprint())

    def test_store_refuses_the_same_receipt_on_record(self):
        intent = _intent()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                store.record(_signed(intent, receipt_id="exec:SOMETHING_ELSE"))


class TestEveryFieldIsBound(unittest.TestCase):
    """MAC TAMPERING per field -- status, evidence, target, action, executed,
    intent_id, recorded_at: changing any one after signing breaks
    verification. Exercised in-memory (replace) so each field is isolated."""

    def _assert_tamper_detected(self, **change):
        intent = _intent()
        good = _signed(intent)
        good.verify(KEY, intent.fingerprint())
        bad = replace(good, **change)
        with self.assertRaises(ReceiptIntegrityError):
            bad.verify(KEY, intent.fingerprint())

    def test_status(self):
        self._assert_tamper_detected(status="FAILED")

    def test_executed_flag(self):
        self._assert_tamper_detected(executed=False)

    def test_evidence(self):
        self._assert_tamper_detected(evidence="stripe:receipt:FORGED")

    def test_target(self):
        self._assert_tamper_detected(target="stripe:customer_999")

    def test_action(self):
        self._assert_tamper_detected(action="REFUND")

    def test_intent_id(self):
        self._assert_tamper_detected(intent_id="EI-OTHER")

    def test_recorded_at(self):
        self._assert_tamper_detected(recorded_at="2030-01-01T00:00:00+00:00")

    def test_status_tampered_on_disk_is_refused_by_gateway(self):
        # Same property through the real path: a persisted, authentic
        # receipt whose status is edited on disk must not be returned.
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.json"
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]),
                ExecutionReceiptStore(path), KEY, consumed)
            gateway.execute_permitted(intent, _permit(intent, consumed, nonce="s0"))
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw[f"exec:{intent.fingerprint()}"]["status"] = "FAILED"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(ReceiptIntegrityError):
                gateway.execute_permitted(intent, _permit(intent, consumed, nonce="s1"))
            self.assertEqual(adapter.calls, 1)


class TestBadSignature(unittest.TestCase):
    """5. BAD SIGNATURE/MAC -- invalid provenance cannot be accepted."""

    def test_flipped_mac_character_is_rejected(self):
        intent = _intent()
        receipt = ExecutionReceipt(
            receipt_id=f"exec:{intent.fingerprint()}", intent_id=intent.intent_id,
            fingerprint=intent.fingerprint(), target=intent.target, action=intent.action,
            status="EXECUTED", executed=True,
            recorded_at="2026-01-01T00:00:00+00:00", evidence="ok",
        ).sign(KEY)
        flipped_char = "0" if receipt.mac[0] != "0" else "1"
        corrupted = replace(receipt, mac=flipped_char + receipt.mac[1:])
        with self.assertRaises(ReceiptIntegrityError):
            corrupted.verify(KEY, intent.fingerprint())

    def test_random_mac_string_is_rejected(self):
        intent = _intent()
        receipt = ExecutionReceipt(
            receipt_id=f"exec:{intent.fingerprint()}", intent_id=intent.intent_id,
            fingerprint=intent.fingerprint(), target=intent.target, action=intent.action,
            status="EXECUTED", executed=True,
            recorded_at="2026-01-01T00:00:00+00:00", evidence="ok",
            mac="deadbeef" * 8,
        )
        with self.assertRaises(ReceiptIntegrityError):
            receipt.verify(KEY, intent.fingerprint())


class TestLegacyUnauthenticatedReceipt(unittest.TestCase):
    """6. LEGACY/UNAUTHENTICATED RECEIPT -- a receipt with no provenance
    (mac="", the shape every receipt had before this fix, and the shape the
    still-unmodified legacy dry-run/dispatcher paths still produce) must not
    be silently trusted by the gateway."""

    def test_unsigned_legacy_shaped_receipt_fails_verify(self):
        intent = _intent()
        receipt = ExecutionReceipt(
            receipt_id=f"exec:{intent.fingerprint()}", intent_id=intent.intent_id,
            fingerprint=intent.fingerprint(), target=intent.target, action=intent.action,
            status="EXECUTED", executed=True,
            recorded_at="2026-01-01T00:00:00+00:00", evidence="ok",
        )  # mac left at its default: ""
        self.assertEqual(receipt.mac, "")
        with self.assertRaises(ReceiptIntegrityError):
            receipt.verify(KEY, intent.fingerprint())

    def test_gateway_refuses_a_legacy_unsigned_receipt_already_on_disk(self):
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            legacy = ExecutionReceipt(
                receipt_id=f"exec:{intent.fingerprint()}", intent_id=intent.intent_id,
                fingerprint=intent.fingerprint(), target=intent.target, action=intent.action,
                status="EXECUTED", executed=True,
                recorded_at="2020-01-01T00:00:00+00:00", evidence="pre-fix receipt",
            )
            store.record(legacy)
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]), store, KEY, consumed)
            with self.assertRaises(ReceiptIntegrityError):
                gateway.execute_permitted(intent, _permit(intent, consumed))
            self.assertEqual(adapter.calls, 0)


class TestSingleUsePermit(unittest.TestCase):
    """7. SINGLE-USE PERMIT -- existing permit-consumption guarantees are
    unaffected by the provenance fix."""

    def test_same_permit_cannot_be_replayed(self):
        from foundation.authorization_gate import ApprovalReplayed

        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]), store, KEY, consumed)
            permit = _permit(intent, consumed)
            gateway.execute_permitted(intent, permit)
            with self.assertRaises(ApprovalReplayed):
                gateway.execute_permitted(intent, permit)
            self.assertEqual(adapter.calls, 1)


class TestConcurrency(unittest.TestCase):
    """8. CONCURRENCY -- concurrent legitimate calls for the same fingerprint
    (via distinct, individually valid permits) must produce exactly one
    domain execution; the rest resolve through the authenticated-receipt
    idempotency path with zero unexpected lock/collision errors."""

    def test_concurrent_distinct_valid_permits_execute_the_adapter_once(self):
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]), store, KEY, consumed)
            permits = [_permit(intent, consumed, nonce=f"c{i}") for i in range(8)]
            results, errors = [], []

            def worker(permit):
                try:
                    results.append(gateway.execute_permitted(intent, permit))
                except Exception as exc:  # noqa: BLE001 -- collecting, not swallowing
                    errors.append(exc)

            threads = [threading.Thread(target=worker, args=(p,)) for p in permits]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(errors, [])
            self.assertEqual(len(results), 8)
            self.assertEqual(adapter.calls, 1)
            self.assertEqual(len(store.load()), 1)
            self.assertTrue(all(r == results[0] for r in results))


class TestColdRestart(unittest.TestCase):
    """9. COLD RESTART -- a legitimately persisted authenticated receipt
    survives a fresh store/gateway instantiation (simulating process
    restart) and remains verifiable, without re-executing the adapter."""

    def test_authenticated_receipt_survives_reload(self):
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.json"
            gateway_1 = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]),
                ExecutionReceiptStore(path), KEY, consumed)
            first = gateway_1.execute_permitted(intent, _permit(intent, consumed, nonce="r0"))

            # Fresh store + fresh gateway object over the same file and
            # ledger, same adapter instance so a re-execution would be
            # observable.
            gateway_2 = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]),
                ExecutionReceiptStore(path), KEY, consumed)
            second = gateway_2.execute_permitted(intent, _permit(intent, consumed, nonce="r1"))

            self.assertEqual(first, second)
            self.assertEqual(adapter.calls, 1)
            second.verify(KEY, intent.fingerprint())


class TestFailClosedOnKeyMismatch(unittest.TestCase):
    """10. FAIL-CLOSED SECRET -- a receipt authenticated under any key other
    than the gateway's real key (e.g. a wrong/dev secret) must not verify."""

    def test_receipt_signed_under_a_different_key_does_not_verify(self):
        intent = _intent()
        receipt = ExecutionReceipt(
            receipt_id=f"exec:{intent.fingerprint()}", intent_id=intent.intent_id,
            fingerprint=intent.fingerprint(), target=intent.target, action=intent.action,
            status="EXECUTED", executed=True,
            recorded_at="2026-01-01T00:00:00+00:00", evidence="ok",
        ).sign(OTHER_KEY)
        with self.assertRaises(ReceiptIntegrityError):
            receipt.verify(KEY, intent.fingerprint())

    def test_gateway_with_real_key_refuses_receipt_planted_under_wrong_key(self):
        consumed = _ledger()
        intent = _intent()
        adapter = CountingAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "receipts.json"
            store = ExecutionReceiptStore(path)
            forged = ExecutionReceipt(
                receipt_id=f"exec:{intent.fingerprint()}", intent_id=intent.intent_id,
                fingerprint=intent.fingerprint(), target=intent.target, action=intent.action,
                status="EXECUTED", executed=True,
                recorded_at="2020-01-01T00:00:00+00:00", evidence="signed by an impostor key",
            ).sign(OTHER_KEY)
            store.record(forged)
            gateway = AdapterExecutionGateway(
                AdapterDispatcher.from_adapters([adapter]), store, KEY, consumed)
            with self.assertRaises(ReceiptIntegrityError):
                gateway.execute_permitted(intent, _permit(intent, consumed))
            self.assertEqual(adapter.calls, 0)


if __name__ == "__main__":
    unittest.main()
