# HUNT SWEEP — DEEP PASS, ALL FIVE SOURCES, CLASSIFIED

Run 2026-09-03. Every notice below was fetched live through the public
APIs `foundation/sources.py` already registers (TED, NZ_GETS,
UK_CONTRACTS_FINDER, UK_FIND_A_TENDER, ETENDERS_IE), consumed as-is —
no `.py` file modified. Every hit was passed through
`foundation/notice_class.py::classify_notice()`. No notice, count, or
classification below is fabricated; every UNKNOWN stayed UNKNOWN.

**Total scanned this sweep: 2,663 live notices across five sources.**
Of those, after removing classifier false positives (below), the real
count of MARKET_ENGAGEMENT + ROLLING_ADMISSION notices that are
genuinely **security-relevant** (cyber/ICT security, not physical
guarding, not CCTV, not payroll) is **4** — one MARKET_ENGAGEMENT, three
ROLLING_ADMISSION schemes. This is the honest headline: the barrier-free
class exists and was found, but it is small. The denominator matters
more than the numerator here.

---

## 1. Denominators — what was actually scanned, and how

| Source | Scanned | Method |
|---|---:|---|
| TED | 2,000 | 20 pages × limit=100 (the measured fields×limit ceiling — the 46-field eligibility+mouth union caps at 100, confirmed: page 20 returned a full 100-row page, `stop_reason=natural_end` at the self-imposed 20-page courtesy bound, not the server's own end) |
| NZ_GETS | 332 | full RSS feed, single fetch |
| UK_CONTRACTS_FINDER (tender stage) | 84 | `stages=tender`, one page (size=100, recency-windowed) |
| UK_CONTRACTS_FINDER (planning stage) | 27 | `stages=planning`, one page — see §3 for why this required bypassing `tender_radar.parse_items()` |
| UK_FIND_A_TENDER | 20 | one request only (CPV 79700000, page 1) — this source 429s hard; one request stayed inside the stated four-per-burst ceiling |
| ETENDERS_IE | 200 | 20 pages × 10 rows via the module's own `_fetch_pages()` (out of 2,916 total open CFTs platform-wide — this sweep saw 6.9% of what exists) |
| **Total** | **2,663** | |

Query used for TED, exactly as specified:
`deadline-receipt-request >= today() AND classification-cpv IN (72000000, 79000000, 48000000, 72212730, 48730000, 72810000)`.

One real failure, recorded honestly: the first `ETENDERS_IE` attempt
timed out on page 1 (`TimeoutError`, no HTTP response at all — a real
network condition, not a 429 or a block). Retried once, cleanly,
succeeded for all 20 pages. No fabricated substitute was used for the
failed attempt; it is simply not counted twice.

No User-Agent was ever spoofed. No block was encountered on any of the
five sources this cycle (unlike the AusTender/state-portal findings
already on record elsewhere in this repository).

---

## 2. Raw classifier output (before false-positive removal)

| Source | MARKET_ENGAGEMENT (raw) | ROLLING_ADMISSION (raw) | COMPETITIVE | UNKNOWN |
|---|---:|---:|---:|---:|
| TED | 8 | 325 | 11 | 1,656 |
| NZ_GETS | 29 | 8 | 90 | 205 |
| UK_CONTRACTS_FINDER (tender) | 0 | 0 | 84 | 0 |
| UK_CONTRACTS_FINDER (planning) | 27 | 0 | 0 | 0 |
| UK_FIND_A_TENDER | 9† | 0 | 0 | 11 |
| ETENDERS_IE | 0 | 5 | 51 | 144 |

† UK_FIND_A_TENDER's first classification pass (title+description only)
returned 0 MARKET_ENGAGEMENT hits and looked like a null result. It was
wrong: this source's own `status` field — a real, structured lifecycle
label ("Preliminary Market Engagement", "Active tender", "Planned
procurement") — was not being fed into `classify_notice()` as
`notice_type`. Re-run with `notice_type=status`, 9 of 20 notices
resolved correctly, including the exact notice
`notice_class.py`'s own docstring names (`UKRI-6251`). Recorded here
because it is a finding about running this sweep correctly, not about
the source: a classifier fed less than a source actually publishes will
under-report, silently, the same failure class this repo's sources
have already caught each other in.

---

## 3. A real gap found in `tender_radar.py`, not fixed (file territory)

`UK_CONTRACTS_FINDER`'s planning-stage feed (`stages=planning`) returned
27 real, live, `tag="planning"` / `tender.status="planned"` releases —
confirmed by reading the raw OCDS JSON directly. But
`tender_radar.parse_items()` hardcodes `_OPEN_TAG = "tender"` and drops
every release whose `tag` list does not contain the literal string
`"tender"` — so **all 27 planning-stage releases are silently discarded
by the module's own parser**, even when fetched from the URL
`planning_feed_url()` itself builds for exactly this purpose. Calling
`tender_radar.observe()`/`sweep()` against the planning feed today
returns zero items, always, regardless of what the server sent.

This sweep worked around it the only way file territory allows —
reading the raw OCDS payload and calling `classify_notice()` directly
on each release's own `tender.title`/`tender.description`/
`tender.status`, bypassing `parse_items()` entirely for this one path.
That is not a fix; it is documented here as a finding for whoever next
touches `tender_radar.py`: `planning_feed_url()` and `_OPEN_TAG` are
currently incompatible with each other.

---

## 4. Classifier false positives found and removed

**TED's 8 raw MARKET_ENGAGEMENT hits are all false positives.** Every
one matched the classifier's `market research` pattern against the
literal CPV category title *"Market research services"* — a service
buyers are procuring (ordinary COMPETITIVE tenders/frameworks to hire a
market-research firm), not a buyer conducting its own pre-tender market
engagement. Sample: `Ireland-Dublin: Market research services`
(85141-2022), `Finland-Veikkaus: Market research services`
(548638-2022). **Corrected TED MARKET_ENGAGEMENT count: 0.**

**A large share of TED's 325 ROLLING_ADMISSION "security" hits are also
false positives**, for a different reason: the CPV business-services
category name itself is *"Business services: law, marketing,
consulting, recruitment, printing and security"* — a fixed boilerplate
phrase. A DPS for e.g. "consultancy services in project management"
(Kolumbus AS, Norway) or "Interpretation Services" (Larvik kommune)
matches the word "security" only because it sits inside that category
title, never because the notice is about security at all. This is
exactly the CCTV/payroll overcounting the brief warned about, one
level removed. Real ROLLING_ADMISSION count (325) is genuine — every
one is a real, live DPS or Qualification System, verified by evidence
string (`DPS`/`Dynamic Purchasing System`/`Qualification System` all
appear literally in each title/procedure) — but the *security-relevant*
subset within it is much smaller than a naive keyword count would
suggest. See §5.

---

## 5. Every genuinely security-relevant MARKET_ENGAGEMENT / ROLLING_ADMISSION notice found

Four, after manual verification against the underlying notice text —
not four hundred, not forty. Reported honestly, with the denominator:
4 out of 2,663 scanned (0.15%).

### MARKET_ENGAGEMENT (1)

| Title | Buyer | Value | Deadline | Class | Source | Security? |
|---|---|---|---|---|---|---|
| UKRI-6251 Cyber Security – Managed Service and Detection Response & Security Operations Centre | UK Research and Innovation | not stated on this page | Preliminary Market Engagement (no deadline — nothing to fail) | MARKET_ENGAGEMENT | UK_FIND_A_TENDER | **Security-relevant** — explicit cyber security / SOC / detection & response scope, not adjacent |

URL: `https://www.find-tender.service.gov.uk/Notice/...` (title
uniquely identifies it in the FTS search results; this module does not
fetch the OCDS package for a resolvable permalink — see
`mouth_find_a_tender_uk.py`'s own CANNOT section).

### ROLLING_ADMISSION (3 distinct schemes, 5 raw notices — TED republishes/corrigenda the same scheme under multiple publication numbers)

| Title | Buyer | Deadline | Class | Source | Security? |
|---|---|---|---|---|---|
| Dynamic Purchasing System – Security Consultancy and Tests | Digitaliseringsdirektoratet (Norway) | 2028-06-28 | ROLLING_ADMISSION | TED | **Security-relevant** — "Tests" implies pen-test/security-testing consultancy, not physical guarding |
| 25P041 RTÉ Dynamic Purchasing System for Cyber Security Services | Raidió Teilifís Éireann (RTÉ, Ireland) | 2030-10-30 | ROLLING_ADMISSION | TED | **Security-relevant** — explicitly named "Cyber Security Services" |
| Dynamic Purchasing System for the Provision of Managed ICT Security Services | Asiera CLG (Ireland) | 2030-05-04 | ROLLING_ADMISSION | TED | **Security-relevant** — explicitly "Managed ICT Security Services" |

URLs (TED): `https://ted.europa.eu/en/notice/-/detail/379245-2024`,
`https://ted.europa.eu/en/notice/-/detail/384204-2024` (Digitaliserings-
direktoratet, two notices for the one scheme);
`https://ted.europa.eu/en/notice/-/detail/612163-2025` (RTÉ);
`https://ted.europa.eu/en/notice/-/detail/88846-2026`,
`https://ted.europa.eu/en/notice/-/detail/273460-2026` (Asiera CLG, two
notices for the one scheme).

One additional TED hit, **AS Vinmonopolet — "20-015 Security IT"**
(Norway, deadline 2028-05-24), is UNCERTAIN and deliberately excluded
from the count of 4: its own CPV category is "System quality assurance
planning services," not a security-services category, and the title
fragment "Security IT" alone is not enough evidence to assert cyber
relevance either way — recorded here as UNKNOWN-leaning rather than
silently dropped or silently counted.

---

## 6. Everything else found — real, but IT-adjacent or unrelated, not security

Reported so nothing is quietly folded into the security count.

**TED ROLLING_ADMISSION, non-security (320 of 325):** the large majority
are ordinary IT/software/business-services DPSes and Qualification
Systems matching the sweep's own CPV list (IT services, software,
computer auditing) with no security content at all — e.g. Hansel Oy
(Finland)'s "Turvallisuus- ja aulapalvelut" (security-guard-and-reception
DPS, physical only), Hansel Oy's "Turvallisuustekniikka, järjestelmät ja
laitteet" (CCTV/alarm hardware DPS — exactly the CCTV-as-security
overcount the brief named), Oslo kommune's manned-guarding DPS (×2,
physical), and a long tail of generic consulting/IT-supply DPSes run by
the European Commission, Registerenheten i Brønnøysund, and others.

**NZ_GETS MARKET_ENGAGEMENT, non-security (29 of 29):** all genuine RFI/
Advance-Notice/PIN/Market-Sounding notices — real, structural class
matches — but the subject matter is hospitals, roading, print services,
aircraft MRO, flood resilience, disability support, and similar. The two
closest to security are **"Body-Worn Camera & Enterprise Digital
Evidence Management System"** (NZ Police) and **"Request for
Information – Persistent Surveillance (Air) Phase 1"** (NZ Defence) —
both surveillance/evidence-management technology, not cyber security,
recorded as IT-adjacent.

**NZ_GETS ROLLING_ADMISSION, non-security (8 of 8):** supplier panels for
job advertising, payroll/ERP, construction, and a Marketplace standing
invitation. "Datacentre Co-location Services" (NZ Police) is
infrastructure-adjacent, not security.

**UK_CONTRACTS_FINDER planning-stage MARKET_ENGAGEMENT, non-security (26
of 27):** facilities management, curriculum design, energy/foreign-
currency, demolition, apprenticeship training, and Ministry of Defence
supply-chain notices for building trades (steel frame, underfloor
heating, rewiring). The one that reads security-adjacent, **"LBWF
Security Services Manned Guarding 2024"** (London Borough of Waltham
Forest), is physical manned guarding, not cyber — flagged, not counted.

**UK_FIND_A_TENDER MARKET_ENGAGEMENT, non-security (8 of 9):** lone-worker
devices, debt collection, an M&E framework, body-worn cameras, and a
generic "Security Services and Surveillance Solutions" notice
(SBS10547) whose own title reads as physical guarding/CCTV procurement,
not cyber. "NOE CPC Specialist Security Services & Nurse Call Systems"
is healthcare physical security, also not cyber.

**ETENDERS_IE ROLLING_ADMISSION, non-security (5 of 5):** website
development (DCU), EV charger installation (Bus Éireann), photography/
videography (TU Dublin), pressure-system filtering/metering (Gas
Networks Ireland), and non-destructive testing inspection (ESB) — none
IT or security relevant.

---

## 7. Method notes / what would change this count

- Every MARKET_ENGAGEMENT/ROLLING_ADMISSION hit above was checked
  against its own title and (where available) description text by
  hand, not accepted on the classifier's `evidence` string alone — the
  TED "Market research services" false positive was found exactly this
  way and would have inflated the headline count 9x if left unchecked.
- Security-relevance was judged by reading each notice's own scope
  text against a narrow, explicit sense of "security" (cyber, ICT
  security, penetration testing, SOC, detection & response) —
  deliberately excluding manned guarding, CCTV/alarm hardware, and
  general "business services...and security" CPV-category boilerplate,
  per this task's explicit instruction not to repeat the prior
  overcount.
- Absence of a MARKET_ENGAGEMENT/ROLLING_ADMISSION classification for a
  notice is never read as "this notice is COMPETITIVE" — see
  `notice_class.py`'s own UNKNOWN rule; 1,656 TED / 205 NZ_GETS / 144
  ETENDERS_IE notices in this sweep are UNKNOWN, not silently treated
  as ordinary tenders.
- Widening this sweep further: TED's own CPV-matched open-deadline
  population is 7,142 notices (per `hunt.py`'s own recorded
  measurement) — this sweep read 2,000 of them (28%). ETENDERS_IE has
  2,916 open CFTs platform-wide — this sweep read 200 (6.9%). Both
  could go deeper within the same courtesy bounds already coded
  (`MAX_PAGES_HARD_CAP=20` for TED paginated path, `MAX_PAGES=20` for
  ETENDERS_IE) by simply running more sweep cycles, not by changing any
  code.
