"""What KIND of notice is this, and can it be answered at all?

WHY THIS EXISTS
---------------
`qualification.py` answers "do the published criteria block this
operator". That is the right question for a tender. It is the wrong
question for roughly a third of what the sources return, and the system
could not tell the difference.

Measured across this campaign:

  - Five live Irish security tenders, all resolved against their real
    documents, all closed at EUR400,000 to EUR2,600,000 turnover.
  - Three live notices where the qualification barrier is ZERO --
    UKRI-6251 (UK preliminary market engagement), Health NZ's
    Enterprise Observability RFI, and NZ Defence's TSS Panel Reset.

Every one of those eight came back `INSUFFICIENT_DATA`, identically,
because none published structured selection criteria. The three that a
solo operator can actually answer were indistinguishable from the five
that would eliminate him on turnover.

That is not a scoring problem. It is a missing distinction, and this
module supplies it.

THE CLASSES
-----------
`MARKET_ENGAGEMENT`  the buyer is asking what is possible, BEFORE
                     writing a tender. Nothing is being awarded, so
                     there is nothing to qualify for. The only notice
                     class a solo operator answers on equal terms with
                     a consultancy.

`ROLLING_ADMISSION`  a DPS, framework or panel that admits suppliers
                     throughout its life. No single closing date to
                     miss; qualification still applies, but on your
                     schedule rather than the buyer's.

`COMPETITIVE`        an ordinary tender. Selection criteria apply and
                     the deadline is real.

`ALREADY_DECIDED`    an award or contract notice. The work is gone.
                     Useful only as intelligence about who wins.

`UNKNOWN`            the notice does not say. NOT a synonym for
                     COMPETITIVE -- see below.

THE RULE THIS MODULE WILL NOT BREAK
-----------------------------------
`UNKNOWN` is never resolved into a class by inference. A notice that
does not state its type stays `UNKNOWN`, and a caller that wants to
treat unknown as competitive may do so explicitly -- this module will
not do it for them.

The asymmetry matters and runs the other way from most defaults here:
mistaking a tender for market engagement wastes an afternoon writing a
response nobody reads. Mistaking market engagement for a tender means
never answering the one notice class with no barrier at all. The second
error is the expensive one, and it is the one silence produces.

NO NETWORK, NO SCORING
----------------------
Pure function over evidence a caller already fetched. It does not fetch,
does not rank, and deliberately does not merge with `qualification.py`:
"what kind of thing is this" and "am I eligible for it" are different
questions, and answering them in one number is how a reader stops
checking either.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

__all__ = [
    "NoticeClassError",
    "CLASSES",
    "NoticeClassification",
    "classify_notice",
    "format_classification",
]


class NoticeClassError(ValueError):
    """Raised when a caller asks this module to assert something it
    cannot support -- an unknown class, or a confident classification
    with no evidence behind it."""


CLASSES = (
    "MARKET_ENGAGEMENT",
    "ROLLING_ADMISSION",
    "COMPETITIVE",
    "ALREADY_DECIDED",
    "UNKNOWN",
)

# Presentation order: what deserves attention first. MARKET_ENGAGEMENT
# leads because it is the only class with no qualification barrier;
# ALREADY_DECIDED is last because the work is gone.
CLASS_ORDER = (
    "MARKET_ENGAGEMENT",
    "ROLLING_ADMISSION",
    "UNKNOWN",
    "COMPETITIVE",
    "ALREADY_DECIDED",
)

# Every pattern below was read off a real notice during this campaign.
# Nothing here is a guessed vocabulary.
_MARKET_ENGAGEMENT_PATTERNS = (
    # UK Find a Tender, notice 2026/S 000-080084 (UKRI-6251)
    r"preliminary market engagement",
    r"\bUK2\b",
    # NZ GETS tender_type, live: Health NZ RFI26-663
    r"request for information",
    r"market research",
    r"market sounding",
    # NZ GETS tender_type, live: NZ Defence TSS-2026-AN
    r"advance notice",
    r"notice of information",
    r"prior information notice",
    r"\bPIN\b",
    r"future procurement opportunit",
)

_ROLLING_ADMISSION_PATTERNS = (
    r"dynamic purchasing system",
    r"\bDPS\b",
    r"standing open invitation",
    r"standing invitation",
    r"open framework",
    r"panel reset",
    r"qualification system",
    r"multi[- ]use list",
    r"supplier panel",
)

_ALREADY_DECIDED_PATTERNS = (
    r"contract award notice",
    r"award notice",
    r"\bcan-standard\b",
    r"awarded to suppliers",
    r"contract notice.*result",
)

_COMPETITIVE_PATTERNS = (
    r"request for tender",
    r"\bRFT\b",
    r"invitation to tender",
    r"\bITT\b",
    r"request for proposal",
    r"\bRFP\b",
    r"request for quotation",
    r"\bRFQ\b",
    r"call for tender",
    r"\bCFT\b",
    r"pre[- ]?qualification questionnaire",
    r"\bPQQ\b",
)

# OCDS `tender.status` values, from the OCDS codelist. `planning` is the
# machine-readable marker that a notice precedes the tender itself --
# confirmed live on UKRI-6251, which returned status "planning" with no
# tenderPeriod at all.
_OCDS_STATUS_CLASS = {
    "planning": "MARKET_ENGAGEMENT",
    "planned": "MARKET_ENGAGEMENT",
    "active": "COMPETITIVE",
    "complete": "ALREADY_DECIDED",
    "unsuccessful": "ALREADY_DECIDED",
    "cancelled": "ALREADY_DECIDED",
    "withdrawn": "ALREADY_DECIDED",
}


@dataclass(frozen=True)
class NoticeClassification:
    """One notice's class, with the evidence that produced it.

    `evidence` is never empty for a non-UNKNOWN class -- a classification
    a human cannot check is one this project has already been burned by.
    """

    notice_class: str
    evidence: str
    matched_on: str

    def __post_init__(self) -> None:
        if self.notice_class not in CLASSES:
            raise NoticeClassError(
                f"class must be one of {CLASSES}, got {self.notice_class!r}")
        if self.notice_class != "UNKNOWN" and not self.evidence.strip():
            raise NoticeClassError(
                f"a {self.notice_class} classification must carry the "
                "evidence that produced it -- a verdict a human cannot "
                "check is not a verdict")

    @property
    def answerable_without_qualification(self) -> bool:
        """True only for MARKET_ENGAGEMENT. A rolling-admission scheme
        still applies its selection criteria; it merely removes the
        deadline. Kept as a property rather than a stored flag so it
        cannot drift from the class it describes."""
        return self.notice_class == "MARKET_ENGAGEMENT"


def _search(text: str, patterns: Tuple[str, ...]) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0)
    return None


def classify_notice(
    *,
    title: str = "",
    notice_type: str = "",
    procedure: str = "",
    ocds_status: str = "",
    description: str = "",
) -> NoticeClassification:
    """Classify one notice from whatever its source published.

    Every argument is optional and defaults to empty, because sources
    genuinely differ in what they carry: GETS states `tender_type`, TED
    states `procedure-type`, UK OCDS states `tender.status`. A caller
    passes what it has; absent fields simply do not vote.

    Precedence is deliberate and ordered by reliability, strongest
    first:

      1. OCDS `tender.status` -- a structured codelist value, not prose
      2. the source's own notice-type / procedure field
      3. the title
      4. the description

    Description is last and title second-last because both are
    buyer-written free text: a tender whose description mentions "a
    previous market engagement exercise" is still a tender, and letting
    prose outvote a structured field is how a confident wrong answer
    gets produced.
    """
    status = (ocds_status or "").strip().lower()
    if status in _OCDS_STATUS_CLASS:
        return NoticeClassification(
            notice_class=_OCDS_STATUS_CLASS[status],
            evidence=f"OCDS tender.status = {status!r}",
            matched_on="ocds_status",
        )

    for field_name, raw in (("notice_type", notice_type),
                            ("procedure", procedure),
                            ("title", title),
                            ("description", description)):
        text = (raw or "").strip()
        if not text:
            continue
        for cls, patterns in (
            ("ALREADY_DECIDED", _ALREADY_DECIDED_PATTERNS),
            ("MARKET_ENGAGEMENT", _MARKET_ENGAGEMENT_PATTERNS),
            ("ROLLING_ADMISSION", _ROLLING_ADMISSION_PATTERNS),
            ("COMPETITIVE", _COMPETITIVE_PATTERNS),
        ):
            hit = _search(text, patterns)
            if hit:
                return NoticeClassification(
                    notice_class=cls,
                    evidence=f"{field_name} matched {hit!r} in: {text[:160]}",
                    matched_on=field_name,
                )

    return NoticeClassification(
        notice_class="UNKNOWN",
        evidence="",
        matched_on="",
    )


_HEADER = (
    "NOTICE CLASS -- what kind of thing this is, not whether you qualify",
    "",
    "MARKET_ENGAGEMENT  the buyer is asking what is possible, before a",
    "                   tender exists. Nothing is being awarded, so there",
    "                   is nothing to qualify for. Answerable by anyone.",
    "ROLLING_ADMISSION  a DPS, framework or panel admitting suppliers",
    "                   throughout its life. Criteria still apply; the",
    "                   deadline does not.",
    "COMPETITIVE        an ordinary tender. Criteria and deadline are real.",
    "ALREADY_DECIDED    the work is gone. Intelligence only.",
    "UNKNOWN            the notice does not say. NOT 'probably a tender'.",
    "",
)


def format_classification(c: NoticeClassification) -> str:
    """Render one classification with its evidence attached."""
    if not isinstance(c, NoticeClassification):
        raise NoticeClassError(
            f"expected a NoticeClassification, got {type(c).__name__}")
    lines = list(_HEADER)
    lines.append(f"class    : {c.notice_class}")
    lines.append(f"matched  : {c.matched_on or '(nothing)'}")
    if c.evidence:
        lines.append(f"evidence : {c.evidence}")
    if c.answerable_without_qualification:
        lines.append(
            "NOTE     : this notice can be answered with no turnover, "
            "insurance, references or certifications.")
    return "\n".join(lines)
