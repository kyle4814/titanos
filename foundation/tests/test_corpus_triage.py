"""Counting files is the mistake this instrument exists to prevent.

Built after three corpora, ~1,800 files, were hand-audited to the same
conclusion by the same repeated checks.
"""

import json
import tempfile
import unittest
from pathlib import Path

from foundation.corpus_triage import (
    CorpusTriageError,
    TEMPLATE_RATIO_SCAFFOLD,
    VERDICTS,
    structural_key,
    triage,
)

SCAFFOLD = '''"""Bounded scaffold. Feedstock, not production."""
from dataclasses import dataclass
from typing import Any

@dataclass
class {name}Result:
    status: str

def execute_{lower}(inputs: dict[str, Any]) -> {name}Result:
    if not isinstance(inputs, dict):
        return {name}Result("REJECT")
    return {name}Result("PROPOSED")
'''

REAL = '''def summarise(rows):
    total = 0
    for r in rows:
        if r > 0:
            total += r
    return total / len(rows) if rows else 0
'''


def _tree(files: dict) -> Path:
    root = Path(tempfile.mkdtemp())
    for name, body in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    return root


class TestStructuralCollapseSeesThroughWording(unittest.TestCase):
    def test_M_the_same_shape_with_different_words_is_one_template(self):
        """The measurement byte-hashing cannot make: twenty specifications
        versus one specification written twenty times."""
        a = structural_key("# TASK SPECIFICATION\nPurpose: define task.\n")
        b = structural_key("# LINEAGE SPECIFICATION\nPurpose: define lineage.\n")
        self.assertEqual(a, b)

    def test_genuinely_different_shapes_stay_distinct(self):
        self.assertNotEqual(
            structural_key("# HEADING\n- bullet\n"),
            structural_key("def f():\n    return 1\n"))

    def test_M_a_templated_corpus_reports_its_real_document_count(self):
        files = {f"d{i}/topic_{i}.md": f"# TOPIC{i} SPEC\nPurpose: {i}.\n"
                 for i in range(40)}
        r = triage(_tree(files))
        self.assertEqual(r.files, 40)
        self.assertEqual(r.structural_templates, 1)
        self.assertEqual(r.copies_not_documents(), 39)
        self.assertLess(r.template_ratio(), TEMPLATE_RATIO_SCAFFOLD)


class TestDeclaredTypeIsNotTrusted(unittest.TestCase):
    def test_M_yaml_that_is_not_yaml_is_reported(self):
        """91 of 123 files in a real corpus were prose under .yaml."""
        r = triage(_tree({"a.yaml": "# HEADING\n\nINPUT -> VALIDATE -> DONE\n",
                          "b.yaml": "key: value\nother: 2\n"}))
        self.assertEqual(r.yaml_total, 2)
        self.assertEqual(r.yaml_not_structured, 1)
        bad = [f for f in r.facts if not f.declared_type_holds]
        self.assertEqual(len(bad), 1)
        self.assertTrue(bad[0].detail)

    def test_M_python_that_does_not_parse_is_reported_with_the_reason(self):
        """A real corpus shipped `class 06ValueEngineResult` -- an
        identifier starting with a digit, one per domain."""
        r = triage(_tree({"broken.py": "class 06Result:\n    pass\n"}))
        self.assertEqual(len(r.py_parse_failures), 1)
        self.assertIn("broken.py", r.py_parse_failures[0])
        self.assertIn("line", r.py_parse_failures[0])

    def test_a_valid_file_is_not_flagged(self):
        r = triage(_tree({"ok.yaml": "a: 1\n", "ok.py": REAL}))
        self.assertTrue(all(f.declared_type_holds for f in r.facts))


class TestScaffoldIsDistinguishedFromImplementation(unittest.TestCase):
    def test_M_a_constant_returning_function_is_a_scaffold(self):
        r = triage(_tree({"s.py": SCAFFOLD.format(name="Thing", lower="thing")}))
        self.assertEqual(r.py_constant_return_scaffolds, 1)
        self.assertEqual(r.py_real_implementations, 0)
        self.assertEqual(r.verdict, "SCAFFOLD_ONLY")

    def test_M_a_function_that_computes_is_not_called_a_scaffold(self):
        """Deliberately narrow: any branch, loop or use of the input is
        real behaviour however small."""
        r = triage(_tree({"r.py": REAL}))
        self.assertEqual(r.py_real_implementations, 1)
        self.assertEqual(r.py_constant_return_scaffolds, 0)

    def test_a_mixed_corpus_is_reported_as_mixed_not_dismissed(self):
        files = {f"t{i}.md": f"# T{i}\ntext {i}\n" for i in range(30)}
        files["real.py"] = REAL
        r = triage(_tree(files))
        self.assertEqual(r.verdict, "MIXED")
        self.assertEqual(r.py_real_implementations, 1)

    def test_real_code_in_a_varied_corpus_is_implementable(self):
        files = {"a.py": REAL,
                 "b.py": "def g(x):\n    return [i*2 for i in x]\n",
                 "c.md": "# notes\n"}
        r = triage(_tree(files))
        self.assertEqual(r.verdict, "IMPLEMENTABLE")

    def test_every_verdict_is_from_the_declared_set(self):
        r = triage(_tree({"x.md": "# x\n"}))
        self.assertIn(r.verdict, VERDICTS)


class TestUnrunnableTestsAreCaught(unittest.TestCase):
    def test_M_a_test_importing_a_module_nobody_ships_is_reported(self):
        """70 corpus tests imported `titanos_stub`, which existed nowhere.
        A corpus whose tests cannot run has demonstrated nothing."""
        r = triage(_tree({
            "test_x.py": "from titanos_stub import execute_x\n"
                         "def test_x():\n    assert execute_x(None)\n"}))
        self.assertIn("titanos_stub", r.unresolved_imports)

    def test_stdlib_imports_are_not_reported_as_unresolved(self):
        r = triage(_tree({"a.py": "import json\nimport pathlib\n"
                                  "def f():\n    return json.dumps({})\n"}))
        self.assertEqual(r.unresolved_imports, ())

    def test_an_import_satisfied_within_the_corpus_resolves(self):
        r = triage(_tree({"helper.py": REAL,
                          "user.py": "import helper\n"
                                     "def f():\n    return helper.summarise([1])\n"}))
        self.assertNotIn("helper", r.unresolved_imports)

    def test_a_caller_may_declare_modules_that_exist_elsewhere(self):
        r = triage(_tree({"a.py": "import foundation\n"
                                  "def f():\n    return foundation\n"}),
                   resolvable=["foundation"])
        self.assertEqual(r.unresolved_imports, ())


class TestManifestClaimsAreChecked(unittest.TestCase):
    def test_M_a_manifest_declaring_the_wrong_count_is_caught(self):
        """A real manifest declared 750 files, shipped 751, and carried no
        hashes at all."""
        r = triage(_tree({
            "PACKAGE_MANIFEST.json": json.dumps(
                {"package_id": "X", "source_file_count": 750}),
            "a.md": "# a\n"}))
        joined = " ".join(r.manifest_claims)
        self.assertIn("declares 750", joined)
        self.assertIn("lists no file entries", joined)

    def test_an_accurate_manifest_raises_no_claim_about_counts(self):
        r = triage(_tree({
            "PACKAGE_MANIFEST.json": json.dumps(
                {"source_file_count": 2, "files": [{"path": "a.md"}]}),
            "a.md": "# a\n"}))
        self.assertEqual(
            [c for c in r.manifest_claims if "declares" in c], [])

    def test_unparseable_manifest_is_reported_not_ignored(self):
        r = triage(_tree({"PACKAGE_MANIFEST.json": "{not json",
                          "a.md": "# a\n"}))
        self.assertTrue(any("not valid JSON" in c for c in r.manifest_claims))


class TestTheInstrumentDoesNotOverclaim(unittest.TestCase):
    def test_M_scaffold_only_is_not_a_judgement_of_worthlessness(self):
        """Honest feedstock says it is feedstock. The verdict routes
        attention; it does not condemn."""
        import foundation.corpus_triage as m
        self.assertIn("SCAFFOLD_ONLY", m.VERDICTS)
        surface = {n for n in dir(m) if not n.startswith("_")}
        for banned in ("worthless", "garbage", "reject_corpus", "score"):
            self.assertNotIn(banned, surface)

    def test_an_empty_tree_is_empty_not_scaffold(self):
        self.assertEqual(triage(_tree({})).verdict, "EMPTY")

    def test_a_missing_directory_raises_rather_than_reporting_zero(self):
        with self.assertRaises(CorpusTriageError):
            triage(Path("/nonexistent/corpus/path"))

    def test_it_never_modifies_the_corpus(self):
        root = _tree({"a.md": "# a\n", "b.py": REAL})
        before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        triage(root)
        after = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_the_report_shows_its_measurements(self):
        text = triage(_tree({"a.py": SCAFFOLD.format(name="A", lower="a"),
                             "b.yaml": "# prose\n"})).show_the_measurements()
        for expected in ("verdict", "structural templates",
                         "copies, not documents", "python", "yaml"):
            self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()


class TestTheInstrumentsOwnFalsePositive(unittest.TestCase):
    """Found by running the instrument against the corpora it was built
    for: it reported MIXED where the hand-audit said SCAFFOLD_ONLY."""

    def test_M_a_bare_assert_test_is_not_an_implementation(self):
        """70 corpus test files are `def test_x(): assert ...` with no
        return. Counting them as real bodies inflated the verdict."""
        r = triage(_tree({
            "test_a.py": "def test_a():\n    assert 1 == 1\n"}))
        self.assertEqual(r.py_real_implementations, 0)
        self.assertEqual(r.verdict, "SCAFFOLD_ONLY")

    def test_M_a_file_that_cannot_import_is_not_evidence_of_anything(self):
        """A file whose imports do not resolve cannot run, whatever its
        body looks like."""
        r = triage(_tree({
            "x.py": "from nowhere_at_all import thing\n"
                    "def f(rows):\n    return sum(r for r in rows)\n"}))
        self.assertIn("nowhere_at_all", r.unresolved_imports)
        self.assertEqual(r.py_real_implementations, 0)

    def test_the_same_body_with_resolvable_imports_does_count(self):
        """Positive control: it is the unresolved import that disqualifies,
        not the shape of the code."""
        r = triage(_tree({
            "x.py": "import json\n"
                    "def f(rows):\n    return sum(r for r in rows)\n"}))
        self.assertEqual(r.unresolved_imports, ())
        self.assertEqual(r.py_real_implementations, 1)

    def test_M_the_real_corpora_now_read_as_scaffold_only(self):
        """The end-to-end check: the instrument must reproduce the
        hand-audit it was built to replace."""
        files = {}
        for i in range(70):
            files[f"test_{i}.py"] = (
                f"from titanos_stub import execute_{i}\n"
                f"def test_{i}():\n    assert execute_{i}(None).status == 'REJECT'\n")
            files[f"mod_{i}.py"] = SCAFFOLD.format(name=f"M{i}", lower=f"m{i}")
        r = triage(_tree(files))
        self.assertEqual(r.verdict, "SCAFFOLD_ONLY")
        self.assertEqual(r.py_real_implementations, 0)
        self.assertIn("titanos_stub", r.unresolved_imports)
