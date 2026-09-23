from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from foundation.execution_adapter import AdapterResult
from foundation.execution_dispatcher import AdapterDispatchError, AdapterDispatcher
from foundation.execution_intent import ExecutionIntent
from foundation.execution_receipt_store import ExecutionReceiptStore


class Adapter:
    def __init__(self, name, prefix, effect="ok"):
        self.name = name
        self.prefix = prefix
        self.effect = effect

    def supports(self, intent):
        return intent.target.startswith(self.prefix)

    def execute(self, intent):
        return AdapterResult("EXECUTED", self.effect, True, (f"{self.name}:receipt",))


class TestExecutionDispatcher(unittest.TestCase):
    def intent(self, target="stripe:customer_123"):
        return ExecutionIntent(
            intent_id="EI-DISPATCH-1",
            target=target,
            action="CREATE_PAYMENT_LINK",
            parameters={"amount": 1000, "currency": "AUD"},
            evidence_refs=("OPP-1",),
            expected_effect="create one payment link",
            authority_required="A3",
            reversible=True,
            expires_at="2099-01-01T00:00:00+00:00",
            policy_version="mothership-1",
        )

    def test_selects_exactly_one_adapter(self):
        adapter = Adapter("stripe", "stripe:")
        dispatcher = AdapterDispatcher.from_adapters([adapter])
        self.assertIs(dispatcher.select(self.intent()), adapter)

    def test_rejects_unsupported_intent(self):
        dispatcher = AdapterDispatcher.from_adapters([Adapter("stripe", "stripe:")])
        with self.assertRaisesRegex(AdapterDispatchError, "no execution adapter"):
            dispatcher.select(self.intent("github:repo"))

    def test_rejects_ambiguous_routing(self):
        dispatcher = AdapterDispatcher.from_adapters([
            Adapter("stripe-a", "stripe:"),
            Adapter("stripe-b", "stripe:"),
        ])
        with self.assertRaisesRegex(AdapterDispatchError, "ambiguous"):
            dispatcher.select(self.intent())

    def test_approved_execution_persists_adapter_result_as_receipt(self):
        intent = self.intent()
        adapter = Adapter("stripe", "stripe:", "payment link created")
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            receipt = AdapterDispatcher.from_adapters([adapter]).execute_approved_with_receipt(
                intent, intent.fingerprint(), store
            )
            self.assertEqual(receipt.receipt_id, f"exec:{intent.fingerprint()}")
            self.assertEqual(receipt.status, "EXECUTED")
            self.assertTrue(receipt.executed)
            self.assertEqual(receipt.evidence, "stripe:receipt")
            self.assertEqual(store.get(receipt.receipt_id), receipt)

    def test_existing_receipt_prevents_adapter_reexecution(self):
        intent = self.intent()
        calls = []
        adapter = Adapter("stripe", "stripe:")
        original_execute = adapter.execute

        def tracked_execute(value):
            calls.append(value.intent_id)
            return original_execute(value)

        adapter.execute = tracked_execute
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            dispatcher = AdapterDispatcher.from_adapters([adapter])
            first = dispatcher.execute_approved_with_receipt(
                intent, intent.fingerprint(), store
            )
            second = dispatcher.execute_approved_with_receipt(
                intent, intent.fingerprint(), store
            )
            self.assertEqual(first, second)
            self.assertEqual(calls, [intent.intent_id])

    def test_approved_execution_rejects_wrong_fingerprint_before_adapter(self):
        intent = self.intent()
        calls = []
        adapter = Adapter("stripe", "stripe:")
        original_execute = adapter.execute

        def tracked_execute(value):
            calls.append(value.intent_id)
            return original_execute(value)

        adapter.execute = tracked_execute
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            with self.assertRaisesRegex(Exception, "does not match"):
                AdapterDispatcher.from_adapters([adapter]).execute_approved_with_receipt(
                    intent, "WRONG", store
                )
            self.assertEqual(calls, [])

    def test_concurrent_same_approval_persists_one_receipt_and_executes_once(self):
        class CountingAdapter(Adapter):
            def __init__(self):
                super().__init__("stripe", "stripe:")
                self.calls = 0
                self.lock = threading.Lock()

            def execute(self, intent):
                with self.lock:
                    self.calls += 1
                return super().execute(intent)

        adapter = CountingAdapter()
        dispatcher = AdapterDispatcher.from_adapters([adapter])
        intent = self.intent()
        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            results = []
            errors = []

            def worker():
                try:
                    results.append(
                        dispatcher.execute_approved_with_receipt(
                            intent, intent.fingerprint(), store
                        )
                    )
                except Exception as exc:
                    errors.append(exc)

            threads = [threading.Thread(target=worker) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            self.assertFalse(errors)
            self.assertEqual(len(results), 8)
            self.assertEqual(adapter.calls, 1)
            self.assertEqual(len(store.load()), 1)
            self.assertTrue(all(result == results[0] for result in results))

    def test_adapter_exception_becomes_unknown_not_success(self):
        class ExplodingAdapter(Adapter):
            def execute(self, intent):
                raise RuntimeError("network response lost")

        result = AdapterDispatcher.from_adapters(
            [ExplodingAdapter("stripe", "stripe:")]
        ).execute(self.intent())
        self.assertEqual(result.status, "UNKNOWN")
        self.assertFalse(result.executed)

    def test_unknown_or_timeout_cannot_claim_executed(self):
        class BadAdapter(Adapter):
            def __init__(self, status):
                super().__init__("stripe", "stripe:")
                self.status = status

            def execute(self, intent):
                return AdapterResult(self.status, "ambiguous", True)

        for status in ("UNKNOWN", "TIMEOUT"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(AdapterDispatchError, "executed=True"):
                    AdapterDispatcher.from_adapters(
                        [BadAdapter(status)]
                    ).execute(self.intent())

    def test_unknown_adapter_outcome_is_persisted(self):
        class ExplodingAdapter(Adapter):
            def execute(self, intent):
                raise TimeoutError("gateway timeout")

        with tempfile.TemporaryDirectory() as tmp:
            store = ExecutionReceiptStore(Path(tmp) / "receipts.json")
            receipt = AdapterDispatcher.from_adapters(
                [ExplodingAdapter("stripe", "stripe:")]
            ).execute_approved_with_receipt(
                self.intent(), self.intent().fingerprint(), store
            )
            self.assertEqual(receipt.status, "UNKNOWN")
            self.assertFalse(receipt.executed)
            self.assertIn("TimeoutError", receipt.evidence)

    def test_dispatch_executes_selected_adapter(self):
        adapter = Adapter("stripe", "stripe:", "payment link created")
        result = AdapterDispatcher.from_adapters([adapter]).execute(self.intent())
        self.assertEqual(result.effect, "payment link created")
        self.assertTrue(result.executed)


if __name__ == "__main__":
    unittest.main()
