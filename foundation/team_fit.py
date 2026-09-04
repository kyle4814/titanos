"""
Team Fit — score each credential-walled target in `team_targets.py` against
a declared team capability profile, and rank the 22 by winnability.

This is the missing link between "here are 22 contracts a team could win"
(`team_targets.py`) and "here are the ones YOUR team can actually win".
Kyle is assembling a team; the moment he declares what the team brings
(turnover, insurance cover, reference contracts, languages, 24x7 staffing,
named capabilities), this ranks every target FIT / PARTIAL / NO-FIT and
names the exact clause that blocks each gap.

HONEST BY CONSTRUCTION. Kyle's own rule: absence of a stated requirement
is UNKNOWN, never satisfied. So:
  - A requirement this module cannot parse into a structured check is
    UNKNOWN (surfaced for a human), never silently passed.
  - A money/reference/language threshold the declared profile does not
    clear is a GAP, quoted verbatim.
  - A capability requirement (SOC/MDR/etc.) is UNKNOWN unless the profile
    explicitly declares that capability — a team saying nothing about SOC
    does not "meet" a SOC requirement.
  - "English/UK — no barrier" style lines are the only auto-MEET, because
    they assert the absence of a wall, not the presence of one.

Nothing here fetches, spends, or contacts anyone. It reads the registry
and a caller-supplied profile and returns a structured verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Tuple

from foundation.team_targets import TEAM_TARGETS, TeamTarget, live_team_targets

__all__ = [
    "TeamCapability",
    "ReqCheck",
    "TargetFit",
    "Verdict",
    "assess_fit",
    "rank_targets",
    "render_fit_md",
]


class Verdict(str, Enum):
    MEET = "MEET"          # every parseable requirement cleared, none UNKNOWN
    PARTIAL = "PARTIAL"    # some cleared, at least one UNKNOWN, no hard GAP
    GAP = "GAP"            # at least one requirement the profile fails outright


# Requirement-string categories the parser recognises. A string that matches
# none of these is UNKNOWN — never assumed met.
class _Kind(str, Enum):
    TURNOVER = "turnover"
    INSURANCE = "insurance"
    REFERENCES = "references"
    LANGUAGE = "language"
    CAPABILITY = "capability"
    NO_BARRIER = "no_barrier"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TeamCapability:
    """What the team declares it can bring. Every field defaults to the
    weakest honest value (zero / empty / False), so an undeclared strength
    is never counted as present — the same UNKNOWN-is-not-zero discipline,
    applied to the team's own claims."""

    annual_turnover_eur: float = 0.0
    max_insurance_eur: float = 0.0          # highest single cover the team can hold/obtain
    can_obtain_higher_insurance: bool = False
    reference_contracts: int = 0            # number of deliverable corporate references
    largest_reference_eur: float = 0.0      # value of the largest single reference
    languages: Tuple[str, ...] = ()         # e.g. ("english", "german")
    has_247_soc: bool = False               # 24x7x365 SOC / incident response
    capabilities: Tuple[str, ...] = ()      # declared capability tags, lowercase
    named_testers: int = 0                  # for pen-test style "N named testers"

    def has_capability(self, *needles: str) -> bool:
        blob = " ".join(self.capabilities).lower()
        return any(n.lower() in blob for n in needles)

    def speaks(self, lang: str) -> bool:
        return lang.lower() in {x.lower() for x in self.languages}


@dataclass(frozen=True)
class ReqCheck:
    requirement: str          # the verbatim requirement string
    kind: _Kind
    status: str               # MEET / GAP / UNKNOWN
    detail: str               # human-readable why


@dataclass(frozen=True)
class TargetFit:
    target: TeamTarget
    verdict: Verdict
    checks: Tuple[ReqCheck, ...]

    @property
    def gaps(self) -> Tuple[ReqCheck, ...]:
        return tuple(c for c in self.checks if c.status == "GAP")

    @property
    def unknowns(self) -> Tuple[ReqCheck, ...]:
        return tuple(c for c in self.checks if c.status == "UNKNOWN")


# --- money parsing -----------------------------------------------------------

_MONEY_RE = re.compile(r"€\s*([\d][\d,\.]*)")


def _parse_money(text: str) -> Optional[float]:
    """First €-amount in the string as a float, or None. '€13,000,000' ->
    13000000.0; '€720k' -> 720000.0; '€1,000,000' -> 1000000.0."""
    m = _MONEY_RE.search(text)
    if not m:
        # handle '£' too — UK targets quote sterling
        m = re.search(r"£\s*([\d][\d,\.]*)\s*([mk]?)", text, re.IGNORECASE)
        if not m:
            return None
    raw = m.group(1).replace(",", "")
    try:
        val = float(raw)
    except ValueError:
        return None
    tail = text[m.end():m.end() + 2].lower()
    if tail.startswith("m"):
        val *= 1_000_000
    elif tail.startswith("k"):
        val *= 1_000
    return val


_INT_RE = re.compile(r"\b(\d+)\b")


def _parse_leading_int(text: str) -> Optional[int]:
    m = _INT_RE.search(text)
    return int(m.group(1)) if m else None


# --- requirement classification ---------------------------------------------

_INSURANCE_WORDS = (
    "insurance", "indemnity", "liability", "professional liability",
    "public liability", "employer's liability", "cyber insurance",
)
_LANG_MAP = {
    "german": "german",
    "dutch": "dutch",
    "danish": "danish",
    "french": "french",
}
_CAP_WORDS = (
    "soc", "mdr", "siem", "soar", "incident response", "managed-service",
    "managed service", "cyber assurance", "audit capability",
    "security advisory", "security governance", "risk-analysis",
    "cybersecurity managed-service", "penetration", "pen test",
)


# Hedge markers: a requirement worded as a soft "probably / confirm this"
# is never a hard structured pass or fail — it routes to UNKNOWN (human read),
# even when it names a country or language. "Likely Danish-market presence or
# partner; confirm in the ESPD" is about market presence and is explicitly
# hedged, not a firm "a team member must speak Danish".
_HEDGE_WORDS = ("likely", "confirm", "often need", "may need",
                "presence or partner", "clearances")


def _classify(req: str) -> _Kind:
    low = req.lower()
    if "no barrier" in low or "no language" in low or "no jurisdiction" in low:
        return _Kind.NO_BARRIER
    if any(h in low for h in _HEDGE_WORDS):
        return _Kind.UNKNOWN
    if "turnover" in low:
        return _Kind.TURNOVER
    if any(w in low for w in _INSURANCE_WORDS):
        return _Kind.INSURANCE
    if "named testers" in low:
        return _Kind.REFERENCES
    if "reference" in low or "similar contract" in low or "similar services" in low \
            or ("contracts" in low and "last 3 years" in low) \
            or "previous contracts" in low or "single order" in low \
            or "single order worth" in low:
        return _Kind.REFERENCES
    if any(l in low for l in _LANG_MAP):
        # a language name present AND framed as a requirement, not "no barrier"
        return _Kind.LANGUAGE
    if any(w in low for w in _CAP_WORDS):
        return _Kind.CAPABILITY
    return _Kind.UNKNOWN


def _check(req: str, cap: TeamCapability) -> ReqCheck:
    kind = _classify(req)

    if kind is _Kind.NO_BARRIER:
        return ReqCheck(req, kind, "MEET", "asserts no wall to clear")

    if kind is _Kind.TURNOVER:
        need = _parse_money(req)
        if need is None:
            return ReqCheck(req, kind, "UNKNOWN", "turnover figure not parseable")
        if cap.annual_turnover_eur >= need:
            return ReqCheck(req, kind, "MEET",
                            f"team turnover €{cap.annual_turnover_eur:,.0f} ≥ €{need:,.0f}")
        return ReqCheck(req, kind, "GAP",
                        f"team turnover €{cap.annual_turnover_eur:,.0f} < €{need:,.0f}")

    if kind is _Kind.INSURANCE:
        need = _parse_money(req)
        if need is None:
            # "Insurance: has in place OR ability to obtain" — no figure
            if cap.can_obtain_higher_insurance:
                return ReqCheck(req, kind, "MEET", "team willing/able to obtain cover")
            return ReqCheck(req, kind, "UNKNOWN", "no figure; obtain-ability not declared")
        if cap.max_insurance_eur >= need:
            return ReqCheck(req, kind, "MEET",
                            f"cover €{cap.max_insurance_eur:,.0f} ≥ €{need:,.0f}")
        if cap.can_obtain_higher_insurance:
            return ReqCheck(req, kind, "UNKNOWN",
                            f"cover €{cap.max_insurance_eur:,.0f} < €{need:,.0f}, "
                            "but team declares it can raise cover — confirm before bid")
        return ReqCheck(req, kind, "GAP",
                        f"cover €{cap.max_insurance_eur:,.0f} < €{need:,.0f}")

    if kind is _Kind.REFERENCES:
        if "named testers" in req.lower():
            need = _parse_leading_int(req) or 1
            if cap.named_testers >= need:
                return ReqCheck(req, kind, "MEET",
                                f"{cap.named_testers} named testers ≥ {need}")
            return ReqCheck(req, kind, "GAP",
                            f"{cap.named_testers} named testers < {need}")
        need_n = _parse_leading_int(req)
        need_val = _parse_money(req)
        # count check
        if need_n is not None and cap.reference_contracts < need_n:
            return ReqCheck(req, kind, "GAP",
                            f"{cap.reference_contracts} references < {need_n} required")
        # value-of-each check, where quoted
        if need_val is not None and cap.largest_reference_eur < need_val:
            return ReqCheck(req, kind, "GAP",
                            f"largest reference €{cap.largest_reference_eur:,.0f} "
                            f"< €{need_val:,.0f} required per reference")
        if need_n is None and need_val is None:
            # e.g. "Previous contracts required (Pass/Fail)" — no number
            if cap.reference_contracts > 0:
                return ReqCheck(req, kind, "MEET",
                                f"team has {cap.reference_contracts} references")
            return ReqCheck(req, kind, "UNKNOWN", "count unspecified; team declares none")
        return ReqCheck(req, kind, "MEET",
                        f"{cap.reference_contracts} references"
                        + (f", largest €{cap.largest_reference_eur:,.0f}"
                           if need_val is not None else ""))

    if kind is _Kind.LANGUAGE:
        low = req.lower()
        lang = next((v for k, v in _LANG_MAP.items() if k in low), None)
        if lang is None:
            return ReqCheck(req, kind, "UNKNOWN", "language not identified")
        if cap.speaks(lang):
            return ReqCheck(req, kind, "MEET", f"team member speaks {lang}")
        return ReqCheck(req, kind, "GAP", f"no declared {lang} speaker")

    if kind is _Kind.CAPABILITY:
        low = req.lower()
        needed = [w for w in _CAP_WORDS if w in low]
        if any("soc" in n or "mdr" in n or "incident response" in n for n in needed):
            if cap.has_247_soc or cap.has_capability("soc", "mdr", "incident response"):
                return ReqCheck(req, kind, "MEET", "team declares SOC/MDR/IR capability")
            return ReqCheck(req, kind, "UNKNOWN",
                            "SOC/MDR/IR capability not declared by team")
        if cap.has_capability(*needed):
            return ReqCheck(req, kind, "MEET", "team declares the capability")
        return ReqCheck(req, kind, "UNKNOWN",
                        "capability not declared by team")

    return ReqCheck(req, _Kind.UNKNOWN, "UNKNOWN",
                    "requirement not machine-checkable — human must read it")


def assess_fit(target: TeamTarget, cap: TeamCapability) -> TargetFit:
    checks = tuple(_check(r, cap) for r in target.requirements)
    if any(c.status == "GAP" for c in checks):
        verdict = Verdict.GAP
    elif any(c.status == "UNKNOWN" for c in checks):
        verdict = Verdict.PARTIAL
    else:
        verdict = Verdict.MEET
    return TargetFit(target=target, verdict=verdict, checks=checks)


# rank: MEET first, then PARTIAL, then GAP; within a class, soonest deadline
# first (dated before undated), so the ranked list is directly actionable.
_VERDICT_ORDER = {Verdict.MEET: 0, Verdict.PARTIAL: 1, Verdict.GAP: 2}


def rank_targets(cap: TeamCapability,
                 now: Optional[datetime] = None,
                 live_only: bool = True) -> List[TargetFit]:
    now = now or datetime.now(timezone.utc)
    pool = live_team_targets(now) if live_only else list(TEAM_TARGETS)
    fits = [assess_fit(t, cap) for t in pool]

    def sort_key(f: TargetFit):
        d = f.target.deadline_date()
        return (_VERDICT_ORDER[f.verdict],
                0 if d is not None else 1,
                d.toordinal() if d is not None else 10 ** 9)

    return sorted(fits, key=sort_key)


def render_fit_md(cap: TeamCapability, now: Optional[datetime] = None) -> str:
    now = now or datetime.now(timezone.utc)
    ranked = rank_targets(cap, now)
    n_meet = sum(1 for f in ranked if f.verdict is Verdict.MEET)
    n_part = sum(1 for f in ranked if f.verdict is Verdict.PARTIAL)
    n_gap = sum(1 for f in ranked if f.verdict is Verdict.GAP)

    lines: List[str] = []
    lines.append("# TEAM FIT — ranked winnability of the live targets")
    lines.append("")
    lines.append(f"Profile: turnover €{cap.annual_turnover_eur:,.0f} · "
                 f"insurance €{cap.max_insurance_eur:,.0f}"
                 + (" (can raise)" if cap.can_obtain_higher_insurance else "")
                 + f" · {cap.reference_contracts} references · "
                 f"languages {', '.join(cap.languages) or 'none declared'} · "
                 f"24x7 SOC {'yes' if cap.has_247_soc else 'no'}")
    lines.append("")
    lines.append(f"**{n_meet} MEET · {n_part} PARTIAL (needs a human read) · "
                 f"{n_gap} GAP** — of {len(ranked)} live targets.")
    lines.append("")
    _sym = {Verdict.MEET: "✅ MEET", Verdict.PARTIAL: "🟡 PARTIAL",
            Verdict.GAP: "⛔ GAP"}
    for f in ranked:
        t = f.target
        lines.append(f"## {_sym[f.verdict]} — {t.title}")
        lines.append(f"- **Value** {t.value} · **Deadline** {t.deadline}")
        lines.append(f"- **Link** {t.link}")
        for c in f.checks:
            mark = {"MEET": "✓", "GAP": "✗", "UNKNOWN": "?"}[c.status]
            lines.append(f"  - {mark} {c.requirement} — {c.detail}")
        lines.append("")
    lines.append("Legend: ✓ met · ✗ gap the profile fails · "
                 "? the team must read/confirm (never auto-passed).")
    return "\n".join(lines)
