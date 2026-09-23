from __future__ import annotations

import unittest

from foundation.execution_adapter import AdapterResult
from foundation.execution_dispatcher import AdapterDispatchError, AdapterDispatcher
from foundation.execution_intent import ExecutionIntent


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

    def test_dispatch_executes_selected_adapter(self):
        adapter = Adapter("stripe", "stripe:", "payment link created")
        result = AdapterDispatcher.from_adapters([adapter]).execute(self.intent())
        self.assertEqual(result.effect, "payment link created")
        self.assertTrue(result.executed)


if __name__ == "__main__":
    unittest.main()
