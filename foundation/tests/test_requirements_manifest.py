"""
Proof that the repository's one confirmed runtime dependency (PyYAML)
is explicitly represented in requirements.txt, matches what's actually
installed, and has not silently grown beyond that one dependency.
"""

import re
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIREMENTS = REPO_ROOT / "requirements.txt"

_PIN_PATTERN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.-]+)$")


class TestRequirementsManifest(unittest.TestCase):
    def test_manifest_exists(self):
        self.assertTrue(REQUIREMENTS.exists())

    def test_pyyaml_present_and_pinned(self):
        lines = [l.strip() for l in REQUIREMENTS.read_text().splitlines() if l.strip()]
        pins = dict(m.groups() for l in lines if (m := _PIN_PATTERN.match(l)))
        self.assertIn("PyYAML", pins)

    def test_declared_version_matches_confirmed_installed_version(self):
        lines = [l.strip() for l in REQUIREMENTS.read_text().splitlines() if l.strip()]
        pins = dict(m.groups() for l in lines if (m := _PIN_PATTERN.match(l)))
        self.assertEqual(pins["PyYAML"], yaml.__version__)

    def test_no_unjustified_dependency_expansion(self):
        """The manifest records what exists now, not what TitanOS might
        one day need -- exactly one declared dependency, matching
        README.md's own "no runtime dependency beyond PyYAML" claim."""
        lines = [l.strip() for l in REQUIREMENTS.read_text().splitlines() if l.strip()]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("PyYAML=="))


if __name__ == "__main__":
    unittest.main()
