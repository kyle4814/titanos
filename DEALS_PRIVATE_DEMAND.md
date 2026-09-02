# Private Demand — Security Help Wanted, Right Now

Research date: 2026-09-03. Operator: solo, Cairns AU, ABN, no certs/insurance/corporate refs, strong technical capability, remote-capable.

RULE FOLLOWED: no scanning/probing/contact. Passive public sources only. Every claim below traces to a URL actually fetched this session. Where a source blocked or 404'd, it's recorded as blocked, not filled in with a guess.

---

## STATUS: mostly BLOCKED on live company-level leads. Strong result on ONE vector.

Government/regulator sites (oaic.gov.au static paths, apra.gov.au, cisc.gov.au, ag.gov.au deep links, cyber.gov.au) largely 403/404/timeout to both WebFetch and curl-with-UA — several are JS-rendered SPAs that return empty static HTML, or block automated fetches outright. Seek returned 403. HN Algolia worked but is irrelevant to AU security-consulting demand (generic tech comments, no leads).

What follows is what actually resolved, ranked by strength of buying trigger.

---

## 1. SOCI Act — CONFIRMED, strongest lead vector, no scan needed

**Source**: en.wikipedia.org/wiki/Security_of_Critical_Infrastructure_Act_2018 (fetched, cross-checkable against the Act text on legislation.gov.au — direct cisc.gov.au obligations page 403'd, so treat sector list as needing a second confirmation before quoting to a client, but the structure is well-documented public law).

**WHO is obligated**: entities owning/operating assets in 11 sectors — Communications, Financial services and markets, Data storage or processing, Defence industry, Higher education and research, Energy, Food and grocery, Healthcare and medical, Space technology, Transport, Water and sewerage.

**WHAT they must do**: formally assess risk on a regular basis and run a risk management program, reporting to the Cyber and Infrastructure Security Centre (CISC); mandatory incident reporting — **72 hours for significant cyber incidents, 12 hours for critical ones**.

**Timeline**: obligations expanded in stages — 2021 (Critical Infrastructure Act), 2022 (Protection Act, added the risk management program duty), **2024 amendment explicitly brought "data storage or processing" into scope** — meaning a large population of SaaS/cloud/hosting/managed-service businesses became newly regulated critical infrastructure operators only in the last two years.

**Why this is the strongest lead class**: "Data storage or processing" as a named critical asset class is broad and recent. Many businesses in it are mid-size Australian data centre operators, MSPs, and B2B SaaS companies — exactly the size that has zero in-house CISO and cannot absorb a 12/72-hour incident reporting obligation without a designed response process. A statutory deadline that already passed (2024) means some of these entities are currently out of compliance and exposed, not merely "coming due."

**Realistic solo offer**: a fixed-price "SOCI readiness pack" — risk management program document mapped to the entity's actual environment, an incident classification + 12hr/72hr reporting runbook, and a one-day tabletop exercise. This is a deliverable a solo operator can scope, price, and deliver remotely without certification, because CISC does not require the assessor to hold a credential — it requires the program to exist and be followed.

**Gap**: I could not get the CISC obligations page itself (403) or a live register of *named* regulated entities — the Register of Critical Infrastructure Assets is not public. So this is a sector-and-deadline lead, not a named-company lead yet. Next step to sharpen it: search (once search budget resets) for AU data centre / MSP / SaaS companies who have themselves published "SOCI compliance" or "critical infrastructure" statements — that would convert this from a sector thesis into named targets.

---

## 2. Privacy Act reform — CONFIRMED status, deadline still soft

**Sources**: ag.gov.au/rights-and-protections/privacy/review-privacy-act-1988 (fetched via curl, 200), oaic.gov.au/privacy/privacy-legislation/the-privacy-act (fetched, 200).

**Confirmed facts**:
- Privacy Act Review Report released 16 February 2023.
- Government response to the review released **28 September 2023**.
- OAIC's own current page states the Privacy Act "regulates how Australian Government agencies and organisations with an annual turnover of more than $3 million, and some other organisations, handle personal information" — i.e. the **$3M small-business exemption is still live** as of this fetch. The reform agenda's headline threat to small business (removing/lowering that exemption) has NOT yet taken effect per this source.

**Implication**: this is real forced-demand-in-waiting, not forced-demand-today. A company under $3M turnover is currently NOT obligated under the Privacy Act regardless of what reform documents propose. Don't sell against a deadline that hasn't landed — I could not confirm a commenced date for exemption removal from a working source this session (the Wikipedia page for the 2024 amendment act does not exist under that title, and OAIC's dedicated tranche-1/tranche-2 tracking pages returned blocked or empty). Treat this as "watch, don't pitch yet" until the removal date is independently confirmed.

---

## 3. Job boards (Seek/Indeed/LinkedIn) — BLOCKED

seek.com.au/cyber-security-jobs (contract worktype) returned HTTP 403 to curl. seek.com.au/penetration-tester-jobs was not reached (search budget was exhausted before I could route around it). No job-ad leads produced this session — this vector needs either WebSearch (budget currently at 0/200) or a logged-in/JS-capable fetch path neither tool here provides.

---

## 4. Breach disclosures (OAIC NDB reports, cyber.gov.au advisories) — BLOCKED

oaic.gov.au/privacy/notifiable-data-breaches loaded but is a landing page only — links to the actual statistics dashboard and specific breach reports are JS-driven and did not resolve to static hrefs I could follow. cyber.gov.au/about-us/view-all-content/alerts-and-advisories timed out on every attempt (3x). No named recently-breached company was found this session — I am not reporting one, per the no-fabrication rule.

---

## 5. Funding rounds (AU/NZ startups needing SOC 2 / ISO 27001) — NOT ATTEMPTED

Search budget was exhausted before this vector could be worked (WebSearch hit 0/200 on the first batch of queries this session, before any results returned). No curl-only fixed index exists for funding announcements the way OAIC/APRA/CISC are fixed regulator pages, so this vector needs WebSearch specifically.

---

## RANKED — what's actually actionable today

1. **SOCI Act "data storage or processing" sector** (Section 1 above) — real, dated, sourced, sector-wide. Convert to named companies by searching for AU data centre/MSP/SaaS firms that self-identify as regulated critical infrastructure, or that publish SOCI/CISC compliance statements. This is the one lever worth pulling next.
2. **Privacy Act reform** — real but not yet a forcing deadline for small business; hold as a 2026-27 watch item, re-check ag.gov.au for a commenced date before using it in outreach.
3. Everything else (breach disclosures, job ads, funding rounds, expired-cert scans) — **not delivered this session**, blocked by tool budget/access, not by absence of real leads. Needs WebSearch budget restored, or a different fetch path for JS-heavy gov/job-board sites.

## NEXT MOVE

Get WebSearch budget raised (currently 0/200, hit before first real query completed) and re-run vectors 3–5, plus name specific SOCI-regulated "data storage or processing" companies to convert vector 1 from sector-thesis into a named-company pitch list.
