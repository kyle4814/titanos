"""Can you physically reach this opportunity, regardless of whether you
qualify for it?

WHY THIS EXISTS
---------------
`qualification.py` answers "do the published criteria block this
operator". It is good at that. It is also, by itself, insufficient, and
one notice proved it:

  PNG National Procurement Commission, NPC/2026-26, e-Government
  Procurement. Its own RFP says "a two-envelope system with rated
  criteria, WITHOUT PREQUALIFICATION ... and is open to all eligible
  Bidders."

Zero eligibility criteria. Exactly the language this project spent nine
cycles hunting for. And it was unreachable anyway:

  - a non-refundable PGK 5,000 fee (about AUD 1,900) just to obtain the
    bidding document
  - "Electronic Bidding will not be permitted" -- sealed paper
    envelopes, physically delivered to Port Moresby

Every filter in this repository scored that notice as unresolved-but-
promising. None of them could see either wall.

THE DISTINCTION THIS MODULE DRAWS
---------------------------------
A QUALIFICATION barrier is about who you are: turnover, insurance,
references, certifications. `qualification.py` owns those.

An ACCESS barrier is about what it costs and what it physically takes to
participate at all, and it applies identically to a global consultancy
and a solo operator. They are different questions and they fail
independently -- a notice can be wide open on one and shut on the other,
which is exactly what PNG was.

  `DOCUMENT_FEE`        money required before you can even read the
                        tender documents
  `PHYSICAL_SUBMISSION`  paper, sealed envelopes, hand delivery, or an
                        explicit prohibition on electronic bidding
  `IN_PERSON_REQUIRED`   a compulsory site visit or pre-bid meeting
  `LOCAL_ENTITY`         a local company, agent, sponsor or registration
                        required in-country
  `BID_SECURITY`         a bond or guarantee that must be lodged

WHAT IT WILL NOT DO
-------------------
It reads text a caller already has. No network, no fetching, no scoring
into a single number.

It never invents a barrier and never converts silence into clearance.
`NONE_DETECTED` means exactly "none of these patterns appeared in the
text supplied" -- not "this notice has no access barriers". A notice
whose fee sits in a document nobody fetched is indistinguishable from a
free one, and this module says so rather than implying otherwise.

The asymmetry is deliberate and runs toward caution: a false positive
costs the operator a second look at a notice that turns out fine. A
false negative costs an application to something he can never submit --
or, worse, AUD1,900 spent finding out.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple

__all__ = [
    "AccessBarrierError",
    "BARRIER_KINDS",
    "AccessBarrier",
    "AccessAssessment",
    "assess_access",
    "format_access",
]


class AccessBarrierError(ValueError):
    """Raised when a caller asks this module to assert something it
    cannot support -- an unknown barrier kind, or a detected barrier
    with no quoted evidence behind it."""


BARRIER_KINDS = (
    "DOCUMENT_FEE",
    "PHYSICAL_SUBMISSION",
    "IN_PERSON_REQUIRED",
    "LOCAL_ENTITY",
    "BID_SECURITY",
)

# Every pattern below was written against real notice text. The PNG ones
# are quoted verbatim from NPC/2026-26; the rest are the standard
# procurement phrasings that surround them.
_PATTERNS = {
    "DOCUMENT_FEE": (
        r"non[- ]refundable fee",
        r"upon payment of a[n]? (?:non[- ]refundable )?fee",
        r"document(?:s)? (?:may be|can be|will be) (?:purchased|obtained).{0,60}fee",
        r"fee of [A-Z]{2,3}\s?[\d,]+",
        r"tender document.{0,40}(?:cost|price|fee)",
        r"payment of (?:a )?[A-Z]{2,3}\s?[\d,]+",
    ),
    "PHYSICAL_SUBMISSION": (
        r"electronic bidding will not be permitted",
        r"sealed (?:bid|envelope|tender|proposal)",
        r"hand[- ]deliver",
        r"delivered? (?:by hand|in person)",
        r"hard cop(?:y|ies) (?:must|shall|are to) be",
        r"outer .{0,20}envelope",
        r"original bid.{0,30}envelope",
        r"by post or courier",
    ),
    "IN_PERSON_REQUIRED": (
        r"(?:mandatory|compulsory) (?:site visit|pre[- ]bid|briefing)",
        r"site visit is (?:mandatory|compulsory|required)",
        r"attendance (?:is|shall be) (?:mandatory|compulsory)",
        r"pre[- ]bid (?:meeting|conference) is (?:mandatory|compulsory)",
    ),
    "LOCAL_ENTITY": (
        r"local(?:ly)? (?:registered|incorporated|licen[cs]ed)",
        r"must be (?:registered|incorporated) in",
        r"local (?:agent|sponsor|partner) (?:is )?(?:required|mandatory)",
        r"trade licen[cs]e",
        r"commercial registration",
        r"nationally registered (?:supplier|bidder|contractor)",
    ),
    "BID_SECURITY": (
        r"bid security",
        r"bid bond",
        r"performance (?:bond|guarantee)",
        r"tender guarantee",
        r"earnest money deposit",
    ),
}


@dataclass(frozen=True)
class AccessBarrier:
    """One detected barrier, with the text that produced it. Evidence is
    mandatory: a barrier a human cannot check is a barrier this project
    has already been burned by asserting."""

    kind: str
    matched: str
    evidence: str

    def __post_init__(self) -> None:
        if self.kind not in BARRIER_KINDS:
            raise AccessBarrierError(
                f"kind must be one of {BARRIER_KINDS}, got {self.kind!r}")
        if not self.matched.strip() or not self.evidence.strip():
            raise AccessBarrierError(
                f"a {self.kind} barrier must carry the text that produced "
                "it -- an unevidenced barrier is a guess")


@dataclass(frozen=True)
class AccessAssessment:
    """What a caller learned about reaching this notice.

    `text_was_supplied` is separate from `barriers` on purpose. No
    barriers found in text nobody read is a completely different state
    from no barriers found in a full tender document, and collapsing the
    two would let an unread notice look clean.
    """

    barriers: Tuple[AccessBarrier, ...]
    text_was_supplied: bool

    @property
    def status(self) -> str:
        if not self.text_was_supplied:
            return "NOT_ASSESSED"
        return "BARRIERS_FOUND" if self.barriers else "NONE_DETECTED"

    @property
    def blocks_remote_solo_operator(self) -> bool:
        """True when a barrier makes participation impossible or
        impractical for someone working alone from another country.

        DOCUMENT_FEE is deliberately NOT in this set: a fee is a cost
        decision, not an impossibility, and calling it a block would
        make this module decide something that is the operator's to
        decide. It is still reported -- loudly, since AUD1,900 to read a
        document is worth knowing before applying.
        """
        blocking = {"PHYSICAL_SUBMISSION", "IN_PERSON_REQUIRED", "LOCAL_ENTITY"}
        return any(b.kind in blocking for b in self.barriers)


# PATTERNS THE NEGATION GUARD MUST NEVER SUPPRESS.
#
# "Electronic Bidding will not be permitted" contains "will not be
# permitted" -- which is exactly the phrasing the negation guard looks
# for. But here the negated thing is ELECTRONIC bidding, which means
# paper only: the sentence IS the barrier, not a clause excusing one.
#
# Found immediately after adding the guard: it silenced the single
# clearest physical-submission statement in the PNG RFP, the notice this
# whole module exists because of. A guard that suppresses the case it
# was built to catch is worse than no guard.
_NEVER_NEGATED = frozenset({
    r"electronic bidding will not be permitted",
})


# NEGATION GUARD -- added after this module's own first live run.
#
# Scanned against six real tender documents, it flagged FOUR of them for
# PHYSICAL_SUBMISSION on the phrase "hand delivery". The surrounding
# text, in all four:
#
#   "Tenders submitted by any other means (including but not limited to:
#    by email, fax, post, hand delivery, etc.) will NOT be accepted"
#
# That is the exact OPPOSITE of a physical-submission requirement. It is
# an electronic-only clause listing hand delivery among the FORBIDDEN
# methods. The module read a prohibition as a requirement and would have
# told the operator that four reachable Irish notices were closed to him.
#
# A false positive here is not free after all: this project's whole
# argument is that a verdict a human can check is worth something and a
# confident wrong one is worth less than nothing.
#
# So: a match is discarded when the phrase sits inside a clause that
# excludes it. Deliberately narrow -- it looks for explicit rejection
# language near the match, not for any nearby "not".
_NEGATION_NEAR_MATCH = re.compile(
    r"(?:will|shall|are|is)\s+NOT\s+be\s+(?:accepted|permitted|considered)"
    r"|any other means"
    r"|other than.{0,40}(?:portal|electronic)"
    r"|not\s+be\s+accepted",
    re.IGNORECASE,
)

# How far around a match to look for that negation. Wide enough to span
# a parenthesised list of excluded methods and the verb that rejects
# them, which is the shape all four false positives took -- and no
# wider, because a window that reaches into the next sentence starts
# negating unrelated clauses.
_NEGATION_WINDOW = 160

# ONLY DELIVERY-METHOD BARRIERS CAN BE NEGATED.
#
# The false positive was specific: a list of excluded submission methods
# ("by email, fax, post, hand delivery") read as a requirement. That
# shape only exists for PHYSICAL_SUBMISSION.
#
# Applying the guard to every kind immediately caused a second, opposite
# error -- the PNG document fee was suppressed because "Electronic
# Bidding will not be permitted" sat two sentences later. A fee clause
# is never cancelled by nearby rejection language about something else,
# and neither is a bid bond or a local-registration requirement.
#
# Narrowing the guard to the one kind that needs it fixes both errors
# without trading one for the other.
_NEGATABLE_KINDS = frozenset({"PHYSICAL_SUBMISSION"})


def _is_negated(text: str, start: int, end: int) -> bool:
    """True when the matched phrase sits inside a clause forbidding it."""
    lo = max(0, start - _NEGATION_WINDOW)
    hi = min(len(text), end + _NEGATION_WINDOW)
    return bool(_NEGATION_NEAR_MATCH.search(text[lo:hi]))


def _context(text: str, start: int, end: int, width: int = 90) -> str:
    lo = max(0, start - width)
    hi = min(len(text), end + width)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def assess_access(text: str) -> AccessAssessment:
    """Scan supplied notice or document text for access barriers.

    Pure function. No network, no fetching. Pass "" and you get
    NOT_ASSESSED, which is the honest answer for a notice whose
    documents nobody has opened -- and is emphatically not NONE_DETECTED.
    """
    if not isinstance(text, str):
        raise AccessBarrierError(
            f"text must be a string, got {type(text).__name__}")
    if not text.strip():
        return AccessAssessment(barriers=(), text_was_supplied=False)

    found = []
    seen_kinds = set()
    for kind in BARRIER_KINDS:
        for pattern in _PATTERNS[kind]:
            m = None
            guarded = (kind in _NEGATABLE_KINDS
                       and pattern not in _NEVER_NEGATED)
            for candidate in re.finditer(pattern, text, re.IGNORECASE):
                if not guarded or not _is_negated(text, candidate.start(),
                                                   candidate.end()):
                    m = candidate
                    break
            if not m:
                continue
            if kind in seen_kinds:
                break
            seen_kinds.add(kind)
            found.append(AccessBarrier(
                kind=kind,
                matched=m.group(0),
                evidence=_context(text, m.start(), m.end()),
            ))
            break
    return AccessAssessment(barriers=tuple(found), text_was_supplied=True)


_HEADER = (
    "ACCESS BARRIERS -- can you reach this at all, regardless of merit",
    "",
    "Separate from qualification. PNG's NPC/2026-26 stated 'without",
    "prequalification ... open to all eligible Bidders' and was still",
    "unreachable: a non-refundable PGK5,000 document fee and 'Electronic",
    "Bidding will not be permitted'. Zero eligibility criteria, two walls.",
    "",
    "NOT_ASSESSED means nobody supplied the document text. It is NOT a",
    "clean bill of health -- an unread notice and a free one look",
    "identical from here, and this says so rather than implying otherwise.",
    "",
)


def format_access(assessment: AccessAssessment) -> str:
    """Render an assessment with every barrier's evidence attached."""
    if not isinstance(assessment, AccessAssessment):
        raise AccessBarrierError(
            f"expected an AccessAssessment, got {type(assessment).__name__}")
    lines = list(_HEADER)
    lines.append(f"status : {assessment.status}")
    if assessment.status == "NOT_ASSESSED":
        lines.append("No document text was supplied. Open the tender "
                     "documents to answer this.")
        return "\n".join(lines)
    if not assessment.barriers:
        lines.append("No access barrier matched the text supplied. That is "
                     "not proof there is none -- a fee stated in an annex "
                     "nobody fetched would not appear here.")
        return "\n".join(lines)
    if assessment.blocks_remote_solo_operator:
        lines.append("BLOCKS A REMOTE SOLO OPERATOR.")
    for b in assessment.barriers:
        lines.append(f"  [{b.kind}] matched {b.matched!r}")
        lines.append(f"      {b.evidence[:180]}")
    return "\n".join(lines)
