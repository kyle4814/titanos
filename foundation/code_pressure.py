"""Is this repository spending its recent commits fixing things?

WHY THIS EXISTS, AND WHY IT WAS NOT BUILT SOONER

`opportunity.rank()` awards points for a signal of kind CODE_PRESSURE, and
for three cells no instrument emitted one. That made INVESTIGATE
structurally unreachable: with every other live lever pulled, the best
achievable priority was 4 against a threshold of 5. The ceiling was made
legible first (`opportunity.ceiling_analysis`) and deliberately not
"fixed" by lowering the threshold, because inventing points is tuning.

This is the honest alternative: measure something real that the missing
lever was always meant to name.

WHAT IT MEASURES

The share of recent commits whose subject lines describe REMEDIATION --
fixing, reverting, patching a regression -- rather than new work. A
repository whose recent history is mostly repair is under pressure in a
sense a maintainer would recognise.

WHAT IT DOES NOT MEASURE, AND MUST NEVER BE READ AS

Not a defect. Not a bug count. Not code quality. A commit saying "fix" is
evidence that somebody fixed something, which is ordinary healthy
behaviour in isolation. Only the SHARE, over a stated window, with a
stated minimum sample, is the signal -- and even then it is weak evidence
from natural-language subject lines, which this module says out loud
rather than burying.

WHY SUBJECT LINES AND NOT DIFFS

Diff statistics would be stronger evidence. They cost one API request per
commit, and the unauthenticated budget is 60 requests per hour -- a single
18-target population sweep would exhaust it. Subject lines arrive free
inside the commit list the mouth already fetches. That is the honest
trade, recorded rather than hidden: weaker evidence at zero marginal cost,
labelled as weaker.

THE THRESHOLD IS A JUDGEMENT AND IS VERSIONED

`PRESSURE_MODEL_VERSION` exists because the share at which repair becomes
"pressure" is a choice, not a discovery. It will be wrong and will need
calibration against outcomes the system does not yet have.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

__all__ = [
    "PressureIntegrityError",
    "COMMIT_CLASSES",
    "PRESSURE_MODEL_VERSION",
    "MIN_SAMPLE",
    "PRESSURE_SHARE",
    "classify_subject",
    "PressureProfile",
    "measure_pressure",
]


class PressureIntegrityError(ValueError):
    """A pressure claim exceeded the evidence behind it."""


PRESSURE_MODEL_VERSION = "1"

# Below this many commits the share is noise: three commits, two of them
# fixes, is not a pattern.
MIN_SAMPLE = 5

# The share of remediation commits at which the window is called pressured.
# A judgement, not a discovery -- see the module docstring.
PRESSURE_SHARE = 0.40

COMMIT_CLASSES = ("REMEDIATION", "FEATURE", "MAINTENANCE", "UNCLASSIFIED")

# Deliberately conservative and word-bounded. "prefix" must not match
# "fix", and "reverted to" in prose must not be mistaken for a revert
# commit. Anything unmatched stays UNCLASSIFIED rather than being guessed.
_REMEDIATION = re.compile(
    r"\b(fix(e[sd])?|hotfix|bugfix|revert|rollback|regress(ion|ed)?|"
    r"repair|broken|breakage|patch(e[sd])?|correct(s|ed)?|workaround)\b",
    re.I)
_FEATURE = re.compile(
    r"\b(add(s|ed|ing)?|feat|feature|implement(s|ed|ing)?|introduce(s|d)?|"
    r"support|enable(s|d)?|new)\b", re.I)
_MAINTENANCE = re.compile(
    r"\b(chore|bump|deps?|dependenc(y|ies)|lint|format|typo|docs?|"
    r"readme|comment|rename|refactor|cleanup|merge|release|version)\b",
    re.I)


def classify_subject(subject: str) -> str:
    """One commit subject to one class.

    REMEDIATION wins over FEATURE when both appear, because "add retry to
    fix flaky upload" is repair work wearing a feature verb. MAINTENANCE
    is checked last so that "fix typo" reads as remediation only if the
    remediation word is the dominant one -- it is not, so ordering places
    maintenance markers ahead of the weaker feature signal.
    """
    s = (subject or "").strip()
    if not s:
        return "UNCLASSIFIED"
    # A merge commit describes no work of its own.
    if re.match(r"^merge\b", s, re.I):
        return "MAINTENANCE"
    if _REMEDIATION.search(s):
        # "fix typo" / "fix docs" is housekeeping, not repair pressure.
        if re.search(r"\b(typo|docs?|readme|comment|spelling|lint|format)\b",
                     s, re.I):
            return "MAINTENANCE"
        return "REMEDIATION"
    if _MAINTENANCE.search(s):
        return "MAINTENANCE"
    if _FEATURE.search(s):
        return "FEATURE"
    return "UNCLASSIFIED"


@dataclass(frozen=True)
class PressureProfile:
    """What the recent window actually looked like.

    `is_pressured()` is deliberately separate from the counts: a caller
    that wants the raw shape gets it without being handed a verdict.
    """

    sample: int
    remediation: int
    feature: int
    maintenance: int
    unclassified: int
    evidence: tuple[str, ...] = ()
    model_version: str = PRESSURE_MODEL_VERSION

    def classified(self) -> int:
        """Commits the classifier could actually place. The share is taken
        over these, not over the whole window -- an unreadable subject is
        not evidence of anything, in either direction."""
        return self.sample - self.unclassified

    def share(self) -> Optional[float]:
        """Remediation share of classified commits. None when there is not
        enough to divide by -- never a fabricated 0.0."""
        base = self.classified()
        return (self.remediation / base) if base else None

    def is_measurable(self) -> bool:
        """The CLASSIFIED base must meet the minimum, not the raw window.

        Found by live execution: dotnet/runtime returned a 67% share from
        two remediation commits out of three classified, with seven
        subjects unreadable. Guarding only the window size moved the
        "three commits, two fixes is not a pattern" problem down one level
        instead of solving it.
        """
        return self.sample >= MIN_SAMPLE and self.classified() >= MIN_SAMPLE

    def is_pressured(self) -> bool:
        """False whenever the sample is too small to say. Silence about a
        three-commit window is the correct answer, not a low score."""
        if not self.is_measurable():
            return False
        share = self.share()
        return share is not None and share >= PRESSURE_SHARE

    def show_the_math(self) -> str:
        if not self.is_measurable():
            return (f"NOT MEASURABLE -- {self.sample} commit(s), only "
                    f"{self.classified()} with a classifiable subject; "
                    f"needs at least {MIN_SAMPLE} classified")
        lines = [f"REMEDIATION SHARE {self.share():.0%} of "
                 f"{self.classified()} classified commit(s) "
                 f"(model v{self.model_version}, threshold "
                 f"{PRESSURE_SHARE:.0%})",
                 f"  remediation   {self.remediation}",
                 f"  feature       {self.feature}",
                 f"  maintenance   {self.maintenance}",
                 f"  unclassified  {self.unclassified} (excluded from the share)"]
        for e in self.evidence:
            lines.append(f"  evidence: {e}")
        lines.append("  NOTE: subject-line evidence is weak; it describes "
                     "what commits SAY, not what they changed.")
        return "\n".join(lines)


def measure_pressure(items: Sequence[dict]) -> PressureProfile:
    """Measure one commit window. Never fetches anything.

    `items` are commit dicts as `mouth_github_commits.parse_items()`
    already produces, so this costs no additional API request.
    """
    counts = {c: 0 for c in COMMIT_CLASSES}
    evidence: list[str] = []
    for it in items:
        subject = str(it.get("subject", ""))
        cls = classify_subject(subject)
        counts[cls] += 1
        if cls == "REMEDIATION":
            sha = str(it.get("sha", ""))[:8]
            evidence.append(f"{sha} {subject[:70]}")
    return PressureProfile(
        sample=len(items), remediation=counts["REMEDIATION"],
        feature=counts["FEATURE"], maintenance=counts["MAINTENANCE"],
        unclassified=counts["UNCLASSIFIED"], evidence=tuple(evidence[:5]))
