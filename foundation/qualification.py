"""Join a notice's bidder conditions (`foundation/eligibility.py`'s
`EligibilityAssessment`) with a real operator's real capabilities
(`OperatorProfile`) and produce a qualification verdict a human can
check clause-by-clause, instead of one read by hand, one notice at a
time.

THE ONE RULE THIS MODULE ENFORCES STRUCTURALLY

Absent criteria data means `INSUFFICIENT_DATA`, never `QUALIFIED`. A
missing requirement is not a satisfied requirement, and an unresolved
dimension is not a cleared one. `DISQUALIFIED` requires at least one
positively-identified failing requirement -- never an inference from
silence, an unlabeled TED code, or a keyword match against free text.
Both directions of this rule are enforced twice: once by `assess()`'s
own band arithmetic, and again, independently, by
`QualificationResult.__post_init__`, which recomputes the same
has-barrier / has-unresolved facts from the factors it was actually
handed and raises `QualificationIntegrityError` if the claimed band
disagrees -- the same two-independent-points discipline this
repository's other switch/gate modules already use (see
`foundation/winnability.py`, `foundation/publication_gate.py`).

WHAT THIS MODULE DOES

Five dimensions, one per `OperatorProfile` field, each checked
independently and always present exactly once on a `QualificationResult`
in a fixed order: `technical_staff_capacity`, `certifications`,
`insurance`, `corporate_references`, `submission_language`. Each
dimension reads only fields `assess_eligibility()` already computed
(TED's own selection-criterion codes, grouped by `eligibility.py`'s own
category prefixes) plus the raw quoted description text -- this module
never re-parses the TED notice dict itself, and never modifies
`eligibility.py`.

THE HONEST LIMIT -- WHY MOST DIMENSIONS LAND ON `INFO`, NOT A VERDICT

TED's eForms codelist is coarser than the real requirements text.
`slc-stand-other` ("Other economic or financial requirements") is where
a real notice's insurance clause can live -- there is no guarantee a
notice tags insurance with the dedicated `slc-stand-ins` code (the live
degewo AG notice this module was tested against, 578580-2026, is
exactly this case: its EUR 3,000,000 professional-indemnity-insurance
requirement is coded `slc-stand-other`, not `slc-stand-ins`). Likewise
`slc-abil-staff-yrly-avg-mp` ("Average yearly manpower") carries a real
headcount threshold ("at least 3 penetration testers") only in its free
text, not as a structured number anywhere TED returns.

This module refuses to keyword-scan that free text to manufacture a
number or a certainty it doesn't structurally have -- the same refusal
`eligibility.py`'s own docstring names as the failure mode this whole
line of work exists to correct, one layer further in would just move
the mistake, not fix it. Where a requirement CODE is present but this
module cannot positively confirm from codes alone whether the operator
clears it (an ambiguous "other" economic code, a staff-capacity code
with no parseable threshold, a certification code the operator holds
*some* but not necessarily the *right* certification against), the
factor's verdict is `INFO`: known to exist, not resolved either way.
`INFO` behaves like `UNKNOWN` for banding purposes -- it can never
produce `QUALIFIED`, and it can never by itself produce `DISQUALIFIED`
either. The raw quoted notice text is always attached to `INFO`
evidence, so a human loses no information -- they get the real clause
to read, not a machine's guess about what it means.

Only two dimensions in this module can ever produce a hard `BARRIER`:
`corporate_references` (TED's own dedicated `slc-abil-ref-*` codes,
checked against the operator's own evidenced reference count) and
`submission_language` (TED's own `submission-language` field, checked
against the operator's own declared languages). Both are drawn from
codes/fields with no ambiguity about what they mean -- a `BARRIER` here
is not a guess.

WHAT THIS DOES NOT DO

  - No network I/O. Pure function over an already-built
    `EligibilityAssessment` and an already-declared `OperatorProfile`.
  - No modification of `foundation/eligibility.py`,
    `foundation/relevance.py`, `foundation/winnability.py`, or
    `foundation/shortlist.py` -- this module only imports
    `EligibilityAssessment`/`CodedRequirement` from the first.
  - No probability, score-out-of-ten, or win-likelihood language --
    same discipline `winnability.py` enforces on itself; this module
    does not import that check but does not need to, since it never
    computes a number in the first place.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Tuple

from foundation.eligibility import CodedRequirement, EligibilityAssessment

__all__ = [
    "BANDS",
    "DIMENSIONS",
    "QualificationIntegrityError",
    "OperatorProfile",
    "QualificationFactor",
    "QualificationResult",
    "assess",
    "format_result",
]


class QualificationIntegrityError(ValueError):
    """Raised when a caller (or this module's own `assess()`) tries to
    construct a claim this module cannot actually support -- a band
    outside `BANDS`, a factor for an unknown dimension, a `QUALIFIED`
    result with an unresolved or failing dimension, a `DISQUALIFIED`
    result with no positively-identified barrier, or a blocking clause
    that isn't the verbatim evidence of one of the result's own barrier
    factors."""


# DISQUALIFIED   at least one dimension carries a positively-identified
#                failing requirement (a `BARRIER` factor).
# QUALIFIED      every dimension resolved cleanly -- KNOWN status,
#                NOT_BARRIER verdict -- with no exceptions. Never
#                reached while any dimension is UNKNOWN or INFO.
# INSUFFICIENT_DATA   no barrier was found, but at least one dimension
#                could not be resolved (UNKNOWN: the notice didn't
#                return the field at all; or INFO: the field came back
#                but this module cannot positively clear or fail it).
#                This is the module's explicit UNKNOWN-is-not-PASS
#                state -- see module docstring.
BANDS = ("DISQUALIFIED", "QUALIFIED", "INSUFFICIENT_DATA")

# One dimension per `OperatorProfile` field. Fixed order; every
# `QualificationResult.factors` must name each of these exactly once.
DIMENSIONS = (
    "technical_staff_capacity",
    "certifications",
    "insurance",
    "corporate_references",
    "submission_language",
)

_FACTOR_STATUSES = ("KNOWN", "UNKNOWN")
_FACTOR_VERDICTS = ("BARRIER", "NOT_BARRIER", "INFO")

# TED eForms codes that unambiguously mean "the notice requires
# reference contracts" -- see `eligibility.SELECTION_CRITERION_LABELS`.
_REFERENCE_CODES = frozenset({
    "slc-abil-ref-services", "slc-abil-ref-supply", "slc-abil-ref-work",
})

# The one TED code that unambiguously means "professional indemnity /
# risk insurance," as opposed to `slc-stand-other`'s generic bucket
# (see module docstring's "THE HONEST LIMIT" section).
_INSURANCE_CODE = "slc-stand-ins"

_STAFF_CODE_PREFIX = "slc-abil-staff-"


@dataclass(frozen=True)
class OperatorProfile:
    """A real operator's real, self-declared capabilities -- not a
    verified fact from a third party, but not a guess either: this is
    what the operator themselves confirms. An empty `certifications` /
    `corporate_references` means the operator confirms they hold none,
    not that the field is unknown -- `OperatorProfile` carries no
    UNKNOWN state of its own; that ambiguity belongs entirely to the
    notice side (`EligibilityAssessment`), never to this side.
    """

    name: str
    staff_count: int
    certifications: FrozenSet[str] = frozenset()
    insurance_cover_eur: Optional[float] = None
    corporate_references: Tuple[str, ...] = ()
    languages: FrozenSet[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise QualificationIntegrityError(
                "an operator profile must be named")
        if self.staff_count < 0:
            raise QualificationIntegrityError(
                "staff_count cannot be negative")
        if not isinstance(self.certifications, frozenset):
            raise QualificationIntegrityError(
                "certifications must be a frozenset")
        if not isinstance(self.corporate_references, tuple):
            raise QualificationIntegrityError(
                "corporate_references must be a tuple")
        if not isinstance(self.languages, frozenset):
            raise QualificationIntegrityError(
                "languages must be a frozenset")
        if not self.languages:
            raise QualificationIntegrityError(
                "an operator profile must declare at least one language "
                "actually worked in -- an empty set is not a real profile")
        if self.insurance_cover_eur is not None and self.insurance_cover_eur < 0:
            raise QualificationIntegrityError(
                "insurance_cover_eur cannot be negative")
        object.__setattr__(
            self, "certifications",
            frozenset(c.strip().upper() for c in self.certifications if c.strip()))
        object.__setattr__(
            self, "languages",
            frozenset(l.strip().upper() for l in self.languages if l.strip()))


@dataclass(frozen=True)
class QualificationFactor:
    """One dimension's verdict, with the evidence a reader can inspect
    and disagree with -- there is no hidden score anywhere in this
    module, every band traces back to a tuple of these, same discipline
    as `winnability.WinnabilityFactor`."""

    dimension: str
    status: str      # KNOWN / UNKNOWN
    verdict: str      # BARRIER / NOT_BARRIER / INFO
    evidence: str

    def __post_init__(self) -> None:
        if self.dimension not in DIMENSIONS:
            raise QualificationIntegrityError(
                f"unknown dimension {self.dimension!r}")
        if self.status not in _FACTOR_STATUSES:
            raise QualificationIntegrityError(
                f"unknown factor status {self.status!r}")
        if self.verdict not in _FACTOR_VERDICTS:
            raise QualificationIntegrityError(
                f"unknown factor verdict {self.verdict!r}")
        if not self.evidence.strip():
            raise QualificationIntegrityError(
                f"factor {self.dimension!r} carries no evidence -- a "
                f"verdict with nothing a reader can check is not a "
                f"verdict, it is an assertion")
        if self.status == "UNKNOWN" and self.verdict != "INFO":
            raise QualificationIntegrityError(
                f"factor {self.dimension!r} is UNKNOWN but claims verdict "
                f"{self.verdict!r} -- an unresolved dimension cannot also "
                f"be a BARRIER or NOT_BARRIER")
        if self.verdict == "BARRIER" and self.status != "KNOWN":
            raise QualificationIntegrityError(
                f"factor {self.dimension!r} claims BARRIER without KNOWN "
                f"status -- a positively-identified failure must be known, "
                f"never inferred from an unresolved state")


_DISCLAIMER = (
    "QUALIFICATION SCREEN ONLY, NOT A BID DECISION. This band reflects "
    "arithmetic and structural facts already present in the notice's own "
    "eForms selection-criterion codes (and, if supplied, the operator's "
    "own declared profile) -- it is not legal advice, and it does not "
    "read every word of the notice's free text for the caller. A "
    "DISQUALIFIED verdict names the specific quoted clause(s) that "
    "produced it; an INFO/UNKNOWN factor means a human still has to read "
    "the quoted text themselves before relying on this result either way."
)


@dataclass(frozen=True)
class QualificationResult:
    """A qualification verdict for one operator against one notice.

    Every dimension in `DIMENSIONS` is represented exactly once in
    `factors`, in that fixed order. `blocking_clauses` is never
    populated except from the verbatim `evidence` of this result's own
    `BARRIER` factors -- enforced below, not merely documented.
    """

    publication_number: str
    operator_name: str
    band: str
    factors: Tuple[QualificationFactor, ...] = ()
    blocking_clauses: Tuple[str, ...] = ()
    note: str = _DISCLAIMER

    def __post_init__(self) -> None:
        if self.band not in BANDS:
            raise QualificationIntegrityError(f"unknown band {self.band!r}")
        present = tuple(f.dimension for f in self.factors)
        if present != DIMENSIONS:
            raise QualificationIntegrityError(
                f"a result must carry exactly one factor per DIMENSIONS, "
                f"in order; got {present!r}")

        has_barrier = any(f.verdict == "BARRIER" for f in self.factors)
        has_unresolved = any(
            f.status == "UNKNOWN" or f.verdict == "INFO" for f in self.factors)

        # THE CRITICAL INVARIANT, ENFORCED A SECOND, INDEPENDENT TIME.
        # `assess()` computes `band` from exactly this same arithmetic --
        # this re-derives it from the factors actually attached to this
        # object and refuses to construct a result where the two
        # disagree, so a caller cannot bypass the invariant by hand-
        # building a `QualificationResult` with mismatched fields.
        if self.band == "QUALIFIED" and (has_barrier or has_unresolved):
            raise QualificationIntegrityError(
                "QUALIFIED requires every dimension to be KNOWN and "
                "NOT_BARRIER -- an unresolved or failing dimension cannot "
                "be silently cleared")
        if self.band == "DISQUALIFIED" and not has_barrier:
            raise QualificationIntegrityError(
                "DISQUALIFIED requires at least one positively-identified "
                "BARRIER factor -- never an inference from silence")
        if self.band == "INSUFFICIENT_DATA" and not has_unresolved:
            raise QualificationIntegrityError(
                "INSUFFICIENT_DATA requires at least one UNKNOWN/INFO "
                "factor -- if every dimension resolved cleanly this must "
                "be QUALIFIED or DISQUALIFIED, not INSUFFICIENT_DATA")
        if self.band == "DISQUALIFIED" and not self.blocking_clauses:
            raise QualificationIntegrityError(
                "DISQUALIFIED must carry at least one quoted blocking clause")
        if self.band != "DISQUALIFIED" and self.blocking_clauses:
            raise QualificationIntegrityError(
                "blocking_clauses must be empty unless band is DISQUALIFIED")

        barrier_evidence = {f.evidence for f in self.factors if f.verdict == "BARRIER"}
        for clause in self.blocking_clauses:
            if clause not in barrier_evidence:
                raise QualificationIntegrityError(
                    "a blocking clause must be the verbatim evidence of "
                    "one of this result's own BARRIER factors -- never a "
                    "fabricated or unrelated string")

    def factor(self, dimension: str) -> QualificationFactor:
        for f in self.factors:
            if f.dimension == dimension:
                return f
        raise KeyError(dimension)  # pragma: no cover -- unreachable given __post_init__


def _quote_text(text_map: Optional[Dict[str, Tuple[str, ...]]]) -> str:
    """Flatten `EligibilityAssessment`'s `{lang: (text, ...)}` shape into
    one inspectable, quoted string -- `""` if nothing was there. Never
    truncates further; `eligibility.py` already bounds each string to
    `_TEXT_MAX_LEN` (8000 chars)."""
    if not text_map:
        return ""
    parts = []
    for lang, texts in text_map.items():
        for t in texts:
            parts.append(f"[{lang}] {t}")
    return " | ".join(parts)


def _labelled(codes: Tuple[CodedRequirement, ...]) -> str:
    fallback = "code not in this module's label snapshot"
    return "; ".join(f"{c.code} ({c.label or fallback})" for c in codes)


def _unparsed_criteria_text(elig: EligibilityAssessment) -> str:
    """The notice's free-text selection criteria, if it stated any.

    THE DEFECT THIS EXISTS TO CLOSE -- found live 2026-09-02 on TED
    244223-2024 (ECHA Helsinki, EUR 14m IT services DPS).

    This module returned QUALIFIED for a solo operator against that
    notice. The notice's own `selection-criterion-description-lot`
    field, which we fetch and which `EligibilityAssessment` carries,
    says verbatim:

        "Average yearly turnover of the last two (2) financial years
         above EUR 1.000.000."

    plus five reference contracts of at least EUR 100,000 each. Both
    exclude the operator outright.

    The reason we cleared it: every dimension below decided
    `NOT_BARRIER` from the CODED criteria alone -- "codes were present,
    and none of them was a staffing/insurance/reference code, therefore
    no such requirement exists". That inference is false. TED's coded
    vocabulary does not capture every requirement a buyer writes, and
    the buyer's real threshold lived in prose the codes never mentioned.

    So: absence of a CODE, while free-text criteria exist that this
    module cannot parse, is NOT clearance. It is exactly the "silence
    is not permission" rule this project already enforces one level up
    (an absent field yields UNKNOWN, never QUALIFIED) -- applied one
    level down, where it was missing.

    Returns "" only when the notice genuinely stated no criteria prose
    at all, which is the one case where "no code of this type" really
    does mean the notice named no such requirement.
    """
    return _quote_text(elig.selection_criteria_description_text)


def _no_code_of_type(
    dim: str,
    elig: EligibilityAssessment,
    clear_evidence: str,
) -> QualificationFactor:
    """Verdict for "criteria codes were present, but none of the type
    this dimension checks".

    Clear only if the notice also stated no free-text criteria. If it
    did state prose, this module has not read it and must say so --
    INFO, which forces INSUFFICIENT_DATA rather than QUALIFIED.
    """
    quoted = _unparsed_criteria_text(elig)
    if not quoted:
        return QualificationFactor(dim, "KNOWN", "NOT_BARRIER", clear_evidence)
    return QualificationFactor(
        dim, "KNOWN", "INFO",
        f"{clear_evidence}. BUT the notice states free-text selection "
        f"criteria this module does not parse, and a real requirement "
        f"can live there with no matching code (proven on TED "
        f"244223-2024, where an unstated-in-codes EUR 1,000,000 "
        f"turnover floor was written only in prose). Unresolved, not "
        f"cleared. Notice text: {quoted}")


def _assess_staff(elig: EligibilityAssessment, profile: OperatorProfile) -> QualificationFactor:
    dim = "technical_staff_capacity"
    tech = elig.technical_professional_criteria
    quoted = _quote_text(elig.selection_criteria_description_text)
    if tech is None:
        return QualificationFactor(
            dim, "UNKNOWN", "INFO",
            "the notice did not return technical/professional "
            "selection-criterion codes (absent field) -- staffing/"
            "technician requirements, if any, are unknown")
    if not tech:
        return _no_code_of_type(
            dim, elig,
            "selection-criterion-lot was present but no technical/"
            "professional-ability code was among the stated criteria")
    staff_codes = tuple(c for c in tech if c.code.startswith(_STAFF_CODE_PREFIX))
    if not staff_codes:
        return _no_code_of_type(
            dim, elig,
            "technical/professional criteria stated, but none named a "
            "required staffing/technician level")
    return QualificationFactor(
        dim, "KNOWN", "INFO",
        f"notice states a staffing/technician requirement "
        f"({_labelled(staff_codes)}); this module does not parse free "
        f"text for a numeric headcount threshold, so it cannot resolve "
        f"this against the operator's declared staff_count="
        f"{profile.staff_count}. Quoted notice text for human "
        f"comparison: {quoted or 'UNKNOWN'}")


def _assess_certifications(elig: EligibilityAssessment, profile: OperatorProfile) -> QualificationFactor:
    dim = "certifications"
    cert = elig.certification_criteria
    quoted = _quote_text(elig.selection_criteria_description_text)
    if cert is None:
        return QualificationFactor(
            dim, "UNKNOWN", "INFO",
            "the notice did not return selection-criterion codes (absent "
            "field) -- certification requirements, if any, are unknown")
    if not cert:
        return _no_code_of_type(
            dim, elig,
            "selection-criterion-lot was present but no independent-"
            "certification code (quality/environmental-management-body "
            "certificate) was among the stated criteria. Note: specific "
            "professional certifications (e.g. OSCP/OSWE) named only in "
            "notice free text, and bucketed under a staff-qualification "
            "code rather than a dedicated certification code, are not "
            "detected by this dimension -- see technical_staff_capacity")
    if not profile.certifications:
        return QualificationFactor(
            dim, "KNOWN", "BARRIER",
            f"notice requires independent certification evidence "
            f"({_labelled(cert)}); operator holds no certifications "
            f"(certifications=frozenset()). Quoted notice text: "
            f"{quoted or 'UNKNOWN'}")
    return QualificationFactor(
        dim, "KNOWN", "INFO",
        f"notice requires independent certification evidence "
        f"({_labelled(cert)}); operator holds {sorted(profile.certifications)}, "
        f"but this module cannot verify from the codes alone whether "
        f"those specific certifications satisfy this specific "
        f"requirement. Quoted notice text: {quoted or 'UNKNOWN'}")


def _assess_insurance(elig: EligibilityAssessment, profile: OperatorProfile) -> QualificationFactor:
    dim = "insurance"
    econ = elig.economic_financial_criteria
    quoted = _quote_text(elig.selection_criteria_description_text)
    if econ is None:
        return QualificationFactor(
            dim, "UNKNOWN", "INFO",
            "the notice did not return economic/financial selection-"
            "criterion codes (absent field) -- an insurance requirement, "
            "if any, is unknown")
    if not econ:
        return _no_code_of_type(
            dim, elig,
            "selection-criterion-lot was present but no economic/"
            "financial-standing code was among the stated criteria")
    ins_codes = tuple(c for c in econ if c.code == _INSURANCE_CODE)
    if ins_codes:
        if profile.insurance_cover_eur is None:
            return QualificationFactor(
                dim, "KNOWN", "BARRIER",
                f"notice requires professional risk indemnity insurance "
                f"({_labelled(ins_codes)}); operator holds no insurance "
                f"cover (insurance_cover_eur=None). Quoted notice text: "
                f"{quoted or 'UNKNOWN'}")
        return QualificationFactor(
            dim, "KNOWN", "INFO",
            f"notice requires professional risk indemnity insurance "
            f"({_labelled(ins_codes)}); operator declares EUR "
            f"{profile.insurance_cover_eur:,.2f} cover, but the required "
            f"minimum stated in the notice's own text must be checked by "
            f"a human. Quoted notice text: {quoted or 'UNKNOWN'}")
    # Present, non-empty, but the ONLY codes are outside the dedicated
    # insurance code (e.g. `slc-stand-other`, TED's generic bucket --
    # see module docstring's "THE HONEST LIMIT"). A real insurance
    # clause can and does live here (the live degewo AG notice this
    # module was tested against does exactly this). This module refuses
    # to guess either way from an ambiguous generic code.
    return QualificationFactor(
        dim, "KNOWN", "INFO",
        f"notice states an economic/financial requirement not coded as "
        f"the dedicated insurance code ({_labelled(econ)}) -- this "
        f"generic category can genuinely include an insurance clause "
        f"TED did not tag specifically; this module will not guess "
        f"either way from the code alone. Operator declares insurance "
        f"cover: {profile.insurance_cover_eur!r}. Quoted notice text: "
        f"{quoted or 'UNKNOWN'}")


def _assess_references(elig: EligibilityAssessment, profile: OperatorProfile) -> QualificationFactor:
    dim = "corporate_references"
    tech = elig.technical_professional_criteria
    quoted = _quote_text(elig.selection_criteria_description_text)
    if tech is None:
        return QualificationFactor(
            dim, "UNKNOWN", "INFO",
            "the notice did not return technical/professional "
            "selection-criterion codes (absent field) -- a reference-"
            "contract requirement, if any, is unknown")
    if not tech:
        return _no_code_of_type(
            dim, elig,
            "selection-criterion-lot was present but no technical/"
            "professional-ability code was among the stated criteria")
    ref_codes = tuple(c for c in tech if c.code in _REFERENCE_CODES)
    if not ref_codes:
        return _no_code_of_type(
            dim, elig,
            "technical/professional criteria stated, but none named a "
            "reference-contract requirement")
    if not profile.corporate_references:
        return QualificationFactor(
            dim, "KNOWN", "BARRIER",
            f"notice requires reference contracts ({_labelled(ref_codes)}); "
            f"operator has zero evidenced corporate references "
            f"(corporate_references=()). Quoted notice text: "
            f"{quoted or 'UNKNOWN'}")
    return QualificationFactor(
        dim, "KNOWN", "INFO",
        f"notice requires reference contracts ({_labelled(ref_codes)}); "
        f"operator declares {len(profile.corporate_references)} "
        f"reference(s), but the exact number/value threshold stated in "
        f"the notice must be checked by a human. Quoted notice text: "
        f"{quoted or 'UNKNOWN'}")


def _assess_language(elig: EligibilityAssessment, profile: OperatorProfile) -> QualificationFactor:
    dim = "submission_language"
    langs = elig.submission_languages
    if not langs:
        return QualificationFactor(
            dim, "UNKNOWN", "INFO",
            "the notice did not return a submission-language field "
            "(absent field) -- the required submission language is "
            "unknown")
    normalized = tuple(sorted({l.strip().upper() for l in langs if l.strip()}))
    if not normalized:
        return QualificationFactor(  # pragma: no cover -- defensive; _as_tuple never yields this
            dim, "UNKNOWN", "INFO",
            "the notice's submission-language field carried no usable "
            "value")
    if any(l in profile.languages for l in normalized):
        return QualificationFactor(
            dim, "KNOWN", "NOT_BARRIER",
            f"notice permits submission in {normalized}; operator's "
            f"declared languages {sorted(profile.languages)} include at "
            f"least one match")
    return QualificationFactor(
        dim, "KNOWN", "BARRIER",
        f"notice requires submission in {normalized}; operator's "
        f"declared languages are {sorted(profile.languages)} -- no overlap")


def assess(eligibility: EligibilityAssessment, profile: OperatorProfile) -> QualificationResult:
    """Score one `EligibilityAssessment` against one `OperatorProfile`.
    Pure function, no network I/O, no gate required.

    Raises `QualificationIntegrityError` if either argument is the
    wrong type -- a caller passing the wrong object here is the exact
    "confident answer to the wrong question" failure this module exists
    to prevent, so it fails loudly rather than silently returning a
    meaningless verdict.
    """
    if not isinstance(eligibility, EligibilityAssessment):
        raise QualificationIntegrityError(
            f"eligibility must be an EligibilityAssessment, got "
            f"{type(eligibility).__name__}")
    if not isinstance(profile, OperatorProfile):
        raise QualificationIntegrityError(
            f"profile must be an OperatorProfile, got {type(profile).__name__}")

    factors = (
        _assess_staff(eligibility, profile),
        _assess_certifications(eligibility, profile),
        _assess_insurance(eligibility, profile),
        _assess_references(eligibility, profile),
        _assess_language(eligibility, profile),
    )

    has_barrier = any(f.verdict == "BARRIER" for f in factors)
    has_unresolved = any(f.status == "UNKNOWN" or f.verdict == "INFO" for f in factors)

    if has_barrier:
        band = "DISQUALIFIED"
    elif has_unresolved:
        band = "INSUFFICIENT_DATA"
    else:
        band = "QUALIFIED"

    blocking = tuple(f.evidence for f in factors if f.verdict == "BARRIER")

    return QualificationResult(
        publication_number=eligibility.publication_number,
        operator_name=profile.name,
        band=band,
        factors=factors,
        blocking_clauses=blocking,
    )


def format_result(r: QualificationResult) -> str:
    """A human-readable text report -- sections, explicit UNKNOWN/INFO
    markers, the quoted blocking clause(s) if any. Intended for a human
    deciding whether to read the underlying notice at all; callers
    wanting the structured data should read the dataclass fields
    directly."""
    lines = [
        f"Qualification: {r.operator_name} vs notice {r.publication_number}",
        f"  BAND: {r.band}",
        "",
    ]
    for f in r.factors:
        lines.append(f"  [{f.dimension}] {f.status}/{f.verdict}")
        lines.append(f"    {f.evidence}")
    if r.blocking_clauses:
        lines.append("")
        lines.append("BLOCKING CLAUSE(S):")
        for c in r.blocking_clauses:
            lines.append(f"  - {c}")
    lines.append("")
    lines.append(r.note)
    return "\n".join(lines)
