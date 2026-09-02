# Live Contracts He Can Bid On Tonight

Researched 2026-09-03, same operator profile as `LIVE_PAID_WORK.md`
(solo, Cairns AU, no certs, ABN held, remote-capable). This file is the
"what's open RIGHT NOW" companion to that doc's platform-access audit —
read that first for the certification-wall findings (Synack = best fit,
HackerOne Pentests = hard no, Upwork/Freelancer = zero barrier).

Every row below traces to a URL actually fetched this session. Where a
fetch failed, blocked, or returned no usable data, that's reported as a
finding, not silently dropped. Nothing fabricated.

---

## RANKED BY MONEY-PER-BARRIER

### 1. Freelancer.com.au — live penetration-testing projects, bid tonight
**Barrier: zero.** Open bidding, no platform gate, ABN/no-cert is fine —
client-side vetting only. Fetched `freelancer.com.au/jobs/penetration-testing`
2026-09-03, live listings:

| Project | Budget (AUD) | Time left | Bids so far |
|---|---|---|---|
| CERT-In Certified Web VAPT | $389 | 6 days | 12 |
| VAPT Assessment | $916 | 6 days | 13 |
| Ethical Application Security Audit | $403 | 5 days | 17 |
| SMS OTP Login Security Assessment | $127 | 5 days | 16 |
| E-Procurement Web App Penetration Test | $216 | 3 days | **134** |
| Harden SOAP API Access Control | $330 | 3 days | 25 |
| CREST-Certified VAPT for Web & Network | $151 | 2 days | 12 |
| Cybersecurity Trainer – Hands-on Labs | $14/hr | 23 hrs | 11 |
| Android Lab-Environment RAT PoC | $35 | 2 hrs | 18 |

URL: https://www.freelancer.com.au/jobs/penetration-testing — Seen 2026-09-03.

Read the fine print before bidding: "CERT-In Certified" and "CREST-Certified
VAPT" listings are explicitly asking for a credential he doesn't hold —
skip those two unless the client will accept uncertified work. The
E-Procurement listing at 134 bids is a race to the bottom, not worth the
time. **Best realistic targets tonight: VAPT Assessment ($916, 13 bids)
and Ethical Application Security Audit ($403, 17 bids)** — no stated
cert requirement, moderate competition, decent budget-to-bid ratio.

### 2. Upwork — could not verify live listings this session
Attempted `upwork.com/hire/penetration-testers/` and a live search URL —
both returned **HTTP 403** to the fetch tool (Upwork blocks non-browser
fetches; this matches the access pattern already noted in
`LIVE_PAID_WORK.md`). The prior session's $60–150/hr median-rate finding
stands as background, but no specific live listing was verified tonight.
**Action: open Upwork directly in a real browser session** — the fetch
tool cannot get past their bot wall.

### 3. HN "Who is hiring?" (September 2026 thread) — checked, negative result
Thread confirmed live: https://news.ycombinator.com/item?id=49522897
(posted 2026-09-01). Pulled all 201 top-level comments via the public
Algolia API and grepped for penetration-test/appsec/red-team/offensive-
security keywords. **Result: zero contract pentest postings.** Every
security-titled listing found (Spade Senior Platform Security Engineer,
Discord Senior AppSec Engineer $280-330K, DuckDuckGo Senior Web Security
Engineer, Zepto Senior Security Engineer remote-AUS, Odyssey Sr Security
Engineer, Wikimedia Lead PM Security, ChainSecurity Blockchain Security
Engineer, Oscilar Sr/Staff Security Engineer) is a **full-time salaried
role**, not a contract, and most want 3+ years plus a title, not a
skills test. Not a lane for tonight.

### 4. WeWorkRemotely — robots.txt clear, not re-scraped this pass
`weworkremotely.com/robots.txt` allows all crawlers with no ClaudeBot
exclusion — confirmed fetchable. `LIVE_PAID_WORK.md`'s prior finding
(Trace3 Offensive Security Engineer, 6-month contract) may still be
live; not re-verified this session due to time budget. **Action: open
`weworkremotely.com/categories/remote-programming-jobs` and search
"security"/"pentest" directly** — worth 5 minutes, zero barrier to read.

### 5. RemoteOK — robots.txt is contradictory, treated as blocked
Two conflicting blocks in `remoteok.com/robots.txt`: a Cloudflare-managed
block explicitly lists `User-agent: ClaudeBot / Disallow: /`, but a
later site-authored block re-lists ClaudeBot under an "AI/LLM crawlers"
group with `Allow: /` and only narrow disallows (`/@`, ad-tracking,
query params). This is a genuine conflict, not a clean allow. Per the
task rule (treat a disallow as a finding and move on), **skipped** —
the more restrictive, platform-level block is the safer read. If you
want RemoteOK checked, it needs a human browsing it directly, not a bot
fetch.

### 6. infosec-jobs.com — redirected, no listings extracted
`infosec-jobs.com/remote-jobs/` 301-redirects to `foorilla.com/hiring/infosec-privacy/`
(same company, rebranded). The rendered page returned only nav/footer
chrome to the fetch tool — it's a JS-rendered SPA and the job list never
loaded in the fetched snapshot. **Unresolved — needs a real browser.**

---

## SECTION 5 — COMPETITIVE AUDIT CONTESTS (the priority lane)

This is the one lane that's genuinely open with zero cert, zero
interview, zero application — pure "submit a finding, get paid if it's
real." Checked all four named platforms directly against live data
(API calls where possible, not just page scrapes).

### Code4rena — MAJOR FINDING: the platform is shutting down
Direct fetch of `code4rena.com` returned this exact meta description in
the page's own `<head>`:

> "After 5 years of securing DeFi, Code4rena is closing its doors.
> Active competitions and bounties are being seen through to
> completion."

Checked `code4rena.com/audits` for anything currently live: **one**
contest shows non-"Completed" status — **Rujira**, $40,000 USDC pool,
but its window was 16 Dec 2025 – 16 Jan 2026 (already fully in the
past relative to today, 2026-09-03) and its own status reads
"submissions closed, report in progress." **There is nothing open to
bid on at Code4rena right now, and the platform has publicly announced
it is winding down.** Do not build a plan around this platform.
URL: https://code4rena.com/audits — Seen 2026-09-03.

### Sherlock — checked via their live API, zero open contests
Sherlock's contest list is served as real JSON at
`audits.sherlock.xyz/api/contests`. Pulled all 301 contests across 4
pages of the API directly (not a scraped guess) and checked every
`starts_at`/`ends_at` timestamp against now. **Result: zero contests
with `starts_at <= now <= ends_at`, and zero with a future `starts_at`.**
Only two status values appear anywhere in the full dataset:
`SHERLOCK_JUDGING` (one contest, Tare, $27,000 pool, judging window
already closed 2026-07-29) and `FINISHED` (everything else). **No live
or upcoming Sherlock contest exists right now.**
URL: https://audits.sherlock.xyz/contests — Seen 2026-09-03.

### Cantina — could not extract listings, genuinely unresolved
`cantina.xyz/competitions` is a client-rendered SPA; the fetch tool got
only "No opportunities found matching your search criteria" from an
empty initial state, and four guessed API paths
(`/api/competitions`, `/api/opportunities`, `/api/opportunities/competitions`,
`/api/v0/competitions`) all returned `{"type":"not_found"}`. **This is
an unresolved gap, not a negative finding** — Cantina may well have live
competitions; this session's tooling just couldn't reach them. **Action:
open `cantina.xyz/competitions` in a real browser** — highest-value
unchecked item in this whole report given Code4rena and Sherlock both
came back empty.

### Immunefi — this is an always-on bug bounty board, not a contest format
Different model from Code4rena/Sherlock/Cantina: standing bounties, not
time-boxed contests. Fetched `immunefi.com/bug-bounty/` (rendered
listing): **Ethena** tops the board at $3M max bounty, then DeXe
Protocol ($500K), SSV Network/ENS/Lombard Finance ($250K tied), The
Graph ($50K max, $1.5M paid out historically), Cosmos ($50K). No
special flash/boosted campaign was visible in what rendered — Immunefi's
public bounty-list JSON endpoint (`immunefi.com/public-api/bounty-list.json`)
returned an HTML shell instead of JSON when hit directly, so this
wasn't independently cross-checked. **These are real, live, standing
programs** — no cert or application needed, submit a valid finding
through their triage flow and get paid per their published severity
table. This is the most concrete, verifiably-live item in Section 5.
URL: https://immunefi.com/bug-bounty/ — Seen 2026-09-03.

### YesWeHack — standing public programs, not a flash campaign
Fetched `yeswehack.com/programs`: Swiss Post E-Voting (up to €230,000,
1,855 reports historically), Doctolib (up to €50,000, 9 scopes),
Infomaniak (up to €7,000, 46 scopes), ExpressVPN ($50–$2,500),
Telenor Sweden (€50–€6,000), HARMAN International ($100–$4,000). Same
character as Immunefi — always-open public programs, not a time-boxed
promotion. No cert required to submit. URL:
https://yeswehack.com/programs — Seen 2026-09-03.

### Bugcrowd — not checked this pass
Carried over as unresolved from `LIVE_PAID_WORK.md` (a login-gated or
JS-rendered recruitment page this session's tooling couldn't reach
either time). Not re-attempted.

---

## THE HONEST BOTTOM LINE

**Section 5's premise — "this lane is genuinely open, no cert needed" —
is still true, but the two headline contest platforms (Code4rena,
Sherlock) currently have nothing open to bid on**, and Code4rena has
announced it's closing entirely. The actually-live, actually-verified
money tonight is:

1. **Freelancer.com.au** — real listings, real budgets, zero barrier.
   Bid on the VAPT Assessment ($916) or Ethical Application Security
   Audit ($403) tonight.
2. **Immunefi / YesWeHack standing bug bounties** — always open, no
   cert, no application, pays on valid findings. Not a "tonight" win
   (finding a real bug takes real time) but genuinely startable right
   now with zero gate.
3. **Cantina** — likely has live competitions but this session's
   tooling couldn't confirm; open it directly in a browser before
   writing it off.
4. Upwork, RemoteOK, infosec-jobs.com — all blocked or SPA-opaque to
   automated fetching this session; each needs 5 minutes of a real
   browser to actually check, not more bot-fetch attempts.

## WHAT WASN'T CHECKED (be honest about the gap)

WebSearch quota was exhausted mid-session (shared session budget, not
this task's doing) — all research after that point used direct
WebFetch/curl only, which works well against real APIs (Sherlock) and
poorly against JS-rendered SPAs (Cantina, Upwork, infosec-jobs.com) and
bot-walled sites (Upwork). PeoplePerHour, Contra, Guru, SEEK, Indeed,
CyberSecJobs, Otta, Intigriti/Bugcrowd flash promos, and Sherlock's
"best-efforts" program list were not re-checked this pass — the prior
`LIVE_PAID_WORK.md` audit already covers Contra (low-confidence claim),
Toptal, Cobalt, Synack, SEEK, and Indeed at the platform-access level;
this file only adds what's newly live.
