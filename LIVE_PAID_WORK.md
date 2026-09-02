# Live Paid Pentest/Security Work — Solo Operator, No Certs, Cairns AU

Researched 2026-09-02. Operator profile: solo, Cairns AU, no OSCP/CREST/GIAC, no
insurance, no corporate references, ABN held, remote-capable.

Every row below traces to a URL actually fetched or returned by search this
session. Nothing fabricated. Where a search snippet couldn't be verified by a
direct fetch, that's flagged.

---

## RANK 1 — Skills-test-gated platforms (no cert wall, real entry route)

### Synack Red Team — BEST FIT, HIGHEST PRIORITY
- Certifications are **not stated as mandatory**. SRT Pathways page: "SRT
  Pathways are predefined third-party certifications/achievements that can be
  used to **expedite** an applicant's onboarding" — i.e. optional accelerant,
  not a gate.
- Non-cert route: standard onboarding's **Technical Review** stage is "done
  through a private CTF on the HackTheBox platform" — a skills test, not a
  credential check.
- Full pipeline: application → background/ID check (residency restrictions
  apply: no Cuba/N.Korea/Syria/Iran/Crimea/China/Russia residents) → resume
  review → technical review (HTB CTF) → onboarding. Reported ~6 month average,
  <10% acceptance historically.
- Pay: per-vuln/mission bounty model, not disclosed publicly in what was
  fetched.
- URL: https://www.synack.com/red-team/pathways/
- Seen: 2026-09-02.
- **Verdict: this is the one to actually pursue.** No cert wall, explicit
  skills-test substitute, remote, Australia not excluded.

### Cobalt Core
- No explicit mandatory certification found on the official page. Vetting is
  5 stages; stage 2 is "a Cobalt skills assessment to test their technical
  abilities" — skills-test gated, not cert-gated on paper.
- However: reviewed applications are "based on tenure, skill and expertise,"
  and the visible Core member base averages 11 years' experience and holds
  OSCP/CISSP/CREST — so while not a hard legal requirement, competitive bar is
  high in practice.
- Freelance, part-time structure — fits solo operator.
- URL: https://www.cobalt.io/life/become-a-pentester
- Seen: 2026-09-02.
- **Verdict: apply after Synack — real skills-test path but tougher de facto bar.**

### Intigriti Hybrid Pentesting (PTaaS)
- No certification requirement of any kind found. Gate is entirely
  **platform track record**, not a paper credential:
  - ID-verified account
  - 1+ years registered on Intigriti
  - 1+ critical/exceptional finding all-time
  - 80%+ validity ratio overall
  - 15+ vulnerabilities found all-time
  - <33% informative/spam in last 15 submissions
  - 50%+ of finds on paid (non-RDP) programs
  - Then a language/communication + pentest-knowledge interview with a PTaaS
    Pentest Manager.
- "If equivalent performance on comparable platforms can be demonstrated,
  these criteria may also be considered fulfilled" — so an established H1/
  Bugcrowd bounty history could count.
- URL: https://www.intigriti.com/blog/news/how-to-become-eligible-for-hybrid-pentesting
- Seen: 2026-09-02.
- **Verdict: not accessible day one — requires first building a 1-year bug
  bounty track record on Intigriti itself (free to start, no cert). Good
  medium-term lane, not immediate income.**

### HackerOne Pentests
- Certifications **effectively required in practice**: "minimum of 3 years of
  professional industry experience, top-tier security testing certifications,
  exemplary HackerOne performance metrics, and a clean Code of Conduct."
  Prioritised certs explicitly listed: OSCP, OSEP, OSWE, OSEE, OSED, CREST,
  AWS Security Specialty.
- Also prefers US citizenship/residency/clearances (soft filter against a
  Cairns-based applicant).
- Applications reviewed quarterly, small cohort each round.
- URL: https://h1.community/pentest-community-application-form/
- Seen: 2026-09-02.
- **Verdict: NOT a fit today — hard cert + experience wall. Revisit only
  after certs/experience exist.**

### Bugcrowd Pentests
- Could not locate a public "become a Bugcrowd pentester" application page
  with stated requirements via search or direct fetch this session — Bugcrowd
  surfaces mainly as a PTaaS *product* page (bugcrowd.com/products/pen-test-as-a-service)
  aimed at buyers, plus an internal salaried "Penetration Tester" job listing
  (workingnomads.com mirror) that wants "strong understanding of OWASP Top
  Ten... history of webapp pentests preferred" but is a W-2/PAYG-style hire,
  not the crowd-tester program.
- **Verdict: unresolved — Bugcrowd's tester-recruitment page needs a login-
  gated or JS-rendered path this fetch couldn't reach. Flag as open item, not
  a confirmed opportunity.**

---

## RANK 2 — Freelance marketplaces (live pentest demand, entry barrier)

### Upwork
- Real, active demand: dedicated hire pages for "Network Pentesters" and
  "Penetration Testers" updated monthly (Aug/May 2026 dated pages).
- Rates: median **$80/hr**, range **$60–$150/hr**; entry-level typically
  $60–80/hr.
- Entry barrier: **low** — no cert or platform-side skills test to create a
  profile and bid. Realistic ramp: new profiles compete on portfolio/reviews;
  first few jobs likely land below median rate and require underbidding
  established profiles. ABN + no-cert is fine here — client vetting, not
  platform vetting.
- URL: https://www.upwork.com/hire/penetration-testers/ ,
  https://www.upwork.com/search/freelance-jobs/penetration-testing/
- Seen: 2026-09-02.

### Freelancer.com (incl. Freelancer.com.au)
- Live project board exists with an Australia-specific mirror
  (freelancer.com.au/jobs/penetration-testing). 10,718 reviews on the
  Penetration Tester category, 4.94/5 avg — signals real recurring demand,
  not a dead category.
- Milestone-payment escrow model.
- Entry barrier: **very low** — open bidding, no gate at all. Race-to-bottom
  pricing risk on this platform specifically.
- URL: https://www.freelancer.com.au/jobs/penetration-testing
- Seen: 2026-09-02.

### Toptal
- Explicitly "top 3%" — screening funnel: language/comms eval → technical
  assessment → expert interviews. Acceptance rate quoted <3% of applicants
  across all Toptal categories (not pentest-specific figure).
- No certification explicitly required, but competitive bar is high and
  favours 2-3+ years verifiable experience.
- Entry barrier: **high effort, several weeks**, but genuinely cert-agnostic.
- URL: https://www.toptal.com/developers/penetration-testing
- Seen: 2026-09-02.

### Contra
- Search states pentesting engagements sourced through Contra "require
  certifications like CISSP and CEH" per one secondary source — this is a
  general claim from search summarisation, **not independently confirmed by a
  direct fetch of a Contra policy page**. Treat as low-confidence.
- Zero-commission model, freelancer-side.
- URL: https://contra.com/hire/security-engineers-for-security
- Seen: 2026-09-02. **Confidence: low, needs direct verification before relying on it.**

### Gun.io / Braintrust
- Both platforms are general software-engineering/dev talent marketplaces.
  No evidence of a dedicated pentest/security-testing vertical or listings
  found this session.
- **Verdict: not a lane for this work.**

---

## RANK 3 — Remote contract/freelance job boards

### SEEK (Australia) — most concrete AU-specific hits
Live contract/temp listings pulled directly from
au.seek.com/penetration-testing-jobs/contract-temp (182 contract/temp results
total in that filter, 2026-09-02):

| Title | Company | Location | Rate | Notes |
|---|---|---|---|---|
| (cleared roles) | TSPV Consultants | Canberra ACT | $150–220/hr | Requires TSPV clearance — disqualifying for this operator |
| Penetration Tester | Davidson | Moranbah/Mackay/Coalfields QLD, remote | not stated | 12-month + 2×12-month extension; QLD council-linked; "Support Cyber Security and ICT Governance Services" |
| Offensive Security Engineer – Red/Purple Team | Bluefin Resources | Brisbane QLD, hybrid | not stated | Cyber hunt/pentest/red team/threat emulation |
| GW Test Consultant | FinXL IT Professional Services | Sydney/Canberra, hybrid | not stated | National security project, likely clearance-gated |

- Certification requirements not visible in the list-page snippets — needs
  individual listing opens to confirm, which wasn't done this pass. The
  **Davidson QLD role (remote-capable, 12mo+ext)** is the standout worth
  opening directly given remote fit.
- URL: https://au.seek.com/penetration-testing-jobs/contract-temp
- Seen: 2026-09-02.

### Indeed AU / general Indeed
- Confirms 647+ remote penetration tester openings on Indeed generally, but
  aggregator-level search couldn't isolate contractor-vs-permanent or
  AU-specific without a direct filtered fetch. Most roles skew 4-5+ years
  experience, salaried.
- URL: https://www.indeed.com/q-remote-penetration-tester-jobs.html
- Seen: 2026-09-02. **Needs a follow-up direct fetch with AU + contract filters to be actionable.**

### We Work Remotely
- Live listings found: Trace3 "Offensive Security Engineer | WebApp/Internal
  & External Pentesting" — explicitly a **6-month contract with possible
  extension**. SixGen "Senior Web App Pentester" requires US citizenship +
  Secret clearance eligibility (disqualifying). Defiant Inc "Security Analyst
  for Infected Websites (Contract)" listed certs as "a strong plus" (not
  mandatory) per search snippet — **direct fetch of that listing returned
  HTTP 403**, so the exact wording is unverified; treat as promising but
  unconfirmed.
- URL: https://weworkremotely.com/remote-jobs/trace3-offensive-security-engineer-webapp-internal-external-penetration-testing-remote
- Seen: 2026-09-02.

### RemoteOK
- No penetration-testing-specific listings surfaced in this search pass —
  general remote job aggregator results dominated by Indeed/Glassdoor mirrors
  instead. **Unconfirmed / likely thin for this niche.**

### Hacker News "Who's Hiring" (September 2026 thread)
- Thread confirmed live: https://news.ycombinator.com/item?id=49522897
  (posted ~8 hours before this search). Not individually scraped for pentest-
  specific postings this pass — high-value follow-up: open the thread and
  Ctrl-F "security"/"pentest".

### Infosec-Jobs.com
- Could not get direct results from this specific board — searches redirected
  to aggregators (ZipRecruiter, Glassdoor, Indeed) instead. **Needs a direct
  fetch of infosec-jobs.com's own listing/filter page next pass — not
  resolved this session.**

---

## Summary — what to actually do, ranked

1. **Synack Red Team** — apply now. No cert wall, explicit HTB CTF skills-test
   substitute, remote-friendly, background check is the only real gate.
   Expect ~6 month vetting.
2. **Cobalt Core** — apply in parallel. Real skills assessment, freelance
   structure, but de facto competitive bar is higher (11yr-avg cohort).
3. **Upwork + Freelancer.com** — open profiles now for immediate low-barrier
   income while Synack/Cobalt vetting runs. Expect to underbid at $60-80/hr
   initially.
4. **Intigriti** — start building bug-bounty track record on the open
   platform now (free); Hybrid Pentest eligibility unlocks after ~1 year if
   metrics hold.
5. **SEEK Davidson QLD remote contract role** — worth opening directly to
   check actual cert requirements (not visible in list snippet).
6. Deferred/unresolved for a follow-up pass: Bugcrowd tester-recruitment page,
   Contra's claimed CISSP/CEH requirement, Defiant Inc listing (403'd),
   infosec-jobs.com direct fetch, HN Sept 2026 thread text search.

## Explicitly ruled out (hard cert/experience/citizenship walls)
- HackerOne Pentests — 3yr min + top-tier certs stated as requirement, US
  citizenship/clearance preferred.
- SixGen (WWR listing) — US citizen + Secret clearance required.
- TSPV Consultants (SEEK) — Australian TSPV clearance required.
