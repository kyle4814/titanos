"""
Portfolio Bundle — assemble the WHOLE tendering portfolio into one folder,
fresh, on demand.

Kyle asked for "the full thing ... everything, all docs ready to go in one
zip" — not the phone digest slice. This module builds that bundle
reproducibly, so every future cycle can hand him a current full portfolio
instead of a one-off. It reuses the existing generators (ops_digest,
close_pack, ops_situation, the dossier CLI, the dashboard script) and
copies the campaign's real documents; it invents nothing.

Layout produced:

    START_HERE.md                      the map + the exact do-first order
    01_PORTFOLIO/                      live opportunities, generated fresh
    02_READY_TO_SEND/                  drafts with [BRACKETS] for Kyle's facts
    03_INTELLIGENCE/                   the full board + decision records + packs
    04_FULL_ARCHIVE/                   every other campaign doc, nothing held back

`build_portfolio_bundle(dest)` returns the list of files written. Zipping
is left to the caller (the CLI does it), so this module opens no archive
format dependency and stays testable offline.
"""

from __future__ import annotations

import datetime
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

from foundation.ops_digest import (
    RULED_OUT,
    STATUS_ORDER,
    format_phone_markdown,
    live_opportunities,
    ruled_out_count,
)

__all__ = ["build_portfolio_bundle", "REPO_ROOT"]

REPO_ROOT = Path(__file__).resolve().parent.parent

_BADGE = {"ACTIONABLE_NOW": "🟢 DO NOW", "ACT_SOON": "🟠 ACT SOON",
          "PURSUE": "🔵 PURSUE", "UNVERIFIED": "🟡 UNVERIFIED",
          "WATCH": "⚪ WATCH"}

# Curated into 03_INTELLIGENCE (the genuinely tendering-useful support docs).
_INTEL_DOCS = (
    "OPS_BOARD.md", "SUBCONTRACT_APPROACH_PACK.md", "SUBCONTRACT_TARGETS_ENGLISH.md",
    "SUBCONTRACT_TARGETS.md", "NZ_ELIGIBILITY.md", "AU_REFEREE_SOLUTION.md",
    "AU_PANEL_CHECKLIST.md", "GRANTS_NO_LICENCE.md", "RUNBOOK_OPPORTUNITY.md",
    "LIVE_TARGET_REQUIREMENTS.md", "HUMAN_LAUNCH_CHECKLIST.md", "BUG_BOUNTY_PLAN.md",
    "BOUNTY_STARTING_POSITION.md", "CAPABILITY_MATRIX.md",
)
# Everything else the campaign produced -> 04_FULL_ARCHIVE (glob prefixes).
_ARCHIVE_GLOBS = ("DEALS_*.md", "HUNT_*.md", "GLOBAL_*.md", "RESOLVED_TARGETS*.md")
_ARCHIVE_NAMED = (
    "DIRECT_INCOME_ROUTES.md", "SOLO_REVENUE_ROUTES.md", "LIVE_PAID_WORK.md",
    "SMALL_CONTRACTS.md", "EU_SMALL_CONTRACTS.md", "UK_SUBTHRESHOLD.md",
    "PRIZE_MARKETS.md", "REMAINING_LIMITATIONS.md", "CASE_STUDY.md",
    "FINAL_LAUNCH_REPORT.md",
)


def _render_start_here() -> str:
    opps = live_opportunities()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%d %B %Y")
    L: List[str] = []
    w = L.append
    w("# 🎯 START HERE — Your Full Tendering Portfolio")
    w("")
    w(f"_Assembled {now}. Everything you need to commit to tendering, in one place._")
    w("")
    w(f"The complete portfolio — not the phone slice. **{len(opps)} live "
      f"opportunities you can move on, {ruled_out_count()} ruled out** (each "
      "with the exact clause that ruled it out, so you can challenge any that "
      "changed).")
    w("")
    w("## ⚡ The one thing that unlocks most of it")
    w("")
    w("Almost every route needs four facts about you the profile is blank on. "
      "Fill these once and most applications become fill-in-the-blanks:")
    w("")
    w("1. **Legal / trading name**  2. **ABN number**  3. **Business address**  "
      "4. **Contact email + phone**")
    w("")
    w("Plus, per tender: your real turnover (or a partner whose turnover you "
      "rely on) and your declared security skills. None of these were invented "
      "— that's why the drafts carry `[BRACKETS]`.")
    w("")
    w("## 📋 The portfolio at a glance")
    w("")
    by: dict = {}
    for o in opps:
        by.setdefault(o.effective_status(), []).append(o)
    for s in STATUS_ORDER:
        if not by.get(s):
            continue
        w(f"### {_BADGE[s]} ({len(by[s])})")
        w("")
        for o in by[s]:
            w(f"- **{o.title}** — {o.value}")
            w(f"  - Gate: {o.gate}")
            w(f"  - Link: {o.link}")
        w("")
    w(f"### ❌ Ruled out ({ruled_out_count()}) — shown so you can challenge them")
    w("")
    w("If a wall changed (you get insurance, a partner covers turnover, you "
      "join a consortium), that one comes back — tell me and I re-add it.")
    w("")
    for r in RULED_OUT:
        w(f"- **{r.title}** ({r.value}) — {r.wall}")
    w("")
    w("## ✅ Do these first (in order)")
    w("")
    w("1. **Send me the 4 facts** — then I generate every application draft.")
    w("2. **Bradford £300k pen-test — closes 14 Sep (a real clock).** Open "
      "`uk.eu-supply.com`, download the ITT, check if CHECK/CREST is required; "
      "if not, bid (OCDS shows no other barrier).")
    w("3. **Register on YesWeHack** (free) — work Ant Group (0 reports) AND file "
      "the ready-made SGSP report in `02_READY_TO_SEND/`.")
    w("4. **Start Synack Red Team** (`synack.com/red-team`) — paid pentest work "
      "vetted by a skills test, no certs/insurance/refs; ~6-month vetting, so "
      "begin now. Apply to Cobalt (`cobalt.io`) in parallel.")
    w("5. **Send the two ready-made inquiries** in `02_READY_TO_SEND/` — NSW "
      "referee question (unlocks a $150k ceiling) and the GNI round check. "
      "Paste your name + ABN into the `[blanks]`.")
    w("")
    w("## 🗂️ What's in this bundle")
    w("")
    w("- **`01_PORTFOLIO/`** — live opportunities, generated fresh: the tappable "
      "`ops_money_printer.html`, `portfolio_full.md`, `close_pack.md` (every "
      "deal at its submit line), `bottleneck_analysis.txt`, "
      "`missing_facts_by_scheme.txt`.")
    w("- **`02_READY_TO_SEND/`** — paste your details into the `[blanks]` and "
      "send: `nsw_referee_email.txt`, `gni_round_question.txt`, "
      "`sgsp_bugbounty_report.md` (a Low *documentation* finding — read its "
      "disclaimer).")
    w("- **`03_INTELLIGENCE/`** — the full `OPS_BOARD.md`, all decision records "
      "(why each route was pursued/closed), the subcontract & eligibility packs.")
    w("- **`04_FULL_ARCHIVE/`** — every other campaign doc. Nothing held back.")
    w("")
    w("## 🔒 One honesty note")
    w("")
    w("Every figure, deadline and clause here was read from a real source, not "
      "invented; unknowns say UNKNOWN. The drafts carry `[BRACKETS]` because a "
      "fake ABN, skill or reference in your name on a real bid is the one thing "
      "that would sink you. Fill the brackets, and it's ready.")
    return "\n".join(L)


def _write(path: Path, text: str, written: List[Path]) -> None:
    path.write_text(text, encoding="utf-8")
    written.append(path)


def _copy(src: Path, dest_dir: Path, written: List[Path]) -> None:
    if src.is_file():
        target = dest_dir / src.name
        shutil.copy2(src, target)
        written.append(target)


def build_portfolio_bundle(dest: Path) -> List[Path]:
    """Assemble the full portfolio under `dest`. Returns files written.
    Generated pieces never depend on external files; document copies are
    best-effort (a missing source doc is skipped, not fatal)."""
    dest = Path(dest)
    for sub in ("01_PORTFOLIO", "02_READY_TO_SEND", "03_INTELLIGENCE",
                "03_INTELLIGENCE/decision_records", "04_FULL_ARCHIVE"):
        (dest / sub).mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    # START_HERE
    _write(dest / "START_HERE.md", _render_start_here(), written)

    # 01 — generated deliverables
    p01 = dest / "01_PORTFOLIO"
    _write(p01 / "portfolio_full.md", format_phone_markdown(), written)
    from foundation.close_pack import render_close_pack, CLOSE_PLANS
    _write(p01 / "close_pack.md", render_close_pack(), written)
    from foundation.ops_situation import analyse_ops_bottleneck, render_bottleneck
    _write(p01 / "bottleneck_analysis.txt",
           render_bottleneck(analyse_ops_bottleneck()), written)
    try:
        from foundation import operator_cli
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            operator_cli.main(["dossier"])
        _write(p01 / "missing_facts_by_scheme.txt", buf.getvalue(), written)
    except Exception:  # pragma: no cover - dossier is best-effort
        pass
    html = p01 / "ops_money_printer.html"
    try:
        subprocess.run([sys.executable, "scripts/build_digest_artifact.py",
                        str(html)], cwd=str(REPO_ROOT), check=True,
                       capture_output=True, timeout=60)
        if html.is_file():
            written.append(html)
    except Exception:  # pragma: no cover - dashboard is best-effort
        pass

    # 02 — ready-to-send drafts
    p02 = dest / "02_READY_TO_SEND"
    for oid, fname in (("NSW_ICT_SCHEME", "nsw_referee_email.txt"),
                       ("IE_GNI_23_049", "gni_round_question.txt")):
        draft = CLOSE_PLANS[oid].draft
        if draft:
            _write(p02 / fname, draft + "\n", written)
    _copy(REPO_ROOT / "SGSP_SUBMISSION_DRAFT.md", p02, written)
    # rename the SGSP copy to a clearer name if it landed
    sgsp = p02 / "SGSP_SUBMISSION_DRAFT.md"
    if sgsp.is_file():
        sgsp.rename(p02 / "sgsp_bugbounty_report.md")
        written[written.index(sgsp)] = p02 / "sgsp_bugbounty_report.md"

    # 03 — intelligence
    p03 = dest / "03_INTELLIGENCE"
    for name in _INTEL_DOCS:
        _copy(REPO_ROOT / name, p03, written)
    dr = REPO_ROOT / "docs" / "DECISIONS"
    if dr.is_dir():
        for f in sorted(dr.glob("*.md")):
            _copy(f, p03 / "decision_records", written)

    # 04 — full archive
    p04 = dest / "04_FULL_ARCHIVE"
    seen = set()
    for pat in _ARCHIVE_GLOBS:
        for f in sorted(REPO_ROOT.glob(pat)):
            if f.name not in seen:
                _copy(f, p04, written)
                seen.add(f.name)
    for name in _ARCHIVE_NAMED:
        if name not in seen:
            _copy(REPO_ROOT / name, p04, written)
            seen.add(name)

    return written
