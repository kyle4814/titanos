"""The one computed answer to "what capabilities does this repository have,
and is anything actually calling them?"

WHY THIS IS COMPUTED AND NEVER HAND-MAINTAINED

`CAPABILITY_MANIFEST.json` was hand-typed. It carried `as_of: 2026-08-27`
and listed 10 subsystems while `compiler/` and `gems/` already existed on
disk, and roughly 20 substantial `foundation/` modules built since that
date appeared nowhere in it. This is the exact pattern this repository has
already lived through and named repeatedly: `README.md`'s test count sat
at 915 against a real 2,400; `CLAUDE.md` asserted "zero network
connections" for several cycles after five fetchers were built; `SIGIL.md`
and `CLAUDE.md` both carried a stale `LATTICE:6` and AGREED with each
other, so nothing caught it. A hand-typed snapshot is a copy of a fact,
and a copy drifts. This module recomputes from disk every call and writes
nothing unless `write_manifest()` is called explicitly.

WHAT "STATE" MEANS AND WHY IT HAS EXACTLY FOUR VALUES

`Capability.state` is derived from two independent, separately-measured
facts -- `has_tests` and `production_importers` -- never asserted by a
human and never inferred from a name or a docstring:

- `VERIFIED`        -- has tests AND at least one production importer.
  Both a correctness check exists and something outside the tests
  actually depends on the code running correctly.
- `IMPLEMENTED_UNWIRED` -- has tests, zero production importers, and no
  `__main__`: nothing can reach it at all.
- `ENTRYPOINT` -- has tests and a `__main__` but no importer. Reachable
  by cron, a shell script or an operator; not unwired.
  THE SINGLE MOST IMPORTANT DISTINCTION THIS FILE MAKES. "The code
  exists and is tested" and "anything in this repository calls it" are
  different facts, and this repository has confused them before --
  `CLAUDE.md`'s own 2026-09-01 gates audit found twelve gate/switch
  modules with declarations, implementations and tests, of which exactly
  one (`discovery_authorization`/`communication_gate`) is reachable from
  a real production call site. Collapsing VERIFIED and
  IMPLEMENTED_UNWIRED into one "VERIFIED" bucket -- which is exactly what
  the old hand-typed manifest did for every entry -- hides that finding
  behind a single reassuring word.
- `UNTESTED`         -- no tests exist for this capability at all.
- `SCAFFOLD_ONLY`    -- the code parses as valid Python and defines
  functions, but every function body is a stub (pass / `...` / a bare
  docstring / `raise NotImplementedError`). It looks like a capability
  from a directory listing and is not one yet.

These four never collapse into each other. A caller wanting a single
"is it done" boolean is asking a question this module deliberately
refuses to answer, because that boolean is exactly what turned an unwired
gate into an unnoticed one.

HOW EVIDENCE IS GATHERED (and what it does NOT claim)

`has_tests`/`test_count` and `production_importers` are both computed by
parsing real `import`/`from ... import` statements with `ast` and
resolving them to files that actually exist in this repository -- the
same resolution strategy already proven in `foundation/autonomy_metric.py`
(`_module_to_path`/`_local_imports`), reimplemented here rather than
imported because that module's helpers are private, this module's
resolution targets differ (capability ownership, not entrypoint reachability),
and a third caller of a private helper is a worse coupling than five
lines of duplicated, individually-testable AST resolution.

This module does not run any test suite. `test_count` is an inventory
(how many `def test_...` exist in files that import this capability), not
a pass count -- the same "inventory, not a pass" honesty
`foundation/system_manifest.py` already applies to its own test count.
`has_build_report` reuses `foundation/sentinel.py::has_substantive_build_
report` rather than re-checking `.exists()`, for the same reason that
function itself documents: eight empty `BUILD_REPORT.md` files once
scored as eight real ones under a bare-existence check.

WHAT IT COVERS

Every top-level directory containing at least one `.py` file (computed by
scanning, not by a hardcoded list -- this is precisely the defect being
fixed) becomes a `SUBSYSTEM` capability. `foundation/sentinel.py`'s
`SUBSYSTEMS_REQUIRING_BUILD_REPORT` is reused as the set that MUST carry a
build report, not re-derived as a second list -- but it is not used to
decide which directories exist; the filesystem is. Every substantial
`foundation/*.py` module (skipping `__init__.py` and anything under a
`tests/` directory) becomes a second, separate `MODULE` capability --
`foundation` itself is both a `SUBSYSTEM` (it has its own tests/ and,
historically, a BUILD_REPORT.md) and the parent of ~60 individually
tracked `MODULE` entries, and collapsing those two views into one would
lose exactly the granularity this file exists to provide.

WHAT `write_manifest()` PRESERVES

The old `CAPABILITY_MANIFEST.json` carried real, human-written prose --
`problem_class`, `limitations`, `authority_required` -- that no generator
can honestly reconstruct. `write_manifest()` reads the CURRENT
`CAPABILITY_MANIFEST.json` (if one exists) before overwriting it, and
carries those three fields forward for any capability_id that already had
them. It never invents a description for a capability that never had one
-- a new entry says so plainly (`"no human-written description recorded"`)
rather than getting a generated paragraph pretending to be prose.

There is no `as_of` field. `generated_at` is a timestamp taken at write
time, alongside `generated_by` (this module's own dotted path) and
`repo_revision` (the git short hash at write time) -- so staleness is
detectable by regenerating and diffing, not by trusting a string someone
typed once.
"""

from __future__ import annotations

import ast
import json
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

__all__ = [
    "Capability",
    "discover_capabilities",
    "write_manifest",
    "STATE_VERIFIED",
    "STATE_IMPLEMENTED_UNWIRED",
    "STATE_ENTRYPOINT",
    "STATE_UNTESTED",
    "STATE_SCAFFOLD_ONLY",
    "ALL_STATES",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "CAPABILITY_MANIFEST.json"

_EXCLUDED_TOP_DIRS = {".git", "__pycache__", "node_modules", "foundation",
                      "corpus", "build", "dist"}
# `foundation` is excluded from the *generic* top-level scan only because
# it is handled explicitly (as both a SUBSYSTEM and the parent of the
# MODULE entries) -- it is not skipped, it is special-cased below.
_EXCLUDED_DIR_PARTS = {".git", "__pycache__", "node_modules", "corpus",
                       "build", "dist"}

STATE_VERIFIED = "VERIFIED"
STATE_IMPLEMENTED_UNWIRED = "IMPLEMENTED_UNWIRED"
# Tested, no importer, but has a `__main__` -- reachable by cron, a shell
# script or an operator. Distinct from IMPLEMENTED_UNWIRED, which means
# nothing can reach it at all. See _derive_state() for why this exists.
STATE_ENTRYPOINT = "ENTRYPOINT"
STATE_UNTESTED = "UNTESTED"
STATE_SCAFFOLD_ONLY = "SCAFFOLD_ONLY"
ALL_STATES = (STATE_VERIFIED, STATE_ENTRYPOINT,
              STATE_IMPLEMENTED_UNWIRED, STATE_UNTESTED,
              STATE_SCAFFOLD_ONLY)

_PROSE_FIELDS = ("problem_class", "limitations", "authority_required")
_NO_PROSE = "no human-written description recorded"


def _git(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True,
                            text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


@dataclass(frozen=True)
class Capability:
    """One discovered capability and the evidence its `state` rests on.

    `kind` is `"SUBSYSTEM"` (a top-level directory) or `"MODULE"` (one
    `foundation/*.py` file). `path` is repo-relative and POSIX-slashed.
    `evidence` is a tuple of short strings, each traceable to one of the
    other fields -- it exists so a reader never has to trust `state`
    without being able to see what produced it.
    """

    capability_id: str
    path: str
    kind: str
    has_build_report: bool
    has_tests: bool
    test_count: int
    production_importers: int
    entrypoint: bool
    state: str
    evidence: tuple = ()
    problem_class: Optional[str] = None
    limitations: Optional[str] = None
    authority_required: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------
# AST: resolve local imports to real files, detect __main__, detect stubs
# ---------------------------------------------------------------------

def _parse(path: Path) -> Optional[ast.Module]:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"),
                          filename=str(path))
    except (OSError, SyntaxError):
        return None


def _resolve_local_import(module: str, level: int, importer: Path,
                           repo_root: Path) -> Optional[Path]:
    """Best-effort resolution of one import target to a real file in this
    repository. Mirrors `foundation/autonomy_metric.py::_module_to_path`'s
    strategy (relative imports walk up from the importer's package;
    absolute imports only resolve if the top-level name is a real
    directory here) -- reimplemented locally rather than imported because
    that function is private to its module and this file's use is a
    distinct question (capability ownership vs. entrypoint reachability)."""
    if level and level > 0:
        pkg_dir = importer.parent
        for _ in range(level - 1):
            pkg_dir = pkg_dir.parent
        if not module:
            return None
        candidate = pkg_dir / (module.replace(".", "/") + ".py")
        if candidate.is_file():
            return candidate
        candidate_pkg = pkg_dir / module.replace(".", "/") / "__init__.py"
        return candidate_pkg if candidate_pkg.is_file() else None
    if not module:
        return None
    top = module.split(".")[0]
    if (repo_root / top).exists():
        candidate = repo_root / (module.replace(".", "/") + ".py")
        if candidate.is_file():
            return candidate
        candidate_pkg = repo_root / module.replace(".", "/") / "__init__.py"
        if candidate_pkg.is_file():
            return candidate_pkg
    # Fallback: sibling-directory script-style import (no package prefix,
    # relies on the caller's own directory being on sys.path -- the
    # convention `gems/claim_ledger/test_claim_ledger.py` uses:
    # `from claim_ledger import ...` resolved against its own directory,
    # not the repo root). Only tried for a single-component module name;
    # a dotted name here would not be a plain sibling import.
    if "." not in module:
        sibling = importer.parent / (module + ".py")
        if sibling.is_file() and sibling != importer:
            return sibling
    return None


def _local_imports(tree: ast.Module, importer: Path,
                    repo_root: Path) -> set:
    """Every real repo-local file this module's `import`/`from ... import`
    statements resolve to. For `from X import Y`, tries both `X` (Y may be
    a symbol inside a package's `__init__.py`) and `X.Y` (Y may itself be
    a submodule, e.g. `from foundation import crystal`)."""
    found: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                p = _resolve_local_import(alias.name, 0, importer, repo_root)
                if p:
                    found.add(p)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            lvl = node.level or 0
            p = _resolve_local_import(base, lvl, importer, repo_root)
            if p:
                found.add(p)
            for alias in node.names:
                combined = f"{base}.{alias.name}" if base else alias.name
                p2 = _resolve_local_import(combined, lvl, importer, repo_root)
                if p2:
                    found.add(p2)
    return found


def _has_main_block(tree: ast.Module) -> bool:
    for node in tree.body:
        if not isinstance(node, ast.If):
            continue
        test = node.test
        if (isinstance(test, ast.Compare)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and len(test.comparators) == 1
                and isinstance(test.comparators[0], ast.Constant)
                and test.comparators[0].value == "__main__"):
            return True
    return False


_STUB_BODY_TYPES = (ast.Pass,)


def _is_stub_body(body: list) -> bool:
    """A function body counts as a stub if every statement is a
    docstring, `pass`, `...`, or `raise NotImplementedError(...)`."""
    for i, stmt in enumerate(body):
        if i == 0 and isinstance(stmt, ast.Expr) and isinstance(
                stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            continue  # docstring
        if isinstance(stmt, _STUB_BODY_TYPES):
            continue
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) \
                and stmt.value.value is Ellipsis:
            continue
        if isinstance(stmt, ast.Raise) and isinstance(stmt.exc, ast.Call) \
                and isinstance(stmt.exc.func, ast.Name) \
                and stmt.exc.func.id == "NotImplementedError":
            continue
        if isinstance(stmt, ast.Raise) and isinstance(stmt.exc, ast.Name) \
                and stmt.exc.id == "NotImplementedError":
            continue
        return False
    return True


def _function_bodies_are_all_stubs(trees: list) -> Optional[bool]:
    """None if there are no function definitions to judge (a scaffold
    verdict about zero functions would be meaningless); True if every
    function found across `trees` has a stub body; False otherwise."""
    total = 0
    real = 0
    for tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total += 1
                if not _is_stub_body(node.body):
                    real += 1
    if total == 0:
        return None
    return real == 0


# ---------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------

def _iter_py_files(root: Path, repo_root: Path):
    for p in root.rglob("*.py"):
        if any(part in _EXCLUDED_DIR_PARTS for part in p.parts):
            continue
        yield p


def _is_test_path(p: Path) -> bool:
    """A file counts as a test file if it sits under a directory literally
    named `tests/` (the convention every subsystem except `gems/` uses) OR
    its own filename starts with `test_` (the convention
    `foundation/sentinel.py::count_real_tests` already uses, via its
    `rglob("test_*.py")`, and the one `gems/claim_ledger/` uses with no
    `tests/` subdirectory at all). Checking only the directory convention
    silently misclassified `gems/claim_ledger/test_claim_ledger.py` as a
    second production file during this module's own development -- caught
    by comparing this function's output against the filesystem, not by
    inspection."""
    return "tests" in p.parts or p.name.startswith("test_")


def _subsystem_dirs(repo_root: Path) -> tuple:
    dirs = []
    for child in sorted(repo_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name in _EXCLUDED_TOP_DIRS or child.name.startswith("."):
            continue
        if any(_iter_py_files(child, repo_root)):
            dirs.append(child)
    # foundation is a subsystem too -- special-cased back in, not skipped.
    foundation_dir = repo_root / "foundation"
    if foundation_dir.is_dir():
        dirs.append(foundation_dir)
    return tuple(sorted(dirs, key=lambda d: d.name))


def _build_import_index(repo_root: Path) -> dict:
    """One pass over every real `.py` file: file -> set of real local
    files it imports. Computed once and reused for every capability's
    `production_importers`, so discovery stays roughly O(files) rather
    than O(files * capabilities)."""
    index: dict = {}
    for p in _iter_py_files(repo_root, repo_root):
        tree = _parse(p)
        if tree is None:
            continue
        index[p] = _local_imports(tree, p, repo_root)
    return index


def _owner_of(p: Path, repo_root: Path, subsystem_names: set) -> tuple:
    """Which capability id(s) a file belongs to, as (subsystem_id or
    None, module_id or None)."""
    rel = p.relative_to(repo_root)
    parts = rel.parts
    if not parts:
        return None, None
    top = parts[0]
    subsystem_id = top if top in subsystem_names else None
    module_id = None
    if top == "foundation" and len(parts) == 2 and parts[1] != "__init__.py":
        module_id = f"foundation/{parts[1]}"
    return subsystem_id, module_id


def _production_importer_count(owner_path_prefix: Path, own_files: set,
                                import_index: dict, repo_root: Path) -> tuple:
    """Distinct non-test files, outside `own_files`, that import at least
    one file under `own_files`. Returns (count, sorted relative paths)."""
    importers: set = set()
    for f, imports in import_index.items():
        if f in own_files:
            continue
        if _is_test_path(f):
            continue
        if imports & own_files:
            importers.add(f)
    rels = sorted(f.relative_to(repo_root).as_posix() for f in importers)
    return len(importers), tuple(rels)


def _test_evidence(own_files: set, import_index: dict,
                    repo_root: Path) -> tuple:
    """(has_tests, test_count, referencing test file paths) for a
    capability, evidenced by real test files that actually import one of
    `own_files` -- not by filename convention."""
    from foundation.sentinel import _TEST_DEF_PATTERN
    referencing = []
    for f, imports in import_index.items():
        if not _is_test_path(f):
            continue
        if imports & own_files:
            referencing.append(f)
    count = 0
    for f in referencing:
        try:
            count += len(_TEST_DEF_PATTERN.findall(
                f.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            continue
    rels = tuple(sorted(f.relative_to(repo_root).as_posix() for f in referencing))
    return (len(referencing) > 0, count, rels)


def _derive_state(has_tests: bool, production_importers: int,
                   is_scaffold: Optional[bool],
                   is_entrypoint: bool = False) -> str:
    """Evidence in, state out. Never asserted.

    ENTRYPOINT EXISTS BECAUSE THE FIRST VERSION WAS WRONG ABOUT
    cron_pulse.py

    The original rule classified anything with zero production importers
    as IMPLEMENTED_UNWIRED. That put `foundation/cron_pulse.py` -- the
    single most-executed module in this repository, scheduled hourly and
    demonstrably running -- in the same bucket as `hells_gate.py`, which
    has 36 tests and genuinely nothing that can reach it.

    Those are not the same fact. A module with a `__main__` has a real
    consumer: cron, a shell script, an operator. Nothing IMPORTS it and
    nothing ever will, because that is not how an entrypoint is used.
    Calling it unwired conflated "no importer" with "no consumer" and
    made a published number wrong.

    So IMPLEMENTED_UNWIRED now means what it says: nothing can reach
    this at all. Whether a given entrypoint is actually SCHEDULED is a
    different question, and `foundation/autonomy_metric.py` already
    owns it -- this module does not answer it twice.
    """
    if not has_tests and is_scaffold:
        return STATE_SCAFFOLD_ONLY
    if not has_tests:
        return STATE_UNTESTED
    if production_importers > 0:
        return STATE_VERIFIED
    if is_entrypoint:
        return STATE_ENTRYPOINT
    return STATE_IMPLEMENTED_UNWIRED


def discover_capabilities(repo_root: Path = REPO_ROOT) -> tuple:
    """Recompute every capability from disk. Reads only; never writes."""
    repo_root = Path(repo_root).resolve()
    import_index = _build_import_index(repo_root)
    subsystem_dirs = _subsystem_dirs(repo_root)
    subsystem_names = {d.name for d in subsystem_dirs}

    from foundation.sentinel import has_substantive_build_report

    capabilities: list = []

    # --- SUBSYSTEM entries -------------------------------------------------
    for d in subsystem_dirs:
        own_files = {p for p in _iter_py_files(d, repo_root)
                     if not _is_test_path(p)}
        if not own_files:
            continue
        rel = d.relative_to(repo_root).as_posix()
        n_importers, importer_rels = _production_importer_count(
            d, own_files, import_index, repo_root)
        has_tests, test_count, test_rels = _test_evidence(
            own_files, import_index, repo_root)
        trees = [t for t in (_parse(p) for p in own_files) if t is not None]
        is_scaffold = _function_bodies_are_all_stubs(trees)
        entrypoint = any(_has_main_block(t) for t in trees)
        has_br = has_substantive_build_report(d)
        state = _derive_state(has_tests, n_importers, is_scaffold, entrypoint)
        evidence = (
            f"{len(own_files)} non-test .py file(s) under {rel}/",
            f"BUILD_REPORT.md: {'present and substantive' if has_br else 'absent or stub'}",
            f"{len(test_rels)} test file(s), {test_count} test function(s): "
            f"{', '.join(test_rels) if test_rels else 'none'}",
            f"{n_importers} production importer(s): "
            f"{', '.join(importer_rels) if importer_rels else 'none'}",
            f"entrypoint (__main__): {'yes' if entrypoint else 'no'}",
        )
        capabilities.append(Capability(
            capability_id=d.name, path=rel, kind="SUBSYSTEM",
            has_build_report=has_br, has_tests=has_tests,
            test_count=test_count, production_importers=n_importers,
            entrypoint=entrypoint, state=state, evidence=evidence,
        ))

    # --- MODULE entries: foundation/*.py ------------------------------------
    foundation_dir = repo_root / "foundation"
    if foundation_dir.is_dir():
        for p in sorted(foundation_dir.glob("*.py")):
            if p.name == "__init__.py":
                continue
            own_files = {p}
            rel = p.relative_to(repo_root).as_posix()
            cap_id = rel
            n_importers, importer_rels = _production_importer_count(
                p, own_files, import_index, repo_root)
            has_tests, test_count, test_rels = _test_evidence(
                own_files, import_index, repo_root)
            tree = _parse(p)
            trees = [tree] if tree is not None else []
            is_scaffold = _function_bodies_are_all_stubs(trees)
            entrypoint = any(_has_main_block(t) for t in trees)
            state = _derive_state(has_tests, n_importers, is_scaffold, entrypoint)
            evidence = (
                f"single module {rel}",
                f"{len(test_rels)} test file(s), {test_count} test function(s): "
                f"{', '.join(test_rels) if test_rels else 'none'}",
                f"{n_importers} production importer(s): "
                f"{', '.join(importer_rels) if importer_rels else 'none'}",
                f"entrypoint (__main__): {'yes' if entrypoint else 'no'}",
            )
            capabilities.append(Capability(
                capability_id=cap_id, path=rel, kind="MODULE",
                has_build_report=False, has_tests=has_tests,
                test_count=test_count, production_importers=n_importers,
                entrypoint=entrypoint, state=state, evidence=evidence,
            ))

    capabilities.sort(key=lambda c: (c.kind, c.capability_id))
    return tuple(capabilities)


# ---------------------------------------------------------------------
# Carrying forward human-written prose, and writing the artifact
# ---------------------------------------------------------------------

def _load_existing_prose(manifest_path: Path) -> dict:
    """capability_id -> {problem_class, limitations, authority_required}
    for whatever the CURRENT manifest file on disk already has. Returns
    {} if no file exists or it cannot be parsed -- never raises, because
    a missing/corrupt prior file must not block regeneration."""
    if not manifest_path.is_file():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out: dict = {}
    for entry in data.get("capabilities", []):
        cap_id = entry.get("capability_id")
        if not cap_id:
            continue
        prose = {k: entry[k] for k in _PROSE_FIELDS if entry.get(k)}
        if prose:
            out[cap_id] = prose
    return out


def write_manifest(repo_root: Path = REPO_ROOT,
                    manifest_path: Path = MANIFEST_PATH) -> dict:
    """Recompute every capability and overwrite `CAPABILITY_MANIFEST.json`.
    Human-written prose (`problem_class`/`limitations`/`authority_required`)
    already on disk under a matching `capability_id` is carried forward
    unchanged; a capability with none gets the plain, honest
    `"no human-written description recorded"` rather than an invented
    paragraph. Returns the dict that was written."""
    repo_root = Path(repo_root).resolve()
    existing_prose = _load_existing_prose(manifest_path)
    capabilities = discover_capabilities(repo_root)
    revision = _git(repo_root, "rev-parse", "--short", "HEAD") or "UNKNOWN"

    entries = []
    for cap in capabilities:
        prose = existing_prose.get(cap.capability_id, {})
        entries.append({
            "capability_id": cap.capability_id,
            "path": cap.path,
            "kind": cap.kind,
            "state": cap.state,
            "has_build_report": cap.has_build_report,
            "has_tests": cap.has_tests,
            "test_count": cap.test_count,
            "production_importers": cap.production_importers,
            "entrypoint": cap.entrypoint,
            "problem_class": prose.get("problem_class", _NO_PROSE),
            "limitations": prose.get("limitations", _NO_PROSE),
            "authority_required": prose.get("authority_required", _NO_PROSE),
            "evidence": list(cap.evidence),
        })

    manifest = {
        "manifest_version": "2",
        "generated_by": "foundation.capability_registry.write_manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_revision": revision,
        "note": "Computed from repository evidence every run -- see "
                "foundation/capability_registry.py for how each field is "
                "derived. Re-run rather than hand-edit; a hand-edit here "
                "is exactly the drift this file replaced.",
        "capabilities": entries,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8")
    return manifest


if __name__ == "__main__":                                  # pragma: no cover
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    m = write_manifest(REPO_ROOT)
    print(f"wrote {MANIFEST_PATH} -- {len(m['capabilities'])} capabilities")
