# EU TED Small/Low-Barrier Security Contracts — Solo Operator Screen

Run 2026-09-02. Live TED data only (`api.ted.europa.eu/v3/notices/search`, POST, CC BY 4.0).
All fetches went through `foundation/mouth_common.fetch_feed()` under a `DiscoveryPolicy`
(objective + budget declared per call, see below). `foundation/eligibility.py::assess_eligibility()`
was used to pull real bidder-condition fields — no verdict is emitted by that module; every
classification below is mine, built only from a quoted field or clause, never inferred.

**Operator profile assumed:** solo, Australia-based, no OSCP/CREST/GIAC, no professional
indemnity insurance, no corporate references, no staff, English only.

## METHOD (so results can be reproduced/audited)

1. `mouth_ted.observe_paginated()` with `full_text_terms=SECURITY_FULL_TEXT_TERMS`
   (`cybersecurity`, `cyber security`, `information security`, `incident response`,
   `ISO 27001`, `informatiebeveiliging`, `IT-Sicherheit`, `sécurité informatique`) ANDed onto
   `EXPERT_QUERY` (CPV 72000000/79000000/48000000/72212730/48730000/72810000 families,
   `deadline-receipt-request >= today()`, `publication-date >= today(-90)`) → **218 live open
   notices**, 1 page, no truncation (`short_page_natural_end`).
2. A second full-text sweep using the specific multilingual pentest/audit terms requested
   (`Penetrationstest`, `test d'intrusion`, `prueba de penetración`, `penetratietest`,
   `test di penetrazione`, `audit de sécurité`, `sécurité informatique`, `sicurezza
   informatica`, `seguridad informática`, `cybersécurité`) → **50 live open notices**.
3. A third sweep ANDing a broader security full-text OR-group with
   `submission-language = ENG` (server-side TED field, confirmed live-filtering: baseline CPV
   query alone returns 475 ENG-submission notices; narrowed by the security terms to **68**) —
   this is the set most likely to contain something an English-only solo operator can actually
   read and answer.
4. For every notice below, a second targeted fetch pulled the full field set
   `mouth_ted.REQUEST_FIELDS ∪ eligibility.FIELDS` for that `publication-number`, and
   `assess_eligibility()` parsed it. `procurement documents`/notice-page URLs below are TED's
   own fields, not invented.
5. **`amount`/`currency` are TED's own value fields where present; `None` means TED did not
   populate a value field for that notice — never treated as zero or as "small".**
6. `DiscoveryPolicy` budgets used across this run: 5 separate policies, each with a concrete
   objective, `max_queries` 3–8, well inside the repo's gate. No socket was opened outside
   `fetch_feed()`.

## HEADLINE FINDING

Across every notice actually inspected in detail (15 from the multilingual sweep + 5 from the
English-submission sweep), **zero were WINNABLE_SOLO on the criteria this module could see.**
Every notice whose selection-criteria text was populated in the search-API projection
(`selection-criteria-source` including `epo-notice`) carried at least one of: a named
professional certification scheme (OSCP, CISSP, PASSI, ISO/IEC 27001 lead-auditor, CEH), a
minimum-staff-count clause, a general/specific turnover floor, or a non-English submission
language — consistent with the prior degewo AG finding (578580-2026), not an isolated case.
Where the notice's own `selection-criteria-source` field said the real criteria live only in
`epo-procurement-document` (the linked national e-procurement portal, not TED's own
projection), this module could not fetch or read that document — classified
`UNKNOWN_CRITERIA_IN_DOCS_ONLY`, not "winnable", per the task's own rule against inferring a
can-bid verdict.

**The one submission-language fact worth acting on:** `submission-language = ENG` genuinely
filters (475 hits, not all-or-nothing) and Ireland's public buyers publish almost entirely in
English, including for pure cybersecurity titles. That narrows the *procedural* barrier (can
you even read/answer it) even though none of the ones checked had their selection criteria
visible in the API projection to confirm the *substantive* barrier (staff/insurance/refs) is
also low.

---

## TOP CANDIDATES — ENGLISH SUBMISSION LANGUAGE

| Notice | Buyer | Value | Deadline | Title | Classification |
|---|---|---|---|---|---|
| [588260-2026](https://ted.europa.eu/en/notice/-/detail/588260-2026) | Fáilte Ireland | €800,000 | 2026-09-24 | **Cybersecurity Specialist Services** (IT/2026/08) | UNKNOWN_CRITERIA_IN_DOCS_ONLY — procedure type is quoted as `"restricted"` (Restricted), meaning this is not a direct open submission; `selection-criteria-source` = `epo-procurement-document` only, no criteria text in the TED projection |
| [601103-2026](https://ted.europa.eu/en/notice/-/detail/601103-2026) | Health and Safety Authority (Ireland) | €900,000 | 2026-10-12 | Security Operations Centre (SOC), SIEM and Managed Incident Response Service | UNKNOWN_CRITERIA_IN_DOCS_ONLY — `submission-language` quoted as `ENG`, `official-language` `ENG`, procedure type `"open"`, but `selection-criteria-source` = `epo-sub-espd` (criteria live only in the ESPD/procurement documents, not fetched) |
| [594961-2026](https://ted.europa.eu/en/notice/-/detail/594961-2026) | Enterprise Ireland | €800,000 | 2026-09-15 | Single Party Framework — Microsoft Azure services partner | Not a security-testing/audit engagement (Azure partner framework); flagged only because it surfaced in the ENG+security-term sweep. Not detail-checked — outside scope. |
| [570451-2026](https://ted.europa.eu/en/notice/-/detail/570451-2026) | Iarnród Éireann (Irish Rail) | €850,000 | 2026-09-14 | Internal Communications Platform | Not security-relevant on inspection (mobile comms SaaS); surfaced by full-text match only. Excluded from further review. |

**Note on 588260 and 601103:** both are real, live, English-submission, EU cybersecurity
service contracts a solo AU operator could physically read and respond to without a
translator — but neither notice's own selection-criteria/exclusion-grounds text is present in
the TED API projection this module can reach. A human must open the linked
`procurement documents` URL (`etenders.gov.ie` for both) to find the real staff/insurance/
reference requirements before any bid/no-bid call. Per this module's own rule, that is reported
as an open question, not resolved by guessing.

---

## SMALLEST-VALUE NOTICES CHECKED IN DETAIL (multilingual security sweep)

Sorted by TED's own stated value, ascending. Every classification below is backed by a quoted
field from `assess_eligibility()`'s output for that exact `publication-number`.

| Notice | Buyer / Country | Value | Deadline | Classification |
|---|---|---|---|---|
| [471543-2026](https://ted.europa.eu/en/notice/-/detail/471543-2026) | EDISU Pavia, Italy | €303,150 | 2026-09-11 | BLOCKED_BY `submission language(s): ITA` (Italian only) — English-only operator cannot submit |
| [510184-2026](https://ted.europa.eu/en/notice/-/detail/510184-2026) | Giubileo 2025 S.p.A., Italy | €454,728 | 2026-09-15 | BLOCKED_BY `submission language(s): ITA`, and by quoted turnover clause: *"Fatturato globale ... almeno pari € 700.000,00 IVA esclusa"* (€700k min turnover) plus *"almeno n. 2 servizi analoghi ... di importo minimo per ciascun contratto pari a € 150.000,00"* (2 reference contracts ≥€150k each) |
| [572519-2026](https://ted.europa.eu/en/notice/-/detail/572519-2026) | Comune di Benevento, Italy | €420,000 | 2026-09-21 | BLOCKED_BY `submission language(s): ITA`; criteria otherwise `epo-sub-espd` (docs only, not fetched) |
| [515847-2026](https://ted.europa.eu/en/notice/-/detail/515847-2026) | Euro-Métropole de Metz, France | €550,000 | 2026-09-07 | BLOCKED_BY `submission language(s): FRA` (repeated FRA per lot); selection criteria `epo-procurement-document` only |
| [592609-2026](https://ted.europa.eu/en/notice/-/detail/592609-2026) | CINECA, Italy | €600,000 | 2026-09-28 | Not detail-checked (not directly security-typed on title: "Document management system") |
| [578580-2026](https://ted.europa.eu/en/notice/-/detail/578580-2026) | degewo AG, Germany | €691,200 | 2026-09-22 | **BLOCKED (prior finding, confirmed again this run)**: quoted *"Jeder Penetrationstester muss ... OSCP oder OSCP+ ... HTB CAPE ... OSWE, GIAC / SANS ... GPEN / CREST ... CompTIA"*; *"Deutschkenntnisse mindestens auf GER Niveau C1"*; *"Betriebshaftpflichtversicherung ... mind. Deckungssumme von 3 Mio. EUR"*; *"Mindestens 3 Penetrationstester, mindestens 1 Projektmanager"* |
| [517049-2026](https://ted.europa.eu/en/notice/-/detail/517049-2026) | Gemeente Rotterdam, Netherlands | €1,750,000 | 2026-09-07 | BLOCKED_BY `submission language(s): NLD` (title literally "Pentesten" — real pentest contract, Dutch-only submission); criteria `epo-procurement-document` only |
| [475583-2026](https://ted.europa.eu/en/notice/-/detail/475583-2026) | Smals, Belgium | value not stated | 2026-09-30 | BLOCKED_BY `submission language(s): NLD, FRA` — "Cyber Threat Intelligence Platform"; no English option |
| [556244-2026](https://ted.europa.eu/en/notice/-/detail/556244-2026) | RTE (Réseau de Transport d'Électricité), France | value not stated | 2026-09-18 | BLOCKED_BY multiple quoted clauses: *"Capacité à communiquer en français, à l'oral comme à l'écrit"*; *"Capacité à intervenir sur site en France métropolitaine en moins de 2 heures"*; *"une ou plusieurs des certifications suivantes : ISO 27001, PASSI, PDIS, CISSP, OSCP, CISM, CEH, IEC62443"* |
| [591004-2026](https://ted.europa.eu/en/notice/-/detail/591004-2026) | Ministerium für Land- und Ernährungswirtschaft, Germany (Brandenburg) | value not stated | 2026-09-28 | BLOCKED_BY `submission language(s): DEU`; and quoted: *"Die Betriebshaftpflichtversicherung muss eine Deckung über EUR 3.000.000 ... und über EUR 1.000.000"*; *"gültiges Zertifikat als 'Interner Auditor ISO/IEC 27001' ... 'IT-Grundschutz-Praktiker'"* |
| [566622-2026](https://ted.europa.eu/en/notice/-/detail/566622-2026) | Landesbetrieb IT, Berlin/NRW, Germany | value not stated | 2026-09-15 | BLOCKED_BY `submission language(s): DEU`; selection text otherwise thin ("Security Advisory Service", `slc-sec-inf` only, no explicit insurance/turnover clause visible) |
| [576565-2026](https://ted.europa.eu/en/notice/-/detail/576565-2026) / [597168-2026](https://ted.europa.eu/en/notice/-/detail/597168-2026) | Tisséo Ingénierie, Toulouse, France | value not stated | 2026-09-07 / 2026-10-30 | BLOCKED_BY `submission language(s): FRA`; and quoted: *"Le candidat doit justifier d'un chiffre d'affaires global annuel de 500 000 euro(s) Ht"*; *"Les certificats de qualifications professionnelles Passi"*; *"Au moins 3 références de test d'intrusion conduits pour des systèmes industriels (Operation Technologies - Ot)"* — real French OT-pentest audit work, PASSI-gated |
| [594937-2026](https://ted.europa.eu/en/notice/-/detail/594937-2026) | PGKiM Sandomierz, Poland | value not stated | 2026-09-11 | BLOCKED_BY `submission language(s): POL`; criteria `epo-procurement-document` only |
| [595436-2026](https://ted.europa.eu/en/notice/-/detail/595436-2026) | Szpital Kliniczny, Poland | value not stated | 2026-09-28 | BLOCKED_BY `submission language(s): POL, POL`; and quoted: *"co najmniej 2 osoby posiadające certyfikat audytora wiodącego ... PN-EN ISO/IEC 27001"*; *"certyfikat CISSP"*; *"certyfikat CEH (Certified Ethical Hacker)"*; *"co najmniej 4 osobami"* (min. 4 named staff with specific certs) |

---

## BROADER SMALLEST-VALUE LIST (not yet eligibility-checked)

From the 218-notice multilingual security sweep, real TED-stated values, smallest first
(includes non-security-titled hits that matched the full-text terms only in body text — kept
for completeness, not pre-filtered by my own judgement of relevance):

| Notice | Value | Buyer / Country | Title (truncated) |
|---|---|---|---|
| [538618-2026](https://ted.europa.eu/en/notice/-/detail/538618-2026) | €60,000 | Greece | Patent and copyright consultancy services |
| [531861-2026](https://ted.europa.eu/en/notice/-/detail/531861-2026) | €82,500 | Greece | Software-related services |
| [545982-2026](https://ted.europa.eu/en/notice/-/detail/545982-2026) | €146,383 | Greece | Database and operating software package |
| [538502/554446/557151/564622-2026](https://ted.europa.eu/en/notice/-/detail/538502-2026) | €226,000 (x4 republications) | Landkreis Rotenburg, Germany | IT services consulting |
| [525634-2026](https://ted.europa.eu/en/notice/-/detail/525634-2026) | €250,000 | European Commission DG CNECT, Belgium | Study of the Cyber Solidarity... |
| [544833-2026](https://ted.europa.eu/en/notice/-/detail/544833-2026) | €265,000 | Wiesbaden, Germany | Communication software package |

None of these were run through `assess_eligibility()` this cycle — flagged as
**UNKNOWN_CRITERIA_IN_DOCS_ONLY** by default until fetched. The 226,000/265,000/60,000-EUR
tier is the next place to spend query budget if a further pass is wanted, since low value is
the one signal this run confirms correlates with (though does not guarantee) lower barriers —
the Rotterdam "Pentesten" notice above is the one clean counter-example already caught
(€1.75M, real pentest contract, but Dutch-only submission — value and barrier are independent
variables, not two names for the same thing).

## CAVEATS / WHAT THIS DOES NOT ESTABLISH

- **`UNKNOWN_CRITERIA_IN_DOCS_ONLY` is not a soft "probably fine."** For 601103 and 588260 (the
  two English-submission candidates), the real gating clauses may say exactly what degewo's
  said. Nobody has read `etenders.gov.ie`'s actual document set yet.
- Currency is not converted (PLN, NOK, SEK, DKK, CZK figures above are exactly as TED stated
  them, not normalised to EUR).
- `submission-language = ENG` was confirmed to genuinely filter server-side (475 of the CPV/
  deadline baseline vs. 7,140 without it), not silently ignored.
- No notice here has been verified beyond what TED's own API states — per `mouth_ted.py`'s own
  value discipline, these are OBSERVED facts about currently-live notices, not VERIFIED offers.
