# AU Panel Application Checklist — Operator: solo trader, Cairns QLD, ABN held, no certs, no insurance, no staff

Builds on `docs/DECISIONS/D-008-australian-retry.md` (reachability already
proven — not re-tested here). This file is APPLICATION MECHANICS only,
read directly off primary-source documents on 2026-09-02. Every quoted
figure below was read from the cited document/page, not inferred.

Ranked order to execute, this week: **NSW ICT Services Scheme first**
(cheapest barrier, no insurance-in-hand required to apply), **QLD
Supplier Portal + QTenders** second (free, no panel gate, but needs
active monitoring — do in parallel, costs nothing), **ICN Gateway**
third (free tier has a real limitation — see below), **insurance
shopping** as a background task this week regardless, because NSW
requires it before *contracting*, not before *joining*.

---

## PART 1 — NSW ICT Services Scheme (SCM0020) — DO THIS FIRST

Primary sources fetched and read directly (not summarised from memory):
- Scheme Rules v2.2, August 2023 — `https://www.info.buy.nsw.gov.au/__data/assets/word_doc/0005/589136/ict-services-scheme-rules-august-2023_v2.docx`
- Summary of ICT Services Scheme Membership Requirements, September 2024 — `https://www.info.buy.nsw.gov.au/__data/assets/word_doc/0003/1325793/Summary-of-ICT-Services-Scheme-Membership-Requirements.docx`
- Scheme info page — `https://www.info.buy.nsw.gov.au/schemes/ict-services-scheme`

### 1.1 Steps, in order

1. **Create a buy.nsw Supplier Hub profile first** — a scheme
   application cannot be started without one. Register at
   `https://suppliers.buy.nsw.gov.au/login`. Quoted from the Scheme
   Rules: *"Entities must have a current Supplier Hub profile on the
   buy.nsw website, before applying to the ICT Services Scheme."*
   Requires an ABN and standard company/organisation details (the
   Supplier Hub itself does not publish a longer checklist than this —
   name, ABN, contact details, business description).
2. **Wait for the Supplier Hub profile to be approved.** Quoted: *"Once
   an entity's Supplier Hub profile is approved, they may apply for the
   ICT Services Scheme."* No published timeframe found for this step
   specifically — treat as a genuine unknown until you do it.
3. **Start the scheme application from the Supplier Dashboard**: log
   in, go to "schemes module," scroll to "ICT Services Schemes," click
   "see details," start the application.
4. **Choose Registered Supplier list** (not Advanced — Advanced is for
   contracts over $150,000 ex GST or high-risk work; Registered covers
   *"total value of up to $150,000 (ex GST) and low risk"* per the
   Scheme Rules — matches D-008's already-established finding).
5. **Select category K03** (see Part 1.5 below) plus any other relevant
   categories — you can apply for as many as you meet the requirements
   for.
6. **Submit the required information** (exact list, quoted from Scheme
   Rules §8.1, Registered-tier column only):
   - Organisation details including ABN.
   - Company Capacity and Capability document: recent relevant
     experience, certification details "where applicable" (none held —
     this is not a blocking field, just leave/note as not applicable),
     qualifications/experience of key personnel where applicable.
   - **Two (2) referee reports for the nominated high-level category**
     — same two referees can cover multiple categories. This is the
     one real friction point for someone with "no corporate references"
     — see 1.6 below.
   - Confirmation you are financially solvent, not subject to
     insolvency/ICAC proceedings, and able to pay debts when due.
   - A Rate Card (exempt if you are supplying ICT Consulting Services
     only).
   - Agreement to use the ICT Purchasing Framework (PBD 2021-02) and
     the ICT Consulting Standard Commercial Framework.
   - A Supplier Declaration (standard authorisation/accuracy
     attestation).
7. **Submit.** You will be notified by email of the outcome.

### 1.2 Insurance — what must be in place, and when

Quoted directly from the Scheme Rules, §8.2, **Registered** column:

| Insurance | Registered Supplier |
|---|---|
| Professional indemnity insurance | **$1,000,000** |
| Public Liability | **$5,000,000** |
| Workers compensation | required where applicable by law |

Critical timing fact, quoted from the Summary document (this is the
part that removes insurance as a blocker to *applying*):

> "Suppliers are not required to provide proof of insurances to join
> the ICT Services Scheme, but rather must agree to have minimum
> insurances in place... before entering into an agreement with NSW
> Government."

And, directly answering the SME case:

> "I am a Small to Medium Enterprise (SME) supplier and I am unable to
> obtain the minimum insurance requirements stated in the ICT Services
> Scheme Rules. Can I still apply to join the ICT Services Scheme? Yes,
> SMEs are encouraged to apply... As an SME, you do not need to provide
> proof of your insurances until during contract award with the NSW
> Government, as per **PBD 2023-03**."

**Practical read for this operator: apply now with no insurance held.**
You only need the $1M PI / $5M PL in hand at the point you are actually
awarded a contract, not to register. This gives real lead time to shop
for and bind a policy (see Part 4) once — and only once — a live
opportunity appears.

### 1.3 Assessment time and fee

- **No application fee found anywhere in either document.**
- Timeframe is stated slightly differently in the two documents (quoted
  exactly as found, not reconciled/rounded):
  - Summary doc: *"It usually takes us one to 2 weeks to process an
    application"* and elsewhere *"maximum expected processing time...
    is 14 business days, but most applications are assessed within 2-3
    business days."*
  - Scheme Rules §9: *"Applicants will be notified by email within 15
    business days."*
  - Treat **up to 3 working weeks** as the safe planning figure; expect
    faster in practice per the Summary doc's own stated median (2-3
    business days).

### 1.4 The scheme is mandatory-use — this matters for the operator

Quoted: *"NSW Government agencies must use the suppliers registered on
the ICT Services Scheme to buy ICT/digital products and services."* An
NSW agency legally cannot engage you for ICT/security work outside this
scheme once it exists — meaning registration is not optional if any
NSW-government security work is ever wanted, it is the only door.

### 1.5 Category — exact label for penetration testing / security work

18 named categories exist (Tab A of the Scheme Rules). The relevant one,
quoted verbatim:

> **"Category K – Security management"**
> - **K01 Security strategy including delivery "as a service"** — create
>   strategy, architecture, solutions and services; security audits,
>   vulnerability assessments; supporting/maintaining ISO 27001
>   certification.
> - **K02 Security management security and firewall installation
>   including delivery "as a service"**
> - **K03 Security testing including delivery "as a service"** —
>   *"Undertake various security testing including, penetration
>   testing, web security testing, secure code reviews, security and
>   environment testing meets agreed standards."*
> - **K04 Security and firewall management including delivery "as a
>   service"**

**Apply for K03 specifically** — it is the exact label that names
penetration testing. K01 is worth adding too if strategy/audit work is
also wanted, since categories are additive (apply for as many as
qualify).

### 1.6 The referee-report problem (the one real gap for this operator)

Two referee reports per nominated high-level category are required, and
the operator has "no corporate references." This is a genuine open
blocker not solved by this research — the Scheme Rules do not define
what counts as an acceptable referee (a private-sector client reference
may well qualify; nothing found restricts it to government or corporate
referees specifically). **Action needed from the operator, this week:**
identify two people who can act as referees for security/IT work
already performed (even non-government, even informal contracting) —
this is the one input only the operator can supply; do not treat it as
disqualifying without first checking the actual referee-report form
(only visible after Supplier Hub login).

### 1.7 How work actually arrives once registered

Quoted from the scheme info page: *"NSW Government agencies and other
eligible customers can contact suppliers directly, or invite and assess
supplier proposals using eTendering or their agency's own procurement
system."* Two real mechanisms, confirmed by the Summary doc:

1. **Passive/searchable**: keep the Supplier Hub profile complete and
   tagged (e.g. SME) — buyers search it directly for suppliers matching
   a category.
2. **Active/published**: the **buy NSW Opportunities Hub** lists current
   tenders/opportunities suppliers should actively check and respond to
   — registration alone does not generate income; the Opportunities Hub
   needs to be checked regularly.

There is also a formal "limited tendering" path (Scheme Rules §14): for
EPP-covered procurements, agencies must invite a minimum of **three**
registered suppliers from the category — being registered in K03 is a
precondition to being one of those three, not a guarantee.

**No guarantee of supply** is stated explicitly in the Scheme Rules
(§20) — registration is eligibility, not a pipeline.

---

## PART 2 — Queensland: no panel, but two portals, and active monitoring required

Sources: `https://www.business.qld.gov.au/running-business/marketing-sales/tendering/supply-queensland-government/buying-categories/general-goods-services`,
`https://www.supply.qld.gov.au/`.

### 2.1 The Supplier Portal (register here — free)

`https://www.supply.qld.gov.au` runs on **VendorPanel Marketplace**
(a Queensland Government / Local Buy partnership — covers both state
and local-council opportunities in one profile). Steps, quoted from the
page:

1. Go to VendorPanel Marketplace.
2. Search and select your supply categories.
3. Register as a supplier and request invitation.
4. Receive a "get started" email from VendorPanel.
5. Verify the account via the email link, then complete registration
   (business info, service regions).

No fee found. Confirms D-008's existing finding: **QLD has no panel
acceptance gate** — this is registration/discoverability, not
prequalification.

### 2.2 Where opportunities actually appear — three separate feeds

Registering on the Supplier Portal does **not** by itself put you in
front of buyers automatically — Queensland buyers are stated to use a
separate directory to find pre-qualified panels rather than searching
individual profiles. Three places to actually watch:

- **QTenders (current opportunities)**: `https://qtenders.hpw.qld.gov.au/`
  — matches D-008's route #6 (reachable, Blazor SPA, no gate).
- **Forward Procurement Pipeline (upcoming tenders)**:
  `https://qtenders.hpw.qld.gov.au/fpp/` — lets you see what's coming
  before it opens, useful for a solo operator planning capacity.
- **Queensland Government Arrangements Directory (existing panels)**:
  `https://qgad.epw.qld.gov.au/` — this is what buyers reportedly check
  first for pre-qualified suppliers; worth checking whether a
  cyber/security panel already exists here that the operator could
  register against, separate from ad hoc QTenders opportunities.

### 2.3 Support contact if the online flow breaks

`bsu@hpw.qld.gov.au` or `(07) 3215 3588` — the human fallback if
VendorPanel registration hits an obstacle the site doesn't explain.

### 2.4 What this route needs from the operator

Register on Supplier Portal (free, ~15 minutes), then set a **recurring
weekly check** of QTenders + FPP for security/penetration-testing
tenders — this is the "follow-up" D-008 already flagged as the
condition for QLD to generate income, not registration alone.

---

## PART 3 — ICN Gateway

Source: `https://gateway.icn.org.au/faq`, corroborated by
`https://gateway.icn.org.au/join` and public pricing pages (see caveat
below).

### 3.1 Registration steps

1. Go to `https://gateway.icn.org.au/join`, click "Join Now."
2. Choose a subscription package (see 3.2 — this matters, don't
   default to free without reading it).
3. Enter ABN — profile auto-populates from the Australian Business
   Register; quoted: for a recently-registered ABN *"allow 5-7 business
   days for us to process the data"* since ICN pulls from ABR weekly.
4. Complete company profile: business summary (first sentence is
   described as the most important — should state what the company
   does), keywords/products/services, categories, contact details.
5. Submit — profile review takes ~24 hours; business-detail changes
   are separately verified by state consultants, taking 1-2 business
   days.

### 3.2 The real catch: free tier is not discoverable

Quoted directly: *"If you are a Limited subscriber your profile will
not appear in the search result."* The free ("Limited") tier lets you
download tender documents and submit Expressions of Interest, but a
head contractor searching Gateway for a subcontractor **will not find
you** on the free tier. Two paid tiers exist that add search visibility
and a capability-statement feature — **figures below came from a
general web search summary, not a directly fetched ICN pricing page,
so treat them as unverified until confirmed on `gateway.icn.org.au`
itself at signup**: reported as roughly $600/year ("Be Compelling") and
$1,480/year ("Premium"). **Action needed: confirm actual current price
on the ICN site during signup before relying on this figure** — this is
a real cost previously undocumented in D-008, which called ICN "free
registration" without checking the discoverability caveat.

### 3.3 What this route is, honestly

Subcontracting exposure (express interest in a head contractor's
already-won project), not direct government contracting — matches
D-008's existing framing. Lowest effort to register, but the "free"
label needs qualifying: free to sign up and browse/apply, not free to
be found.

---

## PART 4 — Insurance: real indicative cost, and the gap that's still open

Source fetched directly: `https://www.bizcover.com.au/it-professional-professional-indemnity-cost/`
(BizCover, dated April 2025 per the page itself).

Quoted/extracted figures:
- Professional indemnity only, sole trader, annual revenue up to
  $50,000: **from $43/month** (~$516/yr).
  Revenue $50,001–$250,000: also **~$43/month**.
  Revenue $500,000+: **~$60+/month**.
- **Combined PI + Public Liability, sole traders: average $81/month**
  (~$972/yr).
- A separate, less-authoritative web-search compilation (not directly
  fetched from a single primary page — treat as lower confidence)
  suggested a freelance IT consultant on ~$140k turnover, seeking $1M
  PI with a $1,000 excess, was quoted **$800–$1,100/year**.

### The real gap this cycle did not close

Every figure found is for policies around the **$1M PI** mark — the
level NSW's Registered tier requires for PI. **None of the fetched
sources gave a price specifically for $5M public liability** (the NSW
Registered-tier PL requirement) as opposed to the more commonly quoted
$1M–$2M PL policies bundled with PI. $5M PL is a materially larger
policy and could cost meaningfully more than the combined $81/month
figure above, which is almost certainly quoted against a lower PL
limit. **This is a named blocking unknown**, not guessed at:

**Action needed from the operator, or a follow-up cycle**: get an
actual quote from an Australian broker/insurer (BizCover, Finder-listed
insurers, or a direct broker) for the specific combination **$1M PI +
$5M PL**, sole trader, IT/cyber-security consulting, Cairns QLD. This
determines the real annual cost of being contract-ready for NSW's
Registered tier and is a number this research could not source without
requesting a personalised quote (which requires supplying real business
details to a third party — a genuine human decision point, not
something to fabricate a placeholder figure for).

---

## SUMMARY — do this, this week, in order

1. **Today**: register a buy.nsw Supplier Hub profile
   (`https://suppliers.buy.nsw.gov.au/login`).
2. **Today**: register on QLD Supplier Portal
   (`https://www.supply.qld.gov.au`) — free, ~15 min, no gate.
3. **This week, once Supplier Hub is approved**: submit the NSW ICT
   Services Scheme Registered-tier application for category **K03**
   (add K01 if relevant), with the two referee reports — **identify the
   two referees now**, this is the one step needing the operator's own
   judgment/network, not more research.
4. **This week**: get an actual insurance quote for $1M PI + $5M PL,
   sole trader IT/security consulting — needed before any NSW contract
   can be signed, and useful to know the real number even before that
   point.
5. **Ongoing, weekly**: check QTenders (`qtenders.hpw.qld.gov.au`) and
   the Forward Procurement Pipeline for security-related tenders; check
   the buy NSW Opportunities Hub once the scheme application is
   submitted.
6. **Optional, lower priority**: ICN Gateway free "Limited" signup is
   harmless but will not surface you to buyers — only worth the $600+/yr
   paid tier once there's a validated reason to chase subcontracting
   leads specifically (confirm actual current price at signup first).

## NAMED BLOCKING UNKNOWNS (not fabricated, explicitly open)

- Real cost of **$5M public liability** specifically (see Part 4) — no
  source found priced this exact limit.
- Whether a **non-corporate/non-government referee** (e.g. a private
  client) satisfies NSW's "two referee reports" requirement — the
  referee-report form itself is only visible after Supplier Hub login,
  not published on the public info pages.
- Supplier Hub profile **approval timeframe** before the scheme
  application can even start — not stated in either fetched document.
- ICN Gateway's **current paid-tier pricing** — sourced from a
  web-search summary, not a directly fetched ICN page; confirm at
  signup.
- Whether a security/pentest panel already exists on the **QLD
  Arrangements Directory** (`qgad.epw.qld.gov.au`) that would be a
  faster route in than ad hoc QTenders — not checked this cycle.
