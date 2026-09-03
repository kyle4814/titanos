"""
Close Pack — drive every deal to the submit line.

WHY THIS FILE EXISTS

Kyle granted broad authority ("you are allowed to close and invest ...
lock that in and proceed", 2026-09-04). Authority removes the PERMISSION
wall, not the five CAPABILITY walls: moving money, opening an account,
sending to a third party, signing, and handling his private data are all
things this repository physically cannot do from here — and each is
irreversible while he is asleep. The correct response is not to fake a
close; it is to drive every deal to the exact line where only that
irreversible half-second remains, so his part drops from hours to a tap.

This module classifies each live opportunity by WHICH wall it stops at,
lists the minimal facts still needed from Kyle to pre-fill it, and — only
for pure information inquiries that assert NO capability — drafts the
ready-to-send text. It never drafts anything that claims a skill,
certification, reference, turnover, or ABN the operator profile has not
verified: the profile is almost entirely UNKNOWN, and a fabricated
capability claim on a real bid is the single worst thing this repository
could emit. A draft carries `[BRACKETED]` placeholders for every fact the
profile does not hold — visible blanks, never invented values.

Sending any draft is Kyle's act (gate 3). This module produces words on a
page; it opens no socket and sends nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from foundation.ops_digest import OPPORTUNITIES, Opportunity

__all__ = [
    "ClosePlanError",
    "GATE_TYPES",
    "ClosePlan",
    "CLOSE_PLANS",
    "plan_for",
    "consolidated_facts_needed",
    "render_close_pack",
]


class ClosePlanError(Exception):
    """Raised when the close plans and the roster disagree — e.g. a new
    opportunity has no plan, or a plan names an unknown gate. Loud, so a
    roster addition cannot silently ship without a close line."""


# The wall a deal actually stops at. All are Kyle's by nature.
GATE_TYPES = (
    "ACCOUNT",    # open a free account / login — his to open
    "FACT",       # blocked only on a fact I still need from him to pre-fill
    "OUTBOUND",   # a message he sends (I can draft it if it claims nothing)
    "MONEY",      # spend / invest — his
)


@dataclass(frozen=True)
class ClosePlan:
    """How one opportunity reaches its submit line."""
    opp_id: str
    gate: str                       # the FIRST wall, one of GATE_TYPES
    needs: tuple[str, ...] = ()     # facts still needed from Kyle
    draft: Optional[str] = None     # ready-to-send text, inquiries only
    human_action: str = ""          # the one tap, in plain words

    def __post_init__(self) -> None:
        if self.gate not in GATE_TYPES:
            raise ClosePlanError(
                f"{self.opp_id!r}: unknown gate {self.gate!r}")
        if self.draft is not None and self.gate != "OUTBOUND":
            raise ClosePlanError(
                f"{self.opp_id!r}: only an OUTBOUND inquiry may carry a draft")


# The four identity facts that unlock the ACCOUNT/FACT registrations. None
# is in operator_profile.json yet; all four are Kyle's to state once.
_IDENTITY = ("legal/trading name", "ABN number", "business address",
             "contact email + phone")

# Pure information inquiries — they ask a question and assert NO capability,
# so they are safe to draft. Placeholders are visible blanks, never invented.
_NSW_DRAFT = """\
To: ICTServices@customerservice.nsw.gov.au
Subject: SCM0020 ICT Services Scheme — referee report eligibility

Hello,

I am a sole trader (ABN [YOUR ABN]) preparing to apply to the ICT Services
Scheme (SCM0020) under category K03 "Security testing".

Scheme Rules clause 8.1 requires two referee reports per nominated
category. Could you confirm whether a documented pro-bono engagement is
acceptable as a referee report, or whether referees must come from paid
contracts?

Kind regards,
[YOUR NAME]
[YOUR CONTACT]"""

_GNI_DRAFT = """\
Send via the eTenders messaging facility on notice 23/049.
Subject: 23/049 Cyber Security Services — admission round status

Hello,

Could you confirm whether a current round for admission to the 23/049
Cyber Security Services qualification system is open, and the closing date
of the next round if not?

Thank you,
[YOUR NAME] (ABN [YOUR ABN])"""


CLOSE_PLANS: dict[str, ClosePlan] = {
    "ZDI": ClosePlan(
        "ZDI", "ACCOUNT",
        human_action="Open a free ZDI researcher account at zerodayinitiative.com."),
    "ANT_GROUP": ClosePlan(
        "ANT_GROUP", "ACCOUNT",
        human_action="Open a free YesWeHack account (one login unlocks every "
                     "bounty program), then read Ant Group's scope."),
    "SWISSPOST_EVOTING": ClosePlan(
        "SWISSPOST_EVOTING", "ACCOUNT",
        human_action="Same free YesWeHack account; the study happens offline "
                     "on the published source, no account needed for that half."),
    "NLNET_NGIZERO": ClosePlan(
        "NLNET_NGIZERO", "FACT",
        needs=("a one-paragraph project idea in your own words (I must not "
               "invent your technical intent)",) + _IDENTITY,
        human_action="Give me the project idea; I draft the proposal, you "
                     "submit it at nlnet.nl before 2026-11-03."),
    "BRADFORD_PENTEST": ClosePlan(
        "BRADFORD_PENTEST", "ACCOUNT",
        human_action="Log in to uk.eu-supply.com, download the ITT, tell me if "
                     "CHECK/CREST is required — then I draft the response."),
    "NSW_ICT_SCHEME": ClosePlan(
        "NSW_ICT_SCHEME", "OUTBOUND",
        needs=("ABN number", "your name + contact"),
        draft=_NSW_DRAFT,
        human_action="Paste your ABN/name into the draft below and send it — "
                     "one question that unlocks a $150k ceiling."),
    "ICN_GATEWAY": ClosePlan(
        "ICN_GATEWAY", "ACCOUNT",
        needs=("ABN number",),
        human_action="Sign up at gateway.icn.org.au with your ABN (it "
                     "auto-fills from the ABR)."),
    "QITC_QLD": ClosePlan(
        "QITC_QLD", "ACCOUNT",
        human_action="Register on QTenders (hpw.qld.gov.au/qtenders)."),
    "IE_CIE_7289": ClosePlan(
        "IE_CIE_7289", "FACT",
        needs=("3 years' turnover figures OR a third-party you'd rely on for "
               "the €250k turnover", "your declared pen-test skills/experience")
              + _IDENTITY,
        human_action="Give me the turnover route + your real experience; I "
                     "draft the PQQ, you submit on eTenders (open till Jan 2029)."),
    "IE_CIE_7162": ClosePlan(
        "IE_CIE_7162", "FACT",
        needs=("turnover route for €200k/lot", "declared ICT skills") + _IDENTITY,
        human_action="Same as 7289 — one lot only. I draft once you give the "
                     "turnover route and real experience."),
    "IE_CIE_7764": ClosePlan(
        "IE_CIE_7764", "FACT",
        needs=("turnover route for Lot 6 €200k", "declared ICT skills") + _IDENTITY,
        human_action="Target Lot 6; I draft once you give the turnover route "
                     "and real experience."),
    "IE_GNI_23_049": ClosePlan(
        "IE_GNI_23_049", "OUTBOUND",
        needs=("ABN number", "your name"),
        draft=_GNI_DRAFT,
        human_action="Send the one-line question below via eTenders to learn if "
                     "a round is open before spending effort."),
    "NZ_MARKETPLACE": ClosePlan(
        "NZ_MARKETPLACE", "ACCOUNT",
        human_action="Create a free GETS supplier account, open the login-gated "
                     "application questions — then I map them to your facts."),
    "UK_CCS_CYBER_DPS": ClosePlan(
        "UK_CCS_CYBER_DPS", "ACCOUNT",
        needs=_IDENTITY,
        human_action="Register on the DPS portal; a human must pick the "
                     "Schedule 1 filter categories (I won't guess those)."),
    "ADB_CMS": ClosePlan(
        "ADB_CMS", "ACCOUNT",
        human_action="Open cms.adb.org, click Register — the form itself states "
                     "eligibility (still UNVERIFIED until you see it)."),
    "IMMUNEFI": ClosePlan(
        "IMMUNEFI", "FACT",
        needs=("an honest read on your smart-contract / Solidity / DeFi audit "
               "skill — the whole question here is capability, not credentials",),
        human_action="Register free at immunefi.com (76 programs need no KYC); "
                     "then judge the skill fit before sinking time into a $10M "
                     "target that specialist auditors compete for."),
}


def plan_for(opp: Opportunity) -> ClosePlan:
    try:
        return CLOSE_PLANS[opp.opp_id]
    except KeyError:
        raise ClosePlanError(
            f"opportunity {opp.opp_id!r} has no close plan — add one to "
            f"CLOSE_PLANS so it reaches a submit line")


def consolidated_facts_needed() -> tuple[str, ...]:
    """The de-duplicated set of facts Kyle can state ONCE to unlock the
    most closes. Identity facts float to the top because they recur."""
    seen: list[str] = []
    for oid in (o.opp_id for o in OPPORTUNITIES):
        for need in CLOSE_PLANS[oid].needs:
            if need not in seen:
                seen.append(need)
    # identity first (most reused), then the rest in first-seen order
    identity = [n for n in seen if n in _IDENTITY]
    rest = [n for n in seen if n not in _IDENTITY]
    return tuple(identity + rest)


def render_close_pack(now_line: str = "") -> str:
    """A phone-first 'close line' for every live deal: the wall it stops
    at, the facts I still need, and the ready-to-send draft where one
    exists. Expired opportunities are skipped."""
    from foundation.ops_digest import live_opportunities
    opps = [o for o in live_opportunities() if not o.is_expired()]
    gate_label = {
        "ACCOUNT": "🔑 opens an account (yours)",
        "FACT": "📝 needs a fact from you",
        "OUTBOUND": "✉️ a message to send (drafted below)",
        "MONEY": "💳 needs spend (yours)",
    }
    out = ["# 🎯 Close Pack — every deal at its submit line", ""]
    if now_line:
        out += [f"_{now_line}_", ""]
    out += [
        "I've taken each live deal as far as it goes without you. What's "
        "left on each is one of your five gates — named, not hidden.",
        "",
        "## The 4 facts that unlock the most closes",
        "",
        "State these once and I can pre-fill every registration and draft:",
        "",
    ]
    for f in consolidated_facts_needed():
        out.append(f"- {f}")
    out += ["", "---", ""]
    for o in opps:
        p = plan_for(o)
        out += [
            f"## {o.title}",
            f"- **Value:** {o.value}",
            f"- **Wall:** {gate_label[p.gate]}",
            f"- **Your move:** {p.human_action}",
        ]
        if p.needs:
            out.append(f"- **I still need from you:** {'; '.join(p.needs)}")
        if p.draft:
            out += ["", "**Ready to send — paste your details into the blanks:**",
                    "", "```", p.draft, "```"]
        out += ["", "---", ""]
    return "\n".join(out)
