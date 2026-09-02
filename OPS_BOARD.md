# OPS BOARD — every live opportunity, what it's worth, what it needs

Compiled 2026-09-02. Every figure here was read off a primary source
during this campaign, not recalled. Where something is unknown it says
UNKNOWN — that is a real state, not a gap someone forgot to fill.

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

### 6. City of Bradford MDC — penetration testing framework ⏰ 12 DAYS

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

### 7. Ireland — five open security notices, English submission

| Notice | Buyer | Closes | Procedure |
|---|---|---|---|
| SOC/SIEM/Managed IR | Health & Safety Authority | **12 Oct** | Open |
| Managed Security Services | Houses of the Oireachtas | **28 Sep** | Open |
| SOC/SIEM | An Post | **29 Sep** | Negotiated w/ prior call |
| National PKI managed services (PQQ) | Dept of Justice | **2 Oct** | Competitive w/ negotiation |
| Cybersecurity Specialist Services | Fáilte Ireland | **24 Sep** | Restricted |

All English submission. All reachable at
`etenders.gov.ie/epps/cft/prepareViewCfTWS.do?resourceId=<id>`.

**Honest caveat on the two SOC/SIEM ones:** a Security Operations Centre
is a 24/7 monitored service. That is a genuine delivery-capacity
barrier, not a paperwork one — one person cannot staff it round the
clock. As a prime bid they are out of reach; as a **subcontract
position** they are live.

**"Cybersecurity Specialist Services"** is the interesting title —
*specialist services* is the shape that gets subcontracted to
individuals — but it is Restricted procedure with a PQQ.

**Why Ireland matters beyond these five:** eTenders carries 2,916 open
notices; TED carries 746 Irish ones. So roughly **2,170 below-threshold
Irish notices are structurally invisible to TED** — a non-overlapping
tier of demand, and the low-barrier band a solo operator can win in.

---

### 8. New Zealand GETS — 36 live matches, no pre-qualification

| | |
|---|---|
| **Pool** | 324 open tenders, **36 security/IT keyword matches** |
| **Barrier** | Three sampled notices **all state `Required Pre-qualifications: None`** |
| **Eligibility** | NZ rules *"do not discriminate against suppliers (domestic or international)"* and reflect *"the Australia New Zealand Government Procurement Agreement"* and the WTO GPA |
| **Local presence** | No NZBN or local-presence requirement found across five procurement.govt.nz pages |

That "None" is the buyer **positively stating** there is no gate — not
silence being read as permission. That distinction is the whole reason
these verdicts are worth anything.

**Sampled:** University of Waikato, Ministry of Education, Statistics NZ.
**3 of 36 checked** — deliberately, because fetching 36 detail pages in a
burst is rude to a live public service. The other 33 are UNKNOWN, not
assumed clear.

**Absence of evidence caveat:** no local-presence requirement was
*found*. That is not the same as one being confirmed absent.

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

1. **Open the Bradford portal in a browser.** 12 days, £300,327, and one
   unanswered question that a human session resolves in ten minutes.
2. **Register with ZDI.** Free, no deadline, no gate, and it is the
   prerequisite for the six-figure prizes.
3. **Email NSW about referees.** One email unlocks a $150,000 ceiling.
4. **Finish ICN Gateway.** No reference gate at all — the one you can
   complete today without waiting on anyone.
