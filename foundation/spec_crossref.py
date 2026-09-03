"""foundation/spec_crossref.py -- systematic cross-reference checking of
a large technical specification.

WHY THIS EXISTS

Swiss Post's e-voting bug bounty pays up to EUR230,000 and explicitly
admits "a static test of documentation and source code" as in scope. Its
System Specification is 166 pages defining 78 numbered algorithms that
reference each other constantly; its Verifier Specification is 48 pages
defining 44 numbered verifications. Checking that every reference
resolves, that no number carries two names, and that no name carries two
numbers, requires holding the whole document at once. That is the one
thing a machine does better than a careful reader, and 1,855 reports
have already been filed by careful readers.

WHAT IT PRODUCES, AND THE WORD MATTERS

`CrossRefCandidate`, never `Finding`. Every candidate this module raised
on its first real run was WRONG, and each was wrong in an instructive
way:

  - `Algorithm 6.7` looked like a reference with no definition. The
    definition exists: `Algorithm 6.7 ConfirmVoteAgreement`. The PDF
    encodes "fi" as the ligature U+FB01, so an identifier pattern built
    from `[A-Za-z0-9]` truncated the name to "Con" and the definition
    vanished. See `normalise_extracted_text()`.
  - `ExtractVeri` looked like one name defined at two different numbers.
    Same ligature, two different names truncated to a common prefix.
  - A gap at verification numbers 4.xx and 9.xx looked like missing
    verifications. The document's own changelog records verifications
    being removed and merged across versions without renumbering.
  - `Verification 0.01` appeared in neither of the two verification
    runs. It is `ManualChecksByAuditors`, explicitly "the checks that
    the auditors must perform manually" -- deliberately outside both
    automated runs.

Four candidates, four disproven. That is the honest yield of systematic
cross-referencing against a target this heavily worked, and it is worth
knowing: it says the cheap structural checks are clean, so the remaining
value is in depth rather than breadth. A module that had called those
four "findings" would have produced four false reports to a programme
that publishes its issue tracker.

So: this module locates candidates. A human resolves them. The
vocabulary refuses to blur that.

NO NETWORK, NO PDF PARSING. Text in, candidates out. Extraction is the
caller's problem precisely because extraction is where the errors were.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

__all__ = [
    "SpecCrossRefError",
    "CANDIDATE_KINDS",
    "LIGATURES",
    "normalise_extracted_text",
    "CrossRefCandidate",
    "CrossRefReport",
    "crossref",
    "format_crossref",
]


class SpecCrossRefError(ValueError):
    """Raised on a malformed candidate or a caller passing something
    that is not text."""


CANDIDATE_KINDS = (
    "REFERENCED_NEVER_DEFINED",
    "NUMBER_WITH_SEVERAL_NAMES",
    "NAME_WITH_SEVERAL_NUMBERS",
    "DEFINED_NEVER_REFERENCED",
)

# THE BUG THAT MANUFACTURED TWO FALSE CANDIDATES.
#
# PDF text extraction preserves typographic ligatures as single
# codepoints. `Confirm` comes out as `Con` + U+FB01 + `rm`, and U+FB01
# is not in [A-Za-z], so any identifier pattern silently truncates at
# it. Two of this module's first four candidates were that, and both
# looked exactly like real structural defects in a security-critical
# specification.
#
# NFKC alone does decompose these, but it also rewrites a great deal
# else in a document full of mathematical notation -- superscripts,
# fractions, and the sub/superscripted indices this specification uses
# throughout for variables like `E1j,i`. So the ligatures are replaced
# explicitly first, and NFKC is applied only as a caller-controlled
# option rather than as an unconditional default.
LIGATURES = {
    "ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
    "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st",
    "Ĳ": "IJ", "ĳ": "ij", "Œ": "OE", "œ": "oe",
    "Æ": "AE", "æ": "ae",
}


def normalise_extracted_text(text: str, *, nfkc: bool = False) -> str:
    """Undo the extraction artefacts that manufacture false candidates.

    Ligatures are always expanded -- see `LIGATURES` for why this is not
    optional. `nfkc` is off by default: NFKC rewrites superscripts and
    other mathematical notation, which in a cryptographic specification
    is content, not noise.
    """
    if not isinstance(text, str):
        raise SpecCrossRefError(
            f"normalise_extracted_text() takes text, got {type(text).__name__}")
    for lig, plain in LIGATURES.items():
        text = text.replace(lig, plain)
    if nfkc:
        text = unicodedata.normalize("NFKC", text)
    # Soft hyphens and non-breaking spaces split identifiers the same
    # way ligatures do.
    text = text.replace("­", "").replace(" ", " ")
    return text


@dataclass(frozen=True)
class CrossRefCandidate:
    """One thing worth a human's attention. NOT a finding.

    `why_it_might_be_fine` is a required field, not documentation. Every
    candidate this module has ever raised turned out to be fine, and a
    candidate presented without its most likely innocent explanation
    invites exactly the false report this module exists to avoid.
    """

    kind: str
    subject: str
    detail: str
    why_it_might_be_fine: str
    occurrences: int = 0

    def __post_init__(self) -> None:
        if self.kind not in CANDIDATE_KINDS:
            raise SpecCrossRefError(
                f"unknown candidate kind {self.kind!r} -- must be one of "
                f"{CANDIDATE_KINDS}")
        if not self.subject.strip():
            raise SpecCrossRefError("a candidate must name its subject")
        if not self.why_it_might_be_fine.strip():
            raise SpecCrossRefError(
                f"candidate {self.subject!r} carries no innocent explanation "
                "-- every candidate raised so far has been innocent, and one "
                "presented without that context invites a false report")


@dataclass(frozen=True)
class CrossRefReport:
    """The result of one cross-reference pass."""

    definitions: Dict[str, Tuple[str, ...]]
    reference_counts: Dict[str, int]
    candidates: Tuple[CrossRefCandidate, ...]
    text_was_supplied: bool
    ligatures_found: int = 0

    @property
    def status(self) -> str:
        if not self.text_was_supplied:
            return "NOT_ASSESSED"
        return "CANDIDATES_RAISED" if self.candidates else "NO_CANDIDATES"

    @property
    def defined_count(self) -> int:
        return len(self.definitions)

    @property
    def referenced_count(self) -> int:
        return len(self.reference_counts)


def crossref(
    text: str,
    *,
    definition_pattern: str,
    reference_pattern: str,
    report_unreferenced: bool = False,
) -> CrossRefReport:
    """Cross-reference one specification against itself.

    `definition_pattern` must capture two groups: the identifier (a
    number, usually) and the name attached to it at its definition site.
    `reference_pattern` must capture one group: the identifier as cited.

    The text is normalised before matching. A caller who has already
    normalised loses nothing by it being done twice.
    """
    if not isinstance(text, str):
        raise SpecCrossRefError(
            f"crossref() takes document text, got {type(text).__name__}")

    raw = text
    text = normalise_extracted_text(text)
    ligatures_found = sum(raw.count(l) for l in LIGATURES)

    if not text.strip():
        return CrossRefReport({}, {}, (), text_was_supplied=False)

    flat = re.sub(r"[ \t]+", " ", text)

    try:
        def_re = re.compile(definition_pattern)
        ref_re = re.compile(reference_pattern)
    except re.error as exc:
        raise SpecCrossRefError(f"bad pattern: {exc}") from exc
    if def_re.groups < 2:
        raise SpecCrossRefError(
            "definition_pattern must capture two groups (identifier, name)")
    if ref_re.groups < 1:
        raise SpecCrossRefError(
            "reference_pattern must capture one group (identifier)")

    # A DEFINITION SITE IS NOT A CITATION OF ITSELF.
    #
    # `Algorithm 6.7 ConfirmVoteAgreement` matches the reference pattern
    # too -- the reference pattern is a prefix of the definition
    # pattern by construction. Counting definition sites as references
    # made `set(defs) - set(refs)` empty for every possible input, so
    # DEFINED_NEVER_REFERENCED could never fire at all. The check was
    # dead code that looked like a working check.
    #
    # Found by the test that asserts it fires, not by reading it.
    defs: Dict[str, set] = defaultdict(set)
    def_spans = []
    for m in def_re.finditer(flat):
        defs[m.group(1)].add(m.group(2))
        def_spans.append((m.start(), m.end()))

    def _inside_a_definition(pos: int) -> bool:
        return any(start <= pos < end for start, end in def_spans)

    refs = Counter(m.group(1) for m in ref_re.finditer(flat)
                   if not _inside_a_definition(m.start()))

    candidates = []

    for ident in sorted(set(refs) - set(defs)):
        candidates.append(CrossRefCandidate(
            kind="REFERENCED_NEVER_DEFINED",
            subject=ident,
            detail=f"cited {refs[ident]} time(s); no definition site matched",
            why_it_might_be_fine=(
                "the definition almost certainly exists and the NAME failed "
                "to match -- a ligature, a line break, or a character class "
                "too narrow for the identifier actually used. Check the "
                "definition site by eye before believing this."),
            occurrences=refs[ident],
        ))

    for ident, names in sorted(defs.items()):
        if len(names) > 1:
            candidates.append(CrossRefCandidate(
                kind="NUMBER_WITH_SEVERAL_NAMES",
                subject=ident,
                detail=f"defined with names {sorted(names)}",
                why_it_might_be_fine=(
                    "one name may be a truncation of the other at a ligature "
                    "or hyphen, or the document may legitimately restate the "
                    "identifier in a summary table with a shortened label."),
                occurrences=len(names),
            ))

    by_name: Dict[str, set] = defaultdict(set)
    for ident, names in defs.items():
        for n in names:
            by_name[n].add(ident)
    for name, idents in sorted(by_name.items()):
        if len(idents) > 1:
            candidates.append(CrossRefCandidate(
                kind="NAME_WITH_SEVERAL_NUMBERS",
                subject=name,
                detail=f"appears as {sorted(idents)}",
                why_it_might_be_fine=(
                    "two longer names may share this prefix and both have "
                    "been truncated at the same character -- the failure "
                    "that produced 'ExtractVeri' on the first real run."),
                occurrences=len(idents),
            ))

    if report_unreferenced:
        # CITED BY NAME COUNTS AS CITED.
        #
        # The first version raised this candidate for any identifier not
        # cited by NUMBER. Against the real 166-page System
        # Specification that was 27 candidates, and all 27 were
        # innocent for one systematic reason: the pseudocode calls
        # algorithms by NAME -- `MixDecOnline` appears 26 times, and its
        # number never does. A check with a 27-out-of-27 false positive
        # rate is not a check, it is a way to bury the real candidates
        # under noise.
        #
        # Now an identifier is only raised when NEITHER its number NOR
        # its name appears anywhere outside its own definition site.
        # Against the same document that yields zero, which is the
        # correct answer.
        for ident in sorted(set(defs) - set(refs)):
            names = defs[ident]
            cited_by_name = False
            for name in names:
                for m in re.finditer(re.escape(name), flat):
                    if not _inside_a_definition(m.start()):
                        cited_by_name = True
                        break
                if cited_by_name:
                    break
            if cited_by_name:
                continue
            candidates.append(CrossRefCandidate(
                kind="DEFINED_NEVER_REFERENCED",
                subject=ident,
                detail=(f"{sorted(names)} cited neither by number nor by "
                        "name anywhere outside its own definition"),
                why_it_might_be_fine=(
                    "it may be cited only from a SIBLING document, or be an "
                    "entry point invoked by the system rather than by "
                    "another algorithm. Unreferenced is not unused."),
                occurrences=0,
            ))

    return CrossRefReport(
        definitions={k: tuple(sorted(v)) for k, v in defs.items()},
        reference_counts=dict(refs),
        candidates=tuple(candidates),
        text_was_supplied=True,
        ligatures_found=ligatures_found,
    )


def format_crossref(report: CrossRefReport) -> str:
    """Operator-facing render. Says CANDIDATES throughout, and says why
    that word was chosen."""
    if not isinstance(report, CrossRefReport):
        raise SpecCrossRefError(
            "format_crossref() takes a CrossRefReport, not "
            f"{type(report).__name__}")

    if report.status == "NOT_ASSESSED":
        return ("NOT_ASSESSED -- no document text was supplied. Nothing was "
                "checked, which is not the same as nothing being wrong.")

    lines = [
        "SPECIFICATION CROSS-REFERENCE",
        "",
        f"definitions found : {report.defined_count}",
        f"identifiers cited : {report.referenced_count}",
    ]
    if report.ligatures_found:
        lines.append(
            f"ligatures expanded: {report.ligatures_found}  "
            "(left in place, these silently truncate identifiers and "
            "manufacture false candidates)")
    lines.append("")

    if not report.candidates:
        lines.append(
            "NO CANDIDATES -- every citation resolves, no identifier carries "
            "two names, no name carries two identifiers.")
        lines.append(
            "That is a real result about this document's internal "
            "consistency. It is not a statement that the document is "
            "correct, only that it is not inconsistent in the ways checked "
            "here.")
        return "\n".join(lines)

    lines.append(f"CANDIDATES ({len(report.candidates)}) -- NOT findings:")
    for c in report.candidates:
        lines.append(f"  [{c.kind}] {c.subject}")
        lines.append(f"      {c.detail}")
        lines.append(f"      might be fine because: {c.why_it_might_be_fine}")
    lines.append("")
    lines.append(
        "Every candidate raised by this module on its first real run against "
        "a 166-page cryptographic specification turned out to be innocent -- "
        "two of them caused by the checker's own text extraction. Resolve "
        "each one against the document by eye before reporting anything.")
    return "\n".join(lines)
