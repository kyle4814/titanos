"""
Regressions found by running the validator against the REAL 3,058-file
legacy YAML corpus (§Phase 9), not synthetic input. Per §Phase 13: no fix
without a corresponding test.
"""

import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from schema.validator import validate_artifact  # noqa: E402


class TestNonStringYamlKeys(unittest.TestCase):
    """A real file in the corpus used `true:`/`yes:` as a mapping key
    (common in hand-written YAML, e.g. a debug flag or a boolean-keyed
    lookup table). This crashed validate_artifact() with an uncaught
    TypeError from sorted() comparing bool and str — a fail-OPEN-shaped bug:
    an exception the caller might not catch is worse than a loud rejection.
    """

    def test_boolean_key_does_not_crash(self):
        r = validate_artifact("true: something\nartifact_id: a1\n")
        self.assertIn(r.status, ("VALID", "INVALID"))  # must return, not raise
        self.assertEqual(r.status, "INVALID")  # missing required fields regardless

    def test_boolean_key_flagged_as_non_string_key(self):
        r = validate_artifact("true: something\nartifact_id: a1\n")
        self.assertTrue(any(i.rule == "R-12" for i in r.issues))

    def test_int_key_does_not_crash(self):
        r = validate_artifact("1: something\nartifact_id: a1\n")
        self.assertEqual(r.status, "INVALID")

    def test_null_key_does_not_crash(self):
        r = validate_artifact("null: something\nartifact_id: a1\n")
        self.assertEqual(r.status, "INVALID")


class TestValidatorNeverRaises(unittest.TestCase):
    """The outer try/except in validate_artifact() must convert ANY
    exception into a structured INVALID result, never propagate."""

    def test_garbage_binary_like_text_does_not_raise(self):
        try:
            r = validate_artifact("\x00\x01\x02: \xff\xfe\n")
        except Exception as e:  # pragma: no cover - this is the failure mode
            self.fail(f"validate_artifact raised {type(e).__name__}: {e}")
        self.assertEqual(r.status, "INVALID")


if __name__ == "__main__":
    unittest.main(verbosity=2)
