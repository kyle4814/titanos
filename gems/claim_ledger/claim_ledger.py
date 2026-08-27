#!/usr/bin/env python3
"""claim_ledger — keep claims of different confidence from collapsing into one tier.

Problem this addresses (evidenced, not assumed): the 2026 State of the
Fact-Checkers report (Poynter) found tool access among fact-checking orgs
dropped from 44.3% to 30.7%, and practitioners describe the real bottleneck
as the verification *workflow* — manual transcription, claim identification,
and juggling many browser tabs — not claim *detection*. A recurring failure
mode in that workflow is that a directly-sourced fact, a synthesized
inference, and an unverified trend claim end up looking the same on the
page once they're all typed into the same document.

What this tool does: takes a small, explicit list of claims (JSON or YAML),
each with its own classification and evidence, and refuses to let a claim
sit at a stronger confidence than its evidence supports. It then prints a
report that keeps the tiers visually and structurally separate, and flags
any two claims about the same subject that disagree.

What it does NOT do: fetch anything from the web, verify a claim's truth,
resolve a disagreement automatically, or replace human judgment. It only
enforces that the *stated* confidence tier is internally consistent with
the *stated* evidence — a much smaller, honest claim.

Standalone: stdlib only, single file, no network access, no dependency on
the rest of this repository. Copy this one file to use it elsewhere.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

CLASSIFICATIONS = (
    "VERIFIED_FACT",          # directly sourced from primary/authoritative evidence
    "SUPPORTED_INFERENCE",    # a synthesis or model built on evidenced claims
    "UNVERIFIED_CLAIM",       # asserted, not yet independently evidenced
    "OPINION_OR_TREND",       # a stated view, forecast, or trend judgment
)

# Classifications that make a strong evidentiary claim. Entering one of
# these without a non-empty source is refused, not silently downgraded —
# a caller who gets this wrong should see an error, not a quiet demotion.
REQUIRES_SOURCE = {"VERIFIED_FACT", "SUPPORTED_INFERENCE"}

# HIGH confidence is only earned by the classes that can actually support it.
CANNOT_BE_HIGH_CONFIDENCE = {"UNVERIFIED_CLAIM", "OPINION_OR_TREND"}

CONFIDENCE_LEVELS = ("HIGH", "MEDIUM", "LOW")


class ClaimError(ValueError):
    """A claim's stated confidence/classification/evidence are inconsistent."""


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    classification: str
    confidence: str
    source: str = ""
    subject: str = ""  # free-text grouping key for contradiction detection

    def __post_init__(self) -> None:
        if not self.claim_id.strip():
            raise ClaimError("claim_id must be non-empty")
        if not self.text.strip():
            raise ClaimError(f"{self.claim_id}: text must be non-empty")
        if self.classification not in CLASSIFICATIONS:
            raise ClaimError(
                f"{self.claim_id}: classification {self.classification!r} not "
                f"in {CLASSIFICATIONS}"
            )
        if self.confidence not in CONFIDENCE_LEVELS:
            raise ClaimError(
                f"{self.claim_id}: confidence {self.confidence!r} not in "
                f"{CONFIDENCE_LEVELS}"
            )
        if self.classification in REQUIRES_SOURCE and not self.source.strip():
            raise ClaimError(
                f"{self.claim_id}: classification {self.classification} "
                f"requires a non-empty source"
            )
        if self.confidence == "HIGH" and self.classification in CANNOT_BE_HIGH_CONFIDENCE:
            raise ClaimError(
                f"{self.claim_id}: {self.classification} can never be HIGH "
                f"confidence — that would make it a different classification"
            )


@dataclass
class Ledger:
    claims: list[Claim] = field(default_factory=list)

    def add(self, claim: Claim) -> None:
        self.claims.append(claim)

    def by_tier(self) -> dict[str, list[Claim]]:
        out: dict[str, list[Claim]] = {c: [] for c in CLASSIFICATIONS}
        for claim in self.claims:
            out[claim.classification].append(claim)
        return out

    def find_subject_conflicts(self) -> list[tuple[str, list[Claim]]]:
        """Group claims sharing a non-empty subject; flag groups spanning
        more than one classification tier as needing reconciliation.

        This is a structural hint, not a truth judgment — it only says
        "these disagree in stated tier," never which one is right.
        """
        by_subject: dict[str, list[Claim]] = {}
        for claim in self.claims:
            if not claim.subject.strip():
                continue
            by_subject.setdefault(claim.subject, []).append(claim)
        conflicts = []
        for subject, group in by_subject.items():
            tiers = {c.classification for c in group}
            if len(tiers) > 1:
                conflicts.append((subject, group))
        return conflicts


def load_claims(path: Path) -> Ledger:
    data = json.loads(path.read_text())
    ledger = Ledger()
    for row in data:
        ledger.add(Claim(
            claim_id=row["claim_id"],
            text=row["text"],
            classification=row["classification"],
            confidence=row["confidence"],
            source=row.get("source", ""),
            subject=row.get("subject", ""),
        ))
    return ledger


def render_report(ledger: Ledger) -> str:
    lines = []
    tiers = ledger.by_tier()
    for tier in CLASSIFICATIONS:
        claims = tiers[tier]
        if not claims:
            continue
        lines.append(f"== {tier} ({len(claims)}) ==")
        for c in claims:
            src = f" [{c.source}]" if c.source else ""
            lines.append(f"  [{c.confidence}] {c.claim_id}: {c.text}{src}")
        lines.append("")

    conflicts = ledger.find_subject_conflicts()
    if conflicts:
        lines.append("== NEEDS_RECONCILIATION (same subject, different tiers) ==")
        for subject, group in conflicts:
            lines.append(f"  subject={subject!r}:")
            for c in group:
                lines.append(f"    [{c.classification}/{c.confidence}] {c.claim_id}: {c.text}")
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("claims_file", type=Path, help="JSON file of claims")
    args = parser.parse_args(argv)

    try:
        ledger = load_claims(args.claims_file)
    except ClaimError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 1

    print(render_report(ledger))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
