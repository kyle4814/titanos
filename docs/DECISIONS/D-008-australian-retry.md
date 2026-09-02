# D-008 — Australian security-work access for a solo, uncertified
# Cairns operator: AusTender itself stays blocked, but three genuinely
# new reachable routes were found — one council SaaS tenant, one state
# panel with a documented low-barrier entry, and a state contracting
# framework with NO panel gate at all.

STATUS: DECISION RECORDED — NO NEW MODULE BUILT (route confirms open-
opportunity signals exist but no single feed both (a) is reachable
unauthenticated and (b) returns machine-readable open-opportunity data
in one shot; see WHAT WOULD JUSTIFY A MODULE below).
DATE: 2026-09-02
OPERATOR PROFILE TESTED AGAINST: solo, Cairns/Australia-based, no
certifications, no insurance, no corporate references, no staff.

## METHOD

Every fetch below went through `foundation/mouth_common.py::fetch_feed()`
with a real `DiscoveryPolicy` (see `foundation/discovery_authorization.py`)
— the repository's one socket, its one honest identifying User-Agent
(`titanos-cosmic-library-mouth/1`), no header forgery, no WAF evasion.
A `403`/challenge page/blocked `robots.txt` is reported as a finding,
never routed around. Scripts used for this cycle live in the scratchpad
(`/tmp/.../scratchpad/au_route_check*.py`), not committed — not part of
this repository's file territory.

Already ruled out by D-003/D-006 and **not re-tried**: AusTender's own
`www.tenders.gov.au` search/Atom/Report/`atm` paths, `api.tenders.gov.au`,
`grants.gov.au`, `data.gov.au`, the five state open-data portals,
`data.open-contracting.org`'s AusTender mirror (award-only, confirmed
50,269/50,269 wrong shape), `catalogue.data.govt.nz`.

## ROUTE TABLE

| # | Host / route | robots.txt | Reachable? | Shape | Sole-trader-usable? |
|---|---|---|---|---|---|
| 1 | `help.tenders.gov.au` | not retrievable — `403 Forbidden` on the robots.txt fetch itself | **NO** | — | — |
| 2 | `sellingtogov.finance.gov.au` | fetch timed out (read timeout, not a 403) — genuinely inconclusive, not claimed blocked | UNKNOWN | — | — |
| 3 | `api.tenders.gov.au` (AusTender's own OCDS API, documented at `github.com/austender/austender-ocds-api`, base URL `https://api.tenders.gov.au/ocds/`) | same host D-006 already tested, `403` | **NO (same WAF)** | contract-award data from 2013 onward per the repo's own docs, same wrong shape as D-006's mirror finding | n/a |
| 4 | `portal.tenderlink.com` (the SaaS host behind Cairns Regional Council's and many QLD councils' tender portals) | robots.txt request itself returns an **Incapsula** bot-challenge page, not a text robots file | **NO** — every path tested (including `/cairns/alltenders/`) returns an Incapsula "Request unsuccessful" iframe | — | — |
| 5 | `tenders.net` (a different, independent tendering SaaS — hosts Cairns Regional Council's actual live portal at `/dtp/cairns/`) | `robots.txt` HTTP 200, real Cloudflare-managed policy: `User-agent: *` → `Content-Signal: search=yes,ai-train=no,use=reference` / `Allow: /`; blocks `GPTBot`/`CCBot`/`Amazonbot`/etc. by name, none of which apply to this fetcher's honest identity | **YES** | **Right shape, genuinely live.** `https://tenders.net/dtp/cairns/` returned real server-rendered HTML: *"Cairns Regional Council does not have any Current Tenders available at the moment. Please check this page regularly..."* — an honest, current, zero-count state, not an award list. Confirms the site is real and would show live open tenders when they exist. | Viewing full tender **details** requires free registration ("Universal Access... registering for free") — a real, cheap friction step, not a certification/insurance barrier. |
| 6 | `qtenders.hpw.qld.gov.au` (Queensland's own state tender portal, distinct from AusTender) | HTTP 200, `User-agent: * / Allow: /` | **YES** | **UNCONFIRMED SHAPE** — the site is a Blazor WebAssembly SPA (`_framework/blazor.webassembly*.js`); the tender list itself loads via a backend API this cycle did not locate. Reachable but not yet provably right-shape. | n/a until the API is found |
| 7 | `www.buyict.gov.au` (BuyICT / Digital Marketplace) | `robots.txt` HTTP 200, **empty** (`Disallow:` for nobody) | **YES** (page fetches; content is a ServiceNow Angular SPA, client-rendered — static fetch cannot read the body text) | Panel entry, not a live-opportunity feed | See PANEL REQUIREMENTS below |
| 8 | `buy.nsw.gov.au` | `403 Forbidden` on robots.txt | **NO** | — | — |
| 9 | `www.info.buy.nsw.gov.au` (NSW's documentation host — different from #8) | HTTP 200, permissive (`Allow: /`, disallows only query-string search-result URLs) | **YES** | Documentation page, not a feed | See PANEL REQUIREMENTS below — **the strongest finding this cycle** |
| 10 | `gateway.icn.org.au` (ICN Gateway) | HTTP 200, `User-agent: * / Disallow:` (nothing disallowed) | **YES** | Server-rendered shell fetched; the live project-tile data itself is client-rendered/filtered via JS, not visible in the static HTML | Free registration; see below |
| 11 | `www.forgov.qld.gov.au`, `www.business.qld.gov.au` | both HTTP 200, reachable | **YES** | Real documentation content extracted (see QITC below) | — |
| 12 | `www.buyingfor.vic.gov.au` (VIC ICT eServices register) | **Inconsistent**: one fetch returned a real `robots.txt` (637 bytes, `Crawl-delay: 2`, disallows `/oauth...`); an immediate retry of the same URL returned `403`. Reported honestly as observed, not smoothed over — possibly a rate-sensitive WAF. | PARTIAL | — | See PANEL REQUIREMENTS below |
| 13 | `www.jcu.edu.au` (James Cook University — the Cairns-local university) | `403 Forbidden` on robots.txt | **NO** | — | — |
| 14 | `www.health.qld.gov.au` (Queensland Health) | HTTP 200, permissive apart from search-result paths | **YES** (host only — the actual tenders sub-path was not located this cycle, time-boxed) | UNCONFIRMED | — |
| 15 | `www.cairns.qld.gov.au` (council's own site, direct) | `403 Forbidden` on robots.txt, reconfirmed this cycle | **NO** | Consistent with D-006's general finding that direct council/government-CMS hosts sit behind the same WAF class | Route #5 (tenders.net) is how this same council's tenders are actually reachable |

## THE ACTUAL ANSWER: WHAT DOES A SOLE TRADER WITH NO CERTIFICATIONS NEED

Three real government-panel requirement sets were read directly off live,
reachable pages (quoted, not summarised from memory):

**NSW ICT Services Scheme** (`info.buy.nsw.gov.au/schemes/ict-services-scheme`,
route #9, fetched live) — the most sole-trader-accessible of the three:

> "Is annual turnover an acceptance criterion? No. It is requested for
> informational purposes but does not form part of the acceptance
> criteria for admission to the ICT Services Scheme."

> "...suppliers on this list may enter into contracts using simplified
> terms and conditions with **lower insurances**, to reduce the cost of
> doing business with government. The advanced registered suppliers
> list has a higher level of acceptance requirements given suppliers on
> this list can be engaged in high-risk procurements..."

> "Can companies from overseas apply for inclusion on the scheme? Yes,
> if they have an Australian Business Number (ABN)."

> "All ICT suppliers are eligible to apply for prequalification to the
> scheme subject to meeting the relevant requirements. The scheme
> offers an online application process."

No certification is named as a gate; no minimum company size, staff
count, or insurance dollar figure is stated for the **Registered**
(entry) tier — that tier exists specifically to be cheaper to qualify
for than the Advanced tier. This is a real, named, application-anytime
("always open" per search-result corroboration) route an ABN-holding
sole trader can apply to. The scheme's own capability requirement is
demonstrated "capacity and capability" and "relative experience" via
application templates, not a credential.

**Queensland QITC** (`business.qld.gov.au`/`forgov.qld.gov.au`, routes
#11, fetched live, body extracted from the page's own `<main>` content)
— **no panel at all**:

> "The Queensland Information Technology Contracting (QITC) framework is
> used for any government purchasing of ICT products and services. The
> QITC framework provides a choice of 4 different contract types to
> reflect the risk and value of the ICT procurement: general contract,
> comprehensive contract, supplier's terms and conditions, bespoke
> contract."

No accreditation/prequalification step is named anywhere on this page —
consistent with the (separately, non-authoritatively) search-sourced
finding that Queensland abolished ICT accreditation in 2017 under the
Queensland Procurement Policy. The live page tells a supplier to go
straight to **QTenders** (route #6) for actual opportunities — which
this cycle confirmed is reachable but could not confirm the shape of
(SPA, API not located).

**Victoria ICT eServices register** (`buyingfor.vic.gov.au`, route #12,
partially reachable) — the one panel with a **real, quoted, quantified
barrier** for a genuine solo operator:

> "Businesses must have insurance certificates that meet the
> requirements: Public liability insurance coverage amount (liability)
> must be at least $5 million (Australian Dollars) per occurrence."

$5M public liability is a real cost a brand-new sole trader with no
prior contracts and no insurer relationship would have to acquire
before registering — the one state route this cycle found that is
genuinely gated on something beyond paperwork.

**BuyICT / Digital Marketplace Panel 2** (route #7): the seller
application itself only opens periodically and is submitted **through
AusTender** — i.e. the one blocked host. Insurance is required "on
request" but the application gateway is the same WAF-blocked door
already ruled out.

**ICN Gateway** (route #10): not a government panel — a free,
open-registration subcontracting marketplace. No certification,
insurance, or ABN gate found on the reachable pages; the model is
"express interest in a project a head contractor posted," not direct
government contracting. Genuinely the lowest-barrier route found this
cycle, but it is subcontracting exposure, not prime-contractor panel
membership.

## RANKED RECOMMENDATION FOR THE OPERATOR

1. **NSW ICT Services Scheme, Registered tier** — apply now (always
   open), ABN only, no accreditation named, ID'd insurance tier exists
   specifically to be cheap. Cross-border (NSW buyer, Cairns supplier)
   is legally fine for government ICT services; nothing found requires
   NSW presence.
2. **ICN Gateway** — free registration today, immediate subcontracting
   exposure, zero certification/insurance gate found.
3. **Queensland QITC / QTenders** — no panel gate exists at all;
   blocked only by this cycle's inability to locate QTenders' live
   opportunity API (SPA). Worth a dedicated follow-up cycle.
4. **Victoria eServices** — real $5M PL insurance cost; revisit once
   the operator has any paying contract and can price that insurance
   in.
5. **BuyICT/AusTender** — not currently accessible by any means this
   fetcher can use without evading a deliberately installed control;
   unchanged from D-006.

## WHAT WOULD JUSTIFY A NEW MOUTH MODULE

None of routes #5/#6/#7/#9/#10 is both (a) reachable unauthenticated
**and** (b) machine-readable open-opportunity data in one fetch, the
same bar `mouth_gets_nz.py` cleared. `tenders.net`'s Cairns page is
right-shape but requires free registration to see item-level detail
(and had zero current items at fetch time, so no parse target exists
yet to build against). `qtenders.hpw.qld.gov.au` is reachable but its
data API is undiscovered. Building a mouth against either now would be
speculative — the module's own parse function would have nothing
confirmed-real to parse. **Next concrete step, not built this cycle:**
register a free `tenders.net` account (a real, cheap, human action, not
this fetcher's job) and inspect what an authenticated Cairns tender page
actually returns; separately, use browser devtools (a human action) to
find QTenders' underlying data endpoint. Either would be the correct
Beta-rung "verify before build" step before a `mouth_tenders_net.py` or
`mouth_qtenders_qld.py` is justified.

## WHAT WOULD CHANGE THIS DECISION

- `tenders.net` shows a live open tender for Cairns (or another
  reachable QLD council) with the item visible unauthenticated — enough
  to build and test a parser against real, not hypothetical, data.
- QTenders' Blazor front-end's backing API is identified and found to
  answer unauthenticated GET requests with open-tender JSON.
- AusTender or `buy.nsw.gov.au` drops behind a CloudFront/Incapsula-class
  WAF this fetcher cannot lawfully evade — no evidence of that today.
- `sellingtogov.finance.gov.au`'s timeout resolves on retry to either a
  real block or a real reachable host — currently genuinely unknown,
  not assumed either way.
