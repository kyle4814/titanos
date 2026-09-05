"""
SpoofGuard remediation — generate the EXACT DNS records a domain should publish
to stop email spoofing, safely.

This is the step most tools skip: not "you failed DMARC", but "publish this
record". It is also the DANGEROUS step — a wrong SPF or DMARC record can bounce
a business's legitimate mail. So the whole module is built around not breaking
a live mail service:

SAFETY BY CONSTRUCTION:
  - SPF starts at ~all (softfail), NEVER -all. We cannot be certain we have
    enumerated every legitimate sender (CRM, newsletter tool, website form), and
    -all tells the world to REJECT anything we missed. Softfail first; tighten
    to -all only after the owner has confirmed their senders. The plan says so.
  - DMARC is STAGED: p=none (monitor) -> p=quarantine -> p=reject. We never emit
    p=reject as the record to publish today when a domain starts from nothing —
    that jump bounces legit mail during any misconfiguration. p=none breaks
    nothing and starts collecting evidence.
  - Provider is detected from real MX hosts. If the provider is not recognised,
    we DO NOT fabricate an SPF include — we emit a template with a placeholder
    and a warning to add the domain's real senders. UNKNOWN, never invented.
  - DKIM keys are provider-specific and cannot be generated here. We emit the
    instruction to enable DKIM at the provider and publish the key THEY give —
    never a fabricated key.
  - A record is only proposed for a control that is actually absent/weak. We do
    not tell an owner to "fix" something already passing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from foundation.email_security_report import EmailSecurityReport, Finding


# MX host substring -> (provider name, SPF include mechanism). Deliberately a
# small, well-known, verifiable set. Anything not here is UNKNOWN, not guessed.
_PROVIDERS: Tuple[Tuple[str, str, str], ...] = (
    ("google.com",             "Google Workspace / Gmail",    "include:_spf.google.com"),
    ("googlemail.com",         "Google Workspace / Gmail",    "include:_spf.google.com"),
    ("protection.outlook.com", "Microsoft 365 / Outlook",     "include:spf.protection.outlook.com"),
    ("zoho.com",               "Zoho Mail",                   "include:zoho.com"),
    ("zoho.eu",                "Zoho Mail (EU)",              "include:zoho.eu"),
    ("protonmail",             "Proton Mail",                 "include:_spf.protonmail.ch"),
    ("proton.me",              "Proton Mail",                 "include:_spf.protonmail.ch"),
    ("messagingengine.com",    "Fastmail",                    "include:spf.messagingengine.com"),
    ("icloud.com",             "Apple iCloud Mail",           "include:icloud.com"),
    ("mimecast.com",           "Mimecast",                    "include:_netblocks.mimecast.com"),
    ("pphosted.com",           "Proofpoint",                  "include:_spf.pphosted.com"),
)


@dataclass(frozen=True)
class Provider:
    name: str
    spf_include: str  # e.g. "include:_spf.google.com"


@dataclass(frozen=True)
class DnsRecord:
    """One concrete record to publish. `host` is the DNS name, `rtype` the
    record type, `value` the exact string to paste at the DNS host."""
    host: str
    rtype: str
    value: str
    note: str = ""


@dataclass
class RemediationPlan:
    domain: str
    provider: Optional[Provider]          # None = UNKNOWN, never invented
    records: List[DnsRecord] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)   # non-DNS steps (DKIM at provider)
    rollout: List[str] = field(default_factory=list)        # the staged DMARC path
    warnings: List[str] = field(default_factory=list)

    @property
    def nothing_to_fix(self) -> bool:
        return not self.records and not self.instructions


def _finding(report: EmailSecurityReport, check: str) -> Optional[Finding]:
    return next((f for f in report.findings if f.check == check), None)


def _mx_hosts_from_report(report: EmailSecurityReport) -> List[str]:
    mx = _finding(report, "MX")
    if not mx or mx.status != "PASS":
        return []
    # detail: "Mail servers configured: host1, host2"
    if ":" in mx.detail:
        tail = mx.detail.split(":", 1)[1]
        return [h.strip().lower() for h in tail.split(",") if h.strip()]
    return []


def detect_provider(mx_hosts: List[str]) -> Optional[Provider]:
    """Identify the mail provider from real MX hosts, or None if unrecognised.
    Never guesses — an unknown provider is UNKNOWN, so no SPF include is
    fabricated for it."""
    for host in mx_hosts:
        h = host.lower()
        for needle, name, include in _PROVIDERS:
            if needle in h:
                return Provider(name=name, spf_include=include)
    return None


def build_remediation(report: EmailSecurityReport,
                      mx_hosts: Optional[List[str]] = None) -> RemediationPlan:
    """Produce the exact records to publish, safely, for whatever is actually
    absent/weak in `report`. See the module docstring for the safety rules."""
    domain = report.domain
    hosts = mx_hosts if mx_hosts is not None else _mx_hosts_from_report(report)
    provider = detect_provider(hosts)
    plan = RemediationPlan(domain=domain, provider=provider)

    spf = _finding(report, "SPF")
    dmarc = _finding(report, "DMARC")
    dkim = _finding(report, "DKIM")

    # A report that could not be read (UNKNOWN) is not a basis for remediation.
    if report.grade.startswith("UNKNOWN"):
        plan.warnings.append(
            "The security scan did not complete (some DNS lookups failed), so no "
            "remediation is generated — re-run the check first. A partial read is "
            "never used to propose changes.")
        return plan

    # ---- SPF ----------------------------------------------------------------
    if spf and spf.status in ("FAIL", "WARN"):
        if provider:
            value = f"v=spf1 {provider.spf_include} ~all"
            note = (f"Softfail (~all), not hardfail (-all), on purpose: it will "
                    f"not bounce a legitimate sender you may have missed. Built "
                    f"for {provider.name} (from your MX).")
        else:
            value = "v=spf1 ~all"
            note = ("Provider not recognised from MX, so no sender is assumed. "
                    "ADD your real senders before publishing — e.g. "
                    "include:<your-mail-provider> and any app that sends as you "
                    "(CRM, newsletter, website form) — then keep ~all for now.")
            plan.warnings.append(
                "SPF: mail provider UNKNOWN — the SPF record is a template. Do "
                "NOT publish it until you have added every service that sends "
                "email as this domain, or you may block your own mail.")
        plan.records.append(DnsRecord(host=domain, rtype="TXT", value=value, note=note))
        plan.rollout.append(
            "SPF: publish the ~all record now; once mail flows clean for ~2 weeks "
            "and you're sure every sender is listed, tighten ~all to -all.")

    # ---- DMARC (staged) -----------------------------------------------------
    if dmarc and dmarc.status in ("FAIL", "WARN"):
        # Determine the safe NEXT stage, never jumping straight to reject.
        detail = (dmarc.detail or "").lower()
        starting_from_reject_ready = "p=quarantine" in detail
        if starting_from_reject_ready:
            value = f"v=DMARC1; p=reject; rua=mailto:dmarc@{domain}"
            note = ("You already quarantine — the safe next step is reject. "
                    "Confirm your aggregate (rua) reports are clean first.")
        else:
            value = f"v=DMARC1; p=none; rua=mailto:dmarc@{domain}"
            note = ("Stage 1: MONITOR only. p=none changes nothing about delivery "
                    "— it just starts collecting reports of who sends as you. "
                    "Safe to publish today.")
        plan.records.append(
            DnsRecord(host=f"_dmarc.{domain}", rtype="TXT", value=value, note=note))
        plan.rollout.append(
            "DMARC: p=none (monitor) -> after ~2-4 weeks of clean rua reports -> "
            "p=quarantine (optionally pct=25 then ramp) -> p=reject. Never skip "
            "straight to reject.")
        plan.instructions.append(
            f"Set up a mailbox or DMARC report service to receive reports at "
            f"dmarc@{domain} (or change the rua address to one you read).")

    # ---- DKIM (cannot generate a key here) ----------------------------------
    if dkim and dkim.status in ("FAIL", "WARN"):
        if provider:
            plan.instructions.append(
                f"DKIM: enable DKIM signing in your {provider.name} admin console; "
                f"it will give you a selector and a public key to publish as a TXT "
                f"record (e.g. selector._domainkey.{domain}). The key is generated "
                f"by the provider — it cannot be made up here.")
        else:
            plan.instructions.append(
                f"DKIM: enable DKIM at your mail provider; publish the selector and "
                f"public key THEY generate at <selector>._domainkey.{domain}. The "
                f"key must come from your provider, never a generated placeholder.")

    return plan


def render_remediation_md(plan: RemediationPlan) -> str:
    L: List[str] = []
    L.append(f"# How to stop email spoofing on {plan.domain}")
    L.append("")
    if plan.provider:
        L.append(f"Detected mail provider: **{plan.provider.name}** (from your MX records).")
    else:
        L.append("Mail provider: **not recognised** from your MX — records below "
                 "are templates, read the warnings before publishing.")
    L.append("")
    if plan.nothing_to_fix:
        if plan.warnings:
            L.extend(f"> ⚠️ {w}" for w in plan.warnings)
        else:
            L.append("✅ Nothing to fix — the spoofing-critical controls are already in place.")
        return "\n".join(L)

    if plan.records:
        L.append("## Records to publish at your DNS host")
        L.append("")
        L.append("| Name / host | Type | Value to paste |")
        L.append("|---|---|---|")
        for r in plan.records:
            L.append(f"| `{r.host}` | {r.rtype} | `{r.value}` |")
        L.append("")
        for r in plan.records:
            if r.note:
                L.append(f"- **{r.host}** — {r.note}")
        L.append("")

    if plan.instructions:
        L.append("## Steps at your mail provider")
        for i in plan.instructions:
            L.append(f"- {i}")
        L.append("")

    if plan.rollout:
        L.append("## Safe rollout (do not rush the last step)")
        for s in plan.rollout:
            L.append(f"- {s}")
        L.append("")

    if plan.warnings:
        L.append("## ⚠️ Before you publish")
        for w in plan.warnings:
            L.append(f"- {w}")
        L.append("")

    L.append("---")
    L.append("*Generated from your public DNS. Publishing DNS records affects "
             "mail delivery — apply during business hours and watch your mail "
             "flow. This is safe guidance, not a guarantee about your specific "
             "sender setup, which only you can confirm.*")
    return "\n".join(L)
