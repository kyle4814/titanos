from __future__ import annotations

import unittest
from types import MappingProxyType

from foundation.execution_intent import ExecutionIntent, ExecutionIntentError


class TestExecutionIntent(unittest.TestCase):
    def make_intent(self, **overrides):
        values = {
            "intent_id": "EI-1",
            "target": "stripe:customer_123",
            "action": "CREATE_PAYMENT_LINK",
            "parameters": {"currency": "AUD", "amount": 1000},
            "evidence_refs": ("OPP-1", "REC-1"),
            "expected_effect": "create one payment link",
            "authority_required": "A3",
            "reversible": True,
            "expires_at": "2026-10-01T00:00:00+00:00",
            "policy_version": "mothership-1",
        }
        values.update(overrides)
        return ExecutionIntent(**values)

    def test_freezes_parameters_and_normalizes_mapping(self):
        intent = self.make_intent(parameters={"b": 2, "a": {"z": 1}})
        self.assertIsInstance(intent.parameters, MappingProxyType)
        with self.assertRaises(TypeError):
            intent.parameters["new"] = "value"

    def test_fingerprint_binds_load_bearing_fields(self):
        first = self.make_intent()
        second = self.make_intent(parameters={"amount": 1000, "currency": "AUD"})
        self.assertEqual(first.fingerprint(), second.fingerprint())
        changed = self.make_intent(action="REFUND_PAYMENT")
        self.assertNotEqual(first.fingerprint(), changed.fingerprint())

    def test_requires_evidence(self):
        with self.assertRaises(ExecutionIntentError):
            self.make_intent(evidence_refs=())

    def test_rejects_empty_required_fields(self):
        with self.assertRaises(ExecutionIntentError):
            self.make_intent(target="")

    def test_rejects_invalid_expiry(self):
        with self.assertRaises(ExecutionIntentError):
            self.make_intent(expires_at="tomorrow")

    def test_to_dict_contains_binding_fingerprint(self):
        intent = self.make_intent()
        rendered = intent.to_dict()
        self.assertEqual(rendered["fingerprint"], intent.fingerprint())
        self.assertEqual(rendered["parameters"]["amount"], 1000)


if __name__ == "__main__":
    unittest.main()
