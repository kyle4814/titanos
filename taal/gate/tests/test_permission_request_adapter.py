import unittest

from taal.gate.permission_request_adapter import permission_request_to_gate_input
from taal.gate.root_gate import GateInput, evaluate_request

READ_ONLY_REQUEST = {
    "id": "pr-001",
    "requester": "agent-alpha",
    "resource": "s3://bucket/reports/",
    "action": "READ",
    "scope": "read-only access to the reports/ prefix for the next 15 minutes",
    "duration": "15m",
    "delegation": False,
    "delegation_chain": [],
    "justification": "generating a quarterly summary report",
    "provenance": "VERIFIED",
    "risk_hint": "low risk, read-only",
    "reversibility": "FULLY_REVERSIBLE",
    "self_authorized": False,
}


class TestDirectFieldMapping(unittest.TestCase):
    def test_ask_fields_map_one_to_one(self):
        gi = permission_request_to_gate_input(READ_ONLY_REQUEST)
        self.assertEqual(gi.request_id, "pr-001")
        self.assertEqual(gi.requester, "agent-alpha")
        self.assertEqual(gi.action, "READ")
        self.assertEqual(gi.resource, "s3://bucket/reports/")
        self.assertEqual(gi.scope, READ_ONLY_REQUEST["scope"])
        self.assertEqual(gi.duration, "15m")

    def test_delegation_maps_directly(self):
        pr = dict(READ_ONLY_REQUEST, delegation=True)
        gi = permission_request_to_gate_input(pr)
        self.assertTrue(gi.delegation)

    def test_provenance_status_maps_directly(self):
        for value in ("VERIFIED", "CLAIMED", "UNKNOWN", "UNVERIFIABLE"):
            pr = dict(READ_ONLY_REQUEST, provenance=value)
            gi = permission_request_to_gate_input(pr)
            self.assertEqual(gi.provenance_status, value)

    def test_returns_a_gate_input_instance(self):
        gi = permission_request_to_gate_input(READ_ONLY_REQUEST)
        self.assertIsInstance(gi, GateInput)


class TestReversibleDerivation(unittest.TestCase):
    def test_fully_reversible_maps_to_true(self):
        gi = permission_request_to_gate_input(READ_ONLY_REQUEST)
        self.assertTrue(gi.reversible)

    def test_partially_reversible_maps_to_false(self):
        pr = dict(READ_ONLY_REQUEST, reversibility="PARTIALLY_REVERSIBLE")
        gi = permission_request_to_gate_input(pr)
        self.assertFalse(gi.reversible)

    def test_irreversible_maps_to_false(self):
        pr = dict(READ_ONLY_REQUEST, reversibility="IRREVERSIBLE")
        gi = permission_request_to_gate_input(pr)
        self.assertFalse(gi.reversible)

    def test_unknown_reversibility_maps_to_false(self):
        pr = dict(READ_ONLY_REQUEST, reversibility="UNKNOWN")
        gi = permission_request_to_gate_input(pr)
        self.assertFalse(gi.reversible)


class TestHighImpactDerivation(unittest.TestCase):
    def test_high_stakes_action_flags_high_impact(self):
        for action in ("DELETE", "CONFIGURATION_CHANGE", "CREDENTIAL_ACCESS"):
            pr = dict(READ_ONLY_REQUEST, action=action)
            gi = permission_request_to_gate_input(pr)
            self.assertTrue(gi.high_impact, f"{action} should flag high_impact")

    def test_irreversible_alone_flags_high_impact_even_for_read(self):
        pr = dict(READ_ONLY_REQUEST, action="READ", reversibility="IRREVERSIBLE")
        gi = permission_request_to_gate_input(pr)
        self.assertTrue(gi.high_impact)

    def test_read_action_and_fully_reversible_is_not_high_impact(self):
        gi = permission_request_to_gate_input(READ_ONLY_REQUEST)
        self.assertFalse(gi.high_impact)


class TestFieldsNeverSelfAsserted(unittest.TestCase):
    """The actual seam this adapter exists to prove: a permission_request
    document cannot smuggle in identity/authority claims about itself."""

    def test_identity_and_authority_fields_always_default_closed(self):
        gi = permission_request_to_gate_input(READ_ONLY_REQUEST)
        self.assertFalse(gi.identity_verified)
        self.assertFalse(gi.authority_asserted)
        self.assertEqual(gi.authority_evidence, ())
        self.assertFalse(gi.scope_declared_necessary)
        self.assertEqual(gi.reducible_scope, ())
        self.assertEqual(gi.supporting_evidence, ())
        self.assertEqual(gi.contradictory_evidence, ())

    def test_even_a_request_document_that_smuggles_those_keys_is_ignored(self):
        # A permission_request document has no schema field for these --
        # but prove the adapter ignores them even if present in the dict,
        # rather than accidentally passing them through via **kwargs-style
        # code that might get added later.
        pr = dict(
            READ_ONLY_REQUEST,
            identity_verified=True,
            authority_asserted=True,
            authority_evidence=["forged"],
        )
        gi = permission_request_to_gate_input(pr)
        self.assertFalse(gi.identity_verified)
        self.assertFalse(gi.authority_asserted)
        self.assertEqual(gi.authority_evidence, ())


class TestEndToEndThroughRealRootGate(unittest.TestCase):
    """Drives a real permission_request dict through the adapter and then
    through the real, unmodified root_gate.evaluate_request()."""

    def test_read_only_verified_request_does_not_reach_authorized_without_identity(self):
        # Q1 in root_gate caps at REQUIRES_HUMAN_REVIEW when identity_verified
        # is False -- and the adapter never sets it True from the document
        # alone, so even a "clean" request cannot self-certify its way to
        # AUTHORIZED through this path.
        gi = permission_request_to_gate_input(READ_ONLY_REQUEST)
        decision = evaluate_request(gi)
        self.assertNotEqual(decision.verdict, "AUTHORIZED")
        self.assertEqual(decision.request_id, "pr-001")

    def test_high_stakes_delete_request_is_not_authorized(self):
        pr = dict(READ_ONLY_REQUEST, action="DELETE", reversibility="IRREVERSIBLE")
        gi = permission_request_to_gate_input(pr)
        decision = evaluate_request(gi)
        self.assertIn(decision.verdict, ("REQUIRES_HUMAN_REVIEW", "QUARANTINED", "REFUSED"))


if __name__ == "__main__":
    unittest.main()
