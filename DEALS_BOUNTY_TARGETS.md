# Bounty targets — newly launched / under-contested, ranked

Written 2026-09-03. Builds directly on `BOUNTY_STARTING_POSITION.md` and
`SOLO_REVENUE_ROUTES.md` — signup mechanics, KYC/tax gates, and the
already-established Adobe/NVIDIA/AS-Watson-trio findings are **not
re-derived here**. This file is the "what's new or under-contested right
now" sweep those two files asked for next.

**This is document/API research only.** Every number below came from
either (a) a platform's own public, unauthenticated JSON API, fetched
with this tool's default, unmodified User-Agent — no spoofing — or (b)
an AI-mediated read of a program's own published brief page, same method
`BOUNTY_STARTING_POSITION.md` already used and flagged as
high-confidence-but-not-final. No account was created. No target
infrastructure was tested, scanned, probed, or fuzzed. Where a fetch was
blocked (Open Bug Bounty, HackerOne, Bugcrowd's per-program dates), that
is recorded honestly below as **UNKNOWN / BLOCKED**, not guessed around.

---

## 1. Newly launched / date-verified findings — Intigriti

Intigriti's own researcher-facing programs page embeds a real Algolia
search-results payload server-side (`window[Symbol.for(
"InstantSearchInitialResults")]`), and — unlike the prior pass, which
only confirmed *that this blob exists* — this pass actually parsed it
for the `createdAt` field every hit carries. That field was not used in
`foundation/mouth_bounty.py`'s prior audit of this source (which correctly
flagged the blob as only 24-of-181 programs and undocumented) — but for
those 24 programs, `createdAt` is real, structured, and gives genuine
launch dates, not an inference. Fetched 2026-09-03, 24 hits, sorted here
by `createdAt` descending:

| Launch date | Age (days) | Program | Reward range | Type |
|---|---|---|---|---|
| 2026-08-17 | 15 | **Adobe Public** | $75–15,000 | Bug bounty |
| 2026-08-11 | 21 | Dutch Lottery VDP | — | VDP, no pay |
| 2026-07-07 | 56 | Ivo: AI VDP | — | VDP, no pay |
| 2026-07-06 | 57 | Dashlane VDP | — | VDP, no pay |
| 2026-06-24 | 69 | Spacelift VDP | — | VDP, no pay |
| 2026-06-19 | 74 | TrueLayer VDP | — | VDP, no pay |
| 2026-06-10 | 83 | Salto VDP | — | VDP, no pay |
| 2026-05-28 | 96 | **NVIDIA Public Bug Bounty** | $150–15,000 | Bug bounty |
| 2026-05-20 | 104 | Grafana Labs VDP | — | VDP, no pay |
| 2026-05-06 | 118 | ESA VDP, OURA VDP | — | VDP, no pay |
| 2026-04-21 | 133 | **Daytona Bug Bounty** | €200–3,500 | Bug bounty |
| 2026-04-15 | 139 | SolarWinds VDP | — | VDP, no pay |
| 2026-04-08 | 146 | Wärtsilä VDP | — | VDP, no pay |
| 2026-03-27→18 | 158–167 | University of Basel VDP, Tekion VDP, Attentia VDP | — | VDP, no pay |
| 2026-03-02 | 183 | Atolls VDP | — | VDP, no pay |
| 2026-02-12 | 201 | CARIAD VDP | — | VDP, no pay |
| 2026-02-04 | 209 | **Coveo Public Bug Bounty** | $100–5,500 | Bug bounty — **now shows status "Suspended"**, see §4 |
| 2026-01-15 | 229 | **ICI PARIS XL, The Perfume Shop, Marionnaud, Superdrug** | $10–8,500 each | Bug bounty (AS Watson group — see §5) |

**Only Adobe is inside the "launched in the last 60 days" window this
brief asked for.** Everything else in that window on this page is a VDP
(no money) — real, but out of scope for a first paid finding.
Seventeen of the 24 visible programs are VDPs — matches
`SOLO_REVENUE_ROUTES.md`'s existing warning not to read a long program
list as a long list of paying programs.

**This snapshot cannot see the other ~157 of ~181 total Intigriti
programs** (confirmed dead end: no query-string pagination works
against this blob, same finding `foundation/mouth_bounty.py`'s own
audit already recorded). A genuinely new paying program older than 21
days but not in this 24-item slice would not be visible here — this is
a real, honest gap, not claimed to be a full sweep.

## 2. A genuine new finding not in either prior file: NVIDIA's timing edge is smaller than assumed

`SOLO_REVENUE_ROUTES.md` and `BOUNTY_STARTING_POSITION.md` both frame
NVIDIA as "~14 months old" (dating from a July 2025 partnership
announcement). **The NVIDIA program's own `createdAt` on Intigriti is
2026-05-28 — 96 days old, not 14 months.** Two readings, neither
resolved here: either the *Intigriti listing itself* is much younger
than the underlying company relationship (a re-platforming, similar in
kind to Adobe's, just less publicised and further along), or `createdAt`
reflects something else Intigriti's own data model tracks (e.g. last
major scope revision) rather than true program age. Either way: **treat
NVIDIA as closer to Daytona's age bracket than to a decade-old program**
for duplicate-landscape purposes — this is better odds than the prior
framing implied, not worse. Still skill-gated per
`BOUNTY_STARTING_POSITION.md` §3's existing ranking (local-privilege/
CUDA-internals focus, poor fit for a web-only newcomer).

## 3. Daytona Bug Bounty — genuinely young, narrow, non-web-first surface

Quoted from the program's own brief:

- **Scope:** "Daytona/Daytona Bug Bounty/Preview" — an open-source
  infrastructure platform for executing AI-generated code inside
  isolated sandbox environments. This is **not a classic web/e-commerce
  surface** — it's an infrastructure/sandbox-isolation product, which
  structurally narrows the competing pool toward people with
  systems/containers/sandbox-escape skill, the same "non-web surface has
  fewer competitors" logic this brief was asked to apply.
- **Reward table by severity, flat amounts:** Low €200 / Medium €500 /
  High €1,000 / Critical €2,500 / Exceptional €3,500. **Pays for Low.**
- **Age:** 133 days at fetch time — younger than Adobe's decade-plus
  code history, though not inside the 60-day window.
- **Requirements:** two-factor authentication and a valid Intigriti
  account. The fetched brief excerpt showed **no separate application
  gate beyond that** — this narrows `SOLO_REVENUE_ROUTES.md`'s earlier
  "2FA + application" characterization; the application step, if one
  exists, was not visible in what was fetched this pass. Treat as
  UNCONFIRMED, not corrected, until read live in-dashboard.
- **Excluded vulnerability classes:** not visible in the fetched
  excerpt — genuinely UNKNOWN here, not "none exist." Read the live
  brief before testing anything.
- **Why it's a better bet than Adobe/NVIDIA for a newcomer with
  systems-adjacent skill specifically:** narrow single-product scope
  (one thing to learn, not a decade-deep suite), flat per-severity
  payouts (no CVSS-scoring ambiguity to get wrong as a newcomer), and a
  non-web attack surface this brief was explicitly asked to weight
  higher. Not ranked above the AS Watson trio for a *web*-skilled
  newcomer — it requires different skills entirely.

## 4. Coveo Public Bug Bounty — status correction, do not start here

`SOLO_REVENUE_ROUTES.md` listed Coveo as live ($100–5,500, 2FA
required). **Read live 2026-09-03: the program's own status field now
shows "Suspended."** Reward table was still visible (Low $100–200 /
Medium $250–350 / High $750–1,250 / Critical $2,500–3,500 / Exceptional
$4,500–5,500 — pays for Low) but a suspended program is not currently
accepting submissions for payment. **Correction to the prior file's
ranking: drop Coveo from any active first-week plan** until its status
is confirmed live again in-dashboard.

## 5. AS Watson group — a fourth sibling found: Superdrug

`BOUNTY_STARTING_POSITION.md` documented three AS Watson brands (ICI
PARIS XL, The Perfume Shop, Marionnaud) sharing one Intigriti
organisation and one policy template. **A fourth exists: Superdrug**,
same `createdAt` (2026-01-15, same day as the other three — confirming
they launched together as one batch), same reward table, same 5 req/s
rate limit, same `@intigriti.me` email requirement, same excluded-class
list almost verbatim. Quoted scope:

- **Tier 1:** `www.superdrug.com`, `api.superdrug.com`,
  `media.superdrug.com`, `app.superdrug.com`, Superdrug iOS/Android;
  `www.savers.co.uk`, `api.savers.co.uk`, `media.savers.co.uk`,
  `app.savers.co.uk`, Savers iOS/Android.
- **Tier 4:** campaign/community/ecom-data/videogp-api/healthclinics/
  innovation/onlinedoctor/onlinepharmacy domains for both brands
  (Superdrug's healthcare-adjacent subdomains — onlinedoctor,
  onlinepharmacy, healthclinics — are a genuinely different surface from
  the other three AS Watson brands, worth noting if pharmacy/health-data
  authorization flaws are a stronger fit than pure e-commerce checkout).
- **Tier 5:** `*.superdrug.com`, `*.savers.co.uk` wildcards.

**This makes the AS Watson multiplier four separately-payable programs
behind one learning curve, not three** — the single strongest update to
`BOUNTY_STARTING_POSITION.md`'s existing #1 ranking. Same boundary rule
applies: methodology transfers, authorization does not — each brand's
listed assets are separately scoped and must be separately tested.

## 6. YesWeHack — the most under-contested paying finds in this whole sweep

YesWeHack's public API (`api.yeswehack.com/programs`, no key, no
robots.txt restriction — same source `foundation/mouth_bounty.py`
already validated) exposes `reports_count` per program: a genuine,
structured, platform-declared measure of how many reports a program has
ever received. No `created_at`/launch-date field exists on this API
(checked directly in the raw JSON — not present), so "newly launched"
cannot be verified here, but **report-count-as-competition-proxy is real
data, not inferred**, sorted across all 60 live public programs:

| Reports | Scopes | Program | Company | Reward range | Pays Low? |
|---|---|---|---|---|---|
| **0** | 8 | Ant Group Security Response Center | Ant Group | $10–2,500 (+bonus to $31,337) | **Yes — $10** |
| **15** | 2 | Tencent Bug Bounty Program | Tencent | $8–5,000 | **Yes — $20–30** |
| 106 | 6 | DataDome Bot Bounty | DataDome | €200–1,000 | UNKNOWN, not fetched |
| 118 | 10 | Dossier Médical Partagé | CNAM (France) | $50–2,000 | UNKNOWN, not fetched |

**Ant Group Security Response Center — the best single find in this
sweep.** Quoted from its own brief: *"To expand its community of
researchers and recruit global talent, Ant Group Security Response
Center is partnering YesWeHack."* That is a program **explicitly stating
it wants new researchers**, matching this brief's criterion 4 exactly,
with **zero reports filed against it on this platform at fetch time** —
the most literally under-contested paying program found this pass, on
any platform. Eight in-scope assets including wildcard domains
(`*.alipayplus.com`, `*.antom.com`, `*.worldfirst.com`) and named apps
(bettrfinancing.com, anext.com.sg, alipayhk.com, antbank.hk). Reward
table: Low $10 / Medium $80 / High $250 / Critical $1,100–2,500 (bonus
up to $31,337). Excludes: tabnabbing, missing cookie flags, content
injection, mixed content, clickjacking, DoS, outdated-browser issues,
self-XSS, hypothetical flaws, outdated libraries, CSRF on login/logout,
missing headers, user enumeration, password-policy findings, spam
capability. English and Chinese both supported. **The honest caveat:**
Ant Group is a large, well-resourced fintech group — zero reports on
*this specific YesWeHack listing* most plausibly means the listing
itself is new to researchers' attention or newly onboarded to this
platform, not that the underlying product is unguarded; still, "zero
prior reports on the platform you'd be submitting through" is exactly
the reset-duplicate-landscape condition this brief asked to find.

**Tencent** is the second find worth naming: a company-name recognisable
enough that 15 reports total (against WeChat, QQ, Tencent Cloud, WeChat
Pay, King of Glory in scope) is a genuinely low number for that surface
area — plausibly under-discovered because it's perceived as
China-focused/harder to engage with, not because it's actually
saturated. Reward table splits Core/Non-Core assets: Low $30/$20,
Medium $100/$50, High $600/$400, Critical $5,000/$1,200. Requires 18+
age and KYC. English and Chinese supported.

**DataDome Bot Bounty and Dossier Médical Partagé** are recorded as
low-report leads but their own briefs were not fetched this pass — their
reward ranges above are from the API only; treat severity-level payment
as UNKNOWN until read directly.

## 7. Bugcrowd — reachable, but no reliable "new program" signal exists

`bugcrowd.com/engagements.json` is genuinely public (no key, standard
User-Agent, 200 response, 265 total live engagements across ~12 pages of
24). But **this API carries no launch-date field of any kind** —
confirmed by inspecting every key on a sample record (`name`, `tagline`,
`briefUrl`, `rewardSummary`, `scopeRank`, `industryName`,
`accessStatus`, `isPrivate`, `isDemo`, `serviceLevel` — no
`createdAt`/`launchedAt`/`startDate` anywhere). `scopeRank` looked like
a candidate proxy but returned 13+ programs tied at rank 1 in the first
page alone — not a usable freshness signal. **Cannot identify newly
launched Bugcrowd programs from this API; recorded as a genuine
capability gap, not silently skipped.**

One real finding from reading the reward summaries directly: several
public programs' `minReward` field reads **"Points"** rather than a
dollar amount (e.g. Web.com Bug Bounty, HostGator LATAM Bug Bounty,
SnapNames Bug Bounty) — meaning **the low end of their severity scale
pays in Bugcrowd points, not cash**, with cash starting only at a higher
tier. This directly answers this brief's "which pay for low severity"
question in the negative for those specific programs — a newcomer's
first Low/Medium finding on one of those would earn points, not money.
Not every Bugcrowd program does this (most show a dollar `minReward`),
but it was not visible without pulling the raw reward summary field, and
is worth checking per-program before choosing a Bugcrowd target.

## 8. HackerOne — still unreachable without executing JavaScript

Re-confirmed, same finding as `foundation/mouth_bounty.py`'s prior
audit: `hackerone.com/robots.txt` permits everything, but
`hackerone.com/directory/programs` returns a bare 1,941-byte
client-rendered shell with zero embedded data, and the historically
known `hackerone.com/programs.json` endpoint now returns 404. **No
newly-launched-program signal obtainable from HackerOne this pass** —
not a scope violation, a genuine dead end, recorded so nobody re-tries
the same fetch expecting a different result.

## 9. Open Bug Bounty — blocked by an active anti-bot challenge, not tested further

`openbugbounty.org` returned **HTTP 403 with a Cloudflare managed
challenge page** (`Just a moment...`, `cf-mitigated: challenge`) on a
plain, unmodified-User-Agent request. Per this task's absolute rules
(no User-Agent spoofing, no probing), **this was not pushed further** —
no headless browser, no UA change, no JS execution attempted. What can
be said about Open Bug Bounty here is general public knowledge, not
independently re-verified this session: it is a free, coordinated
disclosure platform (no monetary bounty), open registration, and is
genuinely useful for the exact reason this brief named it — it builds a
public track record with no KYC/tax gate, which nothing else in this
file offers. **Its current scope list, submission process, and any
policy changes are UNKNOWN — blocked, not fabricated.**

---

## 10. Ranked shortlist — start-this-week order

**1st — Ant Group Security Response Center (YesWeHack).** Zero reports
filed, explicit "recruit global talent" language, pays Low ($10). Best
odds in this entire sweep, for a web/API-skilled newcomer. Non-web
elements too (mobile apps not explicitly listed in the fetched scope
excerpt — confirm live).

**2nd — Superdrug (Intigriti, AS Watson group).** Not new, but newly
*found* — a fourth separately-payable program on the exact methodology
`BOUNTY_STARTING_POSITION.md` already built for ICI PARIS XL/The Perfume
Shop/Marionnaud. If that methodology is already being run, adding
Superdrug is close to free — same reward table, same rate limit, same
exclusions, plus a genuinely different pharmacy/health-data subdomain
set (onlinedoctor, onlinepharmacy, healthclinics) worth a fresh look
even after the other three are exhausted.

**3rd — Tencent Bug Bounty Program (YesWeHack).** Only 15 reports
against a massive, famous surface (WeChat, QQ, WeChat Pay, Tencent
Cloud) — plausibly under-tested because it reads as harder to engage
with, not because it's saturated. Pays Low ($20–30). Requires KYC and
18+.

**4th — Daytona Bug Bounty (Intigriti).** Best fit specifically for a
systems/sandbox/container-skilled newcomer, poor fit for a pure-web
newcomer. Narrow scope, flat per-severity payouts including Low (€200),
133 days old. Confirm the 2FA-only vs. 2FA-plus-application question
live before relying on it.

**5th — Adobe Public (Intigriti).** Still the most time-sensitive single
item (15 days old, matches `SOLO_REVENUE_ROUTES.md`'s existing timing-
edge finding) but ranked below the four above for the same reason
`BOUNTY_STARTING_POSITION.md` already gave: huge, decade-deep surface,
biggest crowd, hardest for a true newcomer's first find specifically.

**Not ranked — do not start here:**
- **Coveo** — status is now Suspended. Drop until reconfirmed live.
- **NVIDIA** — genuinely younger than previously framed (96 days per
  Intigriti's own `createdAt`), but still skill-gated to
  systems/reverse-engineering per `BOUNTY_STARTING_POSITION.md` §3 —
  re-rank up only if the operator's actual skill matches.
- **Bugcrowd (general)** — no reliable freshness signal exists; treat
  as a parallel-registration lane per `BUG_BOUNTY_PLAN.md`'s existing
  sequencing, not a targeted pick from this sweep. Check each
  candidate's reward summary for "Points" vs. dollar minimums before
  choosing one.
- **HackerOne (general)** — same, register in parallel, no
  sweep-specific pick possible from what's reachable.
- **Open Bug Bounty** — worth registering for the free public track
  record it offers, but its current live terms are UNKNOWN here; read
  them directly at signup, not from this file.

## 11. Direct answer — which of these pay for Low severity?

| Program | Pays Low? | Low amount |
|---|---|---|
| Ant Group Security Response Center | **Yes** | $10 |
| Tencent | **Yes** | $20 (non-core) / $30 (core) |
| Daytona | **Yes** | €200 |
| Superdrug / ICI PARIS XL / The Perfume Shop / Marionnaud (Tier 1) | **Yes** | $100–350 |
| Adobe (Tier 1) | **Yes** | $150–300 |
| NVIDIA | Not re-checked this pass — see `BUG_BOUNTY_PLAN.md` §2 for the existing figure |
| Coveo | Yes on paper ($100–200) but program is Suspended — moot until reactivated |
| DataDome Bot Bounty, Dossier Médical Partagé | UNKNOWN — brief not fetched |
| Bugcrowd programs showing "Points" as minReward | **No** — Low/early tiers pay platform points, not cash, on those specific programs |
| Open Bug Bounty | **No** — free/no-bounty by design (general knowledge, not re-verified live) |
| HackerOne (general) | Not assessable — directory unreachable |

**Every program in the top-4 shortlist above pays real cash for a Low
finding.** That is the load-bearing fact for a newcomer: a realistic
first result (a missing rate limit, a low-impact IDOR, a low-severity
auth gap) is not wasted effort on any of them.

---

## Sources

- https://api.yeswehack.com/programs (public API, no key)
- https://www.intigriti.com/researchers/bug-bounty-programs (SSR
  Algolia payload, `createdAt` field)
- https://app.intigriti.com/programs/aswatson/superdrug/detail
- https://app.intigriti.com/programs/daytona/daytonabugbounty/detail
- https://app.intigriti.com/programs/coveo/coveopublicbugbounty/detail
- https://yeswehack.com/programs/ant-group-security-response-center-bug-bounty-program
- https://yeswehack.com/programs/tencent-bug-bounty-program
- https://bugcrowd.com/engagements.json (public API, no key)
- https://hackerone.com/directory/programs (confirmed unreachable —
  client-rendered shell)
- https://www.openbugbounty.org/ (confirmed blocked — Cloudflare
  managed challenge, not bypassed)
- `foundation/mouth_bounty.py` (prior YesWeHack/Intigriti/HackerOne
  reachability audit, 2026-09-02, reused not re-derived)
