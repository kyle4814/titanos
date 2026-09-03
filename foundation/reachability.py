"""foundation/reachability.py -- which capabilities can actually be
invoked, and which exist only in their own test file.

WHY THIS EXISTS

Three times in three days a module in this repository was built, tested,
documented and left unreachable:

  - `mouth_udbud_dk` / `mouth_tenderned_nl` -- 60 tests, absent from
    `sources_for_query()`, so no hunt could ever reach Denmark or the
    Netherlands.
  - `deep_sweep()` -- walked Ireland's whole register, invocable only
    from a Python shell.
  - `spec_crossref` -- 39 tests, no production caller at all.

Each was found by accident, one cycle late. `sources.py` already carries
a comment about the same failure from 2026-09-02: "registering a source
in one list and not the other means it exists everywhere except where
someone would use it."

MEASURED, 2026-09-04: 23 of 90 tested `foundation/` modules have no
importer and no entry point. Twenty-six percent of the tested module
surface cannot be reached from any production path.

WHY THIS IS A REPORT AND NOT A SENTINEL CHECK

Twenty-three findings would fire on every pulse sweep, forever, until
someone worked the list down -- and a check that always fires is a check
people learn to scroll past. `spec_crossref`'s DEFINED_NEVER_REFERENCED
had exactly this shape last cycle (27 candidates, 27 innocent) and was
narrowed rather than shipped. Same judgment here.

It becomes a gate honestly once the number is near zero. Until then it
is a number to drive down, and this module's job is to make the number
real rather than remembered.

WHAT "REACHABLE" MEANS HERE, PRECISELY

A module is reachable if a non-test Python file imports it, OR it is a
self-contained entry point (`if __name__ == "__main__"`, `def main(`,
`def _cli(`). Both are ways a human or a cron line can actually run it.

Nothing here infers INTENT. Some modules are unreachable on purpose --
`publication_gate` guards `git push`, a human action with no in-repo
call path, and `CLAUDE.md` already says so. This module reports the
fact and refuses to guess which unreachable modules are deliberate;
that judgment stays with a reader.

NO NETWORK, NO IMPORTS OF THE MODULES IT SCANS. It reads source text.
Importing them to test reachability would execute them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

__all__ = [
    "ReachabilityError",
    "ModuleReach",
    "ReachabilityReport",
    "scan_reachability",
    "format_reachability",
]


class ReachabilityError(ValueError):
    """Raised when the scan is pointed at something that is not a
    readable package directory."""


# A module that runs itself. Any of these means a human or a cron line
# has a way in, which is what "reachable" is actually asking.
_ENTRY_POINT = re.compile(
    r'^\s*if __name__ == ["\']__main__["\']|^def main\(|^def _cli\(', re.M)


@dataclass(frozen=True)
class ModuleReach:
    """One module and how it can be reached."""

    name: str
    has_test_file: bool
    importers: Tuple[str, ...]
    is_entry_point: bool

    @property
    def is_reachable(self) -> bool:
        return bool(self.importers) or self.is_entry_point

    @property
    def reach(self) -> str:
        if self.importers:
            return "IMPORTED"
        if self.is_entry_point:
            return "ENTRY_POINT"
        return "UNREACHABLE"


@dataclass(frozen=True)
class ReachabilityReport:
    modules: Tuple[ModuleReach, ...]

    @property
    def tested(self) -> Tuple[ModuleReach, ...]:
        return tuple(m for m in self.modules if m.has_test_file)

    @property
    def unreachable(self) -> Tuple[ModuleReach, ...]:
        """Tested but reachable from nowhere. Untested-and-unreachable
        is a different and lesser problem -- a module nobody tests and
        nobody calls is dead weight, not a lost capability."""
        return tuple(m for m in self.tested if not m.is_reachable)

    @property
    def entry_points(self) -> Tuple[ModuleReach, ...]:
        return tuple(m for m in self.modules if m.reach == "ENTRY_POINT")

    @property
    def percentage_unreachable(self) -> float:
        if not self.tested:
            return 0.0
        return 100.0 * len(self.unreachable) / len(self.tested)


def _import_pattern(module: str) -> "re.Pattern[str]":
    return re.compile(
        rf"(from foundation\.{re.escape(module)} import"
        rf"|from foundation import [^\n]*\b{re.escape(module)}\b"
        rf"|import foundation\.{re.escape(module)}\b)")


def scan_reachability(repo_root: Path, package: str = "foundation") -> ReachabilityReport:
    """Read every module in `package` and every non-test `.py` in the
    repository, and record how each module can be reached."""
    repo_root = Path(repo_root)
    pkg_dir = repo_root / package
    if not pkg_dir.is_dir():
        raise ReachabilityError(f"not a package directory: {pkg_dir}")

    modules = sorted(p.stem for p in pkg_dir.glob("*.py")
                     if p.stem != "__init__")
    if not modules:
        raise ReachabilityError(f"no modules found in {pkg_dir}")

    patterns = {m: _import_pattern(m) for m in modules}
    importers: dict = {m: set() for m in modules}

    for path in repo_root.rglob("*.py"):
        # A test importing a module is not a caller. That is the entire
        # distinction this module exists to draw: `spec_crossref` had 39
        # tests importing it and no way to run it.
        if "/tests/" in str(path) or path.name.startswith("test_"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for module in modules:
            if path.stem == module:
                continue
            if patterns[module].search(text):
                importers[module].add(str(path.relative_to(repo_root)))

    out = []
    for module in modules:
        source = (pkg_dir / f"{module}.py").read_text(
            encoding="utf-8", errors="ignore")
        out.append(ModuleReach(
            name=module,
            has_test_file=(pkg_dir / "tests" / f"test_{module}.py").exists(),
            importers=tuple(sorted(importers[module])),
            is_entry_point=bool(_ENTRY_POINT.search(source)),
        ))
    return ReachabilityReport(modules=tuple(out))


def format_reachability(report: ReachabilityReport, *, verbose: bool = False) -> str:
    """Leads with the unreachable count, because that is the number to
    drive down."""
    if not isinstance(report, ReachabilityReport):
        raise ReachabilityError(
            "format_reachability() takes a ReachabilityReport, not "
            f"{type(report).__name__}")

    lines = [
        "CAPABILITY REACHABILITY",
        "",
        f"modules            : {len(report.modules)}",
        f"with a test file   : {len(report.tested)}",
        f"self-running       : {len(report.entry_points)}  "
        "(main/_cli/__main__ -- a human or cron line has a way in)",
        f"UNREACHABLE        : {len(report.unreachable)}  "
        f"({report.percentage_unreachable:.0f}% of tested modules)",
        "",
    ]
    if not report.unreachable:
        lines.append(
            "Every tested module is imported by production code or runs "
            "itself. Nothing here is finished-and-forgotten.")
        return "\n".join(lines)

    lines.append("TESTED, AND REACHABLE FROM NOWHERE:")
    for m in report.unreachable:
        lines.append(f"  ! {m.name}")
    lines.append("")
    lines.append(
        "Unreachable is a FACT, not a verdict. Some of these are "
        "deliberate -- publication_gate guards `git push`, a human "
        "action with no in-repo call path, and CLAUDE.md says so. This "
        "does not guess which ones are intentional; that judgment stays "
        "with a reader.")
    if verbose:
        lines.append("")
        lines.append("REACHED, for contrast:")
        for m in report.modules:
            if m.reach == "IMPORTED":
                lines.append(f"  . {m.name}  <- {', '.join(m.importers[:3])}")
    return "\n".join(lines)
