"""Measures how much of this system can run without a human or a model
typing a command -- and refuses to let that number be mistaken for how
much of the WORK was done by code.

WHY THIS MODULE EXISTS

The operator's claim is "98% code, 1% AI, 1% human in the loop." As of
today that is an assertion with no instrument behind it. Every material
operation in this repository's history -- every build, every commit,
every promotion -- was invoked by a human or an AI typing a command in a
session. Exactly ONE thing runs on a real, unattended schedule
(`foundation/cron_pulse.py`, hourly, via a live `crontab -l` entry), and
it only reads and appends to its own gitignored telemetry -- it commits
nothing, and it does not touch a single git-tracked file.

This module counts what is actually true, from disk, right now:

  scheduled_entrypoints  -- real `crontab -l` entries that reference this
                             repository, each classified READ_ONLY or
                             MUTATING
  runnable_entrypoints   -- modules with a module-level `__main__` block:
                             things that COULD run unattended if scheduled
  wired_entrypoints       -- of those, how many are actually reachable
                             from a scheduled entry (AST import-following)
  human_gated_operations -- distinct operations this repo itself declares
                             require a human: open items in
                             HUMAN_DECISIONS.md, plus distinct
                             *Denied/*Refused/*Forbidden exception classes
                             defined in non-test source
  autonomy_ratio          -- scheduled MUTATING entrypoints divided by
                             runnable entrypoints

TODAY autonomy_ratio IS 0.0. Nothing scheduled mutates anything. That is
the correct, honest answer -- see `show_the_math()`. If a future change
makes this number nonzero, it still will not mean "N% of the work is
done by code" -- see HONEST_LIMITS below and the module's own docstring
on `show_the_math()`. This module is not allowed to imply more than it
measured; if you are tempted to round autonomy_ratio up in a summary,
read HONEST_LIMITS again first.

WHAT "MUTATING" MEANS HERE (a heuristic, stated plainly)

A write to a file whose target name contains a telemetry word this
repository already uses everywhere for exactly this purpose ("log",
"state", "ledger", "receipt", "pulse", "err.log" -- see
`foundation/system_manifest.py::_DURABLE_LEDGERS` and the .gitignore
block naming these same paths "machine-local runtime state/receipts,
not source") is treated as READ_ONLY telemetry, matching how
`cron_pulse.py` is described elsewhere in this repo. A write to
anything else, an append-mode open is never enough by itself to count
as MUTATING, and a `git commit`/`git push`/`git add` subprocess call is
ALWAYS MUTATING regardless of target. This is a syntactic heuristic
over source text, not real dataflow analysis -- see HONEST_LIMITS.

Writes nothing, anywhere. Every field is recomputed from disk on call.
"""

from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__all__ = [
    "ScheduledEntry",
    "AutonomyMeasurement",
    "measure_autonomy",
    "show_the_math",
    "HONEST_LIMITS",
]

REPO_ROOT = Path(__file__).resolve().parent.parent

# This module cannot see, and does not pretend to see, any of these.
# Every count below is bounded by this list -- read it before trusting
# autonomy_ratio for anything more than what it literally says.
HONEST_LIMITS = (
    "cannot see who or what typed the command that invoked a runnable "
    "module -- a human running `python3 foo.py` and an AI session doing "
    "the same are structurally indistinguishable from disk",
    "cannot distinguish an AI-invoked run from a human-invoked one -- "
    "there is no actor field anywhere this module reads",
    "a crontab entry proves the entry is SCHEDULED, not that anything "
    "useful happens when it fires, nor that it has ever fired "
    "successfully -- see foundation/sentinel.py::read_cron_stderr() for "
    "the actual failure evidence, which this module does not read",
    "MUTATING vs READ_ONLY classification is a syntactic heuristic over "
    "source text (write-mode file targets, git subprocess calls) -- it "
    "is not real dataflow analysis and can be fooled by indirection it "
    "does not trace (a write through an opaque callback, a dynamically "
    "constructed git command string)",
    "autonomy_ratio measures what fraction of runnable modules are both "
    "scheduled and capable of mutating something -- it does NOT measure "
    "what fraction of this system's WORK was performed by code rather "
    "than by a human or a model typing commands; those are different "
    "quantities and this module only has evidence for the first one",
    "wired_entrypoints follows LOCAL (this-repo) imports only, to a "
    "bounded depth, and cannot see dynamic imports (importlib, "
    "__import__ with a computed name) or subprocess-launched scripts",
)


@dataclass(frozen=True)
class ScheduledEntry:
    """One `crontab -l` line that references this repository."""

    raw_line: str
    script_path: Optional[str]   # repo-relative, or None if unresolved
    classification: str          # "READ_ONLY" | "MUTATING" | "UNRESOLVED"
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class AutonomyMeasurement:
    """A computed snapshot. Every field is derived, none is declared."""

    crontab_available: bool
    scheduled_entrypoints: tuple[ScheduledEntry, ...]
    runnable_entrypoints: tuple[str, ...]     # repo-relative paths
    wired_entrypoints: tuple[str, ...]        # subset of runnable, reachable
    human_gated_operations: int
    human_gated_detail: tuple[str, ...]
    autonomy_ratio: float
    notes: tuple[str, ...] = ()

    @property
    def scheduled_mutating_count(self) -> int:
        return sum(1 for e in self.scheduled_entrypoints
                    if e.classification == "MUTATING")

    @property
    def scheduled_read_only_count(self) -> int:
        return sum(1 for e in self.scheduled_entrypoints
                    if e.classification == "READ_ONLY")


# ---------------------------------------------------------------------
# crontab
# ---------------------------------------------------------------------

def _read_crontab() -> tuple[bool, list[str]]:
    """Returns (available, lines). Never raises -- an absent crontab
    binary, an empty crontab, and 'no crontab for user' are all
    ordinary states, not failures."""
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True,
                           text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return False, []
    if r.returncode != 0:
        # "no crontab for user" exits nonzero on most cron implementations.
        # That is a real, valid state (zero scheduled entries), not an
        # unavailable crontab -- but we cannot tell the two apart from
        # the exit code alone, so we report unavailable and let the
        # caller's notes say so honestly.
        return False, []
    return True, r.stdout.splitlines()


_CD_RE = re.compile(r"\bcd\s+(\S+)\s*&&")
_PY_FILE_RE = re.compile(r"(\S+\.py)\b")


def _resolve_scheduled_script(line: str, repo_root: Path) -> Optional[Path]:
    """Best-effort: find the .py file this crontab line invokes and
    resolve it to an absolute path. Returns None if no .py token is
    present (e.g. a shell script entry)."""
    m = _PY_FILE_RE.search(line)
    if not m:
        return None
    py_token = m.group(1)
    if py_token.startswith("/"):
        return Path(py_token)
    cd_m = _CD_RE.search(line)
    base = Path(cd_m.group(1)) if cd_m else repo_root
    return (base / py_token).resolve()


def _line_references_repo(line: str, repo_root: Path) -> bool:
    """Does this crontab line schedule something in THIS repository?

    The path is resolved first. The previous version compared
    `str(repo_root)` directly, so a caller passing `Path(".")` -- the
    obvious thing to type -- matched every crontab line containing a
    dot, including entries belonging to entirely unrelated projects on
    the same machine. That inflated the headline autonomy_ratio from
    the true 0.0000 to 0.1111 by counting another project's scheduled
    job as this system's autonomy.

    Caught by running the module two ways and getting two answers. A
    metric whose value depends on how the caller spelled the path is
    not a measurement.
    """
    return str(Path(repo_root).resolve()) in line


# ---------------------------------------------------------------------
# AST: __main__ detection, local-import closure, write/mutation scan
# ---------------------------------------------------------------------

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


def _parse(path: Path) -> Optional[ast.Module]:
    try:
        return ast.parse(path.read_text(errors="ignore"), filename=str(path))
    except (OSError, SyntaxError):
        return None


def _module_to_path(module: str, level: int, importer: Path,
                     repo_root: Path) -> Optional[Path]:
    """Best-effort resolution of an import statement to a repo-local
    .py file. Only resolves imports that plausibly point inside this
    repository; anything else (stdlib, third-party) returns None."""
    if level and level > 0:
        # relative import: from .foo import bar / from . import foo
        pkg_dir = importer.parent
        for _ in range(level - 1):
            pkg_dir = pkg_dir.parent
        if not module:
            return None
        candidate = pkg_dir / (module.replace(".", "/") + ".py")
        return candidate if candidate.is_file() else None
    if not module:
        return None
    top = module.split(".")[0]
    top_dir = repo_root / top
    if not top_dir.exists():
        return None
    candidate = repo_root / (module.replace(".", "/") + ".py")
    if candidate.is_file():
        return candidate
    candidate_pkg = repo_root / module.replace(".", "/") / "__init__.py"
    if candidate_pkg.is_file():
        return candidate_pkg
    return None


def _local_imports(tree: ast.Module, importer: Path, repo_root: Path) -> set[Path]:
    found: set[Path] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                p = _module_to_path(alias.name, 0, importer, repo_root)
                if p:
                    found.add(p)
        elif isinstance(node, ast.ImportFrom):
            p = _module_to_path(node.module or "", node.level or 0,
                                importer, repo_root)
            if p:
                found.add(p)
    return found


_MAX_IMPORT_DEPTH = 6


def _local_import_closure(entry: Path, repo_root: Path,
                           max_depth: int = _MAX_IMPORT_DEPTH) -> set[Path]:
    """BFS over local (this-repo) imports, bounded depth, cycle-safe.
    Includes the entry module itself."""
    seen: set[Path] = {entry}
    frontier = [entry]
    depth = 0
    while frontier and depth < max_depth:
        nxt: list[Path] = []
        for mod_path in frontier:
            tree = _parse(mod_path)
            if tree is None:
                continue
            for imp in _local_imports(tree, mod_path, repo_root):
                if imp not in seen:
                    seen.add(imp)
                    nxt.append(imp)
        frontier = nxt
        depth += 1
    return seen


_TELEMETRY_WORDS = ("log", "state", "ledger", "receipt", "pulse", "err")
_GIT_MUTATING_SUBCOMMANDS = ("commit", "push", "add", "checkout -b",
                             "merge", "rebase", "tag", "rm ")


def _is_telemetry_target(target_node: ast.AST) -> bool:
    try:
        text = ast.unparse(target_node).lower()
    except Exception:  # noqa: BLE001 -- unparse is best-effort here
        return False
    return any(word in text for word in _TELEMETRY_WORDS)


def _call_name(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _string_args(node: ast.Call) -> list[str]:
    out = []
    for a in list(node.args) + [kw.value for kw in node.keywords]:
        if isinstance(a, ast.Constant) and isinstance(a.value, str):
            out.append(a.value)
        else:
            try:
                out.append(ast.unparse(a))
            except Exception:  # noqa: BLE001
                pass
    return out


def _scan_module_for_mutation(path: Path) -> list[str]:
    """Returns evidence strings for MUTATING behaviour found in this one
    module's own source (does not follow imports -- callers that need
    the transitive picture combine this over `_local_import_closure`)."""
    tree = _parse(path)
    if tree is None:
        return []
    evidence: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        line = getattr(node, "lineno", "?")

        if name in ("run", "call", "Popen", "check_call", "check_output", "system"):
            joined = " ".join(_string_args(node)).lower()
            if "git" in joined and any(sub in joined for sub in _GIT_MUTATING_SUBCOMMANDS):
                evidence.append(f"{path.name}:{line} git mutating subprocess call")
            continue

        if name == "open" and node.args:
            mode = None
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if mode and any(c in mode for c in ("w", "x")) and "a" not in mode.replace("+", ""):
                target = node.args[0]
                if not _is_telemetry_target(target):
                    evidence.append(f"{path.name}:{line} open(mode={mode!r}) "
                                    f"on non-telemetry-named target")
            continue

        if name in ("write_text", "write_bytes"):
            target = node.func.value if isinstance(node.func, ast.Attribute) else None
            if target is not None and not _is_telemetry_target(target):
                evidence.append(f"{path.name}:{line} {name}() on "
                                f"non-telemetry-named target")
    return evidence


def _classify_scheduled_script(script: Path, repo_root: Path) -> tuple[str, tuple[str, ...]]:
    if not script.is_file():
        return "UNRESOLVED", (f"{script} does not exist on disk",)
    closure = _local_import_closure(script, repo_root)
    evidence: list[str] = []
    for mod in sorted(closure):
        evidence.extend(_scan_module_for_mutation(mod))
    if evidence:
        return "MUTATING", tuple(evidence)
    return "READ_ONLY", tuple(evidence)


# ---------------------------------------------------------------------
# human-gated operations
# ---------------------------------------------------------------------

_DENIAL_CLASS_RE = re.compile(r"^class\s+(\w*(?:Denied|Refused|Forbidden))\b")


def _count_denial_classes(repo_root: Path) -> tuple[int, tuple[str, ...]]:
    names: set[str] = set()
    for p in repo_root.rglob("*.py"):
        rel = p.relative_to(repo_root).as_posix()
        if rel.startswith(".git/") or "/tests/" in f"/{rel}" or rel.startswith("tests/"):
            continue
        try:
            for line in p.read_text(errors="ignore").splitlines():
                m = _DENIAL_CLASS_RE.match(line.strip())
                if m:
                    names.add(m.group(1))
        except OSError:
            continue
    return len(names), tuple(sorted(names))


def _count_open_human_decisions(repo_root: Path) -> tuple[int, tuple[str, ...]]:
    hd = repo_root / "HUMAN_DECISIONS.md"
    if not hd.is_file():
        return 0, ()
    try:
        text = hd.read_text(errors="ignore")
    except OSError:
        return 0, ()
    items = re.findall(r"^(\d+)\. (.*)$", text, re.M)
    open_titles = [body for _, body in items if not body.lstrip().startswith("~~")]
    return len(open_titles), tuple(open_titles)


# ---------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------

def measure_autonomy(repo_root: Path = REPO_ROOT) -> AutonomyMeasurement:
    """Recompute from disk. Reads only; writes nothing, anywhere."""
    repo_root = Path(repo_root)
    notes: list[str] = []

    crontab_available, lines = _read_crontab()
    if not crontab_available:
        notes.append("crontab unavailable or empty for this user -- "
                     "scheduled_entrypoints reports 0 not because none "
                     "exist, but because none were observable here")

    scheduled: list[ScheduledEntry] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not _line_references_repo(stripped, repo_root):
            continue
        script = _resolve_scheduled_script(stripped, repo_root)
        if script is None:
            scheduled.append(ScheduledEntry(stripped, None, "UNRESOLVED",
                                            ("no .py file token found in this line",)))
            continue
        classification, evidence = _classify_scheduled_script(script, repo_root)
        try:
            rel = script.relative_to(repo_root).as_posix()
        except ValueError:
            rel = str(script)
        scheduled.append(ScheduledEntry(stripped, rel, classification, evidence))

    runnable: list[Path] = []
    for p in repo_root.rglob("*.py"):
        rel = p.relative_to(repo_root).as_posix()
        if rel.startswith(".git/"):
            continue
        # A `__main__` block inside a `tests/` directory is test
        # scaffolding (`unittest.main()`), not an operational entrypoint
        # -- counting it as "runnable unattended" would conflate "this
        # file can execute its own test suite" with "this file performs
        # a real operation if invoked", which is the exact inflation
        # this module exists to refuse.
        if "/tests/" in f"/{rel}":
            continue
        tree = _parse(p)
        if tree is not None and _has_main_block(tree):
            runnable.append(p)
    runnable_rel = tuple(sorted(p.relative_to(repo_root).as_posix() for p in runnable))
    runnable_set = set(runnable)

    reachable: set[Path] = set()
    for entry in scheduled:
        if entry.script_path is None:
            continue
        script_abs = repo_root / entry.script_path
        if script_abs.is_file():
            reachable |= _local_import_closure(script_abs, repo_root)

    wired = tuple(sorted(p.relative_to(repo_root).as_posix()
                         for p in runnable_set & reachable))

    hd_count, hd_titles = _count_open_human_decisions(repo_root)
    denial_count, denial_names = _count_denial_classes(repo_root)
    human_gated_total = hd_count + denial_count
    human_gated_detail = (
        tuple(f"HUMAN_DECISIONS.md open item: {t[:80]}" for t in hd_titles)
        + tuple(f"denial exception class: {n}" for n in denial_names)
    )

    mutating_scheduled = sum(1 for e in scheduled if e.classification == "MUTATING")
    if runnable_rel:
        ratio = mutating_scheduled / len(runnable_rel)
    else:
        ratio = 0.0
        notes.append("runnable_entrypoints is 0 -- autonomy_ratio forced "
                     "to 0.0 rather than dividing by zero")

    return AutonomyMeasurement(
        crontab_available=crontab_available,
        scheduled_entrypoints=tuple(scheduled),
        runnable_entrypoints=runnable_rel,
        wired_entrypoints=wired,
        human_gated_operations=human_gated_total,
        human_gated_detail=human_gated_detail,
        autonomy_ratio=ratio,
        notes=tuple(notes),
    )


def show_the_math(m: AutonomyMeasurement) -> str:
    """Every number, its source, and what it does NOT mean. Read this
    before repeating autonomy_ratio to anyone."""
    lines = [
        "AUTONOMY MEASUREMENT (computed, not stored)",
        "",
        f"  crontab_available     {m.crontab_available}",
        f"  scheduled_entrypoints {len(m.scheduled_entrypoints)}  "
        f"(source: `crontab -l`, filtered to lines mentioning this repo path)",
    ]
    for e in m.scheduled_entrypoints:
        lines.append(f"    - [{e.classification}] {e.script_path or 'UNRESOLVED'}"
                     f"  <- {e.raw_line.strip()}")
        for ev in e.evidence:
            lines.append(f"        evidence: {ev}")
    lines += [
        f"  runnable_entrypoints  {len(m.runnable_entrypoints)}  "
        f"(source: AST scan for a module-level `if __name__ == \"__main__\":`)",
    ]
    for r in m.runnable_entrypoints:
        lines.append(f"    - {r}")
    lines += [
        f"  wired_entrypoints     {len(m.wired_entrypoints)}  "
        f"(source: AST import-closure from each scheduled entry, "
        f"intersected with runnable_entrypoints)",
    ]
    for w in m.wired_entrypoints:
        lines.append(f"    - {w}")
    lines += [
        f"  human_gated_operations {m.human_gated_operations}  "
        f"(source: open items in HUMAN_DECISIONS.md + distinct "
        f"*Denied/*Refused/*Forbidden exception classes in non-test source)",
    ]
    for d in m.human_gated_detail:
        lines.append(f"    - {d}")
    lines += [
        "",
        f"  scheduled MUTATING entries: {m.scheduled_mutating_count}",
        f"  scheduled READ_ONLY entries: {m.scheduled_read_only_count}",
        f"  autonomy_ratio = scheduled_MUTATING / runnable_entrypoints "
        f"= {m.scheduled_mutating_count} / {len(m.runnable_entrypoints)} "
        f"= {m.autonomy_ratio:.4f}",
        "",
        "  WHAT autonomy_ratio DOES NOT MEAN: a high value here would "
        "measure how much of this system CAN run unattended if left "
        "alone. It would never measure how much of the WORK in this "
        "system's history was done BY CODE rather than by a human or an "
        "AI model typing commands -- this module has no evidence at all "
        "about that second quantity, and reporting one as the other "
        "would be a false claim, not a rounding error.",
        "",
        "  HONEST_LIMITS (what this module structurally cannot see):",
    ]
    for h in HONEST_LIMITS:
        lines.append(f"    - {h}")
    for n in m.notes:
        lines.append(f"  NOTE: {n}")
    return "\n".join(lines)


if __name__ == "__main__":                                  # pragma: no cover
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    print(show_the_math(measure_autonomy()))
