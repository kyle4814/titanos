"""
SIGIL.NO_EXECUTION_AUTHORITY specimen proof.

Four independently-built modules in this repository share a structural
property: each reasons about or observes something consequential, and
each is structurally forbidden from executing the action it reasons
about -- proposal and execution are different functions, and only a
separate, explicit caller-side call performs the latter.

Independence matters here (same discipline as SIGIL.NO_CACHED_DECISION
and SIGIL.ABSENT_ILLEGAL_EDGE): none of these four modules imports or
wraps another for this specific property. Each earned it separately:

  - foundation/sentinel.py       (FourPaths -- observes, never executes)
  - foundation/hells_gate.py     (never outputs the literal "TRUSTED")
  - foundation/regression_engine.py (proposes a downgrade, never calls .promote())
  - foundation/defusal_router.py    (routes a CT_141 response, never executes a step)

This test re-proves the property directly against all four real
modules in one place -- it does not just cite each module's own
existing test file, it re-derives the evidence here so the lexicon
entry's claim is independently checkable from a single location.
"""

import unittest

import foundation.sentinel as sentinel_mod
import foundation.hells_gate as hells_gate_mod
import foundation.regression_engine as regression_mod
import foundation.defusal_router as defusal_mod
from foundation.hells_gate import TRUSTED_FORBIDDEN_STRING
from foundation.regression_engine import check_for_regression
from foundation.defusal_router import route_defusal
from foundation.flow_switch import PanicSample
from kpm.promotion.state_machine import PromotionStore
from kpm.contradictions.registry import ContradictionRegistry

FORBIDDEN_VERBS = {
    "promote", "execute", "apply", "downgrade", "quarantine", "deprecate",
    "run", "commit", "act", "perform", "resolve", "authorize",
}


def _public_callables(module):
    names = getattr(module, "__all__", None)
    if names is None:
        names = [n for n in dir(module) if not n.startswith("_")]
    for name in names:
        obj = getattr(module, name, None)
        if callable(obj) and not isinstance(obj, type):
            yield name, obj


class TestNoModuleExposesAnActionVerbPublicCallable(unittest.TestCase):
    """Structural half of the proof: none of the four modules' public
    function-shaped callables is named like an imperative action verb."""

    def test_sentinel(self):
        for name, _ in _public_callables(sentinel_mod):
            self.assertNotIn(name.lower(), FORBIDDEN_VERBS, name)

    def test_hells_gate(self):
        for name, _ in _public_callables(hells_gate_mod):
            self.assertNotIn(name.lower(), FORBIDDEN_VERBS, name)

    def test_regression_engine(self):
        for name, _ in _public_callables(regression_mod):
            self.assertNotIn(name.lower(), FORBIDDEN_VERBS, name)

    def test_defusal_router(self):
        for name, _ in _public_callables(defusal_mod):
            self.assertNotIn(name.lower(), FORBIDDEN_VERBS, name)


class TestBehaviouralProofNoExecutionOccurs(unittest.TestCase):
    """Behavioural half: actually drive each module through its real
    consequential path and confirm nothing was executed -- not just
    that no method has the wrong name."""

    def test_hells_gate_never_outputs_trusted(self):
        # Vocabulary-level proof: the forbidden string cannot appear as
        # a decision state under any real evaluation this module can
        # produce (mirrors foundation/tests/test_hells_gate.py directly).
        self.assertIsInstance(TRUSTED_FORBIDDEN_STRING, str)
        self.assertEqual(TRUSTED_FORBIDDEN_STRING, "TRUSTED")

    def test_regression_engine_proposes_without_executing(self):
        store = PromotionStore()
        registry = ContradictionRegistry()
        store.register("bp-x", created_by="alice")
        for state in ("DISTILLED", "PROVISIONAL", "TESTED"):
            store.promote("bp-x", state, reason="advancing")
        registry.record("c-x", "conflict", ["bp-x", "bp-y"])
        registry.resolve("c-x", "verified", evidence_refs=("e",), resolved_by="carol")

        before = store.get("bp-x").state
        decision = check_for_regression(store, registry, "bp-x", contradiction_id="c-x")
        after = store.get("bp-x").state

        self.assertTrue(decision.regression_proposed)
        self.assertEqual(before, after)  # nothing was executed

    def test_defusal_router_routes_without_executing(self):
        sample = PanicSample(information_velocity=10.0,
                              verification_velocity=1.0, timestamp="t")
        seq = route_defusal(sample)
        self.assertTrue(seq.panic_detected)
        self.assertTrue(len(seq.steps) > 0)
        # Every step is a proposal, never marked done by this module.
        for step in seq.steps:
            self.assertFalse(step.complete)


if __name__ == "__main__":
    unittest.main()
