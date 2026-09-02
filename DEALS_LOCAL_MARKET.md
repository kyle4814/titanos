# DEALS_LOCAL_MARKET.md — Small Fish, Closest to Home

Research date: 2026-09-03. Operator: solo, Cairns QLD, ABN, no certs, no
insurance yet, remote-capable, physically in Far North Queensland (FNQ).

**Session tool constraint, stated honestly:** WebSearch budget was
confirmed exhausted (0/200) on the first query this session — every
finding below is from **WebFetch on a named URL**, marked **[FETCHED]**,
or explicitly marked **BLOCKED** (403/404/timeout, tried and failed) or
**UNKNOWN** (plausible from general knowledge but not verified this
session — not used as a claim). No User-Agent was spoofed anywhere; a
block is recorded as a finding, not routed around.

Reads against `DEALS_PRODUCTS.md` (8 priced offers, AUD $500–6,000) and
`DEALS_PRIVATE_DEMAND.md` (SOCI Act "data storage or processing"
finding, carried forward and extended below).

---

## 1. WHO IS LEGALLY OBLIGATED TO IMPROVE SECURITY BY A DATE

### 1a. SOCI Act 2018 (as amended) — carried forward from `DEALS_PRIVATE_DEMAND.md`

**CONFIRMED** (that file, sourced from Wikipedia + legislation structure,
direct cisc.gov.au deep pages 403'd both in that session and again this
session — `cisc.gov.au/legislation-regulator-guidance/soci-act-2018`
returned 403 to WebFetch this session too, so still not independently
re-verified from the primary regulator page):

11 sectors — Communications, Financial services and markets, **Data
storage or processing**, Defence industry, Higher education and
research, Energy, Food and grocery, Healthcare and medical, Space
technology, Transport, Water and sewerage. Risk management program +
mandatory incident reporting (72hr significant / 12hr critical). "Data
storage or processing" was added in the 2024 amendment — meaning
SaaS/cloud/hosting/MSP businesses became newly regulated only in the
last two years, and the deadline that matters (the amendment's
commencement) has already passed. **No named company list is public**
(Register of Critical Infrastructure Assets is not public) — this is a
sector-and-deadline lead, not a named-account lead.

### 1b. Privacy Act 1988 — health service providers are NOT exempt, regardless of turnover — NEW, CONFIRMED THIS SESSION

**[FETCHED]** oaic.gov.au/privacy/privacy-guidance-for-organisations-and-government-agencies/organisations/small-business
— exact quoted text: *"Regardless of turnover, the Privacy Act covers
any business that is: a health service provider."* The page further
names who counts as a health service provider: *"traditional health
service providers, such as private hospitals, day surgeries, medical
practitioners, pharmacists and allied health professionals;
complementary therapists; child care centres; private schools and
private tertiary educational institutions."*

**Why this matters more than the SOCI lead for a solo operator:** the
Privacy Act's ordinary small-business exemption (turnover under $3M)
excludes almost every genuinely small Cairns business from any Privacy
Act obligation at all — which is why `DEALS_PRIVATE_DEMAND.md` correctly
flagged the general reform as "watch, don't pitch yet." **Health service
providers are the named exception.** A one-GP medical practice, a single
physiotherapist, a dental clinic, a psychologist in private practice, or
a childcare centre in Cairns — regardless of how small — is bound by
the Australian Privacy Principles and the mandatory Notifiable Data
Breaches (NDB) scheme **today**, with no revenue threshold to grow into.
This is a genuinely small, local, low-competition, obligated buyer
class that most generalist security consultants pitch to enterprise
healthcare and skip.

**What they'd buy:** Product 3 (Policy Pack, ISO/SOC2/Essential-Eight-
mapped but here mapped to APPs specifically — a "Privacy Act compliance
pack for health providers" reframe of the same deliverable), Product 2's
smaller cousin (a Privacy Act / NDB-readiness gap check instead of a
SOC2/ISO one), Product 7 (Incident Response Retainer — explicitly
scoped as "technical triage, refer NDB determinations to a solicitor,"
which is precisely the right boundary for this buyer class since the
NDB decision itself is a legal one).

### 1c. Tax Practitioners Board (TPB) Code of Professional Conduct — UNKNOWN, not confirmed this session

**BLOCKED.** `tpb.gov.au/code-professional-conduct`,
`tpb.gov.au/comply-code-professional-conduct`, and the TPB homepage all
either 404'd or timed out to WebFetch across two attempts each. There is
a real, widely-reported 2024 update to the TPB Code of Professional
Conduct that is commonly described as including new record-keeping and
security-adjacent obligations for registered tax/BAS agents — **but I
could not fetch a live TPB page to quote it this session, so it is not
used as a sourced claim here.** Flag as a genuine next-session lead:
re-attempt `tpb.gov.au` fetches when the site is reachable, or ask Kyle
to paste the actual Code text via the `GO <topic>` digestion interface
this repo already has wired.

### 1d. ASIC cyber resilience for AFSL holders (financial advisers) — BLOCKED

`asic.gov.au/regulatory-resources/financial-services/cyber-resilience/`
returned 404 to WebFetch. ASIC does publicly maintain cyber-resilience
expectations for AFSL holders (Regulatory Guide material, INFO sheets)
per general knowledge, but **not independently re-verified this
session** — UNKNOWN, not used as a sourced claim. Same next-step: retry
or digest a pasted source.

### 1e. Legal profession (Law Society Qld / Law Council) — BLOCKED

`qls.com.au/practising_law_in_qld/ethics_and_practice/cybersecurity`
404'd. No working URL found this session for Queensland Law Society or
Law Council of Australia cybersecurity guidance. UNKNOWN — not claimed.

### 1f. Aged care — not directly fetched this session

Aged care is already inside the SOCI Act's "Healthcare and medical"
sector list (1a) for larger operators, and the Aged Care Quality and
Safety Commission separately runs a Standards regime with privacy/
records obligations — **not independently fetched or quoted this
session**, so left as UNKNOWN rather than asserted. Worth a dedicated
fetch next session (`agedcarequality.gov.au`) before pitching this
sector specifically.

### Compressed finding for §1

**One real, sourced, immediately-actionable obligation for a solo
Cairns operator: health service providers of any size are bound by the
Privacy Act and the NDB scheme, unconditionally.** Everything else in
this section (SOCI, TPB, ASIC, legal-profession, aged care specifics)
is either already-recorded-elsewhere (SOCI) or blocked/UNKNOWN this
session — do not repeat those as confirmed facts in a sales pitch until
re-fetched.

---

## 2. CAIRNS / FNQ BUSINESS ECOSYSTEM — WHO CONVENES LOCAL BUSINESSES

Two real, named, contactable conveners, both fetched successfully:

### Cairns Chamber of Commerce — **[FETCHED]** cairnschamber.com.au

Peak body for business representation in the Cairns region, established
1909. Four pillars: Listen / Advocate / Inform / Connect. Runs regular
events and networking (an "Upcoming Events" section, an Emerging Leaders
Program, annual Business Excellence Awards). Membership is open via the
website; a "Become a Member" path exists.

- Phone: (07) 4031 1838
- Email: info@cairnschamber.com.au
- Office: Suite M2a, Mezzanine Level, The Pier, Pier Point Rd, Cairns
  QLD 4870

**How a solo supplier gets in front of them:** join as a member (this is
the direct, no-gatekeeper path the operator profile already assumes —
no procurement, no platform), then use the networking events/Emerging
Leaders Program as the actual point of contact rather than cold
outreach. This is also the literal path `DEALS_PRODUCTS.md` Product 1
and Product 5 already named ("Cairns Chamber of Commerce network" /
"free 20-minute sample session at a Cairns Chamber of Commerce...
event") — this session confirms the organisation is real, active, and
has a stated events/networking function, not just a name on a products
sheet.

### Advance Cairns — **[FETCHED]** advancecairns.com

"The peak independent, non-partisan advocacy and economic development
organisation for Far North Queensland" — member-funded, focused on
advocacy, economic development, and the "Roadmap 2035" regional
strategy. Platinum members include Cairns Airport, Cairns Regional
Council, James Cook University, Ports North. Publishes a member
directory, event listings, and regular "Member Spotlight" pieces across
sectors (aviation, freight, construction, consulting, marine services,
education, real estate).

**Character difference from the Chamber:** Advance Cairns skews toward
larger, infrastructure-anchor members (airport, council, university,
ports) and macro advocacy rather than day-to-day small-business
networking — a slower, higher-level relationship play (visibility via
Member Spotlight, not a direct sales channel), whereas the Chamber is
the faster, cheaper, higher-frequency path to the actual small-business
buyer named in `DEALS_PRODUCTS.md`.

### Cairns Regional Council business page — BLOCKED

`cairns.qld.gov.au/business` timed out twice. Council likely runs a
business directory/permits page but it was not independently confirmed
this session — do not claim it exists in a pitch without re-checking.

### Compressed finding for §2

Two real conveners exist and are reachable without spoofing anything:
**Cairns Chamber of Commerce (join, attend, offer the free sample
session already planned in Product 5) is the primary channel; Advance
Cairns is a secondary, slower visibility channel.** No coworking space
was independently confirmed this session — a genuine gap, not filled
with a guess.

---

## 3. AU INDUSTRIES WITH HIGH BREACH EXPOSURE, LOW SECURITY MATURITY

**BLOCKED, evidence-based version.** The OAIC's Notifiable Data Breaches
statistics index page (`oaic.gov.au/privacy/notifiable-data-breaches/
notifiable-data-breaches-statistics`) loaded, but **only as a list of
report titles/links** — no sector-by-sector breach counts or rankings
were retrievable from the static content this session. The most recent
report title visible was *"Notifiable Data Breaches Report: July to
December 2024"* — but its actual sector breakdown was not fetched.

This is the same finding `DEALS_PRIVATE_DEMAND.md` already recorded for
this exact source ("landing page only ... JS-driven ... did not resolve
to static hrefs"), now independently reconfirmed on a second attempt
with a different URL path. **Do not state a sector breach ranking in any
pitch material — it is not sourced.** The Privacy Act health-provider
finding (§1b) is the strongest evidence-based substitute available this
session: it identifies a sector by *legal exposure* (unconditional
Privacy Act coverage + mandatory NDB reporting for any size business)
rather than by breach-count ranking, which is a defensible stand-in
until the OAIC statistics can actually be pulled.

**Next step to unblock:** the actual PDF/HTML report
(`oaic.gov.au/.../notifiable-data-breaches-report-july-december-2024`,
exact path unknown) would need a direct fetch attempt with its real
URL, or Kyle pasting the sector table through the `GO <topic>`
digestion interface already wired in this repo.

---

## 4. "HAS A WEBSITE AND SOMETHING TO LOSE" — WHO BUYS, WHO CURRENTLY SELLS TO THEM

Not independently re-verified with new fetches this session (WebSearch
exhausted, and this is a synthesis question rather than a single-URL
fact) — reasoned from §1b (confirmed) and `DEALS_PRODUCTS.md`'s existing
buyer profiles, which is the honest label for this section:
**[REASONED]**, not **[FETCHED]**.

| Segment | Why they qualify | What they'd buy (from `DEALS_PRODUCTS.md`) | Who sells to them now |
|---|---|---|---|
| Medical/allied-health practices | **Confirmed** unconditional Privacy Act + NDB exposure (§1b) | Product 3 (Policy Pack, APP-mapped), Product 2-lite (Privacy/NDB gap check), Product 7 (IR Retainer) | UNKNOWN — no incumbent local specialist identified; nationally, generic MSPs and medical-specific compliance vendors (not verified by name this session) |
| Law firms | Client confidentiality is the core professional obligation; no obligation text confirmed this session (§1e blocked) | Product 3, Product 1 (client-portal review) | UNKNOWN |
| Accounting/tax practices | TPB obligation plausible but unconfirmed (§1c blocked); practices hold TFNs, bank details, whole-business financials — obvious high-value target regardless of the regulatory question | Product 1 (client portal), Product 3, Product 6 if they run their own practice-management SaaS | UNKNOWN |
| Real estate agencies | Hold tenant/buyer ID documents, trust account access, client portals | Product 1 (portal review), Product 4/5 (staff are a common phishing target — trust account fraud is a known real-estate attack pattern) | UNKNOWN |
| Tourism operators (Cairns-dense: booking platforms, dive/reef operators, tour agents) | Customer-facing booking systems handling payment data; explicitly named as the example buyer in Product 1 already | Product 1 (booking-platform review), Product 4/5 (seasonal staff turnover = recurring phishing risk) | UNKNOWN |

**Honest gap:** "who currently sells to them" could not be answered with
named competitors this session — that needs either WebSearch (exhausted)
or direct fetches against specific named vendor sites, which was not
attempted given the higher-priority items above. Recorded as a real gap,
not filled with invented competitor names.

---

## 5. GRANTS THAT FUND THE BUYER'S SIDE — HIGHEST-LEVERAGE SECTION, NEGATIVE RESULT CONFIRMED

This was flagged as the highest-leverage part of the brief: if a grant
pays the customer's side, the budget objection disappears. **Every
concrete Queensland/federal program checked this session either does
not fund cybersecurity/digital-security purchases, or is currently
closed.** This is a real, evidence-based negative finding — recorded
honestly rather than papered over.

| Program | Status | Funds security purchase? | Source |
|---|---|---|---|
| **QLD Business Basics Grants Program** | **CLOSED** (Stage 2 concluded, recipients notified) | No — funds "professional business advice," "strategic marketing," "website build and upgrades" only. Cybersecurity/IT security not listed. | **[FETCHED]** business.qld.gov.au/.../business-basics |
| **QLD Business Boost Grants Program** | **CLOSED** for applications | No — funds "future planning," "specialised and automated software," "staff management systems." Cybersecurity/IT security not listed. | **[FETCHED]** business.qld.gov.au/.../business-boost |
| **Digital Solutions – Australian Small Business Advisory Services (ASBAS)** | Appears operational (no explicit dates found) | **No purchase funding** — free workshops/webinars plus a fee-based advisory session (up to 5 hrs) covering topics including "cybersecurity and data privacy," but it is advice/training, not money toward buying a service from someone like the operator. It is technically a **competitor** for the awareness/training products (4/5), not a funding source for products 1/2/6/7/8. | **[FETCHED]** business.gov.au/.../digital-solutions-australian-small-business-advisory-services |
| **Cyber Wardens (COSBOA)** | Federally funded Nov 2023 – Jul 2026; **COSBOA ceases delivering it by 11 September 2026** | Free training only, not a grant, not a purchase-funding mechanism. Lists a "Partner with Cyber Wardens" option but no confirmed pathway for a solo consultant. | **[FETCHED]** cyberwardens.com.au |
| **business.gov.au grants finder, "cyber security" / "online and digital" filters, QLD** | Live tool queried directly | **Zero results** — "We couldn't find any grants or programs that match your current filters." | **[FETCHED]** business.gov.au/grants-and-programs |
| QLD "Secure Communities Partnership Program" | Named on the QLD grants overview page, not individually fetched | Framed as "safety and security infrastructure for small business" — reads as physical/crime-prevention security (CCTV, lighting, alarms), not cyber. **Not confirmed either way this session** — flag as UNKNOWN, worth one direct fetch next session given the name overlap. | **[FETCHED]** (listing only) business.qld.gov.au/.../grants |

### The real implication

**No live AU grant was found this session that pays a small business to
buy the products on `DEALS_PRODUCTS.md`.** The "grant pays the
customer's side" lever the brief hoped for does not currently exist as
searchable/fetchable reality — it is not that the research was
insufficient, it is that Business Basics/Boost (which could plausibly
have covered "professional business advice" broadly enough to include a
security review) are **both closed**, and the programs that are open
(ASBAS/Cyber Wardens) are **free training that competes with Products 4
and 5** rather than funding that unlocks Products 1/2/3/6/7/8.

**One genuinely useful sub-finding inside the negative result:** Cyber
Wardens' free-training window closes **11 September 2026** — after that
date, COSBOA stops delivering the one free, government-funded
alternative to Products 4 and 5 (Phishing Simulation, Awareness
Training) that currently exists. That is a real, dated, actionable fact:
**after mid-September 2026, the free-training competitor for the
cheapest two products on the sheet disappears**, which is the closest
thing to a "grant-shaped" lever this session actually found — not money
toward the buyer's purchase, but the removal of a free substitute good,
which has the same directional effect on demand.

**Next step to genuinely close this question:** re-check
`business.qld.gov.au` for a next Business Basics/Boost round opening
(both are explicitly "closed," not "cancelled" — a new round is the
normal pattern for these programs) and fetch the QLD Secure Communities
Partnership Program page directly to confirm/deny cyber scope.

---

## CONCRETE GO-TO-MARKET

**Who to approach first, and why now:**

1. **Cairns/FNQ medical and allied-health practices** — the one segment
   with a *confirmed, unconditional, already-in-force* legal obligation
   (§1b) regardless of size, which no generic small-business Privacy Act
   messaging captures (most SMBs are exempt and correctly ignore it —
   this segment cannot). Lead product: Product 3 reframed as an
   "APP/NDB-ready policy pack for health practices," priced at the
   sheet's existing $1,500–$3,000 band, with Product 7's IR Retainer as
   the natural follow-on once one practice is a reference.

2. **Cairns Chamber of Commerce membership** — join, attend events, and
   run the free 20-minute Product 5 sample session already planned in
   `DEALS_PRODUCTS.md`. This is the actual convener that exists and
   answers your "no platform, no gatekeeper" requirement literally: a
   membership fee, not a procurement process.

3. **Tourism operators and real-estate agencies with booking/client
   portals** — the existing Product 1 buyer profile, now dated by the
   Cyber Wardens sunset (11 Sept 2026, §5): approach *after* that date
   with awareness-training pitches (Products 4/5), since the free
   government alternative will have just disappeared.

**How to reach them without a marketing budget:** Chamber membership +
events (§2) is the only zero-cost, real, convener-backed channel
confirmed this session. LinkedIn/direct outreach (already planned in
`DEALS_PRODUCTS.md`) remains the fallback for segments with no local
convener confirmed (medical practices specifically — no medical-industry
local association was found or fetched this session; that is a genuine
gap for the next research cycle, not filled here).

**Risks / uncertainties carried forward:** TPB, ASIC, legal-profession,
and aged-care-specific obligations are all UNKNOWN this session (blocked
fetches) — do not cite them as facts in outreach copy until re-verified.
The OAIC sector breach ranking is unretrieved — do not cite breach
statistics by sector. No named competitor was identified for any buyer
segment — pricing/positioning against a specific rival is not yet
possible from this research.

**Highest-leverage next research action:** re-attempt the blocked
regulator fetches (TPB, ASIC, Law Society, cisc.gov.au, the actual OAIC
NDB report file) individually with their precise document URLs rather
than landing pages — landing pages 403/404/timeout consistently this
session; the underlying PDFs/reports may resolve where the HTML index
pages did not.
