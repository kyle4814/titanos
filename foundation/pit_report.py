"""foundation/pit_report.py -- how contested a bug-bounty target already
is, and where its confirmed findings actually came from.

WHY THIS EXISTS

`mouth_bounty.py` and `income_watch.py` answer "which programmes exist"
and "what do they advertise". Neither answers the question that decides
whether a solo operator with no reputation should spend a month on one:
how much has already been taken, at what acceptance rate, and in which
tier of access.

Swiss Post publishes a Public Intrusion Test final report every year --
they are on disk in the e-voting corpus, 2022 through 2026. The 2026
report states 85 reports, 6 confirmed (7% acceptance), 23 duplicates
(27% duplicate rate), and that BOTH paying findings originated in the
invitation-only PIT+ tier of 20, not the open tier of 5,479 IPs. That
is the intelligence that reorders a hunt, and it was sitting in a PDF.

WHAT IT PRODUCES

A `PitSummary`: the headline counts a report states, the confirmed
findings with their severities and rewards, and the derived acceptance
and duplicate rates. Every number is either extracted verbatim from the
report text or computed from extracted numbers -- never inferred. A
figure the report does not state is `None`, not zero: a report that
omits its duplicate count has not told you it had no duplicates.

LIMITATION, STATED PLAINLY: the extraction patterns are tuned to the
2026 report's phrasing ("received a total of 85 reports", "N High
severity finding ... were confirmed", per-finding "Title/Severity/
Reward" blocks). The 2022-2025 reports use different prose -- "received
four reports", "more than 530 vulnerability reports" -- and return all-
`None` rather than wrong numbers, which is the correct failure
direction: a summary that cannot read a report says so via UNKNOWN
fields, it does not guess. Widening to every year's idiosyncratic
phrasing would over-fit patterns to five documents; the 2026 report is
the one that matters (it is the current programme's contest record) and
it parses exactly.

NO NETWORK. Text in -- the caller extracts the PDF, the same split as
every other document tool here. Extraction is the caller's problem
because extraction is where the ligature and offset bugs live (see
`spec_crossref.normalise_extracted_text`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple

__all__ = [
    "PitReportError",
    "SEVERITIES",
    "ConfirmedFinding",
    "PitSummary",
    "summarise_pit_report",
    "format_pit_summary",
]


class PitReportError(ValueError):
    """Raised on non-text input. This module refuses to guess at a
    report it cannot read."""


SEVERITIES = ("Critical", "High", "Medium", "Low")


@dataclass(frozen=True)
class ConfirmedFinding:
    """One confirmed finding a report describes. `reward_eur` is None
    when the report states the finding but not its reward -- UNKNOWN,
    never zero."""

    title: str
    severity: str
    reward_eur: Optional[int]

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise PitReportError(
                f"severity {self.severity!r} must be one of {SEVERITIES}")
        if not self.title.strip():
            raise PitReportError("a confirmed finding must carry a title")


@dataclass(frozen=True)
class PitSummary:
    """What one Public Intrusion Test report says about how contested
    its target already is."""

    reports_received: Optional[int]
    confirmed_count: Optional[int]
    duplicates: Optional[int]
    out_of_scope: Optional[int]
    informative: Optional[int]
    findings: Tuple[ConfirmedFinding, ...]
    text_was_supplied: bool

    @property
    def status(self) -> str:
        return "SUMMARISED" if self.text_was_supplied else "NOT_ASSESSED"

    @property
    def acceptance_rate(self) -> Optional[float]:
        """Confirmed / received, as a percentage. None when either
        figure is missing -- a rate computed from a guessed denominator
        is a fabricated statistic."""
        if not self.reports_received or self.confirmed_count is None:
            return None
        return 100.0 * self.confirmed_count / self.reports_received

    @property
    def duplicate_rate(self) -> Optional[float]:
        if not self.reports_received or self.duplicates is None:
            return None
        return 100.0 * self.duplicates / self.reports_received

    @property
    def top_reward_eur(self) -> Optional[int]:
        rewards = [f.reward_eur for f in self.findings if f.reward_eur is not None]
        return max(rewards) if rewards else None


# "Swiss Post received a total of 85 reports."
_RECEIVED = re.compile(r"received a total of\s+([\d,]+)\s+reports?", re.I)
# "1 High severity finding, 1 Medium severity finding and 4 Low ... were confirmed"
_CONFIRMED_LINE = re.compile(
    r"((?:\d+\s+(?:Critical|High|Medium|Low)\s+severity[^.]*?)+)\s+were confirmed",
    re.I)
_SEV_COUNT = re.compile(
    r"(\d+)\s+(Critical|High|Medium|Low)\s+severity", re.I)
_DUPLICATES = re.compile(r"([\d,]+)\s+as duplicates?", re.I)
_OUT_OF_SCOPE = re.compile(r"([\d,]+)\s+as out of scope", re.I)
_INFORMATIVE = re.compile(r"([\d,]+)\s+(?:reports?\s+)?(?:were\s+)?"
                          r"class\w*\s+as Informative", re.I)
# A finding block: "Severity High ... Reward 19,000 €"
# A finding block. The title is everything up to the next field label
# (`Number` or `Severity`), not `.+?` which stops at the first space and
# yields one-word titles like "Cache". The whole block runs to the next
# `Title` or end of text.
_FINDING_BLOCK = re.compile(
    r"Title\s+(?P<title>.+?)\s+(?:Number|Severity)\b"
    r".*?Severity\s+(?P<sev>Critical|High|Medium|Low)\b"
    r".*?(?:Reward\s+(?P<reward>[\d,\.]+)\s*(?:€|EUR|euro))?"
    r"(?=\s+Title\s|\Z)",
    re.I | re.S)


def _int(match) -> Optional[int]:
    if not match:
        return None
    return int(match.group(1).replace(",", "").replace(".", ""))


def summarise_pit_report(text: str) -> PitSummary:
    """Extract the contest statistics and confirmed findings from one
    PIT final report's text."""
    if not isinstance(text, str):
        raise PitReportError(
            f"summarise_pit_report() takes report text, got {type(text).__name__}")

    if not text.strip():
        return PitSummary(None, None, None, None, None, (),
                          text_was_supplied=False)

    # Collapse ALL whitespace, newlines included: the source PDF wraps
    # "classified as \n Informative" across a line, and a count regex
    # that stops at the newline reports the figure as UNKNOWN -- absence
    # manufactured by extraction, the failure this whole file guards.
    flat = re.sub(r"\s+", " ", text)

    confirmed_count = None
    cm = _CONFIRMED_LINE.search(flat)
    if cm:
        confirmed_count = sum(int(m.group(1))
                              for m in _SEV_COUNT.finditer(cm.group(1)))

    findings = []
    for block in _FINDING_BLOCK.finditer(flat):
        title = " ".join(block.group("title").split())
        # Guard against the greedy title swallowing a whole page: a real
        # finding title is a line, not a paragraph.
        if len(title) > 200:
            title = title[:200]
        reward = block.group("reward")
        findings.append(ConfirmedFinding(
            title=title,
            severity=block.group("sev").capitalize(),
            reward_eur=int(reward.replace(",", "").replace(".", ""))
            if reward else None,
        ))

    return PitSummary(
        reports_received=_int(_RECEIVED.search(flat)),
        confirmed_count=confirmed_count,
        duplicates=_int(_DUPLICATES.search(flat)),
        out_of_scope=_int(_OUT_OF_SCOPE.search(flat)),
        informative=_int(_INFORMATIVE.search(flat)),
        findings=tuple(findings),
        text_was_supplied=True,
    )


def format_pit_summary(summary: PitSummary) -> str:
    """Operator-facing render. Leads with acceptance and duplicate
    rate, because those are what decide whether a target is worth a
    month."""
    if not isinstance(summary, PitSummary):
        raise PitReportError(
            "format_pit_summary() takes a PitSummary, not "
            f"{type(summary).__name__}")

    if summary.status == "NOT_ASSESSED":
        return ("NOT_ASSESSED -- no report text was supplied. Nothing was "
                "read, which is not the same as a target with no history.")

    lines = ["PUBLIC INTRUSION TEST -- HOW CONTESTED THIS TARGET IS", ""]

    def _line(label, value, suffix=""):
        shown = "UNKNOWN (not stated in this report)" if value is None \
            else f"{value}{suffix}"
        lines.append(f"  {label:<22}: {shown}")

    _line("reports received", summary.reports_received)
    _line("confirmed", summary.confirmed_count)
    _line("duplicates", summary.duplicates)
    _line("out of scope", summary.out_of_scope)
    _line("informative", summary.informative)

    ar = summary.acceptance_rate
    dr = summary.duplicate_rate
    lines.append("")
    _line("acceptance rate", None if ar is None else f"{ar:.0f}", "%")
    _line("duplicate rate", None if dr is None else f"{dr:.0f}", "%")

    if summary.findings:
        lines.append("")
        lines.append("CONFIRMED FINDINGS (this is what survived, and paid):")
        for f in summary.findings:
            reward = "reward not stated" if f.reward_eur is None \
                else f"{f.reward_eur:,} EUR"
            lines.append(f"  [{f.severity}] {f.title}")
            lines.append(f"      {reward}")

    lines.append("")
    lines.append(
        "A low acceptance rate and a high duplicate rate mean the obvious "
        "findings are gone. Every UNKNOWN above is a figure this report "
        "did not state -- not a zero.")
    return "\n".join(lines)
