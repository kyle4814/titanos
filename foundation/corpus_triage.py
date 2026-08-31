"""Decide in seconds whether a delivered corpus contains anything buildable.

WHY THIS EXISTS

Three corpora arrived in succession -- roughly 1,800 files across ten ZIP
archives -- and each was hand-audited to the same conclusion: template
noise with no implementable capability. The checks that produced that
verdict were identical every time, and running them by hand cost a full
work cell each. Three repetitions of the same manual procedure is the
signal to build the instrument.

WHAT IT MEASURES, AND WHAT IT REFUSES TO CONCLUDE

It reports measured facts: how many structural templates the files
collapse to, which declared types are lies (`.yaml` that is not YAML,
`.py` that does not parse), which scaffolds only return a constant, which
tests import modules that do not exist, and whether a manifest's claims
match the bytes on disk.

It does NOT decide that a corpus is worthless. `SCAFFOLD_ONLY` means the
files describe rather than implement -- which is exactly what honest
feedstock looks like, and several of these corpora said so in their own
docstrings. The verdict routes attention; a human decides what to do.

THE ONE MEASUREMENT THAT MATTERS MOST

`template_ratio`. A corpus of 751 files that collapses to 11 structural
templates contains 11 documents and 740 copies. Counting files is the
mistake this instrument exists to prevent -- the file count is the
loudest number and the least informative one.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

__all__ = [
    "CorpusTriageError",
    "VERDICTS",
    "FileFact",
    "CorpusReport",
    "structural_key",
    "triage",
]


class CorpusTriageError(ValueError):
    """The corpus could not be triaged as described."""


VERDICTS = (
    "IMPLEMENTABLE",    # real code that parses and does something
    "MIXED",            # some real implementation among the scaffolding
    "SCAFFOLD_ONLY",    # describes capability, does not implement it
    "EMPTY",            # nothing to triage
)

# Below this share of unique templates, the corpus is repetition rather
# than content. Derived from three measured corpora, not chosen: they
# collapsed to 4/341, 10/751 and 11/751 -- all under 2%.
TEMPLATE_RATIO_SCAFFOLD = 0.10


def structural_key(text: str) -> str:
    """Collapse wording, keep shape.

    Every identifier, number and word becomes `W`, so two files that differ
    only by a substituted topic name hash identically. This is what
    separates "twenty specifications" from "one specification written
    twenty times", and byte-level hashing cannot see it.
    """
    skeleton = re.sub(r"[A-Za-z0-9_]+", "W", text)
    return hashlib.md5(re.sub(r"\s+", " ", skeleton).strip().encode()).hexdigest()


@dataclass(frozen=True)
class FileFact:
    """What was actually true of one file, not what its extension claimed."""

    path: str
    bytes: int
    suffix: str
    sha256: str
    structural: str
    declared_type_holds: bool = True
    detail: str = ""


@dataclass(frozen=True)
class CorpusReport:
    """Measured facts about a delivered corpus. No opinions."""

    root: str
    files: int
    unique_content: int
    structural_templates: int
    verdict: str
    py_total: int = 0
    py_parse_failures: tuple[str, ...] = ()
    py_constant_return_scaffolds: int = 0
    py_real_implementations: int = 0
    yaml_total: int = 0
    yaml_not_structured: int = 0
    unresolved_imports: tuple[str, ...] = ()
    manifest_claims: tuple[str, ...] = ()
    facts: tuple[FileFact, ...] = ()

    def template_ratio(self) -> float:
        """Unique shapes per file. The number that survives the file count."""
        return self.structural_templates / self.files if self.files else 0.0

    def copies_not_documents(self) -> int:
        return max(self.files - self.structural_templates, 0)

    def show_the_measurements(self) -> str:
        lines = [
            f"CORPUS {self.root}",
            f"  verdict              {self.verdict}",
            f"  files                {self.files}",
            f"  unique content       {self.unique_content}",
            f"  structural templates {self.structural_templates}"
            f"  ({self.template_ratio():.1%} of files)",
            f"  copies, not documents {self.copies_not_documents()}",
        ]
        if self.py_total:
            lines += [
                f"  python               {self.py_total}",
                f"    parse failures     {len(self.py_parse_failures)}",
                f"    constant-return    {self.py_constant_return_scaffolds}",
                f"    real bodies        {self.py_real_implementations}",
            ]
        if self.yaml_total:
            lines.append(f"  yaml                 {self.yaml_total}"
                         f"  (not structured: {self.yaml_not_structured})")
        for u in self.unresolved_imports:
            lines.append(f"  UNRESOLVED IMPORT    {u}")
        for c in self.manifest_claims:
            lines.append(f"  MANIFEST             {c}")
        return "\n".join(lines)


def _classify_function(fn: ast.FunctionDef) -> str:
    """SCAFFOLD | REAL | NEITHER.

    A function with no return at all is NEITHER, not REAL. Found by
    attacking this module against the corpora it was built for: 70 corpus
    test files are bare `assert` functions with no return, and counting
    them as implementations inflated the verdict from SCAFFOLD_ONLY to
    MIXED -- the instrument's own false positive, on its first real run.
    """
    returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value]
    if not returns:
        return "NEITHER"
    return "SCAFFOLD" if _returns_only_constant(returns) else "REAL"


def _is_literal(node: ast.AST) -> bool:
    """A value built entirely from literals, however deeply nested.

    Container literals count. A second corpus shipped 80 functions
    returning `{"status": "PROPOSED", "topic": "..."}` -- a dict of
    constants -- and an earlier version of this check classified all 80 as
    real implementations because it handled Constant/Call/Tuple/List but
    not Dict. Same defect family as the bare-assert false positive, found
    the same way: by running the instrument on new data.
    """
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_is_literal(e) for e in node.elts)
    if isinstance(node, ast.Dict):
        return all(k is not None and _is_literal(k) for k in node.keys) and \
               all(_is_literal(v) for v in node.values)
    return False


def _returns_only_constant(returns: list) -> bool:
    """True when every return hands back a literal, a literal container, or
    a constructor call whose arguments are all literals -- a scaffold that
    computes nothing from its input.

    Deliberately narrow: a return derived from the inputs is real
    behaviour however small. Input VALIDATION that raises is not enough on
    its own -- a function that checks its argument and then returns the
    same constant regardless still computes nothing.
    """
    for r in returns:
        v = r.value
        if _is_literal(v):
            continue
        if isinstance(v, ast.Call):
            args = list(v.args) + [k.value for k in v.keywords]
            if all(_is_literal(a) for a in args):
                continue
        return False
    return True


def _module_names(tree: ast.AST) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            out.add(n.module.split(".")[0])
    return out


def triage(root: Path, resolvable: Optional[Iterable[str]] = None
           ) -> CorpusReport:
    """Measure a corpus tree. Never modifies it.

    `resolvable` names modules that exist outside the corpus (the standard
    library is assumed). An import satisfied by neither the corpus nor that
    set is reported -- a test importing a module nobody ships cannot run,
    and a corpus whose tests cannot run has not demonstrated anything.
    """
    root = Path(root)
    if not root.is_dir():
        raise CorpusTriageError(f"not a directory: {root}")

    import sys
    known = set(resolvable or ()) | set(sys.stdlib_module_names)

    files = [p for p in sorted(root.rglob("*")) if p.is_file()]
    if not files:
        return CorpusReport(root=str(root), files=0, unique_content=0,
                            structural_templates=0, verdict="EMPTY")

    facts: list[FileFact] = []
    content, structural = set(), set()
    py_fail, py_stub, py_real = [], 0, 0
    yaml_total = yaml_bad = 0
    corpus_modules = {p.stem for p in files if p.suffix == ".py"}
    unresolved: set[str] = set()

    for p in files:
        raw = p.read_bytes()
        text = raw.decode("utf-8", errors="ignore")
        rel = str(p.relative_to(root))
        holds, detail = True, ""

        if p.suffix == ".py":
            try:
                tree = ast.parse(text)
                fns = [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                kinds = [_classify_function(f) for f in fns]
                missing = {m for m in _module_names(tree)
                           if m not in known and m not in corpus_modules}
                unresolved |= missing
                # A file that cannot import cannot run, so it is not
                # evidence of implementation whatever its body looks like.
                runnable = not missing
                if fns and all(k == "SCAFFOLD" for k in kinds):
                    py_stub += 1
                elif runnable and any(k == "REAL" for k in kinds):
                    py_real += 1
            except SyntaxError as exc:
                holds = False
                detail = f"line {exc.lineno}: {exc.msg}"
                py_fail.append(f"{rel} -- {detail}")
        elif p.suffix in (".yaml", ".yml"):
            yaml_total += 1
            try:
                import yaml as _yaml
                if not isinstance(_yaml.safe_load(text), (dict, list)):
                    holds = False
                    detail = "parses to a scalar, not a mapping or sequence"
                    yaml_bad += 1
            except Exception as exc:                      # noqa: BLE001
                holds = False
                detail = type(exc).__name__
                yaml_bad += 1

        digest = hashlib.sha256(raw).hexdigest()
        skey = structural_key(text)
        content.add(digest)
        structural.add(skey)
        facts.append(FileFact(path=rel, bytes=len(raw), suffix=p.suffix,
                              sha256=digest, structural=skey,
                              declared_type_holds=holds, detail=detail))

    claims: list[str] = []
    for mf in (p for p in files if p.name.lower().endswith("manifest.json")):
        try:
            doc = json.loads(mf.read_text(errors="ignore"))
        except ValueError:
            claims.append(f"{mf.name} is not valid JSON")
            continue
        declared = doc.get("source_file_count") or doc.get("file_count")
        if isinstance(declared, int) and declared != len(files):
            claims.append(f"{mf.name} declares {declared} files; "
                          f"{len(files)} are present")
        entries = doc.get("files") or doc.get("artifacts") or []
        if not entries:
            claims.append(f"{mf.name} lists no file entries and no hashes")

    py_total = sum(1 for p in files if p.suffix == ".py")
    ratio = len(structural) / len(files)
    if py_real and ratio > TEMPLATE_RATIO_SCAFFOLD:
        verdict = "IMPLEMENTABLE"
    elif py_real:
        verdict = "MIXED"
    else:
        verdict = "SCAFFOLD_ONLY"

    return CorpusReport(
        root=str(root), files=len(files), unique_content=len(content),
        structural_templates=len(structural), verdict=verdict,
        py_total=py_total, py_parse_failures=tuple(py_fail),
        py_constant_return_scaffolds=py_stub, py_real_implementations=py_real,
        yaml_total=yaml_total, yaml_not_structured=yaml_bad,
        unresolved_imports=tuple(sorted(unresolved)),
        manifest_claims=tuple(claims), facts=tuple(facts))
