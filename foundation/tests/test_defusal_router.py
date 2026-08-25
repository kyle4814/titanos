import inspect
import re
import unittest

from foundation import defusal_router
from foundation.defusal_router import (
    DEFUSAL_STEPS,
    DefusalSequence,
    DefusalStep,
    route_defusal,
)
from foundation.flow_switch import PanicSample


def sample(info: float, verify: float) -> PanicSample:
    return PanicSample(
        information_velocity=info,
        verification_velocity=verify,
        timestamp="2026-08-26T00:00:00Z",
    )


class TestRouteDefusalFailClosed(unittest.TestCase):
    def test_no_panic_returns_empty_steps(self):
        seq = route_defusal(sample(5, 10))
        self.assertFalse(seq.panic_detected)
        self.assertEqual(seq.steps, ())

    def test_equal_velocities_not_panic_returns_empty(self):
        seq = route_defusal(sample(5, 5))
        self.assertFalse(seq.panic_detected)
        self.assertEqual(seq.steps, ())

    def test_zero_zero_not_panic_returns_empty(self):
        seq = route_defusal(sample(0, 0))
        self.assertFalse(seq.panic_detected)
        self.assertEqual(seq.steps, ())

    def test_panic_returns_full_sequence(self):
        seq = route_defusal(sample(10, 5))
        self.assertTrue(seq.panic_detected)
        self.assertEqual(seq.steps, DEFUSAL_STEPS)

    def test_zero_verification_positive_information_is_panic(self):
        seq = route_defusal(sample(1, 0))
        self.assertTrue(seq.panic_detected)
        self.assertEqual(len(seq.steps), len(DEFUSAL_STEPS))

    def test_never_returns_none(self):
        self.assertIsInstance(route_defusal(sample(1, 0)), DefusalSequence)
        self.assertIsInstance(route_defusal(sample(0, 1)), DefusalSequence)

    def test_no_panic_never_returns_partial_nonempty_steps(self):
        # Fail-closed shape: a non-panicking sample must never leak any
        # of the nine steps, not even one.
        for info, verify in [(0, 0), (1, 1), (2, 5), (0, 100)]:
            seq = route_defusal(sample(info, verify))
            self.assertFalse(seq.panic_detected)
            self.assertEqual(len(seq.steps), 0)


class TestDefusalStepsShape(unittest.TestCase):
    def test_nine_steps_derived(self):
        # Honest, derived count — see module docstring for why this is
        # 9 and not a remembered "11" this session cannot verify.
        self.assertEqual(len(DEFUSAL_STEPS), 9)

    def test_step_names_unique(self):
        names = [s.name for s in DEFUSAL_STEPS]
        self.assertEqual(len(names), len(set(names)))

    def test_every_step_has_nonempty_fields(self):
        for step in DEFUSAL_STEPS:
            self.assertTrue(step.name.strip())
            self.assertTrue(step.description.strip())
            self.assertTrue(step.source.strip())

    def test_every_step_starts_incomplete(self):
        for step in DEFUSAL_STEPS:
            self.assertFalse(step.complete)

    def test_throttle_is_first_step(self):
        self.assertEqual(DEFUSAL_STEPS[0].name, "THROTTLE")

    def test_resume_only_on_exit_condition_is_last_step(self):
        self.assertEqual(DEFUSAL_STEPS[-1].name, "RESUME_ONLY_ON_EXIT_CONDITION")

    def test_preserve_raw_input_precedes_verify(self):
        names = [s.name for s in DEFUSAL_STEPS]
        self.assertLess(
            names.index("PRESERVE_RAW_INPUT"), names.index("VERIFY")
        )

    def test_freeze_belief_precedes_verify(self):
        names = [s.name for s in DEFUSAL_STEPS]
        self.assertLess(names.index("FREEZE_BELIEF"), names.index("VERIFY"))

    def test_verify_precedes_take_lowest_regret_action(self):
        names = [s.name for s in DEFUSAL_STEPS]
        self.assertLess(
            names.index("VERIFY"), names.index("TAKE_LOWEST_REGRET_ACTION")
        )


class TestDefusalStepToDict(unittest.TestCase):
    def test_to_dict_round_trips_fields(self):
        step = DEFUSAL_STEPS[0]
        d = step.to_dict()
        self.assertEqual(d["name"], step.name)
        self.assertEqual(d["description"], step.description)
        self.assertEqual(d["source"], step.source)
        self.assertEqual(d["complete"], step.complete)


class TestDefusalSequenceShape(unittest.TestCase):
    def test_steps_is_a_tuple_not_a_list(self):
        seq = route_defusal(sample(10, 1))
        self.assertIsInstance(seq.steps, tuple)

    def test_to_dict_contains_sample_and_steps(self):
        seq = route_defusal(sample(10, 1))
        d = seq.to_dict()
        self.assertTrue(d["panic_detected"])
        self.assertEqual(d["sample"]["information_velocity"], 10)
        self.assertEqual(d["sample"]["verification_velocity"], 1)
        self.assertEqual(len(d["steps"]), 9)

    def test_to_dict_no_panic_has_empty_steps_list(self):
        seq = route_defusal(sample(1, 10))
        d = seq.to_dict()
        self.assertFalse(d["panic_detected"])
        self.assertEqual(d["steps"], [])

    def test_dataclass_is_frozen(self):
        seq = route_defusal(sample(10, 1))
        with self.assertRaises(Exception):
            seq.panic_detected = False  # type: ignore[misc]

    def test_defusal_step_is_frozen(self):
        step = DEFUSAL_STEPS[0]
        with self.assertRaises(Exception):
            step.complete = True  # type: ignore[misc]


class TestNeverAnActionVerb(unittest.TestCase):
    """Mirrors sentinel.py's TestSentinelCannotExecute: this module is a
    router/planner, never an executor. No public callable may be named
    like an imperative action verb that actually performs a step."""

    _FORBIDDEN_PREFIXES = (
        "execute", "apply", "run", "do_", "perform", "commit", "write",
        "delete", "throttle", "freeze", "preserve", "resume", "verify_",
        "log_",
    )

    def test_no_public_callable_is_an_action_verb(self):
        public_callables = [
            name for name, obj in inspect.getmembers(defusal_router)
            if not name.startswith("_")
            and (inspect.isfunction(obj) or inspect.isclass(obj))
            and getattr(obj, "__module__", None) == defusal_router.__name__
        ]
        # route_* is a planning/routing verb, explicitly allowed — it
        # names the routing decision, not an executed action.
        offenders = [
            name for name in public_callables
            if not name.startswith("route_")
            and any(name.lower().startswith(p) for p in self._FORBIDDEN_PREFIXES)
        ]
        self.assertEqual(offenders, [], f"action-verb-named public callables: {offenders}")

    def test_module_never_imports_execution_or_network_primitives(self):
        src = inspect.getsource(defusal_router)
        for forbidden in ("subprocess", "socket", "urllib", "requests"):
            self.assertIsNone(
                re.search(rf"^\s*import {forbidden}\b", src, re.MULTILINE),
                f"unexpected import of {forbidden!r} in defusal_router",
            )


if __name__ == "__main__":
    unittest.main()
