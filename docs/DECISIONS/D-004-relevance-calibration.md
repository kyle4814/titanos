# D-004 — Relevance scorer calibration against real TED data

STATUS: DECISION RECORDED — SCORER NOT FIT FOR USE AS CALIBRATED. `foundation/shortlist.py` NOT BUILT.
AGENT: ENGINEER B, TITANOS cycle 007
DATE: 2026-09-01

## THE QUESTION

`foundation/relevance.py` has 16 passing tests, all against synthetic
notices written by the same author as the scorer. The claim "it can rank
tenders for you" rests entirely on it discriminating against real,
independently-authored text. This cycle pulled a real live sample from
EU TED via `foundation/mouth_ted.py`, built a realistic
`CapabilityProfile` for a cyber-security/IT-consulting operator, scored
the sample, and read the actual titles to judge whether the bands are
sane. Neither `foundation/relevance.py` nor `foundation/mouth_ted.py`
was modified — this cycle reports defects in both rather than fixing
them, per the owning boundary for this task.

## THE SAMPLE

`mouth_ted.sweep()` run live, no injected `fetch_fn`, real network call
through `foundation/mouth_common.fetch_feed()` under `mouth_ted`'s own
`DISCOVERY_POLICY` (`requested_scope="READ_API"`). Result:
`status=FIRST_SEEN fetched=250 signals=250`, **250 unique
publication-numbers** (no duplicate `signal_id`s), CPV family
72000000/79000000/48000000, deadline in the future at query time.
Genuinely live, current EU procurement notices — not a fixture.

## THE PROFILE

```
CapabilityProfile(
    name="cyber-security-operator",
    keywords={cyber security, cybersecurity, penetration testing, pentest,
              security audit, incident response, soc,
              security operations centre, it consulting,
              software development, information security,
              vulnerability assessment, network security},
    cpv_codes={72000000, 79000000},
    exclusions={construction, catering, cleaning, vehicles,
                medical supplies, ambulance},
)
```

## RUN 1 — PROFILE WITH CPV CODES DECLARED (the realistic operator profile)

**Band distribution (n=250):**

```
STRONG_MATCH  241  (96.4%)
EXCLUDED        9  (3.6%)
POSSIBLE        0
WEAK            0
UNKNOWN         0
```

**Failure mode confirmed: everything lands in one band.** 96% of a real,
mixed sample collapsed into the top band. Reading the actual titles that
landed `STRONG_MATCH`:

- `Norway-Oslo: IT services: consulting, software development, Internet and support`
- `United Kingdom-Wakefield: Telematics services`
- `Netherlands-Utrecht: Software package and information systems`
- `Denmark-Kongens Lyngby: Wide area network services`
- `Netherlands-The Hague: Economic research services`
- `Lithuania-Vilnius: Railway traffic control software development services`
- `Netherlands-Etten-Leur: Supply services of personnel including temporary staff` (55 occurrences)
- `Norway-Oslo: Recruitment services`

None of these mention penetration testing, incident response, SOC, or
security audit — the operator's actual declared capabilities. A
temp-staffing framework agreement, a telematics contract, and a railway
signalling software contract scored identically to the top band as a
genuine cyber-security engagement would. **This is the "obviously
irrelevant notices score high" failure mode, confirmed by direct human
read of titles, not inferred from counts alone.**

### ROOT CAUSE — traced, not guessed

`relevance.score()` awards `STRONG_MATCH` unconditionally on ANY CPV
code match (`matched_cpv or distinct_count >= STRONG_MIN_DISTINCT`),
bypassing the distinct-keyword-diversity requirement entirely when a CPV
code matches. Investigated why CPV codes matched on notices whose titles
never mention IT or security at all (e.g. "Telematics services",
"Supply services of personnel"):

`relevance._searchable_text()` includes `signal.source_ref`.
`mouth_ted.ted_signal()` sets `source_ref` to:

```
https://api.ted.europa.eu/v3/notices/search query='deadline-receipt-request
>= today() AND classification-cpv IN (72000000, 79000000, 48000000)'
```

**This string is identical for every signal `mouth_ted` ever produces** —
it is the fetch query, not a per-notice fact. A `CapabilityProfile`
declaring any CPV code that overlaps the mouth's own query filter (a
near-certainty, since a real operator profile in IT/security would
naturally declare 72000000/79000000-family codes, the exact family
`mouth_ted.EXPERT_QUERY` already filters on) will match on **100% of
signals from that mouth**, regardless of what the individual notice is
actually about. The scorer is not reading the notice's declared CPV
classification at all — `mouth_ted`'s `REQUEST_FIELDS` never requests
`classification-cpv` back, and no CPV code is stored anywhere in the
signal's `facts`/`evidence`. The CPV match is firing against the
fetcher's own query string leaking into `source_ref`, which
`relevance.py` treats as searchable notice text. This is a structural,
guaranteed false-positive for any TED-sourced signal, not an edge case.

## RUN 2 — KEYWORDS ONLY, NO CPV CODES (control, to isolate the text-matching path)

**Band distribution (n=250):**

```
WEAK          226  (90.4%)
POSSIBLE       15  (6.0%)
STRONG_MATCH    0
EXCLUDED        9  (3.6%)
UNKNOWN         0
```

**Failure mode confirmed: STRONG_MATCH is structurally empty.** With the
CPV shortcut removed, no notice in the real sample ever reaches
`STRONG_MIN_DISTINCT = 3` distinct keyword hits. All 15 `POSSIBLE` items
matched on exactly one keyword (`software development`).

### ROOT CAUSE — traced against the actual live payload

Fetched the raw TED response and inspected it directly:
**0 of 250 notices had any populated `description-proc` or
`description-lot`** in this live sample — `mouth_ted.parse_items()`
correctly reports this as `description=""` (per its own documented CANNOT
scope), so every signal's searchable text is reduced to a short title
plus buyer name. Worse, titles are frequently just the CPV umbrella
category label duplicated across dozens of unrelated buyers, not a
description of the specific work:

```
55x  "Netherlands-Etten-Leur: Supply services of personnel including temporary staff"
34x  "Netherlands-Veghel: Supply services of personnel including temporary staff"
 8x  "Netherlands-Eindhoven: Supply services of personnel including temporary staff"
```

Against text this thin (a handful of words, mostly buyer name + CPV
umbrella label), no genuinely relevant notice can ever surface 3 distinct
profile keywords — `STRONG_MIN_DISTINCT = 3` is unreachable by
construction, not merely "tuned too tight for this sample." This is a
`mouth_ted` data-quality finding as much as a `relevance.py` calibration
finding: the parser is honest about what it received (`description=""`,
not fabricated), but what TED's API actually returned for this
CPV/date window carries almost no distinguishing free text to score
against.

## FAILURE MODES — DISPOSITION AGAINST THE BRIEF'S OWN LIST

| Failure mode named in the brief | Occurred? | Evidence |
|---|---|---|
| Everything lands in one band | **YES** (Run 1) | 96.4% STRONG_MATCH |
| STRONG_MATCH empty despite obviously relevant content | **YES** (Run 2) | 0/250, thin real text can't reach `STRONG_MIN_DISTINCT` |
| Obviously irrelevant notices score POSSIBLE+ | **YES** (Run 1) | Telematics, personnel-supply, railway-signalling all `STRONG_MATCH` |
| CPV path never fires on real data | **NO — inverse problem** | It fires on **100%** of TED signals, via a leaked query string, not the notice's real classification |

Three of the four named failure modes occurred, plus a fifth,
more specific one the brief didn't anticipate: the CPV evidence path
in `relevance.py`, combined with `mouth_ted.py`'s choice to put the
literal query string in every `source_ref`, produces a false "exact code
match" on every single item from this source — the single strongest
evidence category the scorer has (a code match is explicitly documented
as unfakeable by keyword stuffing) is unconditionally correct and
therefore worthless for this mouth.

## VERDICT

**NOT FIT FOR USE**, as currently calibrated, against real live TED
data, for an IT/security operator profile. Two independent, compounding
defects, in two different owned files:

1. `foundation/relevance.py` (defect, not fixed here — out of scope for
   this cycle's ownership): `score()` treats any CPV code match as
   sufficient alone for `STRONG_MATCH`, with no corroborating
   distinct-keyword requirement. Combined with `_searchable_text()`
   including `source_ref`, this is exploitable (accidentally, in this
   case, not adversarially) by any upstream source whose `source_ref`
   is a constant string containing codes the profile also declares.
2. `foundation/mouth_ted.py` (defect, not fixed here): 0/250 real
   notices in this sample carried any populated description text, and
   title text is frequently a duplicated CPV-umbrella label rather than
   a specific description of the work — the raw material the scorer
   needs to discriminate on free text essentially isn't there for a
   large fraction of real TED notices in this CPV/date window.

Both defects are real, evidenced against a live 250-notice sample, and
neither is a synthetic-test artifact. Per the brief: **`foundation/
shortlist.py` is NOT built this cycle.** Building a ranked shortlist on
top of a scorer that either rubber-stamps 96% of input as top-tier or
structurally cannot reach top-tier at all would hand an operator a
list that looks authoritative and is not — worse than no tool, per this
repository's own standing value discipline (a relevance band is not a
qualification, but a band that doesn't discriminate is not even
relevance).

## NEXT ACTION (not taken this cycle — reported for whoever owns these files)

- `relevance.py`: require CPV match AND at least 1 distinct keyword hit
  (or drop `source_ref` from `_searchable_text()`, which independently
  removes the leaked-query-string false positive) before granting
  `STRONG_MATCH` from a CPV match alone.
- `mouth_ted.py`: investigate why `description-proc`/`description-lot`
  were empty for 100% of this live sample — check whether requesting
  additional fields (e.g. `description-lot` variants, or a different
  `fields` parameter shape) surfaces real text, since the module's own
  docstring recorded seeing populated descriptions in earlier
  ad-hoc probing (publication-number 533561-2026, 533775-2026) that this
  cycle's 250-notice pull did not reproduce at scale.
- Once either or both are fixed, re-run this exact calibration
  (same profile, a fresh live pull) before concluding the scorer is fit
  for use — this decision does not need to be re-derived from scratch,
  only re-run.
