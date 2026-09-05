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


def _cold_call_kit(sample_domain: str) -> str:
    return f"""# SELL TITANOS.TECH — cold-call kit

You sell, the system delivers. The hook is dead simple: nearly every small
business has **spoofable email** (no or weak SPF/DMARC), and that is invoice
fraud and phishing waiting to happen. You run a free 60-second public check,
show them they're exposed, and sell the fix + ongoing monitoring.

## The 30-second pitch
"Hi, I'm [name] from Titanos. I run cyber security for small businesses. I did
a free public check on your email security and found your domain can be
**spoofed** — someone can send email that looks exactly like it's from you, to
your customers. It's a common gap and it's a quick fix. Can I send you the
one-page report, no charge?"

Then: they say yes → you email the report (you already have it) → you follow up
to sell the fix (you set up SPF/DMARC/DKIM properly) + a monthly monitoring
retainer.

## How to generate a prospect's report (ONE command)
Before or after the call, run this on their domain — it reads PUBLIC DNS only,
nothing intrusive, totally legal:

    python3 -m foundation.operator_cli security-report --domain THEIRDOMAIN.com --out report.md

You get a professional graded report (A–D) with the exact gaps and fixes. That
report IS the product you're selling the fix for. A domain that grades C or D
is a hot lead — they're exposed and you can prove it.

## What you're selling (three tiers)
1. **The fix** (one-off): set up SPF, DMARC, DKIM properly. A few hundred $.
2. **Monitoring** (retainer): monthly re-check + report. Recurring $.
3. **Full email-security posture** for bigger clients.

## Rules (keep it clean)
- The report reads PUBLIC records only — never say you "hacked" or "scanned
  their systems." You checked their public email security posture. True + safe.
- Don't overclaim. It's an email-security check, not a full audit. The report
  says so.
- A prospect who grades A: thank them, they're already sorted — move on.

## Sample to show them
See `sample_report.md` in this folder — a real report generated for {sample_domain}.
Send prospects theirs, not this one.
"""


def _start_here(now: datetime, dated, n_tenders: int) -> str:
    soon = [t for t in dated if t.deadline_date()][:3]
    lines: List[str] = []
    lines.append(f"# 🐕 TITAN — START HERE  ({now:%a %d %b %Y})")
    lines.append("")
    lines.append("The system hunted while you slept. Here's what to work today.")
    lines.append("You sell and click; the system already did the finding + prep.")
    lines.append("")
    lines.append("## 🔥 DO FIRST — sell titanos.tech (fastest cash)")
    lines.append("- Open `SELL_TITANOS/COLD_CALL_KIT.md` — the pitch + script.")
    lines.append("- Pick businesses to call. For each, run one command to get")
    lines.append("  their free email-security report (the hook):")
    lines.append("      python3 -m foundation.operator_cli security-report --domain THEIRDOMAIN.com --out report.md")
    lines.append("- A domain grading C or D = spoofable = hot lead. Sell the fix.")
    lines.append("")
    lines.append(f"## 📄 TENDERS — {n_tenders} live, packs ready in TENDERS/")
    lines.append("Each file has the portal, login, steps, and upload checklist.")
    lines.append("Fill your team facts once (a team.json) and the ESPD answers")
    lines.append("auto-fill. Soonest deadlines:")
    for t in soon:
        lines.append(f"- **{t.deadline_date()}** — {t.title} ({t.value}) → `TENDERS/{t.target_id}.md`")
    lines.append("")
    lines.append("## 🧭 STREAMS NOT YET BUILT (honest)")
    lines.append("Grants and on-chain/OSINT streams are on the roadmap but not")
    lines.append("wired yet — the system isn't pretending it has them. Each future")
    lines.append("run aims to add reachable streams here.")
    lines.append("")
    lines.append("_Everything here is real and checkable — links go to the actual")
    lines.append("government/vendor pages. Nothing was invented. Refreshed every run._")
    return "\n".join(lines)


def build_opp_drop(dest: Path,
                   now: Optional[datetime] = None,
                   sample_domain: str = "github.com",
                   include_sample: bool = True) -> List[Path]:
    """Write/refresh the TITAN_OPPORTUNITIES package under `dest`. Returns the
    files written. `dest` is the desktop (or any dir); the package root is
    created inside it. `include_sample=False` skips the live-DNS sample report
    (used by tests, which never touch the network)."""
    now = now or datetime.now(timezone.utc)
    root = Path(dest) / OPP_ROOT_NAME
    written: List[Path] = []

    dated = live_team_targets(now)

    # START_HERE (refreshed each run)
    _write(root / "START_HERE.md", _start_here(now, dated, len(dated)), written)

    # TENDERS — one ready-to-file pack per live tender
    for t in dated:
        pack = build_submission_pack(t, TeamProfile())
        _write(root / "TENDERS" / f"{t.target_id}.md", render_pack_md(pack, now), written)

    # SELL_TITANOS — the cold-call kit + a real sample report
    _write(root / "SELL_TITANOS" / "COLD_CALL_KIT.md",
           _cold_call_kit(sample_domain), written)
    if not include_sample:
        return written
    try:
        from foundation.email_security_report import (
            assess_email_security, render_report_md)
        sample = render_report_md(assess_email_security(sample_domain))
        _write(root / "SELL_TITANOS" / "sample_report.md", sample, written)
    except Exception:
        # Sample needs a live DNS read; if unavailable, skip it (the kit still
        # tells him the command to generate one). Never write a fake sample.
        pass

    return written
