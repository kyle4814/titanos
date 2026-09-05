"""
Email Security Report — the first sellable, fully-automated deliverable.

Kyle's model: the system delivers, Kyle sells and clicks. This is a product
that fits it exactly. Give it a domain and it produces a professional report on
that organisation's public email-security posture — SPF, DMARC, DKIM, DNSSEC,
MX, MTA-STS — every one of which is a real control that real businesses fail and
pay to fix. It reads ONLY public DNS records (no client credentials, no
intrusion, nothing that needs authorisation beyond a public lookup), so it is
safe and legal to run on any domain a client asks about.

HONEST BY CONSTRUCTION:
  - It reads public DNS only. It is an email-security POSTURE check, not a full
    security audit — the report says so. No claim beyond what the records show.
  - A control that is absent is reported as absent (FAIL/spoofable), never
    hand-waved. A control present but weak is a WARN, not a PASS.
  - A control whose DNS lookup FAILED (network error, exhausted query budget)
    is UNKNOWN, never scored as absent — a failed read is not evidence of a
    missing record. A report with any UNKNOWN check grades UNKNOWN, not a
    letter, because it was not fully assessed.
  - Every network read goes through the gated `mouth_common.fetch_feed()` via
    DNS-over-HTTPS (dns.google), so it obeys the same authorization/robots
    discipline as every other fetch in this repo. No raw sockets, no new deps.
  - Tests inject `fetch_fn`; no test touches the network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from foundation.mouth_common import fetch_feed
from foundation.discovery_authorization import DiscoveryPolicy, reset_budgets

__all__ = [
    "Finding",
    "EmailSecurityReport",
    "assess_email_security",
    "render_report_md",
    "DISCOVERY_POLICY",
]

DISCOVERY_POLICY = DiscoveryPolicy(
    objective=("read a domain's public email-security DNS records (SPF, DMARC, "
               "DKIM, DNSSEC, MX, MTA-STS) to produce an email-security posture "
               "report for a client"),
    requested_scope="READ_API",
    # One report issues up to ~17 DoH lookups (DKIM alone probes 12 selectors).
    # The default budget of 5 exhausts mid-report, which — before this was
    # sized correctly — silently failed the later checks (MX, MTA-STS) and
    # scored them as "absent". The budget still bounds ONE report; batch runs
    # reset it per domain (see assess_email_security).
    max_queries=30,
)

_DOH_URL = "https://dns.google/resolve"

# Common DKIM selectors to probe (a domain may use a custom one — absence here
# is reported as "not found at common selectors", never as "no DKIM").
_DKIM_SELECTORS = ("default", "google", "selector1", "selector2", "k1", "mail",
                   "dkim", "s1", "s2", "zoho", "mandrill", "sendgrid")


FetchFn = Callable[[str], bytes]


def _default_fetch(url: str) -> bytes:
    return fetch_feed(url, policy=DISCOVERY_POLICY)


class _LookupFailed(Exception):
    """The DoH read itself failed (network error, exhausted query budget,
    unparseable response). This is NOT the same as a successful lookup that
    returned no records — a failed read is UNKNOWN, an empty read is absent.
    Conflating the two is how a broken fetch manufactures false 'spoofable'
    findings, so the two paths are kept strictly separate."""


def _query(name: str, rrtype: str, fetch: FetchFn) -> dict:
    """One DoH query. Returns the parsed JSON dict (with Answer/AD/Status)
    on success — including a valid response that simply has no Answer.
    Raises `_LookupFailed` if the fetch or JSON parse fails, so a caller can
    tell 'record absent' from 'could not read'."""
    url = f"{_DOH_URL}?name={name}&type={rrtype}"
    try:
        raw = fetch(url)
    except Exception as e:
        raise _LookupFailed(f"fetch failed for {name}/{rrtype}: {e}") from e
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise _LookupFailed(f"unparseable DoH response for {name}/{rrtype}: {e}") from e


def _txt_records(name: str, fetch: FetchFn) -> List[str]:
    d = _query(name, "TXT", fetch)
    out: List[str] = []
    for a in d.get("Answer", []) or []:
        val = str(a.get("data", "")).strip()
        # DoH returns TXT wrapped in quotes; concatenate multi-string TXT.
        val = val.replace('" "', "").strip('"')
        if val:
            out.append(val)
    return out


@dataclass(frozen=True)
class Finding:
    check: str          # e.g. "SPF"
    status: str         # PASS / WARN / FAIL
    detail: str         # what was found
    fix: str            # plain-English remediation ("" if PASS)


def _spf(domain: str, fetch: FetchFn) -> Finding:
    spf = next((r for r in _txt_records(domain, fetch)
                if r.lower().startswith("v=spf1")), None)
    if spf is None:
        return Finding("SPF", "FAIL",
                       "No SPF record — anyone can forge email from this domain.",
                       "Publish an SPF TXT record listing your mail senders, "
                       "ending in -all (hard fail).")
    low = spf.lower()
    if low.rstrip().endswith("-all"):
        return Finding("SPF", "PASS", f"Strong SPF (hard fail): {spf}", "")
    if "~all" in low or "?all" in low or low.rstrip().endswith("all"):
        return Finding("SPF", "WARN",
                       f"SPF present but soft/neutral, not enforced: {spf}",
                       "Change the SPF record's ending to -all so forged mail is "
                       "rejected, not just flagged.")
    return Finding("SPF", "WARN", f"SPF present, no explicit all mechanism: {spf}",
                   "Add a -all mechanism to the end of the SPF record.")


def _dmarc_policy(rec: str) -> str:
    """The value of the DMARC `p=` (domain policy) tag, lowercased, or "".
    Parses the actual tag — NOT a substring match, which would read `p=reject`
    out of the `sp=reject` (subdomain policy) tag. Found live against a domain
    whose record was `p=quarantine; sp=reject`."""
    for part in rec.split(";"):
        if "=" in part:
            key, val = part.split("=", 1)
            if key.strip().lower() == "p":
                return val.strip().lower()
    return ""


def _dmarc(domain: str, fetch: FetchFn) -> Finding:
    rec = next((r for r in _txt_records(f"_dmarc.{domain}", fetch)
                if r.lower().startswith("v=dmarc1")), None)
    if rec is None:
        return Finding("DMARC", "FAIL",
                       "No DMARC record — no policy telling receivers what to do "
                       "with forged mail, and no visibility of abuse.",
                       "Publish a _dmarc TXT record, start at p=none with rua "
                       "reporting, then move to p=quarantine and p=reject.")
    policy = _dmarc_policy(rec)
    if policy == "reject":
        return Finding("DMARC", "PASS", f"Enforcing DMARC (p=reject): {rec}", "")
    if policy == "quarantine":
        return Finding("DMARC", "WARN",
                       f"DMARC quarantining, not rejecting (p=quarantine): {rec}",
                       "Once reports look clean, move the policy to p=reject.")
    return Finding("DMARC", "WARN",
                   f"DMARC in monitor-only mode (p={policy or 'none'}): {rec}",
                   "p=none only watches — move to p=quarantine then p=reject to "
                   "actually block forged mail.")


def _dkim(domain: str, fetch: FetchFn) -> Finding:
    found = []
    for sel in _DKIM_SELECTORS:
        d = _query(f"{sel}._domainkey.{domain}", "TXT", fetch)
        recs = [str(a.get("data", "")) for a in d.get("Answer", []) or []]
        if any("v=dkim1" in r.lower() or "k=rsa" in r.lower() or "p=" in r
               for r in recs):
            found.append(sel)
    if found:
        return Finding("DKIM", "PASS",
                       f"DKIM signing keys found (selectors: {', '.join(found)}).", "")
    return Finding("DKIM", "WARN",
                   "No DKIM key found at common selectors (a custom selector may "
                   "be in use — confirm with the mail provider).",
                   "Enable DKIM signing with your mail provider and publish the "
                   "key, so receivers can cryptographically verify your mail.")


def _dnssec(domain: str, fetch: FetchFn) -> Finding:
    d = _query(domain, "DS", fetch)
    if d.get("Answer"):
        return Finding("DNSSEC", "PASS",
                       "DNSSEC enabled (DS record present) — DNS answers are "
                       "signed and tamper-evident.", "")
    return Finding("DNSSEC", "WARN",
                   "DNSSEC not enabled — DNS responses are not cryptographically "
                   "signed.",
                   "Enable DNSSEC at your DNS host to protect against DNS "
                   "spoofing/cache poisoning.")


def _mx(domain: str, fetch: FetchFn) -> Finding:
    d = _query(domain, "MX", fetch)
    ans = d.get("Answer", []) or []
    if ans:
        hosts = ", ".join(sorted({str(a.get("data", "")).split()[-1].rstrip(".")
                                  for a in ans if a.get("data")}))
        return Finding("MX", "PASS", f"Mail servers configured: {hosts}", "")
    return Finding("MX", "WARN",
                   "No MX records — this domain does not receive email (or is "
                   "misconfigured).",
                   "If this domain should receive mail, add MX records.")


def _mta_sts(domain: str, fetch: FetchFn) -> Finding:
    rec = next((r for r in _txt_records(f"_mta-sts.{domain}", fetch)
                if r.lower().startswith("v=stsv1")), None)
    if rec:
        return Finding("MTA-STS", "PASS",
                       "MTA-STS present — enforces TLS on inbound mail.", "")
    return Finding("MTA-STS", "WARN",
                   "No MTA-STS — inbound mail can be delivered over unencrypted "
                   "connections.",
                   "Publish an MTA-STS policy to require TLS for mail to your "
                   "domain (optional, best-practice).")


# Order shown in the report: the spoofing-critical three first.
_CHECKS = (_spf, _dmarc, _dkim, _dnssec, _mx, _mta_sts)
# Weight the report grade toward the controls that actually stop spoofing.
_CRITICAL = {"SPF", "DMARC", "DKIM"}


@dataclass(frozen=True)
class EmailSecurityReport:
    domain: str
    findings: Tuple[Finding, ...]

    @property
    def grade(self) -> str:
        # A report that could not complete every check was not fully assessed;
        # it does not get a confident letter. UNKNOWN is not FAIL — a failed
        # lookup is never scored as a spoofable gap.
        if any(f.status == "UNKNOWN" for f in self.findings):
            return "UNKNOWN — lookup incomplete, not assessed"
        crit = [f for f in self.findings if f.check in _CRITICAL]
        crit_fail = sum(1 for f in crit if f.status == "FAIL")
        crit_warn = sum(1 for f in crit if f.status == "WARN")
        any_fail = any(f.status == "FAIL" for f in self.findings)
        if crit_fail == 0 and crit_warn == 0 and not any_fail:
            return "A — strong"
        if crit_fail == 0 and crit_warn <= 1:
            return "B — good, minor gaps"
        if crit_fail <= 1:
            return "C — real gaps, spoofable"
        return "D — high risk, easily spoofed"

    @property
    def fails(self) -> Tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.status == "FAIL")


_CHECK_LABELS = {
    _spf: "SPF", _dmarc: "DMARC", _dkim: "DKIM",
    _dnssec: "DNSSEC", _mx: "MX", _mta_sts: "MTA-STS",
}


def _run_check(check: "Callable", domain: str, fetch: FetchFn) -> Finding:
    """Run one check; if the DNS read failed, return UNKNOWN rather than
    letting an absent-record path score a lookup failure as a finding."""
    try:
        return check(domain, fetch)
    except _LookupFailed as e:
        return Finding(_CHECK_LABELS[check], "UNKNOWN",
                       f"DNS lookup failed for this check — status not assessed "
                       f"({e}).", "")


def assess_email_security(domain: str,
                          fetch_fn: Optional[FetchFn] = None,
                          reset_budget: bool = True) -> EmailSecurityReport:
    domain = domain.strip().lower().rstrip(".")
    fetch = fetch_fn or _default_fetch
    # A batch caller assesses many domains in one process. The discovery
    # budget accumulates per policy across the whole process, so without a
    # per-report reset every domain after the budget cap would fail. Reset
    # only applies to the real gated fetch — an injected fetch_fn has no
    # budget and needs no reset (keeps tests isolated from the ledger).
    if fetch_fn is None and reset_budget:
        reset_budgets()
    findings = tuple(_run_check(check, domain, fetch) for check in _CHECKS)
    return EmailSecurityReport(domain=domain, findings=findings)


_MARK = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "UNKNOWN": "❔"}


def render_report_md(report: EmailSecurityReport) -> str:
    L: List[str] = []
    L.append(f"# Email Security Report — {report.domain}")
    L.append("")
    L.append(f"**Overall grade: {report.grade}**")
    L.append("")
    L.append("What this checks: your domain's public email-security controls — "
             "the settings that decide whether criminals can send email that "
             "looks like it came from you (spoofing / phishing / invoice fraud).")
    L.append("")
    L.append("| Check | Status | Finding |")
    L.append("|---|---|---|")
    for f in report.findings:
        L.append(f"| **{f.check}** | {_MARK[f.status]} {f.status} | {f.detail} |")
    L.append("")
    actions = [f for f in report.findings if f.status in ("FAIL", "WARN") and f.fix]
    if actions:
        L.append("## What to fix (in priority order)")
        crit = [f for f in actions if f.check in _CRITICAL]
        rest = [f for f in actions if f.check not in _CRITICAL]
        for i, f in enumerate(crit + rest, 1):
            L.append(f"{i}. **{f.check}** — {f.fix}")
    else:
        L.append("## No action needed — email security controls are strong. ✅")
    L.append("")
    L.append("---")
    L.append("*Scope: this report reads public DNS records only. It is an "
             "email-security posture check, not a full security audit or "
             "penetration test. Findings reflect the domain's DNS at the time of "
             "the check.*")
    return "\n".join(L)
