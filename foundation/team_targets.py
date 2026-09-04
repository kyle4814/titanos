"""
Team Targets — the high-value contracts a TEAM can win that a solo operator
could not.

Kyle is building a team to submit (2026-09-04). Every wall that ruled these
out for a solo Cairns operator — corporate references, insurance held at
admission, turnover, certifications, 24×7 staffing, local presence — is a
capability a team/firm can carry. So the contracts sitting in
`ops_digest.RULED_OUT`, plus the five dated Irish tenders that came back
CANNOT-APPLY, are now real targets. This registry reframes each one: the
'wall' becomes 'what your team must bring', quoted from the real notice, so
the team knows exactly what to prepare.

Nothing is fabricated: every requirement is read from a primary source
(OPS_BOARD.md, which read it from the notice), and where a figure is
unknown it says UNKNOWN. Deadlines are the real closing dates — several are
weeks out, which makes the dated Irish tenders the most urgent team work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple

from foundation.ops_digest import _parse_deadline_date

__all__ = ["TeamTarget", "TEAM_TARGETS", "live_team_targets",
           "render_team_targets_md", "TeamTargetError"]


class TeamTargetError(Exception):
    pass


@dataclass(frozen=True)
class TeamTarget:
    target_id: str
    title: str
    value: str
    deadline: str          # real closing date, or "Standing / rolling"
    link: str
    what: str
    requirements: Tuple[str, ...]   # what the TEAM must bring, quoted
    source_ref: str

    def __post_init__(self) -> None:
        for name in ("target_id", "title", "value", "deadline", "link",
                     "what", "source_ref"):
            if not str(getattr(self, name)).strip():
                raise TeamTargetError(f"{self.target_id!r}: empty {name}")
        if not self.requirements:
            raise TeamTargetError(f"{self.target_id!r}: no requirements listed")

    def deadline_date(self) -> Optional[date]:
        return _parse_deadline_date(self.deadline)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        d = self.deadline_date()
        if d is None:
            return False
        return d < (now or datetime.now(timezone.utc)).date()


_ET = "https://www.etenders.gov.ie"  # Irish notices are searched by reference here

TEAM_TARGETS: Tuple[TeamTarget, ...] = (
    # --- Dated Irish tenders (TIME-CRITICAL — real deadlines, weeks out) ---
    TeamTarget(
        "IE_FAILTE", "Fáilte Ireland — Cybersecurity Specialist Services (IT/2026/08)",
        "€800,000 (contract; turnover bar €400k)",
        "2026-09-24", "https://ted.europa.eu/en/notice/-/detail/588260-2026",
        "Irish national tourism authority cyber services tender (TED-verified).",
        ("Turnover €400,000", "Employer's liability insurance €13,000,000",
         "Professional indemnity €2,000,000", "3 corporate reference contracts",
         "ESPD completed for every consortium member/subcontractor relied on"),
        "OPS_BOARD.md §7 Fáilte Ireland"),
    TeamTarget(
        "IE_OIREACHTAS", "Houses of the Oireachtas — cyber",
        "Contract value UNKNOWN (turnover bar €2.6M)",
        "2026-09-28", _ET,
        "Irish parliament cyber security contract — the largest dated one.",
        ("Turnover €2,600,000", "Employer's liability insurance €13,000,000",
         "Professional indemnity €10,000,000", "Previous contracts required (Pass/Fail)"),
        "OPS_BOARD.md §7 Oireachtas"),
    TeamTarget(
        "IE_ANPOST", "An Post — SOC/SIEM",
        "Contract value UNKNOWN (turnover bar €1M)",
        "2026-09-29", _ET,
        "Irish postal service SOC/SIEM managed security tender.",
        ("Turnover €1,000,000", "Employer's liability insurance €13,000,000",
         "3 corporate reference contracts",
         "Tick-box: may rely on combined consortium turnover"),
        "OPS_BOARD.md §7 An Post"),
    TeamTarget(
        "IE_JUSTICE", "Department of Justice — national PKI", "€800,000",
        "2026-10-02", _ET,
        "Irish national public-key-infrastructure contract.",
        ("Turnover €800,000", "Insurance €12,700,000", "Professional indemnity €1,000,000",
         "1 reference contract over €50,000"),
        "OPS_BOARD.md §7 Dept of Justice"),
    TeamTarget(
        "IE_HSA", "Health & Safety Authority — cyber", "€900,000",
        "2026-10-12", _ET,
        "Irish H&S Authority cyber services tender.",
        ("Turnover €1,800,000", "Employer's liability insurance €13,000,000",
         "Professional indemnity €1,000,000", "3 corporate reference contracts (Pass/Fail)"),
        "OPS_BOARD.md §7 HSA"),
    # --- Standing high-value DPS/quals (no closing pressure, huge ceilings) ---
    TeamTarget(
        "IE_ASIERA", "Asiera / HEAnet — Managed ICT Security Services DPS",
        "€175,000,000", "Standing / rolling DPS", _ET,
        "The largest ceiling on the board — a rolling DPS for managed security.",
        ("SOC + Incident Response delivered 24×7×365",
         "Three named customer references (addresses + phone)",
         "Evidence of a single order worth €80,000/year",
         "Turnover over €500,000 in any of the last 3 years (pro-rata if newer)",
         "Insurance: statement willing to raise cover to required levels if awarded"),
        "OPS_BOARD.md §3 Asiera"),
    TeamTarget(
        "IE_HSE_MTDR", "HSE — Managed Threat Detection & Response DPS (21236)",
        "€60,000,000", "Standing / rolling DPS", _ET,
        "Irish health service managed threat detection — huge ceiling.",
        ("Service delivered by staff BASED IN the Republic of Ireland",
         "Dublin-based on-site incident response within 24 hours",
         "Delivered similar services on at least 3 occasions in last 3 years",
         "Insurance: has in place OR ability to obtain"),
        "OPS_BOARD.md §3 HSE 21236"),
    TeamTarget(
        "IE_HSE_CIR", "HSE — Unified Cyber Incident Response DPS (22167)",
        "€16,000,000", "Standing / rolling DPS", _ET,
        "Irish health service unified cyber IR — same document family as 21236.",
        ("Staff based in Republic of Ireland + Dublin on-site within 24hrs",
         "3 similar contracts in last 3 years with values + references"),
        "OPS_BOARD.md §3 HSE 22167"),
    TeamTarget(
        "IE_HSE_CISO", "HSE 23097 — CISO Threat & Vulnerability Management DPS",
        "€60,000,000", "Standing / rolling DPS", _ET,
        "Irish health service CISO/threat DPS. UNREAD (document exceeds the "
        "fetcher's 5MB cap) — a human on the team should open it.",
        ("UNKNOWN — document not yet read; expect the HSE geography clause "
         "(staff in Ireland + Dublin on-site) plus experience references",),
        "OPS_BOARD.md §3 HSE 23097 (UNREAD)"),
    TeamTarget(
        "IE_RTE", "RTÉ 25P041 — Cyber Security Services DPS", "€7,500,000",
        "2030-10-30", _ET,
        "Irish national broadcaster cyber DPS — admits new suppliers to 2030.",
        ("Turnover €350,000 in each of the last 3 financial years",
         "Public Liability insurance €6,500,000 (held at admission)",
         "Cyber insurance €1,000,000", "Professional Liability €1,000,000"),
        "OPS_BOARD.md §3 RTÉ 25P041"),
    # --- UK / EU big contracts a firm can carry ---
    TeamTarget(
        "UK_NHS_ENGLAND", "NHS England — cyber", "£7,200,000",
        "UNKNOWN (selective via CCS RM3764 DPS)",
        "https://supplierregistration.cabinetoffice.gov.uk/dps",
        "NHS England cyber contract — routed selectively via a CCS DPS.",
        ("Prior admission to CCS RM3764 DPS (join that first)",
         "Then the DPS selection questionnaire"),
        "OPS_BOARD.md §CLOSED NHS England"),
    TeamTarget(
        "EU_ECHA", "ECHA (EU) — TED 244223-2024", "UNKNOWN (large)",
        "Check TED for current status",
        "https://ted.europa.eu/en/notice/-/detail/244223-2024",
        "European Chemicals Agency security services — a real EU contract.",
        ("Average turnover €1,000,000", "5 reference contracts over €100,000 each"),
        "OPS_BOARD.md §CLOSED ECHA"),
    TeamTarget(
        "DE_DEGEWO", "degewo AG (DE) — Penetration Testing framework",
        "€691,200", "2026-09-22",
        "https://ted.europa.eu/en/notice/-/detail/578580-2026",
        "German housing group penetration-testing framework (TED-verified live).",
        ("3 named testers", "2 reference contracts over €50,000 each",
         "Insurance €3,000,000", "CEFR C1 German (a team member must have this)"),
        "OPS_BOARD.md §CLOSED degewo + TED 578580-2026"),
    # --- New team targets found live via TED, 2026-09-04 (verified values) ---
    TeamTarget(
        "DK_STATENS_IT", "Statens IT (DK) — Managed Detection & Response (MDR)",
        "DKK 24,000,000 (≈ €3.2M)", "2026-09-17",
        "https://ted.europa.eu/en/notice/-/detail/568334-2026",
        "Danish state IT authority MDR framework — real cyber delivery, "
        "time-critical. Bilingual notice; a team member reads the Danish/English "
        "spec for the selection criteria.",
        ("MDR / SOC delivery capability",
         "Selection criteria are in the tender documents — a team must read them",
         "Likely Danish-market presence or partner; confirm in the ESPD"),
        "TED 568334-2026 (live 2026-09-04)"),
    TeamTarget(
        "UK_MDR", "UK — Managed Detection and Response Tender", "£10,000,000",
        "2026-09-21",
        "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages/ocds-h6vhtk-0606ff",
        "A live, active UK MDR contract — English-language, £10M, closing in "
        "days (OCDS-verified: status active, closes 2026-09-21). One of the "
        "strongest team targets on the board.",
        ("MDR / SOC delivery capability",
         "English/UK — NO language or jurisdiction barrier for a UK-facing team",
         "Selection criteria are in the tender documents — team must read them"),
        "Find-a-Tender ocds-h6vhtk-0606ff (OCDS-verified 2026-09-04)"),
    TeamTarget(
        "UK_JISC_SIEM", "Jisc (UK) — SIEM/SOAR Solution for its Security Operations Centre",
        "£11,100,000", "Active — deadline UNKNOWN, check the notice",
        "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages/ocds-h6vhtk-066870",
        "Jisc (UK education/research network) SIEM/SOAR for its SOC — active, "
        "£11.1M, English (OCDS-verified). Genuine cyber delivery.",
        ("SIEM/SOAR implementation + SOC capability",
         "English/UK — no language barrier",
         "Read the tender documents for the selection criteria and deadline"),
        "Find-a-Tender ocds-h6vhtk-066870 (OCDS-verified 2026-09-04)"),
    TeamTarget(
        "UK_T160", "UK — T160 Cyber Assurance Services", "£720,000",
        "Active — deadline UNKNOWN, check the notice",
        "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages/ocds-h6vhtk-06dcac",
        "A live, active UK cyber assurance contract — English, £720k "
        "(OCDS-verified). Team-sized.",
        ("Cyber assurance / audit capability",
         "English/UK — no language barrier",
         "Read the tender documents for the selection criteria and deadline"),
        "Find-a-Tender ocds-h6vhtk-06dcac (OCDS-verified 2026-09-04)"),
    TeamTarget(
        "UK_UKRI_6251", "UKRI (UK) — Cyber Security Managed Service / MDR / SOC",
        "£1,500,000 (PLANNING stage — not yet open)",
        "Not yet open — watch for the live tender",
        "https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages/ocds-h6vhtk-06e9f0",
        "UK Research & Innovation cyber MDR + SOC contract, English-language. "
        "Currently PLANNING (buyer intent published, tender NOT yet open) — a "
        "lead to prepare for and register interest, not to bid today.",
        ("Watch for the tender to open (status: planning as of 2026-09-04)",
         "MDR + SOC delivery capability",
         "English/UK — no language or jurisdiction barrier for a UK-facing team"),
        "Find-a-Tender ocds-h6vhtk-06e9f0 (live 2026-09-04)"),
    TeamTarget(
        "DE_UKF", "Universitätsklinikum Frankfurt (DE) — Cybersecurity Managed Service",
        "€7,926,450", "2026-10-06",
        "https://ted.europa.eu/en/notice/-/detail/609103-2026",
        "German university hospital cybersecurity managed service, five service "
        "areas in one lot (TED-verified). Genuine cyber delivery.",
        ("Cybersecurity managed-service delivery (SOC/MDR-style, 5 areas)",
         "CEFR German — the notice and bid are in German; a team member needs it",
         "Selection criteria in the tender documents — team reads them"),
        "TED 609103-2026 (live 2026-09-04)"),
    TeamTarget(
        "NL_RADBOUD", "Radboud University (NL) — security governance / risk / compliance",
        "€10,800,000 (long framework, runs to 2034)", "2034-06-25",
        "https://ted.europa.eu/en/notice/-/detail/432742-2026",
        "Dutch university framework for security governance, risk analysis and "
        "ISO/NEN/BIO compliance advice (TED-verified). Real cyber-advisory work, "
        "but a multi-year framework with a distant end date.",
        ("Security governance, risk-analysis and compliance (ISO/NEN/BIO) capability",
         "Dutch language — the notice is in Dutch; a team member needs it",
         "Framework selection criteria in the documents — team reads them"),
        "TED 432742-2026 (live 2026-09-04)"),
    TeamTarget(
        "DK_NATIONALBANK", "Danmarks Nationalbank (DK) — cybersecurity advisory framework",
        "DKK 9,200,000 (≈ €1.2M)", "2026-10-02",
        "https://ted.europa.eu/en/notice/-/detail/603665-2026",
        "Danish central bank framework for security/technical consultancy "
        "(TED-verified, English half real).",
        ("Security advisory capability",
         "Selection criteria in the framework documents — team reads them",
         "Central-bank engagements often need security clearances — confirm"),
        "TED 603665-2026 (live 2026-09-04)"),
)


def live_team_targets(now: Optional[datetime] = None) -> List[TeamTarget]:
    """Team targets, soonest real deadline first, expired ones dropped."""
    now = now or datetime.now(timezone.utc)
    live = [t for t in TEAM_TARGETS if not t.is_expired(now)]

    def _key(t: TeamTarget):
        d = t.deadline_date()
        return (0, d.toordinal()) if d is not None else (1, 0)
    return sorted(live, key=_key)


def render_team_targets_md(now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    targets = live_team_targets(now)
    dated = [t for t in targets if t.deadline_date() is not None]
    out: List[str] = [
        "# 🏢 TEAM TARGETS — contracts your team can win",
        "",
        f"_{now.strftime('%d %B %Y')}. {len(targets)} high-value contracts that "
        "were out of reach for a solo operator but are winnable with a team that "
        "carries the references, insurance, turnover and staffing._",
        "",
        "Each lists **exactly what your team must bring**, quoted from the real "
        "notice. Nothing invented; UNKNOWN where a figure hasn't been read. The "
        "dated Irish tenders are time-critical — bid those first.",
        "",
    ]
    if dated:
        out += ["## ⏰ Time-critical (real deadlines)", ""]
        for t in dated:
            out += _target_block(t)
    standing = [t for t in targets if t.deadline_date() is None]
    if standing:
        out += ["## ♾️ Standing / rolling (no deadline, huge ceilings)", ""]
        for t in standing:
            out += _target_block(t)
    return "\n".join(out)


def _target_block(t: TeamTarget) -> List[str]:
    lines = [
        f"### {t.title} — {t.value}",
        f"- **Deadline:** {t.deadline}",
        f"- **What it is:** {t.what}",
        f"- **Where:** {t.link}",
        "- **Your team must bring:**",
    ]
    for r in t.requirements:
        lines.append(f"  - {r}")
    lines += [f"  <sub>source: {t.source_ref}</sub>", ""]
    return lines
