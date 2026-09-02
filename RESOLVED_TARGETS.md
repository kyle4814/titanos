# RESOLVED_TARGETS.md

Resolution pass on six UNRESOLVED live procurement opportunities. Operator profile assumed throughout: solo trader, Australia, ABN, no certifications, no insurance, no corporate references, no staff, English only. Australia is a WTO GPA party (5 May 2019).

Method: parallel research agents fetched primary sources (TED, find-tender.service.gov.uk, contractsfinder, tarjouspalvelu.fi, etenders.gov.ie, Mercell). Where a WAF/login/JS-gate blocked access, the agent stopped and reported UNREADABLE rather than guessing. No requirement below is paraphrased — quotes are verbatim from the cited source.

Date of this pass: 2026-09-02.

---

## LEAD RESULT — ECHA (Helsinki): CANNOT APPLY

**VERDICT: CANNOT APPLY** — as a bare solo trader with no track record. The prior automated "QUALIFIED" pass was wrong; corrected here.

Source: TED notice 244223-2024, section 5.1.9 Selection criteria (fetched as PDF export — full official text, not a snippet).

> "Type: Economic and financial standing / Name: Average yearly turnover / Description: Average yearly turnover of the last two (2) financial years above EUR 1.000.000. / Use of this criterion: Used"

> "Type: Technical and professional ability / Name: The Applicant must prove capacity to deliver services similar and relevant in scope and complexity of this DPS / Description: The Applicant must prove its experience with relevant services in the context of this DPS by providing five (5) references covering any of the services of this DPS. All references shall have an invoiceable value of at least 100 000 €. / Use of this criterion: Used"

> "Reserved participation: Participation is not reserved" / "This procurement is also suitable for small and medium-sized enterprises (SMEs)"

No explicit "must be a registered legal entity" clause, and no professional-indemnity-insurance criterion listed in the notice. The disqualifier is purely numeric: >€1,000,000 average yearly turnover across the last two financial years, AND five references each individually invoiced at ≥€100,000. A solo trader with no prior corporate contract history cannot meet either bar.

**DEADLINE:** "Deadline for receipt of requests to participate: 25/04/2028 12:00:00 (UTC)" — rolling DPS, opened 24/04/2024, runs to 2028. Not a near-term cutoff — the disqualification is structural, not timing.

**FIRST STEP (moot given the verdict, recorded for completeness):** Register/submit at https://tarjouspalvelu.fi/echa?id=504137&tpk=3283d842-dacd-4b63-8ebe-162ee93bd8aa — that portal itself is UNREADABLE without login ("Julkaisuun tutustuminen sekä vastauksen jättäminen vaativat sisäänkirjautumisen" — viewing the notice and submitting a response require login), so any additional legal-form/insurance requirements the portal form might add beyond the TED notice are unconfirmed. Immaterial: the TED-notice turnover/reference bar alone disqualifies.

---

## 1. City of Bradford MDC — STILL UNRESOLVED

**VERDICT: STILL UNRESOLVED.** The page carrying the actual conditions of participation is blocked to automated access.

Confirmed from the notice landing page (https://www.find-tender.service.gov.uk/procurement/ocds-h6vhtk-06e59c): buyer is City of Bradford Metropolitan District Council; title "Ad-Hoc Application Penetration Testing and IT Health Checks (PSN) and Other Security Services"; notice 2026/S 000-078110, published 17 August 2026; described (paraphrase from page, not verbatim — full text not extractable) as seeking providers for penetration testing and IT Health Checks aligned to NCSC/OWASP practice, covering PSN compliance, via block purchases of 10 consultancy days, structured as an Open Framework under the Procurement Act 2023 with the top 3 providers, 3-year initial term plus possible 12-month extension.

The detail page that would carry CPV codes, procedure type, exact deadline, and conditions of participation (insurance, CHECK/CREST, staff numbers, references) — https://www.find-tender.service.gov.uk/Notice/078110-2026 — **returned HTTP 403 Forbidden on every fetch attempt.**

**UNREADABLE — human must download from https://www.find-tender.service.gov.uk/Notice/078110-2026**
**UNREADABLE — human must download from https://www.contractsfinder.service.gov.uk/notice/16fed7e8-1b53-4f81-b582-0e84ddc2cdcf** (mirror, also 403)

A superficially similar 2022 predecessor notice (different OCID, expired, not this tender) was found at uk.eu-supply.com and awarded without a stated CHECK/CREST/insurance mandate in the fields exposed — but this is a different, closed procurement and cannot be used as evidence for the 2026 terms.

**CRITICAL QUESTION — unanswered:** whether CHECK/CREST accreditation is mandated for the PSN ITHC element. No verbatim clause found either way. PSN ITHC work conventionally requires CHECK — treat as a strong prior, not a confirmed fact.

**DEADLINE:** not found (blocked page).

**FIRST STEP:** A human (not an automated agent — the WAF blocks fetch tools) must open https://www.find-tender.service.gov.uk/Notice/078110-2026 in a real browser and read the conditions-of-participation section and any linked ITT pack.

---

## 2. NHS England — STILL UNRESOLVED (notice not locatable)

**VERDICT: STILL UNRESOLVED.** No notice matching this description could be found on either UK procurement portal.

Searches of find-tender.service.gov.uk and contractsfinder.service.gov.uk for "NHS England Penetration Testing" / "£7.2M" returned no matching result — both portals' search is JS/form-driven and did not respond to direct query-string fetch, returning generic unfiltered listings instead.

The only genuinely real penetration-testing-related notices located on Find a Tender are unrelated to NHS England:
- "Threat Led Penetration Testing - Black Team" — https://www.find-tender.service.gov.uk/Notice/059973-2025 (buyer: UK Shared Business Services / UK Space Agency, see item 3)
- "ITHC, Penetration Testing and Associated Services Contract 2" — https://www.find-tender.service.gov.uk/Notice/034110-2024 (appears to be Defra Group per snippet, not confirmed)

**No independent confirmation exists that an "NHS England — Penetration Testing Services 2026-2030" notice worth £7.2M is real.** It may be misattributed, mis-titled, or not yet published. Do not treat the figure/title as sourced.

**DEADLINE:** not found.

**FIRST STEP:** A human must run the interactive search UI directly at https://www.find-tender.service.gov.uk/Search/Results and https://www.contractsfinder.service.gov.uk/Search with the keywords "NHS England penetration testing" — the JS-driven search cannot be queried by an automated fetch tool. If nothing surfaces, treat the original opportunity claim as unverified/likely stale.

---

## 3. UK Space Agency — CANNOT APPLY (deadline passed)

**VERDICT: CANNOT APPLY** — this specific opportunity's window is closed regardless of eligibility.

Source: search-snippet extracts of notice 2025/S 000-059973 ("Threat Led Penetration Testing - Black Team," https://www.find-tender.service.gov.uk/Notice/059973-2025 — the primary page itself returned 403 to fetch, so these are snippet quotes, not full-document verbatim):

> "The notice identifier is 2025/S 000-059973, published on 24 September 2025."

> Buyer: UK Shared Business Services Ltd acting for UK Space Agency; sourcing reference "UKSAC25_0071."

> Nature of work: "a limited scope assessment of the physical security posture of a number of companies through a real-world physical intrusion attempt... may be required to gain 'unauthorised' access via gated control, guards, perimeter fencing, CCTV and/or a reception area, and access to a controlled building, floor or room." — this is **physical red-team intrusion testing**, not cyber/application pentesting.

> Contract value: "£200,000 excluding VAT (£240,000 including VAT)." Contract dates: "17 November 2025 to 31 March 2026, with a possible extension to 31 March 2027."

> Process: "Selection questionnaire to identify capable potential bidders... Portal: Jaggaer eSourcing Portal, register at https://beisgroup.ukp.app.jaggaer.com/"

> "The deadline for the EoI Selection Questionnaire submission is Wednesday 1st October 2025 at 14:00."

**DEADLINE: 1 October 2025, 14:00 — already passed** (9+ months before this resolution pass). Dead regardless of what the eligibility criteria say.

Underlying eligibility (SC clearance, UK nationality/right-to-work, insurance, turnover) remains **unconfirmed** — the Selection Questionnaire document is behind the blocked/login-gated Jaggaer portal — but this is now moot for this notice.

**FIRST STEP (for any future reissue):** Register a free supplier account at https://beisgroup.ukp.app.jaggaer.com/, then monitor find-tender.service.gov.uk for a new UK Space Agency TLPT notice.

---

## 4. RTÉ Ireland — STILL UNRESOLVED (fully unreadable)

**VERDICT: STILL UNRESOLVED.** Zero criteria retrieved. Do not trust any prior claim about this DPS's requirements.

The document list page (https://www.etenders.gov.ie/epps/dps/listDPSContractDocuments.do?resourceId=6565390) confirms the real document exists — "25P041 RTÉ Cyber Security DPS v3.0 Revised.docx" is listed — but every download link on the page is `href="#"`, i.e. JS-triggered client-side, with no static URL an automated fetch tool can reach.

Fallback attempts, all failed:
- irl.eu-supply.com mirror (https://irl.eu-supply.com/ctm/Supplier/PublicPurchase/210023/1/1) contains only the older, unrelated **21P042** "RTE Cyber Security Panels Tender" — not the current 25P041 DPS.
- Web search for "25P041" + RTÉ/cyber security/selection criteria/insurance returned nothing before the session's search budget was exhausted.

**UNREADABLE — human must download from https://www.etenders.gov.ie/epps/dps/listDPSContractDocuments.do?resourceId=6565390** (requires a real browser and a registered eTenders.gov.ie supplier account/login; the "25P041 RTÉ Cyber Security DPS v3.0 Revised.docx" file is the only real source for turnover minimums, insurance, certifications, EU/non-EU eligibility, team-size rules, and the actual submission deadline).

**DEADLINE:** not found — not visible on the docs page.

**FIRST STEP:** A human logs into etenders.gov.ie with a registered supplier account and downloads the ITT docx directly.

---

## 5. EU Commission DG DIGIT — STILL UNRESOLVED (fully unreadable)

**VERDICT: STILL UNRESOLVED.** Both primary sources are blocked.

- Mercell portal (https://s2c.mercell.com/today/31298): "Login is required to view content. The page displays only a loading state and the Mercell logo; no procurement documents, details, or information are visible without authentication." No CPV codes, description, or eligibility criteria retrievable.
- TED notice (https://ted.europa.eu/en/notice/-/detail/773405-2024): renders as a JavaScript-only Angular SPA; automated fetch received an empty page shell, no static text. Alternate API/URL forms attempted (`/en/notice/773405-2024`, `api.ted.europa.eu/v3/notices/773405-2024`, `udl?uri=TED:NOTICE:...`) returned 404/400 — these are simply not valid direct paths, not evidence the notice doesn't exist.
- Web search budget was exhausted before an indirect route (mirror/aggregator) could be tried.

**UNREADABLE — human must open https://s2c.mercell.com/today/31298 directly in a browser and log in/register.**
**UNREADABLE — human must open https://ted.europa.eu/en/notice/-/detail/773405-2024 directly in a browser** (client-side rendering only).

**Flag, not a finding:** the notice title contains "IT Supplies" — in EU procurement this framing conventionally denotes hardware/goods delivery rather than services, which would put it out of scope for a solo security consultant regardless of eligibility. This is an inference from the title only, unconfirmed from the notice body — do not act on it as fact.

**DEADLINE:** not found; DPS notices are typically rolling/open-ended but this is unconfirmed for this specific notice.

**FIRST STEP:** A human registers/logs into the Mercell s2c portal directly.

---

## SUMMARY TABLE

| # | Target | Verdict | Deadline | Blocker |
|---|---|---|---|---|
| — | ECHA (Helsinki) | **CANNOT APPLY** | Rolling to 2028 | Turnover >€1M + 5×€100k references — structural, not access |
| 1 | Bradford MDC | STILL UNRESOLVED | Unknown | 403 WAF on notice detail page |
| 2 | NHS England | STILL UNRESOLVED | Unknown | Notice not locatable at all — may not exist as described |
| 3 | UK Space Agency | **CANNOT APPLY** | 1 Oct 2025 (passed) | Deadline expired |
| 4 | RTÉ Ireland | STILL UNRESOLVED | Unknown | JS-gated download links, no static URL |
| 5 | EU DG DIGIT | STILL UNRESOLVED | Unknown | Both Mercell login-wall and TED SPA block fetch |

**Only one of six converts to a clean, evidence-backed verdict the operator can act on immediately, and it's a no: ECHA is CANNOT APPLY on hard numeric grounds.** UK Space Agency is also a closed door (timing). The other four remain genuinely unresolved — not because the opportunities are fictional, but because the qualification documents sit behind WAFs, JS-only SPAs, or login walls that no automated tool here can pass without spoofing (explicitly forbidden by the task rules). Closing 1, 2, 4, 5 requires a human with a browser to open the five UNREADABLE URLs listed above and copy out the actual conditions-of-participation text — there is no further automated path to a verdict without doing that.
