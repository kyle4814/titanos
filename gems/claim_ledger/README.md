# claim_ledger

A single-file, dependency-free tool that keeps claims of different
confidence from collapsing into one undifferentiated block of text.

## The problem, evidenced

The [2026 State of the Fact-Checkers report](https://www.poynter.org/wp-content/uploads/2026/03/2026-State-of-Fact-Checkers-4.pdf)
(Poynter) found fact-checking organisations reporting access to
technology/tools dropped from 44.3% to 30.7%. Practitioner accounts
([GIJN](https://gijn.org/stories/5-free-open-source-digital-tools-combat-disinformation/),
[HKS Misinformation Review](https://misinforeview.hks.harvard.edu/article/fact-checking-at-a-crossroads-fact-checkers-perspectives-on-community-notes-ai-integration-and-design-recommendations/))
describe the actual daily bottleneck as the verification *workflow* —
manual transcription, claim identification, and checking many browser
tabs — not claim *detection*. A recurring failure inside that workflow:
a directly-sourced fact, a synthesized inference, and an unverified
trend claim all end up typed into the same document, at the same visual
weight, once you've been through fifteen tabs.

## What this does

You give it a small JSON list of claims. Each claim declares its own
`classification` and `confidence`. The tool:

- **Refuses** a claim that asks for a stronger tier than its evidence
  supports (e.g. `VERIFIED_FACT` with no source is rejected outright,
  not silently downgraded — you see the error and fix the input).
- **Refuses** `HIGH` confidence on a classification that structurally
  can't earn it (`UNVERIFIED_CLAIM`, `OPINION_OR_TREND`).
- **Groups** the output report by tier, so `VERIFIED_FACT` never visually
  blends into `OPINION_OR_TREND`.
- **Flags** any two claims sharing the same `subject` tag but sitting in
  different tiers, as `NEEDS_RECONCILIATION` — a structural hint that two
  sources disagree, not a verdict on which one is right.

## What this does NOT do

- Fetch anything from the web or verify a claim's truth.
- Resolve a disagreement automatically.
- Replace a human's judgment about which source to trust.
- Detect claims in raw text (you supply the extracted claims).

It only checks that a claim's *stated* tier is internally consistent
with its *stated* evidence — a narrow, honest, mechanically-checkable
property.

## Usage

```
python3 claim_ledger.py example_claims.json
```

`example_claims.json` is a real worked example built from the citations
above, including a genuine tier conflict between two real claims about
what the actual fact-checking bottleneck is.

## Input format

```json
[
  {
    "claim_id": "unique-id",
    "text": "the claim itself",
    "classification": "VERIFIED_FACT | SUPPORTED_INFERENCE | UNVERIFIED_CLAIM | OPINION_OR_TREND",
    "confidence": "HIGH | MEDIUM | LOW",
    "source": "url or citation (required for VERIFIED_FACT / SUPPORTED_INFERENCE)",
    "subject": "optional free-text grouping key for conflict detection"
  }
]
```

## Requirements

Python 3.9+, standard library only. No network access, no dependency
on any other file in this repository — copy `claim_ledger.py` anywhere
and run it standalone.

## Tests

```
python3 -m unittest test_claim_ledger.py -v
```

14 tests, all passing as of 2026-08-27.

## Status (honest, not marketing)

- **FORGED**: yes, this file exists and runs.
- **TESTED**: yes, 14 unit tests pass, covering validation rules and
  conflict detection.
- **INSPECTABLE**: yes, single file, ~150 lines, no obfuscation.
- **REPRODUCIBLE**: yes, stdlib only, deterministic output for the same
  input.
- **RELEASED**: available in this public repository
  (`kyle4814/titanos`, `gems/claim_ledger/`).
- **ADOPTED**: no. No fact-checking organisation has used this. This
  status is not claimed anywhere else in this README.
- **IMPACT**: unknown. Not claimed.

## Limitations

- The classification/confidence vocabulary is intentionally small (4
  tiers) — a real newsroom's needs may require more nuance.
- Conflict detection is purely tier-based on a caller-supplied `subject`
  string; it does not understand claim semantics, so two claims about
  genuinely different things sharing a subject label by mistake would
  false-positive, and two conflicting claims given different subject
  labels would be missed entirely.
- No claim extraction from raw article/video text — that half of the
  practitioner-described bottleneck is explicitly out of scope here.

## Provenance

Built 2026-08-27 in the `cosmic-library` (TitanOS) repository, following
one real web search for current, evidenced fact-checking tooling
bottlenecks (sources above). Not derived from or dependent on any other
module in this repository — this is a standalone artifact placed in
`gems/` specifically so it can be copied out and used independently.
