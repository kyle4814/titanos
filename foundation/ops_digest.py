"""
Ops Digest — the operator's phone-first opportunity roster.

WHY THIS FILE EXISTS

Kyle operates from his phone and asked for the board's live opportunities
delivered as individual, actionable, value-first cards at the end of every
run: "send me all the ops individually, how much, make it pretty, the whole
package ... include all actions I need to take too." OPS_BOARD.md is a
2,400-line prose campaign log — correct as a record, unreadable as a
to-do list on a phone at 6am. This module is the compression: the verified
live opportunities as STRUCTURED records, rendered two ways —

  - `render_telegram_html()` -> one Telegram HTML message per opportunity
    plus a portfolio header, each well under Telegram's 4096-char limit,
    for `telegram_notify.py` to push to Kyle's own chat.
  - `format_phone_markdown()` -> one Markdown document for the artifact
    dashboard / SendUserFile, viewable in the Claude app on his phone.

WHAT THIS IS NOT

It is not a parser of OPS_BOARD.md. The board is prose; regex-parsing it
would manufacture fields the way this repo's own document readers once did
(see OPS_BOARD.md "Two document readers were returning markup"). Instead
every `Opportunity` below is a hand-verified TRANSCRIPTION of a specific
board section, and `source_ref` names that section so any figure can be
checked against its origin. When the board changes, this roster is updated
deliberately, not scraped.

DISCIPLINE (same as the board's own)

  - Every value/deadline/link is quoted from a real source, never invented.
  - A gate stated as "None" means no gate was FOUND at that layer, with the
    honest caveat carried in the card — never "there is no requirement".
  - UNVERIFIED is a first-class status: ADB CMS eligibility could not be
    confirmed, so it says so and is ranked below the confirmed items.
  - No opportunity that came back CANNOT APPLY is dressed up as actionable;
    the ruled-out set is summarised as a count, not sold.

This module opens no socket and imports nothing network-capable. Delivery
is `telegram_notify.py`'s job; this module only produces text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

__all__ = [
    "Opportunity",
    "STATUS_ORDER",
    "OPPORTUNITIES",
    "live_opportunities",
    "render_telegram_html",
    "render_portfolio_header",
    "format_phone_markdown",
    "OpsDigestError",
]


class OpsDigestError(Exception):
    """Raised when a roster record is internally inconsistent — e.g. an
    unknown status, or an empty required field. Loud, so a bad card can
    never silently reach Kyle's phone looking authoritative."""


# Status drives ordering: what Kyle can act on TODAY with nothing missing
# comes first; time-critical dated items next; longer plays; then the
# honestly-unverified; then watch-only. This is the whole point of the
# digest — the phone shows the winnable move at the top, not a 2,400-line
# log he has to scroll.
STATUS_ORDER = (
    "ACTIONABLE_NOW",   # no gate but a free account / an email — do it from the couch
    "ACT_SOON",         # real deadline within weeks
    "PURSUE",           # strong lead, needs a real setup step, no deadline pressure
    "UNVERIFIED",       # promising but a load-bearing fact is unconfirmed
    "WATCH",            # keep an eye on; not actionable now (passed window / needs prereq)
)

_STATUS_BADGE = {
    "ACTIONABLE_NOW": "🟢 DO NOW",
    "ACT_SOON": "🟠 ACT SOON",
    "PURSUE": "🔵 PURSUE",
    "UNVERIFIED": "🟡 UNVERIFIED",
    "WATCH": "⚪ WATCH",
}


@dataclass(frozen=True)
class Opportunity:
    """One live opportunity, transcribed from a verified OPS_BOARD.md
    section. Every field is a claim with a source; `source_ref` is where
    to check it."""

    opp_id: str
    title: str
    what: str            # one plain-English line: what this actually is
    value: str           # the money, quoted from source (or the honest UNKNOWN)
    gate: str            # what stands between Kyle and it right now
    status: str          # one of STATUS_ORDER
    deadline: str        # a date, or "None (standing)"
    link: str            # where to go on the phone
    actions: tuple[str, ...]   # the exact steps Kyle takes, in order
    source_ref: str      # OPS_BOARD.md section this was read from
    note: str = ""       # the honest caveat, if any

    def __post_init__(self) -> None:
        if self.status not in STATUS_ORDER:
            raise OpsDigestError(
                f"opportunity {self.opp_id!r} has unknown status "
                f"{self.status!r}; must be one of {STATUS_ORDER}")
        for name in ("opp_id", "title", "what", "value", "gate",
                     "deadline", "link", "source_ref"):
            if not str(getattr(self, name)).strip():
                raise OpsDigestError(
                    f"opportunity {self.opp_id!r} has empty required "
                    f"field {name!r}")
        if not self.actions:
            raise OpsDigestError(
                f"opportunity {self.opp_id!r} has no actions — a card with "
                f"no next step is not actionable")

    def deadline_date(self) -> Optional[date]:
        """The parsed closing date, or None if the deadline is standing
        or unparseable. Only a confidently-parsed date can ever expire a
        card — the fail-safe direction is 'never hide a live opportunity'."""
        return _parse_deadline_date(self.deadline)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """True only when a parseable closing date is strictly in the
        past. An unparseable or standing deadline is never expired."""
        d = self.deadline_date()
        if d is None:
            return False
        today = (now or datetime.now(timezone.utc)).date()
        return d < today

    def effective_status(self, now: Optional[datetime] = None) -> str:
        """The status to render TODAY. A passed deadline drops the card to
        WATCH regardless of its stored status — so an expired tender can
        never keep showing as DO NOW / ACT SOON and mislead the operator."""
        return "WATCH" if self.is_expired(now) else self.status

    def badge(self, now: Optional[datetime] = None) -> str:
        if self.is_expired(now):
            return "⏱ CLOSED"
        return _STATUS_BADGE[self.effective_status(now)]


# ---------------------------------------------------------------------------
# THE ROSTER — verified transcription of OPS_BOARD.md live opportunities.
# Ruled-out items (HSE/RTÉ/HSA/An Post/Justice/Oireachtas/Fáilte/Asiera —
# all CANNOT APPLY) are deliberately excluded and summarised as a count in
# the header instead of sold as leads.
# ---------------------------------------------------------------------------
OPPORTUNITIES: tuple[Opportunity, ...] = (
    Opportunity(
        opp_id="ZDI",
        title="Zero Day Initiative — cash for vulnerabilities",
        what="A standing market that pays cash per vulnerability. No company, "
             "licence, insurance or references. Australia is not excluded.",
        value="Per-vulnerability cash (published table, varies by target class)",
        gate="None — free researcher account, open globally to individuals",
        status="ACTIONABLE_NOW",
        deadline="None (standing)",
        link="https://www.zerodayinitiative.com",
        actions=(
            "Register a free researcher account.",
            "It is also the prerequisite for Pwn2Own Ireland ($15k must be "
            "earned through ZDI first), so this unlocks more than itself.",
        ),
        source_ref="OPS_BOARD.md §Tier1.1 ZDI",
        note="Non-US payout tax form is not stated on their FAQ — ask at signup.",
    ),
    Opportunity(
        opp_id="ANT_GROUP",
        title="Ant Group bug bounty — 0 reports, 3 wildcard domains",
        what="A bug-bounty program nobody has filed a single report against "
             "after 2+ weeks, with 8 scopes (3 of them wildcards). The most "
             "winnable target on the whole board for someone with no reputation.",
        value="$10 – $2,500 per finding (a $10 floor means a Low pays)",
        gate="One free YesWeHack account (opens every program below too)",
        status="ACTIONABLE_NOW",
        deadline="None (standing)",
        link="https://www.yeswehack.com",
        actions=(
            "Register on YesWeHack (free, one-time — unlocks every program).",
            "Open Ant Group's brief and READ the scope rules first.",
            "Work the 3 wildcards (*.alipayplus.com, *.antom.com, "
            "*.worldfirst.com) — strictly inside the authorised scope.",
        ),
        source_ref="OPS_BOARD.md §Tier1.2 Ant Group (re-verified live 0 reports)",
        note="Testing outside authorised scope is illegal regardless of intent "
             "— read the brief, stay inside it.",
    ),
    Opportunity(
        opp_id="SWISSPOST_EVOTING",
        title="Swiss Post e-voting — bounty on PUBLISHED SOURCE CODE",
        what="The rare bounty whose target is downloadable source + specs you "
             "study offline for weeks, touching nobody's live system. Largest "
             "single payout figure found anywhere in the campaign.",
        value="€100 – €230,000 (plus named special-bounty scenarios)",
        gate="Free YesWeHack account (same one as Ant Group)",
        status="WATCH",
        deadline="None (standing programme); PIT+ 2027 invite round is the prize tier",
        link="https://www.yeswehack.com",
        actions=(
            "Only after Ant Group: this rewards depth, not speed (1,855 reports "
            "already filed).",
            "The real money came from PIT+ (20 invited of 100+ applicants) — "
            "register interest for PIT+ 2027 when it opens.",
            "The implementation can be run on your own machine year-round "
            "(self-deploy is in scope) — a Kyle strategic call, not a quick win.",
        ),
        source_ref="OPS_BOARD.md §Tier1.2b + PIT report analysis",
        note="Cheap structural/spec checks are proven exhausted; the 2026 High "
             "(€19k cache bug) is verified already patched in 1.6.1.",
    ),
    Opportunity(
        opp_id="NLNET_NGIZERO",
        title="NLnet NGI Zero — grant open to individuals",
        what="The only grant found that a sole trader with no trading history "
             "could genuinely receive. Explicitly available to individuals.",
        value="€5,000 – €50,000 (no co-contribution found)",
        gate="A project proposal that fits an open call theme",
        status="ACT_SOON",
        deadline="Call closes 2026-11-03",
        link="https://nlnet.nl/propose/",
        actions=(
            "Read the current open call themes.",
            "Draft a short project proposal (privacy/security/internet tooling "
            "fits your skill set).",
            "Submit before 2026-11-03.",
        ),
        source_ref="OPS_BOARD.md §9 NLnet NGI Zero",
    ),
    Opportunity(
        opp_id="BRADFORD_PENTEST",
        title="City of Bradford — penetration-testing framework",
        what="An OPEN framework (no pre-selection) appointing the top 3 pen-test "
             "providers. OCDS release shows ZERO stated qualification barriers. "
             "Highest-value live item with a near deadline.",
        value="£300,327 (gross) — 10-day consultancy packages, NCSC/OWASP",
        gate="One CHECK/CREST question, answerable only in the portal-gated ITT",
        status="ACT_SOON",
        deadline="2026-09-14 16:00 UTC",
        link="https://uk.eu-supply.com",
        actions=(
            "Open uk.eu-supply.com in your phone browser (cookie-gated, a human "
            "gets in where the fetcher cannot).",
            "Download the ITT and check ONE thing: is CHECK/CREST accreditation "
            "required?",
            "If not required: this is Open procedure, top-3 appointment, on your "
            "exact skill — worth a bid before the 14th.",
        ),
        source_ref="OPS_BOARD.md §6 Bradford (OCDS ocds-h6vhtk-06e59c)",
        note="OCDS shows no CREST/CHECK/insurance/turnover/references. Absence in "
             "the notice ≠ absence in the ITT annex — that is the one thing to check.",
    ),
    Opportunity(
        opp_id="IE_CIE_7289",
        title="Irish Rail CIE 7289 — Penetration Testing qualification",
        what="The best lead the campaign has found. A qualification system (no "
             "competition — you either meet the criteria or don't) for pen "
             "testing specifically, at the lowest financial bar in Ireland, with "
             "insurance DEFERRED to call-off, not required to apply.",
        value="Standing qualification → invited to every mini-competition under it",
        gate="€250k/yr turnover (×3 yrs) — but 4 written routes to meet it with a "
             "third party's turnover",
        status="PURSUE",
        deadline="PQQ closes 'Before Jan 2029' — years away, do it properly",
        link="https://www.etenders.gov.ie/epps/dps/prepareViewCfTDPSWS.do?resourceId=3243649",
        actions=(
            "Open the link and read the PQQ (CIE/Version/2/18).",
            "The turnover gate has 4 sanctioned third-party routes (consortium, "
            "sub-contractor, parent, reliance) — that is a conversation with an "
            "established firm, not a wall.",
            "Insurance and Irish Tax Clearance are deferred to call-off — they do "
            "NOT block applying.",
        ),
        source_ref="OPS_BOARD.md §3 Irish Rail CIE 7289 (PURSUE)",
        note="One UNKNOWN: whether an Australian sole trader can obtain the Irish "
             "Tax Clearance Certificate at award — deferred, does not block applying.",
    ),
    Opportunity(
        opp_id="IE_CIE_7162",
        title="Irish Rail CIE 7162 — ICT Consultancy Services",
        what="Same buyer, same friendly PQQ template as 7289, lowest financial bar "
             "found anywhere in the campaign. Apply for ONE lot (multi-lot "
             "aggregates the turnover requirement).",
        value="€200k/yr per lot (met with a third party's turnover, documented route)",
        gate="€200k turnover per lot — third-party reliance permitted in writing",
        status="PURSUE",
        deadline="Open for application till Feb 2029",
        link="https://www.etenders.gov.ie/epps/dps/prepareViewCfTDPSWS.do?resourceId=3151458",
        actions=(
            "Read the 7162 PQQ (same shape as 7289).",
            "Apply for a single lot only — aggregation is how applicants triple "
            "their own bar by accident.",
        ),
        source_ref="OPS_BOARD.md §3 CIE family (7162)",
    ),
    Opportunity(
        opp_id="IE_CIE_7764",
        title="Irish Rail CIE 7764 — ICT Professional Services",
        what="Third rolling CIE ICT qualification on the same template. Lot 6 is "
             "the lowest bar; other lots run higher.",
        value="Lot 6 €200k; Lots 1&4 €250k; Lot 3 €300k; Lots 2&5 €350k",
        gate="Turnover per chosen lot — third-party reliance permitted",
        status="PURSUE",
        deadline="6 April 2029",
        link="https://www.etenders.gov.ie/epps/dps/prepareViewCfTDPSWS.do?resourceId=3245545",
        actions=(
            "Read the 7764 PQQ.",
            "Target Lot 6 (€200k) — apply for one lot, not several.",
        ),
        source_ref="OPS_BOARD.md §3 CIE family (7764)",
    ),
    Opportunity(
        opp_id="IE_GNI_23_049",
        title="Gas Networks Ireland 23/049 — Cyber Security Services",
        what="Lowest money bar in Ireland (pro-rata for a young business), and "
             "insurance is only a broker's 'can be arranged' letter, not held "
             "cover. Harder on experience, which is scored not pass/fail.",
        value="€175k avg turnover (pro-rata) to pass D1",
        gate="Scored EXPERIENCE (175/375 to pass) — your past employee work "
             "cannot be counted, only your business's",
        status="PURSUE",
        deadline="Round 1 closed 13 Feb 2024; later rounds should exist — confirm",
        link="https://www.etenders.gov.ie/epps/dps/prepareViewCfTDPSWS.do?resourceId=3009835",
        actions=(
            "Read the 23/049 experience clause in full before spending effort.",
            "Send one message through the eTenders facility to confirm a current "
            "admission round is open.",
        ),
        source_ref="OPS_BOARD.md §3 GNI 23/049 (MAYBE)",
        note="The experience carve-out (individual-while-employed excluded) lands "
             "directly on a solo operator — read it first.",
    ),
    Opportunity(
        opp_id="NZ_MARKETPLACE",
        title="NZ Government Marketplace — all-of-government IT, to 2029",
        what="An all-of-government IT marketplace, explicitly international, "
             "Managed Security Services channel open, no turnover/insurance/cert "
             "figure on the public notice. Pre-qualifications field: None.",
        value="All-of-government ICT panel (per-engagement work once admitted)",
        gate="A free GETS supplier account to read the real application questions",
        status="PURSUE",
        deadline="Closes 25 May 2029",
        link="https://www.marketplace.govt.nz",
        actions=(
            "Create a free GETS supplier account.",
            "Open the login-gated docs: 'I/TMS Application questions', the "
            "Information Security Tiering Standard, the 4 GCDO scoping templates.",
            "Those files hold every figure currently UNKNOWN.",
        ),
        source_ref="OPS_BOARD.md §NZ Marketplace + GETS pre-qual sweep (22/22 None)",
        note="'Pre-qualifications: None' means nothing on the platform blocks you "
             "— the real criteria live in the login-gated documents, still UNKNOWN.",
    ),
    Opportunity(
        opp_id="UK_CCS_CYBER_DPS",
        title="UK Crown Commercial Service — Cyber Security Services 3 DPS",
        what="A £800M dynamic purchasing system that admits new suppliers "
             "throughout its life. No certification to JOIN — one filter category "
             "is explicitly 'Non-certified NCSC Services', built for your position.",
        value="£800,000,000 total DPS spend (you join the supplier pool)",
        gate="Selection Questionnaire + DPS Questionnaire (10-day turnaround)",
        status="PURSUE",
        deadline="Open until 13 February 2029",
        link="https://supplierregistration.cabinetoffice.gov.uk/dps",
        actions=(
            "Register on the DPS portal.",
            "Complete the SQ + DPS Questionnaire — a human must pick the Schedule "
            "1 filter categories (we would not guess those).",
        ),
        source_ref="OPS_BOARD.md §5 UK CCS Cyber DPS 3",
    ),
    Opportunity(
        opp_id="NSW_ICT_SCHEME",
        title="NSW ICT Services Scheme (SCM0020) — $150k ceiling",
        what="An always-open NSW scheme. Turnover is NOT an acceptance criterion; "
             "insurance is required only before a contract, not to join. Category "
             "K03 'Security testing' is your exact label.",
        value="Contracts up to $150,000 ex GST at the Registered tier",
        gate="Two referee reports per category — 'referee' is never defined "
             "(pro-bono may qualify)",
        status="ACTIONABLE_NOW",
        deadline="None (always open)",
        link="https://buy.nsw.gov.au",
        actions=(
            "Email ICTServices@customerservice.nsw.gov.au: does a documented "
            "pro-bono engagement qualify as a referee?",
            "That one answer is the only thing between you and a $150k ceiling.",
            "Register with your ABN once confirmed.",
        ),
        source_ref="OPS_BOARD.md §NSW ICT Services Scheme",
    ),
    Opportunity(
        opp_id="ICN_GATEWAY",
        title="ICN Gateway — subcontracting exposure, no reference gate",
        what="Zero reference requirement. ABN at signup. The route you can finish "
             "today without waiting on anyone.",
        value="Subcontracting exposure on large projects (not prime contracts)",
        gate="ABN (free tier exists; discoverability needs a paid tier ~$600–1,480/yr)",
        status="ACTIONABLE_NOW",
        deadline="None (standing)",
        link="https://gateway.icn.org.au",
        actions=(
            "Sign up with your ABN (auto-populates from ABR).",
            "Declare your skills.",
            "Confirm the paid-tier pricing at signup (our figure is lower-confidence).",
        ),
        source_ref="OPS_BOARD.md §ICN Gateway",
    ),
    Opportunity(
        opp_id="QITC_QLD",
        title="Queensland QITC — no panel or accreditation gate",
        what="Queensland contracts IT directly, per-engagement, through QTenders. "
             "No panel or accreditation gate whatsoever.",
        value="Per-engagement Queensland government IT work",
        gate="None (direct contracting via QTenders)",
        status="ACTIONABLE_NOW",
        deadline="None (standing)",
        link="https://www.hpw.qld.gov.au/qtenders",
        actions=(
            "Register on QTenders.",
            "Watch for per-engagement IT/security work.",
        ),
        source_ref="OPS_BOARD.md §4 Queensland QITC",
    ),
    Opportunity(
        opp_id="ADB_CMS",
        title="ADB Consultant Management System — individual track",
        what="Development banks procure from PEOPLE on a separate track with no "
             "incorporation/insurance/turnover/reference requirement — IF the "
             "reported eligibility rule is accurate. Australia is a founding member.",
        value="Individual-consultant assignments (bank-funded)",
        gate="UNVERIFIED eligibility — the load-bearing rule could not be confirmed "
             "by static fetch (JS app)",
        status="UNVERIFIED",
        deadline="None (standing)",
        link="https://cms.adb.org",
        actions=(
            "Open cms.adb.org in an ordinary browser and click Register.",
            "The form itself states what it requires — 10 minutes answers whether "
            "the biggest structural opening found is real.",
        ),
        source_ref="OPS_BOARD.md §ADB CMS (UNVERIFIED)",
        note="Recorded UNVERIFIED on purpose — a wrong eligibility claim is exactly "
             "the error that produced a false QUALIFIED earlier in the campaign.",
    ),
    Opportunity(
        opp_id="IMMUNEFI",
        title="Immunefi — crypto bug bounties, no credentials, 76 need no KYC",
        what="The most structurally open income on this board: no company, no "
             "references, no insurance, no certifications, and 76 of 183 live "
             "programs require no KYC at all. The catch is skill — these are "
             "smart-contract / DeFi security audits, not web app testing.",
        value="$1,000 – $10,000,000 (Sky $10M, GMX & SparkLend $5M — all no-KYC)",
        gate="Free Immunefi account + genuine smart-contract audit skill — your "
             "web3 skill is UNKNOWN, and that is the real question, not credentials",
        status="UNVERIFIED",
        deadline="None (standing)",
        link="https://immunefi.com/bug-bounty/",
        actions=(
            "Register free — the 76 no-KYC programs need no identity documents.",
            "Be honest with yourself about Solidity/DeFi audit skill: a $10M "
            "payout means finding a critical bug in heavily-audited protocol "
            "code — specialist work, the opposite of the $10 Ant Group Low.",
            "If the skill is there (or worth building), this is the only route "
            "with zero credential barriers AND life-changing ceilings.",
        ),
        source_ref="OPS_BOARD.md §Immunefi sweep 2026-09-03 (183 programs read live)",
        note="Highest ceiling on the board AND the hardest skill gate — the exact "
             "opposite tradeoff from Ant Group (low skill, low payout, uncontested). "
             "Do not treat the $10M as reachable without demonstrated expertise.",
    ),
)


_MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def _parse_deadline_date(deadline: str) -> Optional[date]:
    """Best-effort parse of a closing date from a free-form deadline
    string. Handles ISO (2026-09-14), 'D Month YYYY' (6 April 2029),
    'Month YYYY' (Feb 2029 -> the 1st, deliberately conservative so a
    whole-month window is not called closed early), and DD/MM/YYYY.
    Returns None when nothing parses — and None NEVER expires a card, so
    an unrecognised phrasing can only fail safe (stay visible)."""
    text = deadline.replace(",", " ")
    tokens = text.split()
    # ISO or DD/MM/YYYY tokens first.
    for tok in tokens:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(tok, fmt).date()
            except ValueError:
                continue
    # 'D Month YYYY' or abbreviated month.
    low = [t.lower().rstrip(".") for t in tokens]
    for i, tok in enumerate(low):
        month = None
        for name, num in _MONTHS.items():
            if tok == name or (len(tok) >= 3 and name.startswith(tok)):
                month = num
                break
        if month is None:
            continue
        year = None
        day = 1
        # year: any 4-digit token nearby
        for t in tokens:
            if len(t) == 4 and t.isdigit():
                year = int(t)
                break
        # day: a 1-2 digit token immediately before the month
        if i >= 1 and low[i - 1].isdigit() and len(low[i - 1]) <= 2:
            day = int(low[i - 1])
        if year is not None:
            try:
                return date(year, month, day)
            except ValueError:
                return None
    return None


def live_opportunities(now: Optional[datetime] = None) -> tuple[Opportunity, ...]:
    """The roster, sorted by EFFECTIVE status (a passed deadline sinks a
    card to WATCH) then by whether a deadline presses. Deterministic for a
    fixed `now`."""
    def _key(o: Opportunity) -> tuple:
        return (STATUS_ORDER.index(o.effective_status(now)),
                _deadline_sort_key(o.deadline))
    return tuple(sorted(OPPORTUNITIES, key=_key))


def _deadline_sort_key(deadline: str) -> tuple:
    """Sort a soonest-first date ahead of a standing/none item. Non-date
    strings sort last (large sentinel), so a real 2026-09-14 beats
    'None (standing)' without needing to parse every phrasing."""
    d = _parse_deadline_date(deadline)
    if d is not None:
        return (0, d.toordinal())
    return (1, 0)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def _esc(text: str) -> str:
    """Minimal Telegram-HTML escaping (Telegram parse_mode=HTML allows a
    small tag set; everything else must have <, >, & escaped)."""
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_portfolio_header(opps: tuple[Opportunity, ...],
                            ruled_out: int = 8,
                            now: Optional[datetime] = None) -> str:
    """The first message: the whole portfolio at a glance, phone-first."""
    now = now or datetime.now(timezone.utc)
    counts: dict[str, int] = {}
    expired = 0
    for o in opps:
        if o.is_expired(now):
            expired += 1
        counts[o.effective_status(now)] = counts.get(o.effective_status(now), 0) + 1
    live_count = len(opps) - expired
    lines = [
        "💰 <b>TITANOS MONEY-PRINTER — OPS DIGEST</b>",
        f"<i>{now.strftime('%a %d %b %Y %H:%M UTC')}</i>",
        "",
        f"<b>{live_count}</b> live opportunities you CAN move on. "
        f"{ruled_out} already ruled out (references/insurance walls) — not shown.",
        "",
    ]
    if expired:
        lines.append(f"⏱ {expired} closed since last run — shown at the bottom, marked.")
        lines.append("")
    for status in STATUS_ORDER:
        if counts.get(status):
            lines.append(f"{_STATUS_BADGE[status]} — {counts[status]}")
    lines += [
        "",
        "Cards follow, most-winnable first. Each has the link and the exact "
        "steps. Tap, do, done. 🚀",
    ]
    return "\n".join(lines)


def _render_one_html(o: Opportunity, index: int, total: int,
                     now: Optional[datetime] = None) -> str:
    expired = o.is_expired(now)
    lines = [
        f"{o.badge(now)}  <b>{_esc(o.title)}</b>  <i>({index}/{total})</i>",
        "",
        _esc(o.what),
        "",
        f"💵 <b>Value:</b> {_esc(o.value)}",
        f"🔒 <b>Gate:</b> {_esc(o.gate)}",
        f"⏰ <b>Deadline:</b> {_esc(o.deadline)}",
        "",
    ]
    if expired:
        d = o.deadline_date()
        lines += [f"⏱ <b>CLOSED {d.isoformat() if d else ''}</b> — the window "
                  "has passed; here for the record, not to act on.", ""]
    else:
        lines.append("<b>Do this:</b>")
        for i, act in enumerate(o.actions, 1):
            lines.append(f"  {i}. {_esc(act)}")
    lines += ["", f'🔗 <a href="{_esc(o.link)}">{_esc(o.link)}</a>']
    if o.note:
        lines += ["", f"⚠️ <i>{_esc(o.note)}</i>"]
    msg = "\n".join(lines)
    if len(msg) > 4096:
        # Telegram hard limit. Never silently truncate a money figure or a
        # link; drop the note first, then fail loud rather than mislead.
        lines = [ln for ln in lines if not ln.startswith("⚠️")]
        msg = "\n".join(lines)
        if len(msg) > 4096:
            raise OpsDigestError(
                f"card {o.opp_id!r} exceeds Telegram's 4096-char limit even "
                f"without its note — split it rather than truncate a figure")
    return msg


def render_telegram_html(opps: Optional[tuple[Opportunity, ...]] = None,
                         now: Optional[datetime] = None) -> tuple[str, ...]:
    """The full Telegram payload: header first, then one message per
    opportunity. Returned as a tuple of strings — the caller (telegram_
    notify.send_digest) sends them in order with a pause between."""
    opps = opps if opps is not None else live_opportunities(now)
    messages = [render_portfolio_header(opps, now=now)]
    total = len(opps)
    for i, o in enumerate(opps, 1):
        messages.append(_render_one_html(o, i, total, now=now))
    return tuple(messages)


def format_phone_markdown(opps: Optional[tuple[Opportunity, ...]] = None,
                          now: Optional[datetime] = None) -> str:
    """One Markdown document for the artifact dashboard / SendUserFile —
    the same roster, formatted for a scrollable phone page."""
    now = now or datetime.now(timezone.utc)
    opps = opps if opps is not None else live_opportunities(now)
    live_count = sum(1 for o in opps if not o.is_expired(now))
    out = [
        "# 💰 TITANOS Money-Printer — Ops Digest",
        f"_{now.strftime('%A %d %B %Y, %H:%M UTC')}_",
        "",
        f"**{live_count} live opportunities you can move on.** "
        "Most-winnable first. Each card has the link and the exact steps.",
        "",
    ]
    total = len(opps)
    for i, o in enumerate(opps, 1):
        expired = o.is_expired(now)
        out += [
            f"## {o.badge(now)} — {o.title} ({i}/{total})",
            "",
            o.what,
            "",
            f"- **Value:** {o.value}",
            f"- **Gate:** {o.gate}",
            f"- **Deadline:** {o.deadline}",
            f"- **Link:** {o.link}",
            "",
        ]
        if expired:
            d = o.deadline_date()
            out += [f"> ⏱ **CLOSED {d.isoformat() if d else ''}** — window "
                    "passed; here for the record, not to act on.", ""]
        else:
            out += ["**Do this:**", ""]
            for j, act in enumerate(o.actions, 1):
                out.append(f"{j}. {act}")
        if o.note:
            out += ["", f"> ⚠️ {o.note}"]
        out += ["", f"<sub>source: {o.source_ref}</sub>", "", "---", ""]
    return "\n".join(out)
