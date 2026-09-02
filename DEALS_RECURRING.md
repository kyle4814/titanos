# Deals That Pay Without Him Delivering Every Hour

Researched 2026-09-03. Operator profile: solo, Cairns AU, ABN only, no certs, no
insurance, no staff, strong build capability. Scope: recurring/passive-leaning
income — referral/affiliate, white-label resale, subcontract day rates, bug
bounty triage, tooling sales, teaching/content. Excludes direct subcontract
outreach targets (see SUBCONTRACT_TARGETS.md / SUBCONTRACT_APPROACH_PACK.md).

**Access note (read this before trusting any "UNKNOWN" below):** WebSearch was
exhausted at session start (0 queries available), so this run is WebFetch/curl
only, no crawler UA spoofing, robots.txt respected. Most vendor partner-program
pages (Huntress, Vanta, Sonar) gate actual commission percentages behind a
signup/deal-registration wall — the marketing page says "profitable margins,"
the number is not public. That gating is itself a finding: assume any MSP/
vendor partner program requires enrolment before revealing real economics.
Several sites (SEEK, Udemy, Indeed, HackerOne/Bugcrowd job boards) are JS
single-page apps that return an empty shell to a plain HTTP fetch — their data
is UNKNOWN here, not zero.

---

## RANKED BY REALISTIC ANNUAL VALUE vs EFFORT

### 1. Subcontract day-rate pentesting — HIGHEST realistic value, known effort
**What it pays:** UK contract penetration tester median day rate **GBP 675/day**
(itjobswatch.co.uk, live market data, 6 months to 2 Sept 2026, aggregated from
UK contract job ads). UK **permanent** penetration tester median salary
**GBP 62,500/yr** (same source) — floor reference, not what a contractor nets.
AU day rate: **UNKNOWN** — SEEK and Hays AU salary-guide pages are JS apps;
no scrapeable AU day-rate figure obtained this run. Do not assume AU tracks UK;
AU market is thinner and Cairns has no local security consultancy demand — this
is a remote/interstate play.
**Requires:** demonstrable delivery track record, a consultancy willing to
subcontract (this is the gap SUBCONTRACT_TARGETS.md is already chasing) — no
cert gate at the subcontract layer, the primes carry the cert/insurance.
**Time to first money:** as fast as one signed subcontract SOW — bounded by
sales cycle, not skill.
**Open to solo ABN:** yes — this is literally how subcontracting works.
**Caveat:** GBP 675/day is a UK figure; converting it to an AU/remote
expectation without a matching AU data point would be a fabrication, so treat
it as "the ceiling looks real in at least one market," not a guaranteed AU
number.

### 2. Affiliate/referral commissions — LOW effort, LOW-to-moderate realistic value
**Malwarebytes affiliate program** (fetched live, malwarebytes.com/affiliates):
**"Up to 30% commission" per sale**, paid 30 days after point-of-sale, run
through the Partnerize network (join.partnerize.com/malwarebytes). Open signup,
no minimum revenue commitment stated, no company structure required beyond an
affiliate account. This is a real, quotable number — but "up to" means tiered,
top tier likely requires volume not disclosed publicly.
**1Password, Bitwarden, NordVPN/NordLayer affiliate pages:** URLs fetched
404'd — programs may exist under different paths or require the vendor's
affiliate-network listing page instead of a vendor-hosted URL. **UNKNOWN**,
not confirmed absent.
**Realistic value:** affiliate commissions on consumer security tools convert
poorly without an existing audience (blog, YouTube, newsletter). Without
traffic, this is near-zero regardless of the %. Rank it low unless content
(#6 below) is built first to create the audience that makes affiliate links
worth anything.
**Time to first money:** instant signup, but payout depends entirely on
traffic he doesn't currently have.
**Open to solo ABN:** yes, no cert/insurance/company gate found.

### 3. MSP/vendor partner programs (Huntress, Vanta, Sonar checked) — UNKNOWN economics, real gate found
**Huntress partners page:** states "profitable partner margins" — no % given.
**Vanta partners page:** Service Provider / Auditor / AWS Channel / Integration
partner tiers exist; commission/margin **not published**, gated behind deal
registration or a partnership-team contact form (Airtable form).
**Sonar (SonarQube/SonarCloud) channel partners:** technology/cloud/channel
tiers exist; margin **not published**, gated behind a "become a partner"
contact form.
**Finding, not a number:** every MSP-tier security vendor partner program
checked requires you to enrol (or get on a call) before showing real margin.
None of these publish "X% margin" on the open web. This matches how channel
programs generally work — but it means the "what does it actually pay"
question in the brief cannot be answered without contacting them, which was
explicitly out of scope for this run (no sign-ups, no contact).
**Minimum revenue commitment:** not disclosed on any of the three checked;
UNKNOWN whether a solo ABN with zero existing MSP book clears the bar.
**Time to first money:** UNKNOWN — likely months (need a client to sell
into first).
**Open to solo ABN:** plausible but unverified — these programs are typically
built for MSPs with an existing client base, not zero-revenue solo operators.
Treat as speculative until an actual enrolment conversation happens.

### 4. White-label / reseller (compliance SaaS, security tooling) — UNKNOWN, same gating problem
No compliance-SaaS or security-tooling white-label program returned public
margin figures this run (Vanta checked above under partner programs — same
data). No additional distinct white-label programme was independently
confirmed. **UNKNOWN across the board** — this needs direct-contact research
that was out of scope here.

### 5. Bug bounty triage work (HackerOne, Bugcrowd) — access blocked this run, real programme known to exist
HackerOne and Bugcrowd both run paid third-party triage functions in their
business model (triage is a named product line on hackerone.com/product —
page didn't resolve for content extraction this run, but the product exists
publicly under other pages referencing "Triage" as a HackerOne service tier).
Job boards for both companies are Ashby/JS-rendered SPAs — could not extract
actual open roles, pay ranges, or application requirements via plain fetch.
**What it pays:** UNKNOWN this run.
**Is it open to individual applicants without certs:** plausibly yes (both
platforms are known to hire from their own top-ranked researcher pools rather
than requiring formal certification), but this is unverified in this session
— do not present it as confirmed.
**Recommendation:** this needs a direct visit to the actual careers pages in
a real browser, not a fetch — flag as next research action, not a dead end.

### 6. Teaching / content (Udemy, freeCodeCamp) — access blocked this run
Udemy instructor terms page returned 403; freeCodeCamp's write-for-us page
returned 404 (URL likely changed). **Both UNKNOWN this run**, not confirmed
absent. Udemy's revenue-share structure is publicly documented elsewhere (own
site vs Udemy-driven-sale tiers) but could not be pulled live and verified
today, so no % is quoted here to avoid stating a stale/unverified figure.

### 7. Building/selling tooling (Gumroad, GitHub Sponsors, small SaaS) — no real revenue examples found
Checked indiehackers.com's product board — no security/infosec products with
disclosed revenue figures surfaced in the fetched content (the page returned
five unrelated featured products, none infosec). **No verified real example
found this run.** This doesn't mean the market doesn't exist — it means this
research pass didn't turn up a citable number. Needs a longer/manual pass
(indiehackers category filter, Gumroad discover, GitHub Sponsors leaderboard)
that a plain fetch couldn't drive.

---

## HONEST BOTTOM LINE

Only two hard numbers were confirmed live this session:
- **UK contract pentester day rate: GBP 675/day median** (itjobswatch.co.uk,
  dated to 2 Sept 2026) — real, current, but UK not AU.
- **Malwarebytes affiliate: up to 30% commission**, open signup, no minimum
  revenue commitment (malwarebytes.com/affiliates) — real, but affiliate
  income is gated by traffic he doesn't have yet.

Everything else that looked promising on paper (MSP partner margins,
white-label reseller terms, bug bounty triage pay, teaching platform revenue
share) is gated behind either a JS-rendered page this toolset can't execute,
a contact-to-reveal wall, or a blocked fetch. That is a real finding: **the
actual economics of most "recurring deal" channels in security are not
published — they require a conversation to unlock**, which was explicitly
out of scope for this pass (no sign-ups, no contact per the rules given).

**Recommended lever:** the subcontract day-rate channel (item 1) is the only
one with a concrete, current number attached and zero new gatekeeper to get
past beyond what SUBCONTRACT_TARGETS.md is already pursuing — it's the
highest-confidence next move, not a new channel to open.

## NEXT RESEARCH ACTION (not done here, flagged honestly)
A follow-up pass with a real browser session (not plain HTTP fetch) against
HackerOne/Bugcrowd careers, Udemy's instructor terms page, and SEEK/Hays AU
salary data would close the biggest UNKNOWNs above. This file should be
updated once that's done — do not treat the UNKNOWNs as "checked and empty."
