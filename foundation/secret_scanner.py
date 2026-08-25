"""
Reusable secret/credential scanner (`PARETO_FRONTIER.md` FRONTIER-001).

WHAT THIS IS

The ad hoc scan run once during this repository's publication-readiness
pass (API-key shapes, PEM headers, generic secret assignments, email
addresses, filesystem-path leakage) wrapped into a tested module —
mechanical, per that entry's own effort estimate, because the pattern
set was already proven against this real repository (it found the
`legacy/manifests/*.json` path-leakage issue for real).

WHY IT REUSES `foundation.sentinel.Finding` RATHER THAN A NEW TYPE

Same shape, same purpose: an observation with a location, a confidence
level, and a recommended next action — `Finding` already is that. A
second near-identical dataclass here would be exactly the duplication
this repository's own doctrine repeatedly warns against.

WHAT `scan()` FEEDS

`ScanReport.to_evidence_string()` produces the literal string
`foundation/publication_gate.py::PublicationSwitch.secret_scan_evidence`
expects — this scanner is the missing input to an already-existing,
already-tested gate, not a standalone artifact nobody calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from foundation.sentinel import Finding, consolidate

__all__ = ["ScanReport", "scan", "SECRET_PATTERNS"]

_EXCLUDED_DIRS = {".git", "__pycache__", "node_modules"}
_BINARY_SUFFIXES = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".zip"}

# name -> (compiled pattern, confidence). Deliberately narrow and
# imperfect — same spirit as reality_yield_ledger.py's forward-looking-
# word blocklist: a structural nudge that catches the common real
# mistake, not a guarantee against a determined evader.
SECRET_PATTERNS: dict[str, tuple[re.Pattern, str]] = {
    "AWS access key id": (re.compile(r"AKIA[0-9A-Z]{16}"), "HIGH"),
    "PEM private key header": (
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "HIGH",
    ),
    "generic secret/token/password assignment": (
        re.compile(r'(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?token|password)\s*[:=]\s*["\']?[A-Za-z0-9_\-/+]{12,}["\']?'),
        "MEDIUM",
    ),
    "email address": (
        re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "LOW",
    ),
    "external filesystem path leakage": (
        re.compile(r"(?:/home/[A-Za-z0-9_.\-]+/(?!home)|/Users/[A-Za-z0-9_.\-]+/|C:\\Users\\[A-Za-z0-9_.\-]+\\)"),
        "LOW",
    ),
}


@dataclass(frozen=True)
class ScanReport:
    findings: tuple[Finding, ...]
    files_scanned: int

    def to_evidence_string(self) -> str:
        if not self.findings:
            return f"scan() found 0 findings across {self.files_scanned} files"
        summary = "; ".join(f"{f.observation} at {f.evidence_location}" for f in self.findings)
        return f"scan() found {len(self.findings)} finding(s) across {self.files_scanned} files: {summary}"


def scan(paths: list[Path] | Path) -> ScanReport:
    """Scan `paths` (a single root or a list of files/dirs) for the
    patterns in `SECRET_PATTERNS`. Read-only. Text files only — binary
    files are skipped, not scanned byte-for-byte."""
    if isinstance(paths, Path):
        roots = [paths]
    else:
        roots = list(paths)

    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _EXCLUDED_DIRS for part in path.parts):
                continue
            if path.suffix in _BINARY_SUFFIXES:
                continue
            files.append(path)

    raw: list[Finding] = []
    for path in files:
        try:
            text = path.read_text(errors="ignore")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, (pattern, confidence) in SECRET_PATTERNS.items():
                if pattern.search(line):
                    raw.append(Finding(
                        observation=f"possible {name}",
                        evidence_location=f"{path}:{line_no}",
                        confidence=confidence,
                        interpretation=f"line matches the '{name}' pattern",
                        reversibility="reversible — scan is read-only, remediation is a separate step",
                        recommended_next_action="HUMAN_REVIEW_REQUIRED" if confidence != "LOW" else "review if publishing",
                    ))

    return ScanReport(findings=consolidate(raw), files_scanned=len(files))
