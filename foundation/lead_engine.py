"""
Lead Engine — turn a list of domains into ranked hot leads.

The first-dollar lever: Kyle is the closer. Feed this the domains of businesses
he can approach (his own leads, a directory, later a lead-source mouth) and it
ranks them by how *spoofable* their email is — a domain with no or weak SPF/
DMARC can have email forged in its name (invoice fraud, phishing its
customers), which is a real, provable, urgent problem and a clean sales hook.
The weakest domains rise to the top: "call these first."

Reads PUBLIC DNS only (via `email_security_report`, through the gated socket) —
no intrusion, no credentials, legal to run on any domain. It ONLY finds and
ranks; the outreach is Kyle's (lawful, his own compliant contact). Honest: it
is an email-security posture signal, not a full audit, and a domain that grades
well is simply not a hot lead — never inflated into one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from foundation.email_security_report import (
    assess_email_security, EmailSecurityReport, Finding,
)

__all__ = ["LeadResult", "triage_domains", "render_lead_sheet_md"]


@dataclass(frozen=True)
class LeadResult:
    domain: str
    grade: str            # from EmailSecurityReport.grade
    spoofable: bool       # can email be forged in their name?
    heat: int             # 0 (cold) .. 3 (on fire) — the ranking key
    gaps: Tuple[str, ...]  # the failing/weak controls, plain-English
    angle: str            # the one-line sales hook (empty if not a lead)


def _finding(report: EmailSecurityReport, check: str) -> Optional[Finding]:
    return next((f for f in report.findings if f.check == check), None)


def _score(report: EmailSecurityReport) -> LeadResult:
    spf = _finding(report, "SPF")
    dmarc = _finding(report, "DMARC")
    spf_s = spf.status if spf else "FAIL"
    dmarc_s = dmarc.status if dmarc else "FAIL"

    # Spoofable if either of the two forgery-stopping controls is absent or weak.
    spoofable = spf_s in ("FAIL", "WARN") or dmarc_s in ("FAIL", "WARN")

    # Heat: two hard FAILs = on fire; one FAIL = hot; only WARNs = warm; clean = cold.
    fails = sum(1 for s in (spf_s, dmarc_s) if s == "FAIL")
    warns = sum(1 for s in (spf_s, dmarc_s) if s == "WARN")
    if fails >= 2:
        heat = 3
    elif fails == 1:
        heat = 2
    elif warns >= 1:
        heat = 1
    else:
        heat = 0

    gaps = tuple(f.detail for f in report.findings
                 if f.check in ("SPF", "DMARC") and f.status in ("FAIL", "WARN"))

    if heat >= 2:
        angle = ("Their email can be SPOOFED — a criminal can send invoices/"
                 "emails that look exactly like them, to their own customers. "
                 "That's fraud waiting to happen, and it's a quick fix you sell.")
    elif heat == 1:
        angle = ("Email security is partial — present but not enforced, so "
                 "forged mail is flagged, not blocked. Worth tightening; a soft "
                 "sell.")
    else:
        angle = ""  # graded well — not a lead, never inflated into one.

    return LeadResult(domain=report.domain, grade=report.grade,
                      spoofable=spoofable, heat=heat, gaps=gaps, angle=angle)


def triage_domains(domains: List[str],
                   fetch_fn: Optional[Callable[[str], bytes]] = None) -> List[LeadResult]:
    """Assess each domain's public email security and return LeadResults sorted
    hottest-first (call the top ones first). `fetch_fn` is injected in tests."""
    results = [_score(assess_email_security(d, fetch_fn))
               for d in domains if str(d).strip()]
    # Hottest first; ties broken by domain for stable output.
    results.sort(key=lambda r: (-r.heat, r.domain))
    return results


_FLAME = {3: "🔥🔥🔥", 2: "🔥🔥", 1: "🔥", 0: "· "}


def render_lead_sheet_md(results: List[LeadResult]) -> str:
    hot = [r for r in results if r.heat >= 2]
    L: List[str] = []
    L.append("# 🎯 LEAD SHEET — ranked by how spoofable their email is")
    L.append("")
    L.append(f"**{len(hot)} hot leads** (spoofable — provable hook) of "
             f"{len(results)} checked. Call the top ones first.")
    L.append("")
    L.append("Reads public DNS only — no hacking, no scanning their systems. "
             "You're checking their public email-security posture (true + legal).")
    L.append("")
    for r in results:
        L.append(f"## {_FLAME[r.heat]} {r.domain} — grade {r.grade}"
                 + ("  ·  SPOOFABLE" if r.spoofable else "  ·  secure"))
        if r.angle:
            L.append(f"- **Hook:** {r.angle}")
        for g in r.gaps:
            L.append(f"  - {g}")
        if not r.angle:
            L.append("- Already secure — not a lead, move on.")
        L.append("")
    L.append("---")
    L.append("*Email-security posture signal, not a full audit. Generate their "
             "full report with `security-report --domain X`. You make the "
             "contact — lawfully, your own compliant outreach.*")
    return "\n".join(L)
