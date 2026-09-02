# DEALS_PRODUCTS.md — Priced Product Sheet

Compiled 2026-09-03. Operator profile this is scored against (from
`OPS_BOARD.md`/`DIRECT_INCOME_ROUTES.md`): solo trader, Cairns QLD, ABN,
**no certifications** (no OSCP/CREST/GIAC/CISSP), **no professional
indemnity or public liability insurance yet**, **no corporate reference
contracts**, strong technical security/software capability, fast
tooling build speed, a large working codebase (cosmic-library —
epistemic/verification engine, 3,600+ tests) usable as portfolio proof.

**Session tool constraint, stated honestly:** this session's WebSearch
budget was exhausted before this task started (confirmed, same
limitation `DIRECT_INCOME_ROUTES.md` already recorded). Every rate
figure below is either (a) fetched directly this session via WebFetch
from a named URL — marked **[FETCHED]** — or (b) carried over from
`OPS_BOARD.md`, itself sourced live in an earlier session — marked
**[OPS_BOARD]** — or (c) reasoned from one of those two anchors with the
reasoning shown — marked **[REASONED, not directly sourced]**. Nothing
below is invented. Where no real anchor exists at all, it says
**UNKNOWN**.

---

## THE RATE EVIDENCE THIS SHEET IS BUILT ON

| Fact | Figure | Source |
|---|---|---|
| AU penetration tester salary (employee, not freelance) | Avg **AU$97,592/yr**, range AU$59k–$156k total pay, 31 profiles, updated Jun 2026 | **[FETCHED]** payscale.com/research/AU/Job=Penetration_Tester/Salary |
| ISO 27001 accredited certification audit | **$8,000–$30,000**, surveillance audits $8k–$15k/yr, cert-body daily audit fees $1,800–$2,500/day | **[FETCHED]** isms.online/iso-27001/cost/ — **currency not confirmed on the page** (isms.online is UK-based; treat as GBP-or-USD, not AUD, until re-verified) |
| Web app penetration test, per engagement | **$5,000–$50,000 USD**; "a simple web app on a single server costs around $5,000 USD" | **[FETCHED]** getastra.com/blog — a vendor (India-based, USD pricing), global/US market reference, not AU-specific |
| AU professional indemnity insurance, sole trader IT consultant | **from $43/month** | **[OPS_BOARD]** BizCover, April 2025 |
| AU PI + public liability combined | **~$81/month average** | **[OPS_BOARD]** BizCover, April 2025 |
| NSW Government ICT Services Scheme, "K03 Security testing" category | Contracts up to **$150,000 AUD** ceiling at Registered tier | **[OPS_BOARD]** NSW scheme rules, live-fetched |
| UK Bradford MDC pentest framework | **£300,327** total, awarded as 10-day consultancy packages, NCSC/OWASP standards | **[OPS_BOARD]** live tender notice |
| UK Kingston-upon-Thames cyber security training contract (2025–2029) | **£69,552** total (≈£17k/yr) | **[OPS_BOARD]** live tender notice — evidence councils buy training at this size, not a live target now |
| Gumroad platform fee | **10% + $0.50/transaction** direct sales, **30%** via Discover marketplace, no monthly fee | **[OPS_BOARD]** live-fetched, gumroad.com/pricing |

Everything not in that table and used below is marked inline as
**[REASONED]** with the arithmetic shown, or **UNKNOWN**.

**The legal flag, carried forward from `DIRECT_INCOME_ROUTES.md` and
repeated wherever it applies below:** whether Queensland's *Security
Providers Act 1993* captures IT/penetration-testing work is recorded
there as **UNCLEAR, LEANING NO** — structurally, that Act and its
interstate equivalents license physical security (guards, crowd
control, alarm/CCTV installers), and no Commonwealth licensing regime
for pentesting was found. But it was never confirmed in writing from
the Queensland Office of Fair Trading. **Do not invoice anything as
"penetration testing" until that written answer exists.** Every offer
below that touches testing is worded and should be sold as "security
review" / "vulnerability assessment" / "security assessment" instead —
descriptive, defensible language that doesn't invoke the regulated-sounding
term, while the OFT question is still open.

---

## PRODUCT 1 — Web Application Security Review

**Invoice name:** *Web Application Security Review — Fixed Scope*

**Exact scope:** grey-box manual + tool-assisted review of one defined
web application or public-facing site against the OWASP Top 10 and
OWASP ASVS Level 1 controls: authentication/session handling, access
control, input validation/injection classes, exposed config/secrets,
transport security, common misconfiguration. One authenticated test
account provided by the client. Deliverable: a written report —
findings with severity (Critical/High/Medium/Low), reproduction steps,
remediation guidance, an executive summary a non-technical owner can
read.

**Explicitly excluded:** network/infrastructure testing, physical
testing, social engineering, red-team/adversarial simulation, DoS
testing, retesting after fixes (offered separately), anything outside
the one named application's URL scope.

**Duration:** 2–3 working days effort, delivered inside a 5–7 day
window (thinking/write-up time included).

**Price:** **AUD $2,500–$3,500 for the first 1–2 clients** (below-market,
deliberately, to buy the first real testimonial), moving to
**AUD $4,500–$6,000** once a track record exists. Justification: getastra's
own quoted floor for "a simple web app on a single server" is $5,000
USD (**[FETCHED]**) — call it roughly AUD $7,500–$8,000 at current
rates for a full US/global-market vendor engagement; this offer is
scoped narrower (one app, capped days, no retest) and priced under that
anchor rather than at it, both because the scope is smaller and because
there is no track record yet to price at parity.

**Who buys it:** a Cairns/FNQ small business with a customer-facing
web app — example company type: a regional tourism booking platform, a
trades/services marketplace app, a real-estate agency's client portal.

**Why they buy:** a customer, insurer, or investor has asked "have you
had this tested"; a cyber-insurance renewal now asks the question; a
competitor or supplier in the same industry was breached and it made
the local news; preparing to answer a government-tender security
question honestly.

**What it requires him to have:** a written scope/authorisation letter
signed by the business owner before any testing starts — non-negotiable
regardless of licensing status, because unauthorised access is a
Criminal Code Act 1995 (Cth) Pt 10.7 matter independent of any
state licence question. **No certification or insurance is legally
required to sell this** under current understanding, but flag it to
the buyer honestly: he has no PI/PL insurance yet (BizCover quotes
combined cover from ~$81/month **[OPS_BOARD]** — cheap enough that
buying it before the first paid engagement is a real option, not a
blocker).

**First-sale path:** direct outreach to 15–20 named Cairns/FNQ
businesses with an obvious web presence (booking systems, e-commerce,
client portals) via LinkedIn/email/Cairns Chamber of Commerce network;
offer the first engagement at the low end of the discounted band
explicitly in exchange for a written testimonial and permission to name
them (or describe them anonymously) as a reference. No platform, no
gatekeeper — the bottleneck is finding the first buyer, not any
external approval.

**Remote from Cairns to UK/EU/US:** **Yes, entirely.** Nothing in this
scope requires physical presence — delivery is a report over email/call.

---

## PRODUCT 2 — SOC 2 / ISO 27001 Readiness Gap Analysis

**Invoice name:** *Compliance Readiness Gap Analysis (SOC 2 / ISO 27001)*
— **never invoiced or marketed as "certification," "audit," or
"attestation"; those require an accredited third-party body he is not.**

**Exact scope:** structured review of the client's current security
posture against SOC 2 Trust Services Criteria or ISO 27001 Annex A
controls (client picks the framework); interviews with 1–2 staff;
document/config review (access control, backup, change management,
vendor risk, incident response); a gap report mapping current state →
target control, with a prioritised remediation roadmap and rough effort
estimate per gap.

**Explicitly excluded:** the actual audit or certification decision
(only an accredited certification body — e.g. for ISO 27001 — or a
licensed CPA firm — for SOC 2 — can issue that), penetration testing
(sold separately as Product 1), implementation of the remediation items
(scoped and quoted separately once the gap list exists).

**Duration:** 3–5 working days.

**Price:** **AUD $3,000–$6,000 fixed**. Justification, marked
**[REASONED, not directly sourced]**: isms.online's own figures
(**[FETCHED]**) put the *full accredited audit* at $8,000–$30,000 with
$1,800–$2,500/day certification-body fees; a readiness gap analysis is
a smaller, non-audit deliverable that should structurally price well
under the audit itself — no vendor's specific gap-analysis-only price
was found and re-verifiable this session, so this band is reasoned
from that anchor, not quoted from a source pricing gap analysis
directly. Flag this honestly to any buyer who asks for a source.

**Who buys it:** a SaaS or B2B software vendor, roughly 5–30 staff —
example company type: a Brisbane or remote-first AU SaaS startup whose
biggest prospect's procurement team has said "no SOC 2/ISO 27001, no
contract."

**Why they buy:** an enterprise sales deal is stalled on exactly that
question; a board or investor has asked for a security roadmap; cyber
insurance renewal now asks about a formal framework.

**What it requires him to have:** no certification or insurance
required — this is advisory/documentation work, not an attestation. He
is not claiming to *be* a SOC 2 auditor or ISO 27001 certification
body, and the deliverable must say so explicitly on its cover page to
avoid any misrepresentation risk.

**First-sale path:** LinkedIn outreach to AU/NZ SaaS founders and
CTOs directly, framed as "what would a real auditor find before you
pay one to find it" — cheaper and faster than hiring a compliance
consultancy for a first look; alternatively list as a fixed-price gig
on Upwork/Freelancer (already flagged in `DIRECT_INCOME_ROUTES.md` as
fast-to-start, no vetting gate) using this repo's own epistemic/schema
validation engine as concrete proof of rigorous, structured thinking —
a genuine differentiator, not a claim.

**Remote from Cairns to UK/EU/US:** **Yes, entirely.** Interviews by
video call, documents shared digitally, report delivered as a PDF.
This is the single best-suited offer on this sheet for an overseas
buyer — no timezone-sensitive live component beyond 1–2 scheduled
calls.

---

## PRODUCT 3 — Security Policy & Documentation Pack

**Invoice name:** *Information Security Policy Pack*

**Exact scope:** a tailored written policy suite — Acceptable Use,
Access Control, Incident Response Plan, Data Classification & Handling,
Password/MFA Standard, Third-Party/Vendor Risk, a one-page Business
Continuity basics document — mapped to ISO 27001 Annex A / SOC 2 /
Australian Signals Directorate Essential Eight where relevant, written
in plain language a small-business owner can actually follow, not
boilerplate legalese.

**Explicitly excluded:** implementation of the policies (e.g. actually
configuring MFA), legal review (recommend the client's own solicitor
sign off on anything with employment-law implications), ongoing
maintenance (offered as a cheap annual review add-on).

**Duration:** 2–3 working days (much of this is templatable — the
economics improve fast after the first two or three are built).

**Price:** custom-tailored version **AUD $1,500–$3,000**; a cheaper
**generic template pack at AUD $500–$800** sold as a self-serve
download (see first-sale path). Reasoning: **[REASONED]** — priced as
a fraction of Product 2's readiness assessment since it is pure
documentation output with no interview/gap-mapping labour, calibrated
by his own time (2–3 days) at a rate consistent with the freelance
day-rate reasoning used in Product 6 below.

**Who buys it:** any small-mid AU business needing to *show* governance
— for a tender response, a cyber-insurance renewal, or a client
contract clause requiring "documented security policies." Example
company type: a 10–40 person regional engineering or accounting firm
bidding on a government contract that lists ISM/Essential Eight
documentation as a requirement.

**Why they buy:** insurers increasingly ask for named policies at
renewal, not just a yes/no; government and enterprise tenders often
list this as a pass/fail line item; a new client's due-diligence
questionnaire literally asks for the policy names.

**What it requires him to have:** nothing beyond ABN and competent
writing — no cert, no insurance, no licence question at all (this is
pure advisory documentation, the safest offer on this sheet from a
regulatory-exposure standpoint).

**First-sale path:** build the generic template pack once, sell it on
Gumroad (fee confirmed **[OPS_BOARD]**: 10%+$0.50/txn direct, no
monthly cost) at $500–$800 to generate the first transactions and
reviews with zero outreach cost per sale, then use every buyer as a
warm lead for the $1,500–$3,000 tailored version.

**Remote from Cairns to UK/EU/US:** **Yes, entirely** — though note UK
buyers will expect GDPR-flavoured language and US buyers state-specific
breach-notification references; both are extra research he'd need to
do per-market, not currently a verified capability (flag as UNKNOWN
whether his current policy templates already cover those correctly —
check before selling into UK/US specifically).

---

## PRODUCT 4 — Phishing Simulation Campaign

**Invoice name:** *Phishing Awareness Simulation*

**Exact scope:** one simulated phishing campaign against a client-
supplied staff list (1–3 email templates, realistic but non-destructive
lures), run over 1–2 weeks, tracked click-through and report rates, a
results report with a per-department breakdown and follow-up
recommendations. Built on free/open tooling (e.g. GoPhish, self-hosted
— keeps this zero-dependency, consistent with his existing build
posture) rather than a paid platform licence.

**Explicitly excluded:** disciplinary action against staff who click
(client's call, not his), credential harvesting beyond a landing-page
click event, any campaign without named management sign-off.

**Duration:** 1–2 days setup, 1–2 week live run (low-touch), half a day
for the report.

**Price:** **AUD $800–$1,500 flat, for up to ~50 staff** (scale price
by headcount above that). **[REASONED]** — priced as a low-effort,
templatable add-on rather than against any specific competitor
quote; no phishing-simulation-specific AU price point was
sourced this session — treat this band as a starting point to test,
not a confirmed market rate.

**Who buys it:** a 20–100 staff AU small-mid business, typically
alongside a cyber-insurance renewal or after a near-miss (a staff
member nearly paid a fake invoice).

**Why they buy:** insurer asked "do you run phishing tests"; a recent
close call made the owner nervous; annual awareness-training budget
exists and this is the cheapest visible action.

**What it requires him to have:** **written, management-level
authorisation is not optional here — this is the one offer on this
sheet with a real ethical/legal edge**, because it involves deliberately
deceiving employees. Get explicit sign-off in writing before every
campaign, scope exactly who is in/out of scope, and be ready to explain
to any employee who complains that management authorised it. No
licence/certification required to run it technically.

**First-sale path:** bundle as an add-on to Product 3 (Policy Pack) or
Product 5 (Training) for the first client rather than sell it
standalone cold — it lands better as "part of a hygiene package" than
as a first-contact pitch.

**Remote from Cairns to UK/EU/US:** **Yes**, fully — email-based, no
physical or strict-timezone dependency once the campaign is configured.

---

## PRODUCT 5 — Security Awareness Training (Remote Workshop)

**Invoice name:** *Staff Security Awareness Workshop*

**Exact scope:** one live remote (Zoom/Teams) 60–90 minute session for
up to ~30 staff — phishing recognition, password/MFA hygiene, social
engineering, "how to report a suspected incident" — plus a one-page
handout/slide deck the client keeps.

**Explicitly excluded:** in-person delivery (not offered — see
travel note below), certification/CPD accreditation of the training
itself, more than one session per booking (repeat sessions quoted
separately).

**Duration:** 0.5–1 day prep, 1.5 hours delivery.

**Price:** **AUD $600–$1,200 flat per session**. **[REASONED]** —
same basis as Product 4, no direct AU market quote sourced this
session; positioned as an impulse-purchase price point relative to
Products 1–3.

**Who buys it:** the same SME buyer as Product 4, often purchased
together as a "hygiene package" (Training + Phishing Sim + Policy
Pack).

**Why they buy:** cheapest, fastest-to-schedule visible security
action available; often mandated informally by an insurer or a
larger client's due-diligence process.

**What it requires him to have:** nothing beyond competent delivery —
no cert, no insurance, no licence question.

**First-sale path:** offer one free 20-minute sample session at a
Cairns Chamber of Commerce or local business networking event to
demonstrate delivery quality live, convert attendees to paid bookings.

**Remote from Cairns to UK/EU/US:** **Partially.** Fully deliverable to
UK (Cairns AEST is UK evening/morning depending on daylight saving —
workable). Live delivery to US business hours is difficult from Cairns
(US morning/afternoon = Cairns overnight); offer a pre-recorded version
for US buyers instead, or restrict this specific live-session product
to AU/UK/EU clients.

---

## PRODUCT 6 — Secure Code Review (Fixed Scope)

**Invoice name:** *Secure Code Review — Fixed Scope*

**Exact scope:** manual + tool-assisted review of one defined codebase
slice (e.g. the authentication/authorisation module, payment handling,
or a single API layer), capped at an agreed file/LOC count, delivered
as a findings report referencing OWASP categories with remediation
guidance and code-level examples.

**Explicitly excluded:** the rest of the codebase outside the agreed
slice, architecture redesign work, implementing the fixes (quoted
separately), infrastructure/deployment review.

**Duration:** 2–4 working days, entirely async (git repo access +
written report, no live session required).

**Price:** **AUD $2,000–$4,000 fixed**. Justification: getastra's own
figure (**[FETCHED]**) for white-box/code-informed testing methodology
is "$500–$2,000 per asset" USD, and full pentest engagements run
$5,000–$50,000 USD; a scoped, single-slice code review sits below a
full pentest and is priced accordingly in AUD, adjusted down further
for no track record on the first sales.

**Who buys it:** a small software/SaaS dev shop or a solo/small-team
startup CTO — example company type: a 3–10 person AU or overseas SaaS
startup ahead of an enterprise customer's security due diligence or a
funding round.

**Why they buy:** an investor or enterprise customer's due-diligence
checklist requires "evidence of a security review"; the founding team
has no in-house security person and wants a second pair of eyes before
shipping a sensitive feature (auth, payments).

**What it requires him to have:** nothing beyond competent delivery and
repo-access discipline (read-only access, agreed handling of any
secrets encountered) — no cert, no insurance, no licence question;
this and Product 2 are the cleanest offers on the sheet from a
regulatory-exposure standpoint.

**First-sale path:** list as a fixed-price gig on Upwork/Freelancer
(**[DIRECT_INCOME_ROUTES]** — open sign-up, no vetting gate, but
heavy low-cost overseas competition in "security" categories — undercut
on scope clarity and portfolio proof, not on price) and point directly
at this repository's own test suite (3,600+ tests, structured
epistemic/verification architecture) as demonstrated rigour — a real
artifact, not a claimed one.

**Remote from Cairns to UK/EU/US:** **Yes, entirely** — the single most
naturally async, travel-friendly offer on this sheet: repo access in,
report out, no scheduled call strictly required (though one wrap-up
call is good practice).

---

## PRODUCT 7 — Incident Response Retainer

**Invoice name:** *Incident Response Retainer — Technical Triage*

**Exact scope:** a monthly retainer buying a defined response SLA
(e.g. acknowledge within 24 hours) and a fixed number of hours/month
(e.g. 4) for technical triage of a suspected security incident —
suspected compromise, ransomware, business email compromise — scoped
explicitly as **technical containment/triage advice, not legal or
regulatory advice**.

**Explicitly excluded, and stated on the contract:** Privacy Act 1988
notifiable-data-breach determinations, OAIC reporting decisions, any
legal advice — refer the client to a solicitor for those; overage
hours billed separately.

**Duration:** ongoing, monthly.

**Price:** retainer **AUD $400–$800/month** (4 hrs included), overage
at **AUD $150–$250/hour**. **[REASONED]**: the overage rate is derived
from the PayScale AU pentester salary anchor (**[FETCHED]**,
avg $97,592/yr) — dividing by roughly 1,600 realistic billable
hours/year gives an approximate employed cost-basis near $60/hr, then
marked up 2.5–4x for freelance/contractor margin, a standard freelance
pricing heuristic, not a sourced freelance IR rate. No AU incident-
response freelance rate was found and confirmed this session — treat
this whole price band as a reasoned starting point to test against real
buyers, not a verified market rate.

**Who buys it:** a Cairns/FNQ small business with no in-house IT
security — example company type: a regional medical practice, a small
accounting firm, a tourism operator — wanting "someone to call" without
paying for a managed security service provider contract.

**Why they buy:** a recent industry breach made local news; a cyber
insurance policy now requires a named incident-response contact; a
near-miss already happened and the owner doesn't want to be caught flat-
footed next time.

**What it requires him to have — the honest flag:** **this is the
riskiest offer on the sheet.** Real incident response involves
high-stakes decisions under pressure, potential Privacy Act notification
exposure for the client, and giving advice that, if wrong, causes real
financial harm. Selling this without professional indemnity insurance
is a real personal risk. **Get PI+PL insurance before selling this
one specifically** — BizCover's own quoted combined rate is only
~$81/month (**[OPS_BOARD]**), which is cheap enough that there's no good
reason to sell this particular product without it, even though nothing
found requires it by law.

**First-sale path:** hardest of the eight to sell cold with zero
track record — realistically the **last** product to open, offered
only to an existing client from Products 1, 2, 3, or 6 once at least
one engagement has gone well and there's a real relationship to extend
into a retainer.

**Remote from Cairns to UK/EU/US:** **No — keep this AU-only.** The
"technical triage, refer to a solicitor" scoping relies on Privacy Act
1988 being the applicable law; UK (ICO/UK GDPR) and US (state-by-state
breach law) have entirely different notification regimes he has not
researched, and timezone-dependent on-call commitments don't travel
well to distant markets either. This is the one product on the sheet
that is structurally local.

---

## PRODUCT 8 — Vulnerability Disclosure Programme (VDP) Setup

**Invoice name:** *Vulnerability Disclosure Programme Setup*

**Exact scope:** stands up a basic VDP for a small software vendor —
a `security.txt` file, a written disclosure policy (scope, safe-harbour
language, response-time commitment), a triage workflow using free
tooling (a dedicated inbox or a free-tier reporting form), and a short
guide on how to respond to an incoming report.

**Explicitly excluded:** ongoing triage of reports after handover
(quoted separately as a retainer if wanted), any paid managed-VDP
platform subscription (client's choice and cost if they want one later),
actual vulnerability remediation.

**Duration:** 1–2 working days.

**Price:** **AUD $1,000–$2,000 flat**. **[REASONED]** — priced between
Product 3 (pure documentation, cheaper) and Product 2 (interview-driven
gap analysis, more expensive), no direct source found for VDP-setup
pricing specifically.

**Who buys it:** a small SaaS or software vendor whose enterprise
customer's security questionnaire asks "do you have a vulnerability
disclosure programme?" and the honest current answer is no.

**Why they buy:** exactly that questionnaire moment — it's a checkbox
they're currently failing with no budget for a managed Bugcrowd/
HackerOne programme.

**What it requires him to have:** nothing beyond ABN and competent
technical writing — no cert, no insurance, no licence question.

**First-sale path:** bundle with Product 3 (Policy Pack) as a combined
"governance readiness" offer for the first client; alternatively build
one for free on a real open-source project he's already engaged with as
a visible before/after portfolio piece — this repo's own posture is
already public-facing, so pointing at a genuine example (not a
fabricated one) is available if one exists.

**Remote from Cairns to UK/EU/US:** **Yes, entirely.**

---

## SUMMARY TABLE

| # | Product | Price (AUD) | Cert/insurance needed? | Remote to UK/EU/US? | First-sale difficulty |
|---|---|---|---|---|---|
| 1 | Web App Security Review | $2,500–$6,000 | No (insurance strongly advisable) | Yes | Medium — cold local outreach |
| 2 | SOC2/ISO27001 Readiness Gap Analysis | $3,000–$6,000 | No | Yes — best-suited offer | Medium — LinkedIn/Upwork |
| 3 | Security Policy Pack | $500–$3,000 | No | Yes (research UK/US law gaps first) | Easy — Gumroad self-serve |
| 4 | Phishing Simulation | $800–$1,500 | No (written consent mandatory) | Yes | Easy — bundle with #3/#5 |
| 5 | Awareness Training | $600–$1,200 | No | Partial (UK yes, US live hard) | Easy — free sample session |
| 6 | Secure Code Review | $2,000–$4,000 | No | Yes — most travel-friendly | Medium — Upwork w/ portfolio |
| 7 | Incident Response Retainer | $400–$800/mo | **Insurance strongly advised** | **No — AU only** | Hard — needs prior client |
| 8 | VDP Setup | $1,000–$2,000 | No | Yes | Easy — bundle with #3 |

**Sequencing recommendation, not part of the priced sheet:** sell 3
and 6 first (cheapest regulatory exposure, easiest to prove with this
repo's own test suite as evidence), use the first paying client as the
reference for 1 and 2, buy PI+PL insurance (~$81/month, trivial cost)
before attempting 7, and get the Queensland OFT licensing question
answered in writing before ever using the words "penetration test" on
an invoice for any of the above.
