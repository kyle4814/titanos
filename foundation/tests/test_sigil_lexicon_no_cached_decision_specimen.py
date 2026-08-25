"""
AUTHORITY_REDERIVATION_001 -- careful fresh derivation, not a cached
description.

FINDING: the three named leads (rpa/gates/human_jurisdiction.py,
foundation/publication_gate.py, foundation/communication_gate.py) do
NOT share one causal property, despite similar vocabulary
("re-derive", "never trust a cached flag", "two-point enforcement").

human_jurisdiction.py::confirm_pilot_authorized() walks a durable,
append-only PromotionRecord.history to defend against a FORGED OR
STALE HISTORICAL RECORD -- a record whose .state field says STABLE
could lie; the function re-derives from .history instead, with a real
counterfactual (a naive `rec.state == "STABLE"` check would accept a
TESTED->STABLE promotion this gate never authorized). This is
EXCLUDED from the registered property below -- it is a materially
stronger, differently-shaped mechanism (cross-call ledger
verification), not the same contract.

publication_gate.py / communication_gate.py share a narrower, real
property: authorize_X() never accepts a pre-computed Decision object
as its parameter -- only raw declared evidence (a Switch) -- so
evaluate() always runs fresh, and there is no object shape a caller
could construct to inject an already-"approved" result. This is
SINGLE-CALL INPUT HYGIENE, not cross-call ledger verification. Proven
behaviorally below (not merely asserted): passing a Decision object
where a Switch is expected raises AttributeError, because the Decision
type does not carry the Switch's own evidence fields.
"""

import inspect
import unittest

from foundation.communication_gate import (
    CommunicationDecision, CommunicationDenied, CommunicationSwitch,
    authorize_communication,
)
from foundation import communication_gate as _comm_module
from foundation.publication_gate import (
    PublicationDecision, PublicationRefused, PublicationSwitch,
    authorize_publish,
)
from foundation import publication_gate as _pub_module


def _valid_publication_switch() -> PublicationSwitch:
    return PublicationSwitch(
        target_repo="github.com/example/repo",
        secret_scan_passed=True, secret_scan_evidence="clean scan",
        license_present=True, readme_present=True, classification="PUBLIC",
        human_authorized_by="Kyle", human_authorization_note="go ahead",
        reversibility_acknowledged=True,
    )


def _valid_communication_switch() -> CommunicationSwitch:
    return CommunicationSwitch(
        requested_scope="READ_URL", human_authorized_by="Kyle",
        human_authorization_note="test", reversibility_acknowledged=True,
    )


class TestDomainAPublicationGate(unittest.TestCase):
    def test_1_valid_evidence_authorizes(self):
        self.assertTrue(authorize_publish(_valid_publication_switch()))

    def test_2_absent_evidence_blocks(self):
        with self.assertRaises(PublicationRefused):
            authorize_publish(PublicationSwitch())


class TestDomainBCommunicationGate(unittest.TestCase):
    def test_3_valid_evidence_authorizes(self):
        self.assertTrue(authorize_communication(_valid_communication_switch()))

    def test_4_absent_evidence_blocks(self):
        with self.assertRaises(CommunicationDenied):
            authorize_communication(CommunicationSwitch())


class TestIndependence(unittest.TestCase):
    def test_5_no_cross_import_between_the_two_gate_modules(self):
        for mod, other_names in (
            (_pub_module, ("communication_gate", "CommunicationSwitch")),
            (_comm_module, ("publication_gate", "PublicationSwitch")),
        ):
            source = inspect.getsource(mod)
            import_lines = [l for l in source.splitlines() if l.startswith(("import ", "from "))]
            for line in import_lines:
                for name in other_names:
                    self.assertNotIn(name, line, line)


class TestNoCachedDecisionBypass(unittest.TestCase):
    """The actual claimed property, proven behaviorally -- not merely
    asserted by a docstring, unlike the prior test this cycle audited
    and found to be tautological given the type signature alone."""

    def test_6_publication_decision_cannot_be_substituted_for_a_switch(self):
        forged = PublicationDecision(action_permitted=True)
        with self.assertRaises(AttributeError):
            authorize_publish(forged)  # type: ignore[arg-type]

    def test_7_communication_decision_cannot_be_substituted_for_a_switch(self):
        forged = CommunicationDecision.__new__(CommunicationDecision)
        forged.action_permitted = True
        with self.assertRaises(AttributeError):
            authorize_communication(forged)  # type: ignore[arg-type]


class TestRepresentationBoundaryHumanJurisdictionExcluded(unittest.TestCase):
    """human_jurisdiction.py's property is materially different and
    explicitly NOT part of this registration -- it re-derives from a
    durable, cross-call, append-only history walk, which neither gate
    module does at all."""

    def test_8_neither_gate_module_reads_a_history_attribute(self):
        for mod in (_pub_module, _comm_module):
            source = inspect.getsource(mod)
            self.assertNotIn(".history", source)

    def test_9_human_jurisdiction_genuinely_walks_history(self):
        import sys
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(repo_root))
        from rpa.gates import human_jurisdiction
        source = inspect.getsource(human_jurisdiction)
        self.assertIn("rec.history", source)
        self.assertIn("stable_entries", source)


class TestPriorControlIntegrity(unittest.TestCase):
    def test_10_prior_lexicon_specimens_still_present(self):
        from pathlib import Path
        lexicon = (Path(__file__).resolve().parents[2] / "SIGIL_LEXICON.md").read_text()
        for stable_id in ("SIGIL.REF_INTEGRITY", "SIGIL.NO_DELETE_SURFACE", "SIGIL.ABSENT_ILLEGAL_EDGE"):
            self.assertIn(stable_id, lexicon)


if __name__ == "__main__":
    unittest.main()
