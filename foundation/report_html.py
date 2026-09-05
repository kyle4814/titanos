"""
SpoofGuard client-facing HTML report — the deliverable a prospect actually sees.

`email_security_report.render_report_md()` is fine for a terminal; a business
owner responds to a clean, self-contained report they can open in any browser or
receive by email. This composes the same graded posture + the same safe
remediation records into one HTML file with NO external resources (inline CSS,
no fonts, no scripts, no images) so it renders identically offline, in an email
client, or on a phone, and can be sent as a single attachment.

HONEST BY CONSTRUCTION, same as the rest of SpoofGuard:
  - Every value shown comes from the report; nothing is invented.
  - An UNKNOWN (incomplete) scan renders as UNKNOWN, never a confident grade.
  - The exact records are the safe ones remediation.py generates (SPF softfail,
    staged DMARC, provider-aware) — the HTML only presents them.
  - All dynamic text is HTML-escaped: a domain or DNS string cannot inject markup.
  - The scope disclaimer (posture check, not a full audit) travels with it.
"""

from __future__ import annotations

from html import escape
from typing import List

from foundation.email_security_report import EmailSecurityReport
from foundation.remediation import build_remediation, RemediationPlan


# Grade letter -> (accent colour, plain-English one-liner). Neutral, brandable.
_GRADE_STYLE = {
    "A": ("#1a7f4b", "Strong — email spoofing is well defended."),
    "B": ("#3d7a1f", "Good, with minor gaps worth closing."),
    "C": ("#b8860b", "Real gaps — this domain can be spoofed."),
    "D": ("#b3261e", "High risk — email can be forged in your name right now."),
    "U": ("#5a5a5a", "Not assessed — some DNS lookups did not complete."),
}

_STATUS_STYLE = {
    "PASS": ("#1a7f4b", "PASS"),
    "WARN": ("#b8860b", "WARN"),
    "FAIL": ("#b3261e", "FAIL"),
    "UNKNOWN": ("#5a5a5a", "UNKNOWN"),
}


def _grade_key(report: EmailSecurityReport) -> str:
    g = report.grade[0]
    return g if g in ("A", "B", "C", "D") else "U"


def _records_rows(plan: RemediationPlan) -> List[str]:
    rows = []
    for r in plan.records:
        rows.append(
            "<tr>"
            f"<td class=\"mono\">{escape(r.host)}</td>"
            f"<td>{escape(r.rtype)}</td>"
            f"<td class=\"mono val\">{escape(r.value)}</td>"
            "</tr>")
    return rows


def render_report_html(report: EmailSecurityReport,
                       title: str = "Email Security Report") -> str:
    """A complete, self-contained HTML report for one domain: grade, what is
    exposed, and the exact records to publish to fix it."""
    domain = escape(report.domain)
    gk = _grade_key(report)
    accent, gradeline = _GRADE_STYLE[gk]
    plan = build_remediation(report)

    finding_rows = []
    for f in report.findings:
        colour, label = _STATUS_STYLE.get(f.status, _STATUS_STYLE["UNKNOWN"])
        finding_rows.append(
            "<tr>"
            f"<td class=\"chk\">{escape(f.check)}</td>"
            f"<td><span class=\"pill\" style=\"background:{colour}\">{label}</span></td>"
            f"<td>{escape(f.detail)}</td>"
            "</tr>")

    records_section = ""
    if plan.records:
        rows = "\n".join(_records_rows(plan))
        provider = (f"Detected mail provider: <strong>{escape(plan.provider.name)}</strong>."
                    if plan.provider else
                    "Mail provider not recognised — the records below are a safe "
                    "template; add your real senders before publishing.")
        warn = ""
        if plan.warnings:
            items = "".join(f"<li>{escape(w)}</li>" for w in plan.warnings)
            warn = f"<div class=\"warn\"><strong>Before you publish</strong><ul>{items}</ul></div>"
        records_section = f"""
    <section>
      <h2>How to fix it — records to publish</h2>
      <p>{provider}</p>
      <table class="records">
        <thead><tr><th>Name / host</th><th>Type</th><th>Value to paste</th></tr></thead>
        <tbody>
{rows}
        </tbody>
      </table>
      <p class="note">SPF is set to <span class="mono">~all</span> (softfail, never
      hardfail) and DMARC starts at <span class="mono">p=none</span> (monitor) so
      publishing these will not bounce your legitimate mail. Tighten only after
      your reports read clean.</p>
      {warn}
    </section>"""

    body = f"""
  <header class="hero">
    <div class="grade" style="border-color:{accent};color:{accent}">
      {escape(report.grade.split(' ')[0])}
    </div>
    <div class="head-text">
      <h1>Email security: {domain}</h1>
      <p class="lead" style="color:{accent}">{escape(gradeline)}</p>
    </div>
  </header>

  <section>
    <h2>What this checks</h2>
    <p>The public DNS settings that decide whether a criminal can send email that
    looks exactly like it came from {domain} — the fake-invoice and phishing risk
    to your own customers and suppliers.</p>
    <table class="findings">
      <thead><tr><th>Control</th><th>Status</th><th>What we found</th></tr></thead>
      <tbody>
{chr(10).join(finding_rows)}
      </tbody>
    </table>
  </section>
{records_section}

  <footer>
    <p>Generated from {domain}'s public DNS records only — no scanning of your
    systems, no credentials, nothing collected. This is an email-security posture
    check, not a full security audit or penetration test; it reflects your DNS at
    the time of the check.</p>
  </footer>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — {domain}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#f6f7f9; color:#1a1c1e;
         font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  .wrap {{ max-width:760px; margin:0 auto; padding:28px 20px 56px; }}
  .hero {{ display:flex; gap:20px; align-items:center; background:#fff;
          border:1px solid #e3e6ea; border-radius:14px; padding:22px 24px; margin-bottom:22px; }}
  .grade {{ flex:0 0 auto; width:74px; height:74px; border:3px solid; border-radius:14px;
           display:flex; align-items:center; justify-content:center;
           font-size:34px; font-weight:800; letter-spacing:-1px; }}
  h1 {{ font-size:22px; margin:0 0 4px; letter-spacing:-.3px; }}
  .lead {{ margin:0; font-weight:600; }}
  section {{ background:#fff; border:1px solid #e3e6ea; border-radius:14px;
            padding:20px 24px; margin-bottom:18px; }}
  h2 {{ font-size:16px; margin:0 0 12px; }}
  table {{ width:100%; border-collapse:collapse; font-size:14.5px; }}
  th {{ text-align:left; color:#5a5f66; font-weight:600; border-bottom:2px solid #eceef1;
       padding:8px 10px; }}
  td {{ padding:9px 10px; border-bottom:1px solid #f0f2f4; vertical-align:top; }}
  .chk {{ font-weight:600; white-space:nowrap; }}
  .pill {{ color:#fff; font-size:12px; font-weight:700; padding:2px 9px; border-radius:20px;
          letter-spacing:.4px; }}
  .mono {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:13px; }}
  .val {{ word-break:break-all; background:#f4f6f8; }}
  .records td {{ background:#fbfcfd; }}
  .note {{ color:#5a5f66; font-size:13.5px; margin:12px 0 0; }}
  .warn {{ margin-top:14px; padding:12px 14px; border-radius:10px;
          background:#fff6e6; border:1px solid #f0d79a; font-size:14px; }}
  .warn ul {{ margin:6px 0 0; padding-left:18px; }}
  footer {{ color:#6b7076; font-size:12.5px; padding:4px 6px; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background:#15171a; color:#e6e8ea; }}
    .hero, section {{ background:#1e2125; border-color:#2c3037; }}
    th {{ color:#9aa0a6; border-bottom-color:#2c3037; }}
    td {{ border-bottom-color:#24272c; }}
    .val, .records td {{ background:#24272c; }}
    .note, footer {{ color:#9aa0a6; }}
    .warn {{ background:#2a2412; border-color:#4a3f18; }}
  }}
</style>
</head>
<body>
  <div class="wrap">
{body}
  </div>
</body>
</html>"""
