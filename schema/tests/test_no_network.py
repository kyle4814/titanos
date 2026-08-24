"""
AST-scans schema/ and firewall/ source for network/execution imports.
Ported from titanos-provenance/tests/test_no_network.py — same rationale:
a promise in a docstring is not enforcement; a static scan that fails the
build is.
"""

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = ("schema", "firewall", "legacy")

FORBIDDEN_MODULES = {
    "socket", "urllib", "urllib2", "urllib3", "http", "httplib", "requests",
    "httpx", "ftplib", "telnetlib", "smtplib", "asyncio", "websockets",
    "aiohttp", "subprocess", "ctypes", "os.system",
}


def _iter_py_files():
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if "__pycache__" in p.parts or "/tests/" in str(p):
                continue
            yield p


class TestNoNetworkOrExecImports(unittest.TestCase):
    def test_no_forbidden_imports_in_library_source(self):
        violations = []
        for path in _iter_py_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in FORBIDDEN_MODULES:
                            violations.append(f"{path}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in FORBIDDEN_MODULES:
                        violations.append(f"{path}: from {node.module} import ...")
        self.assertEqual(violations, [],
                         f"forbidden imports found:\n" + "\n".join(violations))

    def test_no_eval_exec_or_dynamic_import_calls(self):
        violations = []
        for path in _iter_py_files():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec", "__import__"):
                        violations.append(f"{path}:{node.lineno}: {node.func.id}(...)")
        self.assertEqual(violations, [], f"dynamic execution found:\n" + "\n".join(violations))

    def test_yaml_loader_is_always_safe(self):
        """schema/validator.py must never use yaml.Loader / yaml.FullLoader,
        which permit arbitrary Python object construction from tags."""
        violations = []
        for path in _iter_py_files():
            text = path.read_text(encoding="utf-8")
            if "yaml.load(" in text and "Loader=yaml.SafeLoader" not in text \
               and "SafeLoader" not in text:
                violations.append(str(path))
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
