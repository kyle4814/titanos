# HUNT — bug bounty programs with almost no reports filed

Fetched 2026-09-03. Method: `api.yeswehack.com/programs` (public, keyless,
no `robots.txt` at all — same finding `foundation/mouth_bounty.py`
already recorded), paginated fully (`?page=1`, `?page=2` — API's own
`pagination.nb_pages=2`, `nb_results=60`; both pages fetched, 42+18=60,
confirmed complete, no partial page). No target system tested, scanned,
or probed. No account created. No User-Agent spoofed.

**This supersedes nothing in `DEALS_BOUNTY_TARGETS.md`** — it is a wider
sweep (all 60 programs, not the 4-row sample that file's §6 showed) using
the same source that file already validated. Read `DEALS_BOUNTY_TARGETS.md`
first for the Ant Group / Tencent / AS Watson / Daytona narrative
analysis; this file is the full ranked table plus eight new program briefs
that file didn't reach.

---

## 1. Full YesWeHack public program list, sorted by `reports_count` ascending

All 60 live public programs on the platform at fetch time. `reports_count`
is a real structured field the platform declares per program — not
inferred. `Pays Low?` for the bottom 10 is confirmed by reading each
program's own published brief (§2 below); for the rest it is UNKNOWN
(reward range only shows min/max, not a per-severity table) unless
otherwise marked.

| # | Reports | Program | Company | Reward range | Currency | Scopes | Pays Low? |
|---|---|---|---|---|---|---|---|
| 1 | **0** | Ant Group Security Response Center | Ant Group | 10–2,500 | USD | 8 | **Yes — $10** (see `DEALS_BOUNTY_TARGETS.md` §6) |
| 2 | **15** | Tencent Bug Bounty Program | Tencent | 8–5,000 | USD | 2 | **Yes — $20–30** (see `DEALS_BOUNTY_TARGETS.md` §6) |
| 3 | 106 | DataDome Bot Bounty | DataDome | 200–1,000 | EUR | 6 | **Yes — €200** |
| 4 | 118 | Dossier Medical Partagé Bug Bounty Program | CNAM (France) | 50–2,000 | EUR | 10 | **Yes — €100** |
| 5 | 122 | Xelians - Blackbox program | Xelians | 50–1,500 | EUR | 2 | **Yes — €50** |
| 6 | 136 | Moneybox Bug Bounty | Moneybox | 50–2,000 | EUR | 6 | **Yes — €50** |
| 7 | 141 | Thüringer Aufbaubank Bug Bounty Program | Thüringer Aufbaubank | 50–7,000 | EUR | 2 | **Yes — €50** |
| 8 | 144 | Okto - Bug Bounty Program | Coindcx | 0–2,000 | USD | 2 | **Yes — $50** |
| 9 | 159 | GRW Trading FZE - Open Bug Bounty Program | GRW Trading FZE | 50–3,000 | EUR | 2 | **Yes — €50/€100** (two-tier) |
| 10 | 169 | Alasco GmbH - Bug Bounty Program | Alasco GmbH | 50–1,000 | EUR | 4 | **Yes — €50** |
| 11 | 171 | Maya - Public Bug Bounty Program | Maya | 50–5,000 | USD | 9 | UNKNOWN — not fetched |
| 12 | 180 | ZECIBLE PUBLIC BUG BOUNTY PROGRAM | ZECIBLE | 100–2,000 | EUR | 17 | UNKNOWN — not fetched |
| 13 | 190 | IMOU Public Bug Bounty Program | Hangzhou Huacheng Network Tech | 10–1,200 | USD | 6 | UNKNOWN — not fetched |
| 14 | 229 | BitOasis - Bug Bounty Program | Coindcx | 5–2,000 | USD | 3 | UNKNOWN — not fetched |
| 15 | 259 | Sogexia | Sogexia | 100–2,000 | EUR | 3 | UNKNOWN — not fetched |
| 16 | 273 | CyberGhost - Bug Bounty Program | Kape Technologies | 50–1,250 | USD | 12 | UNKNOWN |
| 17 | 277 | Santé Publique France Bug Bounty Program | Santé publique France | 50–1,500 | EUR | 8 | UNKNOWN |
| 18 | 278 | Private Internet Access - Bug Bounty Program | Kape Technologies | 50–1,250 | USD | 12 | UNKNOWN |
| 19 | 281 | 3DS OUTSCALE | Dassault Systèmes | 50–5,000 | EUR | 7 | UNKNOWN |
| 20 | 284 | DANA Bug Bounty Program | DANA Indonesia | 0–3,000 | USD | 4 | UNKNOWN |
| 21 | 292 | Harman International Lifestyle Products & Services | Harman International | 100–4,000 | USD | 25 | UNKNOWN |
| 22 | 301 | Coindcx - Bug Bounty Program | Coindcx | 50–2,000 | USD | 4 | UNKNOWN |
| 23 | 354 | Dovecot | Open-Xchange | 100–5,000 | EUR | 1 | UNKNOWN |
| 24 | 355 | Cryptobox | Ercom | 100–5,000 | EUR | 3 | UNKNOWN |
| 25 | 374 | Mon Espace Santé (MES) | CNAM (France) | 50–8,000 | EUR | 43 | UNKNOWN |
| 26 | 423 | ATG Public Bug Bounty Program | ATG | 0–4,000 | EUR | 7 | UNKNOWN |
| 27 | 446 | toom Baumarkt GmbH - Webshop | Toom Baumarkt | 50–3,000 | EUR | 2 | UNKNOWN |
| 28 | 458 | DataDome Bug Bounty | DataDome | 50–3,000 | EUR | 8 | UNKNOWN |
| 29 | 564 | MediaMarktSaturn Bug Bounty Program | MediaMarktSaturn Retail Group | 100–4,000 | EUR | 31 | UNKNOWN |
| 30 | 581 | vidaXL Services - Open Bug Bounty Program | vidaXL Services Holding | 50–3,000 | EUR | 5 | UNKNOWN |
| 31 | 618 | BookBeat | BookBeat | 50–2,000 | EUR | 6 | UNKNOWN |
| 32 | 624 | KOMOJU - Public Bug Bounty Program | KOMOJU Co Ltd. | 50–7,000 | USD | 2 | UNKNOWN |
| 33 | 631 | Programme de prime aux bogues du Gouvernement du Québec | MCN (Québec) | 50–3,000 | USD | 2 | UNKNOWN |
| 34 | 645 | VINCI SA - Public program | VINCI SA | 50–3,000 | EUR | 20 | UNKNOWN |
| 35 | 656 | Louis Vuitton Malletier - Public Bug Bounty Program | Louis Vuitton Malletier | 50–5,000 | EUR | 6 | UNKNOWN |
| 36 | 683 | Pine Labs Bug Bounty Program | Pine Labs Pvt Ltd | 0–1,000 | USD | 22 | UNKNOWN |
| 37 | 689 | FDJ United (Online Betting and Gaming) - Bug Bounty program | FDJ United | 50–15,000 | EUR | 33 | UNKNOWN |
| 38 | 759 | Ooredoo QPSC - Customer Portal Bug Bounty Program | Ooredoo QPSC | 50–1,500 | USD | 5 | UNKNOWN |
| 39 | 774 | GoTo Financial - Public Bounty Program | PT GoTo Gojek Tokopedia Tbk | 5–5,000 | USD | 14 | UNKNOWN |
| 40 | 781 | Qwant | Qwant | 100–5,000 | EUR | 6 | UNKNOWN |
| 41 | 789 | Ezviz - Bug Bounty Program | ezviz | 0–5,000 | USD | 13 | UNKNOWN |
| 42 | 804 | DECATHLON | Decathlon | 50–2,500 | EUR | 5 | UNKNOWN |
| 43 | 819 | YesWeHack | YesWeHack (platform's own program) | 50–15,000 | EUR | 4 | UNKNOWN |
| 44 | 838 | ExpressVPN - Bug Bounty Program | Kape Technologies | 50–2,500 | USD | 31 | UNKNOWN |
| 45 | 844 | OTTO.DE Bug Bounty | OTTO (GmbH & Co. KG) | 50–2,500 | EUR | 10 | UNKNOWN |
| 46 | 926 | TeamViewer - Bounty Program | TeamViewer Germany GmbH | 100–10,000 | EUR | 9 | UNKNOWN |
| 47 | 974 | GOJEK - Public Bounty Program | PT GoTo Gojek Tokopedia Tbk | 5–3,500 | USD | 16 | UNKNOWN |
| 48 | 978 | Paddle.com Public Bug Bounty Program | Paddle.com Market Ltd | 50–5,000 | USD | 12 | UNKNOWN |
| 49 | 1,030 | Swapcard | Swapcard | 50–2,000 | EUR | 12 | UNKNOWN |
| 50 | 1,150 | Deezer Bug Bounty Program | Deezer | 0–2,500 | EUR | 15 | UNKNOWN |
| 51 | 1,239 | Bug Bounty Program - BlaBlaCar | Comuto SA | 50–3,000 | EUR | 11 | UNKNOWN |
| 52 | 1,740 | Doctolib | Doctolib | 0–50,000 | EUR | 9 | UNKNOWN |
| 53 | 1,768 | OVHcloud | OVHcloud | 50–12,500 | EUR | 3 | UNKNOWN |
| 54 | 1,802 | Telenor Sweden Public Bug Bounty Program | Telenor Sweden | 50–6,000 | EUR | 24 | UNKNOWN |
| 55 | 1,855 | Swiss Post - E-Voting | Swiss Post | 100–230,000 | EUR | 4 | UNKNOWN |
| 56 | 2,282 | HARMAN International - Web Applications | Harman International | 100–4,000 | USD | 27 | UNKNOWN |
| 57 | 2,559 | Swiss Post | Swiss Post | 50–10,000 | EUR | 11 | UNKNOWN |
| 58 | 2,593 | VFS Global Bug Bounty Program | VFS GLOBAL SERVICES PVT. LTD. | 5–1,500 | USD | 26 | UNKNOWN |
| 59 | 3,346 | Infomaniak Bug Bounty program | Infomaniak | 100–7,000 | EUR | 46 | UNKNOWN |
| 60 | 5,722 | YesWeHack Dojo | YesWeHack Dojo | — (no bounty, `bounty:false`) | EUR | 1 | No — VDP-style training program, not a paying target |

None of the 60 declare a "member/hunter count" field on this API — checked
directly, no such key exists in the raw JSON (same finding
`DEALS_BOUNTY_TARGETS.md` §6 already recorded for `created_at`). Member
counts are therefore UNKNOWN across the whole table, not just the top 10 —
recorded honestly rather than fabricated. `#60 Dojo` is YesWeHack's own
in-house training program (self-referential, no real company behind it,
no bounty) — included for completeness since it is public, excluded from
the newcomer ranking below.

## 2. Ten lowest-report programs — scope, technology, newcomer language

Ranks 1–2 (Ant Group, Tencent) are already fully analysed in
`DEALS_BOUNTY_TARGETS.md` §6 — not re-derived here. Ranks 3–10, read live
from each program's own published brief 2026-09-03:

**#3 — DataDome Bot Bounty (106 reports).** Scope: 6 assets, all bot-
protection infrastructure endpoints (`bounty-nodejs/fastly/nginx.
datashield.co`, `*.captcha-delivery.com`, `js.datadome.co`,
`api-js.datadome.co`) — narrow, single-product, anti-bot/anti-fraud
platform for websites/apps/APIs. Reward: Low €200 / Medium €500 / High
€700 / Critical €1,000 — pays Low. No explicit newcomer language. Notably
excludes distributed/multi-IP scraping demos and requires mandatory CSV
documentation + reproduction code with every report — a real barrier for
a first-timer unfamiliar with their submission format, not a skill
barrier.

**#4 — Dossier Medical Partagé (118 reports).** Scope: 10 subdomains of
France's national shared electronic health-records platform (DMP), all
rated "High" asset value, operated by CNAM. Reward: Low €100 / Medium
€300 / High €800 / Critical €2,000 — pays Low. No newcomer language.
Requires a program-specific User-Agent string
(`CNAM-DPM-privateBBP`) — mechanical registration step, not a skill gate.
24 excluded categories, standard shape.

**#5 — Xelians Blackbox Program (122 reports).** Scope: 2 preprod web
apps (`preprod-xam.xelians.fr`, `preprod-datahub.xelians.fr`) — enterprise
document-archival software (XAM, built on VITAM/CAS/ElasticSearch) and an
ETL document-exchange hub (XDH). Reward: Low €50 / Medium €150 / High €700
/ Critical €1,500 — pays Low, all tiers. No explicit newcomer language
("happy to thank everyone who submits valid reports"). Requires a
program-specific User-Agent suffix; first-reporter-only eligibility.

**#6 — Moneybox Bug Bounty (136 reports).** Scope: 1 API + 3 web apps +
iOS/Android apps — UK fintech, 600,000+ customers, cash-savings and
investment products. Reward: Low €50 / Medium €500 / High €1,000 /
Critical €2,000 — pays Low. No explicit newcomer language. Requires
YesWeHack email aliases + User-Agent suffix.

**#7 — Thüringer Aufbaubank (141 reports).** Scope: 2 web apps — German
state development bank's public funding-application portals
(`thueringer-foerderportal.eu`, `login.aufbaubank.de`). Reward: Low €50 /
Medium €200 / High €2,000 / Critical €7,000 — pays Low, and the High/
Critical ceiling is unusually generous for a 2-scope program. No explicit
newcomer language, but a genuinely narrow, learnable scope. Notable
operational constraint: any vulnerability found must be reported within
24 hours of discovery — tighter than most programs' disclosure windows,
worth knowing before starting.

**#8 — Okto Bug Bounty (144 reports).** Scope: iOS + Android apps plus
`*.okto.tech` APIs — DeFi/crypto wallet (multi-chain token swap,
self-custody), same parent company (Coindcx) as #22 on the full table.
Reward: Low $50 / Medium $250 / High $1,000 / Critical $2,000 — pays Low.
No explicit newcomer language. Mobile-first scope — worth noting for a
web-only newcomer, narrower fit than the web-based programs on this list.

**#9 — GRW Trading FZE / dropXL (159 reports).** Scope: 2 wildcard
domains — `*.grwtrading.com` (High) and `*.dropxl.com` (Critical), a
cross-border dropshipping/e-commerce platform (~90,000 SKU catalog).
Reward: two-tier table — grwtrading.com Low €50/Med €250/High €800/Crit
€2,000; dropxl.com Low €100/Med €400/High €1,500/Crit €3,000 — pays Low
on both. **Explicit newcomer-adjacent language, the only one of this
batch besides Ant Group/Tencent to carry it:** *"We invite ethical
hackers and security researchers to test our systems, report any bugs or
vulnerabilities, and help us strengthen our security."* Wildcard scope on
both domains is genuinely broad for a sub-200-report program.

**#10 — Alasco GmbH (169 reports).** Scope: `app.alasco.de` + `api.
alasco.de` (both High) + two wildcard "Other" scopes — German real-estate
project-management SaaS (financial controlling, ESG data). Reward: Low
€50 / Medium €200 / High €600 / Critical €1,000 — pays Low, but the
overall ceiling (€1,000 max) is the lowest of this ten-item batch. No
explicit newcomer language. Authenticated areas are explicitly
out-of-scope — narrows the attack surface to what's reachable
unauthenticated, a genuine constraint on finding anything beyond
low/medium severity. Testing window restricted to 08:00–17:00 CET.

**Cross-cutting finding across all ten:** every single one pays cash for
a Low finding — none of this ten-item batch is a points-only or
VDP-disguised-as-bounty program. Every one requires a distinguishing
User-Agent string or YesWeHack email alias at minimum — mechanical
registration overhead, not a skill barrier, but worth doing before
testing anything.

## 3. Intigriti — re-pulled, no new program found

Re-fetched `intigriti.com/researchers/bug-bounty-programs` 2026-09-03.
**Identical 24-program list to `DEALS_BOUNTY_TARGETS.md` §1**, same names,
same order, same reward ranges (Adobe $75–15k, NVIDIA $150–15k, Daytona
€200–3.5k, Coveo $100–5.5k, the four AS Watson siblings $10–8.5k each,
seventeen VDPs). **No newly-listed program found this pass.** Confirmed
again: this page's server-rendered Algolia payload still exposes only
this 24-of-~181 slice with no working pagination — the same structural
limit `foundation/mouth_bounty.py` and `DEALS_BOUNTY_TARGETS.md` already
recorded, not re-solved here. A genuinely new low-report Intigriti
program older than this slice's window would not be visible from this
fetch — an honest, standing gap, not claimed as a full sweep.

## 4. HackenProof — swept, Zest Protocol's report metric no longer public

`hackenproof.com/robots.txt` returns HTTP 200, `User-agent: * / Allow: /`
— fully permissive, confirmed live this pass. The `/programs` page is
real, server-rendered data (321 total results across 33 pages, confirmed
by the page's own pagination footer).

**Zest Protocol** (named in this task's brief at 9 reports/6 members from
a prior pass) is still listed, now titled "Zest Protocol Smart Contracts"
(Bitcoin lending protocol, Clarity-language smart contracts, reward
ceiling $100,000) — but its paid amount and submission count are now
shown as **private/not publicly disclosed** on this fetch. This is a
genuine change from the prior pass, recorded honestly: either
HackenProof altered what's shown publicly per-program, or the prior
figure came from a page this fetch didn't reach. Not fabricated forward —
treat the 9/6 figure as stale until re-confirmed.

**Two programs with a visible low-activity signal on HackenProof's own
`Submissions` field** (a genuine platform-declared metric, comparable in
kind to YesWeHack's `reports_count` though not proven to mean exactly the
same thing):

| Program | Reward ceiling | Paid | Submissions |
|---|---|---|---|
| Zynk Protocol | $5,000 | $0 | 16 |
| ADI Predictstreet Smart Contracts | $10,000 | $0 | 36 |

Both are smart-contract-only scopes (Clarity/Solidity-class skill
required, not general web) — narrower fit than the YesWeHack top 10
above for a web-skilled newcomer, but genuinely low-report by the
platform's own count. **Not fully swept**: only page 1 of 33 (321 total
programs) was read this pass — HackenProof is reachable and permits
crawling per its own `robots.txt`, so a full 33-page paginated sweep
matching the YesWeHack method is possible but was not completed this
cycle; recorded as a real gap, not silently dropped. If Kyle wants the
full HackenProof ranking, that is the direct next action (33 page
fetches, same method as §1 above).

## 5. Direct ranking answer — same weighting order this brief specified

1. Report count (lowest first) — 2. pays cash for Low — 3. scope breadth
— 4. payout size (last).

1. **Ant Group Security Response Center** — 0 reports, pays Low ($10), 8
   scopes, explicit "recruit global talent" language. Best bet, unchanged
   from `DEALS_BOUNTY_TARGETS.md`.
2. **Tencent Bug Bounty Program** — 15 reports, pays Low ($20–30), only 2
   scopes but each is a massive product surface (WeChat, QQ, WeChat Pay,
   Tencent Cloud).
3. **GRW Trading FZE / dropXL** — 159 reports, pays Low on both domains,
   2 wildcard scopes, explicit invitation language — the strongest
   newcomer signal in the 3rd–10th band.
4. **DataDome Bot Bounty** — 106 reports (numerically lower than GRW but
   ranked below it here because of the mandatory CSV/PoC submission
   requirement and narrower non-web-first scope), pays Low, 6 scopes.
5. **Dossier Medical Partagé** — 118 reports, pays Low, 10 High-value
   scopes, real government health-data surface.
6. **Xelians Blackbox** — 122 reports, pays Low across all tiers
   (unusual — most programs skip Low or Medium), only 2 scopes.
7. **Moneybox** — 136 reports, pays Low, 6 scopes across web+API+mobile.
8. **Thüringer Aufbaubank** — 141 reports, pays Low, only 2 scopes but
   unusually high High/Critical ceiling (€7,000) for that scope size —
   24-hour report deadline is a real operational constraint.
9. **Okto** — 144 reports, pays Low, mobile-first (narrower fit for a
   web-only newcomer).
10. **Alasco GmbH** — 169 reports, pays Low, but lowest overall ceiling
    (€1,000 max) of this batch and authenticated areas excluded, capping
    what a first finding could realistically be worth.

**Not ranked, needs a full sweep before joining this list:** HackenProof
Zynk Protocol / ADI Predictstreet (16/36 submissions respectively) — real
low-activity signals, but smart-contract-only scope and only 1 of 33
pages checked.

---

## Sources

- https://api.yeswehack.com/programs?page=1 (public API, no key, no
  robots.txt at all)
- https://api.yeswehack.com/programs?page=2
- https://yeswehack.com/programs/datadome-bot-bounty
- https://yeswehack.com/programs/dossier-medical-partage-program
- https://yeswehack.com/programs/xelians-blackbox-program
- https://yeswehack.com/programs/moneybox-bug-bounty
- https://yeswehack.com/programs/thuringer-aufbaubank-bug-bounty-program
- https://yeswehack.com/programs/okto-bug-bounty-program
- https://yeswehack.com/programs/grw-trading-fze-bug-bounty-program
- https://yeswehack.com/programs/alasco-gmbh-bug-bounty-program
- https://www.intigriti.com/researchers/bug-bounty-programs (SSR Algolia
  payload, re-pulled, unchanged from prior pass)
- https://hackenproof.com/robots.txt (HTTP 200, fully permissive)
- https://hackenproof.com/programs (page 1 of 33 only)
- https://hackenproof.com/programs?search=zest
- `DEALS_BOUNTY_TARGETS.md` (prior pass, reused not re-derived for Ant
  Group / Tencent / Intigriti / AS Watson analysis)
- `foundation/mouth_bounty.py` (YesWeHack/Intigriti/HackerOne
  reachability audit, reused not re-derived)
