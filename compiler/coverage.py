"""
TitanOS doctrine compiler — doctrine <-> code <-> test coverage checker.

WHY THIS EXISTS

This session produced a defect (F-006) with a precise shape: the doctrine
claimed an invariant was enforced, the enforcement existed only in an
optional constructor, and the actual trust boundary validated nothing. The
claim and the code disagreed for weeks and nothing detected it, because
nothing was checking that the doctrine's own claims were true.

This module is that check. It is deliberately boring: no model inference,
no heuristics, no scoring. Every result is a deterministic predicate over
files that either exist or do not.

WHAT IT VERIFIES

For each invariant declared in a doctrine YAML:

  1. Does the file named in `enforced_at` exist?
  2. Does the symbol named after `::` actually appear in that file?
  3. Does the file named in `test` exist?
  4. Does the declared `status` match what the evidence supports?

(4) is the important one. A doctrine may claim ENFORCED while pointing at
a symbol that no longer exists — which is precisely how F-006 survived. A
status is a CLAIM, and this compiler's job is to refuse claims that the
filesystem contradicts.

WHAT IT CANNOT VERIFY — stated, not hidden

It checks that enforcement code EXISTS and is REACHABLE BY NAME. It does
not and cannot verify that the code is CORRECT, that it is actually called
on every path, or that it enforces what the prose says it enforces. A
symbol present in a file satisfies this checker; only tests and adversarial
review establish that it works.

So: passing this checker is necessary, never sufficient. It closes the gap
between "doctrine claims X" and "no such code exists". It does not close
the gap between "code exists" and "code is right". Anyone reading a green
report should understand exactly that much and no more.

REFUSAL IS THE SUCCESS PATH

A mismatch returns a non-zero exit and a structured failure record. Per
§20, failure is data: the report is emitted either way and is meant to be
committed, not discarded.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    raise

# Statuses a doctrine may declare, and what evidence each one requires.
# DOCUMENTARY_ONLY and ASPIRATIONAL are first-class: a doctrine is allowed
# to describe something not yet built, provided it says so. What is NOT
# allowed is claiming ENFORCED without enforcement.
STATUS_REQUIRES_CODE = {"ENFORCED", "PARTIAL"}
STATUS_NO_CODE_EXPECTED = {"NOT_ENFORCED", "DOCUMENTARY_ONLY", "ASPIRATIONAL"}
VALID_STATUSES = STATUS_REQUIRES_CODE | STATUS_NO_CODE_EXPECTED


@dataclass
class InvariantFinding:
    invariant_id: str
    declared_status: str
    verdict: str  # CONSISTENT | STALE_CLAIM | UNDERCLAIMED | INVALID_STATUS | UNCHECKABLE
    enforced_at: str | None
    file_exists: bool | None
    symbol_found: bool | None
    test_exists: bool | None
    detail: str


def _resolve(root: Path, ref: str) -> tuple[Path | None, str | None]:
    """Split 'path/file.ts::symbol' into a resolved path and symbol name."""
    if "::" in ref:
        rel, symbol = ref.split("::", 1)
    else:
        rel, symbol = ref, None
    candidate = (root / rel).resolve()
    return (candidate if candidate.exists() else None), symbol


def check_invariant(root: Path, inv: dict[str, Any]) -> InvariantFinding:
    inv_id = str(inv.get("id", "<unnamed>"))
    status = str(inv.get("status", "")).upper()
    enforced_at = inv.get("enforced_at")
    test_ref = inv.get("test")

    if status not in VALID_STATUSES:
        return InvariantFinding(
            inv_id, status, "INVALID_STATUS", enforced_at, None, None, None,
            f"status '{status}' is not one of {sorted(VALID_STATUSES)}",
        )

    # Some enforcement is genuinely not a file+symbol (e.g. "AST scan of the
    # package source"). Mark it UNCHECKABLE rather than failing it — but say
    # so loudly, because an unverifiable claim is not a verified one.
    if not enforced_at or "/" not in str(enforced_at):
        return InvariantFinding(
            inv_id, status, "UNCHECKABLE", enforced_at, None, None, None,
            "enforced_at is prose, not a file reference — this compiler cannot "
            "verify it. Treat the ENFORCED claim as unverified by automation.",
        )

    path, symbol = _resolve(root, str(enforced_at))
    file_exists = path is not None
    symbol_found: bool | None = None
    if file_exists and symbol:
        symbol_found = symbol in path.read_text(encoding="utf-8", errors="replace")

    test_exists: bool | None = None
    if test_ref and "/" in str(test_ref):
        tpath, _ = _resolve(root, str(test_ref).split("::", 1)[0])
        test_exists = tpath is not None

    evidence_ok = file_exists and (symbol_found is not False)

    if status in STATUS_REQUIRES_CODE and not evidence_ok:
        missing = "file does not exist" if not file_exists else f"symbol '{symbol}' not found in file"
        return InvariantFinding(
            inv_id, status, "STALE_CLAIM", enforced_at, file_exists, symbol_found, test_exists,
            f"doctrine claims {status} but {missing}. A status is a claim; the "
            f"filesystem contradicts it. This is the F-006 failure shape.",
        )

    if status in STATUS_NO_CODE_EXPECTED and evidence_ok:
        return InvariantFinding(
            inv_id, status, "UNDERCLAIMED", enforced_at, file_exists, symbol_found, test_exists,
            f"doctrine says {status} but enforcement appears to exist. Doctrine is "
            f"stale relative to code — issue a new doctrine version rather than "
            f"editing this one in place.",
        )

    detail = "declared status matches the evidence on disk"
    if status in STATUS_REQUIRES_CODE and test_exists is False:
        detail += " (WARNING: declared test file not found — enforcement is untested)"
    return InvariantFinding(
        inv_id, status, "CONSISTENT", enforced_at, file_exists, symbol_found, test_exists, detail,
    )


def check_doctrine(doctrine_path: Path, root: Path) -> dict[str, Any]:
    doc = yaml.safe_load(doctrine_path.read_text(encoding="utf-8"))
    findings = [check_invariant(root, inv) for inv in doc.get("invariants", [])]
    failed = [f for f in findings if f.verdict in {"STALE_CLAIM", "INVALID_STATUS", "UNDERCLAIMED"}]
    return {
        "doctrine_id": doc.get("id"),
        "doctrine_version": str(doc.get("version")),
        "invariants_checked": len(findings),
        "consistent": sum(1 for f in findings if f.verdict == "CONSISTENT"),
        "uncheckable": sum(1 for f in findings if f.verdict == "UNCHECKABLE"),
        "failed": len(failed),
        # Refusal is the success path: a doctrine that misstates its own
        # enforcement must not compile.
        "result": "REFUSED" if failed else "ACCEPTED",
        "findings": [asdict(f) for f in findings],
    }


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: coverage.py <doctrine.yaml> <workspace-root>", file=sys.stderr)
        return 2
    report = check_doctrine(Path(argv[1]), Path(argv[2]))
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
