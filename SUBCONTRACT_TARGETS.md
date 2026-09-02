# SUBCONTRACT TARGETS
## Companies that won public-sector penetration-testing / security-testing contracts (subcontracting route)

Built 2026-09-02. Every row below traces to a real, named public procurement
notice — not a guess, not a marketing claim. This is the list of companies
who already have the paperwork (certifications, insurance, corporate
references) to win the contract, and therefore have a standing, recurring
need for people who can actually do the technical work.

## METHODOLOGY — read before using this list

**Source 1: EU TED (Tenders Electronic Daily), contract AWARD notices.**
Queried `api.ted.europa.eu/v3/notices/search` directly (POST, no key, CC BY
4.0) for `notice-type = "can-standard"` (a decided, awarded contract, not an
open tender) AND `publication-date >= today(-730)` (24 months) AND a
multilingual full-text clause matching: penetration test(ing), pentest(ing),
red team(ing), vulnerability assessment, ethical hacking, security audit,
cybersecurity audit, plus French/German/Dutch equivalents (`audit de
sécurité`, `test d'intrusion`, `Penetrationstest`, `beveiligingstest`).
198 award notices matched the full-text query; hand-checked each title +
description against the same keyword set a second time (client-side,
stricter) to drop false positives the server-side `FT ~` match let through
(a Siemens Mobility railway-signalling contract, two geotechnical-engineering
contracts, one environmental-services contract, one hardware-delivery
contract — all excluded, named here rather than silently dropped). Winner
name comes from TED's own `winner-name` field on the award notice. **65
notices survive with a real, non-empty winner name** — the table below.
17 further award notices matched the keyword search but published no
winner name at all (`winner-name` absent or a literal "Keine Angabe"/"None")
— TED itself did not disclose who won those; they are not fabricated here.

**Source 2: UK Contracts Finder (OCDS, OGL v3.0, no key).** The search API
has no CPV or keyword filter (confirmed by `foundation/tender_radar.py`'s
own prior finding — an unrecognised query parameter is silently accepted
and ignored, not honoured), so every UK award has to be pulled and
filtered client-side. **The endpoint rate-limits aggressively**: HTTP 429
after 2 pages (200 releases) with no delay, and even a 15s delay between
pages was insufficient; a 50s delay between pages was needed to sustain a
pull. Under that constraint, 800 of the most recent UK releases were
retrieved — covering **12 days** (2026-08-21 to 2026-09-01), not a
24-month window. Of those 800 (667 tagged `award`), **4 award-tagged
releases matched the keyword filter with a genuine named supplier**, plus
one `tenderAmendment` (a framework extension, not a fresh award — recorded
separately below). **This is an honest negative finding, not a failure to
try**: extending the UK pull to a real 24-month window at a rate that
avoids 429s would need on the order of 150+ sequential requests at 45-60s
apart (2+ hours) for a single pass — out of proportion to this task's
scope. The 12-day sample is real data, correctly labelled as a sample, not
presented as a full sweep.

**What "operates in English" means below**: either the company's own
careers site publishes in English (confirmed by direct search per company,
not assumed from country), or the company is headquartered in an
English-first jurisdiction (Ireland, UK).

**What this list is NOT**: not a claim that any of these companies is
hiring right now, not an endorsement, not verified to still be accurate
after publication (procurement award data ages). No outreach has been
attempted or drafted — this is a target list for a human to act on, not
an action taken.

---

## TIER 1 — REPEAT WINNERS (sustained, recurring demand)

Winning more than once in 24 months means the buyer relationship is
ongoing — the strongest signal of standing capacity need, not a one-off
project that's already fully staffed.

| Company | Country | Wins (24mo) | Notable buyers | Careers/entry path |
|---|---|---|---|---|
| **INFODAS GmbH** | Germany | 3 | Berliner Wasserbetriebe (x3, recurring framework) | [infodas.com/en/career](https://www.infodas.com/en/career/) — dedicated "Security Testing" role track. 50-year-old firm, cybersecurity consulting for German public administration/defence; also subcontracts to prime contractors (documented subcontractor role on a Diehl Defence/Bundeswehr order). |
| **Certitude Consulting GmbH** | Austria (working German buyers) | 2 | Techniker Krankenkasse (Germany, x2) | [certitude.consulting/career.html](https://certitude.consulting/career.html) — Vienna-based, cybersecurity-only consultancy; actively posts Senior Information Security Consultant / Software Security Consultant roles on LinkedIn. |
| **adesso SE** | Germany | 2 | German public-sector clients | [jobs.adesso-group.com](https://jobs.adesso-group.com/) — large German IT consultancy, dedicated cybersecurity/IT-Sicherheit job track (recognised "Germany's Best Employers in IT" x4). |
| **EY Consulting GmbH** | Germany | 2 | Sovereign Tech Agency GmbH (software security review framework) | Global firm — recruits through regional EY Careers portals; German entity contracted for open-source software security review work. |

---

## TIER 2 — NAMED WINNERS WITH A CONFIRMED, OPEN ENGLISH-LANGUAGE ENTRY PATH

Single award in the window, but a real careers page or open registration
route was independently confirmed (not assumed) for each.

| Company | Country | Award (buyer, value) | Entry path |
|---|---|---|---|
| **Secura B.V.** | Netherlands | Avans Hogeschool, €600,000 ([TED 218321-2025](https://ted.europa.eu/en/notice/-/detail/218321-2025)) | [secura.com/careers](https://www.secura.com/careers) — dedicated Penetration Tester + Penetration Testing Team Lead openings, Amsterdam/Eindhoven. Independent digital-security firm since 2000, explicit vulnerability assessment/pentest/red-team practice. |
| **Dionach** (by Nomios) | UK, worked a Danish award | Danske Spil A/S (Denmark), DKK 6,500,000 ([TED 528447-2025](https://ted.europa.eu/en/notice/-/detail/528447-2025)) | UK-headquartered (Oxford), ISO 27001/PCI QSA/CESG CHECK/CREST-certified; active "Penetration Tester (UK)" postings via Workable, "Graduate Hackademi" programme. |
| **mnemonic AS / mnemonic as** | Norway/Denmark | Norsk Tipping AS, NOK 8,000,000 ([TED 546065-2025](https://ted.europa.eu/en/notice/-/detail/546065-2025)); Danmarks Nationalbank, DKK 31,550,400 ([TED 124558-2026](https://ted.europa.eu/en/notice/-/detail/124558-2026)) — **two separate awards, different legal-entity capitalisation, not counted as Tier 1 repeat pending confirmation they're the same legal entity** | [careers.mnemonic.io](https://careers.mnemonic.io/) — 400+ staff, one of Europe's largest MDR/cybersecurity firms, regularly posts Penetration Tester (Application, Cloud) roles, English-language careers site. |
| **S2 Grupo Soluciones de Seguridad, S.L.** | Spain | European Union Agency for the Space Programme, €2,550,000 ([TED 417280-2025](https://ted.europa.eu/en/notice/-/detail/417280-2025)) — "Penetration Testing Support Services", EU-agency buyer | [talento.s2grupo.es](https://talento.s2grupo.es/) — 550+ cybersecurity specialists, active job board. |
| **AWARE7 GmbH** (and "Bieter 14 - Aware7 GmbH") | Germany | Landkreis Harz, €32,558.40 ([TED 299760-2026](https://ted.europa.eu/en/notice/-/detail/299760-2026)); Berliner Wasserbetriebe ([TED 409998-2026](https://ted.europa.eu/en/notice/-/detail/409998-2026)) — **2 awards, likely Tier-1-eligible but named inconsistently across notices ("Bieter 14 - Aware7 GmbH" vs "AWARE7 GmbH"), so not merged without confirming it's one legal entity** | [aware7.com/career](https://aware7.com/career/) / [a7.de/karriere](https://a7.de/karriere/) — Gelsenkirchen, ~30 staff, explicitly welcomes "initiative applications, especially from experienced pentesters," pays for OSCP/CEH/CISM certification. |
| **Knowit Cybersecurity & Law AB** | Sweden | Försäkringskassan, SEK 36,762,000 ([TED 139846-2025](https://ted.europa.eu/en/notice/-/detail/139846-2025)) — "Penetrationstester 2025" | [knowit.eu](https://www.knowit.eu/what-we-offer/cybersecurity-law/) — Nordic-region cybersecurity supplier, ~12-specialist offensive-security team, English-language site. |
| **YesWeHack** | France (Belgium award) | European Commission DG, €7,679,875 ([TED 397463-2025](https://ted.europa.eu/en/notice/-/detail/397463-2025)) — "Bug Bounty security related services" | [yeswehack.com/researchers/start-hunting](https://www.yeswehack.com/researchers/start-hunting) — **open registration, no certification required**; 135,000+ researcher community; won an EU-institution bug-bounty contract directly, meaning EC-scoped bounty work is reachable via ordinary hunter sign-up, not a subcontract negotiation. |
| **Intigriti** | Belgium | Shield VZW ([TED 360284-2025](https://ted.europa.eu/en/notice/-/detail/360284-2025), €45,000,000 — appears to be a multi-year framework ceiling, not one project's value) | [intigriti.com/researchers](https://www.intigriti.com/researchers) — same open-registration model as YesWeHack, 150,000+ researchers. |

---

## TIER 3 — ALL OTHER NAMED TED WINNERS (single award, 24-month window)

Full list for completeness — repeat winners and Tier-2 entries above are
not duplicated here. Values are TED's own published figures; a value of
`0.01`, `1`, or `-1` (currency) is TED's own placeholder for "value not
disclosed by the buyer," not a real contract size — carried through
honestly rather than hidden, per the same discipline `foundation/
mouth_ted.py` already documents for open-notice values.

| Company | Country | Buyer | Value | Award date | Source |
|---|---|---|---|---|---|
| GAI NetConsult | DE | NRW.BANK AöR | not disclosed | 2024-10-01 | [590453-2024](https://ted.europa.eu/en/notice/-/detail/590453-2024) |
| Solita Oy | FI | Valtioneuvoston kanslia | €304,000 | 2024-10-07 | [600254-2024](https://ted.europa.eu/en/notice/-/detail/600254-2024) |
| UAB "Baltic Amadeus" | LT | Finansų ministerija | €65,000 | 2024-10-21 | [636937-2024](https://ted.europa.eu/en/notice/-/detail/636937-2024) |
| Minana International T/A GoodPeople | IE | Dept. Children, Equality, Disability | €6,000,000 | 2024-11-07 | [678770-2024](https://ted.europa.eu/en/notice/-/detail/678770-2024) |
| CCVOSSEL GmbH | DE | Kassenzahnärztliche Vereinigung WL | not disclosed | 2024-11-28 | [726245-2024](https://ted.europa.eu/en/notice/-/detail/726245-2024) |
| ProSec GmbH | DE | Klinikum Hochsauerland GmbH | not disclosed | 2024-12-04 | [739350-2024](https://ted.europa.eu/en/notice/-/detail/739350-2024) |
| CGI Deutschland B.V. & Co. KG | DE | Berliner Wasserbetriebe | not disclosed | 2024-12-10 | [754390-2024](https://ted.europa.eu/en/notice/-/detail/754390-2024) |
| APASEC Consulting | DE | Messe Berlin GmbH | not disclosed | 2024-12-10 | [754638-2024](https://ted.europa.eu/en/notice/-/detail/754638-2024) |
| FR_KYOS SA | CH | Ville de Lausanne | CHF 1,157,518 | 2024-12-18 | [777456-2024](https://ted.europa.eu/en/notice/-/detail/777456-2024) |
| Sopra Steria Nederland B.V. | NL | Autoriteit Financiële Markten | €650,000 | 2025-02-28 | [134280-2025](https://ted.europa.eu/en/notice/-/detail/134280-2025) |
| PricewaterhouseCoopers Advisory N.V. | NL | Stichting ICTU | €1,320,000 | 2025-03-18 | [173516-2025](https://ted.europa.eu/en/notice/-/detail/173516-2025) |
| IlionX Group B.V. | NL | Nationale ombudsman | €415,000 | 2025-03-20 | [180839-2025](https://ted.europa.eu/en/notice/-/detail/180839-2025) |
| BearingPoint GmbH | DE | Land Baden-Württemberg | not disclosed | 2025-04-29 | [276172-2025](https://ted.europa.eu/en/notice/-/detail/276172-2025) |
| S.C. Deloitte Consultanta S.R.L. | RO | Banca Nationala a Romaniei | €217,974 | 2025-04-30 | [280327-2025](https://ted.europa.eu/en/notice/-/detail/280327-2025) |
| EY Advisory Oy | FI | Valtioneuvoston kanslia | €304,000 | 2025-05-13 | [303523-2025](https://ted.europa.eu/en/notice/-/detail/303523-2025) |
| Secora Consulting | IE | Teagasc | €80,000 | 2025-07-18 | [472495-2025](https://ted.europa.eu/en/notice/-/detail/472495-2025) |
| Conscia Sverige AB | SE | Region Skåne / Skånetrafiken | SEK 15,000,000 | 2025-07-21 | [475760-2025](https://ted.europa.eu/en/notice/-/detail/475760-2025) |
| TÜV Informationstechnik GmbH | DE | Stadt Solingen | €146,600 | 2025-08-06 | [514105-2025](https://ted.europa.eu/en/notice/-/detail/514105-2025) |
| CRONOS Public Services | BE | Stad Brugge | €192,000,000 (multi-year framework) | 2025-09-01 | [566833-2025](https://ted.europa.eu/en/notice/-/detail/566833-2025) |
| PricewaterhouseCoopers Enterprise Advisory | BE | SNCB | €600,000 | 2025-09-04 | [578189-2025](https://ted.europa.eu/en/notice/-/detail/578189-2025) |
| SmartTECS Cyber Security GmbH | DE | civillent GmbH | not disclosed | 2025-09-24 | [624967-2025](https://ted.europa.eu/en/notice/-/detail/624967-2025) |
| usd AG | DE | Land Hessen | €8,447,760 | 2025-10-21 | [693873-2025](https://ted.europa.eu/en/notice/-/detail/693873-2025) |
| Cipherbit S.L.U. | ES | Dirección General de la Entidad Pública | €206,080.48 | 2025-11-12 | [750858-2025](https://ted.europa.eu/en/notice/-/detail/750858-2025) |
| OPPIDA | FR | AFNIC | €500,000 | 2025-11-14 | [754891-2025](https://ted.europa.eu/en/notice/-/detail/754891-2025) |
| welldone cloud mk e.U. | AT | Österreichischer Rundfunk | €2,520,000 (likely framework ceiling) | 2025-11-14 | [755833-2025](https://ted.europa.eu/en/notice/-/detail/755833-2025) |
| Orange Cyberdefense Netherlands B.V. | NL | Kadaster | not disclosed | 2025-12-03 | [802182-2025](https://ted.europa.eu/en/notice/-/detail/802182-2025) |
| KPMG AS (Hovedenhet) | NO | Norsk rikskringkasting AS | NOK 500,000 | 2026-01-21 | [44963-2026](https://ted.europa.eu/en/notice/-/detail/44963-2026) |
| UAB Solutionlab Production | EE | Eesti Energia AS | €6,000 | 2026-01-28 | [62687-2026](https://ted.europa.eu/en/notice/-/detail/62687-2026) |
| AIUKEN Solutions S.L.U | ES | Gobierno de La Rioja | €381,340 | 2026-02-17 | [112124-2026](https://ted.europa.eu/en/notice/-/detail/112124-2026) |
| Innovative Datensysteme GmbH indasys | DE | EnBW Energie Baden-Württemberg AG | not disclosed | 2026-02-24 | [129654-2026](https://ted.europa.eu/en/notice/-/detail/129654-2026) |
| PRAGMA Computers S.R.L. | RO | Direcția Generală de Protecție Internă | RON 6,083,317 | 2026-03-16 | [179127-2026](https://ted.europa.eu/en/notice/-/detail/179127-2026) |
| mgm security partners GmbH | DE | Bundesagentur für Arbeit | not disclosed | 2026-03-30 | [216889-2026](https://ted.europa.eu/en/notice/-/detail/216889-2026) |
| T.A.I. Software Solution S.R.L. | IT | Soggetto Aggregatore Regione Toscana | €11,172,582.96 | 2026-04-13 | [249563-2026](https://ted.europa.eu/en/notice/-/detail/249563-2026) |
| Gofore Finland Oy | FI | Business Finland Oy | €690,000 | 2026-04-16 | [260117-2026](https://ted.europa.eu/en/notice/-/detail/260117-2026) |
| Dataeye Consulting | RO | Compania Nationala de Cai Ferate "CFR" | RON 239,000 | 2026-05-07 | [314532-2026](https://ted.europa.eu/en/notice/-/detail/314532-2026) |
| Research Industrial Systems Engineering RISE GmbH | DE | Bundesrepublik Deutschland | €1,215,126.05 | 2026-06-16 | [411673-2026](https://ted.europa.eu/en/notice/-/detail/411673-2026) |
| HiSolutions AG | DE | DAK-Gesundheit | €500,000 | 2026-06-25 | [433915-2026](https://ted.europa.eu/en/notice/-/detail/433915-2026) |
| Dizparc Secured AB | SE | Statistiska Centralbyrån | SEK 3,400,000 | 2026-07-02 | [455869-2026](https://ted.europa.eu/en/notice/-/detail/455869-2026) |
| FR_Oneconsult AG | CH | Swissgrid AG | CHF 26,921,224 | 2026-07-24 | [512623-2026](https://ted.europa.eu/en/notice/-/detail/512623-2026) |
| Badger Systems GmbH | DE | Sovereign Tech Agency GmbH | €2,040,000 | 2026-08-19 | [573395-2026](https://ted.europa.eu/en/notice/-/detail/573395-2026) |
| Ada Logics Ltd | DE (working via German buyer) | Sovereign Tech Agency GmbH | €2,715,000 | 2026-08-19 | [573607-2026](https://ted.europa.eu/en/notice/-/detail/573607-2026) |
| ACT Digital Deutschland GmbH | DE | gematik GmbH | €2,497,000 | 2026-08-19 | [574636-2026](https://ted.europa.eu/en/notice/-/detail/574636-2026) |
| Liquid Reply GmbH | DE | Sovereign Tech Agency GmbH | €1,805,000 | 2026-08-19 | [575190-2026](https://ted.europa.eu/en/notice/-/detail/575190-2026) |
| Tweede Golf BV | DE (working via German buyer) | Sovereign Tech Agency GmbH | €905,000 | 2026-08-20 | [577232-2026](https://ted.europa.eu/en/notice/-/detail/577232-2026) |
| IAV GmbH | DE | Sovereign Tech Agency GmbH | €905,000 | 2026-08-20 | [578108-2026](https://ted.europa.eu/en/notice/-/detail/578108-2026) |

**Note on the "Sovereign Tech Agency GmbH" cluster (7 entries above):**
these are open-source software security engineering/audit framework
awards, not classic black-box penetration testing — grouped honestly
under the security-testing keyword match rather than re-labelled as
something they're not. Genuine, recurring demand for security-focused
software engineers, just a different work shape than a pentest engagement.

---

## UK CONTRACTS FINDER — direct awards (12-day sample, 2026-08-21 to 2026-09-01)

| Company | Buyer | Value | Award date | Source |
|---|---|---|---|---|
| **Salus Digital Security Limited** | Intellectual Property Office | £1,337,500 | 2026-08-27 | "Provision of IT Penetration Testing (NCSC CHECK)", [Contracts Finder OCDS release 747e0208-...](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/747e0208-e6d0-470a-8299-e756de657547-912272) |
| **Layer 7 Limited** | NS&I | £62,500 | 2026-08-26 | "IT Health Checks", [OCDS release f027760c-...](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/f027760c-6b1d-4fec-a5d0-8094ea503ce0-912120) |
| **NCC Group Security Services Limited** | DSIT (Dept. for Science, Innovation & Technology) | £21,125 | 2026-08-25 | "GovAssure Independent Audit for One Login", [OCDS release 2b828d25-...](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/2b828d25-4766-4d07-8962-1937e8cf894a-912053) |
| **Qinetiq UK Ltd** | Home Office | £28,000 | 2026-08-25 | "DVI ITHC Testing", [OCDS release 23f4d912-...](https://www.contractsfinder.service.gov.uk/Published/Notice/OCDS/23f4d912-6c48-40b8-9c5c-3c8f0934597c-911916) |

**NCC Group** and **QinetiQ** are large, well-known UK cybersecurity/defence
firms with public careers sites — worth checking directly
([careers.nccgroup.com](https://careers.nccgroup.com/), [qinetiq.com/careers](https://www.qinetiq.com/en/careers)).
**Salus Digital Security** and **Layer 7 Limited** are smaller, specialist
UK pentest firms — the size of win here (£1.3M and £62.5K respectively)
suggests genuine capacity need at the smaller end, where a solo
subcontractor is more likely to be useful than at NCC/QinetiQ scale.

**The standing UK route worth knowing about even without a fresh award**:
**Crown Commercial Service's "Cyber Security Services 3" Dynamic Purchasing
System** (RM3764.iii, extended to 2029, £800M estimated total value across
its lifetime) is the umbrella vehicle almost all UK central-government
cyber-services spend — including penetration testing — flows through.
Suppliers already on this DPS are the pool that gets invited to bid on
individual call-offs; this notice itself names the DPS, not a single
winner ([Contracts Finder search for "Cyber Security Services 3"](https://www.contractsfinder.service.gov.uk/Search/Results?Keywords=Cyber%20Security%20Services%203)).
Finding the current supplier roster on this DPS (a public, searchable list)
is the highest-leverage next UK-specific research step — every firm on it
has already cleared the certification/insurance/reference bar this
operator cannot clear directly, and by definition needs delivery capacity
to fulfil call-offs.

---

## RANKING SUMMARY — who to approach first

1. **INFODAS GmbH** (3 wins) — largest, most consistent recurring German
   public-sector pentest/security-testing buyer relationship in this data.
2. **AWARE7 GmbH** (2 wins under related names, small team, explicit
   "welcomes initiative applications from experienced pentesters") —
   smallest team of any repeat winner, most plausible entry point for a
   solo operator specifically (large firms subcontract less per-head).
3. **Certitude Consulting GmbH** (2 wins, security-only boutique, Vienna).
4. **Dionach** (UK-headquartered, English-native, CREST-certified, active
   external hiring, cross-border Danish award proves willingness to staff
   outside home country).
5. **Secura B.V.** (Netherlands, English careers site, explicit pentest
   team-lead + tester openings).
6. **YesWeHack / Intigriti** — not subcontracting in the traditional
   sense, but the only two entries on this list with **zero-friction,
   no-certification-required entry** (sign up, start hunting); both hold
   real EU public-sector bug-bounty contracts, so EU-institution-scoped
   bounty work is reachable today, not hypothetically.
7. **Salus Digital Security Limited / Layer 7 Limited** (UK) — small firms,
   recent single UK CHECK-scheme awards; worth checking for CHECK Team
   Member (non-lead) routes, which have a lower bar than full CHECK Team
   Leader status.

## LIMITATIONS (stated honestly, not hidden)

- TED coverage is 24 months, EU + EEA/UK-adjacent (CH, NO). UK coverage is
  a 12-day sample only, due to Contracts Finder's aggressive rate limiting
  (429 after 2 unthrottled pages; sustainable only at ~50s/request).
- No Australian, US, or non-European award data — out of scope for this
  pass; TED/Contracts Finder were the two sources this task named.
- A company appearing once is not proven to be a "target" — some single
  awards are large one-off framework ceilings (e.g. CRONOS Public
  Services' €192M, Intigriti's €45M) that may already be fully staffed
  internally; some are tiny (UAB Solutionlab Production, €6,000) and may
  not need external capacity at all. Company size and the specific award
  size were both left in the table for the operator's own judgment call,
  not pre-filtered out.
- No individual person's name, personal email, or personal phone number
  was collected anywhere in this file — every identifier above is a
  company/legal-entity name, matching the task's own rule.
- No outreach was drafted or attempted. This file is research only.
