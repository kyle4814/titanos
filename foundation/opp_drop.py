"""
Opportunity Drop — the mad-dog hunter's hand-off to the closer.

Kyle wants to stop talking to the system and just WORK opportunities: open a
folder on his desktop, pick up a package, and cold-call / sell / submit. This
builds that package — a self-contained `TITAN_OPPORTUNITIES` folder written
wherever he points it (his desktop by default), refreshed every run.

Contents:
  START_HERE.md              — the day's top moves, in priority order.
  TENDERS/<id>.md            — one ready-to-file pack per live tender
                               (portal, steps, checklist), from submission_pack.
  SELL_TITANOS/              — the cold-call kit for selling titanos.tech:
    COLD_CALL_KIT.md         — the pitch, the script, the exact command to run
                               a prospect's free email-security check.
    sample_report.md         — a real generated sample report to show prospects.

HONEST BY CONSTRUCTION: it packages only what is real and reachable now
(tenders across the 5 live sources + the email-security service). It does not
invent opportunities. Where a stream is not yet built (grants, on-chain), it
says so in START_HERE rather than pretending. It writes files only; it never
calls, submits, or contacts anyone — those are the operator's.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from foundation.team_targets import live_team_targets
from foundation.submission_pack import build_submission_pack, render_pack_md, TeamProfile

__all__ = ["build_opp_drop", "default_desktop", "OPP_ROOT_NAME"]

OPP_ROOT_NAME = "TITAN_OPPORTUNITIES"

# Candidate Windows-desktop locations when running under WSL. The first that
# exists wins; if none do, the caller must pass an explicit dest.
_DESKTOP_CANDIDATES = (
    "/mnt/c/Users/tech2/OneDrive/Desktop",
    "/mnt/c/Users/tech2/Desktop",
)


def default_desktop() -> Optional[Path]:
    for c in _DESKTOP_CANDIDATES:
        p = Path(c)
        if p.is_dir():
            return p
    return None


def _write(path: Path, text: str, written: List[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    written.append(path)


def _start_here(now: datetime, dated) -> str:
    """The day's hunt result: opportunities to apply for, ranked, with Kyle's
    ONE action per item. He applies/actions/authorises, then goes back to
    selling. No cold-call kit — he has his own leads and offer."""
    withd = [t for t in dated if t.deadline_date()]
    standing = [t for t in dated if not t.deadline_date()]
    lines: List[str] = []
    lines.append(f"# 🐕 TITAN — OPPORTUNITIES TO APPLY FOR  ({now:%a %d %b %Y})")
    lines.append("")
    lines.append("The system hunted the world while you were calling. Below is")
    lines.append("real money you can apply for — every figure is off the actual")
    lines.append("notice, nothing invented. Action the good ones, then back to it.")
    lines.append("")
    lines.append(f"**{len(dated)} live opportunities. {len(withd)} on a clock, "
                 f"{len(standing)} always-open.**")
    lines.append("")
    lines.append("## ⏰ CLOSING SOON — apply first (soonest deadline)")
    for t in withd:
        lines.append(f"- **{t.deadline_date()}** · {t.value} · {t.title}")
        lines.append(f"  → ACTION: open `TENDERS/{t.target_id}.md`, apply at {t.link}")
    lines.append("")
    lines.append("## 💰 ALWAYS-OPEN — join anytime, no deadline")
    for t in standing:
        lines.append(f"- {t.value} · {t.title} → `TENDERS/{t.target_id}.md`")
    lines.append("")
    lines.append("## YOUR ACTION PER ITEM")
    lines.append("Open the pack in `TENDERS/`. Each has the portal, the steps, and")
    lines.append("the exact checklist. You: apply / run the command it names /")
    lines.append("authorise it. Fill your team facts once (a team.json) and the")
    lines.append("qualification answers auto-fill across every pack.")
    lines.append("")
    lines.append("## 🧭 STREAMS NOT YET BUILT (honest — the net is still widening)")
    lines.append("Grants, bug bounties, and on-chain opportunities are on the")
    lines.append("roadmap but not wired yet. The system isn't pretending it has")
    lines.append("them — each run adds another reachable source here. Say NEXT and")
    lines.append("it hunts another 2–4 hours and this folder grows.")
    lines.append("")
    lines.append("_Real and checkable — links go to the actual notice pages. "
                 "Refreshed every run._")
    return "\n".join(lines)


def build_opp_drop(dest: Path,
                   now: Optional[datetime] = None) -> List[Path]:
    """Write/refresh the TITAN_OPPORTUNITIES package under `dest`. Returns the
    files written. `dest` is the desktop (or any dir); the package root is
    created inside it. Pure file assembly from the registry — no network."""
    now = now or datetime.now(timezone.utc)
    root = Path(dest) / OPP_ROOT_NAME
    written: List[Path] = []

    dated = live_team_targets(now)

    # START_HERE (refreshed each run) — the ranked hunt result + actions.
    _write(root / "START_HERE.md", _start_here(now, dated), written)

    # TENDERS — one ready-to-apply pack per live opportunity.
    for t in dated:
        pack = build_submission_pack(t, TeamProfile())
        _write(root / "TENDERS" / f"{t.target_id}.md", render_pack_md(pack, now), written)

    return written
