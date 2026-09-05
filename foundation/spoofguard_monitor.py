"""
SpoofGuard Monitor — continuous email-security posture watch + change detection.

Outcome #3 of the NLnet/SpoofGuard proposal: a one-shot check tells you your
domain is spoofable today; monitoring catches the moment it *becomes* spoofable
(or silently regresses) so it can be fixed before criminals exploit it. This
snapshots a domain's posture, compares it against the last recorded snapshot,
and flags regressions (a control that got weaker) — the alertable event.

Reuses `email_security_report` (public DNS only, gated). Pure logic + a plain
JSONL store; no network in tests (fetch_fn injected). Honest: it reports only
what changed against a real prior snapshot — a first-ever check has nothing to
compare to and reports no change, never a fabricated one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from foundation.email_security_report import assess_email_security

__all__ = [
    "snapshot_from_report", "diff_snapshots", "regressions",
    "render_alert", "monitor", "last_snapshot", "append_snapshot",
    "PostureChange",
]

# Higher = worse. A move to a higher severity is a regression.
_SEVERITY = {"PASS": 0, "WARN": 1, "FAIL": 2}


@dataclass(frozen=True)
class PostureChange:
    check: str
    old_status: str
    new_status: str
    worse: bool          # True = regression (the alertable direction)


def snapshot_from_report(report, now: Optional[datetime] = None) -> dict:
    """A compact, serialisable snapshot of a domain's posture."""
    now = now or datetime.now(timezone.utc)
    return {
        "domain": report.domain,
        "grade": report.grade,
        "checks": {f.check: f.status for f in report.findings},
        "at": now.isoformat(),
    }


def diff_snapshots(old: dict, new: dict) -> List[PostureChange]:
    """Per-check status changes between two snapshots. `worse` marks the ones
    that regressed (moved to a higher severity)."""
    old_checks = (old or {}).get("checks", {})
    new_checks = (new or {}).get("checks", {})
    changes: List[PostureChange] = []
    for check in sorted(set(old_checks) | set(new_checks)):
        o = old_checks.get(check, "PASS")
        n = new_checks.get(check, "PASS")
        if o != n:
            worse = _SEVERITY.get(n, 0) > _SEVERITY.get(o, 0)
            changes.append(PostureChange(check, o, n, worse))
    return changes


def regressions(changes: List[PostureChange]) -> List[PostureChange]:
    return [c for c in changes if c.worse]


def render_alert(domain: str, changes: List[PostureChange]) -> str:
    regs = regressions(changes)
    if not regs:
        improved = [c for c in changes if not c.worse]
        if improved:
            return (f"✅ {domain}: email security improved "
                    f"({', '.join(c.check for c in improved)}).")
        return f"· {domain}: no change in email-security posture."
    lines = [f"⚠️ {domain}: EMAIL SECURITY REGRESSED — spoofing risk up."]
    for c in regs:
        lines.append(f"  - {c.check}: {c.old_status} → {c.new_status}")
    lines.append("Fix it before criminals notice. Run a full report for the "
                 "exact records: security-report --domain " + domain)
    return "\n".join(lines)


# --- persistence: a plain append-only JSONL of snapshots -------------------

def append_snapshot(store_path: Path, snap: dict) -> None:
    store_path = Path(store_path)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(snap) + "\n")


def last_snapshot(store_path: Path, domain: str) -> Optional[dict]:
    """The most recent stored snapshot for `domain`, or None if never seen."""
    store_path = Path(store_path)
    if not store_path.is_file():
        return None
    latest = None
    try:
        for line in store_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                snap = json.loads(line)
            except json.JSONDecodeError:
                continue
            if snap.get("domain") == domain:
                latest = snap  # last matching line wins (append-only order)
    except OSError:
        return None
    return latest


def monitor(domain: str,
            store_path: Path,
            fetch_fn: Optional[Callable[[str], bytes]] = None,
            now: Optional[datetime] = None) -> Tuple[dict, List[PostureChange]]:
    """Check the domain now, diff against its last stored snapshot, persist the
    new one, and return (new_snapshot, changes). First-ever check has no prior
    and returns no changes."""
    domain = domain.strip().lower().rstrip(".")
    report = assess_email_security(domain, fetch_fn)
    new = snapshot_from_report(report, now=now)
    prior = last_snapshot(store_path, domain)
    changes = diff_snapshots(prior, new) if prior else []
    append_snapshot(store_path, new)
    return new, changes
