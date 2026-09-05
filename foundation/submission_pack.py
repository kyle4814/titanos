"""
Submission Pack — turn a team profile + a target into a ready-to-file pack,
everything assembled up to (never through) the final legally-binding Submit.

This is the "drive to the submit line" machinery for real bids. Given a
`TeamProfile` (the team's real, Kyle-supplied identity/facts) and a target
from `team_targets.py`, it produces:
  - the portal + direct login URL and the known step sequence for that portal,
  - the upload checklist derived from the target's quoted requirements,
  - a qualification/ESPD answer sheet filled from the profile,
  - a MISSING list: exactly what the team still has to supply for this tender.

HONEST BY CONSTRUCTION (Kyle's rules):
  - Nothing is invented. A fact the profile does not carry is emitted as
    UNKNOWN and listed under MISSING — never guessed, never defaulted.
  - The pack stops at the Submit button. Submitting a bid is a binding legal
    act the portal requires a human to attest; this module never automates
    that click and says so in the steps.
  - No network, no credentials, no account creation. It assembles files from
    the profile and the registry; logging in and filing are the operator's.

The portal step sequences are the real, publicly-documented flows for each
system, kept deliberately generic (they are the shape every notice on that
portal shares); the tender's own documents remain the authority for anything
notice-specific.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from foundation.team_targets import TEAM_TARGETS, TeamTarget

__all__ = [
    "TeamProfile",
    "SubmissionPack",
    "build_submission_pack",
    "render_pack_md",
    "portal_of",
]

# Sentinel for a fact the team has not supplied. Never rendered as a real
# value; always also surfaces under the pack's MISSING list.
UNKNOWN = "UNKNOWN — team must supply"


@dataclass(frozen=True)
class TeamProfile:
    """The team's real identity and qualification facts, supplied by the
    operator (e.g. from a JSON file). Every field defaults to empty so an
    unsupplied fact is UNKNOWN, never invented. This module reads it; it never
    writes it and never fills a blank with a guess."""

    legal_name: str = ""
    registration: str = ""          # company reg / ABN / VAT, as applicable
    contact_name: str = ""
    contact_email: str = ""
    address: str = ""
    annual_turnover_eur: float = 0.0
    insurance_cover: Dict[str, float] = field(default_factory=dict)  # type -> amount
    references: Tuple[str, ...] = ()      # short reference-project descriptions
    certifications: Tuple[str, ...] = ()  # e.g. "ISO 27001", "Cyber Essentials"
    languages: Tuple[str, ...] = ()
    has_247_soc: bool = False

    def value_or_unknown(self, raw: object) -> str:
        if raw in (None, "", 0, 0.0, (), {}, False):
            return UNKNOWN
        return str(raw)


# Portal identity + the real, generic step sequence for filing on it. The
# final step is always the human Submit — this module drives nothing past it.
_PORTAL_STEPS: Dict[str, Tuple[str, Tuple[str, ...]]] = {
    "eTenders (IE)": (
        "https://www.etenders.gov.ie",
        (
            "Log in to eTenders (free account; register once if you have not).",
            "Open the notice via its resourceId link and click 'Express Interest'.",
            "Download the RFT / PQQ document pack from the notice's Documents area.",
            "Complete the response: the ESPD, the qualification questionnaire, and "
            "any pricing/method-statement templates in the pack.",
            "Upload every completed document into the notice's 'My Response' area.",
            "Review the response summary the portal shows you.",
            "SUBMIT before the deadline — this is a binding act; a human does it.",
        ),
    ),
    "TED / buyer portal (EU)": (
        "https://ted.europa.eu",
        (
            "Open the TED notice; find the 'Electronic submission' / buyer "
            "eProcurement URL named in the notice.",
            "Register/log in on that buyer portal (each EU buyer runs its own).",
            "Download the procurement documents and the ESPD request.",
            "Complete the ESPD (eESPD XML or the portal's form) and the response.",
            "Upload the completed response on the buyer portal.",
            "Review the submission summary.",
            "SUBMIT before the deadline — binding; a human does it.",
        ),
    ),
    "Find a Tender / eSourcing (UK)": (
        "https://www.find-tender.service.gov.uk",
        (
            "Open the Find a Tender notice; follow the link to the buyer's "
            "eSourcing portal (e.g. bravosolution, eu-supply, Jaggaer).",
            "Register/log in on that eSourcing portal (free).",
            "Download the ITT / SQ document pack.",
            "Complete the selection questionnaire, pricing and method responses.",
            "Upload the completed response into the portal.",
            "Review the response.",
            "SUBMIT before the deadline — binding; a human does it.",
        ),
    ),
}


def portal_of(target: TeamTarget) -> str:
    link = target.link.lower()
    if "etenders.gov.ie" in link:
        return "eTenders (IE)"
    if "ted.europa.eu" in link:
        return "TED / buyer portal (EU)"
    if "find-tender.service.gov.uk" in link or "cabinetoffice.gov.uk" in link:
        return "Find a Tender / eSourcing (UK)"
    return "Buyer portal (see notice)"


@dataclass(frozen=True)
class SubmissionPack:
    target: TeamTarget
    portal: str
    login_url: str
    steps: Tuple[str, ...]
    upload_checklist: Tuple[str, ...]     # from the target's requirements
    espd_answers: Tuple[Tuple[str, str], ...]  # (question, answer-or-UNKNOWN)
    missing: Tuple[str, ...]              # exactly what the team must still supply

    @property
    def ready(self) -> bool:
        return not self.missing


def build_submission_pack(target: TeamTarget,
                          profile: Optional[TeamProfile] = None) -> SubmissionPack:
    profile = profile or TeamProfile()
    portal = portal_of(target)
    login_url, steps = _PORTAL_STEPS.get(
        portal, (target.link, ("Open the notice and follow its submission "
                               "instructions.",
                               "SUBMIT before the deadline — a human does it.")))

    # The upload checklist is the target's own quoted requirements — the real
    # things this buyer asks a bidder to evidence.
    upload_checklist = tuple(target.requirements)

    # ESPD / qualification answer sheet, filled ONLY from supplied facts.
    v = profile.value_or_unknown
    espd_answers = (
        ("Legal name of economic operator", v(profile.legal_name)),
        ("Registration / ABN / VAT", v(profile.registration)),
        ("Contact name", v(profile.contact_name)),
        ("Contact email", v(profile.contact_email)),
        ("Registered address", v(profile.address)),
        ("Annual turnover (EUR)",
         v(profile.annual_turnover_eur) if profile.annual_turnover_eur else UNKNOWN),
        ("Insurance cover held",
         "; ".join(f"{k}: {int(a):,}" for k, a in profile.insurance_cover.items())
         if profile.insurance_cover else UNKNOWN),
        ("Reference contracts",
         " | ".join(profile.references) if profile.references else UNKNOWN),
        ("Certifications",
         ", ".join(profile.certifications) if profile.certifications else UNKNOWN),
    )

    missing = tuple(q for q, a in espd_answers if a == UNKNOWN)

    return SubmissionPack(
        target=target, portal=portal, login_url=login_url, steps=steps,
        upload_checklist=upload_checklist, espd_answers=espd_answers,
        missing=missing,
    )


def render_pack_md(pack: SubmissionPack,
                   now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    t = pack.target
    L: List[str] = []
    L.append(f"# Submission pack — {t.title}")
    L.append("")
    L.append(f"- **Value** {t.value}")
    L.append(f"- **Deadline** {t.deadline}")
    L.append(f"- **Portal** {pack.portal}")
    L.append(f"- **Open / log in** {pack.login_url}")
    L.append(f"- **Direct notice** {t.link}")
    L.append("")
    L.append("## Steps (the last one — Submit — is yours, by law)")
    for i, s in enumerate(pack.steps, 1):
        L.append(f"{i}. {s}")
    L.append("")
    L.append("## Upload checklist — what this buyer asks you to evidence")
    for c in pack.upload_checklist:
        L.append(f"- [ ] {c}")
    L.append("")
    L.append("## Qualification / ESPD answers (from your team profile)")
    for q, a in pack.espd_answers:
        mark = "⚠️ " if a == UNKNOWN else ""
        L.append(f"- **{q}:** {mark}{a}")
    L.append("")
    if pack.missing:
        L.append("## ⚠️ MISSING — supply these before this bid can be filed")
        for m in pack.missing:
            L.append(f"- {m}")
    else:
        L.append("## ✅ Profile complete for the standard qualification fields")
        L.append("(The tender's own documents may still ask for extra, "
                 "notice-specific responses — read the pack.)")
    L.append("")
    L.append("> This pack stops at the Submit button. Submitting a public "
             "tender is a binding legal act; log in and file it yourself after "
             "reviewing. Nothing here was invented — blanks are marked UNKNOWN.")
    return "\n".join(L)
