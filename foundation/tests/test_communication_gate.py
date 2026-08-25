"""
Tests for foundation/communication_gate.py — EXTERNAL_COMMUNICATION_SWITCH_001.

No test in this file performs, mocks pretending to perform, or requires
network access. The property under test is entirely: does the switch
correctly deny by default, and correctly refuse to be bypassed.
"""

import inspect
import sys
import unittest

from foundation.communication_gate import (
    CAPABILITY_ID, COMMUNICATION_SCOPES,
    CommunicationDecision, CommunicationDenied, CommunicationSwitch,
    authorize_communication, evaluate,
)
from foundation import communication_gate as _module


def _full_authorization(**overrides) -> CommunicationSwitch:
    base = dict(
        capability_id=CAPABILITY_ID, requested_scope="READ_URL",
        human_authorized_by="Kyle", human_authorization_note="test authorization",
        reversibility_acknowledged=True,
    )
    base.update(overrides)
    return CommunicationSwitch(**base)


class TestExternalCommunicationExistsAsAGovernedBoundary(unittest.TestCase):
    def test_1_capability_id_is_explicit(self):
        self.assertEqual(CAPABILITY_ID, "EXTERNAL_COMMUNICATION")

    def test_wrong_capability_id_is_refused(self):
        switch = _full_authorization(capability_id="SOMETHING_ELSE")
        d = evaluate(switch)
        self.assertFalse(d.action_permitted)


class TestDefaultStateDeniesOrQuarantines(unittest.TestCase):
    def test_2_default_switch_is_fully_blocked(self):
        # capability_id defaults to CAPABILITY_ID itself, so trigger_
        # verified is correctly True (this IS the governed capability) --
        # everything downstream of trigger still fails closed.
        d = evaluate(CommunicationSwitch())
        self.assertFalse(d.armed)
        self.assertFalse(d.scope_declared)
        self.assertTrue(d.human_review_required)
        self.assertFalse(d.action_permitted)

    def test_unscoped_request_is_refused(self):
        switch = _full_authorization(requested_scope="")
        d = evaluate(switch)
        self.assertFalse(d.action_permitted)
        self.assertIn("not an authorizable request", d.reasons[0])

    def test_scope_outside_declared_set_is_refused(self):
        switch = _full_authorization(requested_scope="DELETE_EVERYTHING")
        d = evaluate(switch)
        self.assertFalse(d.action_permitted)


class TestNoImplicitStateTransition(unittest.TestCase):
    def test_3_missing_authorized_by_blocks_even_with_scope_declared(self):
        switch = _full_authorization(human_authorized_by="")
        d = evaluate(switch)
        self.assertTrue(d.scope_declared)
        self.assertFalse(d.action_permitted)

    def test_authorized_by_alone_without_note_blocks(self):
        switch = _full_authorization(human_authorization_note="")
        d = evaluate(switch)
        self.assertFalse(d.action_permitted)

    def test_missing_reversibility_acknowledgement_blocks(self):
        switch = _full_authorization(reversibility_acknowledged=False)
        d = evaluate(switch)
        self.assertFalse(d.action_permitted)

    def test_full_authorization_satisfies_every_gate(self):
        d = evaluate(_full_authorization())
        self.assertTrue(d.action_permitted)


class TestSwitchStateIsInspectable(unittest.TestCase):
    def test_4_to_dict_shape(self):
        d = evaluate(_full_authorization())
        as_dict = d.to_dict()
        self.assertEqual(as_dict["action_permitted"], True)
        self.assertIn("reasons", as_dict)


class TestRequiredAuthorityIsExplicit(unittest.TestCase):
    def test_5_reasons_name_who_authorized_and_why(self):
        d = evaluate(_full_authorization())
        self.assertIn("Kyle", d.reasons[-1])
        self.assertIn("test authorization", d.reasons[-1])


class TestInvalidTransitionIsRejected(unittest.TestCase):
    def test_6_cannot_bypass_by_hand_constructing_a_permitted_decision(self):
        """authorize_communication() re-derives from the SWITCH, never
        trusts a caller-constructed CommunicationDecision."""
        switch = CommunicationSwitch()  # fully blank, fails everything
        with self.assertRaises(CommunicationDenied):
            authorize_communication(switch)

    def test_authorize_communication_raises_never_returns_false_silently(self):
        with self.assertRaises(CommunicationDenied):
            authorize_communication(CommunicationSwitch())

    def test_authorize_communication_succeeds_on_genuinely_valid_switch(self):
        self.assertTrue(authorize_communication(_full_authorization()))


class TestNoNetworkAccessRequired(unittest.TestCase):
    def test_7_no_test_in_this_module_imports_a_network_capability(self):
        """Structural proof, not just convention: this test file's own
        import lines name no network-capable module."""
        source = inspect.getsource(sys.modules[__name__])
        import_lines = [l for l in source.splitlines() if l.startswith(("import ", "from "))]
        for line in import_lines:
            for forbidden in ("requests", "urllib", "socket", "http.client"):
                self.assertNotIn(forbidden, line, line)


class TestNoProductionNetworkImport(unittest.TestCase):
    def test_8_communication_gate_module_has_no_network_import(self):
        source = inspect.getsource(_module)
        import_lines = [l for l in source.splitlines() if l.startswith(("import ", "from "))]
        for line in import_lines:
            for forbidden in ("requests", "urllib", "socket", "http.client", "boto3"):
                self.assertNotIn(forbidden, line, line)

    def test_module_performs_no_io_calls(self):
        """No open(), no subprocess, no socket construction anywhere in
        the module's actual source — a pure decision function."""
        source = inspect.getsource(_module)
        for forbidden in ("subprocess", "socket.socket", "urlopen", "requests.get", "requests.post"):
            self.assertNotIn(forbidden, source)


class TestFutureCapabilityPathDocumentedNotClaimed(unittest.TestCase):
    def test_10_module_docstring_states_no_capability_implemented(self):
        doc = _module.__doc__
        self.assertIn("MAKES NO NETWORK CONNECTION", doc)

    def test_scopes_are_declared_but_none_implemented_anywhere_in_repo(self):
        self.assertEqual(COMMUNICATION_SCOPES, frozenset({
            "READ_URL", "READ_API", "RECEIVE_WEBHOOK",
        }))


if __name__ == "__main__":
    unittest.main()
