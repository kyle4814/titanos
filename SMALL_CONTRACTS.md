# SMALL_CONTRACTS.md — the low-value / no-barrier band

**Sweep date:** 2026-09-02, one-off, read-only, via `foundation/mouth_common.py::fetch_feed()`
with fresh `DiscoveryPolicy` objects per source. No `.py` file was edited. No
state file owned by another mouth was written to. Full raw sweep output:
`/tmp/claude-1000/-home-tech2/7a233700-c5d0-42b0-a73b-54c78cec2146/scratchpad/sweep_results.json`.

**Sources swept:** UK Contracts Finder (`tender_radar.py`), UK Find a Tender
(`mouth_find_a_tender_uk.py`), NZ GETS (`mouth_gets_nz.py`), Ireland eTenders
(`mouth_etenders_ie.py`), TED (`mouth_ted.py`). All five reachable sources
named in the task brief were live-fetched; no source was skipped.

## THE HEADLINE FINDING, STATED HONESTLY

**No source produced a confirmed NO_BARRIER_STATED + genuinely sub-threshold
+ open + security-relevant hit this cycle.** That is a real result, not a
tooling failure — see the per-source detail below for why. The closest thing
to the target band is the NZ GETS list (36 candidates), and even there the
value and the barrier status are both structurally unobservable from the
feed itself — not "no barrier", but "the source does not say," which is a
different, weaker claim.

A second, load-bearing structural finding: **none of the five sources
combines all three of (a) a genuinely open/live notice, (b) a machine-
readable value figure, and (c) machine-readable bidder-criteria fields.**
TED is the only source with a criteria vocabulary at all
(`foundation/eligibility.py`), and TED by its own nature (EU-mandated
above-threshold publication) structurally cannot carry a sub-threshold
notice — the insight in the task brief (small contracts skip the
prequalification apparatus) is real, but the one source built to detect
that apparatus is also the one source that never sees a small contract.

---

## RANKED LIST

### Tier 1 — NZ GETS, security/IT-relevant, open, UNRESOLVED barrier (36 candidates, top 10 shown)

Source: `https://www.gets.govt.nz/ExternalRSSFeed.htm` (RSS, no key). 324
open NZ public-sector tenders/RFQs fetched; 36 matched a security/IT/audit
keyword filter against title+description+category text.

**Why UNRESOLVED, not NO_BARRIER_STATED:** confirmed structurally, not
guessed — `mouth_gets_nz.py`'s own module docstring and `foundation/
sources.py`'s "CRITICAL HONESTY RULE" both establish that this feed carries
**no selection-criteria, no exclusion-ground, no legal-form, no insurance,
no reference vocabulary at all** — the RSS envelope simply has no field for
any of it. That is evidence the criterion was never asked about in THIS
feed, not evidence no criterion exists on the actual RFx page behind the
link. GETS itself is a supplier portal — responding typically requires a
free GETS account (a soft platform-level barrier, not a corporate-scale
prequalification questionnaire) — this is a known characteristic of the
platform, not something verified per-listing this cycle. No value field
exists on this source at all (`money_state` is always `NOT_OBSERVED`), so
"below GBP/NZD X" cannot be asserted for any GETS item either — closing
dates only.

| Title | Buyer | Close date | Link |
|---|---|---|---|
| 322859 - Security Services | University of Waikato | 25 Sep 2026 5pm | https://www.gets.govt.nz//UW/ExternalTenderDetails.htm?id=34808478 |
| Corporate Security | Ministry of Education | 11 Sep 2026 4pm | https://www.gets.govt.nz//MEDU/ExternalTenderDetails.htm?id=34721345 |
| Identity Management Services | Statistics New Zealand | 16 Sep 2026 12pm | https://www.gets.govt.nz//SNZ/ExternalTenderDetails.htm?id=34705876 |
| Audit Services: Contract Procurement & Management | Otago Regional Council | 22 Sep 2026 4pm | https://www.gets.govt.nz//ORC/ExternalTenderDetails.htm?id=34782371 |
| 324523 - Enterprise CCTV Solution - Supply, Implementation, Migration and Support | University of Waikato | 25 Sep 2026 5pm | https://www.gets.govt.nz//UW/ExternalTenderDetails.htm?id=34809308 |
| Metro Network Safety Team | Environment Canterbury | 24 Sep 2026 5pm | https://www.gets.govt.nz//CRC/ExternalTenderDetails.htm?id=34751307 |
| RFT - Fire and Security Services Contractor for Site - Fire Alarm Remediation at Ōtaki School | Ministry of Education - School Infra | 11 Sep 2026 5pm | (see raw sweep file) |
| RFT - Fire and Security Services Contractor for Site - Fire Alarm Remediation at Fairfield | Ministry of Education - School Infra | 10 Sep 2026 5pm | (see raw sweep file) |
| Datacentre Co-location Services | New Zealand Police | 7 Sep 2026 3pm | (see raw sweep file) |
| Body-Worn Camera & Enterprise Digital Evidence Management System | New Zealand Police | 7 Sep 2026 9am | (see raw sweep file) |

Note: several of these (Police, large hospitals, university enterprise IT)
read as institutional-scale by buyer identity even though the source
carries no value figure — a solo operator's realistic shot is likely
concentrated in the smaller-council/school entries (Otago Regional
Council, Environment Canterbury, individual school fire-alarm jobs), not
the NZ Police/Statistics NZ/University enterprise items, but this is a
judgment call from buyer name, not a verified fact — full list of 36 is in
the raw sweep JSON.

### Tier 2 — UK Contracts Finder, the source built for this exact band — negative result, live

Source: `https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search`
(the one UK source with no minimum publication value and a real structured
`tender.value` field). Fetched the 100 most-recently-published releases:
**94 are `award`/`awardUpdate` (already decided, not open) and only 5 are
genuinely open** (`tender`-tagged, status `active`/`planning`):

| Title | Buyer/ref | Value | Security-relevant |
|---|---|---|---|
| CA18403 - RFQ 2026/32 - PR Agent for DTFF Celebration Event | — | £29,500 | No |
| CA18401 - Window Cleaning Service | — | £200,000 | No |
| Felix Batch 52 | — | £88,000 | No |
| Taxi and MPV (1-8 seats) Passenger Assistant (x2 near-duplicate entries) | — | not stated | No |

**Zero of the 5 currently open notices on this feed are security/IT-related.**
CA18403 (£29,500) is genuinely inside the sub-£30k target band and carries
no visible barrier language in the title, but it is a PR/events contract,
not security work — included for completeness of the sweep, not as a lead.
This is a real, live, honest negative result for the exact source the task
brief expected to be richest — this feed's page-1 window is simply
dominated by award notices right now, not by open sub-threshold RFQs, and
this module cannot paginate past page 1 (proven dead — see
`tender_radar.py`'s own CANNOT section; every filter/CPV/keyword parameter
on this endpoint is silently ignored, confirmed again this cycle).

### Tier 3 — Ireland eTenders — negative result, narrow window

Source: `https://www.etenders.gov.ie/epps/prepareCurrentOpportunities.do?currentType=cft`.
This endpoint is capped to the first 10 of 2,916 currently-open CFTs
(pagination, sorting and every filter parameter are proven silently
ignored — see `mouth_etenders_ie.py`'s own module docstring). All 10 items
in today's window:

| Title | Buyer | Est. value | Security-relevant |
|---|---|---|---|
| RFT — Scheme Climate Change Adaptation Plans, Package B | OPW | €836,000 | No |
| Non-Statutory Public Consultation Programme | OPW | not stated | No |
| Bespoke Multi-... Framework | Kildare/Wicklow ETB | €2,200,000 | No |
| Traffic and Transport Survey Resources Framework | National Transport Authority | €2,800,000 | No |
| South East Greenway – Lot 4 | Wexford County Council | not stated | No |
| Automatic Heat Sealer and Dual Lidder | Molaga Honey Ltd | €140,000 | No |
| New Dual Power Crusher | N and C Enterprises Ltd | €350,000 | No |
| Design and Project Management Services Framework | National Treatment Purchase Fund | €600,000 | No |
| Site Supervisory Services, Castletownbere Fishery Harbour | Dept. Agriculture Food and Marine | €170,000 | No |
| Electricity Supply Framework | Digital Manufacturing Ireland | €1,880,000 | No |

**Zero of the 10 visible notices are security/IT-related, and none is
genuinely below-threshold** (all stated values are well above small-quote
territory). This window is a snapshot of whatever the server's default
sort returns right now — it cannot confirm or deny that a below-threshold
security CFT exists elsewhere among the 2,916 open notices; that is a real
blind spot of this source, not a negative finding about Ireland's
procurement volume as a whole.

### Tier 4 — UK Find a Tender — structurally excluded from this band

Source: `https://www.find-tender.service.gov.uk/search/opportunities`
(CPV 79700000). 20 live items fetched, all real (Bradford penetration
testing, NHS England, UK Space Agency, Bluelight Commercial — see
`mouth_find_a_tender_uk.py`'s own module docstring for the full named
list). **FTS is the UK's ABOVE-threshold register by legal design** — a
notice only appears here because it crossed the England/Wales/NI
above-threshold value floor (roughly £123k–£663k depending on buyer type
and category). No item on this feed can be in the sub-threshold band by
construction; not re-listed here, included only to record that the
source was checked and correctly excluded.

### Tier 5 — TED — structurally excluded, and its own barrier fields came back UNKNOWN

Source: `https://api.ted.europa.eu/v3/notices/search`
(`classification-cpv IN (72000000, 79000000, 48000000, 72212730, 48730000,
72810000)`). 50 notices fetched, 30 carried a value; smallest real value
(excluding one nominal-€1 framework-agreement placeholder, see below):
**€200,000** (Netherlands, temp staff supply). TED is the EU's
above-EU-threshold register by legal design (thresholds €140k–€5.538m
depending on category/authority) — **no TED notice can be in the
sub-threshold band by construction**, confirming the task brief's own
premise rather than contradicting it.

A second check: fetched `foundation/eligibility.py`'s full criteria field
set (`selection-criterion-lot`, `exclusion-grounds`, `tenderer-legal-form-lot`,
...) for 15 of these notices and ran `assess_eligibility()` on each. **Every
one of the 15 came back `selection_criteria_used=None` and
`exclusion_grounds_used=None`** — TED's own structured API frequently does
not populate these fields even for large above-threshold notices, which
means `INSUFFICIENT_DATA` (unresolved), not `QUALIFIED` or a confirmed
absence of a barrier — see `foundation/qualification.py`'s own discipline,
reused rather than re-derived here. This is a genuine, separate finding
from the value-threshold one: even where TED could show a corporate-scale
barrier, its API frequently doesn't surface it in a machine-readable form,
so a human still has to open the actual procurement documents.

One data anomaly worth naming rather than hiding: publication-number
`401313-2026` (Provincie Flevoland, photo/video services framework
agreement) carries `total-value=1 EUR`. This is a real, live field value,
not a fetch error — but a €1 total value on a framework agreement is a
well-known TED convention for "no guaranteed minimum spend," not a real
€1 contract. Recorded here so it is not mistaken for a genuine low-value
lead.

---

## CLASSIFICATION SUMMARY

| Classification | Count | Where |
|---|---|---|
| NO_BARRIER_STATED (confirmed, structural) | 0 | none found this cycle |
| BARRIER_STATED (confirmed) | 0 | none checked this cycle carried a populated criteria field |
| UNRESOLVED | 36 | NZ GETS security/IT-relevant candidates — feed carries no criteria vocabulary at all, value never stated |
| Checked and excluded (not open / not relevant / not sub-threshold) | 20 (FTS) + 10 (IE) + 5 (UK CF) + 15 (TED eligibility sample) | see Tiers 2–5 |

## WHAT WOULD ACTUALLY CLOSE THE UNRESOLVED BAND

The single highest-leverage next step is not a new source — it's opening
a handful of the Tier 1 NZ GETS links by hand (or a future module reading
the full `ExternalTenderDetails.htm` page, not just the RSS envelope) to
read the RFx's own stated response requirements. The RSS feed structurally
cannot answer the question this task asks; the underlying HTML page it
links to might. That page fetch was not made this cycle — it is a new,
undeclared discovery objective distinct from the ones already authorized
for the RSS feed, and making it without a fresh `DiscoveryPolicy` naming
that specific objective would be exactly the kind of scope-creep this
repository's communication gate exists to prevent.
