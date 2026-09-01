"""Surface-relevance ranking for public procurement notices. Not a qualifier.

WHY THIS EXISTS

`tender_radar` (owned elsewhere this cycle) can reach hundreds of
thousands of public procurement notices. That is noise, not opportunity.
An operator cannot read 400,000 notices, and a system that hands him all
of them, unranked, has not helped. What is missing is a way to order
notices against what this operator has DECLARED he can deliver.

THE TRAP THIS MODULE REFUSES TO WALK INTO

This repository's outcome vocabulary is
    MODELLED != OBSERVED != VERIFIED != REALIZED
and `foundation/opportunity_pipeline.py` reads
    signals -> qualified -> contracts -> cash
with `qualified`, `contracts`, `cash` structurally pinned at 0, because
no `CanonicalSignal` carries evidence that any of those three facts
happened. This module produces exactly one more fact than a bare
signal already carries: "this notice's text surface-matches the
capability profile the caller supplied about themselves." That is all
it produces.

A RELEVANCE SCORE IS NOT A QUALIFICATION. It does not mean the operator
can win the notice, is eligible to bid on it, meets any threshold the
buyer will actually apply, or that any human or process has assessed
it. No band, field, docstring or log line in this module uses the word
"qualified" or "qualification" about a scored item, and none of them
ever will -- that word is reserved for the outcome ledger's own
vocabulary (`foundation/outcome_ledger.py`), and this module does not
import it, does not touch it, and writes to no ledger anywhere.

WHAT `CapabilityProfile` ACTUALLY IS

`CapabilityProfile` is DATA the caller supplies describing what they
claim they do. It is a self-report, not a verified fact -- nothing in
this module checks it against a licence register, a past-contracts
history, or any external authority. Treat a `CapabilityProfile` exactly
as you would treat a CV: informative, and unverified until someone
checks it.

DEFENDING AGAINST KEYWORD STUFFING

The obvious attack on any relevance scorer is a notice engineered to
contain every keyword in the profile so it floats to the top. Since
`CanonicalSignal.claim`/`evidence`/`facts` are attacker-controlled text
(see `foundation/untrusted_text.py`'s own docstring on this exact
pipeline), this module never scores on raw keyword-hit COUNT. It scores
on two things a stuffed notice cannot fake at once:

  1. DISTINCT keyword coverage, not occurrence count. Ten repeats of
     one keyword are worth exactly what one repeat is worth.
  2. KEYWORD DENSITY relative to the notice's total word count, plus a
     REPETITION RATIO (occurrences per distinct term). A notice that is
     mostly the profile's own keyword list, or that repeats one term
     far more than natural prose would, is flagged as
     `stuffing_suspected` and is structurally barred from the top band
     (`STRONG_MATCH`) regardless of how many distinct terms it hits --
     see `_looks_stuffed()`.

`STRONG_MATCH` therefore requires broad, non-repetitive, non-dominant
coverage: exactly what an honestly-worded, genuinely relevant notice
looks like, and exactly what a crude keyword-stuffing attack does not.

UNKNOWN IS NOT ZERO

A notice with no searchable text at all (empty claim, no facts, no
evidence, no target) is `UNKNOWN`. It is never silently treated as
"no match" (which would look identical to a confidently-scored
irrelevant notice) or as a zero score. `UNKNOWN` names the missing
evidence explicitly, per this repository's founding rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import FrozenSet, Mapping, Optional, Sequence, Tuple

from foundation.signal_spine import CanonicalSignal
from foundation.untrusted_text import neutralise

__all__ = [
    "BANDS",
    "STRONG_MIN_DISTINCT",
    "STUFFING_DENSITY_THRESHOLD",
    "STUFFING_REPETITION_THRESHOLD",
    "RelevanceIntegrityError",
    "CapabilityProfile",
    "RelevanceAssessment",
    "score",
    "rank",
]


class RelevanceIntegrityError(ValueError):
    """A caller tried to make this module claim more than a surface match."""


# The fixed band vocabulary. Deliberately small and deliberately NOT the
# outcome ledger's vocabulary (PENDING/HUMAN_RESPONDED/...) -- these are
# different questions ("does the text surface-match?" vs "did an outcome
# happen?") and merging them is exactly the blur this module exists to
# prevent.
#
#   STRONG_MATCH  broad, non-repetitive coverage of the declared profile.
#   POSSIBLE      some real, non-stuffed match, but thin.
#   WEAK          little or no positive evidence -- including a match
#                 that only exists because of detected keyword stuffing.
#   EXCLUDED      the caller's own exclusion terms were found. Wins over
#                 every positive signal; an operator's stated "we do not
#                 do X" is a hard boundary, not a tiebreak.
#   UNKNOWN       nothing in the signal was searchable. Never conflated
#                 with WEAK -- WEAK means "we looked and found little",
#                 UNKNOWN means "there was nothing to look at".
BANDS = ("STRONG_MATCH", "POSSIBLE", "WEAK", "EXCLUDED", "UNKNOWN")

# Distinct profile keywords a notice must hit, with no stuffing flagged,
# to earn the top band. A single very specific CPV code match also
# earns it (see `score()`) because an exact code match is not something
# a keyword-stuffed free-text blob can fake.
STRONG_MIN_DISTINCT = 3

# Fraction of a notice's total word count that may consist of profile
# keyword occurrences before the notice is treated as stuffed. Chosen
# well above what natural prose describing a real relevant tender would
# ever produce (a real notice mentions its own subject a handful of
# times among hundreds of procedural words).
STUFFING_DENSITY_THRESHOLD = 0.25

# Occurrences-per-distinct-term ratio above which a notice is treated as
# stuffed even if density alone did not trip -- catches "security
# security security security consulting" style repetition of one term
# padded with little else.
STUFFING_REPETITION_THRESHOLD = 6

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenise(text: str) -> Tuple[str, ...]:
    return tuple(_WORD_RE.findall(text.lower()))


def _keyword_pattern(term: str) -> re.Pattern:
    # Word-boundary match so "cat" does not match inside "category".
    # Multi-word terms match as a literal phrase with flexible internal
    # whitespace.
    escaped = re.escape(term.strip().lower())
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(rf"\b{escaped}\b")


def _norm_set(values: Sequence[str]) -> FrozenSet[str]:
    return frozenset(v.strip().lower() for v in values if v and v.strip())


@dataclass(frozen=True)
class CapabilityProfile:
    """A caller-supplied CLAIM about what they do. Not a verified fact.

    Every field here is DATA the caller declares about themselves --
    this module never infers, augments or verifies any of it. A future
    caller who wants this profile checked against real evidence (past
    contract history, a licence register, a certification) must build
    that check separately; scoring against an unverified self-report is
    the entire and honest scope of this module.

    `keywords`      terms that indicate the notice is in-scope.
    `cpv_codes`     Common Procurement Vocabulary codes (or any other
                    scheme's codes) the caller claims to be able to
                    deliver against. Matched as exact tokens, which is
                    why a match against these is stronger evidence than
                    a free-text keyword hit -- a code cannot be
                    accidentally paraphrased into existence.
    `exclusions`    terms whose presence means "not for us", regardless
                    of how well the notice otherwise matches. Checked
                    before, and overriding, every positive signal.
    """

    name: str
    declared_by: str
    keywords: FrozenSet[str] = field(default_factory=frozenset)
    cpv_codes: FrozenSet[str] = field(default_factory=frozenset)
    exclusions: FrozenSet[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise RelevanceIntegrityError(
                "a capability profile must be named")
        if not self.declared_by.strip():
            raise RelevanceIntegrityError(
                "a capability profile must record who declared it -- an "
                "unattributed self-report cannot be weighed by a reader")
        object.__setattr__(self, "keywords", _norm_set(self.keywords))
        object.__setattr__(self, "cpv_codes", _norm_set(self.cpv_codes))
        object.__setattr__(self, "exclusions", _norm_set(self.exclusions))
        if not self.keywords and not self.cpv_codes:
            raise RelevanceIntegrityError(
                "a capability profile with no keywords and no CPV codes "
                "cannot score anything -- it would only ever produce "
                "UNKNOWN, which is not a useful profile to declare")


@dataclass(frozen=True)
class RelevanceAssessment:
    """A surface-match verdict for one signal against one profile.

    This is NOT a qualification. See the module docstring. Every field
    is evidence a reader can inspect and disagree with -- there is no
    hidden score, only what matched, what was excluded, and why.
    """

    signal_id: str
    profile_name: str
    band: str
    matched_keywords: Tuple[str, ...] = ()
    matched_cpv_codes: Tuple[str, ...] = ()
    exclusion_reasons: Tuple[str, ...] = ()
    unknown_reason: str = ""
    stuffing_suspected: bool = False
    coverage: float = 0.0  # distinct matched / len(profile.keywords), diagnostic only
    note: str = (
        "SURFACE MATCH ONLY. This band reflects whether the notice's own "
        "text resembles a self-declared capability profile. It does not "
        "mean this can be won, that eligibility was checked, or that any "
        "assessment has been performed by anyone. Verify independently "
        "before acting."
    )

    def __post_init__(self) -> None:
        if self.band not in BANDS:
            raise RelevanceIntegrityError(f"unknown band {self.band!r}")
        if self.band == "UNKNOWN" and not self.unknown_reason.strip():
            raise RelevanceIntegrityError(
                "an UNKNOWN assessment must name why nothing was "
                "scorable -- UNKNOWN is not allowed to be a silent zero")
        if self.band == "EXCLUDED" and not self.exclusion_reasons:
            raise RelevanceIntegrityError(
                "an EXCLUDED assessment must name the exclusion terms "
                "that were found")


def _searchable_text(signal: CanonicalSignal) -> str:
    """Everything on the signal a caller might plausibly search, safely
    rendered. All of it is attacker-controlled (see
    `foundation/untrusted_text.py`), so it is neutralised before this
    module ever matches against it or hands it back in an assessment.
    """
    parts = [signal.claim, signal.target, signal.source_ref]
    parts.extend(str(v) for v in signal.facts.values())
    parts.extend(str(v) for v in signal.evidence.values())
    joined = " ".join(p for p in parts if p)
    return neutralise(joined, max_len=8000)


def _looks_stuffed(text_tokens: Tuple[str, ...],
                    occurrences_by_term: Mapping[str, int]) -> bool:
    total_occurrences = sum(occurrences_by_term.values())
    distinct = sum(1 for c in occurrences_by_term.values() if c > 0)
    word_count = max(len(text_tokens), 1)
    density = total_occurrences / word_count
    if density > STUFFING_DENSITY_THRESHOLD:
        return True
    if distinct > 0:
        repetition = total_occurrences / distinct
        if repetition > STUFFING_REPETITION_THRESHOLD:
            return True
    return False


def score(signal: CanonicalSignal,
          profile: CapabilityProfile) -> RelevanceAssessment:
    """Score one signal's surface text against one capability profile.

    Returns a `RelevanceAssessment`. Never mutates `signal` or
    `profile`. Never writes anywhere -- this function has no side
    effects beyond returning a value.
    """
    text = _searchable_text(signal)
    tokens = _tokenise(text)

    if not text.strip():
        return RelevanceAssessment(
            signal_id=signal.signal_id,
            profile_name=profile.name,
            band="UNKNOWN",
            unknown_reason=(
                "signal carried no searchable text: claim, target, "
                "source_ref, facts and evidence were all empty"),
        )

    # Exclusion check first and unconditional -- overrides every
    # positive signal below.
    matched_exclusions = tuple(sorted(
        term for term in profile.exclusions
        if _keyword_pattern(term).search(text)
    ))
    if matched_exclusions:
        return RelevanceAssessment(
            signal_id=signal.signal_id,
            profile_name=profile.name,
            band="EXCLUDED",
            exclusion_reasons=matched_exclusions,
        )

    occurrences = {
        term: len(_keyword_pattern(term).findall(text))
        for term in profile.keywords
    }
    matched_keywords = tuple(sorted(t for t, c in occurrences.items() if c))
    matched_cpv = tuple(sorted(
        code for code in profile.cpv_codes
        if _keyword_pattern(code).search(text)
    ))

    stuffed = _looks_stuffed(tokens, occurrences)
    distinct_count = len(matched_keywords)
    coverage = (distinct_count / len(profile.keywords)) if profile.keywords else 0.0

    if stuffed:
        band = "WEAK"
    elif distinct_count == 0 and not matched_cpv:
        band = "WEAK"
    elif matched_cpv or distinct_count >= STRONG_MIN_DISTINCT:
        band = "STRONG_MATCH"
    else:
        band = "POSSIBLE"

    return RelevanceAssessment(
        signal_id=signal.signal_id,
        profile_name=profile.name,
        band=band,
        matched_keywords=matched_keywords,
        matched_cpv_codes=matched_cpv,
        stuffing_suspected=stuffed,
        coverage=coverage,
    )


_BAND_RANK = {"STRONG_MATCH": 3, "POSSIBLE": 2, "WEAK": 1, "EXCLUDED": 0,
              "UNKNOWN": 0}


def rank(signals: Sequence[CanonicalSignal],
          profile: CapabilityProfile) -> Tuple[RelevanceAssessment, ...]:
    """Score every signal and return assessments ordered best-first.

    Tiebreak is (band rank, coverage, distinct-match count, signal_id)
    -- entirely deterministic, so the same input always produces the
    same order regardless of iteration order or hash randomisation.
    """
    assessments = [score(s, profile) for s in signals]
    return tuple(sorted(
        assessments,
        key=lambda a: (
            -_BAND_RANK[a.band],
            -a.coverage,
            -len(a.matched_keywords),
            a.signal_id,
        ),
    ))
