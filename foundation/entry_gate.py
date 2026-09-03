"""foundation/entry_gate.py -- what does STARTING this cost the operator
personally, and can any of it be discharged by doing work instead?

WHY THIS EXISTS

Every ranking surface in this repository sorts by what an opportunity is
worth. None of them sorts by what it costs to begin. Across the
2026-09-02/03/04 sweeps that produced exactly the wrong shape of report:
a EUR175,000,000 Managed ICT Security DPS at the top and a EUR250k-
turnover penetration-testing qualification system buried underneath it,
when the second is reachable and the first demands a 24x7x365 staffed
Security Operations Centre.

The operator's instruction, 2026-09-03, is the specification for this
module: find the routes that need nothing from him. That cannot be a
promise in prose. It has to be a computed field, or the next report will
be sorted by contract value again.

WHAT IT ADDS THAT `access_barriers.py` DOES NOT

`access_barriers.assess_access()` already answers "can this notice be
REACHED at all" -- document fees, paper-only submission, mandatory site
visits, bid bonds, local-entity rules. That module is not re-implemented
here and its five kinds are not re-detected; `assess_entry()` calls it
and carries its findings through untouched.

Two axes are genuinely new, and both were discovered the hard way:

  1. WHO MUST ACT. A reference contract and a professional indemnity
     policy are both "requirements", and they are not the same kind of
     obstacle. One is closed by doing work. The other is closed only by
     the operator signing something, paying for something, or being
     someone. `REQUIRES_OPERATOR` vs `DISCHARGEABLE_BY_WORK` is that
     split, and it is the whole point of the module.

  2. AT WHICH STAGE. Iarnrod Eireann's penetration-testing PQQ mentions
     insurance exactly once: "those who have been selected to proceed to
     tender stage, will be required to comply with the insurance
     requirements of the Contract". RTE's DPS makes the identical
     requirement a Pass/Fail gate at admission. Same requirement, same
     country, same instrument -- and one of them is a wall while the
     other is a thing to arrange later, once there is actual work on the
     table. A tool that reports both as "insurance required" throws away
     the single most valuable distinction this campaign found.

THE HONESTY RULE, WHICH IS THE SAME ONE AS EVERYWHERE ELSE HERE

A gate that is NOT_STATED is UNKNOWN. It is never "no requirement". The
top-level status for a clean read is `NO_GATE_STATED`, deliberately not
`UNGATED` -- a document that does not mention insurance has not told you
that no insurance is needed, and the word chosen here must not let a
caller believe otherwise. `NOT_ASSESSED` (nobody supplied text) is a
third state again, because an unread document and a permissive one look
identical from inside this module.

NO NETWORK. Pure text in, structured findings out. `assess_entry()`
takes text a caller already has; it never fetches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from foundation.access_barriers import AccessAssessment, assess_access

__all__ = [
    "EntryGateError",
    "GATE_KINDS",
    "REQUIRES_OPERATOR",
    "DISCHARGEABLE_BY_WORK",
    "STAGES",
    "SATISFIABILITY",
    "GateFinding",
    "EntryAssessment",
    "assess_entry",
    "format_entry",
    "rank_by_entry_cost",
    "SHORT_DOCUMENT_CHARS",
]


class EntryGateError(ValueError):
    """Raised on a malformed gate or a caller passing something that is
    not text. This module refuses to guess at an operator's position."""


# Every gate this module can recognise. A kind not in this tuple cannot
# be constructed -- the same closed-vocabulary discipline
# `access_barriers.BARRIER_KINDS` uses.
GATE_KINDS = (
    "ACCOUNT_REGISTRATION",
    "LEGAL_ENTITY",
    "IDENTITY_VERIFICATION",
    "CERTIFICATION",
    "INSURANCE",
    "REFERENCES",
    "LOCAL_PRESENCE",
    "STAFFED_ROUND_THE_CLOCK",
    "MINIMUM_TURNOVER",
    "ENTRY_FEE",
)

# THE SPLIT THIS MODULE EXISTS TO MAKE.
#
# REQUIRES_OPERATOR: cannot be closed by producing better work. Someone
# has to register, sign, pay, insure, or BE a thing. These are the gates
# that make an opportunity need Kyle.
#
# DISCHARGEABLE_BY_WORK: closed by doing the work, hiring, partnering, or
# by relying on another entity's resources where the buyer permits it
# (four Irish documents name that route explicitly). Real obstacles --
# but they are the kind effort moves.
REQUIRES_OPERATOR = frozenset({
    "ACCOUNT_REGISTRATION",
    "LEGAL_ENTITY",
    "IDENTITY_VERIFICATION",
    "CERTIFICATION",
    "INSURANCE",
    "ENTRY_FEE",
})
DISCHARGEABLE_BY_WORK = frozenset({
    "REFERENCES",
    "LOCAL_PRESENCE",
    "STAFFED_ROUND_THE_CLOCK",
    "MINIMUM_TURNOVER",
})

# HOW HARD EACH GATE ACTUALLY IS, calibrated against six real documents
# whose verdicts were established by reading them by hand.
#
# The first version of this module weighted by CLASS -- 10 for anything
# requiring the operator, 1 for anything else -- and ranked Asiera's
# EUR175M DPS as the single cheapest opportunity on the board. Asiera
# demands a 24x7x365 staffed Security Operations Centre. It is the least
# reachable thing found in Ireland, and the ranking put it first.
#
# "Dischargeable by work" is a statement about WHO must act, not about
# how much work. A round-the-clock staffed service and a turnover figure
# are both closed without the operator signing anything personally, and
# one of them needs a night shift while the other needs a partner's
# accounts. Weight is a separate axis from class and has to be one.
_GATE_WEIGHT = {
    # Structural. Only a differently-shaped organisation clears these --
    # no amount of effort, money or paperwork does it alone.
    "STAFFED_ROUND_THE_CLOCK": 10,
    "LOCAL_PRESENCE": 10,
    # Cost money or credentials the operator must personally hold.
    "INSURANCE": 6,
    "CERTIFICATION": 6,
    "ENTRY_FEE": 4,
    # Paperwork with a known path.
    "LEGAL_ENTITY": 3,
    "IDENTITY_VERIFICATION": 2,
    "ACCOUNT_REGISTRATION": 1,
    # Real obstacles with a route through them the buyers themselves
    # write down -- four Irish documents name reliance on a third
    # party's resources for exactly these two.
    "REFERENCES": 5,
    "MINIMUM_TURNOVER": 3,
}
if set(_GATE_WEIGHT) != set(GATE_KINDS):
    raise EntryGateError(
        "every gate kind needs a weight -- missing: "
        f"{sorted(set(GATE_KINDS) - set(_GATE_WEIGHT))}")

# Every kind is in exactly one class. Checked at import rather than
# trusted: a kind added to GATE_KINDS and forgotten here would silently
# vanish from every count this module produces.
if set(GATE_KINDS) != REQUIRES_OPERATOR | DISCHARGEABLE_BY_WORK:
    raise EntryGateError(
        "every GATE_KINDS entry must be classified exactly once as "
        "REQUIRES_OPERATOR or DISCHARGEABLE_BY_WORK -- unclassified: "
        f"{sorted(set(GATE_KINDS) - REQUIRES_OPERATOR - DISCHARGEABLE_BY_WORK)}")

# Below this many characters a document is treated as a fragment and
# `format_entry()` says so. Calibrated on the six real documents read
# 2026-09-03/04: the full PQQs run 68,000-134,000 characters, and the
# one fragment that scored misleadingly cheap was 7,569.
SHORT_DOCUMENT_CHARS = 20_000

# When the requirement bites. UNKNOWN is the default and by far the most
# common: most documents state a requirement without saying when.
STAGES = ("ADMISSION", "POST_ADMISSION", "UNKNOWN")

# HOW an admission requirement can be met. The distinction that separated
# the campaign's one pursuable Irish lead from the noes, and which the
# first version of this module collapsed:
#   HELD         -- you must POSSESS the thing now. A real wall.
#                   RTE: "must maintain the following minimum levels of
#                   insurance cover: Public Liability EUR6.5M ..."
#   DECLARATION  -- satisfiable by a STATEMENT, not possession. Soft.
#                   GNI: "provide a letter ... stating cover can be
#                   arranged"; HSE: "has in place (or the ability to
#                   obtain)"; Asiera: "willing and able to raise ... if
#                   awarded".
#   UNSPECIFIED  -- the document did not say. UNKNOWN, not soft.
SATISFIABILITY = ("HELD", "DECLARATION", "UNSPECIFIED")

# Verbatim softeners from the real Irish documents (2026-09). A
# DECLARATION marker near a requirement means it is met by a statement of
# intent or arrangeability, not by holding the thing.
_DECLARATION_MARKERS = (
    "ability to obtain",
    "can be arranged",
    "willing and able to raise",
    "willing to raise",
    "should the company be awarded",
    "if awarded",
    "provide a letter",
    "letter from their insurers",
    "statement confirming",
    "confirm that the company",
    "has applied for",
    "will be made available on request",
)

# Verbatim "you must possess it" language. Only consulted when no
# DECLARATION marker is present, and only to promote UNSPECIFIED -> HELD;
# a softener always wins, because a document that offers a soft route has
# offered it.
_HELD_MARKERS = (
    "must maintain",
    "shall maintain",
    "effect and maintain",
    "must have in place",
    "must hold",
    "must possess",
    "must be in possession of",
    "currently hold",
)

# How wide to read around a requirement for satisfiability language. Same
# order of magnitude as _STAGE_WINDOW; the softener usually sits in the
# same clause as the requirement.
_SATISFIABILITY_WINDOW = 220

# Phrases that place a nearby requirement AFTER admission. Taken verbatim
# from real documents read 2026-09-03/04 -- Iarnrod Eireann 7289/7162/
# 7764, HSE 21236/22167, Asiera ICTSS.
_POST_ADMISSION_MARKERS = (
    "selected to call-off",
    "selected to proceed to tender stage",
    "at time of contract award",
    "prior to the award",
    "should the company be awarded",
    "if awarded",
    "when selected to call-off",
    "at call-off stage",
    "successful tenderer shall be required",
)

# Phrases that place a requirement AT admission. These BEAT the
# post-admission markers above when both appear near a requirement.
#
# RTE's insurance table -- "P3 Minimum Insurance Requirements ...
# Pass/Fail" -- was read as POST_ADMISSION by the first version of this
# module, because an unrelated tax-clearance sentence sat inside the
# window. That single mistake inverts the one distinction the module
# exists to make: RTE demands cover held at admission and Irish Rail
# defers it, and the tool said the opposite. When a document says both
# "pass/fail" and "at time of contract award" near a requirement, the
# pass/fail is the one that decides whether you can start.
_ADMISSION_MARKERS = (
    "pass/fail",
    "pass / fail",
    "minimum qualification criteria",
    "minimum requirement",
    "minimum levels of insurance",
    "in order to proceed to the next stage",
    "will be excluded",
    "may be excluded",
)

# How far from a requirement a staging phrase may sit and still be read
# as governing it. Was 400, which reached into the next clause's staging
# language; 180 is about one sentence in the documents this was
# calibrated against.
_STAGE_WINDOW = 180

# Patterns per gate. Deliberately narrow: a gate detector that fires on
# everything gets ignored, which returns the operator to reading 40-page
# PQQs by hand, which is the state this exists to end.
_PATTERNS: Dict[str, Tuple[str, ...]] = {
    "ACCOUNT_REGISTRATION": (
        r"must (?:first )?(?:register|be registered) (?:on|with|as)",
        r"create an account",
        r"registration (?:on|with) the (?:portal|platform|system) is (?:required|mandatory)",
        r"registered users? only",
    ),
    # `company registration number` alone was a FALSE POSITIVE on
    # Iarnrod Eireann 7289 -- it matched the applicant-details form
    # ("1.5 Company registration number:"), which is a field asking who
    # you are, not a requirement to be a company. Every PQQ in existence
    # has that field, so the pattern fired on all of them, at weight 3.
    # A requirement has requirement grammar; a form label does not.
    "LEGAL_ENTITY": (
        r"must be (?:a )?(?:legally )?(?:registered|incorporated) (?:company|entity|business)",
        r"(?:must (?:provide|submit)|provide) (?:a |their )?certificate of incorporation",
        r"only (?:registered|incorporated) (?:companies|entities|businesses) (?:may|can)",
    ),
    "IDENTITY_VERIFICATION": (
        r"tax clearance certificate",
        r"identity verification",
        r"proof of identity",
        r"know.your.customer",
    ),
    # A BARE `iso 9001` MATCH IS NOT A REQUIREMENT, and both false
    # positives found were the same failure in different clothes:
    #
    #   RTE      "Support for certification and regulatory compliance
    #             (e.g., ISO 27001, GDPR)"  <- describing the SERVICES
    #             BEING BOUGHT, not a condition on the bidder
    #   Irish    "Is the Applicants Quality Management System currently
    #   Rail      certified as compliant with EN ISO 9001:2000"  <- a
    #             scored question, answerable "no"
    #
    # This is the same class as the TED sweep matching "Market research
    # services" as market engagement when it was the thing being
    # procured. A standard named in a document is not a standard
    # demanded of you -- the requirement grammar has to be there too.
    "CERTIFICATION": (
        r"must (?:hold|possess|maintain|have) (?:a |an )?(?:valid |current )?"
        r"(?:[\w ]{0,30})?(?:accreditation|certification|iso\s?\d{4,5})",
        r"(?:accreditation|certification) (?:is|are) (?:required|mandatory|essential)",
        r"(?:hold|holding) (?:a |an )?(?:valid )?cyber essentials",
        r"certified to iso\s?\d{4,5}",
    ),
    "INSURANCE": (
        # Added after Iarnrod Eireann 7289/7162/7764 -- their ONLY
        # insurance sentence is "comply with the insurance requirements
        # of the Contract", which named no policy type and so was not
        # detected at all. A gate this module cannot see cannot be
        # reported as deferred, which is the whole finding for those
        # three documents.
        r"insurance requirements of the",
        r"professional indemnity",
        r"public liability insurance",
        r"employer'?s liability insurance",
        r"cyber (?:security |liability )?insurance",
        r"minimum (?:levels? of )?insurance",
    ),
    "REFERENCES": (
        r"(?:at least |a minimum of )?(?:two|three|four|five|\d+)\s?\(?\d*\)?\s?"
        r"(?:comparable |similar |client |customer )?references?",
        r"reference (?:sites?|contracts?|projects?)",
        r"evidence of (?:at least )?(?:two|three|\d+)\s?\(?\d*\)? (?:customers|occasions)",
    ),
    "LOCAL_PRESENCE": (
        r"staff based (?:with)?in",
        r"based in the republic",
        r"locally based (?:staff|resources|personnel)",
        r"on-?site within \d+\s?(?:hrs|hours)",
        r"(?:dublin|london|local)[- ]based (?:non-contract )?resources",
    ),
    "STAFFED_ROUND_THE_CLOCK": (
        r"24\s?[/x]\s?7",
        r"24 hours? a day,? 7 days? a week",
        r"365 days? a year",
        r"round[- ]the[- ]clock",
    ),
    "MINIMUM_TURNOVER": (
        r"minimum (?:annual )?turnover",
        r"annual turnover of",
        r"turnover (?:of at least|exceeded|must exceed)",
    ),
    "ENTRY_FEE": (
        r"non-?refundable fee",
        r"fee of (?:eur|gbp|usd|aud|pgk|€|£|\$)",
        r"payment of a fee",
    ),
}

_COMPILED = {
    kind: tuple(re.compile(p, re.IGNORECASE) for p in pats)
    for kind, pats in _PATTERNS.items()
}


@dataclass(frozen=True)
class GateFinding:
    """One requirement the document actually stated, quoted so it can be
    checked and disputed. `quote` is never paraphrased -- a summarised
    criterion is an invented one."""

    kind: str
    matched: str
    quote: str
    stage: str
    satisfiability: str = "UNSPECIFIED"

    def __post_init__(self) -> None:
        if self.kind not in GATE_KINDS:
            raise EntryGateError(
                f"unknown gate kind {self.kind!r} -- must be one of {GATE_KINDS}")
        if self.stage not in STAGES:
            raise EntryGateError(
                f"unknown stage {self.stage!r} -- must be one of {STAGES}")
        if self.satisfiability not in SATISFIABILITY:
            raise EntryGateError(
                f"unknown satisfiability {self.satisfiability!r} -- must be "
                f"one of {SATISFIABILITY}")
        if not self.quote.strip():
            raise EntryGateError(
                f"a {self.kind} finding with no quotable evidence is an "
                "assertion, not a finding")

    @property
    def satisfiable_by_declaration(self) -> bool:
        """Met by a statement of intent or arrangeability, not by holding
        the thing. Soft even at admission -- see SATISFIABILITY."""
        return self.satisfiability == "DECLARATION"

    @property
    def requires_operator(self) -> bool:
        return self.kind in REQUIRES_OPERATOR

    @property
    def blocks_starting(self) -> bool:
        """Does this stop the operator STARTING, as opposed to being a
        thing to arrange later?

        A requirement the document explicitly defers to after admission
        does not block starting. An `UNKNOWN` stage does -- treating an
        unstated stage as "probably later" would be exactly the
        optimistic guess this repository refuses everywhere else.
        """
        return self.stage != "POST_ADMISSION"


@dataclass(frozen=True)
class EntryAssessment:
    """What it costs the operator to begin.

    `text_was_supplied` is kept separate from `gates` for the same
    reason `AccessAssessment` keeps it separate: nothing found in text
    nobody read is a different state from nothing found in a full PQQ.
    """

    gates: Tuple[GateFinding, ...]
    access: AccessAssessment
    text_was_supplied: bool
    # How much text this verdict was computed over. `entry_cost` is only
    # comparable between comparably complete reads, and nothing enforces
    # that -- so the number that would let a caller notice is carried on
    # the assessment rather than left implicit. Asiera's Part B is 7,569
    # characters of a multi-document pack and scored cheapest in the
    # first run precisely because most of its requirements are in files
    # this assessment never saw.
    chars_read: int = 0

    @property
    def status(self) -> str:
        if not self.text_was_supplied:
            return "NOT_ASSESSED"
        if self.gates or self.access.barriers:
            return "GATES_FOUND"
        # NOT `UNGATED`. The document did not say there is no gate; it
        # did not say anything. See the module docstring's honesty rule.
        return "NO_GATE_STATED"

    @property
    def operator_gates(self) -> Tuple[GateFinding, ...]:
        """Gates that need the operator personally, bite at the point of
        entry, AND require holding the thing -- the hard walls.

        A declaration-satisfiable gate is excluded here: 'provide a
        letter that cover can be arranged' does not require possessing
        EUR6.5M of insurance, so it is not the wall that 'must maintain
        EUR6.5M' is. Those are surfaced by `declaration_gates`."""
        return tuple(g for g in self.gates
                     if g.requires_operator and g.blocks_starting
                     and not g.satisfiable_by_declaration)

    @property
    def declaration_gates(self) -> Tuple[GateFinding, ...]:
        """Operator-class admission requirements the document says are
        met by a STATEMENT -- a broker letter, an ability-to-obtain, a
        willing-to-raise-if-awarded. Real, but not a wall: Kyle can
        satisfy them now without possessing the thing."""
        return tuple(g for g in self.gates
                     if g.requires_operator and g.blocks_starting
                     and g.satisfiable_by_declaration)

    @property
    def deferred_gates(self) -> Tuple[GateFinding, ...]:
        """Real requirements the document itself puts after admission.
        These turn a 'no' into a 'later'."""
        return tuple(g for g in self.gates if not g.blocks_starting)

    @property
    def work_gates(self) -> Tuple[GateFinding, ...]:
        return tuple(g for g in self.gates
                     if not g.requires_operator and g.blocks_starting)

    @property
    def entry_cost(self) -> int:
        """Sort key. Lower is cheaper to begin.

        Counts only what blocks STARTING, weighted per kind by
        `_GATE_WEIGHT` (see the note there for the ranking this got
        wrong), plus the access barriers `access_barriers.py` found.

        Deliberately crude and deliberately not a score out of ten: it
        exists to put the reachable thing at the top of a list, not to
        be quoted as a measurement. It is comparable only between
        documents of comparable completeness -- see `chars_read`.
        """
        gates = self.operator_gates + self.work_gates
        # A declaration-satisfiable gate is a statement Kyle writes now,
        # not a thing he must possess -- weight 1 each, far below a held
        # requirement's _GATE_WEIGHT, so an opportunity gated only by
        # declarations ranks near an ungated one.
        return (sum(_GATE_WEIGHT[g.kind] for g in gates)
                + len(self.declaration_gates)
                + 2 * len(self.access.barriers))

    def gate(self, kind: str) -> Optional[GateFinding]:
        if kind not in GATE_KINDS:
            raise EntryGateError(f"unknown gate kind {kind!r}")
        for g in self.gates:
            if g.kind == kind:
                return g
        return None


def _context(text: str, start: int, end: int, width: int = 110) -> str:
    return " ".join(text[max(0, start - width):end + width].split())


def _stage_for(text: str, start: int, end: int) -> str:
    """Read the document's own staging language around a requirement.

    Only ever returns POST_ADMISSION on an explicit marker. There is no
    rule that infers ADMISSION -- a requirement stated with no staging
    language is UNKNOWN, and `blocks_starting` already treats UNKNOWN
    conservatively.
    """
    window = text[max(0, start - _STAGE_WINDOW):end + _STAGE_WINDOW].lower()
    # Admission evidence wins. See _ADMISSION_MARKERS for the real case
    # that forced this ordering.
    for marker in _ADMISSION_MARKERS:
        if marker in window:
            return "ADMISSION"
    for marker in _POST_ADMISSION_MARKERS:
        if marker in window:
            return "POST_ADMISSION"
    return "UNKNOWN"


def _satisfiability_for(text: str, kind: str) -> str:
    """Is this requirement met by holding the thing, or by a statement?

    Scans EVERY occurrence of `kind`'s own patterns, not just the first
    match reported. A document states a requirement once and its
    satisfiability elsewhere: GNI names "Insurance requirements" in a
    heading and "provide a letter ... can be arranged" a paragraph later;
    Asiera's tax-clearance softener "has applied for" sits well away from
    the first tax mention. A window around only the first match misses
    both.

    A DECLARATION softener anywhere near any occurrence wins over HELD: a
    document that offers a soft route has offered it.
    """
    lowered = text.lower()
    saw_held = False
    for pattern in _COMPILED[kind]:
        for m in pattern.finditer(text):
            window = lowered[max(0, m.start() - _SATISFIABILITY_WINDOW):
                             m.end() + _SATISFIABILITY_WINDOW]
            for marker in _DECLARATION_MARKERS:
                if marker in window:
                    return "DECLARATION"
            if not saw_held:
                saw_held = any(hm in window for hm in _HELD_MARKERS)
    return "HELD" if saw_held else "UNSPECIFIED"


def assess_entry(text: str) -> EntryAssessment:
    """Read one tender/programme document for what it costs to begin.

    Each gate kind is reported at most once, at its FIRST occurrence --
    a 40-page PQQ mentions insurance eleven times and eleven identical
    findings is noise, not evidence.
    """
    if not isinstance(text, str):
        raise EntryGateError(
            f"assess_entry() takes document text, got {type(text).__name__}")

    supplied = bool(text.strip())
    access = assess_access(text)
    if not supplied:
        return EntryAssessment(gates=(), access=access,
                               text_was_supplied=False, chars_read=0)

    found: list[GateFinding] = []
    for kind in GATE_KINDS:
        for pattern in _COMPILED[kind]:
            m = pattern.search(text)
            if not m:
                continue
            found.append(GateFinding(
                kind=kind,
                matched=m.group(0),
                quote=_context(text, m.start(), m.end()),
                stage=_stage_for(text, m.start(), m.end()),
                satisfiability=_satisfiability_for(text, kind),
            ))
            break
    return EntryAssessment(gates=tuple(found), access=access,
                           text_was_supplied=True, chars_read=len(text))


def rank_by_entry_cost(items):
    """Sort `(label, EntryAssessment)` pairs cheapest-to-start first.

    Exists so "put the reachable ones first" is a function rather than a
    good intention. Ties break on label so the order is deterministic.
    """
    for entry in items:
        if (not isinstance(entry, tuple) or len(entry) != 2
                or not isinstance(entry[1], EntryAssessment)):
            raise EntryGateError(
                "rank_by_entry_cost() takes (label, EntryAssessment) pairs")
    return sorted(items, key=lambda pair: (pair[1].entry_cost, pair[0]))


def format_entry(assessment: EntryAssessment) -> str:
    """Operator-facing render. Leads with what it costs to START,
    because that is the question this module was built to answer."""
    if not isinstance(assessment, EntryAssessment):
        raise EntryGateError(
            "format_entry() takes an EntryAssessment, not "
            f"{type(assessment).__name__}")

    lines = ["WHAT IT COSTS TO START", ""]
    if assessment.status == "NOT_ASSESSED":
        lines.append(
            "NOT_ASSESSED -- no document text was supplied. This is not a "
            "clean bill of health: an unread document and a permissive one "
            "look identical from here.")
        return "\n".join(lines)

    if assessment.status == "NO_GATE_STATED":
        lines.append(
            "NO_GATE_STATED -- this document states no entry requirement "
            "this module recognises.")
        lines.append(
            "That is NOT the same as 'no requirement'. A document that "
            "does not mention insurance has not told you none is needed. "
            "UNKNOWN, not zero.")
        return "\n".join(lines)

    if assessment.chars_read < SHORT_DOCUMENT_CHARS:
        lines.append(
            f"CAUTION: only {assessment.chars_read:,} characters were read. "
            f"Procurement packs run to tens of thousands, and a fragment "
            f"states few requirements simply because most of them are in "
            f"the files this did not see. A low cost here may mean an "
            f"unread pack, not an open door.")
        lines.append("")

    ops = assessment.operator_gates
    lines.append(
        f"needs the operator personally : {len(ops)}"
        f"   (entry cost {assessment.entry_cost})")
    for g in ops:
        lines.append(f"  [{g.kind}] {g.matched!r}")
        lines.append(f"      {g.quote}")

    declarations = assessment.declaration_gates
    if declarations:
        lines.append("")
        lines.append(
            f"satisfiable by a STATEMENT, not by holding the thing : "
            f"{len(declarations)}   (a broker letter, an ability-to-obtain, "
            f"a willing-to-raise-if-awarded -- Kyle can meet these now)")
        for g in declarations:
            lines.append(f"  [{g.kind}] {g.matched!r}")
            lines.append(f"      {g.quote}")

    work = assessment.work_gates
    if work:
        lines.append("")
        lines.append(f"closable by doing the work / partnering : {len(work)}")
        for g in work:
            lines.append(f"  [{g.kind}] {g.matched!r}")
            lines.append(f"      {g.quote}")

    deferred = assessment.deferred_gates
    if deferred:
        lines.append("")
        lines.append(
            f"NOT required to start -- the document defers these : "
            f"{len(deferred)}")
        for g in deferred:
            lines.append(f"  [{g.kind}] {g.matched!r}")
            lines.append(f"      {g.quote}")

    if assessment.access.barriers:
        lines.append("")
        lines.append("access barriers (see access_barriers.py):")
        for b in assessment.access.barriers:
            lines.append(f"  [{b.kind}] {b.matched!r}")

    lines.append("")
    lines.append(
        "Every gate above is quoted so it can be checked and disputed. A "
        "gate NOT listed is UNKNOWN -- this module found no statement of "
        "it, which is not a statement that it does not exist.")
    return "\n".join(lines)
