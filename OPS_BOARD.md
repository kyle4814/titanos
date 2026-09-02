# OPS BOARD — every live opportunity, what it's worth, what it needs

Compiled 2026-09-02, last re-swept 2026-09-03. Every figure here was
read off a primary source during this campaign, not recalled. Where
something is unknown it says UNKNOWN — that is a real state, not a gap
someone forgot to fill.

**Operator profile this board is scored against:** solo trader, Cairns
QLD, has an ABN, **no certifications** (no OSCP/CREST/GIAC/CISSP), **no
professional indemnity or public liability insurance**, **no corporate
reference contracts**, no employees, English only. Australia is a WTO
GPA party (since 5 May 2019), so nationality is not a barrier anywhere
below.

---

## TIER 1 — open today, no credential gate, no deadline

These need nothing you do not already have. None has a closing date,
which is exactly why they are the ones that quietly never get done.

### 1. ZDI (Zero Day Initiative) — pays cash for vulnerabilities, year-round

| | |
|---|---|
| **Value** | Per-vulnerability. Range varies by target class; see their published table |
| **Gate** | None. Open globally to individuals |
| **Excluded countries** | Cuba, Iran, North Korea, Sudan, Syria. **Australia is not excluded** |
| **Deadline** | None — standing market |
| **Cost to enter** | Free |
| **URL** | zerodayinitiative.com |

The purest capability-for-cash market found in this entire campaign. No
company, no licence, no insurance, no references, no interview.

**It is also the prerequisite for the big prizes** — see Pwn2Own Ireland
below, which requires $15,000 already earned through ZDI.

**ACTION:** register a researcher account. Free, no deadline, no risk.

**UNKNOWN:** the non-US tax form for payouts is not stated on their FAQ
(only W-9 for US taxpayers is confirmed). Ask them at signup.

---

### 2. ADB Consultant Management System — the modality built for people

Every barrier on this board — €13,000,000 employer's liability,
€2,600,000 turnover, three corporate references — exists because the
buyer was procuring from a **firm**. Development banks run a separate
track for procuring from a **person**, and it does not carry those
requirements because there is no company to carry them.

**What I verified myself, 2026-09-03:**

| | |
|---|---|
| `cms.adb.org` | **live, HTTP 200, publicly reachable** |
| robots.txt | permits it — only `/admin/`, `/user/`, `/search/` disallowed |
| Registration | open: *"Don't have an account yet? Register here."* |
| Menu | Consulting Opportunities · Shortlisted Firms · Awarded Contracts |
| **Australia's ADB membership** | **1966** — quoted from ADB's own members page |
| ADB founded | 1966, with 31 members. **So Australia is a founding member.** |
| Members today | 69 |

**What I could NOT verify, and it is the load-bearing part.**

A research pass reported ADB's individual-consultant eligibility as
*"a citizen of an ADB member country, not barred, not a close relative
of an ADB staff member"* — with no incorporation, insurance, turnover or
reference requirement. If accurate that is the single most important
finding of this campaign.

**I could not confirm it.** Every CMS path — the registration page, the
terms page, the opportunities listing — returns the same 14,518-byte
shell, because CMS is a JavaScript application that routes client-side.
The rule is real or it is not; static fetch cannot tell you which, and
neither can I.

It is recorded here as **UNVERIFIED** rather than promoted to the top of
the board, because a wrong eligibility claim is exactly the error that
produced a false QUALIFIED on ECHA earlier in this campaign — and that
one cost a €1,000,000 turnover clause hiding in plain sight.

**ACTION, and it is small:** open `cms.adb.org` in an ordinary browser
and click Register. The form itself states what it requires. Ten minutes
answers whether the biggest structural opening found in nine cycles is
real.

**Related, same class, same unresolved status:** UNGM's registration
reportedly offers "Individual Consultant" and "Sole proprietor" account
types with no incorporation requirement. UNOPS's Individual Contractor
Agreement, the World Bank's individual-consultant track and the EU
expert roster are all JavaScript applications that static fetch cannot
read. All four are reachable and unblocked — none is confirmed.

---

### 2. NZ Government Marketplace — all-of-government IT, open to 2029, international

Found 2026-09-03 by the new notice classifier, which is the only reason
it surfaced: it had been sitting in every NZ sweep since the start,
scoring `INSUFFICIENT_DATA` alongside 324 other notices.

| | |
|---|---|
| **Buyer** | Department of Internal Affairs |
| **Type** | Invitation to Participate (ITP) |
| **Coverage** | **All of Government** |
| **Open** | 25 March 2026 → **closes 25 May 2029** |
| **Categories** | 43000000 Information Technology · **81110000 Computer services** · 81160000 IT service delivery |
| **Regions** | **International** |
| **Required Pre-qualifications** | **None** |
| **URL** | gets.govt.nz//DIA/ExternalTenderDetails.htm?id=33732411 |

Read that row set again. An **all-of-government** IT marketplace, in
**computer services**, explicitly **international**, with
**pre-qualifications stated as None**, open for another **two years and
eight months**.

It is the New Zealand analogue of the NSW ICT Services Scheme — except
NZ states the international eligibility outright, and NZ's procurement
rules already confirm they *"do not discriminate against suppliers
(domestic or international)"* under the Australia New Zealand Government
Procurement Agreement.

**No deadline pressure, no credential gate published, and a buyer that
covers every NZ government agency.**

**THE APPLICATION CRITERIA, read 2026-09-03 from marketplace.govt.nz.**
The channel open for application is literally **Managed Security
Services** (alongside Infrastructure and Telecommunications). Quoted:

> *"accept the Collaborative Marketplace Agreement terms"*
> *"be an active and legitimate business"*
> *"be financially viable to provide the services applied for"*
> *"have in place appropriate insurance provisions"*
> *"should not be involved in disputes or legal proceedings"*
> *"demonstrate relevant experience in the services they applied for"*
> *"demonstrate relevant capability and capacity to provide services"*
> *"provide required security information"*

**No turnover threshold. No insurance amount. No certification named. No
reference count.** Compare to Ireland, where four of five buyers wanted
€13,000,000 employer's liability and three reference contracts, and
turnover ran €400,000 to €2,600,000.

And the buyer's own framing of the whole scheme:

> *"The Marketplace simplifies how the NZ Government buys ICT and lowers
> the barriers for suppliers to provide us with services — in short, the
> Marketplace makes it easier for suppliers — large and small — to do
> business with government."*

**What is still genuinely UNKNOWN, and matters:**

- *"appropriate insurance provisions"* names no figure. Undefined is not
  absent — it could still mean $5M public liability at contract stage.
- *"demonstrate relevant experience"* names no threshold. This is the
  clause most likely to bite, and it is the same shape as the referee
  question outstanding at NSW.
- The detailed security documents (Marketplace Information Security
  Tiering Standard, GCDO Continuous Security Certification Controls
  Validation Plan, and four scoping templates) are **only available
  after registration begins.** They are listed on the GETS notice as
  attachments, so they exist and they are substantial.
- **Whether a sole trader may apply is not stated either way.** The
  criteria say "business" and "company" without defining or excluding.
  UNKNOWN, and worth one email.

**THE APPLICATION QUESTIONS ARE BEHIND A FREE ACCOUNT — a human step.**
The GETS notice lists its attachments, and one is literally *"Standing
Notice of Procurement: Appendix 2: The I/TMS Application questions"* —
the exact document that would answer what the application asks. On the
anonymous page every attachment link routes through
`TendererLogin.auth`. That is a supplier account, not a paywall and not
a block: free to create, and this cycle will not create one because
account creation is yours, not mine.

**Ten minutes with a GETS account gets you the actual application
questions, the Information Security Tiering Standard, and the four GCDO
certification scoping templates.** Everything currently marked UNKNOWN
above is inside those files.

Contact published on the notice: `marketplace@dia.govt.nz`, and their
own site currently warns *"Due to high demand, it may take us longer
than usual to process applications"* — which is a live scheme, not a
dormant one.

Also live, same class, same buyer type:

- **All-of-Government Construction Consultancy** — Standing Open
  Invitation, MBIE, closes 30 Sep, pre-qualifications None. Wrong
  category for you, listed only because it confirms the pattern: NZ runs
  several of these standing invitations and they recur.

---

### 2. NSW ICT Services Scheme (SCM0020) — $150,000 contract ceiling

| | |
|---|---|
| **Value** | Contracts up to **$150,000 ex GST** at the Registered tier |
| **Gate** | An ABN. That is the hard requirement |
| **Turnover** | **Not an acceptance criterion** — quoted from their own FAQ: *"It is requested for informational purposes but does not form part of the acceptance criteria"* |
| **Insurance** | $1M PI / $5M PL required **before entering an agreement, NOT to join**. PBD 2023-03 exempts SMEs from proving it until contract award |
| **Deadline** | None. Always open |
| **Fee** | None |
| **Assessment** | 2–3 business days typical, up to 14–15 maximum (the two source documents disagree; both figures quoted, neither averaged) |
| **Category** | **K03 "Security testing"** — the exact label covering penetration testing, web security testing, secure code review |

**THE ONE BLOCKER:** Scheme Rules §8.1 requires **two referee reports**
per nominated category.

**But that blocker may not be real.** §8.1's full text on referees is
*"two (2) referee reports for each nominated high-level category"* — and
that is the **entire** mention of referees in the Rules and the FAQ,
both fetched and full-text searched. **"Referee" is never defined.**
Nothing restricts it to paying customers, government agencies, or
corporate clients. That restriction was our assumption, not their rule.

No new-entrant or start-up waiver exists (full-text searched, zero hits).

**ACTION:** email `ICTServices@customerservice.nsw.gov.au` and ask
whether a documented pro-bono engagement qualifies as a referee. One
email resolves the only thing standing between you and a $150k ceiling.

**Still outstanding for this scheme (5 facts, all yours):** ABN, declared
service skills, two referee reports, Supplier Declaration signature,
financial solvency confirmation.

---

### 3. ICN Gateway — no reference gate at all

| | |
|---|---|
| **Value** | Subcontracting exposure, not prime contracts |
| **Gate** | **Zero reference requirement.** ABN at signup (auto-populates from ABR) |
| **Deadline** | None |
| **Cost** | Free tier exists — **but** the "Limited" free tier does **not appear in buyer search results**. Discoverability needs a paid tier, reported ~$600–$1,480/yr |
| **URL** | gateway.icn.org.au |

**Confidence note:** the pricing figure was not fetched from ICN's own
pricing page and is lower-confidence. Confirm at signup.

**ACTION:** this is the route you can finish today without waiting on
the NSW referee answer. 2 facts outstanding: ABN, declared skills.

---

### 4. Queensland — no panel gate whatsoever

QITC has **no panel or accreditation gate**. Contracting is direct,
per-engagement, through QTenders.

**The catch, and it is a real one:** registering on the Supplier Portal
alone does not generate leads. Buyers reportedly check the Arrangements
Directory (`qgad.epw.qld.gov.au`), which is separate from QTenders and
needs active weekly monitoring.

**2 facts outstanding:** declared supply categories, business info and
service regions.

---

### 5. UK Crown Commercial Service — Cyber Security Services 3 DPS

| | |
|---|---|
| **Value** | £800,000,000 total DPS spend |
| **Open until** | **13 February 2029** — a DPS admits new suppliers throughout its life |
| **To join** | Selection Questionnaire + DPS Questionnaire |
| **Where** | supplierregistration.cabinetoffice.gov.uk/dps |
| **Turnaround** | 10 days |
| **Certification to join** | **None** |

Certification gates the **filters**, not entry — and one filter category
is explicitly **"Non-certified NCSC Services"**. That category exists for
suppliers in exactly your position.

A web claim that "Cyber Essentials is now baseline" was checked, could
not be sourced, and was discarded rather than repeated.

**3 facts outstanding:** DPS Schedule 1 filter selection (a human must
read the real document — we would not guess), SQ financial details,
declared service skills.

---

## TIER 2 — live, dated, act within weeks

### 6. City of Bradford MDC — penetration testing framework ⏰ 11 DAYS

| | |
|---|---|
| **Value** | **£300,327** |
| **Deadline** | **2026-09-14 16:00 UTC** |
| **Procedure** | Open Framework under the Procurement Act 2023 |
| **Award** | Council intends to appoint the **top 3 providers** |
| **Scoring** | Quality 40 / Social Value 10 / Price 50 |
| **Work** | 10-day consultancy packages, NCSC and OWASP standards |
| **Notice** | 2026/S 000-078110 |

**The notice states only that it seeks "a suitably experienced and
qualified Provider"** — no turnover, insurance, certification, staffing
or reference threshold appears anywhere in its text.

**DO NOT read that as clear.** PSN IT Health Check work is conventionally
performed by **CHECK-scheme accredited** testers, and that requirement
would sit in the tender documents rather than the notice. This is
**unresolved**, not cleared.

**ACTION — needs your browser, ten minutes:** the submission portal is
`uk.eu-supply.com` and it is **session-cookie-gated, not WAF-blocked**,
which means a human browser gets in where an automated fetcher cannot.
Open it, find the CHECK/CREST answer, and tell me. This is the
highest-value live item on the board.

---

### 7. Ireland — two RESOLVED (both no), three still open

**2026-09-02 overnight: the documents are now readable.** eTenders'
document pages offer **"Proceed without association"** — anonymous
download is an option the site itself provides, not a control worked
around. The static path is
`/epps/cft/downloadContractDocument.do?documentId=<id>&resourceId=<id>`,
recovered by reading (never executing) the page's own JavaScript.

That closes the two biggest Irish notices with quoted evidence.

#### ❌ Health & Safety Authority — €900,000, closes 12 Oct — CANNOT APPLY

> *"Tenderers will either pass OR fail each of the Selection Criteria in
> this part 3.2. A Tenderer who fails a selection criterion will be
> excluded from participation."*

| Requirement | Threshold | You |
|---|---|---|
| Annual turnover, auditor-signed | **€1,800,000** | ✗ |
| Employer's Liability | €13,000,000 | ✗ |
| Public Liability | €6,500,000 | ✗ |
| Product Liability | €6,500,000 | ✗ |
| Professional Indemnity | €1,000,000 | ✗ |
| Cyber Security insurance | €2,500,000 | ✗ |
| Reference contracts | **3 of similar value, last 3 years** | ✗ |
| Bank letter confirming good standing | required | ✗ |

#### ❌ Fáilte Ireland — €800,000, closes 24 Sep — CANNOT APPLY

Section A is explicitly **"PASS/FAIL CRITERIA"** with a **"MINIMUM RULE
/ ELIMINATOR"**. Reference `IT/2026/08`, 3-year contract.

| Requirement | Threshold | You |
|---|---|---|
| Turnover, any of previous 3 financial years | **€400,000** | ✗ |
| Employer's Liability | €13,000,000 | ✗ |
| Public Liability | €6,500,000 | ✗ |
| Professional Indemnity | €2,000,000 | ✗ |
| Cyber Liability | €5,000,000 | ✗ |
| Reference contracts | **3 in last 3 years, similar scope, scale and complexity** | ✗ |

**ONE GENUINELY USEFUL CLAUSE, quoted verbatim:**

> *"NOTE #1: in the case of the Candidate being a grouping, the condition
> at (i) above may be satisfied by the group members as a whole."*

**Turnover can be met by a consortium as a whole.** That is written into
the rules, not inferred. It does not make you eligible alone — the
insurance and reference bars still apply to the grouping — but it is the
first explicit, quoted confirmation in this entire campaign that
**joining a group is a sanctioned route into contracts you cannot reach
solo.** It reframes the subcontracting lane from a workaround into a
procurement mechanism the buyer names itself.

#### ❌ An Post — SOC/SIEM, closes 29 Sep — CANNOT APPLY

Tender ref `0055`. Sections 2.1 Turnover, 2.2 Insurance, 2.3 Tax
Clearance and 2.4 Going Concern are each marked **(PASS/FAIL)**, plus
References 1, 2 and 3.

> *"TURNOVER (exclusive of VAT): A minimum annual turnover of one million
> euro (€1,000,000.00) per annum for any two of the last three financial
> year ends."*

Insurance limits: €13,000,000 / €6,500,000 / €2,600,000 / €3,000,000.

**But this one hands you the consortium route on a form field:**

> *"In the case of a consortium, the turnover threshold must be met by the
> combined annual turnover of all members of the consortium for any two
> of the last 3 audited financial year end."*

> *"Tick to confirm if Applicant is relying on combined turnover of
> consortium members or those of any other persons/entities, in order to
> meet the minimum financial qualification..."*

There is a **checkbox on the PQQ** for exactly this. Third independent
confirmation, and the most explicit.

#### ❌ Department of Justice — national PKI, closes 2 Oct — CANNOT APPLY, but closest yet

Contract up to €2,000,000; initial phase €450,000–€700,000.

| Requirement | Threshold | You |
|---|---|---|
| Turnover, each of last 3 years | **€800,000** | ✗ |
| Employer's Liability | €12,700,000 | ✗ |
| Public Liability | €6,500,000 | ✗ |
| Professional Indemnity | €1,000,000 | ✗ |
| Reference | PKI delivery **> €50,000** | ✗ |

**Two things make this the most solo-friendly document found anywhere:**

> *"Applicants must demonstrate access to at least the minimum numbers of
> skilled personnel stated. **Please note that the skills outlined may
> reside in the same person.**"*

A buyer explicitly accommodating one person holding several skills — the
opposite of degewo's "minimum 3 penetration testers". And the reference
bar is **€50,000**, against €100,000-and-similar-value elsewhere.

It still fails on turnover and insurance. But it proves the personnel
requirement is not universally a headcount test, and it is worth
watching this buyer for smaller future work.

#### ❌ Houses of the Oireachtas — closes 28 Sep — CANNOT APPLY, hardest of the five

Tender ref `2026/1021`, 88-page RFT, now parsed.

> *"Tenderers are required to demonstrate that they have a minimum
> average annual turnover of €2,600,000 (excl. VAT) in each of the last
> three financial years. Failure to demonstrate the minimum required
> turnover will result in the tenderer being eliminated from the
> competition."*

| Requirement | Threshold |
|---|---|
| Minimum average annual turnover, each of last 3 years | **€2,600,000** |
| Employer's Liability | €13,000,000 |
| Public Liability | €6,500,000 |
| **Professional Indemnity** | **€10,000,000 in aggregate** |
| Cyber Liability (incl. loss of data) | €5,000,000 |
| Evidence | Banker's statement within 6 months + 3 years audited accounts |

The highest turnover bar and the highest professional indemnity of any
notice assessed in this campaign — €10m PI against €1–2m elsewhere.

Award is 55% weighted on functional and technical merit (SIEM platform
management, SOC threat detection and response, incident response
retainer), which is genuine capability scoring — but you never reach it,
because §3.2 eliminates first.

---

### What five Irish documents establish

Five notices, five independent sources, one consistent shape:

| Buyer | Turnover | Employer's Liability | Prof. Indemnity | References |
|---|---|---|---|---|
| Oireachtas | €2,600,000 | €13,000,000 | €10,000,000 | prev. contracts |
| HSA | €1,800,000 | €13,000,000 | €1,000,000 | 3 |
| An Post | €1,000,000 | €13,000,000 | — | 3 |
| Dept of Justice | €800,000 | €12,700,000 | €1,000,000 | 1 × >€50k |
| Fáilte Ireland | €400,000 | €13,000,000 | €2,000,000 | 3 |

**€13,000,000 employer's liability appears in four of five, unchanged**
(the fifth is €12.7M). That is not five buyers each deciding
independently — it is a standard Irish public-sector template. The
barrier is therefore not negotiable per-contract, and it is
**predictable**: any Irish public security tender will want roughly
this. There is no point assessing them one at a time hoping for a
lenient buyer.

**Turnover is the figure that varies — €400,000 to €2,600,000, a 6.5×
spread — and turnover is precisely the one they let a consortium satisfy
jointly.**

All five documents were checked for the reliance clause. **All five
carry it.** The Oireachtas RFT, verbatim:

> *"Tenderers should note that where a Tenderer is relying on the capacity
> of other entities (for example, Subcontractors) for the purposes of
> fulfilling any of the Selection Criteria in part 3.2 below it must
> ensure that each such entity: (i) completes and submits a separate
> eESPD in respect of..."*

Five for five. This is not a quirk of one buyer — it is how Irish public
procurement is written.

**Deeper sweep, 2026-09-02:** 400 of 2,916 open Irish notices walked
(double the previous 200, 40 pages). Security-relevant hits: **7, of
which 5 are the notices already resolved above** and 2 are false
positives (an Irish Rail mediation system, an internal communications
platform).

**No new Irish security work exists in the visible half of the
platform.** The five resolved notices are the Irish market right now,
and all five are closed to a solo bidder. That is a complete answer for
Ireland, not a partial one.

eTenders carries 2,916 open notices against TED's 746 Irish ones, so
roughly 2,170 remain below TED's threshold and structurally invisible to
it. Worth re-sweeping periodically — but the current answer is
established, and re-running it hoping for a different result would be
waiting rather than working.

---

### 8. New Zealand GETS — two real items, and a correction

**CORRECTION, 2026-09-02 overnight sweep.** This entry previously said
"36 security/IT keyword matches". That figure was produced by a LOOSE
keyword set including `ICT`, `software`, `data`, `network` and
`technology`. Swept properly against tight security terms:

```
325  open NZ notices
  5  titles contain "secur" at all
  0  are cyber security
```

All five are physical: fire-alarm remediation at two schools, corporate
(guard) security, an enterprise CCTV install, and a poultry biosecurity
grant. The 43 broad matches are payroll, ERP, footpath replacement,
train-door technology and glazing panels.

**New Zealand currently has zero live cyber security tenders.** The
earlier headline was IT-adjacent volume, not demand for your work, and
promoting it as "36 matches" overstated the market.

**What IS real, both confirmed `Required Pre-qualifications: None`:**

| | |
|---|---|
| **NZ Ministry of Defence — Technical Support Services (TSS) Panel Reset 2026** | |
| Closes | **30 September 2026** |
| Type | Notice of Information (Advance Notice), ref `TSS-2026-AN` |
| Pre-qualifications | **None** |
| Categories | Management advisory, professional engineering, technical writing |

A **panel reset** is the rolling-admission structure that fits a solo
operator — and an Advance Notice means the real RFP is still coming, so
there is time to prepare rather than react.

| | |
|---|---|
| **Health NZ — Enterprise Observability Capability and Platform** | |
| Closes | **25 September 2026** |
| Type | Request for Information (market research), ref `RFI26-663` |
| Pre-qualifications | **None** |
| Regions | **International** — explicitly open to non-NZ suppliers |
| Category | Software |

An RFI is low-commitment by design: responding is a legitimate way onto
a buyer's radar with no bid machinery, no consortium, no references.

**Eligibility (unchanged, still verified):** NZ rules *"do not
discriminate against suppliers (domestic or international)"* and reflect
*"the Australia New Zealand Government Procurement Agreement"* and the
WTO GPA. No NZBN or local-presence requirement found across five
procurement.govt.nz pages — absence of evidence, not confirmed absence.

---

### 9. NLnet NGI Zero — €5,000–€50,000, individuals eligible

| | |
|---|---|
| **Value** | €5,000 – €50,000 |
| **Eligibility** | Quoted: *"available to both individuals and organisations of any type"* |
| **Co-contribution** | None found |
| **Call opens** | **2026-09-03 — tomorrow** |
| **Call closes** | 2026-11-03 |

The only grant found that a sole trader with no trading history could
genuinely receive.

---

### 10. Pwn2Own Berlin 2026

| | |
|---|---|
| **Value** | **$20,000 – $250,000 per target** |
| **Registration closes** | 7 May 2026 |
| **Lifetime-earnings gate** | **None** |

**Pwn2Own Ireland is gated:** it requires **$15,000 already earned
through ZDI** before you may compete. Quoted from its own rules. Which
is another reason ZDI is item 1 on this board.

---

## ❌ PNG e-GP (NPC/2026-26) — CLOSED, and worth reading why

The Asia-Pacific sweep surfaced this as the only genuinely live cyber
notice in the region: Papua New Guinea's National Procurement Commission
seeking an Electronic Government Procurement system, scoping
"cybersecurity risk assessment and testing".

The RFP was downloaded and read. It is closed, and three separate
things would have blocked it anyway:

> *"Bidding will be conducted through competitive procurement using a
> Request for Proposals (RFP), a two-envelope system with rated
> criteria, **without prequalification** ... and is open to all eligible
> Bidders."*

**No prequalification** and **open to all eligible bidders** — genuinely
the shape we have been hunting. Then:

| | |
|---|---|
| Deadline | **June 15, 2026, 17:00 PNG time** — passed |
| Bidding document | **non-refundable fee of PGK 5,000** (~AUD 1,900) |
| Submission | **"Electronic Bidding will not be permitted"** — sealed envelopes, physically delivered to Port Moresby |
| Structure | four lots |

An addendum exists (`ADDENDUM-1-NPC-2026-26.pdf`) but is a scanned
image with no extractable text, so whether it moved the date is
**UNKNOWN** — a human could open it in seconds.

**The lesson worth keeping, beyond this one notice.** "Without
prequalification" and "open to all eligible bidders" is exactly the
language this campaign has been searching for — and it still came with a
AUD1,900 document fee and a requirement to physically deliver paper to
another country. **Qualification is not the only barrier.** Access cost
and submission mechanics can close a notice that has no eligibility
criteria at all, and no filter built so far would have caught either.

## THE STAGE BEFORE THE BARRIER EXISTS

Every threshold on this board — €2,600,000 turnover, €13,000,000
employer's liability, three reference contracts — is a **selection
criterion**, and selection criteria only exist once a buyer is running a
competition. Before that, a buyer publishes what they intend to buy, and
there is nothing to qualify for because nothing is being awarded.

UK Contracts Finder exposes this directly: `stages=planning`, the same
live-verified parameter as `stages=tender` (a garbage value returns
HTTP 400, so the server genuinely reads it). Confirmed live 2026-09-03 —
it returns real releases with `status: "planned"` and no `tenderPeriod`,
which is exactly the shape the classifier reads as MARKET_ENGAGEMENT.

`foundation/tender_radar.py::planning_feed_url()` now makes that a
standing capability rather than a one-off query.

### The base rate, measured

Eighteen 30-day windows walked back from 2026-09-03, throttled:

```
444  planning-stage releases scanned
  3  unique cyber-relevant notices
     = 0.7%
```

That is the honest yield of this route on this source. It is thin, and
saying so is worth more than re-running it hoping otherwise. The route
is permanent and costs one request per cycle; it is not a lane to sit
and wait on.

**What the 18 months actually contained:**

| Notice | Buyer | Value | Published |
|---|---|---|---|
| Supply Chain Notice: WP078 Data | Ministry of Defence | **£600,000** | ~Jun 2026 |
| **Cybersecurity Training 2025 to 2029** | Royal Borough of Kingston upon Thames | **£69,552** | ~Jun 2025 |
| CCS Cyber Security Services 3 (DPS) Stage 1 | Metropolitan Police Service | — | ~Nov 2025 |

The Kingston notice is the interesting shape: **£69,552** is small enough
that a solo operator is a plausible supplier, and it is *training* rather
than testing — deliverable by one person, with no SOC to staff round the
clock. It is also from June 2025 and is therefore likely gone; it is
listed as **evidence that councils buy cyber work at this size**, not as
a live target.

The first sweep's three hits were all physical security — Waltham Forest
manned guarding at £5,798,058, MoD supply-chain notice WP073 for CCTV,
access and intruder at £300,000.

### Find a Tender rate-limits

Probing find-tender.service.gov.uk's search for a notice-type filter
returned **HTTP 429** after four requests spaced three seconds apart.
Backed off rather than continuing — that host needs a slower cadence
than Contracts Finder, and UKRI-6251 was reached through its OCDS API
rather than its search page anyway. Recorded so the next sweep does not
rediscover it.

---

## THE MECHANISM THAT CHANGES THE STRATEGY

Found 2026-09-02 by reading **all five** live Irish tender documents in
full. **All five carry it**, in the buyers' own words, and one puts a
**checkbox** on the form for it. This is not a quirk of one buyer — it
is how Irish public procurement is written.

**You do not have to meet the selection criteria yourself.**

Health & Safety Authority RFT, §3.1:

> *"Tenderers should note that where a Tenderer is relying on the
> capacity of other entities (for example, Subcontractors) for the
> purposes of fulfilling any of the Selection Criteria..."*

An Post SOC/SIEM PQQ — a tickbox on the form itself:

> *"Tick to confirm if Applicant is relying on combined turnover of
> consortium members or those of any other persons/entities, in order to
> meet the minimum financial qualification..."*

Fáilte Ireland PQQ, Section A:

> *"NOTE #1: in the case of the Candidate being a grouping, the condition
> at (i) above may be satisfied by the group members as a whole."*

And the same PQQ, on how capability is assessed:

> *"Candidates should distinguish between capabilities delivered directly
> by the Candidate and those delivered by consortium members or
> subcontractors."*

### What this actually means

Every EU tender on this board demanded turnover you do not have,
insurance you do not carry, and reference contracts you have never held.
The conclusion drawn all campaign was "these are structurally out of
reach."

That conclusion was about **bidding as the prime**. The rules explicitly
provide for a different position: the specialist whose capacity a prime
**relies on**. The buyer does not merely tolerate this — the PQQ has a
dedicated field for it and requires the prime to name who delivers what.

So the honest reframing:

| | |
|---|---|
| **Wrong question** | "How do I reach €1,800,000 turnover?" |
| **Right question** | "Which prime bidding this contract needs a tester, and how do I become the named specialist in their submission?" |

That is not a lesser path. It is the position the procurement framework
was written to accommodate, and it needs no turnover, no insurance of
your own, and no corporate reference history — the prime carries those.

### What it does NOT mean

It does not make you eligible alone. The insurance and reference bars
still apply to the grouping as a whole, and the prime still has to want
you. It also does not bypass anything: the ESPD must be completed for
every consortium member and every subcontractor whose capacity is relied
on, so you are declared, visible, and accountable in the submission.

### Why this outranks everything else found tonight

`SUBCONTRACT_TARGETS.md` and `SUBCONTRACT_APPROACH_PACK.md` were built
as a fallback lane — what to do because the tenders were closed. This
promotes that lane from consolation to **the mechanism the buyers
themselves specify**. Pulse Security, Volkis, INFODAS and AWARE7 stop
being "firms that might give you work" and become "firms whose bids
have a slot with your name on it."

**ACTION:** when approaching any firm on that list, the offer is not
"do you have spare work." It is "I am available as named specialist
capacity for tenders you are bidding." That is a different conversation,
and it is the one the documents say buyers expect to see.

---

## MARKET ENGAGEMENT — the notice type with no qualification at all

Found 2026-09-03. A **preliminary market engagement** notice (UK) or a
**Request for Information** (NZ, Ireland) is a buyer asking the market
what is possible, BEFORE writing a tender. Responding to one requires no
turnover, no insurance, no references, no certifications — because
nothing is being awarded yet.

It is the only public-sector notice type a solo operator can answer on
equal terms with a consultancy, and it puts you in front of the buyer
while the requirement is still being shaped.

| | |
|---|---|
| **UKRI-6251 — Cyber Security, Managed Service, Detection & Response, SOC** | |
| Buyer | UK Research & Innovation |
| Type | **Preliminary market engagement notice (UK2)** |
| Notice | 2026/S 000-080084, published 21 Aug 2026 |
| Scope | *"A Cyber Security provider to deliver collaborative SOC services, working with the existing STFC cyber security team"* |
| Stated qualification requirements | **None** |
| URL | find-tender.service.gov.uk/procurement/ocds-h6vhtk-06e9f0 |

Note the word **collaborative**, and *"working with the existing STFC
cyber security team"*. That is a buyer describing augmentation of their
own team, not replacement of it — which is the shape that fits a
specialist rather than a managed-service prime.

**Deadline UNKNOWN** — not published on the notice page. Needs a human
to open it or contact the buyer.

Also in this class, already on the board:

- **Health NZ — Enterprise Observability**, RFI, closes 25 Sep, regions
  International, `Required Pre-qualifications: None`
- **NZ Ministry of Defence — TSS Panel Reset**, Advance Notice, closes
  30 Sep, `Required Pre-qualifications: None`

**Three live notices where the barrier is zero.** After five Irish
documents proved the tender lane is closed at €400k–€2.6M turnover, this
is the class worth watching — and no sweep before tonight distinguished
it from ordinary tenders.

---

## TIER 3 — no credential gate, results-paid, slow

### 11. Bug bounty

| Program | Range | Platform |
|---|---|---|
| Adobe Public | $75 – $15,000 | Intigriti |
| NVIDIA Public | $150 – $15,000 | Intigriti |
| ICI PARIS XL | $10 – $8,500 | Intigriti |
| The Perfume Shop | $10 – $8,500 | Intigriti |
| Marionnaud | $10 – $8,500 | Intigriti |
| Coveo | $100 – $5,500 | Intigriti (2FA) |

**The three retail programs are one org — AS Watson Group.** Same reward
table, same exclusions, three separately-scoped brands. One methodology,
three payable programs. **Ranked ABOVE Adobe for a newcomer**, because
Adobe's platform migration reset the *platform*, not a decade of
picked-over application code.

**Rate limit:** The Perfume Shop's brief states a hard **5 req/s** cap.
Apply it to all three AS Watson brands.

**Payment gates — paperwork, not credentials.** Intigriti: ID
verification for KYC, sole traders explicitly supported as natural
persons. HackerOne: tax form, Veriff identity check, payment method.

**Sequencing trap worth knowing before you hit it:** HackerOne's ID check
unlocks **after** your first report; Intigriti's blocks payout if done
**before**. Same task, opposite order, weeks lost if you get it wrong.

**The honest economics, from HackerOne's own data:** the top 100
researchers took **39% of one year's $81M**. Newcomer duplicate rates
50–80%. No platform publishes a time-to-first-bounty figure. **Budget
three to six months of near-zero income.**

**Seventeen of Intigriti's 24 programs are VDPs** — responsible
disclosure, no money. A long program list is not a long paying list.

---

### 12. Pentest-as-a-service — skills tests, not certificates

| Platform | Gate | Verdict |
|---|---|---|
| **Synack Red Team** | Private CTF on HackTheBox | **Certifications explicitly optional.** Best fit |
| **Cobalt Core** | Same logic, tougher de facto bar | Second |
| Intigriti Hybrid | Requires 1yr bug-bounty track record first | Later |
| **HackerOne Pentests** | 3 years + named certs (OSCP/OSEP/OSWE) | **Hard no** |
| Bugcrowd Pentests | Page could not be fetched | **UNRESOLVED — not researched** |

**Synack vetting takes ~6 months.** Start it now so it is running in the
background while other lanes produce.

---

### 13. Subcontracting — firms that win this work and take individuals

| Firm | Country | Gate | Note |
|---|---|---|---|
| **Pulse Security** | NZ | **No CV gate, no cert requirement** | Work samples substitute. Lowest friction found |
| **Volkis** | Sydney | Ran an associate-tester program for varying experience levels | Confirmed from a staff member's own published bio. **Site 403s to my fetcher — check it in a normal browser** |
| **Airglow Security** | AU | Explicit no-certification, capability-first | |
| **Vertex Cyber Security** | AU | Same | |
| **AWARE7** | Germany | ~30 staff, publicly solicits pentester applications | Careers URL moved to `a7.de/career/` |
| **INFODAS** | Germany | 3 TED wins, "Security Testing" track confirmed | Vacancies page empty at last fetch |

**Correction carried forward:** **OnSecurity has no "Associate Network"
and no OSCP/OSWE/CREST requirement** anywhere on its own live pages. That
bar came from a third-party aggregator and we had recorded it as fact.
They are currently not recruiting.

---

## CLOSED — stop paying attention to these

Each was investigated and eliminated with evidence. Recorded so nobody
re-chases them.

| Target | Why it's dead |
|---|---|
| **TED 578580-2026 degewo** | `Ausschlusskriterien`: 3 testers + 2× €50k corporate refs + €3M insurance + CEFR C1 German |
| **TED 244223-2024 ECHA** | €1,000,000 average turnover + 5× €100k references. **I reported this as QUALIFIED and was wrong** |
| **RTÉ 25P041 (Ireland)** | Turnover ≥€350k/yr × 3yrs, PL €6.5M, Cyber €1M, Professional €1M, Employer's €13M. All Pass/Fail |
| **NHS England £7.2M** | Real, but `procurementMethod: selective` via CCS RM3764 DPS. Needs prior DPS admission |
| **EU DG DIGIT 773405-2024** | It's a **hardware** DPS — "end-user IT hardware equipment". An earlier pass inferred services from the title alone |
| **UK Space Agency** | EoI closed 1 Oct 2025 |
| **UK sub-threshold band** | 60-day sweep, 975 releases, 62 open, **0** that were open + under £30k + security |
| **AusTender** | Every route WAF-blocked. OCP mirror holds 50,269 records, **0** with a tenderPeriod — all awarded |
| **CanadaBuys** | Best data found anywhere (966 open, 867 future-dated) — robots.txt names bingbot/Googlebot then disallows everyone else. **You can download the CSV in a browser; my crawler won't** |
| **World Bank** | 417k records, **0** currently open. Date filters silently ignored |
| **Singapore GeBIZ** | Award-only, and foreign suppliers need a Singapore-incorporated entity |
| **SAM.gov (US)** | Requires US entity registration (UEI/NCAGE) |
| **Victoria eServices** | $5,000,000 public liability insurance |
| **SA Government bug bounty** | Press reported "financial rewards"; the official page says they do **not** compensate |
| **R&D Tax Incentive** | Restricted by statute to body corporates. Sole traders categorically excluded |
| **Industry Growth / Ignite Ideas** | Matched co-funding required — disqualifying with no capital |

---

## THE THINGS ONLY YOU CAN DO

Twelve facts across four schemes, and none of them can be generated:

```
ABN                              → NSW, ICN
Declared service skills          → NSW, CCS DPS, ICN, QLD
Two referee reports              → NSW          ← the one open question
Supplier Declaration signature   → NSW
Financial solvency confirmation  → NSW
DPS Schedule 1 filter selection  → CCS DPS
SQ financial details             → CCS DPS
Supply categories                → QLD
Business info / service regions  → QLD
```

The dossier generator fills what is known and writes
`UNKNOWN — VERIFICATION REQUIRED` everywhere else. It **cannot** invent
an ABN, ACN, licence, insurance figure, certification, customer or
referee — a test asserts no 9+ digit run appears anywhere in an empty
profile's output. These forms carry legal declarations you sign.

---

## COSTS, so nothing is a surprise

| Item | Cost | Source |
|---|---|---|
| Professional indemnity, sole trader IT consultant | **from $43/month** | BizCover, April 2025 |
| PI + public liability combined | **~$81/month average** | BizCover, April 2025 |
| **$5M PL specifically (what NSW wants at contract time)** | **UNKNOWN** | Nothing found priced at that limit — needs a broker quote |
| NSW scheme application | Free | |
| ZDI registration | Free | |
| ICN Gateway discoverability | ~$600–$1,480/yr (low confidence) | |

---

## THE LEGAL QUESTION, unresolved

**Does an individual need a licence to sell penetration testing in
Queensland?**

Verdict recorded: **UNCLEAR, LEANING NO.** The Federal Register of
Legislation was confirmed live to have no Commonwealth pentesting
licensing instrument. The Queensland Security Providers Act 1993 text
could not be fetched (every URL 404'd), and Queensland's Act is
generally understood to cover *physical* security rather than IT
security testing — but that was not confirmed from the source.

**Get the Queensland Office of Fair Trading's answer in writing before
selling pentesting under that name.** This is the only item on this
board with legal exposure attached, and it is cheap to close.

---

## RUN THE SYSTEM

```sh
python3 -m foundation.operator_cli brief --live     # what needs you today
python3 -m foundation.operator_cli income --live    # new bounty programs, gigs
python3 -m foundation.operator_cli dossier          # your paperwork + what's missing
python3 -m foundation.scheduled_brief               # one cron-safe run
```

Sources swept: TED (EU), NZ GETS, UK Contracts Finder, UK Find a Tender,
Ireland eTenders.

Bands mean exactly this and nothing more:
- **QUALIFIED** — no *published* criterion blocks you. Criteria held
  back in the procurement documents still can.
- **INSUFFICIENT_DATA** — the notice does not publish enough to decide.
  **Unresolved, not promising.**
- **DISQUALIFIED** — a published clause blocks you, and the clause is
  quoted so you can check it and disagree.

---

## IF YOU DO FOUR THINGS

1. **Open the Bradford portal in a browser.** 11 days, £300,327, and one
   unanswered question that a human session resolves in ten minutes.
2. **Register with ZDI.** Free, no deadline, no gate, and it is the
   prerequisite for the six-figure prizes.
3. **Email NSW about referees.** One email unlocks a $150,000 ceiling.
4. **Finish ICN Gateway.** No reference gate at all — the one you can
   complete today without waiting on anyone.

Then, when those are moving: the **NZ Ministry of Defence TSS Panel
Reset** (30 Sep, pre-qualifications None) and the **Health NZ
Observability RFI** (25 Sep, International, pre-qualifications None).
Both are low-commitment ways onto a buyer's list.

---

## SWEEP LOG — 2026-09-03

Re-ran `sources_for_query()` + `hunt_multi()` across all five sources
(TED, NZ_GETS, UK_CONTRACTS_FINDER, UK_FIND_A_TENDER, ETENDERS_IE)
against four keywords ("cyber security", "penetration testing",
"security testing", "security"), TED bounded to the last 30 days via
`with_recency()`. Also ran `tender_radar.planning_feed_url()` for the
UK pre-tender (planning-stage) feed directly. `operator_profile.json`
does not exist at the repo root — this run classified notices only
(title/buyer/value/deadline/notice class), which does not depend on the
real operator's facts; no EXAMPLE-profile band verdict is asserted as
real qualification here.

**Fetched (raw, deduped across keyword passes):** 1,520 items touched,
125 unique notices actually reached assessment (TED 75, NZ_GETS 30,
UK_FIND_A_TENDER 20). UK_CONTRACTS_FINDER (5 raw open-status items this
cycle) and ETENDERS_IE (10 raw items) matched none of the four keywords
client-side — a real zero, not a fetch failure (no `SOURCE FAILED` in
either run's skip list).

**Planning-stage feed (UK Contracts Finder, `stages=planning`):**
0 items. A genuinely empty pre-tender sweep this cycle, not an error.

**New MARKET_ENGAGEMENT / ROLLING_ADMISSION notices found:** the NZ
Government Marketplace standing invitation (id 33732411) and the NZ
Defence TSS Panel Reset (id 33830698) both resurfaced — both already on
this board, nothing new there. Two more NZ_GETS RFIs from Ministry of
Defence matched the broad "security" keyword client-side —
**Persistent Surveillance (Air) Phase 1** (id 34593228) and
**Supplier Data Directory Service** (id 34758151) — read and confirmed
**not relevant** to a cyber security / penetration-testing capability
(drone surveillance and a supplier-directory service respectively).
Logged here, not added to the pipeline.

**New COMPETITIVE notices found, none actionable:** an Ireland IT
services RFT (554895-2026, EUR180,000, closed 2026-08-28 — already past
deadline), an Ireland educational-software services contract
(560033-2026, EUR335,917, cyber-irrelevant), and four NZ_GETS RFPs/RFTs
(MOSP 2027, two Fire & Security fire-alarm-remediation contracts,
Pacific renewable-energy scoping, interactive-tool replacement) — all
read and confirmed out of scope.

**New TED notices found, genuinely cyber-relevant, genuinely new, not
on this board — but flagged as likely out of reach on scale, not
added to the pipeline without a value check:**

| Notice | Buyer | Value | Deadline |
|---|---|---|---|
| [Poland — SOC (Security Operations Center) service](https://ted.europa.eu/en/notice/-/detail/545435-2026) | Ministerstwo Aktywów Państwowych | 1,491,951.90 PLN | UNKNOWN — not published in the feed item |
| [Austria — Cyber Security und SOC Dienstleistungen](https://ted.europa.eu/en/notice/-/detail/604199-2026) | Umweltbundesamt GmbH | 7,200,000 EUR | UNKNOWN — not published in the feed item |
| [Belgium — Cyber Security](https://ted.europa.eu/en/notice/-/detail/605935-2026) | Opdrachtencentrale vzw | 35,000,000 EUR | UNKNOWN — not published in the feed item |

All three are UNKNOWN notice class (title didn't match any of
`classify_notice()`'s four pattern sets; this does not mean they are
not tenders — TED's own procedure-type field was not read by this
extraction pass). All three publish only a total contract value, no
per-supplier turnover/insurance/reference threshold in the fields this
sweep read — same "unresolved, not promising" caveat as everything else
INSUFFICIENT_DATA on this board. Given the five-Irish-document finding
(EUR400,000–2,600,000 turnover typically required in the competitive
lane) and these three contracts running 5–200x that ceiling, they are
logged here for completeness, not added to the deal pipeline — opening
the actual procurement documents is the next step if you want to check,
not something this sweep fabricates a verdict on.

**UKRI-6251** (Cyber Security Managed Service / SOC, UK_FIND_A_TENDER)
resurfaced under this cycle's keywords — already on this board and in
the pipeline (deal_id `ukri-6251`), nothing new there.

**Deadlines checked against today, 2026-09-03:** only **Bradford (14
Sep)** falls inside the 14-day window — 11 days out. Fáilte Ireland (24
Sep, 21 days), Health NZ RFI (25 Sep, 22 days), Oireachtas (28 Sep, 25
days), An Post (29 Sep, 26 days), NZ Defence TSS (30 Sep, 27 days),
Dept of Justice (2 Oct, 29 days) and HSA (12 Oct, 39 days) all remain
outside the window.

**Pipeline:** no new deal events appended this cycle — every notice
found was either already tracked or read and confirmed not relevant/not
actionable. `foundation/deal_pipeline_log.jsonl` is unchanged.
