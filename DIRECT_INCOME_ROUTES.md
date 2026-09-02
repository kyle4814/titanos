# Direct Income Routes — Selling Capability, Not a Vetted Relationship

Operator: solo, Cairns QLD, ABN, no certifications, no insurance, no corporate
references. Assets: strong technical/security/software capability + this
repository (cosmic-library — epistemic/verification engine, 3,500+ tests) +
fast tooling build speed.

**Tool-access note, stated plainly:** this session's WebSearch budget was
exhausted (200/200) before this task started, and it is shared across every
subagent spawned in-session — confirmed by spawning a fresh general-purpose
agent and watching its WebSearch call fail with the identical "budget
exhausted" error. WebFetch to guessed legislation/platform URLs mostly
returned 404 (no search engine was reachable to find the correct path —
Google/Bing gave irrelevant physical-security-company results, DuckDuckGo's
HTML endpoint served a CAPTCHA). Where a fact below is tagged **[LIVE]** it
was fetched and quoted in this session, right now, 2026-09-02. Where a fact
is tagged **[KNOWLEDGE, unverified live]** it reflects stable, well-documented
regulatory/market structure from training data (cutoff Jan 2026) that I could
not re-confirm live this session — treat it as "very likely still true" not
"confirmed today," and re-verify before relying on it for a real
engagement. Nothing below is fabricated; where I have no real basis I have
written **UNKNOWN**.

---

## THE CRITICAL LEGAL QUESTION

**Does an individual need a licence to perform paid penetration testing or IT
security consulting in Australia, specifically Queensland?**

**[LIVE]** A direct search of the Federal Register of Legislation
(legislation.gov.au) for "penetration testing" returned no Commonwealth Act
or legislative instrument governing it — the search tool itself reported:
*"no Commonwealth Acts or Legislative Instruments specifically related to
penetration testing, cybersecurity licensing, or IT security services are
listed."* So there is no federal licensing regime.

**[KNOWLEDGE, unverified live]** At state level, every Australian jurisdiction
regulates a "security industry" — Queensland's is the *Security Providers
Act 1993* (Qld), administered by the Office of Fair Trading. I could not
fetch the current in-force text this session (every URL I tried 404'd
without a working search engine to locate the correct page), so the exact
current definitions section is **not quoted here** and should be pulled
directly before relying on this. What is well-established and consistent
across every state Security Industry/Providers Act (Qld, NSW *Security
Industry Act 1997*, VIC *Private Security Act 2004*, etc.) is that they
license **physical** security work: crowd controllers, bodyguards, security
officers/guards, security equipment installers (alarms, CCTV, locks), and
in some states "security advisers" for *physical* premises risk. None of
these regimes were built for, and none are documented as extending to,
network penetration testing, application security review, or IT/cyber
consulting — because the licensable activity in each Act is tied to
physical premises, persons, or hardware, not computer systems.

**Verdict: UNCLEAR-LEANING-NO, not UNKNOWN.** I have high confidence from
structural knowledge that Queensland's Security Providers Act 1993 does not
capture pentesting/IT security consulting, but I was not able to pull and
quote the current definitions section live this session to make that
100% certain, and this is a decision with real consequences if wrong
(unlicensed practice of a captured activity would be an offence). Do not
treat this document as the legal confirmation.

**Exactly who to ask, before taking a paying pentest client:**
1. **Queensland Office of Fair Trading — Security Providers licensing team**
   (the regulator itself). Ask directly: "Does IT/cyber penetration testing
   or security consulting fall within a licensable 'security activity'
   under the Security Providers Act 1993?" Get the answer in writing
   (email), not verbal.
2. As a cross-check, most large AU firms and industry bodies (AISA — the
   Australian Information Security Association) have stated publicly that
   pentesting is unregulated by security-licensing law in Australia — this
   aligns with the structural reading above but I could not fetch AISA's
   current published statement live this session to quote it.
3. There is no Commonwealth equivalent of the UK's CREST-mandatory-for-gov
   model in Australia; ASD's IRAP (Infosec Registered Assessors Program) is
   a scheme for assessors doing formal ISM-compliance assessments of
   government/regulated systems — relevant only if selling *into government*
   or regulated-entity engagements requiring ISM assessment, not a general
   licence to practice. I attempted to fetch cyber.gov.au's IRAP page twice
   this session; both timed out, so this is **[KNOWLEDGE, unverified live]**
   — confirm before quoting it to a client.

**Practical implication:** general "security review," "hardening," "incident
cleanup," and "security awareness training" for small business are almost
certainly unregulated activities in Queensland — no licence, no
certification legally required to charge for them. Formal penetration
testing sits in the same unregulated bucket on current structural
understanding, but get the Office of Fair Trading's written answer before
selling it under that name to a paying client, given the money and
liability involved. Selling to *authorised* targets only, with a signed
scope/authorisation letter, is a contractual/criminal-law issue (Criminal
Code Act 1995 (Cth) Pt 10.7, unauthorised access offences) regardless of
licensing — get written authorisation for every engagement, always.

---

## RANKED ROUTES BY REALISTIC TIME-TO-FIRST-DOLLAR

### 1. Direct local small-business security/hardening services — fastest
**What:** website security review, WordPress hardening, malware/incident
cleanup, basic security awareness training, for Cairns-region small
businesses, sold directly (cold outreach, local network, Facebook business
groups).
**Licence/cert required:** none identified (see legal section above —
confirm with OFT before calling it "penetration testing").
**Pay:** UNKNOWN — no live market-rate data pulled this session. Structurally,
solo AU small-business IT/security cleanup work is commonly quoted as flat
fixed-price jobs rather than day rates; I do not have a verified current
figure and will not invent one.
**Time to first dollar:** fastest of all routes — no platform approval,
no account vetting, payment is whatever terms you set (deposit + on
completion). Bottleneck is finding the first client, not any external gate.
**Requirement to start:** ABN (already held), an invoice, a written scope/
authorisation document for anything resembling a security test.
**Source:** structural/legal reasoning above; no earnings figure sourced.

### 2. Consulting marketplaces with no vetting — fast, uncertain pay
**What:** Upwork, Freelancer.com — open sign-up, bid on jobs directly, no
credential gate to create a profile.
**[LIVE attempt failed]** Upwork's own fee-structure help page returned
HTTP 403 this session — could not confirm current freelancer service fee
or profile requirements live. **[KNOWLEDGE, unverified live]** Upwork has
historically charged freelancers a sliding service fee (was 20/10/5% tiered
by lifetime billings with a client, later moved toward a flat ~10% plus a
one-time client contract fee) — do not quote this figure to anyone without
re-verifying on Upwork's current help pages, it has changed more than once.
**Time to first dollar:** days to weeks — profile approval is near-instant,
but winning the first contract against an oversaturated freelancer pool
(especially in "security"/"penetration testing" categories, which attract
heavy low-cost overseas competition) is the real bottleneck, not any
external vetting.
**Requirement to start:** email, profile, no certification.
**URL:** https://www.upwork.com , https://www.freelancer.com
**Toptal**, by contrast, explicitly *is* a vetted marketplace (screening
interview + technical test) — it does not fit "no vetting" and is excluded
from this ranked list on that basis.

### 3. Marketplaces that pay for output — Gumroad
**[LIVE]** Confirmed fee structure from gumroad.com/pricing, fetched this
session: **"10% + $0.50 per transaction for all sales through your profile
or direct links"**, **"30% per transaction when new customers find and buy
from you through our discover marketplace,"** no monthly subscription fee,
and as of 1 January 2025 Gumroad states it handles applicable sales-tax
remittance automatically. The page did not state any KYC/vetting gate to
start selling.
**Pay:** UNKNOWN in absolute terms — no live figures were pulled on what
security/dev tools actually earn on Gumroad; do not trust any number for
this without a fresh source, published "creator earnings" figures move
constantly and are heavily survivorship-biased in marketing material.
**Time to first dollar:** fast to *list* (sign up, upload product, set
price — no approval gate found), slow to *earn* — Gumroad has no built-in
discovery/traffic engine of consequence; income depends entirely on the
seller's own audience/marketing, not the platform.
**Requirement to start:** account, product, payout method.
**URL:** https://gumroad.com/pricing
**Adjacent, not independently checked this session:** Lemon Squeezy,
Polar, Ko-fi, GitHub Sponsors — same shape (open sign-up, platform cut,
depends on your own audience). No live figures for any of these; mark
UNKNOWN rather than reuse remembered marketing numbers.

### 4. Bug bounty platforms (HackerOne, Bugcrowd)
**[LIVE attempt failed]** Both hackerone.com/leaderboard and
bugcrowd.com/about-us/ returned 404/could not be fetched this session — no
live confirmation of current payout stats or onboarding requirements.
**[KNOWLEDGE, unverified live]** Both platforms are open sign-up for
researchers (no certification required to register), pay is bounty-per-
valid-finding (not hourly), and realistic income is extremely skewed —
a small number of top researchers earn substantial money, the median
researcher earns little to nothing, and payout depends entirely on finding
valid, in-scope, unique vulnerabilities in programs that accept public
researchers (many are private/invite-only). This repository's 3,500+ tests
and verification-engine focus is a plausible skills match for security
research, but this is a low-time-to-first-dollar-is-NOT-guaranteed route —
could be one day, could be months of unpaid searching with zero payout.
**Requirement to start:** account only.
**URL:** https://hackerone.com , https://www.bugcrowd.com
**Do not** treat any specific dollar figure here as sourced — none was
verified this session.

### 5. Technical writing paid per piece
**UNKNOWN — not verified this session.** I did not successfully fetch any
publication's current pay-per-article rate or submission guidelines (no
working search to find current live pages, no direct fetch attempted
against a confirmed-correct URL). Known-to-exist-in-general categories:
security research blogs/magazines that have historically paid for
technical writeups, CTF writeups, and tutorials. Do not quote a rate for
any named publication without fetching its current writer-guidelines page
directly.
**Time to first dollar:** typically the slowest route — pitch, write,
editorial review, payment on publication (weeks, not days), even before
factoring in acceptance uncertainty.

### 6. Selling tooling / research output (legitimate, above-board only)
This repository (cosmic-library) is the operator's most differentiated
asset for this route — an epistemic/verification engine with a genuine,
large, tested codebase is not a common solo-operator asset. Two legitimate
angles:
- **Package a slice of the codebase as a sellable tool** (e.g. a specific
  verification/audit component) via Gumroad/Lemon Squeezy (route 3) —
  fastest to list, income entirely dependent on marketing/audience, which
  the operator does not yet have built.
- **Vulnerability/research data markets:** legitimate outlets exist
  (bug bounty programs above; some vendors run private VRP/data programs)
  but I have no live-verified entry point, rate, or submission process for
  any specific one this session. No grey-market/exploit-broker route is
  in scope per the task rules, and none is suggested.
**Verdict: UNKNOWN on pay, plausible on legitimacy, requires the operator
to build an audience/reputation first — not a fast route.**

### 7. AI/agent build market for small business
**UNKNOWN — no live data pulled this session** on real demand or real
rates for solo operators building automation/agent systems for small
businesses. This is squarely inside the operator's demonstrated capability
(this repo is direct proof of fast tooling build ability) but I have no
sourced figure to report, and will not invent one. This is realistically a
**route 1 clone** — direct local outreach, same licence-free status, same
"find the first client yourself" bottleneck — rather than a distinct
marketplace with its own gate.

---

## SUMMARY RANKING (time-to-first-dollar, honest)

1. **Direct local small-business services (route 1)** — fastest, zero
   external gate, pay UNKNOWN but entirely self-set; bottleneck is finding
   the first client.
2. **Gumroad/output marketplaces (route 3)** — fast to list, slow to earn
   without an existing audience; fee structure confirmed live (10%+$0.50,
   or 30% via Discover).
3. **Open consulting marketplaces (route 2, Upwork/Freelancer)** — fast
   profile approval, slow/uncertain first contract against saturated
   low-cost competition; fee terms not re-confirmed live this session.
4. **AI/agent build for small business (route 7)** — same shape as route 1,
   no verified rate data.
5. **Bug bounty (route 4)** — fastest possible payout in theory (find one
   valid bug), but zero guarantee of any payout at all; highly skewed.
6. **Technical writing (route 5)** — slowest, editorial-gated, no rates
   verified this session.
7. **Tooling/data sales (route 6)** — legitimate but requires an audience
   the operator does not yet have; no rates verified.

---

## WHAT THIS DOCUMENT DOES NOT GIVE YOU

No dollar figure in this document should be repeated to a client or used
in a financial plan without re-verification — most earnings figures
requested by the task could not be sourced live this session (WebSearch
budget was pre-exhausted for the entire session before this task began,
and most guessed direct-fetch URLs to legislation and platform pages
404'd). The one clean exception is Gumroad's fee structure, fetched and
quoted directly above. Before acting on this for real income decisions:
re-run the legal question (Queensland OFT, in writing) and re-run market
searches for routes 2, 4, 5, 6, 7 with a working search tool.
